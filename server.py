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
    db = load_db()
    changed = False
    for uid, val in list(db.items()):
        if not isinstance(val, dict):
            try:
                old = int(val)
            except Exception:
                old = 10000
            db[uid] = {"balance": old, "inventory": []}
            changed = True
        else:
            if "balance" not in val:
                val["balance"] = 10000
                changed = True
            if "inventory" not in val:
                val["inventory"] = []
                changed = True
    if changed:
        save_db(db)

def get_user(user_id):
    db = load_db()
    uid = str(user_id)
    if uid not in db:
        db[uid] = {"balance": 10000, "inventory": []}
        save_db(db)
    else:
        val = db[uid]
        if not isinstance(val, dict):
            try:
                old = int(val)
            except Exception:
                old = 10000
            db[uid] = {"balance": old, "inventory": []}
            save_db(db)
        else:
            if "balance" not in val:
                val["balance"] = 10000
                save_db(db)
            if "inventory" not in val:
                val["inventory"] = []
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
.game { background:linear-gradient(160deg,#12122a,#0d0d1f); border-radius:14px; padding:18px 10px; text-align:center; cursor:pointer; border:1px solid #1e1e3a; transition:all .15s; }
.game:active { transform:scale(.96); border-color:#4a3aff; }
.game .name { font-size:12px; font-weight:700; letter-spacing:1px; text-transform:uppercase; }
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

.rocket-stage { position:relative; height:420px; background:linear-gradient(180deg,#000005 0%,#05051a 40%,#0a0a25 100%); border-radius:14px; overflow:hidden; border:1px solid #1e1e3a; margin-top:10px; }
.star { position:absolute; background:#fff; border-radius:50%; }
.rocket-svg { position:absolute; left:50%; transform:translateX(-50%); width:36px; height:60px; transition:bottom .12s linear; z-index:5; filter:drop-shadow(0 0 12px #4a3aff); }
.flame { position:absolute; left:50%; transform:translateX(-50%); width:14px; height:30px; background:radial-gradient(ellipse at top,#ffaa00,#ff4400,transparent); border-radius:50%; opacity:.9; animation:flame .1s infinite alternate; }
@keyframes flame { from{height:20px;opacity:.7} to{height:34px;opacity:1} }
.mult-display { position:absolute; top:45%; left:50%; transform:translate(-50%,-50%); font-size:48px; font-weight:900; color:#4aff8a; text-shadow:0 0 30px #4aff8a; z-index:10; letter-spacing:-2px; }
.mult-display.crashed { color:#ff3a5a; text-shadow:0 0 30px #ff3a5a; }
.countdown { position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); font-size:72px; font-weight:900; color:#fff; text-shadow:0 0 40px #4a3aff; z-index:20; }
.countdown.hidden { display:none; }
.bets-list { position:absolute; top:10px; left:10px; right:10px; max-height:120px; overflow-y:auto; z-index:15; }
.bet-row { display:flex; justify-content:space-between; padding:6px 10px; background:rgba(20,20,40,.8); border-radius:8px; margin-bottom:4px; font-size:11px; border:1px solid #1e1e3a; }
.bet-row .name { color:#8a8aff; font-weight:700; }
.bet-row .amount { color:#4aff8a; font-weight:700; }

.plane-stage { position:relative; height:420px; background:linear-gradient(180deg,#001a2a 0%,#003355 60%,#005588 100%); border-radius:14px; overflow:hidden; border:1px solid #1e3a5a; margin-top:10px; }
.cloud { position:absolute; background:rgba(255,255,255,.1); border-radius:50%; filter:blur(20px); }
.plane-svg { position:absolute; left:50%; transform:translateX(-50%); width:50px; height:30px; transition:bottom .15s linear; z-index:5; filter:drop-shadow(0 0 10px #ffaa00); }
.balloon { position:absolute; width:18px; height:22px; background:radial-gradient(circle at 30% 30%,#ff6a8a,#cc2255); border-radius:50% 50% 40% 40%; z-index:3; }
.balloon.gold { background:radial-gradient(circle at 30% 30%,#ffdd44,#cc9900); }
.balloon.diamond { background:radial-gradient(circle at 30% 30%,#88eeff,#2266cc); }
.fuel-bar { position:absolute; top:10px; right:10px; width:120px; height:20px; background:rgba(0,0,0,.6); border-radius:10px; border:1px solid #3a5a7a; overflow:hidden; z-index:10; }
.fuel-fill { height:100%; background:linear-gradient(90deg,#ff3a5a,#ffaa00,#4aff8a); width:100%; transition:width .3s; }
.fuel-text { position:absolute; top:12px; right:14px; font-size:10px; font-weight:700; z-index:11; color:#fff; }
.plane-alt { position:absolute; top:40px; right:14px; font-size:12px; color:#4aff8a; font-weight:700; z-index:10; }

.wheel-wrap { position:relative; width:300px; height:300px; margin:20px auto; }
.wheel { width:100%; height:100%; border-radius:50%; border:10px solid #2a2a4a; position:relative; transition:transform 5s cubic-bezier(.15,.85,.25,1); overflow:hidden; box-shadow:0 0 50px rgba(74,58,255,.4),inset 0 0 30px rgba(0,0,0,.8); }
.wheel-num { position:absolute; font-size:14px; font-weight:900; color:#fff; text-shadow:0 0 6px #000,0 0 10px #000; }
.pointer { position:absolute; top:-16px; left:50%; transform:translateX(-50%); width:0; height:0; border-left:14px solid transparent; border-right:14px solid transparent; border-top:24px solid #ff3a5a; z-index:10; filter:drop-shadow(0 0 8px #ff3a5a); }
.wheel-center { position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:50px; height:50px; background:radial-gradient(circle,#4a3aff,#2a1a8a); border-radius:50%; border:3px solid #6a4aff; z-index:5; display:flex; align-items:center; justify-content:center; font-size:10px; font-weight:900; }

.nft-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:12px; }
.nft-card { background:linear-gradient(160deg,#12122a,#0a0a1a); border:1px solid #2a2a4a; border-radius:14px; padding:14px; text-align:center; }
.nft-img { width:80px; height:80px; margin:0 auto 8px; }
.nft-name { font-size:11px; font-weight:700; }
.nft-price { font-size:10px; color:#4aff8a; margin:4px 0; }
.nft-btn { background:linear-gradient(135deg,#4a3aff,#6a4aff); border:none; color:#fff; padding:8px 16px; border-radius:8px; font-size:11px; font-weight:700; cursor:pointer; margin-top:4px; }
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
    <div class="game" onclick="openGame('rocket')"><div class="name">РАКЕТА</div><div class="desc">10 СЕК / КРАХ</div></div>
    <div class="game" onclick="openGame('plane')"><div class="name">САМОЛЁТ</div><div class="desc">ШАРИКИ / СТАНЦИЯ</div></div>
    <div class="game" onclick="openGame('wheel')"><div class="name">РУЛЕТКА</div><div class="desc">КРУТИ КОЛЕСО</div></div>
    <div class="game" onclick="openGame('nft')"><div class="name">NFT</div><div class="desc">КОЛЛЕКЦИЯ</div></div>
    <div class="game" onclick="openGame('inventory')"><div class="name">ИНВЕНТАРЬ</div><div class="desc">ТВОИ NFT</div></div>
    <div class="game" onclick="openGame('shop')"><div class="name">МАГАЗИН</div><div class="desc">КУПИТЬ NFT</div></div>
  </div>
</div>

<div id="rocket" class="screen">
  <button class="back" onclick="goMenu()">← НАЗАД</button>
  <h2>РАКЕТА</h2>
  <div class="rocket-stage" id="rocket-stage">
    <div class="countdown hidden" id="countdown">10</div>
    <div class="mult-display" id="rocket-mult">x1.00</div>
    <div class="rocket-svg" id="rocket-svg">
      <svg viewBox="0 0 36 60" width="36" height="60">
        <polygon points="18,0 28,20 28,45 8,45 8,20" fill="#e8e8f0"/>
        <polygon points="18,0 28,20 8,20" fill="#4a3aff"/>
        <rect x="12" y="22" width="12" height="8" fill="#4a3aff"/>
        <polygon points="8,45 2,55 8,55" fill="#ff3a5a"/>
        <polygon points="28,45 34,55 28,55" fill="#ff3a5a"/>
        <rect x="14" y="50" width="8" height="6" fill="#333"/>
      </svg>
      <div class="flame" id="flame" style="bottom:-20px;display:none;"></div>
    </div>
    <div class="bets-list" id="bets-list"></div>
  </div>
  <div id="rocket-status" style="text-align:center;margin-top:12px;font-size:12px;opacity:.7;">ВЫБЕРИ СТАВКУ</div>
  <div id="rocket-buttons" class="bet-buttons"></div>
  <div id="rocket-confirm" style="display:none;">
    <button class="big-btn" onclick="confirmRocketBet()">ПОДТВЕРДИТЬ СТАВКУ</button>
  </div>
  <button id="rocket-cashout" class="big-btn" style="display:none;background:linear-gradient(135deg,#4aff8a,#2acc6a);color:#000;" onclick="cashoutRocket()">ЗАБРАТЬ</button>
</div>

<div id="plane" class="screen">
  <button class="back" onclick="goMenu()">← НАЗАД</button>
  <h2>САМОЛЁТ</h2>
  <div class="plane-stage" id="plane-stage">
    <div class="fuel-bar"><div class="fuel-fill" id="fuel-fill"></div></div>
    <div class="fuel-text" id="fuel-text">100%</div>
    <div class="plane-alt" id="plane-alt">0 м</div>
    <div class="plane-svg" id="plane-svg">
      <svg viewBox="0 0 50 30" width="50" height="30">
        <polygon points="0,15 20,10 25,0 30,10 50,15 30,18 25,30 20,18" fill="#e8e8f0"/>
        <polygon points="20,10 30,10 25,18" fill="#4a3aff"/>
        <circle cx="25" cy="14" r="3" fill="#4a3aff"/>
      </svg>
    </div>
  </div>
  <div id="plane-status" style="text-align:center;margin-top:12px;font-size:12px;opacity:.7;">ВЫБЕРИ СТАВКУ</div>
  <div id="plane-buttons" class="bet-buttons"></div>
  <button id="plane-cashout" class="big-btn" style="display:none;background:linear-gradient(135deg,#4aff8a,#2acc6a);color:#000;" onclick="cashoutPlane()">ЗАБРАТЬ</button>
</div>

<div id="wheel" class="screen">
  <button class="back" onclick="goMenu()">← НАЗАД</button>
  <h2>РУЛЕТКА</h2>
  <div class="wheel-wrap">
    <div class="pointer"></div>
    <div class="wheel" id="wheel-el"></div>
    <div class="wheel-center">x</div>
  </div>
  <div id="wheel-status" style="text-align:center;font-size:12px;opacity:.7;min-height:30px;">ВЫБЕРИ СТАВКУ</div>
  <div id="wheel-buttons" class="bet-buttons"></div>
</div>

<div id="nft" class="screen">
  <button class="back" onclick="goMenu()">← НАЗАД</button>
  <h2>NFT КОЛЛЕКЦИЯ</h2>
  <div class="nft-grid" id="nft-list"></div>
</div>

<div id="inventory" class="screen">
  <button class="back" onclick="goMenu()">← НАЗАД</button>
  <h2>ИНВЕНТАРЬ</h2>
  <div class="nft-grid" id="inv-list"></div>
</div>

<div id="shop" class="screen">
  <button class="back" onclick="goMenu()">← НАЗАД</button>
  <h2>МАГАЗИН NFT</h2>
  <div id="shop-list"></div>
</div>

<script>
const tg = window.Telegram.WebApp;
tg.ready(); tg.expand();
const user = tg.initDataUnsafe?.user;
const BETS = [100, 500, 1000, 5000];
let balance = 10000, inventory = [];
let rocketBet = 0, rocketInterval = null, rocketMult = 1.0, rocketBottom = 20;
let planeBet = 0, planeInterval = null, planeMult = 1.0, planeBottom = 40, planeFuel = 100;
let selectedBet = 0;

function svgIcon(shape, color) {
  const c = color;
  if (shape==="diamond") return '<svg viewBox="0 0 80 80" class="nft-img"><polygon points="40,5 70,30 40,75 10,30" fill="'+c+'" stroke="#fff" stroke-width="2"/><polygon points="40,5 55,30 40,40 25,30" fill="#fff" opacity=".3"/></svg>';
  if (shape==="crown") return '<svg viewBox="0 0 80 80" class="nft-img"><path d="M10,60 L10,30 L25,45 L40,15 L55,45 L70,30 L70,60 Z" fill="'+c+'" stroke="#fff" stroke-width="2"/><circle cx="40" cy="55" r="4" fill="#fff"/></svg>';
  if (shape==="skull") return '<svg viewBox="0 0 80 80" class="nft-img"><ellipse cx="40" cy="40" rx="25" ry="28" fill="'+c+'"/><circle cx="30" cy="38" r="6" fill="#000"/><circle cx="50" cy="38" r="6" fill="#000"/><rect x="32" y="55" width="16" height="12" fill="#000"/></svg>';
  if (shape==="star") return '<svg viewBox="0 0 80 80" class="nft-img"><polygon points="40,5 50,32 78,32 55,50 63,78 40,60 17,78 25,50 2,32 30,32" fill="'+c+'" stroke="#fff" stroke-width="1"/></svg>';
  if (shape==="rocket") return '<svg viewBox="0 0 80 80" class="nft-img"><polygon points="40,5 52,30 52,60 28,60 28,30" fill="'+c+'" stroke="#fff" stroke-width="2"/><polygon points="40,5 52,30 28,30" fill="#fff" opacity=".3"/><polygon points="28,60 20,72 28,72" fill="#ff3a5a"/><polygon points="52,60 60,72 52,72" fill="#ff3a5a"/></svg>';
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
  if (rocketInterval){clearInterval(rocketInterval);rocketInterval=null;}
  if (planeInterval){clearInterval(planeInterval);planeInterval=null;}
}
function openGame(n) {
  document.querySelectorAll('.screen').forEach(s=>s.classList.remove('active'));
  document.getElementById(n).classList.add('active');
  if(n==='rocket') initRocket();
  if(n==='plane') initPlane();
  if(n==='wheel') initWheel();
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

function initRocket() {
  if(rocketInterval){clearInterval(rocketInterval);rocketInterval=null;}
  rocketBet=0; rocketMult=1.0; rocketBottom=20; selectedBet=0;
  const stage = document.getElementById('rocket-stage');
  stage.querySelectorAll('.star,.trail').forEach(e=>e.remove());
  for(let i=0;i<40;i++){
    const s=document.createElement('div'); s.className='star';
    const sz=Math.random()*2+1;
    s.style.width=sz+'px'; s.style.height=sz+'px';
    s.style.left=Math.random()*100+'%'; s.style.top=Math.random()*100+'%';
    s.style.opacity=Math.random()*0.7+0.3;
    stage.appendChild(s);
  }
  document.getElementById('rocket-svg').style.bottom='20px';
  document.getElementById('flame').style.display='none';
  document.getElementById('rocket-mult').textContent='x1.00';
  document.getElementById('rocket-mult').classList.remove('crashed');
  document.getElementById('rocket-status').textContent='ВЫБЕРИ СТАВКУ';
  document.getElementById('rocket-cashout').style.display='none';
  document.getElementById('rocket-confirm').style.display='none';
  document.getElementById('countdown').classList.add('hidden');
  document.getElementById('bets-list').innerHTML='';
  makeBetButtons('rocket-buttons', selectRocketBet);
}
function selectRocketBet(b) {
  if(b>balance){tg.showAlert('Недостаточно средств');return;}
  selectedBet=b;
  document.getElementById('rocket-confirm').style.display='block';
  document.getElementById('rocket-status').textContent='СТАВКА: '+fmt(b)+' ₽';
}
async function confirmRocketBet() {
  if(selectedBet===0) return;
  rocketBet=selectedBet; selectedBet=0;
  await changeBalance(-rocketBet);
  document.getElementById('rocket-buttons').innerHTML='';
  document.getElementById('rocket-confirm').style.display='none';
  document.getElementById('rocket-status').textContent='РАКЕТА СТАРТУЕТ...';
  document.getElementById('bets-list').innerHTML =
    '<div class="bet-row"><span class="name">'+(user?.first_name||'Вы')+'</span><span class="amount">'+fmt(rocketBet)+' ₽</span></div>';
  const cd = document.getElementById('countdown');
  cd.classList.remove('hidden');
  for(let i=10;i>=1;i--){
    cd.textContent=i;
    await new Promise(r=>setTimeout(r,700));
  }
  cd.classList.add('hidden');
  document.getElementById('flame').style.display='block';
  document.getElementById('rocket-cashout').style.display='block';
  rocketInterval=setInterval(()=>{
    rocketMult=+(rocketMult+0.08+Math.random()*0.15).toFixed(2);
    rocketBottom=Math.min(370, rocketBottom+2.2);
    document.getElementById('rocket-svg').style.bottom=rocketBottom+'px';
    document.getElementById('rocket-mult').textContent='x'+rocketMult.toFixed(2);
    if(Math.random()<0.012){
      clearInterval(rocketInterval);rocketInterval=null;
      document.getElementById('rocket-mult').textContent='x'+rocketMult.toFixed(2);
      document.getElementById('rocket-mult').classList.add('crashed');
      document.getElementById('flame').style.display='none';
      document.getElementById('rocket-status').textContent='КРАХ! ПОТЕРЯНО: '+fmt(rocketBet)+' ₽';
      document.getElementById('rocket-cashout').style.display='none';
      setTimeout(initRocket,3000);
      return;
    }
    document.getElementById('rocket-status').textContent='ПОТЕНЦИАЛ: '+fmt(Math.floor(rocketBet*rocketMult))+' ₽';
  },120);
}
async function cashoutRocket() {
  if(!rocketInterval) return;
  clearInterval(rocketInterval);rocketInterval=null;
  const win=Math.floor(rocketBet*rocketMult);
  await changeBalance(win);
  document.getElementById('flame').style.display='none';
  document.getElementById('rocket-cashout').style.display='none';
  document.getElementById('rocket-status').textContent='ЗАБРАЛ '+fmt(win)+' ₽ (x'+rocketMult.toFixed(2)+')';
  setTimeout(initRocket,3000);
}

function initPlane() {
  if(planeInterval){clearInterval(planeInterval);planeInterval=null;}
  planeBet=0; planeMult=1.0; planeBottom=40; planeFuel=100;
  const stage=document.getElementById('plane-stage');
  stage.querySelectorAll('.balloon,.cloud').forEach(e=>e.remove());
  for(let i=0;i<8;i++){
    const cl=document.createElement('div'); cl.className='cloud';
    const sz=Math.random()*120+60;
    cl.style.width=sz+'px'; cl.style.height=sz/2+'px';
    cl.style.left=Math.random()*100+'%'; cl.style.top=Math.random()*100+'%';
    stage.appendChild(cl);
  }
  document.getElementById('plane-svg').style.bottom='40px';
  document.getElementById('fuel-fill').style.width='100%';
  document.getElementById('fuel-text').textContent='100%';
  document.getElementById('plane-alt').textContent='0 м';
  document.getElementById('plane-status').textContent='ВЫБЕРИ СТАВКУ';
  document.getElementById('plane-cashout').style.display='none';
  makeBetButtons('plane-buttons', startPlane);
}
async function startPlane(bet) {
  if(bet>balance){tg.showAlert('Недостаточно средств');return;}
  planeBet=bet; planeMult=1.0; planeBottom=40; planeFuel=100;
  await changeBalance(-bet);
  document.getElementById('plane-buttons').innerHTML='';
  document.getElementById('plane-cashout').style.display='block';
  const stage=document.getElementById('plane-stage');
  const balloons=[];
  for(let i=0;i<12;i++){
    const b=document.createElement('div'); b.className='balloon';
    const r=Math.random();
    if(r<0.15) b.classList.add('diamond');
    else if(r<0.35) b.classList.add('gold');
    b.style.left=(10+Math.random()*80)+'%';
    b.style.bottom=(80+i*30)+'px';
    stage.appendChild(b);
    balloons.push({el:b, used:false, y:80+i*30});
  }
  planeInterval=setInterval(()=>{
    planeFuel=Math.max(0, planeFuel-1.5);
    document.getElementById('fuel-fill').style.width=planeFuel+'%';
    document.getElementById('fuel-text').textContent=Math.floor(planeFuel)+'%';
    if(planeFuel>0) planeBottom+=1.5;
    document.getElementById('plane-svg').style.bottom=planeBottom+'px';
    document.getElementById('plane-alt').textContent=Math.floor(planeBottom-40)+' м';
    balloons.forEach(b=>{
      if(!b.used && Math.abs(planeBottom-b.y)<25){
        b.used=true;
        b.el.style.transition='all .5s';
        b.el.style.transform='scale(0)';
        b.el.style.opacity='0';
        if(b.el.classList.contains('diamond')){ planeMult+=1.0; planeFuel=Math.min(100,planeFuel+25); }
        else if(b.el.classList.contains('gold')){ planeMult+=0.5; planeFuel=Math.min(100,planeFuel+15); }
        else { planeMult+=0.2; planeFuel=Math.min(100,planeFuel+8); }
      }
    });
    if(planeFuel<=0){
      clearInterval(planeInterval);planeInterval=null;
      document.getElementById('plane-cashout').style.display='none';
      if(planeBottom<340){
        document.getElementById('plane-status').textContent='ТОПЛИВО КОНЧИЛОСЬ! ПОТЕРЯНО: '+fmt(planeBet)+' ₽';
      } else {
        const win=Math.floor(planeBet*planeMult*2);
        changeBalance(win);
        document.getElementById('plane-status').textContent='ПРИЗЕМЛИЛСЯ! +'+fmt(win)+' ₽';
      }
      setTimeout(initPlane,3000);
      return;
    }
    document.getElementById('plane-status').textContent='ШАРИКОВ x'+planeMult.toFixed(1)+' | ТОПЛИВО '+Math.floor(planeFuel)+'%';
  },120);
}
async function cashoutPlane() {
  if(!planeInterval) return;
  clearInterval(planeInterval);planeInterval=null;
  const win=Math.floor(planeBet*planeMult);
  await changeBalance(win);
  document.getElementById('plane-cashout').style.display='none';
  document.getElementById('plane-status').textContent='ЗАБРАЛ '+fmt(win)+' ₽ (x'+planeMult.toFixed(2)+')';
  setTimeout(initPlane,3000);
}

function initWheel() {
  const wheel=document.getElementById('wheel-el');
  wheel.style.transition='none';
  wheel.style.transform='rotate(0deg)';
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
    num.style.cssText='position:absolute;top:20px;left:50%;transform:translateX(-50%) rotate('+(i*30+15)+'deg);font-size:14px;font-weight:900;color:#fff;';
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
  const targetDeg=360*6+(360-idx*30);
  wheel.style.transform='rotate('+targetDeg+'deg)';
  await new Promise(r=>setTimeout(r,5200));
  const win=Math.floor(bet*mult);
  if(win>0) await changeBalance(win);
  document.getElementById('wheel-status').textContent = mult
    ? 'ВЫПАЛО x'+mult+'! ВЫИГРЫШ '+fmt(win)+' ₽'
    : 'МИМО. ПОТЕРЯНО '+fmt(bet)+' ₽';
  setTimeout(initWheel,3000);
}

function renderNFT() {
  const c=document.getElementById('nft-list'); c.innerHTML='';
  Object.keys(GIFTS).forEach(id=>{
    const n=GIFTS[id];
    const d=document.createElement('div'); d.className='nft-card';
    d.innerHTML = svgIcon(n.shape, n.color) +
      '<div class="nft-name">'+n.name+'</div>' +
      '<div class="nft-price">'+fmt(n.price)+' ₽</div>' +
      '<button class="nft-btn" onclick="buyNFT(\''+id+'\')">КУПИТЬ</button>';
    c.appendChild(d);
  });
}
async function buyNFT(id) {
  const r=await fetch('/api/buy',{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({user_id:user.id, gift_id:id})
  });
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
    d.innerHTML = svgIcon(n.shape,n.color) +
      '<div class="nft-name">'+n.name+'</div>' +
      '<div class="nft-price">'+fmt(n.price)+' ₽</div>' +
      '<button class="nft-btn" style="background:linear-gradient(135deg,#ff3a5a,#cc2244);" onclick="sellNFT('+i+')">ПРОДАТЬ</button>';
    c.appendChild(d);
  });
}
async function sellNFT(index) {
  const r=await fetch('/api/sell',{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({user_id:user.id, index})
  });
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
    d.innerHTML = svgIcon(n.shape,n.color) +
      '<div class="nft-name">'+n.name+'</div>' +
      '<div class="nft-price">'+fmt(n.price)+' ₽</div>' +
      '<button class="nft-btn" onclick="buyNFT(\''+id+'\')">КУПИТЬ</button>';
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
