import asyncio
import os
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import init_db, get_balance, update_balance, set_balance

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Хранилище активных ставок
bets = {}          # user_id -> сумма ставки
rocket = {}        # user_id -> {"mult": 1.0, "bet": сумма}
mines = {}         # user_id -> {"bet": сумма, "field": [...], "opened": []}
plinko = {}        # user_id -> ставка

# ---------- ГЛАВНОЕ МЕНЮ ----------
def main_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="🚀 Ракета", callback_data="game_rocket")
    kb.button(text="🎲 Плинко", callback_data="game_plinko")
    kb.button(text="💣 Мины", callback_data="game_mines")
    kb.button(text="🎰 Слоты", callback_data="game_slots")
    kb.button(text="💰 Баланс", callback_data="balance")
    kb.adjust(2, 2, 1)
    return kb.as_markup()

@dp.message(Command("start"))
async def start(message: types.Message):
    await get_balance(message.from_user.id)
    balance = await get_balance(message.from_user.id)
    await message.answer(
        f"🎰 Добро пожаловать в казино!\n\n"
        f"💰 Твой баланс: <b>{balance} руб.</b>\n\n"
        f"Выбери игру:",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "balance")
async def show_balance(call: CallbackQuery):
    balance = await get_balance(call.from_user.id)
    await call.message.edit_text(
        f"💰 Твой баланс: <b>{balance} руб.</b>\n\nВыбери игру:",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "main_menu")
async def back_to_menu(call: CallbackQuery):
    balance = await get_balance(call.from_user.id)
    await call.message.edit_text(
        f"💰 Твой баланс: <b>{balance} руб.</b>\n\nВыбери игру:",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

# ---------- РАКЕТА ----------
@dp.callback_query(F.data == "game_rocket")
async def rocket_start(call: CallbackQuery):
    bets[call.from_user.id] = 0
    kb = InlineKeyboardBuilder()
    for b in [10, 50, 100, 500]:
        kb.button(text=f"{b} руб.", callback_data=f"rocket_bet_{b}")
    kb.button(text="⬅️ Назад", callback_data="main_menu")
    kb.adjust(2, 2, 1)
    await call.message.edit_text("🚀 Ракета\n\nСделай ставку:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("rocket_bet_"))
async def rocket_bet(call: CallbackQuery):
    bet = int(call.data.split("_")[2])
    balance = await get_balance(call.from_user.id)
    if bet > balance:
        await call.answer("❌ Недостаточно средств!", show_alert=True)
        return
    await update_balance(call.from_user.id, -bet)
    rocket[call.from_user.id] = {"mult": 1.0, "bet": bet}
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💸 Забрать", callback_data="rocket_cashout")]
    ])
    await call.message.edit_text(
        f"🚀 Ставка: {bet} руб.\n\nМножитель: <b>x1.00</b>\n💰 Потенциальный выигрыш: {bet} руб.",
        reply_markup=kb, parse_mode="HTML"
    )
    asyncio.create_task(rocket_grow(call.from_user.id, call.message.chat.id, call.message.message_id, bet))

async def rocket_grow(user_id, chat_id, msg_id, bet):
    while user_id in rocket:
        await asyncio.sleep(1.5)
        if user_id not in rocket:
            break
        r = rocket[user_id]
        r["mult"] = round(r["mult"] + random.uniform(0.1, 0.5), 2)
        # Шанс краха растёт с множителем
        if random.random() < r["mult"] / 10:
            await update_balance(user_id, 0)
            del rocket[user_id]
            try:
                await bot.edit_message_text(
                    f"💥 <b>КРАХ!</b>\n\nМножитель достиг x{r['mult']:.2f}\nТы потерял {bet} руб.",
                    chat_id=chat_id, message_id=msg_id, parse_mode="HTML"
                )
            except Exception:
                pass
            return
        win = int(bet * r["mult"])
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💸 Забрать", callback_data="rocket_cashout")]
        ])
        try:
            await bot.edit_message_text(
                f"🚀 Ставка: {bet} руб.\n\nМножитель: <b>x{r['mult']:.2f}</b>\n💰 Потенциальный выигрыш: {win} руб.",
                chat_id=chat_id, message_id=msg_id, reply_markup=kb, parse_mode="HTML"
            )
        except Exception:
            pass

