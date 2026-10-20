import asyncio
import os
import json
import random
import string
import logging
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import (
    Command, CommandStart,
    ChatMemberUpdatedFilter, IS_NOT_MEMBER, ADMINISTRATOR, MEMBER
)
from aiogram.filters.command import CommandObject
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton, ChatMemberUpdated, CallbackQuery
)
from aiogram.enums import ChatType
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

# --- НАСТРОЙКИ ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
GIGACHAT_KEY = os.getenv("GIGACHAT_KEY")
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "0"))
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
DATA_DIR = os.getenv("DATA_DIR", "./data")
os.makedirs(DATA_DIR, exist_ok=True)

CHATS_FILE = os.path.join(DATA_DIR, "chats.json")
WARNS_FILE = os.path.join(DATA_DIR, "warns.json")
USERS_FILE = os.path.join(DATA_DIR, "users.json")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- БАЗА ---
def load_json(f, default=None):
    if os.path.exists(f):
        try:
            with open(f, "r", encoding="utf-8") as fp:
                return json.load(fp)
        except:
            return default if default is not None else {}
    return default if default is not None else {}

def save_json(f, data):
    with open(f, "w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)

def get_chat(chat_id):
    chats = load_json(CHATS_FILE, {})
    return chats.get(str(chat_id))

def save_chat(chat_id, data):
    chats = load_json(CHATS_FILE, {})
    chats[str(chat_id)] = data
    save_json(CHATS_FILE, chats)

def delete_chat(chat_id):
    chats = load_json(CHATS_FILE, {})
    if str(chat_id) in chats:
        del chats[str(chat_id)]
        save_json(CHATS_FILE, chats)

def get_warns(chat_id, user_id):
    warns = load_json(WARNS_FILE, {})
    return warns.get(f"{chat_id}_{user_id}", 0)

def add_warn(chat_id, user_id):
    warns = load_json(WARNS_FILE, {})
    key = f"{chat_id}_{user_id}"
    warns[key] = warns.get(key, 0) + 1
    save_json(WARNS_FILE, warns)
    return warns[key]

def get_user(chat_id, user_id):
    users = load_json(USERS_FILE, {})
    return users.get(f"{chat_id}_{user_id}", {"last_greet": None, "last_farewell": None})

def set_user(chat_id, user_id, data):
    users = load_json(USERS_FILE, {})
    users[f"{chat_id}_{user_id}"] = data
    save_json(USERS_FILE, users)

# --- GIGACHAT ---
giga = GigaChat(credentials=GIGACHAT_KEY, verify_ssl_certs=False, scope="GIGACHAT_API_PERS")

async def log_error(text):
    if LOG_CHANNEL_ID:
        try:
            await bot.send_message(LOG_CHANNEL_ID, f"⚠️ <b>ОШИБКА</b>\n\n{text}", parse_mode="HTML")
        except:
            pass

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
        response = giga.chat(Chat(messages=[Messages(role=MessagesRole.USER, content=prompt)]))
        content = ""
        if hasattr(response, "choices") and response.choices:
            content = response.choices[0].message.content
        elif hasattr(response, "messages") and response.messages:
            content = response.messages[0].content
        content = content.strip()
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(content[start:end])
        return {"action": "none"}
    except Exception as e:
        await log_error(f"GigaChat: {e}")
        return {"action": "none"}

# --- BOT ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- ГЛАВНОЕ МЕНЮ ---
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить чат", callback_data="add_channel")],
        [InlineKeyboardButton(text="📋 Мои чаты", callback_data="list_channels")],
    ])

@dp.message(CommandStart())
async def start(message: Message):
    if message.chat.type == ChatType.PRIVATE:
        await message.answer(
            "👋 <b>Привет! Я бот-модератор.</b>\n\n"
            "Я помогаю следить за порядком в чатах с помощью ИИ.\n\n"
            "Чтобы начать, добавь меня в свой чат (группу).",
            reply_markup=main_menu(),
            parse_mode="HTML"
        )

# --- КНОПКА «ДОБАВИТЬ ЧАТ» (ДВЕ ОПЦИИ) ---
@dp.callback_query(F.data == "add_channel")
async def cb_add_channel(callback: CallbackQuery):
    await callback.answer()
    me = await bot.get_me()
    admin_url = f"https://t.me/{me.username}?startgroup=true&admin=delete_messages+restrict_members+invite_users"
    await callback.message.answer(
        f"<b>Добавление чата</b>\n\n"
        f"<b>Способ 1:</b> Нажми кнопку ниже — Telegram предложит добавить меня с правами.\n\n"
        f"<b>Способ 2:</b> Добавь меня в чат вручную (как админа), потом нажми «📨 Прислать код» — я пришлю код в личку.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить в чат (с правами)", url=admin_url)],
            [InlineKeyboardButton(text="📨 Прислать код", callback_data="send_code")],
        ]),
        parse_mode="HTML"
    )

