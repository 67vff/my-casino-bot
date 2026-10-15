import asyncio
import os
import json
import random
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")
PORT = int(os.getenv("PORT", 3000))
DATA_DIR = os.getenv("DATA_DIR", "./data")
os.makedirs(DATA_DIR, exist_ok=True)

DB_FILE = os.path.join(DATA_DIR, "balances.json")

# ---------- ПРОСТАЯ БАЗА ДАННЫХ (JSON) ----------
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False)

def get_balance(user_id: int) -> int:
    db = load_db()
    uid = str(user_id)
    if uid not in db:
        db[uid] = 100
        save_db(db)
    return db[uid]

def set_balance(user_id: int, amount: int):
    db = load_db()
    db[str(user_id)] = amount
    save_db(db)

def update_balance(user_id: int, delta: int):
    new = max(0, get_balance(user_id) + delta)
    set_balance(user_id, new)
    return new

# ---------- HTML MINI APP ----------
HTML_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>🎰 Казино</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
* { margin:0; padding:0; box-sizing:border-box; -webkit-tap-highlight-color:transparent; }
body { font-family:-apple-system,BlinkMacSystemFont,sans-serif; background:#1a1a2e; color:#fff; min-height:100vh; padding:16px; }
.balance { background:linear-gradient(135deg,#667eea,#764ba2); padding:16px; border-radius:12px; text-align:center; margin-bottom:20px; }
.balance h1 { font-size:14px; opacity:.9; margin-bottom:4px; font-weight:normal; }
.balance .amount { font-size:32px; font-weight:bold; }
.games { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
.game { background:#16213e; border-radius:12px; padding:24px 12px; text-align:center; cursor:pointer; transition:transform .2s; border:1px solid #0f3460; }
.game:active { transform:scale(.95); }
.game .icon { font-size:40px; margin-bottom:8px; }
.game .name { font-size:14px; font-weight:600; }
.game .desc { font-size:11px; opacity:.6; margin-top:4px; }
.screen { display:none; }
.screen.active { display:block; }
.back { background:#0f3460; border:none; color:#fff; padding:10px 16px; border-radius:8px; font-size:14px; margin-bottom:16px; cursor:pointer; }
.bet-buttons { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:16px; }
.bet-btn { background:#0f3460; border:1px solid #667eea; color:#fff; padding:14px; border-radius:10px; font-size:16px; font-weight:600; cursor:pointer; }
.bet-btn:active { background:#667eea; }
.result { margin-top:20px; padding:20px; background:#16213e; border-radius:12px; text-align:center; font-size:18px; }
.big-btn { background:linear-gradient(135deg,#e94560,#c62a47); border:none; color:#fff; padding:16px; border-radius:10px; font-size:18px; font-weight:bold; width:100%; margin-top:16px; cursor:pointer; }
</style>
</head>
<body>

<div id="menu" class="screen active">
  <div class="balance">
    <h1>💰 Твой баланс</h1>
    <div class="amount"><span id="balance">100</span> ₽</div>
  </div>
  <div class="games">
    <div class="game" onclick="openGame('rocket')"><div class="icon">🚀</div><div class="name">Ракета</div><div class="desc">Успей забрать</div></div>
    <div class="game" onclick="openGame('plinko')"><div class="icon">🎲</div><div class="name">Плинко</div><div class="desc">До x10</div></div>
    <div class="game" onclick="openGame('mines')"><div class="icon">💣</div><div class="name">Мины</div><div class="desc">Не попадись</div></div>
    <div class="game" onclick="openGame('slots')"><div class="icon">🎰</div><div class="name">Слоты</div><div class="desc">Три в ряд</div></div>
  </div>
</div>

<div id="rocket" class="screen">
  <button class="back" onclick="goMenu()">← Назад</button>
  <h2>🚀 Ракета</h2>
  <div id="rocket-status" style="margin-top:20px;text-align:center;font-size:20px;">Выбери ставку</div>
  <div id="rocket-buttons" class="bet-buttons"></div>
  <button id="rocket-cashout" class="big-btn" style="display:none" onclick="cashoutRocket()">💸 Забрать</button>
</div>

<div id="plinko" class="screen">
  <button class="back" onclick="goMenu()">← Назад</button>
  <h2>🎲 Плинко</h2>
  <div id="plinko-status" style="margin-top:20px;text-align:center;font-size:20px;">Выбери ставку</div>
  <div id="plinko-buttons" class="bet-buttons"></div>
</div>

<div id="mines" class="screen">
  <button class="back" onclick="goMenu()">← Назад</button>
  <h2>💣 Мины</h2>
  <div id="mines-status" style="margin-top:20px;text-align:center;font-size:20px;">Выбери ставку</div>
  <div id="mines-buttons" class="bet-buttons"></div>
  <div id="mines-field" style="display:grid;grid-template-columns:repeat(5,1fr);gap:6px;margin-top:16px;"></div>
  <button id="mines-cashout" class="big-btn" style="display:none" onclick="cashoutMines()">💸 Забрать</button>
</div>

<div id="slots" class="screen">
  <button class="back" onclick="goMenu()">← Назад</button>
  <h2>🎰 Слоты</h2>
  <div id="slots-status" style="margin-top:20px;text-align:center;font-size:20px;">Выбери ставку</div>
  <div id="slots-buttons" class="bet-buttons"></div>
</div>

<script>
const tg = window.Telegram.WebApp;
tg.ready(); tg.expand();
const user = tg.initDataUnsafe?.user;
const BETS = [10, 50, 100, 500];

let balance = 100;
let rocketInterval = null;
let rocketMult = 1.0;
let rocketBet = 0;
let minesBet = 0;
let minesField = [];
let minesOpened = 0;
let minesMult = 1.0;

async function loadBalance() {
  if (!user) return;
  const r = await fetch(`/api/balance?user_id=${user.id}`);
  const d = await r.json();
  balance = d.balance;
  document.getElementById('balance').textContent = balance;
}

async function changeBalance(delta) {
  if (!user) return;
  const r = await fetch('/api/balance', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({user_id: user.id, delta})
  });
  const d = await r.json();
  balance = d.balance;
  document.getElementById('balance').textContent = balance;
}

function goMenu() {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById('menu').classList.add('active');
  if (rocketInterval) { clearInterval(rocketInterval); rocketInterval = null; }
}

function openGame(name) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById(name).classList.add('active');
  if (name === 'rocket') initRocket();
  if (name === 'plinko') initPlinko();
  if (name === 'mines') initMines();
  if (name === 'slots') initSlots();
}

function makeBetButtons(containerId, callback) {
  const c = document.getElementById(containerId);
  c.innerHTML = '';
  BETS.forEach(b => {
    const btn = document.createElement('button');
    btn.className = 'bet-btn';
    btn.textContent = b + ' ₽';
    btn.onclick = () => callback(b);
    c.appendChild(btn);
  });
}

// ---------- РАКЕТА ----------
function initRocket() {
  rocketBet = 0; rocketMult = 1.0;
  if (rocketInterval) { clearInterval(rocketInterval); rocketInterval = null; }
  document.getElementById('rocket-status').innerHTML = 'Выбери ставку';
  document.getElementById('rocket-cashout').style.display = 'none';
  makeBetButtons('rocket-buttons', startRocket);
}

async function startRocket(bet) {
  if (bet > balance) { tg.showAlert('Недостаточно средств'); return; }
  rocketBet = bet; rocketMult = 1.0;
  await changeBalance(-bet);
  document.getElementById('rocket-buttons').innerHTML = '';
  document.getElementById('rocket-cashout').style.display = 'block';
  document.getElementById('rocket-status').innerHTML = `🚀 x1.00<br>Ставка: ${bet} ₽`;
  rocketInterval = setInterval(() => {
    rocketMult = +(rocketMult + (0.1 + Math.random() * 0.4)).toFixed(2);
    if (Math.random() < rocketMult / 10) {
      clearInterval(rocketInterval); rocketInterval = null;
      document.getElementById('rocket-status').innerHTML = `💥 КРАХ!<br>Множитель: x${rocketMult.toFixed(2)}<br>Потеряно: ${rocketBet} ₽`;
      document.getElementById('rocket-cashout').style.display = 'none';
      setTimeout(initRocket, 2500);
      return;
    }
    document.getElementById('rocket-status').innerHTML = `🚀 x${rocketMult.toFixed(2)}<br>Потенциал: ${Math.floor(rocketBet * rocketMult)} ₽`;
  }, 1500);
}

async function cashoutRocket() {
  if (!rocketInterval) return;
  clearInterval(rocketInterval); rocketInterval = null;
  const win = Math.floor(rocketBet * rocketMult);
  await changeBalance(win);
  document.getElementById('rocket-cashout').style.display = 'none';
  document.getElementById('rocket-status').innerHTML = `✅ Забрал ${win} ₽ (x${rocketMult.toFixed(2)})`;
  setTimeout(initRocket, 2500);
}

// ---------- ПЛИНКО ----------
function initPlinko() {
  document.getElementById('plinko-status').innerHTML = 'Выбери ставку';
  makeBetButtons('plinko-buttons', playPlinko);
}

async function playPlinko(bet) {
  if (bet > balance) { tg.showAlert('Недостаточно средств'); return; }
  await changeBalance(-bet);
  const mults = [0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0];
  const weights = [30, 25, 20, 12, 8, 4, 1];
  let total = weights.reduce((a, b) => a + b, 0);
  let r = Math.random() * total;
  let mult = 0.5;
  for (let i = 0; i < mults.length; i++) { r -= weights[i]; if (r <= 0) { mult = mults[i]; break; } }
  const win = Math.floor(bet * mult);
  if (win > 0) await changeBalance(win);
  document.getElementById('plinko-status').innerHTML = `🎲 x${mult}<br>${bet} ₽ → ${win} ₽`;
}

// ---------- МИНЫ ----------
function initMines() {
  minesBet = 0; minesOpened = 0; minesMult = 1.0;
  document.getElementById('mines-status').innerHTML = 'Выбери ставку';
  document.getElementById('mines-field').innerHTML = '';
  document.getElementById('mines-cashout').style.display = 'none';
  makeBetButtons('mines-buttons', startMines);
}

async function startMines(bet) {
  if (bet > balance) { tg.showAlert('Недостаточно средств'); return; }
  minesBet = bet; minesOpened = 0; minesMult = 1.0;
  await changeBalance(-bet);
  minesField = Array(20).fill('💎').concat(Array(5).fill('💣'));
  for (let i = minesField.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [minesField[i], minesField[j]] = [minesField[j], minesField[i]];
  }
  document.getElementById('mines-buttons').innerHTML = '';
  document.getElementById('mines-cashout').style.display = 'block';
  renderMines();
  document.getElementById('mines-status').innerHTML = `💣 Множитель: x${minesMult.toFixed(2)}`;
}

function renderMines() {
  const f = document.getElementById('mines-field');
  f.innerHTML = '';
  minesField.forEach((cell, i) => {
    const btn = document.createElement('button');
    btn.className = 'bet-btn';
    btn.style.padding = '14px 0';
    btn.textContent = cell === '?' ? '⬜' : cell;
    btn.disabled = cell !== '?';
    btn.onclick = () => openMine(i);
    f.appendChild(btn);
  });
}

async function openMine(i) {
  if (minesField[i] !== '?') return;
  if (minesField[i] === undefined) return;
  const real = minesField[i];
  if (real === '💣') {
    minesField[i] = '💣';
    document.getElementById('mines-field').children[i].textContent = '💣';
    document.getElementById('mines-status').innerHTML = `💥 БУМ!<br>Потеряно: ${minesBet} ₽`;
    document.getElementById('mines-cashout').style.display = 'none';
    setTimeout(initMines, 2500);
    return;
  }
  minesField[i] = '💎';
  minesOpened++;
  minesMult = +(1.0 + minesOpened * 0.3).toFixed(2);
  document.getElementById('mines-field').children[i].textContent = '💎';
  document.getElementById('mines-field').children[i].disabled = true;
  document.getElementById('mines-status').innerHTML = `💎 x${minesMult.toFixed(2)}<br>Потенциал: ${Math.floor(minesBet * minesMult)} ₽`;
}

async function cashoutMines() {
  const win = Math.floor(minesBet * minesMult);
  await changeBalance(win);
  document.getElementById('mines-status').innerHTML = `✅ Забрал ${win} ₽ (x${minesMult.toFixed(2)})`;
  document.getElementById('mines-cashout').style.display = 'none';
  setTimeout(initMines, 2500);
}

// ---------- СЛОТЫ ----------
function initSlots() {
  document.getElementById('slots-status').innerHTML = 'Выбери ставку';
  makeBetButtons('slots-buttons', playSlots);
}

async function playSlots(bet) {
  if (bet > balance) { tg.showAlert('Недостаточно средств'); return; }
  await changeBalance(-bet);
  const s = ['🍒','🍋','🍊','💎','7️⃣'];
  const r = [s[Math.floor(Math.random()*5)], s[Math.floor(Math.random()*5)], s[Math.floor(Math.random()*5)]];
  let mult = 0;
  if (r[0]===r[1] && r[1]===r[2]) mult = r[0]==='7️⃣' ? 10 : 5;
  else if (r[0]===r[1] || r[1]===r[2]) mult = 2;
  const win = Math.floor(bet * mult);
  if (win > 0) await changeBalance(win);
  let msg = `🎰 ${r[0]} | ${r[1]} | ${r[2]}<br>`;
  msg += mult ? `✅ +${win} ₽ (x${mult})` : '😢 Не повезло';
  document.getElementById('slots-status').innerHTML = msg;
}

// ---------- ИНИЦИАЛИЗАЦИЯ ----------
loadBalance();
</script>
</body>
</html>
"""

# ---------- ВЕБ-СЕРВЕР ----------
async def handle_index(request):
    return web.Response(text=HTML_PAGE, content_type="text/html")

async def handle_get_balance(request):
    user_id = request.query.get("user_id")
    if not user_id:
        return web.json_response({"error": "no user_id"}, status=400)
    return web.json_response({"balance": get_balance(int(user_id))})

async def handle_post_balance(request):
    data = await request.json()
    user_id = int(data["user_id"])
    delta = int(data["delta"])
    new_balance = update_balance(user_id, delta)
    return web.json_response({"balance": new_balance})

app = web.Application()
app.router.add_get("/", handle_index)
app.router.add_get("/api/balance", handle_get_balance)
app.router.add_post("/api/balance", handle_post_balance)

# ---------- БОТ ----------
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    get_balance(message.from_user.id)  # создаём запись с 100 руб
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 Открыть Казино", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    await message.answer(
        "🎰 <b>Добро пожаловать в Казино!</b>\n\n"
        "Нажми кнопку ниже, чтобы играть:",
        reply_markup=kb,
        parse_mode="HTML"
    )

# ---------- ЗАПУСК ----------
async def start_web():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"✅ Web server on port {PORT}")

async def main():
    await start_web()
    print("🤖 Bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
