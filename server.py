import asyncio, os, json, random
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
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False)

def get_user(uid):
    db = load_db()
    k = str(uid)
    if k not in db or not isinstance(db[k], dict):
        db[k] = {"balance": 10000}
        save_db(db)
    return db[k]

def save_user(uid, data):
    db = load_db()
    db[str(uid)] = data
    save_db(db)

def update_balance(uid, delta):
    u = get_user(uid)
    u["balance"] = max(0, u["balance"] + delta)
    save_user(uid, u)
    return u["balance"]

HTML_PAGE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>CASINO</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent;font-family:-apple-system,sans-serif}
body{background:#05050f;color:#e8e8f0;min-height:100vh;padding:14px}
.balance{background:linear-gradient(135deg,#1e1e3a,#2a1e4a);border:1px solid #3a2a5a;padding:16px;border-radius:14px;text-align:center;margin-bottom:14px}
.balance h1{font-size:11px;opacity:.6;letter-spacing:2px}
.balance .amount{font-size:28px;font-weight:800;color:#fff}
.games{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.game{background:linear-gradient(160deg,#12122a,#0d0d1f);border-radius:14px;padding:20px 10px;text-align:center;cursor:pointer;border:1px solid #1e1e3a}
.game:active{transform:scale(.96);border-color:#4a3aff}
.game .name{font-size:13px;font-weight:700;letter-spacing:1px}
.game .desc{font-size:10px;opacity:.5;margin-top:4px}
.screen{display:none}.screen.active{display:block}
.back{background:#12122a;border:1px solid #1e1e3a;color:#fff;padding:10px 16px;border-radius:10px;font-size:13px;margin-bottom:14px;cursor:pointer}
h2{font-size:18px;margin-bottom:16px;text-align:center;font-weight:800;letter-spacing:2px}
.bet-buttons{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:14px}
.bet-btn{background:#12122a;border:1px solid #2a2a4a;color:#fff;padding:14px;border-radius:10px;font-size:15px;font-weight:700;cursor:pointer}
.bet-btn:active{background:#2a2a4a}
.big-btn{background:linear-gradient(135deg,#4a3aff,#6a4aff);border:none;color:#fff;padding:16px;border-radius:12px;font-size:15px;font-weight:800;width:100%;margin-top:12px;cursor:pointer}
.big-btn:active{transform:scale(.98)}
.status{text-align:center;font-size:14px;min-height:24px;margin-bottom:8px;font-weight:600}
.slots{display:flex;justify-content:center;gap:10px;margin:30px 0}
.slot{width:90px;height:120px;background:linear-gradient(180deg,#1a1a2e,#0f0f1e);border:2px solid #4a3aff;border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:52px}
.slot.spinning{animation:sp .1s infinite}
@keyframes sp{0%,100%{transform:translateY(-8px)}50%{transform:translateY(8px)}}
.dice-display{font-size:110px;text-align:center;margin:30px 0;min-height:120px}
.num-buttons{display:grid;grid-template-columns:repeat(6,1fr);gap:6px;margin-top:10px}
.coin{width:130px;height:130px;border-radius:50%;background:radial-gradient(circle,#ffdd44,#cc9900);margin:30px auto;display:flex;align-items:center;justify-content:center;font-size:40px;font-weight:900;color:#3a2a00}
.coin.flipping{animation:fl .3s infinite}
@keyframes fl{0%{transform:rotateY(0)}100%{transform:rotateY(360deg)}}
.wheel-wrap{position:relative;width:280px;height:280px;margin:20px auto}
.wheel{width:100%;height:100%;border-radius:50%;border:8px solid #2a2a4a;position:relative;transition:transform 5s cubic-bezier(.15,.85,.25,1);overflow:hidden}
.wheel-num{position:absolute;font-size:9px;font-weight:900;color:#fff}
.pointer{position:absolute;top:-14px;left:50%;transform:translateX(-50%);width:0;height:0;border-left:12px solid transparent;border-right:12px solid transparent;border-top:22px solid #ff3a5a;z-index:10}
.wheel-center{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:46px;height:46px;background:radial-gradient(circle,#4a3aff,#2a1a8a);border-radius:50%;border:3px solid #6a4aff;z-index:5;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:900}
.mines-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:6px;margin-top:12px}
.mine-cell{aspect-ratio:1;background:#12122a;border:1px solid #2a2a4a;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:22px;cursor:pointer}
.mine-cell.opened{background:#1a1a3a}.mine-cell.mine{background:#3a0a0a;border-color:#ff3a5a}

/* Ракета */
.rocket-stage{position:relative;height:400px;background:linear-gradient(180deg,#000005,#05051a 40%,#0a0a25);border-radius:14px;overflow:hidden;border:1px solid #1e1e3a;margin-top:10px}
.star{position:absolute;background:#fff;border-radius:50%}
.rocket-svg{position:absolute;width:30px;height:50px;z-index:5;transition:left .05s linear,bottom .05s linear}
.mult-display{position:absolute;top:15%;left:50%;transform:translateX(-50%);font-size:42px;font-weight:900;color:#4aff8a;text-shadow:0 0 30px #4aff8a;z-index:10}
.mult-display.crashed{color:#ff3a5a}
.fuel-bar{position:absolute;top:10px;left:10px;right:10px;height:14px;background:rgba(0,0,0,.6);border-radius:7px;border:1px solid #3a3a5a;overflow:hidden;z-index:10}
.fuel-fill{height:100%;background:linear-gradient(90deg,#ff3a5a,#ffaa00,#4aff8a);width:100%;transition:width .05s}
.flame{position:absolute;left:50%;transform:translateX(-50%);width:12px;background:radial-gradient(ellipse at top,#ffaa00,#ff4400,transparent);border-radius:50%;animation:f .1s infinite alternate}
@keyframes f{from{height:14px}to{height:24px}}
.countdown{position:absolute;top:40%;left:50%;transform:translate(-50%,-50%);font-size:64px;font-weight:900;color:#fff;z-index:20}
.countdown.hidden{display:none}
.fuel-item{position:absolute;width:14px;height:20px;background:linear-gradient(180deg,#ffdd44,#cc9900);border-radius:3px;z-index:4}
.asteroid{position:absolute;width:24px;height:24px;background:radial-gradient(circle at 30% 30%,#886644,#332211);border-radius:50%;z-index:4}
.controls{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px}
.ctrl{background:#1a1a3a;border:1px solid #4a3aff;color:#fff;padding:18px;border-radius:12px;font-size:22px;font-weight:900;cursor:pointer;user-select:none}
.ctrl:active{background:#4a3aff}

/* Плинко */
.plinko-stage{position:relative;height:400px;background:#0a0a1e;border-radius:14px;overflow:hidden;border:1px solid #1e1e3a;margin-top:10px}
.peg{position:absolute;width:9px;height:9px;background:#4a3aff;border-radius:50%;box-shadow:0 0 8px #4a3aff}
.ball{position:absolute;width:16px;height:16px;background:#fbbf24;border-radius:50%;box-shadow:0 0 15px #fbbf24;z-index:5}
.plinko-bottom{position:absolute;bottom:0;width:100%;display:flex}
.plinko-slot{flex:1;text-align:center;font-size:10px;padding:6px 0;color:#fff;font-weight:700}

/* Корова перебегает дорогу */
.road-stage{position:relative;height:400px;background:#2a2a3a;border-radius:14px;overflow:hidden;border:1px solid #1e1e3a;margin-top:10px}
.road-line{position:absolute;left:0;right:0;height:3px;background:repeating-linear-gradient(90deg,#fff 0,#fff 20px,transparent 20px,transparent 40px)}
.cow{position:absolute;width:50px;height:50px;font-size:42px;z-index:5;transition:left .1s linear,bottom .1s linear;text-align:center;line-height:50px}
.car{position:absolute;font-size:40px;z-index:4;text-align:center;line-height:50px}
.road-mult{position:absolute;top:10px;left:50%;transform:translateX(-50%);font-size:32px;font-weight:900;color:#4aff8a;text-shadow:0 0 20px #4aff8a;z-index:10}
.road-mult.crashed{color:#ff3a5a}
.road-controls{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px}

/* Скорость */
.speed-wrap{text-align:center;margin:20px 0}
.speed-mult{font-size:60px;font-weight:900;color:#4aff8a;text-shadow:0 0 30px #4aff8a;margin:20px 0}
.speed-mult.crashed{color:#ff3a5a}
.speed-bar{height:30px;background:#12122a;border-radius:15px;overflow:hidden;border:1px solid #2a2a4a;margin:20px 0}
.speed-fill{height:100%;background:linear-gradient(90deg,#4aff8a,#ffaa00,#ff3a5a);width:0%;transition:width .1s}
</style>
</head>
<body>

<div id="menu" class="screen active">
  <div class="balance"><h1>БАЛАНС</h1><div class="amount"><span id="balance">100.00</span> ₽</div></div>
  <div class="games">
    <div class="game" id="btn-slots"><div class="name">🎰 СЛОТЫ</div><div class="desc">3 БАРАБАНА</div></div>
    <div class="game" id="btn-dice"><div class="name">🎲 КОСТИ</div><div class="desc">УГАДАЙ ЧИСЛО</div></div>
    <div class="game" id="btn-coin"><div class="name">🪙 МОНЕТКА</div><div class="desc">ОРЁЛ/РЕШКА</div></div>
    <div class="game" id="btn-wheel"><div class="name">🎡 РУЛЕТКА</div><div class="desc">КРУТИ</div></div>
    <div class="game" id="btn-mines"><div class="name">💣 МИНЫ</div><div class="desc">5x5</div></div>
    <div class="game" id="btn-rocket"><div class="name">🚀 РАКЕТА</div><div class="desc">УПРАВЛЯЙ</div></div>
    <div class="game" id="btn-plinko"><div class="name">🎯 ПЛИНКО</div><div class="desc">ШАРИК</div></div>
    <div class="game" id="btn-cow"><div class="name">🐄 КОРОВА</div><div class="desc">ПЕРЕБЕГИ ДОРОГУ</div></div>
    <div class="game" id="btn-speed"><div class="name">⚡ СКОРОСТЬ</div><div class="desc">x2 x5 x10</div></div>
  </div>
</div>

<!-- СЛОТЫ -->
<div id="slots" class="screen">
  <button class="back" id="back-slots">← НАЗАД</button>
  <h2>СЛОТЫ</h2>
  <div class="slots">
    <div class="slot" id="slot0">🍒</div>
    <div class="slot" id="slot1">🍒</div>
    <div class="slot" id="slot2">🍒</div>
  </div>
  <div class="status" id="slots-status">ВЫБЕРИ СТАВКУ</div>
  <div class="bet-buttons" id="slots-buttons"></div>
</div>

<!-- КОСТИ -->
<div id="dice" class="screen">
  <button class="back" id="back-dice">← НАЗАД</button>
  <h2>КОСТИ</h2>
  <div class="dice-display" id="dice-display">🎲</div>
  <div class="status" id="dice-status">ВЫБЕРИ ЧИСЛО И СТАВКУ</div>
  <div class="num-buttons">
    <button class="bet-btn" data-dice="1">1</button>
    <button class="bet-btn" data-dice="2">2</button>
    <button class="bet-btn" data-dice="3">3</button>
    <button class="bet-btn" data-dice="4">4</button>
    <button class="bet-btn" data-dice="5">5</button>
    <button class="bet-btn" data-dice="6">6</button>
  </div>
  <div class="bet-buttons" id="dice-buttons"></div>
</div>

<!-- МОНЕТКА -->
<div id="coin" class="screen">
  <button class="back" id="back-coin">← НАЗАД</button>
  <h2>МОНЕТКА</h2>
  <div class="coin" id="coin-display">?</div>
  <div class="status" id="coin-status">ВЫБЕРИ СТОРОНУ</div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px;">
    <button class="bet-btn" id="pick-o">ОРЁЛ</button>
    <button class="bet-btn" id="pick-r">РЕШКА</button>
  </div>
  <div class="bet-buttons" id="coin-buttons"></div>
</div>

<!-- РУЛЕТКА -->
<div id="wheel" class="screen">
  <button class="back" id="back-wheel">← НАЗАД</button>
  <h2>РУЛЕТКА</h2>
  <div class="wheel-wrap">
    <div class="pointer"></div>
    <div class="wheel" id="wheel-el"></div>
    <div class="wheel-center">SPIN</div>
  </div>
  <div class="status" id="wheel-status">ВЫБЕРИ СТАВКУ</div>
  <div class="bet-buttons" id="wheel-buttons"></div>
</div>

<!-- МИНЫ -->
<div id="mines" class="screen">
  <button class="back" id="back-mines">← НАЗАД</button>
  <h2>МИНЫ</h2>
  <div class="status" id="mines-status">ВЫБЕРИ СТАВКУ</div>
  <div class="bet-buttons" id="mines-buttons"></div>
  <div class="mines-grid" id="mines-grid"></div>
  <button class="big-btn" id="mines-cashout" style="display:none;background:linear-gradient(135deg,#4aff8a,#2acc6a);color:#000;">ЗАБРАТЬ</button>
</div>

<!-- РАКЕТА -->
<div id="rocket" class="screen">
  <button class="back" id="back-rocket">← НАЗАД</button>
  <h2>РАКЕТА</h2>
  <div class="rocket-stage" id="rocket-stage">
    <div class="fuel-bar"><div class="fuel-fill" id="fuel-fill"></div></div>
    <div class="countdown hidden" id="countdown">10</div>
    <div class="mult-display" id="rocket-mult">x1.00</div>
    <div class="rocket-svg" id="rocket-svg" style="left:calc(50% - 15px);bottom:20px;">
      <svg viewBox="0 0 30 50" width="30" height="50"><polygon points="15,0 24,18 24,38 6,38 6,18" fill="#e8e8f0"/><polygon points="15,0 24,18 6,18" fill="#4a3aff"/><circle cx="15" cy="22" r="4" fill="#4a3aff"/></svg>
      <div class="flame" id="flame" style="bottom:-16px;display:none;"></div>
    </div>
  </div>
  <div class="status" id="rocket-status" style="font-size:12px;">ЖДЁМ СТАРТА</div>
  <div class="bet-buttons" id="rocket-buttons"></div>
  <div class="controls">
    <button class="ctrl" id="ctrl-left">←</button>
    <button class="ctrl" id="ctrl-right">→</button>
  </div>
  <button class="big-btn" id="rocket-cashout" style="display:none;background:linear-gradient(135deg,#4aff8a,#2acc6a);color:#000;">ЗАБРАТЬ</button>
</div>

<!-- ПЛИНКО -->
<div id="plinko" class="screen">
  <button class="back" id="back-plinko">← НАЗАД</button>
  <h2>ПЛИНКО</h2>
  <div class="plinko-stage" id="plinko-stage"><div class="plinko-bottom" id="plinko-bottom"></div></div>
  <div class="status" id="plinko-status" style="font-size:12px;">ВЫБЕРИ СТАВКУ</div>
  <div class="bet-buttons" id="plinko-buttons"></div>
</div>

<!-- КОРОВА -->
<div id="cow" class="screen">
  <button class="back" id="back-cow">← НАЗАД</button>
  <h2>КОРОВА ПЕРЕБЕГАЕТ ДОРОГУ</h2>
  <div class="road-stage" id="road-stage">
    <div class="road-mult" id="road-mult">x1.00</div>
    <div class="cow" id="cow-el" style="left:10px;bottom:20px;">🐄</div>
  </div>
  <div class="status" id="cow-status" style="font-size:12px;">ВЫБЕРИ СТАВКУ</div>
  <div class="bet-buttons" id="cow-buttons"></div>
  <div class="road-controls">
    <button class="ctrl" id="cow-left">←</button>
    <button class="ctrl" id="cow-right">→</button>
  </div>
  <button class="big-btn" id="cow-cashout" style="display:none;background:linear-gradient(135deg,#4aff8a,#2acc6a);color:#000;">ЗАБРАТЬ</button>
</div>

<!-- СКОРОСТЬ -->
<div id="speed" class="screen">
  <button class="back" id="back-speed">← НАЗАД</button>
  <h2>СКОРОСТЬ</h2>
  <div class="speed-wrap">
    <div class="speed-mult" id="speed-mult">x1.00</div>
    <div class="speed-bar"><div class="speed-fill" id="speed-fill"></div></div>
  </div>
  <div class="status" id="speed-status">ВЫБЕРИ СТАВКУ</div>
  <div class="bet-buttons" id="speed-buttons"></div>
  <button class="big-btn" id="speed-cashout" style="display:none;background:linear-gradient(135deg,#4aff8a,#2acc6a);color:#000;">ЗАБРАТЬ</button>
</div>

<script>
// ==== ИНИЦИАЛИЗАЦИЯ ====
var tg = null;
try {
  tg = window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null;
  if (tg) { tg.ready(); tg.expand(); }
} catch(e) { console.log('TG error:', e); }

var user = (tg && tg.initDataUnsafe && tg.initDataUnsafe.user) ? tg.initDataUnsafe.user : { id: 0 };
var BETS = [100, 500, 1000, 5000];
var balance = 10000;

function fmt(k) { return (k / 100).toFixed(2); }
function showAlert(msg) { if (tg && tg.showAlert) { tg.showAlert(msg); } else { alert(msg); } }
function updateUI() { var el = document.getElementById('balance'); if (el) el.textContent = fmt(balance); }
function $(id) { return document.getElementById(id); }

function loadBalance() {
  fetch('/api/balance?user_id=' + user.id)
    .then(function(r) { return r.json(); })
    .then(function(d) { balance = d.balance; updateUI(); })
    .catch(function(e) { console.log('loadBalance:', e); });
}
function changeBalance(delta) {
  return fetch('/api/balance', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: user.id, delta: delta })
  }).then(function(r) { return r.json(); }).then(function(d) { balance = d.balance; updateUI(); })
    .catch(function(e) { console.log('changeBalance:', e); });
}
function showScreen(id) {
  var screens = document.querySelectorAll('.screen');
  for (var i = 0; i < screens.length; i++) { screens[i].classList.remove('active'); }
  $(id).classList.add('active');
}
function goMenu() { showScreen('menu'); }
function makeBetButtons(containerId, callback) {
  var c = $(containerId);
  if (!c) return;
  c.innerHTML = '';
  for (var i = 0; i < BETS.length; i++) {
    (function(bet) {
      var btn = document.createElement('button');
      btn.className = 'bet-btn';
      btn.textContent = fmt(bet) + ' ₽';
      btn.addEventListener('click', function() { callback(bet); });
      c.appendChild(btn);
    })(BETS[i]);
  }
}

// ==== МЕНЮ ====
var menuBtns = {
  'btn-slots': 'slots', 'btn-dice': 'dice', 'btn-coin': 'coin', 'btn-wheel': 'wheel',
  'btn-mines': 'mines', 'btn-rocket': 'rocket', 'btn-plinko': 'plinko',
  'btn-cow': 'cow', 'btn-speed': 'speed'
};
for (var key in menuBtns) {
  (function(screenId) {
    var btn = $(key);
    if (btn) btn.addEventListener('click', function() { showScreen(screenId); initGame(screenId); });
  })(menuBtns[key]);
}
['slots','dice','coin','wheel','mines','rocket','plinko','cow','speed'].forEach(function(id) {
  var b = $('back-' + id);
  if (b) b.addEventListener('click', goMenu);
});

function initGame(id) {
  if (id === 'slots') initSlots();
  if (id === 'dice') initDice();
  if (id === 'coin') initCoin();
  if (id === 'wheel') initWheel();
  if (id === 'mines') initMines();
  if (id === 'rocket') initRocket();
  if (id === 'plinko') initPlinko();
  if (id === 'cow') initCow();
  if (id === 'speed') initSpeed();
}

// ============ СЛОТЫ ============
var slotsBusy = false;
function initSlots() {
  slotsBusy = false;
  $('slots-status').textContent = 'ВЫБЕРИ СТАВКУ';
  $('slot0').textContent = '🍒'; $('slot1').textContent = '🍒'; $('slot2').textContent = '🍒';
  makeBetButtons('slots-buttons', playSlots);
}
function playSlots(bet) {
  if (slotsBusy) return;
  if (bet > balance) { showAlert('Недостаточно средств'); return; }
  slotsBusy = true;
  changeBalance(-bet).then(function() {
    var symbols = ['🍒','🍋','🍊','💎','7️⃣'];
    $('slots-buttons').innerHTML = '';
    $('slots-status').textContent = 'КРУТИМ...';
    for (var i = 0; i < 3; i++) $('slot' + i).classList.add('spinning');
    var final = [symbols[Math.floor(Math.random()*5)], symbols[Math.floor(Math.random()*5)], symbols[Math.floor(Math.random()*5)]];
    setTimeout(function(){ $('slot0').classList.remove('spinning'); $('slot0').textContent = final[0]; }, 700);
    setTimeout(function(){ $('slot1').classList.remove('spinning'); $('slot1').textContent = final[1]; }, 1200);
    setTimeout(function(){
      $('slot2').classList.remove('spinning'); $('slot2').textContent = final[2];
      var mult = 0;
      if (final[0] === final[1] && final[1] === final[2]) mult = final[0] === '7️⃣' ? 10 : 5;
      else if (final[0] === final[1] || final[1] === final[2] || final[0] === final[2]) mult = 2;
      var win = Math.floor(bet * mult);
      var done = function() {
        $('slots-status').textContent = mult ? ('ВЫИГРЫШ: +' + fmt(win) + ' ₽ (x' + mult + ')') : 'НЕ ПОВЕЗЛО';
        setTimeout(initSlots, 2500);
      };
      if (win > 0) changeBalance(win).then(done); else done();
    }, 1700);
  });
}

// ============ КОСТИ ============
var diceBusy = false, dicePick = 0;
function initDice() {
  diceBusy = false; dicePick = 0;
  $('dice-display').textContent = '🎲';
  $('dice-status').textContent = 'ВЫБЕРИ ЧИСЛО И СТАВКУ';
  makeBetButtons('dice-buttons', playDice);
}
var diceBtns = document.querySelectorAll('[data-dice]');
for (var i = 0; i < diceBtns.length; i++) {
  (function(btn) {
    btn.addEventListener('click', function() {
      dicePick = parseInt(btn.getAttribute('data-dice'));
      $('dice-status').textContent = 'ВЫБРАНО: ' + dicePick + ' | ВЫБЕРИ СТАВКУ';
    });
  })(diceBtns[i]);
}
function playDice(bet) {
  if (diceBusy) return;
  if (!dicePick) { showAlert('Выбери число'); return; }
  if (bet > balance) { showAlert('Недостаточно средств'); return; }
  diceBusy = true;
  changeBalance(-bet).then(function() {
    $('dice-buttons').innerHTML = '';
    $('dice-status').textContent = 'БРОСАЕМ...';
    setTimeout(function() {
      var result = Math.floor(Math.random()*6)+1;
      var faces = ['','⚀','⚁','⚂','⚃','⚄','⚅'];
      $('dice-display').textContent = faces[result];
      if (result === dicePick) {
        var win = bet * 6;
        changeBalance(win).then(function() {
          $('dice-status').textContent = 'ВЫПАЛО ' + result + '! +' + fmt(win) + ' ₽';
          setTimeout(initDice, 3000);
        });
      } else {
        $('dice-status').textContent = 'ВЫПАЛО ' + result + '. МИМО';
        setTimeout(initDice, 3000);
      }
    }, 1000);
  });
}

// ============ МОНЕТКА ============
var coinBusy = false, coinPick = '';
function initCoin() {
  coinBusy = false; coinPick = '';
  $('coin-display').textContent = '?';
  $('coin-status').textContent = 'ВЫБЕРИ СТОРОНУ';
  makeBetButtons('coin-buttons', playCoin);
}
$('pick-o').addEventListener('click', function() { coinPick = 'О'; $('coin-status').textContent = 'ВЫБРАНО: ОРЁЛ | ВЫБЕРИ СТАВКУ'; });
$('pick-r').addEventListener('click', function() { coinPick = 'Р'; $('coin-status').textContent = 'ВЫБРАНО: РЕШКА | ВЫБЕРИ СТАВКУ'; });
function playCoin(bet) {
  if (coinBusy) return;
  if (!coinPick) { showAlert('Выбери сторону'); return; }
  if (bet > balance) { showAlert('Недостаточно средств'); return; }
  coinBusy = true;
  changeBalance(-bet).then(function() {
    $('coin-buttons').innerHTML = '';
    var cd = $('coin-display');
    cd.classList.add('flipping');
    setTimeout(function() {
      cd.classList.remove('flipping');
      var result = Math.random() < 0.5 ? 'О' : 'Р';
      cd.textContent = result === 'О' ? 'ОРЁЛ' : 'РЕШКА';
      if (result === coinPick) {
        var win = bet * 2;
        changeBalance(win).then(function() {
          $('coin-status').textContent = '+' + fmt(win) + ' ₽ (x2)';
          setTimeout(initCoin, 3000);
        });
      } else {
        $('coin-status').textContent = 'МИМО';
        setTimeout(initCoin, 3000);
      }
    }, 1500);
  });
}

// ============ РУЛЕТКА ============
var wheelBusy = false;
function initWheel() {
  wheelBusy = false;
  var wheel = $('wheel-el');
  wheel.style.transition = 'none'; wheel.style.transform = 'rotate(0deg)';
  setTimeout(function(){ wheel.style.transition = 'transform 5s cubic-bezier(.15,.85,.25,1)'; }, 50);
  wheel.innerHTML = '';
  var reds = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36];
  for (var i = 0; i < 37; i++) {
    var seg = document.createElement('div');
    seg.style.cssText = 'position:absolute;width:50%;height:50%;top:0;left:50%;transform-origin:0% 100%;transform:rotate(' + (i*(360/37)) + 'deg);background:' + (i===0?'#0a8a3a':(reds.indexOf(i)>=0?'#cc2244':'#111')) + ';clip-path:polygon(0 0,100% 0,0 100%);';
    wheel.appendChild(seg);
    var num = document.createElement('div');
    num.className = 'wheel-num'; num.textContent = i;
    num.style.cssText = 'position:absolute;top:16px;left:50%;transform:translateX(-50%) rotate(' + (i*(360/37)+(360/74)) + 'deg);';
    seg.appendChild(num);
  }
  $('wheel-status').textContent = 'ВЫБЕРИ СТАВКУ';
  makeBetButtons('wheel-buttons', playWheel);
}
function playWheel(bet) {
  if (wheelBusy) return;
  if (bet > balance) { showAlert('Недостаточно средств'); return; }
  wheelBusy = true;
  changeBalance(-bet).then(function() {
    $('wheel-buttons').innerHTML = '';
    $('wheel-status').textContent = 'КРУТИМ...';
    var idx = Math.floor(Math.random()*37);
    var wheel = $('wheel-el');
    wheel.style.transform = 'rotate(' + (360*6 + (360 - idx*(360/37))) + 'deg)';
    setTimeout(function() {
      var win = Math.random() < 0.03 ? bet * 30 : 0;
      var done = function() {
        $('wheel-status').textContent = 'ВЫПАЛО ' + idx + '. ' + (win ? ('ВЫИГРЫШ ' + fmt(win) + ' ₽') : 'МИМО');
        wheelBusy = false;
        setTimeout(initWheel, 3000);
      };
      if (win > 0) changeBalance(win).then(done); else done();
    }, 5200);
  });
}

// ============ МИНЫ ============
var minesBet = 0, minesField = [], minesOpened = 0, minesMult = 1.0, minesActive = false;
function initMines() {
  minesBet = 0; minesField = []; minesOpened = 0; minesMult = 1.0; minesActive = false;
  $('mines-status').textContent = 'ВЫБЕРИ СТАВКУ';
  $('mines-grid').innerHTML = '';
  $('mines-cashout').style.display = 'none';
  makeBetButtons('mines-buttons', startMines);
}
function startMines(bet) {
  if (bet > balance) { showAlert('Недостаточно средств'); return; }
  if (minesActive) return;
  minesBet = bet; minesOpened = 0; minesMult = 1.0; minesActive = true;
  changeBalance(-bet).then(function() {
    $('mines-buttons').innerHTML = '';
    $('mines-cashout').style.display = 'block';
    minesField = [];
    for (var i = 0; i < 20; i++) minesField.push('gem');
    for (var i = 0; i < 5; i++) minesField.push('mine');
    for (var i = minesField.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random()*(i+1));
      var t = minesField[i]; minesField[i] = minesField[j]; minesField[j] = t;
    }
    var c = $('mines-grid'); c.innerHTML = '';
    for (var i = 0; i < 25; i++) {
      (function(idx) {
        var cell = document.createElement('div');
        cell.className = 'mine-cell';
        cell.addEventListener('click', function() { openMine(idx, cell); });
        c.appendChild(cell);
      })(i);
    }
    $('mines-status').textContent = 'МНОЖИТЕЛЬ: x' + minesMult.toFixed(2);
  });
}
function openMine(i, cell) {
  if (!minesActive || cell.classList.contains('opened')) return;
  cell.classList.add('opened');
  if (minesField[i] === 'mine') {
    cell.classList.add('mine'); cell.textContent = '💥';
    minesActive = false;
    $('mines-status').textContent = 'БУМ! ПОТЕРЯНО: ' + fmt(minesBet) + ' ₽';
    $('mines-cashout').style.display = 'none';
    var cells = document.querySelectorAll('#mines-grid .mine-cell');
    for (var k = 0; k < minesField.length; k++) {
      if (minesField[k] === 'mine') cells[k].textContent = '💣';
    }
    setTimeout(initMines, 3000);
    return;
  }
  cell.textContent = '💎';
  minesOpened++;
  minesMult = +(1 + minesOpened * 0.3).toFixed(2);
  $('mines-status').textContent = 'x' + minesMult.toFixed(2) + ' | ПОТЕНЦИАЛ: ' + fmt(Math.floor(minesBet * minesMult)) + ' ₽';
}
$('mines-cashout').addEventListener('click', function() {
  if (!minesActive) return;
  minesActive = false;
  var win = Math.floor(minesBet * minesMult);
  changeBalance(win).then(function() {
    $('mines-cashout').style.display = 'none';
    $('mines-status').textContent = 'ЗАБРАЛ ' + fmt(win) + ' ₽ (x' + minesMult.toFixed(2) + ')';
    setTimeout(initMines, 3000);
  });
});

// ============ РАКЕТА ============
var rocketBet = 0, rocketRunning = false, rocketMult = 1.0, rocketX = 50, rocketY = 20, fuel = 100, rocketVel = 0;
var rocketLoop = null, countdownTimer = null;

function initRocket() {
  if (rocketLoop) { clearInterval(rocketLoop); rocketLoop = null; }
  if (countdownTimer) { clearInterval(countdownTimer); countdownTimer = null; }
  rocketBet = 0; rocketRunning = false; rocketMult = 1.0; rocketX = 50; rocketY = 20; fuel = 100;
  var stage = $('rocket-stage');
  var olds = stage.querySelectorAll('.star,.fuel-item,.asteroid');
  for (var i = 0; i < olds.length; i++) olds[i].remove();
  for (var i = 0; i < 40; i++) {
    var s = document.createElement('div'); s.className = 'star';
    var sz = Math.random()*2+1;
    s.style.width = sz+'px'; s.style.height = sz+'px';
    s.style.left = Math.random()*100+'%'; s.style.top = Math.random()*100+'%';
    s.style.opacity = Math.random()*0.7+0.3;
    stage.appendChild(s);
  }
  $('rocket-svg').style.left = 'calc(50% - 15px)';
  $('rocket-svg').style.bottom = '20px';
  $('flame').style.display = 'none';
  $('rocket-mult').textContent = 'x1.00';
  $('rocket-mult').classList.remove('crashed');
  $('rocket-status').textContent = 'ЖДЁМ СТАРТА';
  $('rocket-cashout').style.display = 'none';
  $('fuel-fill').style.width = '100%';
  makeBetButtons('rocket-buttons', selectRocketBet);
  startRocketCountdown();
}
function selectRocketBet(b) {
  if (b > balance) { showAlert('Недостаточно средств'); return; }
  if (rocketRunning) { showAlert('Ракета уже летит'); return; }
  rocketBet = b;
}
function startRocketCountdown() {
  var t = 10;
  var cd = $('countdown');
  cd.classList.remove('hidden'); cd.textContent = t;
  countdownTimer = setInterval(function() {
    t--;
    if (t <= 0) {
      clearInterval(countdownTimer); countdownTimer = null;
      cd.classList.add('hidden');
      if (rocketBet > 0) { changeBalance(-rocketBet).then(launchRocket); }
      else { setTimeout(initRocket, 500); }
      return;
    }
    cd.textContent = t;
  }, 1000);
}
function launchRocket() {
  rocketRunning = true;
  $('rocket-buttons').innerHTML = '';
  $('flame').style.display = 'block';
  $('rocket-cashout').style.display = 'block';
  var stage = $('rocket-stage');
  var stageH = stage.clientHeight;
  var asteroids = [], fuels = [], lastFuel = 0;

  $('ctrl-left').onmousedown = function() { rocketVel = -5; };
  $('ctrl-right').onmousedown = function() { rocketVel = 5; };
  $('ctrl-left').ontouchstart = function(e) { e.preventDefault(); rocketVel = -5; };
  $('ctrl-right').ontouchstart = function(e) { e.preventDefault(); rocketVel = 5; };
  $('ctrl-left').onmouseup = function() { rocketVel = 0; };
  $('ctrl-right').onmouseup = function() { rocketVel = 0; };
  $('ctrl-left').ontouchend = function() { rocketVel = 0; };
  $('ctrl-right').ontouchend = function() { rocketVel = 0; };

  rocketLoop = setInterval(function() {
    if (!rocketRunning) return;
    rocketX += rocketVel;
    if (rocketX < 2) rocketX = 2;
    if (rocketX > 98) rocketX = 98;
    if (fuel > 0) rocketY += 0.6;
    $('rocket-svg').style.left = rocketX + '%';
    $('rocket-svg').style.bottom = rocketY + 'px';
    fuel -= 0.4; if (fuel < 0) fuel = 0;
    $('fuel-fill').style.width = fuel + '%';
    rocketMult = +(1 + rocketY / 40).toFixed(2);
    $('rocket-mult').textContent = 'x' + rocketMult.toFixed(2);
    $('rocket-status').textContent = 'ВЫСОТА: ' + Math.floor(rocketY) + 'м | ТОПЛИВО: ' + Math.floor(fuel) + '%';

    if (Date.now() - lastFuel > 2500 && fuels.length < 2) {
      lastFuel = Date.now();
      var f = document.createElement('div'); f.className = 'fuel-item';
      var fx = 10 + Math.random()*80;
      var fy = rocketY + 100 + Math.random()*150;
      f.style.left = fx + '%'; f.style.bottom = fy + 'px';
      stage.appendChild(f);
      fuels.push({ el: f, x: fx, y: fy, used: false });
    }
    if (Math.random() < 0.03 && asteroids.length < 6) {
      var a = document.createElement('div'); a.className = 'asteroid';
      var ax = 5 + Math.random()*90;
      var ay = rocketY + 200 + Math.random()*200;
      a.style.left = ax + '%'; a.style.bottom = ay + 'px';
      stage.appendChild(a);
      asteroids.push({ el: a, x: ax, y: ay });
    }
    for (var i = 0; i < fuels.length; i++) {
      var f = fuels[i];
      if (!f.used && Math.abs(f.x - rocketX) < 5 && Math.abs(f.y - rocketY) < 30) {
        f.used = true; f.el.remove();
        fuel = Math.min(100, fuel + 40);
      }
    }
    fuels = fuels.filter(function(f){ return !f.used; });
    for (var i = 0; i < asteroids.length; i++) {
      if (Math.abs(asteroids[i].x - rocketX) < 5 && Math.abs(asteroids[i].y - rocketY) < 25) { endRocket(); return; }
    }
    if (fuel <= 0 && rocketY < 20) { endRocket(); return; }
    if (rocketY > stageH - 80) { cashoutRocket(); return; }
    if (Math.random() < 0.005) { endRocket(); return; }
  }, 50);
}
function endRocket() {
  rocketRunning = false;
  if (rocketLoop) { clearInterval(rocketLoop); rocketLoop = null; }
  $('flame').style.display = 'none';
  $('rocket-cashout').style.display = 'none';
  $('rocket-mult').classList.add('crashed');
  $('rocket-status').textContent = 'КРАХ! ПОТЕРЯНО: ' + fmt(rocketBet) + ' ₽';
  setTimeout(initRocket, 3000);
}
$('rocket-cashout').addEventListener('click', function() {
  if (!rocketRunning) return;
  cashoutRocket();
});
function cashoutRocket() {
  rocketRunning = false;
  if (rocketLoop) { clearInterval(rocketLoop); rocketLoop = null; }
  var win = Math.floor(rocketBet * rocketMult);
  changeBalance(win).then(function() {
    $('flame').style.display = 'none';
    $('rocket-cashout').style.display = 'none';
    $('rocket-status').textContent = 'ЗАБРАЛ ' + fmt(win) + ' ₽ (x' + rocketMult.toFixed(2) + ')';
    setTimeout(initRocket, 3000);
  });
}

// ============ ПЛИНКО ============
var plinkoBusy = false;
function initPlinko() {
  plinkoBusy = false;
  var stage = $('plinko-stage');
  var olds = stage.querySelectorAll('.peg,.ball');
  for (var i = 0; i < olds.length; i++) olds[i].remove();
  var rows = 7;
  for (var r = 0; r < rows; r++) {
    var count = r + 3;
    for (var i = 0; i < count; i++) {
      var peg = document.createElement('div');
      peg.className = 'peg';
      peg.style.top = (40 + r * 38) + 'px';
      peg.style.left = 'calc(50% + ' + ((i - (count - 1) / 2) * 32) + 'px)';
      stage.appendChild(peg);
    }
  }
  var mults = [0.5,1,1.5,2,3,5,10,3,2,1.5,1,0.5];
  var bottom = $('plinko-bottom');
  bottom.innerHTML = '';
  for (var i = 0; i < mults.length; i++) {
    var d = document.createElement('div');
    d.className = 'plinko-slot';
    d.textContent = 'x' + mults[i];
    d.style.background = mults[i] >= 3 ? '#ff3a5a' : (mults[i] >= 1.5 ? '#ffaa00' : '#374151');
    bottom.appendChild(d);
  }
  $('plinko-status').textContent = 'ВЫБЕРИ СТАВКУ';
  makeBetButtons('plinko-buttons', playPlinko);
}
function playPlinko(bet) {
  if (plinkoBusy) return;
  if (bet > balance) { showAlert('Недостаточно средств'); return; }
  plinkoBusy = true;
  changeBalance(-bet).then(function() {
    $('plinko-buttons').innerHTML = '';
    $('plinko-status').textContent = 'ШАРИК ПАДАЕТ...';
    var stage = $('plinko-stage');
    var ball = document.createElement('div');
    ball.className = 'ball';
    ball.style.left = 'calc(50% - 8px)';
    ball.style.top = '10px';
    stage.appendChild(ball);

    var mults = [0.5,1,1.5,2,3,5,10,3,2,1.5,1,0.5];
    var weights = [20,20,15,12,8,4,1,4,8,12,15,20];
    var total = 0;
    for (var i = 0; i < weights.length; i++) total += weights[i];
    var rnd = Math.random() * total;
    var idx = 0;
    for (var i = 0; i < weights.length; i++) {
      rnd -= weights[i];
      if (rnd <= 0) { idx = i; break; }
    }
    var finalX = (idx / (mults.length - 1)) * 100;
    var step = 0;
    var steps = 25;
    var anim = setInterval(function() {
      step++;
      var y = 10 + (step / steps) * (stage.clientHeight - 50);
      var x = 50 + (finalX - 50) * (step / steps) + (Math.random() - 0.5) * 12;
      ball.style.top = y + 'px';
      ball.style.left = 'calc(' + x + '% - 8px)';
      if (step >= steps) {
        clearInterval(anim);
        ball.remove();
        var mult = mults[idx];
        var win = Math.floor(bet * mult);
        var done = function() {
          $('plinko-status').innerHTML = 'x' + mult + ' → ' + (win ? ('+' + fmt(win) + ' ₽') : 'МИМО');
          plinkoBusy = false;
          setTimeout(initPlinko, 3000);
        };
        if (win > 0) changeBalance(win).then(done); else done();
      }
    }, 55);
  });
}

// ============ КОРОВА ПЕРЕБЕГАЕТ ДОРОГУ ============
var cowBet = 0, cowRunning = false, cowX = 10, cowY = 20, cowMult = 1.0, cowVel = 0;
var cowLoop = null, carsLoop = null, cowCars = [];

function initCow() {
  if (cowLoop) { clearInterval(cowLoop); cowLoop = null; }
  if (carsLoop) { clearInterval(carsLoop); carsLoop = null; }
  cowBet = 0; cowRunning = false; cowX = 10; cowY = 20; cowMult = 1.0; cowVel = 0; cowCars = [];
  var stage = $('road-stage');
  var olds = stage.querySelectorAll('.road-line,.car');
  for (var i = 0; i < olds.length; i++) olds[i].remove();

  // Линии дороги
  for (var i = 0; i < 5; i++) {
    var line = document.createElement('div');
    line.className = 'road-line';
    line.style.bottom = (60 + i * 70) + 'px';
    stage.appendChild(line);
  }
  $('cow-el').style.left = '10px';
  $('cow-el').style.bottom = '20px';
  $('road-mult').textContent = 'x1.00';
  $('road-mult').classList.remove('crashed');
  $('cow-status').textContent = 'ВЫБЕРИ СТАВКУ';
  $('cow-cashout').style.display = 'none';
  makeBetButtons('cow-buttons', selectCowBet);

  // Спавним машины
  carsLoop = setInterval(function() {
    if (!cowRunning) return;
    if (cowCars.length >= 8) return;
    var car = document.createElement('div');
    car.className = 'car';
    var isLeft = Math.random() < 0.5;
    car.textContent = isLeft ? '🚗' : '🚙';
    car.style.bottom = (60 + Math.floor(Math.random() * 4) * 70) + 'px';
    car.style.left = isLeft ? '-60px' : 'calc(100% + 60px)';
    stage.appendChild(car);
    cowCars.push({
      el: car,
      x: isLeft ? -60 : stage.clientWidth + 60,
      y: parseInt(car.style.bottom),
      speed: (isLeft ? 1 : -1) * (4 + Math.random() * 4),
      isLeft: isLeft
    });
  }, 1200);

  $('cow-left').onmousedown = function() { cowVel = -5; };
  $('cow-right').onmousedown = function() { cowVel = 5; };
  $('cow-left').ontouchstart = function(e) { e.preventDefault(); cowVel = -5; };
  $('cow-right').ontouchstart = function(e) { e.preventDefault(); cowVel = 5; };
  $('cow-left').onmouseup = function() { cowVel = 0; };
  $('cow-right').onmouseup = function() { cowVel = 0; };
  $('cow-left').ontouchend = function() { cowVel = 0; };
  $('cow-right').ontouchend = function() { cowVel = 0; };
}
function selectCowBet(b) {
  if (b > balance) { showAlert('Недостаточно средств'); return; }
  if (cowRunning) { showAlert('Корова уже бежит'); return; }
  cowBet = b;
  if (cowBet > 0 && !cowRunning) {
    // Автостарт после выбора ставки
    setTimeout(function() {
      if (cowBet > 0 && !cowRunning) {
        changeBalance(-cowBet).then(startCowRun);
      }
    }, 300);
  }
}
function startCowRun() {
  cowRunning = true;
  $('cow-buttons').innerHTML = '';
  $('cow-cashout').style.display = 'block';
  var stage = $('road-stage');
  var stageW = stage.clientWidth;

  cowLoop = setInterval(function() {
    if (!cowRunning) return;
    // Движение коровы
    cowX += cowVel;
    if (cowX < 5) cowX = 5;
    if (cowX > 90) cowX = 90;
    $('cow-el').style.left = cowX + '%';

    // Прогресс вверх
    cowY += 0.5;
    $('cow-el').style.bottom = cowY + 'px';
    cowMult = +(1 + cowY / 60).toFixed(2);
    $('road-mult').textContent = 'x' + cowMult.toFixed(2);
    $('cow-status').textContent = 'ВЫСОТА: ' + Math.floor(cowY) + 'м | x' + cowMult.toFixed(2);

    // Движение машин
    for (var i = 0; i < cowCars.length; i++) {
      var c = cowCars[i];
      c.x += c.speed;
      c.el.style.left = c.x + 'px';
      // Проверка столкновения
      var cowPx = (cowX / 100) * stageW;
      if (Math.abs(c.x - cowPx) < 35 && Math.abs(c.y - cowY) < 40) {
        endCow();
        return;
      }
    }
    // Убираем уехавшие машины
    cowCars = cowCars.filter(function(c) {
      if (c.x < -100 || c.x > stageW + 100) { c.el.remove(); return false; }
      return true;
    });

    // Дошла до верха — забрать
    if (cowY > stage.clientHeight - 80) { cashoutCow(); return; }
  }, 50);
}
function endCow() {
  cowRunning = false;
  if (cowLoop) { clearInterval(cowLoop); cowLoop = null; }
  if (carsLoop) { clearInterval(carsLoop); carsLoop = null; }
  $('cow-cashout').style.display = 'none';
  $('road-mult').classList.add('crashed');
  $('cow-status').textContent = '💥 СБИЛИ! ПОТЕРЯНО: ' + fmt(cowBet) + ' ₽';
  setTimeout(initCow, 3000);
}
$('cow-cashout').addEventListener('click', function() {
  if (!cowRunning) return;
  cashoutCow();
});
function cashoutCow() {
  cowRunning = false;
  if (cowLoop) { clearInterval(cowLoop); cowLoop = null; }
  if (carsLoop) { clearInterval(carsLoop); carsLoop = null; }
  var win = Math.floor(cowBet * cowMult);
  changeBalance(win).then(function() {
    $('cow-cashout').style.display = 'none';
    $('cow-status').textContent = 'ЗАБРАЛ ' + fmt(win) + ' ₽ (x' + cowMult.toFixed(2) + ')';
    setTimeout(initCow, 3000);
  });
}

// ============ СКОРОСТЬ ============
var speedBet = 0, speedRunning = false, speedMult = 1.0, speedLoop = null;

function initSpeed() {
  if (speedLoop) { clearInterval(speedLoop); speedLoop = null; }
  speedBet = 0; speedRunning = false; speedMult = 1.0;
  $('speed-mult').textContent = 'x1.00';
  $('speed-mult').classList.remove('crashed');
  $('speed-fill').style.width = '0%';
  $('speed-status').textContent = 'ВЫБЕРИ СТАВКУ';
  $('speed-cashout').style.display = 'none';
  makeBetButtons('speed-buttons', startSpeed);
}
function startSpeed(bet) {
  if (bet > balance) { showAlert('Недостаточно средств'); return; }
  if (speedRunning) return;
  speedBet = bet; speedMult = 1.0; speedRunning = true;
  changeBalance(-bet).then(function() {
    $('speed-buttons').innerHTML = '';
    $('speed-cashout').style.display = 'block';
    $('speed-status').textContent = 'РАЗГОН...';

    var crashPoint = 1 + Math.random() * 15; // x1 - x16

    speedLoop = setInterval(function() {
      speedMult = +(speedMult + 0.08 + Math.random() * 0.15).toFixed(2);
      $('speed-mult').textContent = 'x' + speedMult.toFixed(2);
      var pct = Math.min(100, (speedMult / 16) * 100);
      $('speed-fill').style.width = pct + '%';
      $('speed-status').textContent = 'ПОТЕНЦИАЛ: ' + fmt(Math.floor(speedBet * speedMult)) + ' ₽';

      if (speedMult >= crashPoint) {
        clearInterval(speedLoop); speedLoop = null;
        speedRunning = false;
        $('speed-mult').classList.add('crashed');
        $('speed-status').textContent = '💥 ВЗРЫВ НА x' + speedMult.toFixed(2) + '! ПОТЕРЯНО ' + fmt(speedBet) + ' ₽';
        $('speed-cashout').style.display = 'none';
        setTimeout(initSpeed, 3000);
      }
    }, 100);
  });
}
$('speed-cashout').addEventListener('click', function() {
  if (!speedRunning) return;
  speedRunning = false;
  clearInterval(speedLoop); speedLoop = null;
  var win = Math.floor(speedBet * speedMult);
  changeBalance(win).then(function() {
    $('speed-cashout').style.display = 'none';
    $('speed-status').textContent = 'ЗАБРАЛ ' + fmt(win) + ' ₽ на x' + speedMult.toFixed(2);
    setTimeout(initSpeed, 3000);
  });
});

// ==== ЗАПУСК ====
window.addEventListener('load', function() { loadBalance(); });
</script>
</body>
</html>
"""

async def handle_index(request):
    return web.Response(text=HTML_PAGE, content_type="text/html")

async def handle_get_balance(request):
    try:
        user_id = request.query.get("user_id", "0")
        u = get_user(int(user_id))
        return web.json_response({"balance": u["balance"]})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def handle_post_balance(request):
    try:
        data = await request.json()
        user_id = int(data.get("user_id", 0))
        delta = int(data.get("delta", 0))
        new = update_balance(user_id, delta)
        return web.json_response({"balance": new})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

app = web.Application()
app.router.add_get("/", handle_index)
app.router.add_get("/api/balance", handle_get_balance)
app.router.add_post("/api/balance", handle_post_balance)

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    get_user(message.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 Открыть Казино", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    await message.answer("🎰 <b>Добро пожаловать!</b>\n\nНажми кнопку ниже:", reply_markup=kb, parse_mode="HTML")

async def start_web():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print("✅ Web server on port " + str(PORT))

async def main():
    await start_web()
    print("🤖 Bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