# --- КНОПКА «ПРИСЛАТЬ КОД» ---
@dp.callback_query(F.data == "send_code")
async def cb_send_code(callback: CallbackQuery):
    await callback.answer()
    chats = load_json(CHATS_FILE, {})
    
    # Ищем последний непривязанный чат, где бот админ
    found = None
    for cid, data in chats.items():
        if data.get("pending_code") and not data.get("owner_id"):
            found = (cid, data)
            break
    
    if not found:
        await callback.message.answer(
            "❌ Нет непривязанных чатов.\n\n"
            "Сначала добавь меня в чат как администратора, потом нажми эту кнопку.",
            parse_mode="HTML"
        )
        return
    
    cid, data = found
    me = await bot.get_me()
    code = data["pending_code"]
    await callback.message.answer(
        f"🔗 <b>Код для чата «{data.get('title', 'Чат')}»</b>\n\n"
        f"Нажми кнопку ниже, чтобы привязать чат:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🔗 Привязать чат",
                url=f"https://t.me/{me.username}?start={code}"
            )]
        ]),
        parse_mode="HTML"
    )

# --- КНОПКА «МОИ ЧАТЫ» ---
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
    
    buttons = []
    for cid, data in my_chats:
        sub_until = data.get("sub_until", "")
        status = ""
        if sub_until:
            try:
                dt = datetime.fromisoformat(sub_until)
                days_left = (dt - datetime.utcnow()).days
                if days_left > 0:
                    status = f" ✅ {days_left}д"
                else:
                    status = " ❌"
            except:
                pass
        buttons.append([InlineKeyboardButton(
            text=f"📋 {data.get('title', 'Чат')}{status}",
            callback_data=f"chat_{cid}"
        )])
    
    await callback.message.answer(
        "📋 <b>Твои чаты:</b>\n\nВыбери чат:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )

# --- МЕНЮ ЧАТА (УДАЛИТЬ / НАСТРОИТЬ ДЕЙСТВИЯ) ---
@dp.callback_query(F.data.startswith("chat_"))
async def cb_chat_menu(callback: CallbackQuery):
    await callback.answer()
    chat_id = callback.data.replace("chat_", "")
    chat_data = get_chat(chat_id)
    if not chat_data:
        await callback.message.answer("Чат не найден.")
        return
    
    if chat_data.get("owner_id") != callback.from_user.id:
        await callback.message.answer("Это не твой чат.")
        return
    
    sub_until = chat_data.get("sub_until", "")
    status = "❓"
    if sub_until:
        try:
            dt = datetime.fromisoformat(sub_until)
            days_left = (dt - datetime.utcnow()).days
            if days_left > 0:
                status = f"✅ активна ({days_left} дн.)"
            else:
                status = "❌ истекла"
        except:
            pass
    
    text = (
        f"📋 <b>{chat_data.get('title', 'Чат')}</b>\n\n"
        f"ID: <code>{chat_id}</code>\n"
        f"Подписка: {status}\n\n"
        f"Что хочешь сделать?"
    )
    
    await callback.message.answer(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Настроить действия бота", callback_data=f"settings_{chat_id}")],
            [InlineKeyboardButton(text="📚 База знаний", callback_data=f"knowledge_{chat_id}")],
            [InlineKeyboardButton(text="🗑️ Удалить чат", callback_data=f"delete_{chat_id}")],
        ]),
        parse_mode="HTML"
    )

# --- НАСТРОИТЬ ДЕЙСТВИЯ (ЖДЁМ ТЕКСТ) ---
@dp.callback_query(F.data.startswith("settings_"))
async def cb_settings(callback: CallbackQuery):
    await callback.answer()
    chat_id = callback.data.replace("settings_", "")
    chat_data = get_chat(chat_id)
    if not chat_data or chat_data.get("owner_id") != callback.from_user.id:
        await callback.message.answer("Это не твой чат.")
        return
    
    await callback.message.answer(
        f"✏️ <b>Настройка чата «{chat_data.get('title', 'Чат')}»</b>\n\n"
        f"<b>Напиши текст правил</b> для этого чата. Например:\n"
        f"<i>«Запрещён мат, спам и реклама. За мат — предупреждение, за спам — бан»</i>",
        parse_mode="HTML"
    )
    
    users = load_json(USERS_FILE, {})
    key = f"waiting_rules_{callback.from_user.id}"
    users[key] = chat_id
    save_json(USERS_FILE, users)

