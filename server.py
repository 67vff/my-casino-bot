import warnings
warnings.filterwarnings(
    "ignore",
    message=r'Field "model_.*" in .* has conflict with protected namespace "model_"'
)

import asyncio
import os
import json
import random
import string
import logging
from datetime import datetime, timedelta, timezone

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import (
    Command, CommandStart,
    ChatMemberUpdatedFilter, IS_NOT_MEMBER, ADMINISTRATOR, MEMBER
)
from aiogram.filters.command import CommandObject
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    ChatMemberUpdated, CallbackQuery
)
from aiogram.enums import ChatType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

# --- НАСТРОЙКИ ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
GIGACHAT_KEY = os.getenv("GIGACHAT_KEY")
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "0") or "0")
OWNER_ID = int(os.getenv("OWNER_ID", "0") or "0")
DATA_DIR = os.getenv("DATA_DIR", "./data")

if not BOT_TOKEN:
    raise SystemExit("❌ Не задан BOT_TOKEN")
if not GIGACHAT_KEY:
    raise SystemExit("❌ Не задан GIGACHAT_KEY")

os.makedirs(DATA_DIR, exist_ok=True)

CHATS_FILE = os.path.join(DATA_DIR, "chats.json")
WARNS_FILE = os.path.join(DATA_DIR, "warns.json")
USERS_FILE = os.path.join(DATA_DIR, "users.json")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

UTC = timezone.utc
def utcnow() -> datetime:
    return datetime.now(UTC)

# --- БАЗА ---
def load_json(f, default=None):
    if os.path.exists(f):
        try:
            with open(f, "r", encoding="utf-8") as fp:
                return json.load(fp)
        except Exception as e:
            logger.error(f"load_json {f}: {e}")
            return default if default is not None else {}
    return default if default is not None else {}

def save_json(f, data):
    with open(f, "w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)

def get_chat(chat_id):
    return load_json(CHATS_FILE, {}).get(str(chat_id))

def save_chat(chat_id, data):
    chats = load_json(CHATS_FILE, {})
    chats[str(chat_id)] = data
    save_json(CHATS_FILE, chats)

def get_warns(chat_id, user_id):
    return load_json(WARNS_FILE, {}).get(f"{chat_id}_{user_id}", 0)

def add_warn(chat_id, user_id):
    warns = load_json(WARNS_FILE, {})
    key = f"{chat_id}_{user_id}"
    warns[key] = warns.get(key, 0) + 1
    save_json(WARNS_FILE, warns)
    return warns[key]

def reset_warns(chat_id, user_id):
    warns = load_json(WARNS_FILE, {})
    key = f"{chat_id}_{user_id}"
    if key in warns:
        warns[key] = 0
        save_json(WARNS_FILE, warns)

def get_user(chat_id, user_id):
    return load_json(USERS_FILE, {}).get(
        f"{chat_id}_{user_id}",
        {"last_greet": None, "last_farewell": None}
    )

def set_user(chat_id, user_id, data):
    users = load_json(USERS_FILE, {})
    users[f"{chat_id}_{user_id}"] = data
    save_json(USERS_FILE, users)

# --- GIGACHAT ---
giga = GigaChat(credentials=GIGACHAT_KEY, verify_ssl_certs=False, scope="GIGACHAT_API_PERS")

# --- BOT ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- FSM ---
class RulesStates(StatesGroup):
    waiting_rules = State()

# --- ХЕЛПЕРЫ ---
async def log_error(text):
    logger.error(text)
    if LOG_CHANNEL_ID:
        try:
            await bot.send_message(
                LOG_CHANNEL_ID,
                f"⚠️ <b>ОШИБКА</b>\n\n{text}",
                parse_mode="HTML"
            )
        except Exception:
            pass

async def is_admin(chat_id: int, user_id: int) -> bool:
    if user_id == OWNER_ID:
        return True
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator")
    except Exception:
        return False

async def check_message_ai(text, rules):
    try:
        prompt = f"""Ты — модератор Telegram-чата. Правила чата:
{rules}

Проанализируй сообщение. Ответь ТОЛЬКО JSON (без пояснений):
{{"action": "none"}} — всё чисто
{{"action": "warn", "reason": "причина"}} — предупреждение
{{"action": "delete", "reason": "причина"}} — удалить
{{"action": "ban", "reason": "причина"}} — забанить

Сообщение: "{text}"
"""
        response = await asyncio.to_thread(
            giga.chat,
            Chat(messages=[Messages(role=MessagesRole.USER, content=prompt)])
        )
        content = ""
        if hasattr(response, "choices") and response.choices:
            content = response.choices[0].message.content
        elif hasattr(response, "messages") and response.messages:
            content = response.messages[0].content
        content = (content or "").strip()
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(content[start:end])
        return {"action": "none"}
    except Exception as e:
        await log_error(f"GigaChat: {e}")
        return {"action": "none"}

# --- ГЛАВНОЕ МЕНЮ ---
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить чат", callback_data="add_channel")],
        [InlineKeyboardButton(text="📋 Мои чаты", callback_data="list_channels")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")],
    ])

