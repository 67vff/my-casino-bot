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
    db[str(user_id)] = max(0, amount)
    save_db(db)

def update_balance(user_id: int, delta: int):
    new = max(0, get_balance(user_id) + delta)
    set_balance(user_id, new)
    return new

HTML_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>🎰 Казино</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
* { margin:0; padding:0; box-sizing:border-box; -webkit-tap-highlight-color:transparent; font-family:-apple-system,BlinkMacSystemFont,sans-serif; }
body { background:#0f0f1e; color:#fff; min-height:100vh; padding:16px; overflow-x:hidden; }
.balance { background:linear-gradient(135deg,#667eea,#764ba2); padding:14px; border-radius:14px; text-align:center; margin-bottom:16px; }
.balance h1 { font-size:13px; opacity:.9; font-weight:normal; }
.balance .amount { font-size:30px; font-weight:bold; margin-top:2px; }
.games { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
.game { background:#1a1a2e; border-radius:14px; padding:20px 10px; text-align:center; cursor:pointer; border:1px solid #2a2a4a; transition:transform .15s; }
.game:active { transform:scale(.95); }
.game .icon { font-size:36px; margin-bottom:6px; }
.game .name { font-size:13px; font-weight:600; }
.game .desc { font-size:10px; opacity:.6; margin-top:2px; }
.screen { display:none; }
.screen.active { display:block; animation:fadeIn .3s; }
@keyframes fadeIn { from{opacity:0} to{opacity:1} }
.back { background:#1a1a2e; border:1px solid #2a2a4a; color:#fff; padding:10px 16px; border-radius:10px; font-size:14px; margin-bottom:16px; cursor:pointer; }
h2 { font-size:20px; margin-bottom:16px; text-align:center; }
.bet-buttons { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:16px; }
.bet-btn { background:#1a1a2e; border:1px solid #667eea; color:#fff; padding:14px; border-radius:12px; font-size:16px; font-weight:600; cursor:pointer; }
.bet-btn:active { background:#667eea; }
.bet-btn:disabled { opacity:.5; }
.big-btn { background:linear-gradient(135deg,#e94560,#c62a47); border:none; color:#fff; padding:16px; border-radius:12px; font-size:18px; font-weight:bold; width:100%; margin-top:16px; cursor:pointer; }
.big-btn:active { transform:scale(.97); }

/* РАКЕТА */
.rocket-area { position:relative; height:280px; background:linear-gradient(180deg,#0a0a1e,#1a1a3e); border-radius:14px; overflow:hidden; margin-top:12px; }
.rocket { position:absolute; font-size:40px; bottom:20px; left:50%; transform:translateX(-50%); transition:bottom .1s; }
.rocket.flying { animation:fly .5s infinite alternate; }
@keyframes fly { from{transform:translateX(-50%) rotate(-5deg)} to{transform:translateX(-50%) rotate(5deg)} }
.rocket-mult { position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); font-size:44px; font-weight:bold; color:#4ade80; text-shadow:0 0 20px #4ade80; }
.rocket-mult.crashed { color:#e94560; text-shadow:0 0 20px #e94560; animation:shake .3s; }
@keyframes shake { 0%,100%{transform:translate(-50%,-50%)} 25%{transform:translate(-55%,-50%)} 75%{transform:translate(-45%,-50%)} }
.stars { position:absolute; width:100%; height:100%; }

/* СЛОТЫ */
.slots { display:flex; justify-content:center; gap:10px; margin:20px 0; }
.slot { width:80px; height:100px; background:#1a1a2e; border:2px solid #667eea; border-radius:14px; display:flex; align-items:center; justify-content:center; font-size:48px; }
.slot.spinning { animation:spin .1s infinite; }
@keyframes spin { 0%{transform:translateY(-5px)} 50%{transform:translateY(5px)} 100%{transform:translateY(-5px)} }

/* ПЛИНКО */
.plinko-area { position:relative; height:320px; background:#0a0a1e; border-radius:14px; overflow:hidden; margin-top:12px; }
.peg { position:absolute; width:8px; height:8px; background:#667eea; border-radius:50%; box-shadow:0 0 8px #667eea; }
.ball { position:absolute; width:14px; height:14px; background:#fbbf24; border-radius:50%; box-shadow:0 0 12px #fbbf24; transition:all .1s linear; }
.slots-bottom { position:absolute; bottom:0; width:100%; display:flex; }
.slot-bottom { flex:1; text-align:center; font-size:11px; padding:6px 0; color:#fff; }

/* РУЛЕТКА */
.wheel-container { position:relative; width:260px; height:260px; margin:20px auto; }
.wheel { width:100%; height:100%; border-radius:50%; border:6px solid #667eea; position:relative; transition:transform 3s cubic-bezier(.2,.8,.3,1); }
.wheel-seg { position:absolute; width:50%; height:50%; top:0; left:50%; transform-origin:0% 100%; }
.wheel-num { position:absolute; font-size:12px; font-weight:bold; }
.pointer { position:absolute; top:-10px; left:50%; transform:translateX(-50%); font-size:24px; color:#e94560; z-index:10; }
</style>
</head>
<body>

<!-- МЕНЮ -->
<div id="menu" class="screen active">
  <div class="balance">
    <h1>💰 Твой баланс</h1>
    <div class="amount"><span id="balance">100</span> ₽</div>
  </div>
  <div class="games">
    <div class="game" onclick="openGame('rocket')"><div class="icon">🚀</div><div class="name">Ракета</div><div class="desc">Успей забрать</div></div>
    <div class="game" onclick="openGame('slots')"><div class="icon">🎰</div><div class="name">Слоты</div><div class="desc">Три в ряд</div></div>
    <div class="game" onclick="openGame('plinko')"><div class="icon">🎲</div><div class="name">Плинко</div><div class="desc">Шарик и множитель</div></div>
    <div class="game" onclick="openGame('wheel')"><div class="icon">🎡</div><div class="name">Рулетка</div><div class="desc">Крути колесо</div></div>
  </div>
</div>

<!-- РАКЕТА -->
<div id="rocket" class="screen">
  <button class="back" onclick="goMenu()">← Назад</button>
  <h2>🚀 Ракета</h2>
  <div class="rocket-area">
    <div class="rocket" id="rocket-emoji">🚀</div>
    <div class="rocket-mult" id="rocket-mult">x1.00</div>
  </div>
  <div id="rocket-status" style="text-align:center;margin-top:12px;font-size:15px;">Выбери ставку</div>
  <div id="rocket-buttons" class="bet-buttons"></div>
  <button id="rocket-cashout" class="big-btn" style="display:none" onclick="cashoutRocket()">💸 Забрать</button>
</div>

<!-- СЛОТЫ -->
<div id="slots" class="screen">
  <button class="back" onclick="goMenu()">← Назад</button>
  <h2>🎰 Слоты</h2>
  <div class="slots">
    <div class="slot" id="slot0">🍒</div>
    <div class="slot" id="slot1">🍒</div>
    <div class="slot" id="slot2">🍒</div>
  </div>
  <div id="slots-status" style="text-align:center;font-size:15px;min-height:40px;">Выбери ставку</div>
  <div id="slots-buttons" class="bet-buttons"></div>
</div>

<!-- ПЛИНКО -->
<div id="plinko" class="screen">
  <button class="back" onclick="goMenu()">← Назад</button>
  <h2>🎲 Плинко</h2>
  <div class="plinko-area" id="plinko-area">
    <div class="slots-bottom" id="plinko-bottom"></div>
  </div>
  <div id="plinko-status" style="text-align:center;margin-top:12px;font-size:15px;">Выбери ставку</div>
  <div id="plinko-buttons" class="bet-buttons"></div>
</div>

<!-- РУЛЕТКА -->
<div id="wheel" class="screen">
  <button class="back" onclick="goMenu()">← Назад</button>
  <h2>🎡 Рулетка</h2>
  <div class="wheel-container">
    <div class="pointer">▼</div>
    <div class="wheel" id="wheel-el"></div>
  </div>
  <div id="wheel-status" style="text-align:center;font-size:15px;min-height:40px;">Выбери ставку</div>
  <div id="wheel-buttons" class="bet-buttons"></div>
</div>

<script>
const tg = window.Telegram.WebApp;
tg.ready(); tg.expand();
const user = tg.initDataUnsafe?.user;
const BETS = [10, 50, 100, 500];
let balance = 100;
let rocketInterval = null, rocketMult = 1.0, rocketBet = 0;

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
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({user_id:user.id, delta})
  });
  const d = await r.json();
  balance = d.balance;
  document.getElementById('balance').textContent = balance;
}
function goMenu() {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById('menu').classList.add('active');
  if (rocketInterval) { clearInterval(rocketInterval); rocketInterval = null; }
  document.getElementById('rocket-emoji').classList.remove('flying');
}
function openGame(name) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById(name).classList.add('active');
  if (name==='rocket') initRocket();
  if (name==='slots') initSlots();
  if (name==='plinko') initPlinko();
  if (name==='wheel') initWheel();
}
function makeBetButtons(id, cb) {
  const c = document.getElementById(id);
  c.innerHTML = '';
  BETS.forEach(b => {
    const btn = document.createElement('button');
    btn.className = 'bet-btn';
    btn.textContent = b + ' ₽';
    btn.onclick = () => cb(b);
    c.appendChild(btn);
  });
}

// ===== РАКЕТА =====
function initRocket() {
  if (rocketInterval) { clearInterval(rocketInterval); rocketInterval = null; }
  rocketBet = 0; rocketMult = 1.0;
  document.getElementById('rocket-mult').textContent = 'x1.00';
  document.getElementById('rocket-mult').classList.remove('crashed');
  document.getElementById('rocket-emoji').style.bottom = '20px';
  document.getElementById('rocket-emoji').classList.remove('flying');
  document.getElementById('rocket-status').textContent = 'Выбери ставку';
  document.getElementById('rocket-cashout').style.display = 'none';
  makeBetButtons('rocket-buttons', startRocket);
}
async function startRocket(bet) {
  if (bet > balance) { tg.showAlert('Недостаточно средств'); return; }
  rocketBet = bet; rocketMult = 1.0;
  await changeBalance(-bet);
  document.getElementById('rocket-buttons').innerHTML = '';
  document.getElementById('rocket-cashout').style.display = 'block';
  document.getElementById('rocket-emoji').classList.add('flying');
  document.getElementById('rocket-status').textContent = `Ставка: ${bet} ₽`;
  rocketInterval = setInterval(() => {
    rocketMult = +(rocketMult + (0.08 + Math.random()*0.3)).toFixed(2);
    document.getElementById('rocket-mult').textContent = 'x' + rocketMult.toFixed(2);
    // ракета летит вверх
    const bottom = Math.min(240, 20 + (rocketMult-1)*40);
    document.getElementById('rocket-emoji').style.bottom = bottom + 'px';
    // шанс краха
    if (Math.random() < rocketMult / 12) {
      clearInterval(rocketInterval); rocketInterval = null;
      document.getElementById('rocket-mult').textContent = '💥 x' + rocketMult.toFixed(2);
      document.getElementById('rocket-mult').classList.add('crashed');
      document.getElementById('rocket-emoji').classList.remove('flying');
      document.getElementById('rocket-emoji').textContent = '💥';
      document.getElementById('rocket-status').textContent = `Потеряно: ${rocketBet} ₽`;
      document.getElementById('rocket-cashout').style.display = 'none';
      setTimeout(() => { document.getElementById('rocket-emoji').textContent = '🚀'; initRocket(); }, 2500);
      return;
    }
    document.getElementById('rocket-status').textContent = `Потенциал: ${Math.floor(rocketBet*rocketMult)} ₽`;
  }, 400);
}
async function cashoutRocket() {
  if (!rocketInterval) return;
  clearInterval(rocketInterval); rocketInterval = null;
  const win = Math.floor(rocketBet * rocketMult);
  await changeBalance(win);
  document.getElementById('rocket-cashout').style.display = 'none';
  document.getElementById('rocket-emoji').classList.remove('flying');
  document.getElementById('rocket-status').textContent = `✅ Забрал ${win} ₽ (x${rocketMult.toFixed(2)})`;
  setTimeout(initRocket, 2500);
}

// ===== СЛОТЫ =====
function initSlots() {
  document.getElementById('slots-status').textContent = 'Выбери ставку';
  makeBetButtons('slots-buttons', playSlots);
}
async function playSlots(bet) {
  if (bet > balance) { tg.showAlert('Недостаточно средств'); return; }
  await changeBalance(-bet);
  const symbols = ['🍒','🍋','🍊','💎','7️⃣'];
  document.getElementById('slots-buttons').innerHTML = '';
  document.getElementById('slots-status').textContent = 'Крутим...';
  for (let i = 0; i < 3; i++) document.getElementById('slot'+i).classList.add('spinning');
  const final = [symbols[Math.floor(Math.random()*5)], symbols[Math.floor(Math.random()*5)], symbols[Math.floor(Math.random()*5)]];
  // останавливаем по одному с задержкой
  for (let i = 0; i < 3; i++) {
    await new Promise(r => setTimeout(r, 700 + i*500));
    document.getElementById('slot'+i).classList.remove('spinning');
    document.getElementById('slot'+i).textContent = final[i];
  }
  let mult = 0;
  if (final[0]===final[1] && final[1]===final[2]) mult = final[0]==='7️⃣' ? 10 : 5;
  else if (final[0]===final[1] || final[1]===final[2]) mult = 2;
  const win = Math.floor(bet * mult);
  if (win > 0) await changeBalance(win);
  document.getElementById('slots-status').innerHTML = mult
    ? `🎉 Выигрыш: <b>+${win} ₽</b> (x${mult})`
    : '😢 Не повезло';
  setTimeout(initSlots, 2500);
}

// ===== ПЛИНКО =====
function initPlinko() {
  const area = document.getElementById('plinko-area');
  // очищаем всё кроме bottom
  area.querySelectorAll('.peg, .ball').forEach(e => e.remove());
  // рисуем колышки
  const rows = 7;
  for (let r = 0; r < rows; r++) {
    const count = r + 3;
    for (let i = 0; i < count; i++) {
      const peg = document.createElement('div');
      peg.className = 'peg';
      peg.style.top = (40 + r*40) + 'px';
      peg.style.left = `calc(50% + ${(i - (count-1)/2) * 34}px)`;
      area.appendChild(peg);
    }
  }
  // множители внизу
  const mults = [0.5, 1, 1.5, 2, 3, 5, 10, 3, 2, 1.5, 1, 0.5];
  const bottom = document.getElementById('plinko-bottom');
  bottom.innerHTML = '';
  mults.forEach(m => {
    const d = document.createElement('div');
    d.className = 'slot-bottom';
    d.textContent = 'x' + m;
    d.style.background = m >= 3 ? '#e94560' : (m >= 1.5 ? '#f59e0b' : '#374151');
    bottom.appendChild(d);
  });
  document.getElementById('plinko-status').textContent = 'Выбери ставку';
  makeBetButtons('plinko-buttons', playPlinko);
}
async function playPlinko(bet) {
  if (bet > balance) { tg.showAlert('Недостаточно средств'); return; }
  await changeBalance(-bet);
  document.getElementById('plinko-buttons').innerHTML = '';
  document.getElementById('plinko-status').textContent = 'Шарик падает...';
  const area = document.getElementById('plinko-area');
  const ball = document.createElement('div');
  ball.className = 'ball';
  ball.style.left = 'calc(50% - 7px)';
  ball.style.top = '10px';
  area.appendChild(ball);
  // выбираем финальную позицию
  const mults = [0.5, 1, 1.5, 2, 3, 5, 10, 3, 2, 1.5, 1, 0.5];
  const weights = [20, 20, 15, 12, 8, 4, 1, 4, 8, 12, 15, 20];
  let total = weights.reduce((a,b)=>a+b,0);
  let rnd = Math.random()*total, idx = 0;
  for (let i = 0; i < weights.length; i++) { rnd -= weights[i]; if (rnd <= 0) { idx = i; break; } }
  const finalX = (idx / (mults.length-1)) * 100;
  // анимация: плавное движение вниз с "зигзагом"
  const steps = 20;
  for (let s = 1; s <= steps; s++) {
    await new Promise(r => setTimeout(r, 60));
    const y = 10 + (s / steps) * (area.clientHeight - 40);
    const x = 50 + (finalX - 50) * (s / steps) + (Math.random()-0.5) * 10;
    ball.style.top = y + 'px';
    ball.style.left = `calc(${x}% - 7px)`;
  }
  ball.remove();
  const mult = mults[idx];
  const win = Math.floor(bet * mult);
  if (win > 0) await changeBalance(win);
  document.getElementById('plinko-status').innerHTML = `🎲 Множитель <b>x${mult}</b><br>${bet} ₽ → <b>${win} ₽</b>`;
  setTimeout(initPlinko, 3000);
}

// ===== РУЛЕТКА =====
function initWheel() {
  const wheel = document.getElementById('wheel-el');
  wheel.style.transform = 'rotate(0deg)';
  wheel.innerHTML = '';
  const segs = 12;
  const colors = ['#e94560','#1a1a2e','#f59e0b','#1a1a2e','#4ade80','#1a1a2e','#667eea','#1a1a2e','#e94560','#1a1a2e','#f59e0b','#1a1a2e'];
  const mults = [2,0,5,0,3,0,10,0,2,0,5,0];
  segs && mults.forEach((m,i) => {
    const seg = document.createElement('div');
    seg.style.cssText = `position:absolute;width:50%;height:50%;top:0;left:50%;transform-origin:0% 100%;transform:rotate(${i*30}deg);background:${colors[i]};clip-path:polygon(0 0,100% 0,0 100%);`;
    wheel.appendChild(seg);
    const num = document.createElement('div');
    num.style.cssText = `position:absolute;top:20px;left:50%;transform:translateX(-50%) rotate(${i*30+15}deg);font-size:14px;font-weight:bold;color:#fff;`;
    num.textContent = 'x' + m;
    seg.appendChild(num);
  });
  document.getElementById('wheel-status').textContent = 'Выбери ставку';
  makeBetButtons('wheel-buttons', playWheel);
}
async function playWheel(bet) {
  if (bet > balance) { tg.showAlert('Недостаточно средств'); return; }
  await changeBalance(-bet);
  document.getElementById('wheel-buttons').innerHTML = '';
  document.getElementById('wheel-status').textContent = 'Крутим...';
  const mults = [2,0,5,0,3,0,10,0,2,0,5,0];
  const idx = Math.floor(Math.random()*12);
  const mult = mults[idx];
  const wheel = document.getElementById('wheel-el');
  const targetDeg = 360*5 + (360 - idx*30);
  wheel.style.transform = `rotate(${targetDeg}deg)`;
  await new Promise(r => setTimeout(r, 3200));
  const win = Math.floor(bet * mult);
  if (win > 0) await changeBalance(win);
  document.getElementById('wheel-status').innerHTML = mult
    ? `🎉 Выпало <b>x${mult}</b> → <b>+${win} ₽</b>`
    : '😢 Мимо';
  setTimeout(initWheel, 3000);
}

loadBalance();
</script>
</body>
</html>
"""

async def handle_index(request):
    return web.Response(text=HTML_PAGE, content_type="text/html")

async def handle_get_balance(request):
    user_id = request.query.get("user_id")
    if not user_id:
        return web.json_response({"error":"no user_id"}, status=400)
    return web.json_response({"balance": get_balance(int(user_id))})

async def handle_post_balance(request):
    data = await request.json()
    user_id = int(data["user_id"])
    delta = int(data["delta"])
    return web.json_response({"balance": update_balance(user_id, delta)})

app = web.Application()
app.router.add_get("/", handle_index)
app.router.add_get("/api/balance", handle_get_balance)
app.router.add_post("/api/balance", handle_post_balance)

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    get_balance(message.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 Открыть Казино", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    await message.answer("🎰 <b>Добро пожаловать в Казино!</b>\n\nНажми кнопку ниже:", reply_markup=kb, parse_mode="HTML")

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