# --- БАЗА ЗНАНИЙ ---
@dp.callback_query(F.data.startswith("knowledge_"))
async def cb_knowledge(callback: CallbackQuery):
    await callback.answer()
    chat_id = callback.data.replace("knowledge_", "")
    chat_data = get_chat(chat_id)
    if not chat_data or chat_data.get("owner_id") != callback.from_user.id:
        await callback.message.answer("Это не твой чат.")
        return
    
    rules = chat_data.get("rules", "")
    if not rules:
        await callback.message.answer(
            "📚 <b>База знаний пуста.</b>\n\n"
            "Напиши правила через «✏️ Настроить действия бота».",
            parse_mode="HTML"
        )
    else:
        await callback.message.answer(
            f"📚 <b>База знаний чата «{chat_data.get('title', 'Чат')}»:</b>\n\n{rules}",
            parse_mode="HTML"
        )

# --- УДАЛИТЬ ЧАТ ---
@dp.callback_query(F.data.startswith("delete_"))
async def cb_delete_chat(callback: CallbackQuery):
    await callback.answer()
    chat_id = callback.data.replace("delete_", "")
    chat_data = get_chat(chat_id)
    if not chat_data or chat_data.get("owner_id") != callback.from_user.id:
        await callback.message.answer("Это не твой чат.")
        return
    
    delete_chat(chat_id)
    await callback.message.answer(
        f"🗑️ Чат «{chat_data.get('title', 'Чат')}» удалён из списка."
    )

# --- ПРИВЯЗКА ЧАТА (БОТ ДОБАВЛЕН) ---
@dp.my_chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> (ADMINISTRATOR | MEMBER)))
async def on_bot_added(event: ChatMemberUpdated):
    chat_id = event.chat.id
    chat_title = event.chat.title or "Без названия"
    member = event.new_chat_member
    
    has_rights = False
    if member.status == "administrator":
        has_rights = member.can_delete_messages and member.can_restrict_members
    
    if has_rights:
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        save_chat(chat_id, {
            "title": chat_title,
            "owner_id": None,
            "rules": "",
            "sub_until": (datetime.utcnow() + timedelta(days=3)).isoformat(),
            "pending_code": code,
            "custom_commands": {},
            "greeting": "👋 Привет, {name}! Добро пожаловать.",
            "farewell": "👋 Пока, {name}.",
            "warn_limit": 3
        })
        me = await bot.get_me()
        await bot.send_message(
            chat_id,
            f"👋 <b>Привет! Я бот-модератор.</b>\n\n"
            f"Чтобы привязать этот чат, скопируй код и отправь мне в личку:\n\n"
            f"<code>{code}</code>\n\n"
            f"Или нажми кнопку ниже:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔗 Привязать чат", url=f"https://t.me/{me.username}?start={code}")]
            ]),
            parse_mode="HTML"
        )
    else:
        save_chat(chat_id, {
            "title": chat_title,
            "owner_id": None,
            "rules": "",
            "sub_until": (datetime.utcnow() + timedelta(days=3)).isoformat(),
            "pending_code": None,
            "custom_commands": {},
            "greeting": "👋 Привет, {name}! Добро пожаловать.",
            "farewell": "👋 Пока, {name}.",
            "warn_limit": 3
        })
        try:
            await bot.send_message(
                chat_id,
                "⚠️ <b>Внимание!</b>\n\n"
                "Чтобы я мог удалять мат и банить спамеров, выдай мне права администратора:\n"
                "• Удалять сообщения\n"
                "• Блокировать участников\n\n"
                "Без этих прав я не смогу модерировать.",
                parse_mode="HTML"
            )
        except:
            pass

# --- ПРИВЯЗКА ПО КОДУ ---
@dp.message(CommandStart(deep_link=True))
async def start_with_code(message: Message, command: CommandObject):
    code = command.args
    if not code:
        await start(message)
        return
    
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
        await message.answer(
            f"✅ <b>Чат «{chats[str(found_chat_id)]['title']}» привязан!</b>\n\n"
            f"Теперь напиши мне правила модерации для этого чата (например: «Запрещён мат, спам и реклама»).",
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Код не найден или устарел.")

# --- ОБРАБОТКА ТЕКСТА ПРАВИЛ ---
@dp.message(F.text & ~F.text.startswith("/") & (F.chat.type == ChatType.PRIVATE))
async def handle_rules(message: Message):
    users = load_json(USERS_FILE, {})
    key = f"waiting_rules_{message.from_user.id}"
    chat_id = users.get(key)
    
    if not chat_id:
        return
    
    chat_data = get_chat(chat_id)
    if not chat_data:
        await message.answer("Чат не найден.")
        return
    
    chat_data["rules"] = message.text
    save_chat(int(chat_id), chat_data)
    
    del users[key]
    save_json(USERS_FILE, users)
    
    await message.answer(
        f"✅ Правила для чата «{chat_data.get('title', 'Чат')}» сохранены!\n\n"
        f"Теперь я буду модерировать по этим правилам.",
        parse_mode="HTML"
    )

# --- ПРИВЕТСТВИЕ / ПРОЩАНИЕ ---
@dp.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> MEMBER))
async def on_user_join(event: ChatMemberUpdated):
    chat_id = event.chat.id
    chat_data = get_chat(chat_id)
    if not chat_data or not chat_data.get("greeting"):
        return
    user_id = event.new_chat_member.user.id
    user_data = get_user(chat_id, user_id)
    now = datetime.utcnow()
    last = user_data.get("last_greet")
    if last and (now - datetime.fromisoformat(last)) < timedelta(hours=24):
        return
    greeting = chat_data["greeting"].replace("{name}", event.new_chat_member.user.first_name)
    await bot.send_message(chat_id, greeting)
    user_data["last_greet"] = now.isoformat()
    set_user(chat_id, user_id, user_data)