# --- /start (в т.ч. deep-link) ---
@dp.message(CommandStart())
async def start(message: Message, command: CommandObject, state: FSMContext):
    if message.chat.type != ChatType.PRIVATE:
        return

    code = command.args
    if code:
        chats = load_json(CHATS_FILE, {})
        found_chat_id = None
        for cid, data in chats.items():
            if data.get("pending_code") == code:
                found_chat_id = int(cid)
                data["owner_id"] = message.from_user.id
                data["pending_code"] = None
                save_chat(found_chat_id, data)
                break

        if found_chat_id:
            await state.set_state(RulesStates.waiting_rules)
            await state.update_data(chat_id=found_chat_id)
            await message.answer(
                f"✅ <b>Чат «{chats[str(found_chat_id)]['title']}» привязан!</b>\n\n"
                f"Теперь напиши мне правила модерации для этого чата "
                f"(например: «Запрещён мат, спам и реклама»).",
                parse_mode="HTML"
            )
            return

        await message.answer("❌ Код не найден или устарел.")
        return

    await message.answer(
        "👋 <b>Привет! Я бот-модератор.</b>\n\n"
        "Я помогаю следить за порядком в чатах с помощью ИИ.\n\n"
        "Нажми «➕ Добавить чат» — я предложу добавить меня в группу "
        "сразу с правами администратора.",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

# --- ОБРАБОТЧИКИ КНОПОК ---
@dp.callback_query(F.data == "add_channel")
async def cb_add_channel(callback: CallbackQuery):
    await callback.answer()
    me = await bot.get_me()
    # startgroup + admin=true → Telegram предложит сразу сделать бота админом
    add_url = f"https://t.me/{me.username}?startgroup=true&admin=true"
    await callback.message.answer(
        "Чтобы добавить чат:\n\n"
        "1. Нажми «➕ Добавить в чат как админа»\n"
        "2. Выбери группу\n"
        "3. Подтверди права администратора\n"
        "4. Я напишу в чат код — отправь его мне сюда\n\n"
        "Если Telegram не предложит права — после добавления зайди в "
        "«Управление → Администраторы» и включи:\n"
        "✅ Отправлять сообщения\n"
        "✅ Удалять сообщения\n"
        "✅ Банить пользователей\n"
        "✅ Ограничивать участников",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="➕ Добавить в чат как админа",
                url=add_url
            )]
        ])
    )

@dp.callback_query(F.data == "list_channels")
async def cb_list_channels(callback: CallbackQuery):
    await callback.answer()
    chats = load_json(CHATS_FILE, {})
    my_chats = []
    for cid, data in chats.items():
        if data.get("owner_id") == callback.from_user.id:
            my_chats.append((cid, data))

    if not my_chats:
        await callback.message.answer("У тебя пока нет привязанных чатов.")
        return

    text = "📋 <b>Твои чаты:</b>\n\n"
    for cid, data in my_chats:
        sub_until = data.get("sub_until", "")
        status = "❓"
        if sub_until:
            try:
                dt = datetime.fromisoformat(sub_until)
                days_left = (dt - utcnow()).days
                status = f"✅ активна ({days_left} дн.)" if days_left > 0 else "❌ истекла"
            except Exception:
                status = "❓"
        text += f"• <b>{data.get('title', 'Без названия')}</b>\n"
        text += f"  ID: <code>{cid}</code>\n"
        text += f"  Подписка: {status}\n\n"

    await callback.message.answer(text, parse_mode="HTML")

