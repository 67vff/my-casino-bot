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
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")

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

def get_history(chat_id):
    h = load_json(HISTORY_FILE, {})
    return h.get(str(chat_id), [])

def save_history(chat_id, hist):
    h = load_json(HISTORY_FILE, {})
    h[str(chat_id)] = hist[-20:]
    save_json(HISTORY_FILE, h)

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
giga = GigaChat(
    credentials=GIGACHAT_KEY,
    verify_ssl_certs=False,
    scope="GIGACHAT_API_PERS",
    model="GigaChat-2"
)

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

Проанализируй сообщение. Ответь ТОЛЬКО JSON:
{{"action": "none"}}
{{"action": "warn", "reason": "причина"}}
{{"action": "delete", "reason": "причина"}}
{{"action": "ban", "reason": "причина"}}

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

async def ask_ai_for_rules(chat_id, user_text):
    history = get_history(chat_id)
    history.append({"role": "user", "content": user_text})
    
    chat_data = get_chat(chat_id)
    current_rules = chat_data.get("rules", "") if chat_data else ""
    
    system_prompt = f"""Ты — помощник по настройке правил модерации для Telegram-чата.

Текущие правила:
{current_rules if current_rules else "(пусто)"}

Твоя задача:
1. Понять, что пользователь хочет изменить/добавить в правилах.
2. Если непонятно — переспроси.
3. Если понятно — сформулируй новые правила красиво и предложи их.

Отвечай кратко и по делу."""
    
    messages = [Messages(role=MessagesRole.SYSTEM, content=system_prompt)]
    for h in history[-10:]:
        role = MessagesRole.USER if h["role"] == "user" else MessagesRole.ASSISTANT
        messages.append(Messages(role=role, content=h["content"]))
    
    try:
        response = giga.chat(Chat(messages=messages))
        content = ""
        if hasattr(response, "choices") and response.choices:
            content = response.choices[0].message.content
        elif hasattr(response, "messages") and response.messages:
            content = response.messages[0].content
        content = content.strip()
        
        history.append({"role": "assistant", "content": content})
        save_history(chat_id, history)
        return content
    except Exception as e:
        await log_error(f"AI rules: {e}")
        return "Не могу обработать. Попробуй ещё раз."

# --- BOT ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

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
            "Добавь меня в чат (группу) — я напишу туда кнопку для привязки.",
            reply_markup=main_menu(),
            parse_mode="HTML"
        )

@dp.callback_query(F.data == "add_channel")
async def cb_add_channel(callback: CallbackQuery):
    await callback.answer()
    me = await bot.get_me()
    admin_url = f"https://t.me/{me.username}?startgroup=true&admin=delete_messages+restrict_members+invite_users"
    await callback.message.answer(
        f"<b>Добавление чата</b>\n\n"
        f"1. Нажми кнопку ниже\n"
        f"2. Выбери группу\n"
        f"3. Подтверди права\n\n"
        f"После добавления я напишу в чат кнопку «✅ Привязать чат».",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить в чат (с правами)", url=admin_url)],
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
    
    buttons = []
    for cid, data in my_chats:
        buttons.append([InlineKeyboardButton(
            text=f"📋 {data.get('title', 'Чат')}",
            callback_data=f"chat_{cid}"
        )])
    
    await callback.message.answer(
        "📋 <b>Твои чаты:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("chat_"))
async def cb_chat_menu(callback: CallbackQuery):
    await callback.answer()
    chat_id = callback.data.replace("chat_", "")
    chat_data = get_chat(chat_id)
    if not chat_data or chat_data.get("owner_id") != callback.from_user.id:
        await callback.message.answer("Это не твой чат.")
        return
    
    text = f"📋 <b>{chat_data.get('title', 'Чат')}</b>\n\nID: <code>{chat_id}</code>"
    
    await callback.message.answer(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Настроить действия", callback_data=f"settings_{chat_id}")],
            [InlineKeyboardButton(text="📚 База знаний", callback_data=f"knowledge_{chat_id}")],
            [InlineKeyboardButton(text="🗑️ Удалить чат", callback_data=f"delete_{chat_id}")],
        ]),
        parse_mode="HTML"
    )

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
        f"Напиши, что нужно настроить (например: «Запрещён мат, спам и реклама»).\n"
        f"ИИ предложит вариант, а ты сможешь сохранить или отменить.",
        parse_mode="HTML"
    )
    
    users = load_json(USERS_FILE, {})
    users[f"waiting_rules_{callback.from_user.id}"] = chat_id
    save_json(USERS_FILE, users)

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
        await callback.message.answer("📚 <b>База знаний пуста.</b>", parse_mode="HTML")
    else:
        await callback.message.answer(f"📚 <b>Правила:</b>\n\n{rules}", parse_mode="HTML")

