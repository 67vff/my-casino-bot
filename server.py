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
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False)

def migrate_db():
    db = load_db(); changed = False
    for uid, val in list(db.items()):
        if not isinstance(val, dict):
            try: old = int(val)
            except: old = 10000
            db[uid] = {"balance": old, "inventory": []}; changed = True
        else:
            if "balance" not in val: val["balance"] = 10000; changed = True
            if "inventory" not in val: val["inventory"] = []; changed = True
    if changed: save_db(db)

def get_user(user_id):
    db = load_db(); uid = str(user_id)
    if uid not in db:
        db[uid] = {"balance": 10000, "inventory": []}
        save_db(db)
    else:
        val = db[uid]
        if not isinstance(val, dict):
            try: old = int(val)
            except: old = 10000
            db[uid] = {"balance": old, "inventory": []}
            save_db(db)
        else:
            if "balance" not in val: val["balance"] = 10000; save_db(db)
            if "inventory" not in val: val["inventory"] = []; save_db(db)
    return db[uid]

def save_user(user_id, data):
    db = load_db(); db[str(user_id)] = data; save_db(db)

def get_balance(user_id): return get_user(user_id)["balance"]

def update_balance(user_id, delta):
    u = get_user(user_id)
    u["balance"] = max(0, u["balance"] + delta)
    save_user(user_id, u)
    return u["balance"]

GIFTS = {
    "1": {"name": "АЛМАЗ", "price": 5000, "color": "#88eeff", "shape": "diamond"},
    "2": {"name": "КОРОНА", "price": 15000, "color": "#ffdd44", "shape": "crown"},
    "3": {"name": "ЧЕРЕП", "price": 3000, "color": "#ff3a5a", "shape": "skull"},
    "4": {"name": "ЗВЕЗДА", "price": 25000, "color": "#ffaa00", "shape": "star"},
    "5": {"name": "РАКЕТА", "price": 50000, "color": "#4a3aff", "shape": "rocket"},
    "6": {"name": "ПЛАНЕТА", "price": 100000, "color": "#4aff8a", "shape": "planet"},
}