@dp.callback_query(F.data == "settings")
async def cb_settings(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "⚙️ <b>Настройки</b>\n\n"
        "Чтобы изменить правила для конкретного чата, используй:\n"
        "<code>/setrules &lt;chat_id&gt;</code>\n\n"
        "Команды:\n"
        "/setrules &lt;chat_id&gt; — задать правила\n"
        "/activate &lt;chat_id&gt; &lt;дней&gt; — продлить подписку (только владелец бота)",
        parse_mode="HTML"
    )

# --- ПРИВЯЗКА ЧАТА (ЛЮБОЙ ПЕРЕХОД В АДМИНА) ---
@dp.my_chat_member()
async def on_bot_added(event: ChatMemberUpdated):
    logger.info(
        f"MY_CHAT_MEMBER: chat={event.chat.id} type={event.chat.type} "
        f"title={event.chat.title!r} "
        f"old={event.old_chat_member.status} new={event.new_chat_member.status}"
    )

    # Реагируем только когда бот стал админом
    if event.new_chat_member.status != "administrator":
        return

    # Пропускаем каналы — там своя логика
    if event.chat.type == ChatType.CHANNEL:
        logger.info("Пропуск: это канал, а не группа")
        return

    chat_id = event.chat.id
    chat_title = event.chat.title or "Без названия"

    existing = get_chat(chat_id)
    if existing and existing.get("owner_id"):
        logger.info(f"Чат {chat_id} уже привязан к owner_id={existing['owner_id']}")
        return

    code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

    save_chat(chat_id, {
        "title": chat_title,
        "owner_id": None,
        "rules": "",
        "sub_until": (utcnow() + timedelta(days=3)).isoformat(),
        "pending_code": code,
        "custom_commands": {},
        "greeting": "👋 Привет, {name}! Добро пожаловать.",
        "farewell": "👋 Пока, {name}.",
        "warn_limit": 3
    })

    me = await bot.get_me()
    try:
        await bot.send_message(
            chat_id,
            f"👋 <b>Привет! Я бот-модератор.</b>\n\n"
            f"Чтобы привязать этот чат, скопируй код и отправь мне в личку:\n\n"
            f"<code>{code}</code>\n\n"
            f"Или нажми кнопку ниже:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="🔗 Привязать чат",
                    url=f"https://t.me/{me.username}?start={code}"
                )]
            ]),
            parse_mode="HTML"
        )
        logger.info(f"✅ Код {code} отправлен в чат {chat_id}")
    except Exception as e:
        logger.error(
            f"❌ Не удалось отправить код в чат {chat_id}: "
            f"{type(e).__name__}: {e}"
        )

# --- НАСТРОЙКА ПРАВИЛ (FSM) ---
@dp.message(RulesStates.waiting_rules)
async def handle_rules(message: Message, state: FSMContext):
    if message.chat.type != ChatType.PRIVATE or not message.text:
        return

    data = await state.get_data()
    chat_id = data.get("chat_id")
    if not chat_id:
        await state.clear()
        await message.answer("❌ Сессия истекла. Начни заново через /start.")
        return

    chat_data = get_chat(chat_id)
    if not chat_data:
        await state.clear()
        await message.answer("❌ Чат не найден.")
        return

    chat_data["rules"] = message.text
    save_chat(chat_id, chat_data)
    await state.clear()

    await message.answer(
        f"✅ Правила для «{chat_data['title']}» сохранены! "
        f"Теперь я буду модерировать чат по этим правилам."
    )

# --- ЗАДАНИЕ ПРАВИЛ ЧЕРЕЗ КОМАНДУ ---
@dp.message(Command("setrules"))
async def cmd_setrules(message: Message, state: FSMContext):
    if message.chat.type != ChatType.PRIVATE:
        await message.answer("Команда работает только в личке с ботом.")
        return

    args = (message.text or "").split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: /setrules <chat_id>")
        return

    try:
        chat_id = int(args[1].strip())
    except ValueError:
        await message.answer("chat_id должен быть числом.")
        return

    chat_data = get_chat(chat_id)
    if not chat_data or chat_data.get("owner_id") != message.from_user.id:
        await message.answer("Чат не найден или не принадлежит тебе.")
        return

    await state.set_state(RulesStates.waiting_rules)
    await state.update_data(chat_id=chat_id)
    await message.answer(f"✏️ Напиши новые правила для «{chat_data['title']}».")