@dp.callback_query(F.data.startswith("delete_"))
async def cb_delete_chat(callback: CallbackQuery):
    await callback.answer()
    chat_id = callback.data.replace("delete_", "")
    chat_data = get_chat(chat_id)
    if not chat_data or chat_data.get("owner_id") != callback.from_user.id:
        await callback.message.answer("Это не твой чат.")
        return
    
    delete_chat(chat_id)
    await callback.message.answer(f"🗑️ Чат «{chat_data.get('title', 'Чат')}» удалён.")

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
    
    ai_response = await ask_ai_for_rules(chat_id, message.text)
    
    chat_data["draft"] = ai_response
    save_chat(int(chat_id), chat_data)
    
    await message.answer(
        f"🤖 <b>ИИ предлагает:</b>\n\n{ai_response}\n\n"
        f"Что сделать?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Сохранить", callback_data=f"save_{chat_id}")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_{chat_id}")],
            [InlineKeyboardButton(text="➕ Дописать", callback_data=f"append_{chat_id}")],
        ]),
        parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("save_"))
async def cb_save(callback: CallbackQuery):
    await callback.answer()
    chat_id = callback.data.replace("save_", "")
    chat_data = get_chat(chat_id)
    if not chat_data:
        await callback.message.answer("Чат не найден.")
        return
    
    draft = chat_data.get("draft", "")
    chat_data["rules"] = draft
    chat_data.pop("draft", None)
    save_chat(int(chat_id), chat_data)
    
    users = load_json(USERS_FILE, {})
    key = f"waiting_rules_{callback.from_user.id}"
    if key in users:
        del users[key]
        save_json(USERS_FILE, users)
    
    await callback.message.answer(f"✅ Правила для чата «{chat_data.get('title', 'Чат')}» сохранены!")

@dp.callback_query(F.data.startswith("cancel_"))
async def cb_cancel(callback: CallbackQuery):
    await callback.answer()
    chat_id = callback.data.replace("cancel_", "")
    chat_data = get_chat(chat_id)
    if chat_data:
        chat_data.pop("draft", None)
        save_chat(int(chat_id), chat_data)
    
    users = load_json(USERS_FILE, {})
    key = f"waiting_rules_{callback.from_user.id}"
    if key in users:
        del users[key]
        save_json(USERS_FILE, users)
    
    await callback.message.answer("❌ Отменено.")

@dp.callback_query(F.data.startswith("append_"))
async def cb_append(callback: CallbackQuery):
    await callback.answer()
    chat_id = callback.data.replace("append_", "")
    await callback.message.answer("➕ Напиши, что добавить к правилам.")
    
    users = load_json(USERS_FILE, {})
    users[f"waiting_rules_{callback.from_user.id}"] = chat_id
    save_json(USERS_FILE, users)