HTML_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>CASINO</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
* { margin:0; padding:0; box-sizing:border-box; -webkit-tap-highlight-color:transparent; font-family:'Segoe UI',-apple-system,sans-serif; }
body { background:#05050f; color:#e8e8f0; min-height:100vh; padding:14px; overflow-x:hidden; }
.balance { background:linear-gradient(135deg,#1e1e3a,#2a1e4a); border:1px solid #3a2a5a; padding:16px; border-radius:14px; text-align:center; margin-bottom:14px; }
.balance h1 { font-size:11px; opacity:.6; font-weight:400; letter-spacing:2px; }
.balance .amount { font-size:28px; font-weight:800; margin-top:4px; color:#fff; }
.balance .coins { font-size:11px; opacity:.5; margin-top:2px; }
.games { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
.game { background:linear-gradient(160deg,#12122a,#0d0d1f); border-radius:14px; padding:16px 10px; text-align:center; cursor:pointer; border:1px solid #1e1e3a; }
.game:active { transform:scale(.96); border-color:#4a3aff; }
.game .name { font-size:11px; font-weight:700; letter-spacing:1px; text-transform:uppercase; }
.game .desc { font-size:9px; opacity:.4; margin-top:3px; }
.screen { display:none; }
.screen.active { display:block; animation:fadeIn .25s; }
@keyframes fadeIn { from{opacity:0} to{opacity:1} }
.back { background:#12122a; border:1px solid #1e1e3a; color:#fff; padding:9px 14px; border-radius:10px; font-size:12px; margin-bottom:14px; cursor:pointer; }
h2 { font-size:16px; margin-bottom:14px; text-align:center; font-weight:800; letter-spacing:2px; text-transform:uppercase; }
.bet-buttons { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:12px; }
.bet-btn { background:#12122a; border:1px solid #2a2a4a; color:#fff; padding:12px; border-radius:10px; font-size:14px; font-weight:700; cursor:pointer; }
.bet-btn:active { background:#2a2a4a; }
.big-btn { background:linear-gradient(135deg,#4a3aff,#6a4aff); border:none; color:#fff; padding:14px; border-radius:12px; font-size:14px; font-weight:800; width:100%; margin-top:12px; cursor:pointer; letter-spacing:1px; text-transform:uppercase; }
.result-box { text-align:center; padding:20px; margin-top:12px; background:#12122a; border-radius:14px; border:1px solid #2a2a4a; font-size:16px; min-height:80px; display:flex; align-items:center; justify-content:center; flex-direction:column; }

.rocket-stage { position:relative; height:400px; background:linear-gradient(180deg,#000005 0%,#05051a 40%,#0a0a25 100%); border-radius:14px; overflow:hidden; border:1px solid #1e1e3a; margin-top:10px; }
.star { position:absolute; background:#fff; border-radius:50%; }
.rocket-svg { position:absolute; width:30px; height:50px; z-index:5; filter:drop-shadow(0 0 12px #4a3aff); }
.flame { position:absolute; left:50%; transform:translateX(-50%); width:12px; background:radial-gradient(ellipse at top,#ffaa00,#ff4400,transparent); border-radius:50%; opacity:.9; animation:flame .1s infinite alternate; }
@keyframes flame { from{height:14px;opacity:.7} to{height:24px;opacity:1} }
.mult-display { position:absolute; top:45%; left:50%; transform:translate(-50%,-50%); font-size:44px; font-weight:900; color:#4aff8a; text-shadow:0 0 30px #4aff8a; z-index:10; }
.mult-display.crashed { color:#ff3a5a; }
.countdown { position:absolute; top:40%; left:50%; transform:translate(-50%,-50%); font-size:64px; font-weight:900; color:#fff; text-shadow:0 0 40px #4a3aff; z-index:20; }
.countdown.hidden { display:none; }
.fuel-item { position:absolute; width:14px; height:20px; background:linear-gradient(180deg,#ffdd44,#cc9900); border-radius:3px; box-shadow:0 0 12px #ffdd44; z-index:4; }
.asteroid { position:absolute; width:24px; height:24px; background:radial-gradient(circle at 30% 30%,#886644,#332211); border-radius:50%; z-index:4; }
.fuel-bar { position:absolute; top:10px; left:10px; right:10px; height:14px; background:rgba(0,0,0,.6); border-radius:7px; border:1px solid #3a3a5a; overflow:hidden; z-index:10; }
.fuel-fill { height:100%; background:linear-gradient(90deg,#ff3a5a,#ffaa00,#4aff8a); width:100%; transition:width .1s; }
.controls { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:10px; }
.ctrl { background:#1a1a3a; border:1px solid #4a3aff; color:#fff; padding:16px; border-radius:12px; font-size:20px; font-weight:900; cursor:pointer; user-select:none; }
.ctrl:active { background:#4a3aff; }

.wheel-wrap { position:relative; width:280px; height:280px; margin:20px auto; }
.wheel { width:100%; height:100%; border-radius:50%; border:8px solid #2a2a4a; position:relative; transition:transform 5s cubic-bezier(.15,.85,.25,1); overflow:hidden; box-shadow:0 0 50px rgba(74,58,255,.4); }
.wheel-num { position:absolute; font-size:13px; font-weight:900; color:#fff; text-shadow:0 0 6px #000; }
.pointer { position:absolute; top:-14px; left:50%; transform:translateX(-50%); width:0; height:0; border-left:12px solid transparent; border-right:12px solid transparent; border-top:22px solid #ff3a5a; z-index:10; }
.wheel-center { position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:44px; height:44px; background:radial-gradient(circle,#4a3aff,#2a1a8a); border-radius:50%; border:3px solid #6a4aff; z-index:5; display:flex; align-items:center; justify-content:center; font-size:9px; font-weight:900; }

.mines-grid { display:grid; grid-template-columns:repeat(5,1fr); gap:6px; margin-top:12px; }
.mine-cell { aspect-ratio:1; background:#12122a; border:1px solid #2a2a4a; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:22px; cursor:pointer; }
.mine-cell.opened { background:#1a1a3a; cursor:default; }
.mine-cell.mine { background:#3a0a0a; border-color:#ff3a5a; }

.slots { display:flex; justify-content:center; gap:8px; margin:20px 0; }
.slot { width:80px; height:110px; background:linear-gradient(180deg,#1a1a2e,#0f0f1e); border:2px solid #4a3aff; border-radius:14px; display:flex; align-items:center; justify-content:center; font-size:48px; }
.slot.spinning { animation:spin .1s infinite; }
@keyframes spin { 0%{transform:translateY(-6px)} 50%{transform:translateY(6px)} 100%{transform:translateY(-6px)} }

.dice { font-size:80px; text-align:center; margin:20px 0; }
.coin { width:120px; height:120px; border-radius:50%; background:radial-gradient(circle,#ffdd44,#cc9900); margin:20px auto; display:flex; align-items:center; justify-content:center; font-size:60px; font-weight:900; color:#3a2a00; box-shadow:0 0 30px rgba(255,221,68,.6); }
.coin.flipping { animation:flip .3s infinite; }
@keyframes flip { 0%{transform:rotateY(0)} 100%{transform:rotateY(360deg)} }
.case-open { display:grid; grid-template-columns:repeat(5,1fr); gap:4px; margin:20px 0; overflow:hidden; }
.case-item { aspect-ratio:1; background:#12122a; border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:20px; border:1px solid #2a2a4a; }

.nft-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:12px; }
.nft-card { background:linear-gradient(160deg,#12122a,#0a0a1a); border:1px solid #2a2a4a; border-radius:14px; padding:14px; text-align:center; }
.nft-img { width:70px; height:70px; margin:0 auto 6px; }
.nft-name { font-size:11px; font-weight:700; }
.nft-price { font-size:10px; color:#4aff8a; margin:4px 0; }
.nft-btn { background:linear-gradient(135deg,#4a3aff,#6a4aff); border:none; color:#fff; padding:8px 14px; border-radius:8px; font-size:11px; font-weight:700; cursor:pointer; margin-top:4px; }
</style>
</head>
<body>

<div id="menu" class="screen active">
  <div class="balance">
    <h1>БАЛАНС</h1>
    <div class="amount"><span id="balance">100.00</span> ₽</div>
    <div class="coins" id="coins">10000 КОПЕЕК</div>
  </div>
  <div class="games">
    <div class="game" onclick="openGame('rocket')"><div class="name">РАКЕТА</div><div class="desc">УПРАВЛЯЙ / ТОПЛИВО</div></div>
    <div class="game" onclick="openGame('mines')"><div class="name">МИНЫ</div><div class="desc">5x5 / 5 МИН</div></div>
    <div class="game" onclick="openGame('wheel')"><div class="name">РУЛЕТКА</div><div class="desc">КРУГЛАЯ</div></div>
    <div class="game" onclick="openGame('slots')"><div class="name">СЛОТЫ</div><div class="desc">3 БАРАБАНА</div></div>
    <div class="game" onclick="openGame('dice')"><div class="name">КОСТИ</div><div class="desc">УГАДАЙ ЧИСЛО</div></div>
    <div class="game" onclick="openGame('coin')"><div class="name">МОНЕТКА</div><div class="desc">ОРЁЛ / РЕШКА</div></div>
    <div class="game" onclick="openGame('case')"><div class="name">КЕЙСЫ</div><div class="desc">ОТКРОЙ NFT</div></div>
    <div class="game" onclick="openGame('nft')"><div class="name">NFT</div><div class="desc">КОЛЛЕКЦИЯ</div></div>
    <div class="game" onclick="openGame('inventory')"><div class="name">ИНВЕНТАРЬ</div><div class="desc">ТВОИ NFT</div></div>
    <div class="game" onclick="openGame('shop')"><div class="name">МАГАЗИН</div><div class="desc">КУПИТЬ NFT</div></div>
  </div>
</div>

<div id="rocket" class="screen">
  <button class="back" onclick="goMenu()">← НАЗАД</button>
  <h2>РАКЕТА</h2>
  <div class="rocket-stage" id="rocket-stage">
    <div class="fuel-bar"><div class="fuel-fill" id="fuel-fill"></div></div>
    <div class="countdown hidden" id="countdown">10</div>
    <div class="mult-display" id="rocket-mult">x1.00</div>
    <div class="rocket-svg" id="rocket-svg" style="left:calc(50% - 15px);bottom:20px;">
      <svg viewBox="0 0 30 50" width="30" height="50">
        <polygon points="15,0 24,18 24,38 6,38 6,18" fill="#e8e8f0"/>
        <polygon points="15,0 24,18 6,18" fill="#4a3aff"/>
        <circle cx="15" cy="22" r="4" fill="#4a3aff"/>
      </svg>
      <div class="flame" id="flame" style="bottom:-16px;display:none;"></div>
    </div>
  </div>
  <div id="rocket-status" style="text-align:center;margin-top:10px;font-size:12px;opacity:.7;">ЖДЁМ СТАРТА</div>
  <div class="bet-buttons" id="rocket-buttons"></div>
  <div class="controls">
    <button class="ctrl" id="ctrl-left">←</button>
    <button class="ctrl" id="ctrl-right">→</button>
  </div>
  <button id="rocket-cashout" class="big-btn" style="display:none;background:linear-gradient(135deg,#4aff8a,#2acc6a);color:#000;" onclick="cashoutRocket()">ЗАБРАТЬ</button>
</div>

<div id="mines" class="screen">
  <button class="back" onclick="goMenu()">← НАЗАД</button>
  <h2>МИНЫ</h2>
  <div id="mines-status" style="text-align:center;font-size:13px;">ВЫБЕРИ СТАВКУ</div>
  <div class="bet-buttons" id="mines-buttons"></div>
  <div class="mines-grid" id="mines-grid"></div>
  <button id="mines-cashout" class="big-btn" style="display:none;background:linear-gradient(135deg,#4aff8a,#2acc6a);color:#000;" onclick="cashoutMines()">ЗАБРАТЬ</button>
</div>

<div id="wheel" class="screen">
  <button class="back" onclick="goMenu()">← НАЗАД</button>
  <h2>РУЛЕТКА</h2>
  <div class="wheel-wrap">
    <div class="pointer"></div>
    <div class="wheel" id="wheel-el"></div>
    <div class="wheel-center">SPIN</div>
  </div>
  <div id="wheel-status" style="text-align:center;font-size:13px;min-height:30px;">ВЫБЕРИ СТАВКУ</div>
  <div class="bet-buttons" id="wheel-buttons"></div>
</div>

<div id="slots" class="screen">
  <button class="back" onclick="goMenu()">← НАЗАД</button>
  <h2>СЛОТЫ</h2>
  <div class="slots">
    <div class="slot" id="slot0">🍒</div>
    <div class="slot" id="slot1">🍒</div>
    <div class="slot" id="slot2">🍒</div>
  </div>
  <div id="slots-status" style="text-align:center;font-size:13px;min-height:30px;">ВЫБЕРИ СТАВКУ</div>
  <div class="bet-buttons" id="slots-buttons"></div>
</div>

<div id="dice" class="screen">
  <button class="back" onclick="goMenu()">← НАЗАД</button>
  <h2>КОСТИ</h2>
  <div class="dice" id="dice-display">🎲</div>
  <div id="dice-status" style="text-align:center;font-size:13px;min-height:30px;">ВЫБЕРИ ЧИСЛО И СТАВКУ</div>
  <div style="display:grid;grid-template-columns:repeat(6,1fr);gap:6px;margin-top:10px;">
    <button class="bet-btn" onclick="pickDice(1)">1</button>
    <button class="bet-btn" onclick="pickDice(2)">2</button>
    <button class="bet-btn" onclick="pickDice(3)">3</button>
    <button class="bet-btn" onclick="pickDice(4)">4</button>
    <button class="bet-btn" onclick="pickDice(5)">5</button>
    <button class="bet-btn" onclick="pickDice(6)">6</button>
  </div>
  <div class="bet-buttons" id="dice-buttons"></div>
</div>

<div id="coin" class="screen">
  <button class="back" onclick="goMenu()">← НАЗАД</button>
  <h2>МОНЕТКА</h2>
  <div class="coin" id="coin-display">?</div>
  <div id="coin-status" style="text-align:center;font-size:13px;min-height:30px;">ВЫБЕРИ СТОРОНУ</div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px;">
    <button class="bet-btn" onclick="pickCoin('О')">ОРЁЛ</button>
    <button class="bet-btn" onclick="pickCoin('Р')">РЕШКА</button>
  </div>
  <div class="bet-buttons" id="coin-buttons"></div>
</div>

<div id="case" class="screen">
  <button class="back" onclick="goMenu()">← НАЗАД</button>
  <h2>КЕЙСЫ</h2>
  <div class="case-open" id="case-display"></div>
  <div id="case-status" style="text-align:center;font-size:13px;min-height:30px;">ОТКРОЙ КЕЙС ЗА 500 ₽</div>
  <button class="big-btn" onclick="openCase()">ОТКРЫТЬ ЗА 500 ₽</button>
</div>

<div id="nft" class="screen">
  <button class="back" onclick="goMenu()">← НАЗАД</button>
  <h2>NFT</h2>
  <div class="nft-grid" id="nft-list"></div>
</div>

<div id="inventory" class="screen">
  <button class="back" onclick="goMenu()">← НАЗАД</button>
  <h2>ИНВЕНТАРЬ</h2>
  <div class="nft-grid" id="inv-list"></div>
</div>

<div id="shop" class="screen">
  <button class="back" onclick="goMenu()">← НАЗАД</button>
  <h2>МАГАЗИН</h2>
  <div id="shop-list"></div>
</div>

<script>
const tg = window.Telegram.WebApp;
tg.ready(); tg.expand();
const user = tg.initDataUnsafe?.user;
const BETS = [100, 500, 1000, 5000];
let balance = 10000, inventory = [];
let rocketBet = 0, rocketRunning = false, rocketMult = 1.0;
let rocketX = 50, rocketY = 20, fuel = 100, rocketVelocity = 0;
let gameLoop = null, countdownTimer = null;
let minesBet = 0, minesField = [], minesOpened = 0, minesMult = 1.0, minesActive = false;
let dicePick = 0, coinPick = '';

function svgIcon(shape, color) {
  const c = color;
  if (shape==="diamond") return '<svg viewBox="0 0 80 80" class="nft-img"><polygon points="40,5 70,30 40,75 10,30" fill="'+c+'" stroke="#fff" stroke-width="2"/></svg>';
  if (shape==="crown") return '<svg viewBox="0 0 80 80" class="nft-img"><path d="M10,60 L10,30 L25,45 L40,15 L55,45 L70,30 L70,60 Z" fill="'+c+'" stroke="#fff" stroke-width="2"/></svg>';
  if (shape==="skull") return '<svg viewBox="0 0 80 80" class="nft-img"><ellipse cx="40" cy="40" rx="25" ry="28" fill="'+c+'"/><circle cx="30" cy="38" r="6" fill="#000"/><circle cx="50" cy="38" r="6" fill="#000"/></svg>';
  if (shape==="star") return '<svg viewBox="0 0 80 80" class="nft-img"><polygon points="40,5 50,32 78,32 55,50 63,78 40,60 17,78 25,50 2,32 30,32" fill="'+c+'" stroke="#fff"/></svg>';
  if (shape==="rocket") return '<svg viewBox="0 0 80 80" class="nft-img"><polygon points="40,5 52,30 52,60 28,60 28,30" fill="'+c+'" stroke="#fff" stroke-width="2"/></svg>';
  if (shape==="planet") return '<svg viewBox="0 0 80 80" class="nft-img"><circle cx="40" cy="40" r="25" fill="'+c+'"/><ellipse cx="40" cy="40" rx="38" ry="8" fill="none" stroke="#fff" stroke-width="2" transform="rotate(-20 40 40)"/></svg>';
  return '';
}

function fmt(k){ return (k/100).toFixed(2); }

async function loadBalance() {
  if (!user) return;
  try {
    const r = await fetch('/api/balance?user_id=' + user.id);
    const d = await r.json();
    balance = d.balance; inventory = d.inventory || [];
    updateUI();
  } catch(e){}
}
async function changeBalance(delta) {
  if (!user) return;
  const r = await fetch('/api/balance', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({user_id:user.id, delta})
  });
  const d = await r.json();
  balance = d.balance; inventory = d.inventory || [];
  updateUI();
}
function updateUI() {
  document.getElementById('balance').textContent = fmt(balance);
  document.getElementById('coins').textContent = balance + ' КОПЕЕК';
}
function goMenu() {
  document.querySelectorAll('.screen').forEach(s=>s.classList.remove('active'));
  document.getElementById('menu').classList.add('active');
  if (gameLoop){clearInterval(gameLoop);gameLoop=null;}
  if (countdownTimer){clearInterval(countdownTimer);countdownTimer=null;}
  rocketRunning = false;
}
function openGame(n) {
  document.querySelectorAll('.screen').forEach(s=>s.classList.remove('active'));
  document.getElementById(n).classList.add('active');
  if(n==='rocket') initRocket();
  if(n==='mines') initMines();
  if(n==='wheel') initWheel();
  if(n==='slots') initSlots();
  if(n==='dice') initDice();
  if(n==='coin') initCoin();
  if(n==='case') initCase();
  if(n==='nft') renderNFT();
  if(n==='inventory') renderInv();
  if(n==='shop') renderShop();
}
function makeBetButtons(id, cb) {
  const c=document.getElementById(id); c.innerHTML='';
  BETS.forEach(b=>{
    const btn=document.createElement('button');
    btn.className='bet-btn'; btn.textContent=fmt(b)+' ₽';
    btn.onclick=()=>cb(b); c.appendChild(btn);
  });
}

// РАКЕТА
function initRocket() {
  if(gameLoop){clearInterval(gameLoop);gameLoop=null;}
  if(countdownTimer){clearInterval(countdownTimer);countdownTimer=null;}
  rocketBet=0; rocketRunning=false; rocketMult=1.0; rocketX=50; rocketY=20; fuel=100;
  const stage=document.getElementById('rocket-stage');
  stage.querySelectorAll('.star,.fuel-item,.asteroid').forEach(e=>e.remove());
  for(let i=0;i<40;i++){
    const s=document.createElement('div'); s.className='star';
    const sz=Math.random()*2+1;
    s.style.width=sz+'px'; s.style.height=sz+'px';
    s.style.left=Math.random()*100+'%'; s.style.top=Math.random()*100+'%';
    s.style.opacity=Math.random()*0.7+0.3;
    stage.appendChild(s);
  }
  document.getElementById('rocket-svg').style.left='calc(50% - 15px)';
  document.getElementById('rocket-svg').style.bottom='20px';
  document.getElementById('flame').style.display='none';
  document.getElementById('rocket-mult').textContent='x1.00';
  document.getElementById('rocket-mult').classList.remove('crashed');
  document.getElementById('rocket-status').textContent='ЖДЁМ СТАРТА';
  document.getElementById('rocket-cashout').style.display='none';
  document.getElementById('fuel-fill').style.width='100%';
  makeBetButtons('rocket-buttons', selectRocketBet);
  startCountdown();
}
function selectRocketBet(b) {
  if(b>balance){tg.showAlert('Недостаточно средств');return;}
  if(rocketRunning){tg.showAlert('Ракета уже летит');return;}
  rocketBet=b;
}
function startCountdown() {
  let t=10;
  const cd=document.getElementById('countdown');
  cd.classList.remove('hidden'); cd.textContent=t;
  countdownTimer=setInterval(async ()=>{
    t--;
    if(t<=0){
      clearInterval(countdownTimer);countdownTimer=null;
      cd.classList.add('hidden');
      if(rocketBet>0){ await changeBalance(-rocketBet); launchRocket(); }
      else { setTimeout(initRocket, 500); }
      return;
    }
    cd.textContent=t;
  },1000);
}
function launchRocket() {
  rocketRunning=true;
  document.getElementById('rocket-buttons').innerHTML='';
  document.getElementById('flame').style.display='block';
  document.getElementById('rocket-cashout').style.display='block';
  const stage=document.getElementById('rocket-stage');
  const stageH=stage.clientHeight;
  let asteroids=[], fuels=[], lastFuel=0;
  document.getElementById('ctrl-left').onmousedown = ()=>{ rocketVelocity = -5; };
  document.getElementById('ctrl-right').onmousedown = ()=>{ rocketVelocity = 5; };
  document.getElementById('ctrl-left').ontouchstart = (e)=>{ e.preventDefault(); rocketVelocity = -5; };
  document.getElementById('ctrl-right').ontouchstart = (e)=>{ e.preventDefault(); rocketVelocity = 5; };
  document.getElementById('ctrl-left').onmouseup = ()=>{ rocketVelocity = 0; };
  document.getElementById('ctrl-right').onmouseup = ()=>{ rocketVelocity = 0; };
  document.getElementById('ctrl-left').ontouchend = ()=>{ rocketVelocity = 0; };
  document.getElementById('ctrl-right').ontouchend = ()=>{ rocketVelocity = 0; };
  gameLoop = setInterval(()=>{
    if(!rocketRunning) return;
    rocketX += rocketVelocity;
    if(rocketX<2) rocketX=2;
    if(rocketX>98) rocketX=98;
    if(fuel>0) rocketY += 0.6;
    document.getElementById('rocket-svg').style.left = rocketX+'%';
    document.getElementById('rocket-svg').style.bottom = rocketY+'px';
    fuel -= 0.4;
    if(fuel<0) fuel=0;
    document.getElementById('fuel-fill').style.width = fuel+'%';
    rocketMult = +(1 + rocketY/40).toFixed(2);
    document.getElementById('rocket-mult').textContent = 'x'+rocketMult.toFixed(2);
    document.getElementById('rocket-status').textContent = 'ВЫСОТА: '+Math.floor(rocketY)+'м | ТОПЛИВО: '+Math.floor(fuel)+'%';
    if(Date.now() - lastFuel > 2500 && fuels.length < 2){
      lastFuel = Date.now();
      const f=document.createElement('div'); f.className='fuel-item';
      const fx = 10+Math.random()*80;
      const fy = rocketY + 100 + Math.random()*150;
      f.style.left = fx+'%'; f.style.bottom = fy+'px';
      stage.appendChild(f);
      fuels.push({el:f, x:fx, y:fy, used:false});
    }
    if(Math.random()<0.03 && asteroids.length<6){
      const a=document.createElement('div'); a.className='asteroid';
      const ax = 5+Math.random()*90;
      const ay = rocketY + 200 + Math.random()*200;
      a.style.left = ax+'%'; a.style.bottom = ay+'px';
      stage.appendChild(a);
      asteroids.push({el:a, x:ax, y:ay});
    }
    fuels.forEach(f=>{
      if(!f.used && Math.abs(f.x-rocketX)<5 && Math.abs(f.y-rocketY)<30){
        f.used=true; f.el.remove(); fuel = Math.min(100, fuel+40);
      }
    });
    fuels = fuels.filter(f=>!f.used);
    for(let a of asteroids){
      if(Math.abs(a.x-rocketX)<5 && Math.abs(a.y-rocketY)<25){ endRocket(); return; }
    }
    if(fuel<=0 && rocketY<20){ endRocket(); return; }
    if(rocketY > stageH-80){ cashoutRocket(); return; }
    if(Math.random()<0.005){ endRocket(); return; }
  }, 50);
}
function endRocket() {
  rocketRunning=false;
  if(gameLoop){clearInterval(gameLoop);gameLoop=null;}
  document.getElementById('flame').style.display='none';
  document.getElementById('rocket-cashout').style.display='none';
  document.getElementById('rocket-mult').classList.add('crashed');
  document.getElementById('rocket-status').textContent = 'КРАХ! ПОТЕРЯНО: '+fmt(rocketBet)+' ₽';
  setTimeout(initRocket, 3000);
}
async function cashoutRocket() {
  if(!rocketRunning) return;
  rocketRunning=false;
  if(gameLoop){clearInterval(gameLoop);gameLoop=null;}
  const win=Math.floor(rocketBet*rocketMult);
  await changeBalance(win);
  document.getElementById('flame').style.display='none';
  document.getElementById('rocket-cashout').style.display='none';
  document.getElementById('rocket-status').textContent='ЗАБРАЛ '+fmt(win)+' ₽ (x'+rocketMult.toFixed(2)+')';
  setTimeout(initRocket,3000);
}

// МИНЫ
function initMines() {
  minesBet=0; minesField=[]; minesOpened=0; minesMult=1.0; minesActive=false;
  document.getElementById('mines-status').textContent='ВЫБЕРИ СТАВКУ';
  document.getElementById('mines-grid').innerHTML='';
  document.getElementById('mines-cashout').style.display='none';
  makeBetButtons('mines-buttons', startMines);
}
async function startMines(bet) {
  if(bet>balance){tg.showAlert('Недостаточно средств');return;}
  if(minesActive) return;
  minesBet=bet; minesOpened=0; minesMult=1.0; minesActive=true;
  await changeBalance(-bet);
  document.getElementById('mines-buttons').innerHTML='';
  document.getElementById('mines-cashout').style.display='block';
  minesField = Array(20).fill('gem').concat(Array(5).fill('mine'));
  for(let i=minesField.length-1;i>0;i--){
    const j=Math.floor(Math.random()*(i+1));
    [minesField[i],minesField[j]]=[minesField[j],minesField[i]];
  }
  const c=document.getElementById('mines-grid'); c.innerHTML='';
  for(let i=0;i<25;i++){
    const cell=document.createElement('div');
    cell.className='mine-cell';
    cell.onclick=()=>openMine(i, cell);
    c.appendChild(cell);
  }
  document.getElementById('mines-status').textContent='МНОЖИТЕЛЬ: x'+minesMult.toFixed(2);
}
async function openMine(i, cell) {
  if(!minesActive || cell.classList.contains('opened')) return;
  cell.classList.add('opened');
  if(minesField[i]==='mine'){
    cell.classList.add('mine'); cell.textContent='💥';
    minesActive=false;
    document.getElementById('mines-status').textContent='БУМ! ПОТЕРЯНО: '+fmt(minesBet)+' ₽';
    document.getElementById('mines-cashout').style.display='none';
    const cells=document.querySelectorAll('#mines-grid .mine-cell');
    minesField.forEach((v,idx)=>{ if(v==='mine') cells[idx].textContent='💣'; });
    setTimeout(initMines,3000);
    return;
  }
  cell.textContent='💎';
  minesOpened++;
  minesMult = +(1 + minesOpened*0.3).toFixed(2);
  document.getElementById('mines-status').textContent='МНОЖИТЕЛЬ: x'+minesMult.toFixed(2)+' | ПОТЕНЦИАЛ: '+fmt(Math.floor(minesBet*minesMult))+' ₽';
}
async function cashoutMines() {
  if(!minesActive) return;
  minesActive=false;
  const win=Math.floor(minesBet*minesMult);
  await changeBalance(win);
  document.getElementById('mines-cashout').style.display='none';
  document.getElementById('mines-status').textContent='ЗАБРАЛ '+fmt(win)+' ₽ (x'+minesMult.toFixed(2)+')';
  setTimeout(initMines,3000);
}

// РУЛЕТКА
function initWheel() {
  const wheel=document.getElementById('wheel-el');
  wheel.style.transition='none'; wheel.style.transform='rotate(0deg)';
  setTimeout(()=>wheel.style.transition='transform 5s cubic-bezier(.15,.85,.25,1)',50);
  wheel.innerHTML='';
  const mults=[2,0,5,0,3,0,10,0,2,0,5,0];
  const colors=['#ff3a5a','#12122a','#ffaa00','#12122a','#4aff8a','#12122a','#4a3aff','#12122a','#ff3a5a','#12122a','#ffaa00','#12122a'];
  mults.forEach((m,i)=>{
    const seg=document.createElement('div');
    seg.style.cssText='position:absolute;width:50%;height:50%;top:0;left:50%;transform-origin:0% 100%;transform:rotate('+(i*30)+'deg);background:'+colors[i]+';clip-path:polygon(0 0,100% 0,0 100%);';
    wheel.appendChild(seg);
    const num=document.createElement('div');
    num.className='wheel-num';
    num.textContent=m===0?'—':'x'+m;
    num.style.cssText='position:absolute;top:22px;left:50%;transform:translateX(-50%) rotate('+(i*30+15)+'deg);';
    seg.appendChild(num);
  });
  document.getElementById('wheel-status').textContent='ВЫБЕРИ СТАВКУ';
  makeBetButtons('wheel-buttons', playWheel);
}
async function playWheel(bet) {
  if(bet>balance){tg.showAlert('Недостаточно средств');return;}
  await changeBalance(-bet);
  document.getElementById('wheel-buttons').innerHTML='';
  document.getElementById('wheel-status').textContent='КРУТИМ...';
  const mults=[2,0,5,0,3,0,10,0,2,0,5,0];
  const idx=Math.floor(Math.random()*12);
  const mult=mults[idx];
  const wheel=document.getElementById('wheel-el');
  wheel.style.transform='rotate('+(360*6+(360-idx*30))+'deg)';
  await new Promise(r=>setTimeout(r,5200));
  const win=Math.floor(bet*mult);
  if(win>0) await changeBalance(win);
  document.getElementById('wheel-status').textContent = mult ? 'ВЫПАЛО x'+mult+'! ВЫИГРЫШ '+fmt(win)+' ₽' : 'МИМО';
  setTimeout(initWheel,3000);
}

// СЛОТЫ
function initSlots() {
  document.getElementById('slots-status').textContent='ВЫБЕРИ СТАВКУ';
  makeBetButtons('slots-buttons', playSlots);
}
async function playSlots(bet) {
  if(bet>balance){tg.showAlert('Недостаточно средств');return;}
  await changeBalance(-bet);
  const symbols=['🍒','🍋','🍊','💎','7️⃣'];
  document.getElementById('slots-buttons').innerHTML='';
  document.getElementById('slots-status').textContent='КРУТИМ...';
  for(let i=0;i<3;i++) document.getElementById('slot'+i).classList.add('spinning');
  const final=[symbols[Math.floor(Math.random()*5)],symbols[Math.floor(Math.random()*5)],symbols[Math.floor(Math.random()*5)]];
  for(let i=0;i<3;i++){
    await new Promise(r=>setTimeout(r,700+i*500));
    document.getElementById('slot'+i).classList.remove('spinning');
    document.getElementById('slot'+i).textContent=final[i];
  }
  let mult=0;
  if(final[0]===final[1]&&final[1]===final[2]) mult = final[0]==='7️⃣'?10:5;
  else if(final[0]===final[1]||final[1]===final[2]) mult=2;
  const win=Math.floor(bet*mult);
  if(win>0) await changeBalance(win);
  document.getElementById('slots-status').textContent = mult ? 'ВЫИГРЫШ: +'+fmt(win)+' ₽ (x'+mult+')' : 'НЕ ПОВЕЗЛО';
  setTimeout(initSlots,2500);
}

// КОСТИ
function initDice() {
  dicePick = 0;
  document.getElementById('dice-display').textContent='🎲';
  document.getElementById('dice-status').textContent='ВЫБЕРИ ЧИСЛО И СТАВКУ';
  makeBetButtons('dice-buttons', playDice);
}
function pickDice(n) {
  dicePick = n;
  document.getElementById('dice-status').textContent = 'ВЫБРАНО: '+n+' | ВЫБЕРИ СТАВКУ';
}
async function playDice(bet) {
  if(!dicePick){tg.showAlert('Выбери число');return;}
  if(bet>balance){tg.showAlert('Недостаточно средств');return;}
  await changeBalance(-bet);
  document.getElementById('dice-buttons').innerHTML='';
  document.getElementById('dice-display').textContent='🎲';
  await new Promise(r=>setTimeout(r,1000));
  const result = Math.floor(Math.random()*6)+1;
  const faces = ['','⚀','⚁','⚂','⚃','⚄','⚅'];
  document.getElementById('dice-display').textContent = faces[result];
  if(result === dicePick){
    const win = bet*6;
    await changeBalance(win);
    document.getElementById('dice-status').textContent='ВЫПАЛО '+result+'! ВЫИГРЫШ '+fmt(win)+' ₽ (x6)';
  } else {
    document.getElementById('dice-status').textContent='ВЫПАЛО '+result+'. МИМО. ПОТЕРЯНО '+fmt(bet)+' ₽';
  }
  setTimeout(initDice,3000);
}

// МОНЕТКА
function initCoin() {
  coinPick = '';
  document.getElementById('coin-display').textContent='?';
  document.getElementById('coin-status').textContent='ВЫБЕРИ СТОРОНУ';
  makeBetButtons('coin-buttons', playCoin);
}
function pickCoin(s) {
  coinPick = s;
  document.getElementById('coin-status').textContent = 'ВЫБРАНО: '+(s==='О'?'ОРЁЛ':'РЕШКА')+' | ВЫБЕРИ СТАВКУ';
}
async function playCoin(bet) {
  if(!coinPick){tg.showAlert('Выбери сторону');return;}
  if(bet>balance){tg.showAlert('Недостаточно средств');return;}
  await changeBalance(-bet);
  document.getElementById('coin-buttons').innerHTML='';
  const cd = document.getElementById('coin-display');
  cd.classList.add('flipping');
  await new Promise(r=>setTimeout(r,1500));
  cd.classList.remove('flipping');
  const result = Math.random()<0.5?'О':'Р';
  cd.textContent = result==='О'?'ОРЁЛ':'РЕШКА';
  if(result === coinPick){
    const win = bet*2;
    await changeBalance(win);
    document.getElementById('coin-status').textContent='ВЫИГРЫШ '+fmt(win)+' ₽ (x2)';
  } else {
    document.getElementById('coin-status').textContent='МИМО. ПОТЕРЯНО '+fmt(bet)+' ₽';
  }
  setTimeout(initCoin,3000);
}

// КЕЙСЫ
function initCase() {
  document.getElementById('case-status').textContent='ОТКРОЙ КЕЙС ЗА 500 ₽';
  const c=document.getElementById('case-display'); c.innerHTML='';
  const all = ['💎','👑','💀','⭐','🚀','🪐','🎁','💰','🔮','🍀'];
  for(let i=0;i<5;i++){
    const d=document.createElement('div'); d.className='case-item';
    d.textContent = all[Math.floor(Math.random()*all.length)];
    c.appendChild(d);
  }
}
async function openCase() {
  if(balance < 500){tg.showAlert('Нужно 500 ₽');return;}
  await changeBalance(-500);
  const keys = Object.keys(GIFTS);
  const winId = keys[Math.floor(Math.random()*keys.length)];
  const win = GIFTS[winId];
  inventory.push(winId);
  // сохраняем на сервере
  await fetch('/api/balance', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user_id:user.id, delta:0})});
  const c=document.getElementById('case-display'); c.innerHTML='';
  const d=document.createElement('div'); d.className='case-item';
  d.style.gridColumn='1 / -1'; d.style.fontSize='60px';
  d.textContent = win.name;
  c.appendChild(d);
  document.getElementById('case-status').textContent = 'ВЫПАЛО: '+win.name+' ('+fmt(win.price)+' ₽)';
}

// NFT
function renderNFT() {
  const c=document.getElementById('nft-list'); c.innerHTML='';
  Object.keys(GIFTS).forEach(id=>{
    const n=GIFTS[id];
    const d=document.createElement('div'); d.className='nft-card';
    d.innerHTML = svgIcon(n.shape, n.color) + '<div class="nft-name">'+n.name+'</div><div class="nft-price">'+fmt(n.price)+' ₽</div><button class="nft-btn" onclick="buyNFT(\\''+id+'\\')">КУПИТЬ</button>';
    c.appendChild(d);
  });
}
async function buyNFT(id) {
  const r=await fetch('/api/buy',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user_id:user.id, gift_id:id})});
  const d=await r.json();
  if(d.error){tg.showAlert(d.error);return;}
  balance=d.balance; inventory=d.inventory; updateUI();
  tg.showAlert('Куплено!');
}
function renderInv() {
  const c=document.getElementById('inv-list'); c.innerHTML='';
  if(!inventory||inventory.length===0){
    c.innerHTML='<div style="grid-column:1/-1;text-align:center;opacity:.5;padding:40px;font-size:12px;">ПУСТО</div>';
    return;
  }
  inventory.forEach((gid,i)=>{
    const n=GIFTS[gid]; if(!n) return;
    const d=document.createElement('div'); d.className='nft-card';
    d.innerHTML = svgIcon(n.shape,n.color) + '<div class="nft-name">'+n.name+'</div><div class="nft-price">'+fmt(n.price)+' ₽</div><button class="nft-btn" style="background:linear-gradient(135deg,#ff3a5a,#cc2244);" onclick="sellNFT('+i+')">ПРОДАТЬ</button>';
    c.appendChild(d);
  });
}
async function sellNFT(index) {
  const r=await fetch('/api/sell',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user_id:user.id, index})});
  const d=await r.json();
  if(d.error){tg.showAlert(d.error);return;}
  balance=d.balance; inventory=d.inventory; updateUI();
  renderInv();
}
function renderShop() {
  const c=document.getElementById('shop-list'); c.innerHTML='';
  Object.keys(GIFTS).forEach(id=>{
    const n=GIFTS[id];
    const d=document.createElement('div'); d.className='nft-card'; d.style.marginBottom='10px';
    d.innerHTML = svgIcon(n.shape,n.color) + '<div class="nft-name">'+n.name+'</div><div class="nft-price">'+fmt(n.price)+' ₽</div><button class="nft-btn" onclick="buyNFT(\\''+id+'\\')">КУПИТЬ</button>';
    c.appendChild(d);
  });
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
    print("✅ Web server on port " + str(PORT))

async def main():
    migrate_db()
    await start_web()
    print("🤖 Bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