@dp.callback_query(F.data == "rocket_cashout")
async def rocket_cashout(call: CallbackQuery):
    if call.from_user.id not in rocket:
        await call.answer("Игра уже завершена!", show_alert=True)
        return
    r = rocket.pop(call.from_user.id)
    win = int(r["bet"] * r["mult"])
    await update_balance(call.from_user.id, win)
    balance = await get_balance(call.from_user.id)
    await call.message.edit_text(
        f"✅ Ты забрал <b>{win} руб.</b> (x{r['mult']:.2f})\n\n"
        f"💰 Баланс: {balance} руб.",
        reply_markup=main_menu(), parse_mode="HTML"
    )

# ---------- ПЛИНКО ----------
@dp.callback_query(F.data == "game_plinko")
async def plinko_start(call: CallbackQuery):
    kb = InlineKeyboardBuilder()
    for b in [10, 50, 100, 500]:
        kb.button(text=f"{b} руб.", callback_data=f"plinko_bet_{b}")
    kb.button(text="⬅️ Назад", callback_data="main_menu")
    kb.adjust(2, 2, 1)
    await call.message.edit_text("🎲 Плинко\n\nШарик упадёт, и ты получишь множитель!\nВыбери ставку:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("plinko_bet_"))
async def plinko_play(call: CallbackQuery):
    bet = int(call.data.split("_")[2])
    balance = await get_balance(call.from_user.id)
    if bet > balance:
        await call.answer("❌ Недостаточно средств!", show_alert=True)
        return
    await update_balance(call.from_user.id, -bet)
    # Множители: чем реже, тем больше
    multipliers = [0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0]
    weights =     [30,  25,  20,  12,  8,   4,   1]
    mult = random.choices(multipliers, weights=weights)[0]
    win = int(bet * mult)
    await update_balance(call.from_user.id, win)
    balance = await get_balance(call.from_user.id)
    emoji = "🎉" if mult >= 2 else ("🙂" if mult >= 1 else "😢")
    await call.message.edit_text(
        f"🎲 Шарик упал!\n\n{emoji} Множитель: <b>x{mult}</b>\n"
        f"Ставка: {bet} руб. → Выигрыш: <b>{win} руб.</b>\n\n"
        f"💰 Баланс: {balance} руб.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎲 Ещё раз", callback_data="game_plinko")],
            [InlineKeyboardButton(text="⬅️ Меню", callback_data="main_menu")]
        ]),
        parse_mode="HTML"
    )