# --- ПРИВЕТСТВИЕ / ПРОЩАНИЕ ---
@dp.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> MEMBER))
async def on_user_join(event: ChatMemberUpdated):
    chat_id = event.chat.id
    chat_data = get_chat(chat_id)
    if not chat_data or not chat_data.get("greeting"):
        return
    user_id = event.new_chat_member.user.id
    if event.new_chat_member.user.is_bot:
        return
    user_data = get_user(chat_id, user_id)
    now = utcnow()
    last = user_data.get("last_greet")
    if last and (now - datetime.fromisoformat(last)) < timedelta(hours=24):
        return
    name = event.new_chat_member.user.first_name or "друг"
    greeting = chat_data["greeting"].replace("{name}", name)
    try:
        await bot.send_message(chat_id, greeting)
    except Exception as e:
        await log_error(f"Greeting failed: {e}")
        return
    user_data["last_greet"] = now.isoformat()
    set_user(chat_id, user_id, user_data)

@dp.chat_member(ChatMemberUpdatedFilter(MEMBER >> IS_NOT_MEMBER))
async def on_user_leave(event: ChatMemberUpdated):
    chat_id = event.chat.id
    chat_data = get_chat(chat_id)
    if not chat_data or not chat_data.get("farewell"):
        return
    user_id = event.old_chat_member.user.id
    if event.old_chat_member.user.is_bot:
        return
    user_data = get_user(chat_id, user_id)
    now = utcnow()
    last = user_data.get("last_farewell")
    if last and (now - datetime.fromisoformat(last)) < timedelta(hours=1):
        return
    name = event.old_chat_member.user.first_name or "друг"
    farewell = chat_data["farewell"].replace("{name}", name)
    try:
        await bot.send_message(chat_id, farewell)
    except Exception as e:
        await log_error(f"Farewell failed: {e}")
        return
    user_data["last_farewell"] = now.isoformat()
    set_user(chat_id, user_id, user_data)

# --- МОДЕРАЦИЯ ---
async def moderate_message(message: Message):
    chat_id = message.chat.id
    chat_data = get_chat(chat_id)
    if not chat_data:
        return

    try:
        me = await bot.get_me()
        bot_member = await bot.get_chat_member(chat_id, me.id)
        if bot_member.status not in ("administrator", "creator"):
            return
    except Exception:
        return

    if message.from_user:
        if message.from_user.id == OWNER_ID:
            return
        if message.from_user.is_bot:
            return
        if await is_admin(chat_id, message.from_user.id):
            return

    sub_until = chat_data.get("sub_until")
    if sub_until and datetime.fromisoformat(sub_until) < utcnow():
        return

    rules = chat_data.get("rules", "")
    if not rules:
        return

    text = message.text or message.caption or ""
    if not text:
        return

    result = await check_message_ai(text, rules)
    action = result.get("action", "none")
    reason = result.get("reason", "нарушение")
    warn_limit = chat_data.get("warn_limit", 3)

    if action == "warn" and message.from_user:
        w = add_warn(chat_id, message.from_user.id)
        try:
            await message.reply(f"⚠️ Предупреждение ({w}/{warn_limit}): {reason}")
        except Exception:
            pass
        if w >= warn_limit:
            try:
                await bot.ban_chat_member(chat_id, message.from_user.id)
                await bot.send_message(chat_id, f"🚫 Забанен за {warn_limit} нарушения.")
            except Exception as e:
                await log_error(f"Ban failed: {e}")
    elif action == "delete":
        try:
            await message.delete()
            await bot.send_message(chat_id, f"🗑️ Удалено: {reason}")
        except Exception as e:
            await log_error(f"Delete failed: {e}")
    elif action == "ban" and message.from_user:
        try:
            await bot.ban_chat_member(chat_id, message.from_user.id)
            await bot.send_message(chat_id, f"🚫 Забанен: {reason}")
        except Exception as e:
            await log_error(f"Ban failed: {e}")