@dp.chat_member(ChatMemberUpdatedFilter(MEMBER >> IS_NOT_MEMBER))
async def on_user_leave(event: ChatMemberUpdated):
    chat_id = event.chat.id
    chat_data = get_chat(chat_id)
    if not chat_data or not chat_data.get("farewell"):
        return
    user_id = event.old_chat_member.user.id
    user_data = get_user(chat_id, user_id)
    now = datetime.utcnow()
    last = user_data.get("last_farewell")
    if last and (now - datetime.fromisoformat(last)) < timedelta(hours=1):
        return
    farewell = chat_data["farewell"].replace("{name}", event.old_chat_member.user.first_name)
    await bot.send_message(chat_id, farewell)
    user_data["last_farewell"] = now.isoformat()
    set_user(chat_id, user_id, user_data)

# --- МОДЕРАЦИЯ ---
async def moderate_message(message: Message):
    chat_id = message.chat.id
    chat_data = get_chat(chat_id)
    if not chat_data:
        return

    if message.from_user:
        if message.from_user.id == OWNER_ID:
            return
        try:
            member = await bot.get_chat_member(chat_id, message.from_user.id)
            if member.status in ("administrator", "creator"):
                return
        except:
            pass

    sub_until = chat_data.get("sub_until")
    if sub_until and datetime.fromisoformat(sub_until) < datetime.utcnow():
        await log_error(f"Подписка истекла: {chat_data.get('title')} ({chat_id})")
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
        await message.reply(f"⚠️ Предупреждение ({w}/{warn_limit}): {reason}")
        if w >= warn_limit:
            try:
                await bot.ban_chat_member(chat_id, message.from_user.id)
                await message.answer(f"🚫 Забанен за {warn_limit} нарушения.")
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

# --- КОМАНДЫ В ЧАТЕ ---
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
    if not message.reply_to_message:
        await message.reply("Ответь на сообщение пользователя.")
        return
    user_id = message.reply_to_message.from_user.id
    w = add_warn(message.chat.id, user_id)
    await message.reply(f"⚠️ @{message.reply_to_message.from_user.username} получил предупреждение ({w}/3).")

@dp.message(Command("mute"))
async def cmd_mute(message: Message):
    if not message.reply_to_message:
        await message.reply("Ответь на сообщение пользователя.")
        return
    user_id = message.reply_to_message.from_user.id
    try:
        await bot.restrict_chat_member(
            message.chat.id, user_id,
            types.ChatPermissions(can_send_messages=False),
            until_date=datetime.utcnow() + timedelta(minutes=60)
        )
        await message.reply(f"🔇 @{message.reply_to_message.from_user.username} замучен на 60 минут.")
    except Exception as e:
        await message.reply(f"Ошибка: {e}")

@dp.message(Command("ban"))
async def cmd_ban(message: Message):
    if not message.reply_to_message:
        await message.reply("Ответь на сообщение пользователя.")
        return
    user_id = message.reply_to_message.from_user.id
    try:
        await bot.ban_chat_member(message.chat.id, user_id)
        await message.reply(f"🚫 @{message.reply_to_message.from_user.username} забанен.")
    except Exception as e:
        await message.reply(f"Ошибка: {e}")

@dp.message(Command("activate"))
async def cmd_activate(message: Message):
    if message.from_user.id != OWNER_ID:
        await message.reply("Только владелец бота может активировать подписку.")
        return
    args = message.text.split()
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
        chat_data["sub_until"] = (datetime.utcnow() + timedelta(days=days)).isoformat()
        save_chat(chat_id, chat_data)
        await message.reply(f"✅ Подписка для «{chat_data['title']}» продлена на {days} дней.")
    except Exception as e:
        await message.reply(f"Ошибка: {e}")

# --- ЗАПУСК ---
async def main():
    logger.info("✅ Бот запущен")
    await dp.start_polling(
        bot,
        allowed_updates=["message", "callback_query", "chat_member", "my_chat_member"]
    )

if __name__ == "__main__":
    asyncio.run(main())