# ---------- МИНЫ ----------
@dp.callback_query(F.data == "game_mines")
async def mines_start(call: CallbackQuery):
    kb = InlineKeyboardBuilder()
    for b in [10, 50, 100, 500]:
        kb.button(text=f"{b} руб.", callback_data=f"mines_bet_{b}")
    kb.button(text="⬅️ Назад", callback_data="main_menu")
    kb.adjust(2, 2, 1)
    await call.message.edit_text("💣 Мины\n\nОткрывай клетки, но не попади на мину!\nВыбери ставку:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("mines_bet_"))
async def mines_play(call: CallbackQuery):
    bet = int(call.data.split("_")[2])
    balance = await get_balance(call.from_user.id)
    if bet > balance:
        await call.answer("❌ Недостаточно средств!", show_alert=True)
        return
    await update_balance(call.from_user.id, -bet)
    # Поле 5x5 = 25 клеток, 5 мин
    field = ["💎"] * 20 + ["💣"] * 5
    random.shuffle(field)
    mines[call.from_user.id] = {"bet": bet, "field": field, "opened": [], "mult": 1.0}
    await show_mines(call, call.from_user.id)

async def show_mines(call, user_id):
    m = mines[user_id]
    kb = InlineKeyboardBuilder()
    for i in range(25):
        if i in m["opened"]:
            kb.button(text=m["field"][i], callback_data="mines_none")
        else:
            kb.button(text="⬜", callback_data=f"mines_open_{i}")
    kb.button(text=f"💸 Забрать (x{m['mult']:.2f})", callback_data="mines_cashout")
    kb.adjust(5, 5, 5, 5, 5, 1)
    try:
        await call.message.edit_text(
            f"💣 Мины\n\nСтавка: {m['bet']} руб.\n"
            f"Открыто: {len(m['opened'])}\nМножитель: <b>x{m['mult']:.2f}</b>\n"
            f"💰 Потенциал: {int(m['bet'] * m['mult'])} руб.",
            reply_markup=kb.as_markup(), parse_mode="HTML"
        )
    except Exception:
        pass

@dp.callback_query(F.data.startswith("mines_open_"))
async def mines_open(call: CallbackQuery):
    user_id = call.from_user.id
    if user_id not in mines:
        await call.answer("Игра не найдена", show_alert=True)
        return
    idx = int(call.data.split("_")[2])
    m = mines[user_id]
    if idx in m["opened"]:
        await call.answer("Уже открыто")
        return
    if m["field"][idx] == "💣":
        del mines[user_id]
        await call.message.edit_text(
            f"💥 <b>БУМ!</b> Ты попал на мину.\n\nПотеряно: {m['bet']} руб.",
            reply_markup=main_menu(), parse_mode="HTML"
        )
        return
    m["opened"].append(idx)
    # Множитель растёт с каждой безопасной клеткой
    m["mult"] = round(1.0 + len(m["opened"]) * 0.3, 2)
    await show_mines(call, user_id)

@dp.callback_query(F.data == "mines_cashout")
async def mines_cashout(call: CallbackQuery):
    user_id = call.from_user.id
    if user_id not in mines:
        await call.answer("Игра не найдена", show_alert=True)
        return
    m = mines.pop(user_id)
    win = int(m["bet"] * m["mult"])
    await update_balance(user_id, win)
    balance = await get_balance(user_id)
    await call.message.edit_text(
        f"✅ Ты забрал <b>{win} руб.</b> (x{m['mult']:.2f})\n\n"
        f"💰 Баланс: {balance} руб.",
        reply_markup=main_menu(), parse_mode="HTML"
    )

@dp.callback_query(F.data == "mines_none")
async def mines_none(call: CallbackQuery):
    await call.answer("Эта клетка уже открыта")

# ---------- СЛОТЫ ----------
@dp.callback_query(F.data == "game_slots")
async def slots_start(call: CallbackQuery):
    kb = InlineKeyboardBuilder()
    for b in [10, 50, 100, 500]:
        kb.button(text=f"{b} руб.", callback_data=f"slots_bet_{b}")
    kb.button(text="⬅️ Назад", callback_data="main_menu")
    kb.adjust(2, 2, 1)
    await call.message.edit_text("🎰 Слоты\n\nТри одинаковых — джекпот!\nВыбери ставку:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("slots_bet_"))
async def slots_play(call: CallbackQuery):
    bet = int(call.data.split("_")[2])
    balance = await get_balance(call.from_user.id)
    if bet > balance:
        await call.answer("❌ Недостаточно средств!", show_alert=True)
        return
    await update_balance(call.from_user.id, -bet)
    symbols = ["🍒", "🍋", "🍊", "💎", "7️⃣"]
    result = [random.choice(symbols) for _ in range(3)]
    if result[0] == result[1] == result[2]:
        mult = 10 if result[0] == "7️⃣" else 5
    elif result[0] == result[1] or result[1] == result[2]:
        mult = 2
    else:
        mult = 0
    win = int(bet * mult)
    if win:
        await update_balance(call.from_user.id, win)
    balance = await get_balance(call.from_user.id)
    text = f"🎰 | {result[0]} | {result[1]} | {result[2]} |\n\n"
    if mult == 10:
        text += f"🔥 ДЖЕКПОТ! x10 → <b>{win} руб.</b>"
    elif mult:
        text += f"🎉 Выигрыш: <b>{win} руб.</b> (x{mult})"
    else:
        text += "😢 Не повезло."
    text += f"\n\n💰 Баланс: {balance} руб."
    await call.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎰 Ещё раз", callback_data="game_slots")],
            [InlineKeyboardButton(text="⬅️ Меню", callback_data="main_menu")]
        ]),
        parse_mode="HTML"
    )

# ---------- ЗАПУСК ----------
async def main():
    await init_db()
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