# --- МОДЕРАЦИЯ В ГРУППАХ ---
@dp.message(F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
async def moderate_group_message(message: Message):
    if message.text and message.text.startswith("/"):
        return
    await moderate_message(message)

# --- КОМАНДЫ ---
@dp.message(F.text.lower().in_({"правила", "/правила"}))
async def cmd_rules(message: Message):
    chat_data = get_chat(message.chat.id)
    if chat_data and chat_data.get("rules"):
        await message.reply(f"📜 <b>Правила:</b>\n\n{chat_data['rules']}", parse_mode="HTML")
    else:
        await message.reply("Правила ещё не настроены.")

@dp.message(F.text.lower().in_({"помощь", "/help", "help"}))
async def cmd_help(message: Message):
    await message.reply(
        "📋 <b>Доступные команды:</b>\n\n"
        "/правила — показать правила\n"
        "/help — эта справка\n\n"
        "Админы: /warn, /mute, /ban (реплаем).",
        parse_mode="HTML"
    )

@dp.message(Command("warn"))
async def cmd_warn(message: Message):
    if not message.from_user or not await is_admin(message.chat.id, message.from_user.id):
        await message.reply("Только админы могут выдавать предупреждения.")
        return
    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.reply("Ответь на сообщение пользователя.")
        return
    user_id = message.reply_to_message.from_user.id
    w = add_warn(message.chat.id, user_id)
    uname = message.reply_to_message.from_user.username or user_id
    await message.reply(f"⚠️ @{uname} получил предупреждение ({w}/3).")

@dp.message(Command("mute"))
async def cmd_mute(message: Message):
    if not message.from_user or not await is_admin(message.chat.id, message.from_user.id):
        await message.reply("Только админы могут мутить.")
        return
    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.reply("Ответь на сообщение пользователя.")
        return
    user_id = message.reply_to_message.from_user.id
    try:
        await bot.restrict_chat_member(
            message.chat.id, user_id,
            types.ChatPermissions(can_send_messages=False),
            until_date=utcnow() + timedelta(minutes=60)
        )
        uname = message.reply_to_message.from_user.username or user_id
        await message.reply(f"🔇 @{uname} замучен на 60 минут.")
    except Exception as e:
        await message.reply(f"Ошибка: {e}")

@dp.message(Command("ban"))
async def cmd_ban(message: Message):
    if not message.from_user or not await is_admin(message.chat.id, message.from_user.id):
        await message.reply("Только админы могут банить.")
        return
    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.reply("Ответь на сообщение пользователя.")
        return
    user_id = message.reply_to_message.from_user.id
    try:
        await bot.ban_chat_member(message.chat.id, user_id)
        uname = message.reply_to_message.from_user.username or user_id
        await message.reply(f"🚫 @{uname} забанен.")
    except Exception as e:
        await message.reply(f"Ошибка: {e}")

@dp.message(Command("activate"))
async def cmd_activate(message: Message):
    if not message.from_user or message.from_user.id != OWNER_ID:
        await message.reply("Только владелец бота может активировать подписку.")
        return
    args = (message.text or "").split()
    if len(args) < 3:
        await message.reply("Использование: /activate <chat_id> <дней>")
        return
    try:
        chat_id = int(args[1])
        days = int(args[2])
        chat_data = get_chat(chat_id)
        if not chat_data:
            await message.reply("Чат не найден.")
            return
        chat_data["sub_until"] = (utcnow() + timedelta(days=days)).isoformat()
        save_chat(chat_id, chat_data)
        await message.reply(f"✅ Подписка для «{chat_data['title']}» продлена на {days} дней.")
    except Exception as e:
        await message.reply(f"Ошибка: {e}")

# --- ОТЛАДОЧНЫЙ ХЕНДЛЕР (в самом конце!) ---
@dp.callback_query()
async def debug_callback(callback: CallbackQuery):
    logger.info(f"🔔 CALLBACK data={callback.data!r} from={callback.from_user.id}")
    await callback.answer()

# --- ЗАПУСК ---
async def main():
    logger.info("✅ Бот запущен")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())