@dp.my_chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> (ADMINISTRATOR | MEMBER)))
async def on_bot_added(event: ChatMemberUpdated):
    chat_id = event.chat.id
    chat_title = event.chat.title or "Без названия"
    member = event.new_chat_member
    
    has_rights = False
    if member.status == "administrator":
        has_rights = member.can_delete_messages and member.can_restrict_members
    
    save_chat(chat_id, {
        "title": chat_title,
        "owner_id": None,
        "rules": "",
        "sub_until": (datetime.utcnow() + timedelta(days=3)).isoformat(),
        "bot_is_admin": has_rights,
        "greeting": "👋 Привет, {name}! Добро пожаловать.",
        "farewell": "👋 Пока, {name}.",
        "warn_limit": 3
    })
    
    if has_rights:
        await bot.send_message(
            chat_id,
            f"👋 <b>Привет! Я бот-модератор.</b>\n\n"
            f"Нажми кнопку ниже, чтобы привязать этот чат.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Привязать чат", callback_data=f"bind_{chat_id}")]
            ]),
            parse_mode="HTML"
        )
    else:
        try:
            await bot.send_message(
                chat_id,
                "⚠️ <b>Дай мне права администратора:</b>\n• Удалять сообщения\n• Блокировать участников",
                parse_mode="HTML"
            )
        except:
            pass

@dp.callback_query(F.data.startswith("bind_"))
async def cb_bind_chat(callback: CallbackQuery):
    chat_id = callback.data.replace("bind_", "")
    chat_data = get_chat(chat_id)
    if not chat_data:
        await callback.answer("Чат не найден.", show_alert=True)
        return
    
    if chat_data.get("owner_id"):
        await callback.answer("Этот чат уже привязан.", show_alert=True)
        return
    
    chat_data["owner_id"] = callback.from_user.id
    save_chat(int(chat_id), chat_data)
    
    await callback.answer("✅ Чат привязан!", show_alert=True)
    await callback.message.edit_text(
        f"✅ <b>Чат «{chat_data.get('title', 'Чат')}» привязан!</b>\n\n"
        f"Теперь напиши мне правила модерации в личку.",
        parse_mode="HTML"
    )
    
    try:
        await bot.send_message(
            callback.from_user.id,
            f"✅ <b>Чат «{chat_data.get('title', 'Чат')}» привязан!</b>\n\n"
            f"Теперь напиши мне правила модерации для этого чата.",
            parse_mode="HTML"
        )
    except:
        pass

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

@dp.message(F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
async def moderate_group_message(message: Message):
    if message.text and message.text.startswith("/"):
        return
    await moderate_message(message)

@dp.message(F.text.lower().in_({"правила", "/правила"}))
async def cmd_rules(message: Message):
    chat_data = get_chat(message.chat.id)
    if chat_data and chat_data.get("rules"):
        await message.reply(f"📜 <b>Правила:</b>\n\n{chat_data['rules']}", parse_mode="HTML")
    else:
        await message.reply("Правила ещё не настроены.")

# --- ИСПРАВЛЕННЫЙ МУТ ---
@dp.message(Command("mute"))
async def cmd_mute(message: Message):
    if message.chat.type not in ("group", "supergroup"):
        await message.reply("Мут работает только в группах и супергруппах.")
        return
    
    if not message.reply_to_message:
        await message.reply("Ответь на сообщение пользователя.")
        return
    
    user_id = message.reply_to_message.from_user.id
    args = message.text.split()
    minutes = 60
    if len(args) > 1:
        try:
            minutes = int(args[1])
        except:
            pass
    
    try:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=user_id,
            permissions=types.ChatPermissions(can_send_messages=False),
            until_date=timedelta(minutes=minutes)
        )
        await message.reply(f"🔇 @{message.reply_to_message.from_user.username} замучен на {minutes} минут.")
    except Exception as e:
        await message.reply(f"Ошибка: {e}")

@dp.message(Command("unmute"))
async def cmd_unmute(message: Message):
    if not message.reply_to_message:
        await message.reply("Ответь на сообщение пользователя.")
        return
    
    user_id = message.reply_to_message.from_user.id
    try:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=user_id,
            permissions=types.ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        await message.reply(f"🔊 @{message.reply_to_message.from_user.username} размучен.")
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

async def main():
    logger.info("✅ Бот запущен")
    await dp.start_polling(
        bot,
        allowed_updates=["message", "callback_query", "chat_member", "my_chat_member"]
    )

if __name__ == "__main__":
    asyncio.run(main())
