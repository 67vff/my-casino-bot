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

# ---------- БАЗА ----------
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False)

def get_user(user_id):
    db = load_db()
    uid = str(user_id)
    if uid not in db:
        db[uid] = {"balance": 10000, "inventory": []}
        save_db(db)
    else:
        # Миграция старого формата (число) в новый (словарь)
        if not isinstance(db[uid], dict):
            try:
                old_balance = int(db[uid])
            except Exception:
                old_balance = 10000
            db[uid] = {"balance": old_balance, "inventory": []}
            save_db(db)
        elif "inventory" not in db[uid]:
            db[uid]["inventory"] = []
            save_db(db)
        elif "balance" not in db[uid]:
            db[uid]["balance"] = 10000
            save_db(db)
    return db[uid]

def save_user(user_id, data):
    db = load_db()
    db[str(user_id)] = data
    save_db(db)

def get_balance(user_id):
    return get_user(user_id)["balance"]

def update_balance(user_id, delta):
    u = get_user(user_id)
    u["balance"] = max(0, u["balance"] + delta)
    save_user(user_id, u)
    return u["balance"]

GIFTS = {
    "1": {"name": "🐻 Мишка", "price": 5000, "emoji": "🐻"},
    "2": {"name": "💎 Алмаз", "price": 15000, "emoji": "💎"},
    "3": {"name": "🎁 Подарок", "price": 3000, "emoji": "🎁"},
    "4": {"name": "🏆 Кубок", "price": 25000, "emoji": "🏆"},
    "5": {"name": "👑 Корона", "price": 50000, "emoji": "👑"},
    "6": {"name": "🚀 Ракета-NFT", "price": 100000, "emoji": "🚀"},
}

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
body { background:#0a0a1a; color:#fff; min-height:100vh; padding:16px; overflow-x:hidden; }
.balance { background:linear-gradient(135deg,#667eea,#764ba2); padding:14px; border-radius:16px; text-align:center; margin-bottom:16px; box-shadow:0 4px 20px rgba(102,126,234,.4); }
.balance h1 { font-size:12px; opacity:.9; font-weight:normal; letter-spacing:1px; }
.balance .amount { font-size:30px; font-weight:800; margin-top:2px; }
.balance .coins { font-size:12px; opacity:.85; margin-top:2px; }
.games { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
.game { background:linear-gradient(135deg,#1a1a2e,#16162a); border-radius:16px; padding:20px 10px; text-align:center; cursor:pointer; border:1px solid #2a2a4a; transition:transform .15s; }
.game:active { transform:scale(.95); }
.game .icon { font-size:38px; margin-bottom:6px; }
.game .name { font-size:13px; font-weight:700; }
.game .desc { font-size:10px; opacity:.5; margin-top:3px; }
.screen { display:none; }
.screen.active { display:block; animation:fadeIn .3s; }
@keyframes fadeIn { from{opacity:0; transform:translateY(10px)} to{opacity:1; transform:translateY(0)} }
.back { background:#1a1a2e; border:1px solid #2a2a4a; color:#fff; padding:10px 16px; border-radius:12px; font-size:14px; margin-bottom:16px; cursor:pointer; }
h2 { font-size:20px; margin-bottom:16px; text-align:center; font-weight:800; }
.bet-buttons { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:16px; }
.bet-btn { background:linear-gradient(135deg,#1a1a2e,#252547); border:1px solid #667eea; color:#fff; padding:14px; border-radius:12px; font-size:16px; font-weight:700; cursor:pointer; }
.bet-btn:active { background:#667eea; }
.big-btn { background:linear-gradient(135deg,#e94560,#c62a47); border:none; color:#fff; padding:16px; border-radius:14px; font-size:18px; font-weight:800; width:100%; margin-top:16px; cursor:pointer; box-shadow:0 4px 20px rgba(233,69,96,.4); }
.big-btn:active { transform:scale(.97); }

.rocket-area { position:relative; height:400px; background:linear-gradient(180deg,#000010 0%,#0a0a2a 50%,#1a1a3e 100%); border-radius:16px; overflow:hidden; margin-top:12px; border:1px solid #2a2a4a; }
.star { position:absolute; background:#fff; border-radius:50%; opacity:.6; animation:twinkle 2s infinite; }
@keyframes twinkle { 0%,100%{opacity:.2} 50%{opacity:.9} }
.rocket-ship { position:absolute; font-size:44px; left:50%; transform:translateX(-50%); filter:drop-shadow(0 0 15px #fbbf24); transition:bottom .15s linear; z-index:5; }
.rocket-ship.flying { animation:shake .15s infinite; }
@keyframes shake { 0%,100%{transform:translateX(-52%) rotate(-2deg)} 50%{transform:translateX(-48%) rotate(2deg)} }
.rocket-mult { position:absolute; top:40%; left:50%; transform:translate(-50%,-50%); font-size:52px; font-weight:900; color:#4ade80; text-shadow:0 0 30px #4ade80; z-index:10; }
.rocket-mult.crashed { color:#e94560; text-shadow:0 0 30px #e94560; animation:shake2 .4s; }
@keyframes shake2 { 0%,100%{transform:translate(-50%,-50%)} 25%{transform:translate(-55%,-50%)} 75%{transform:translate(-45%,-50%)} }
.station { position:absolute; top:20px; left:50%; transform:translateX(-50%); font-size:56px; filter:drop-shadow(0 0 20px #4ade80); animation:float 2s infinite; }
@keyframes float { 0%,100%{transform:translateX(-50%) translateY(0)} 50%{transform:translateX(-50%) translateY(-5px)} }
.spring { position:absolute; font-size:28px; animation:spring-pulse 1s infinite; }
@keyframes spring-pulse { 0%,100%{transform:scale(1)} 50%{transform:scale(1.3)} }
.timer { position:absolute; top:10px; right:14px; font-size:14px; color:#fbbf24; font-weight:800; z-index:6; background:rgba(0,0,0,.5); padding:4px 10px; border-radius:8px; }
.trail { position:absolute; width:5px; height:5px; background:#fbbf24; border-radius:50%; opacity:.6; pointer-events:none; }

.slots { display:flex; justify-content:center; gap:8px; margin:20px 0; }
.slot { width:80px; height:110px; background:linear-gradient(180deg,#1a1a2e,#0f0f1e); border:2px solid #667eea; border-radius:14px; display:flex; align-items:center; justify-content:center; font-size:52px; box-shadow:inset 0 0 20px rgba(102,126,234,.3); }
.slot.spinning { animation:spin .1s infinite; }
@keyframes spin { 0%{transform:translateY(-6px)} 50%{transform:translateY(6px)} 100%{transform:translateY(-6px)} }

.plinko-area { position:relative; height:340px; background:#0a0a1e; border-radius:16px; overflow:hidden; margin-top:12px; border:1px solid #2a2a4a; }
.peg { position:absolute; width:9px; height:9px; background:#667eea; border-radius:50%; box-shadow:0 0 10px #667eea; }
.ball { position:absolute; width:16px; height:16px; background:#fbbf24; border-radius:50%; box-shadow:0 0 15px #fbbf24; transition:all .08s linear; z-index:5; }
.slots-bottom { position:absolute; bottom:0; width:100%; display:flex; }

.wheel-wrap { position:relative; width:280px; height:280px; margin:20px auto; }
.wheel { width:100%; height:100%; border-radius:50%; border:8px solid #667eea; position:relative; transition:transform 4s cubic-bezier(.17,.67,.3,1); box-shadow:0 0 40px rgba(102,126,234,.5); overflow:hidden; }
.wheel-seg { position:absolute; width:50%; height:50%; top:0; left:50%; transform-origin:0% 100%; border-left:1px solid rgba(255,255,255,.15); }
.wheel-num { position:absolute; font-size:13px; font-weight:900; color:#fff; text-shadow:0 0 4px #000; }
.pointer { position:absolute; top:-14px; left:50%; transform:translateX(-50%); font-size:30px; color:#e94560; z-index:10; filter:drop-shadow(0 0 8px #e94560); }

.inv-grid { display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-top:12px; }
.inv-item { background:linear-gradient(135deg,#1a1a2e,#252547); border-radius:14px; padding:16px; text-align:center; border:1px solid #2a2a4a; }
.inv-item .emoji { font-size:40px; }
.inv-item .name { font-size:13px; font-weight:700; margin-top:6px; }
.inv-item .price { font-size:12px; color:#4ade80; margin-top:4px; }
.sell-btn { background:#e94560; border:none; color:#fff; padding:8px 16px; border-radius:10px; margin-top:8px; font-size:13px; font-weight:700; cursor:pointer; }
.shop-item { background:linear-gradient(135deg,#1a1a2e,#252547); border-radius:14px; padding:16px; text-align:center; border:1px solid #2a2a4a; margin-bottom:10px; }
</style>
</head>
<body>

<div id="menu" class="screen active">
  <div class="balance">
    <h1>💰 БАЛАНС</h1>
    <div class="amount"><span id="balance">100.00</span> ₽</div>
    <div class="coins" id="coins">= 10000 копеек</div>
  </div>
  <div class="games">
    <div class="game" onclick="openGame('rocket')"><div class="icon">🚀</div><div class="name">Ракета</div><div class="desc">Долети до станции</div></div>
    <div class="game" onclick="openGame('slots')"><div class="icon">🎰</div><div class="name">Слоты</div><div class="desc">Три в ряд</div></div>
    <div class="game" onclick="openGame('plinko')"><div class="icon">🎲</div><div class="name">Плинко</div><div class="desc">Шарик и множитель</div></div>
    <div class="game" onclick="openGame('wheel')"><div class="icon">🎡</div><div class="name">Рулетка</div><div class="desc">Крути колесо</div></div>
    <div class="game" onclick="openGame('inventory')"><div class="icon">🎒</div><div class="name">Инвентарь</div><div class="desc">Твои подарки</div></div>
    <div class="game" onclick="openGame('shop')"><div class="icon">🛒</div><div class="name">Магазин</div><div class="desc">Купить подарок</div></div>
  </div>
</div>

<div id="rocket" class="screen">
  <button class="back" onclick="goMenu()">← Назад</button>
  <h2>🚀 Ракета до станции</h2>
  <div class="rocket-area" id="rocket-area">
    <div class="timer" id="rocket-timer">⏱ 10.0s</div>
    <div class="station">🛸</div>
    <div class="rocket-ship" id="rocket-ship">🚀</div>
    <div class="rocket-mult" id="rocket-mult">x1.00</div>
  </div>
  <div id="rocket-status" style="text-align:center;margin-top:12px;font-size:14px;">Выбери ставку</div>
  <div id="rocket-buttons" class="bet-buttons"></div>
  <button id="rocket-cashout" class="big-btn" style="display:none" onclick="cashoutRocket()">💸 Забрать</button>
</div>

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

<div id="plinko" class="screen">
  <button class="back" onclick="goMenu()">← Назад</button>
  <h2>🎲 Плинко</h2>
  <div class="plinko-area" id="plinko-area">
    <div class="slots-bottom" id="plinko-bottom"></div>
  </div>
  <div id="plinko-status" style="text-align:center;margin-top:12px;font-size:15px;">Выбери ставку</div>
  <div id="plinko-buttons" class="bet-buttons"></div>
</div>

<div id="wheel" class="screen">
  <button class="back" onclick="goMenu()">← Назад</button>
  <h2>🎡 Рулетка</h2>
  <div class="wheel-wrap">
    <div class="pointer">▼</div>
    <div class="wheel" id="wheel-el"></div>
  </div>
  <div id="wheel-status" style="text-align:center;font-size:15px;min-height:40px;">Выбери ставку</div>
  <div id="wheel-buttons" class="bet-buttons"></div>
</div>

<div id="inventory" class="screen">
  <button class="back" onclick="goMenu()">← Назад</button>
  <h2>🎒 Инвентарь</h2>
  <div id="inv-list" class="inv-grid"></div>
</div>

<div id="shop" class="screen">
  <button class="back" onclick="goMenu()">← Назад</button>
  <h2>🛒 Магазин подарков</h2>
  <div id="shop-list"></div>
</div>

<script>
const tg = window.Telegram.WebApp;
tg.ready(); tg.expand();
const user = tg.initDataUnsafe?.user;
const BETS = [100, 500, 1000, 5000];
let balance = 10000;
let inventory = [];
let rocketInterval = null, rocketMult = 1.0, rocketBet = 0, rocketTimer = 0, rocketSprings = 0;

const GIFTS = {
  "1": {name:"🐻 Мишка", price:5000, emoji:"🐻"},
  "2": {name:"💎 Алмаз", price:15000, emoji:"💎"},
  "3": {name:"🎁 Подарок", price:3000, emoji:"🎁"},
  "4": {name:"🏆 Кубок", price:25000, emoji:"🏆"},
  "5": {name:"👑 Корона", price:50000, emoji:"👑"},
  "6": {name:"🚀 Ракета-NFT", price:100000, emoji:"🚀"},
};

function fmt(kop) { return (kop / 100).toFixed(2); }

async function loadBalance() {
  if (!user) return;
  try {
    const r = await fetch(`/api/balance?user_id=${user.id}`);
    const d = await r.json();
    balance = d.balance;
    inventory = d.inventory || [];
    updateUI();
  } catch(e) { console.error(e); }
}
async function changeBalance(delta) {
  if (!user) return;
  try {
    const r = await fetch('/api/balance', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({user_id:user.id, delta})
    });
    const d = await r.json();
    balance = d.balance;
    inventory = d.inventory || [];
    updateUI();
  } catch(e) { console.error(e); }
}
function updateUI() {
  document.getElementById('balance').textContent = fmt(balance);
  document.getElementById('coins').textContent = `= ${balance} копеек`;
}
function goMenu() {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById('menu').classList.add('active');
  if (rocketInterval) { clearInterval(rocketInterval); rocketInterval = null; }
  document.getElementById('rocket-ship').classList.remove('flying');
}
function openGame(name) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById(name).classList.add('active');
  if (name==='rocket') initRocket();
  if (name==='slots') initSlots();
  if (name==='plinko') initPlinko();
  if (name==='wheel') initWheel();
  if (name==='inventory') renderInventory();
  if (name==='shop') renderShop();
}
function makeBetButtons(id, cb) {
  const c = document.getElementById(id);
  c.innerHTML = '';
  BETS.forEach(b => {
    const btn = document.createElement('button');
    btn.className = 'bet-btn';
    btn.textContent = fmt(b) + ' ₽';
    btn.onclick = () => cb(b);
    c.appendChild(btn);
  });
}

function initRocket() {
  if (rocketInterval) { clearInterval(rocketInterval); rocketInterval = null; }
  rocketBet = 0; rocketMult = 1.0; rocketTimer = 10; rocketSprings = 0;
  const area = document.getElementById('rocket-area');
  area.querySelectorAll('.spring, .trail, .star').forEach(e => e.remove());
  for (let i = 0; i < 30; i++) {
    const s = document.createElement('div');
    s.className = 'star';
    const sz = Math.random()*2 + 1;
    s.style.width = sz + 'px';
    s.style.height = sz + 'px';
    s.style.left = Math.random()*100 + '%';
    s.style.top = Math.random()*100 + '%';
    s.style.animationDelay = Math.random()*2 + 's';
    area.appendChild(s);
  }
  document.getElementById('rocket-mult').textContent = 'x1.00';
  document.getElementById('rocket-mult').classList.remove('crashed');
  document.getElementById('rocket-ship').style.bottom = '20px';
  document.getElementById('rocket-ship').textContent = '🚀';
  document.getElementById('rocket-timer').textContent = '⏱ 10.0s';
  document.getElementById('rocket-status').textContent = 'Выбери ставку';
  document.getElementById('rocket-cashout').style.display = 'none';
  makeBetButtons('rocket-buttons', startRocket);
}
async function startRocket(bet) {
  if (bet > balance) { tg.showAlert('Недостаточно средств'); return; }
  rocketBet = bet; rocketMult = 1.0; rocketTimer = 10; rocketSprings = 0;
  await changeBalance(-bet);
  document.getElementById('rocket-buttons').innerHTML = '';
  document.getElementById('rocket-cashout').style.display = 'block';
  document.getElementById('rocket-ship').classList.add('flying');
  document.getElementById('rocket-status').textContent = `Ставка: ${fmt(bet)} ₽`;
  const area = document.getElementById('rocket-area');
  const springs = [];
  for (let i = 0; i < 5; i++) {
    const sp = document.createElement('div');
    sp.className = 'spring';
    sp.textContent = '🌀';
    sp.style.left = (15 + Math.random()*70) + '%';
    sp.style.top = (80 + i*60) + 'px';
    area.appendChild(sp);
    springs.push(sp);
  }
  rocketInterval = setInterval(() => {
    rocketTimer -= 0.15;
    document.getElementById('rocket-timer').textContent = '⏱ ' + Math.max(0, rocketTimer).toFixed(1) + 's';
    const progress = (10 - rocketTimer) / 10;
    const bottom = 20 + progress * 300;
    document.getElementById('rocket-ship').style.bottom = bottom + 'px';
    const trail = document.createElement('div');
    trail.className = 'trail';
    trail.style.left = 'calc(50% - 2px)';
    trail.style.bottom = (bottom - 10) + 'px';
    area.appendChild(trail);
    setTimeout(() => trail.remove(), 800);
    springs.forEach((sp, i) => {
      const spTop = 80 + i*60;
      if (!sp.dataset.used && Math.abs(bottom - spTop) < 30) {
        sp.dataset.used = '1';
        sp.textContent = '💫';
        rocketSprings++;
        rocketMult += 0.5;
      }
    });
    rocketMult = +(rocketMult + 0.05 + rocketSprings * 0.1).toFixed(2);
    document.getElementById('rocket-mult').textContent = 'x' + rocketMult.toFixed(2);
    if (Math.random() < 0.015 * (1 + rocketSprings * 0.3)) {
      clearInterval(rocketInterval); rocketInterval = null;
      document.getElementById('rocket-mult').textContent = '💥 x' + rocketMult.toFixed(2);
      document.getElementById('rocket-mult').classList.add('crashed');
      document.getElementById('rocket-ship').classList.remove('flying');
      document.getElementById('rocket-ship').textContent = '💥';
      document.getElementById('rocket-status').textContent = `Потеряно: ${fmt(rocketBet)} ₽`;
      document.getElementById('rocket-cashout').style.display = 'none';
      setTimeout(() => { document.getElementById('rocket-ship').textContent = '🚀'; initRocket(); }, 2500);
      return;
    }
    if (rocketTimer <= 0 || bottom >= 310) {
      clearInterval(rocketInterval); rocketInterval = null;
      const win = Math.floor(rocketBet * rocketMult * 2);
      changeBalance(win);
      document.getElementById('rocket-mult').textContent = '🛸 x' + rocketMult.toFixed(2);
      document.getElementById('rocket-status').textContent = `✅ Долетел до станции! +${fmt(win)} ₽`;
      document.getElementById('rocket-cashout').style.display = 'none';
      setTimeout(initRocket, 3000);
      return;
    }
    document.getElementById('rocket-status').textContent = `Потенциал: ${fmt(Math.floor(rocketBet*rocketMult))} ₽ | Пружин: ${rocketSprings}`;
  }, 150);
}
async function cashoutRocket() {
  if (!rocketInterval) return;
  clearInterval(rocketInterval); rocketInterval = null;
  const win = Math.floor(rocketBet * rocketMult);
  await changeBalance(win);
  document.getElementById('rocket-cashout').style.display = 'none';
  document.getElementById('rocket-ship').classList.remove('flying');
  document.getElementById('rocket-status').textContent = `✅ Забрал ${fmt(win)} ₽ (x${rocketMult.toFixed(2)})`;
  setTimeout(initRocket, 2500);
}

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
    ? `🎉 Выигрыш: <b>+${fmt(win)} ₽</b> (x${mult})`
    : '😢 Не повезло';
  setTimeout(initSlots, 2500);
}

function initPlinko() {
  const area = document.getElementById('plinko-area');
  area.querySelectorAll('.peg, .ball').forEach(e => e.remove());
  const rows = 7;
  for (let r = 0; r < rows; r++) {
    const count = r + 3;
    for (let i = 0; i < count; i++) {
      const peg = document.createElement('div');
      peg.className = 'peg';
      peg.style.top = (40 + r*38) + 'px';
      peg.style.left = `calc(50% + ${(i - (count-1)/2) * 32}px)`;
      area.appendChild(peg);
    }
  }
  const mults = [0.5, 1, 1.5, 2, 3, 5, 10, 3, 2, 1.5, 1, 0.5];
  const bottom = document.getElementById('plinko-bottom');
  bottom.innerHTML = '';
  mults.forEach(m => {
    const d = document.createElement('div');
    d.style.cssText = 'flex:1;text-align:center;font-size:10px;padding:6px 0;color:#fff;';
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
  ball.style.left = 'calc(50% - 8px)';
  ball.style.top = '10px';
  area.appendChild(ball);
  const mults = [0.5, 1, 1.5, 2, 3, 5, 10, 3, 2, 1.5, 1, 0.5];
  const weights = [20, 20, 15, 12, 8, 4, 1, 4, 8, 12, 15, 20];
  let total = weights.reduce((a,b)=>a+b,0);
  let rnd = Math.random()*total, idx = 0;
  for (let i = 0; i < weights.length; i++) { rnd -= weights[i]; if (rnd <= 0) { idx = i; break; } }
  const finalX = (idx / (mults.length-1)) * 100;
  const steps = 25;
  for (let s = 1; s <= steps; s++) {
    await new Promise(r => setTimeout(r, 55));
    const y = 10 + (s / steps) * (area.clientHeight - 50);
    const x = 50 + (finalX - 50) * (s / steps) + (Math.random()-0.5) * 12;
    ball.style.top = y + 'px';
    ball.style.left = `calc(${x}% - 8px)`;
  }
  ball.remove();
  const mult = mults[idx];
  const win = Math.floor(bet * mult);
  if (win > 0) await changeBalance(win);
  document.getElementById('plinko-status').innerHTML = `🎲 Множитель <b>x${mult}</b><br>${fmt(bet)} ₽ → <b>${fmt(win)} ₽</b>`;
  setTimeout(initPlinko, 3000);
}

function initWheel() {
  const wheel = document.getElementById('wheel-el');
  wheel.style.transition = 'none';
  wheel.style.transform = 'rotate(0deg)';
  setTimeout(() => wheel.style.transition = 'transform 4s cubic-bezier(.17,.67,.3,1)', 50);
  wheel.innerHTML = '';
  const colors = ['#e94560','#1a1a2e','#f59e0b','#1a1a2e','#4ade80','#1a1a2e','#667eea','#1a1a2e','#e94560','#1a1a2e','#f59e0b','#1a1a2e'];
  const mults = [2,0,5,0,3,0,10,0,2,0,5,0];
  mults.forEach((m,i) => {
    const seg = document.createElement('div');
    seg.className = 'wheel-seg';
    seg.style.background = colors[i];
    seg.style.transform = `rotate(${i*30}deg)`;
    wheel.appendChild(seg);
    const num = document.createElement('div');
    num.className = 'wheel-num';
    num.textContent = 'x' + m;
    num.style.transform = `rotate(${i*30 + 15}deg)`;
    num.style.top = '18px';
    num.style.left = '50%';
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
  await new Promise(r => setTimeout(r, 4200));
  const win = Math.floor(bet * mult);
  if (win > 0) await changeBalance(win);
  document.getElementById('wheel-status').innerHTML = mult
    ? `🎉 Выпало <b>x${mult}</b> → <b>+${fmt(win)} ₽</b>`
    : '😢 Мимо';
  setTimeout(initWheel, 3000);
}

function renderInventory() {
  const c = document.getElementById('inv-list');
  c.innerHTML = '';
  if (!inventory || inventory.length === 0) {
    c.innerHTML = '<div style="grid-column:1/-1;text-align:center;opacity:.5;padding:40px;">Пусто. Купи подарок в магазине 🛒</div>';
    return;
  }
  inventory.forEach((giftId, i) => {
    const g = GIFTS[giftId];
    if (!g) return;
    const d = document.createElement('div');
    d.className = 'inv-item';
    d.innerHTML = `<div class="emoji">${g.emoji}</div><div class="name">${g.name}</div>
      <div class="price">${fmt(g.price)} ₽</div>
      <button class="sell-btn" onclick="sellGift(${i})">Продать</button>`;
    c.appendChild(d);
  });
}
async function sellGift(index) {
  try {
    const r = await fetch('/api/sell', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({user_id:user.id, index})
    });
    const d = await r.json();
    if (d.error) { tg.showAlert(d.error); return; }
    balance = d.balance;
    inventory = d.inventory;
    updateUI();
    renderInventory();
    tg.showAlert('Подарок продан!');
  } catch(e) { console.error(e); }
}

function renderShop() {
  const c = document.getElementById('shop-list');
  c.innerHTML = '';
  Object.keys(GIFTS).forEach(id => {
    const g = GIFTS[id];
    const d = document.createElement('div');
    d.className = 'shop-item';
    d.innerHTML = `<div style="font-size:40px;">${g.emoji}</div>
      <div style="font-weight:700;margin-top:6px;">${g.name}</div>
      <div style="color:#4ade80;margin:6px 0;">${fmt(g.price)} ₽</div>
      <button class="sell-btn" style="background:#4ade80;color:#000;" onclick="buyGift('${id}')">Купить</button>`;
    c.appendChild(d);
  });
}
async function buyGift(id) {
  try {
    const r = await fetch('/api/buy', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({user_id:user.id, gift_id:id})
    });
    const d = await r.json();
    if (d.error) { tg.showAlert(d.error); return; }
    balance = d.balance;
    inventory = d.inventory;
    updateUI();
    tg.showAlert('Куплено!');
  } catch(e) { console.error(e); }
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
    u = get_user(int(user_id))
    return web.json_response({"balance": u["balance"], "inventory": u["inventory"]})

async def handle_post_balance(request):
    data = await request.json()
    user_id = int(data["user_id"])
    delta = int(data["delta"])
    new = update_balance(user_id, delta)
    u = get_user(user_id)
    return web.json_response({"balance": new, "inventory": u["inventory"]})

async def handle_buy(request):
    data = await request.json()
    user_id = int(data["user_id"])
    gift_id = str(data["gift_id"])
    u = get_user(user_id)
    if gift_id not in GIFTS:
        return web.json_response({"error":"Нет такого подарка"}, status=400)
    price = GIFTS[gift_id]["price"]
    if u["balance"] < price:
        return web.json_response({"error":"Недостаточно средств"})
    u["balance"] -= price
    u["inventory"].append(gift_id)
    save_user(user_id, u)
    return web.json_response({"balance": u["balance"], "inventory": u["inventory"]})

async def handle_sell(request):
    data = await request.json()
    user_id = int(data["user_id"])
    index = int(data["index"])
    u = get_user(user_id)
    if index < 0 or index >= len(u["inventory"]):
        return web.json_response({"error":"Нет такого предмета"}, status=400)
    gift_id = u["inventory"].pop(index)
    price = GIFTS[gift_id]["price"]
    u["balance"] += price
    save_user(user_id, u)
    return web.json_response({"balance": u["balance"], "inventory": u["inventory"]})

app = web.Application()
app.router.add_get("/", handle_index)
app.router.add_get("/api/balance", handle_get_balance)
app.router.add_post("/api/balance", handle_post_balance)
app.router.add_post("/api/buy", handle_buy)
app.router.add_post("/api/sell", handle_sell)

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    get_user(message.from_user.id)
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
