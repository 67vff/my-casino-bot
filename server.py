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

HTML_PAGE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>CASINO</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
* { margin:0; padding:0; box-sizing:border-box; -webkit-tap-highlight-color:transparent; font-family:'Segoe UI',-apple-system,sans-serif; }
body { background:#05050f; color:#e8e8f0; min-height:100vh; padding:14px; }
.balance { background:linear-gradient(135deg,#1e1e3a,#2a1e4a); border:1px solid #3a2a5a; padding:16px; border-radius:14px; text-align:center; margin-bottom:14px; }
.balance h1 { font-size:11px; opacity:.6; letter-spacing:2px; }
.balance .amount { font-size:28px; font-weight:800; color:#fff; }
.games { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
.game { background:linear-gradient(160deg,#12122a,#0d0d1f); border-radius:14px; padding:16px 10px; text-align:center; cursor:pointer; border:1px solid #1e1e3a; }
.game:active { transform:scale(.96); border-color:#4a3aff; }
.game .name { font-size:11px; font-weight:700; letter-spacing:1px; text-transform:uppercase; }
.game .desc { font-size:9px; opacity:.4; margin-top:3px; }
.screen { display:none; }
.screen.active { display:block; }
.back { background:#12122a; border:1px solid #1e1e3a; color:#fff; padding:9px 14px; border-radius:10px; font-size:12px; margin-bottom:14px; cursor:pointer; }
h2 { font-size:16px; margin-bottom:14px; text-align:center; font-weight:800; letter-spacing:2px; }
.bet-buttons { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:12px; }
.bet-btn { background:#12122a; border:1px solid #2a2a4a; color:#fff; padding:12px; border-radius:10px; font-size:14px; font-weight:700; cursor:pointer; }
.bet-btn:active { background:#2a2a4a; }
.big-btn { background:linear-gradient(135deg,#4a3aff,#6a4aff); border:none; color:#fff; padding:14px; border-radius:12px; font-size:14px; font-weight:800; width:100%; margin-top:12px; cursor:pointer; }

/* РУЛЕТКА */
.wheel-wrap { position:relative; width:300px; height:300px; margin:20px auto; }
.wheel { width:100%; height:100%; border-radius:50%; border:10px solid #2a2a4a; position:relative; transition:transform 5s cubic-bezier(.15,.85,.25,1); overflow:hidden; box-shadow:0 0 50px rgba(74,58,255,.4); }
.wheel-seg { position:absolute; width:50%; height:50%; top:0; left:50%; transform-origin:0% 100%; }
.wheel-num { position:absolute; font-size:9px; font-weight:900; color:#fff; text-shadow:0 0 4px #000; }
.pointer { position:absolute; top:-16px; left:50%; transform:translateX(-50%); width:0; height:0; border-left:14px solid transparent; border-right:14px solid transparent; border-top:24px solid #ff3a5a; z-index:10; }
.wheel-center { position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:50px; height:50px; background:radial-gradient(circle,#4a3aff,#2a1a8a); border-radius:50%; border:3px solid #6a4aff; z-index:5; display:flex; align-items:center; justify-content:center; font-size:10px; font-weight:900; }

/* КОРОВА */
.cow-stage { position:relative; height:400px; background:#0a0a1a; border-radius:14px; overflow:hidden; border:1px solid #1e1e3a; margin-top:10px; }
.road { position:absolute; width:100%; height:60px; border-top:2px dashed #333; border-bottom:2px dashed #333; }
.cow { position:absolute; font-size:32px; bottom:10px; left:50%; transform:translateX(-50%); z-index:5; transition:bottom .3s; }
.car { position:absolute; font-size:32px; z-index:4; }
.mult-badge { position:absolute; right:6px; font-size:11px; font-weight:700; color:#4aff8a; z-index:6; }

/* ГОНКИ */
.race-stage { position:relative; height:400px; background:#0a0a1a; border-radius:14px; overflow:hidden; border:1px solid #1e1e3a; margin-top:10px; }
.lane { position:absolute; width:100%; height:60px; border-bottom:1px dashed #222; }
.race-car { position:absolute; font-size:32px; left:10px; transition:left .3s; z-index:5; }

/* ПОКЕР */
.poker-dice { display:flex; justify-content:center; gap:10px; margin:20px 0; }
.pd { width:60px; height:60px; background:#1a1a3a; border:2px solid #4a3aff; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:36px; }

.nft-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
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
  </div>
  <div class="games">
    <div class="game" onclick="openGame('wheel')"><div class="name">РУЛЕТКА</div><div class="desc">36 СЕКТОРОВ</div></div>
    <div class="game" onclick="openGame('cow')"><div class="name">КОРОВА</div><div class="desc">ПЕРЕБЕГИ ДОРОГУ</div></div>
    <div class="game" onclick="openGame('race')"><div class="name">ГОНКИ</div><div class="desc">СТАВЬ НА МАШИНУ</div></div>
    <div class="game" onclick="openGame('poker')"><div class="name">ПОКЕР</div><div class="desc">5 КУБИКОВ</div></div>
    <div class="game" onclick="openGame('nft')"><div class="name">NFT</div><div class="desc">КОЛЛЕКЦИЯ</div></div>
    <div class="game" onclick="openGame('inventory')"><div class="name">ИНВЕНТАРЬ</div><div class="desc">ТВОИ NFT</div></div>
    <div class="game" onclick="openGame('shop')"><div class="name">МАГАЗИН</div><div class="desc">КУПИТЬ NFT</div></div>
  </div>
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

<div id="cow" class="screen">
  <button class="back" onclick="goMenu()">← НАЗАД</button>
  <h2>КОРОВА</h2>
  <div class="cow-stage" id="cow-stage"></div>
  <div id="cow-status" style="text-align:center;margin-top:10px;font-size:13px;">СТАВКА, ПОТОМ ЖМИ «ВПЕРЁД»</div>
  <div class="bet-buttons" id="cow-buttons"></div>
  <button class="big-btn" id="cow-forward" style="display:none;background:linear-gradient(135deg,#4aff8a,#2acc6a);color:#000;" onclick="cowForward()">ВПЕРЁД</button>
</div>

<div id="race" class="screen">
  <button class="back" onclick="goMenu()">← НАЗАД</button>
  <h2>ГОНКИ</h2>
  <div class="race-stage" id="race-stage"></div>
  <div id="race-status" style="text-align:center;margin-top:10px;font-size:13px;">ВЫБЕРИ МАШИНУ И СТАВКУ</div>
  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-top:10px;">
    <button class="bet-btn" onclick="pickCar(0)">🚗</button>
    <button class="bet-btn" onclick="pickCar(1)">🚙</button>
    <button class="bet-btn" onclick="pickCar(2)">🏎️</button>
    <button class="bet-btn" onclick="pickCar(3)">🚕</button>
  </div>
  <div class="bet-buttons" id="race-buttons"></div>
</div>

<div id="poker" class="screen">
  <button class="back" onclick="goMenu()">← НАЗАД</button>
  <h2>ПОКЕР НА КУБИКАХ</h2>
  <div class="poker-dice" id="poker-dice"></div>
  <div id="poker-status" style="text-align:center;font-size:13px;min-height:30px;">БРОСЬ 5 КУБИКОВ</div>
  <div class="bet-buttons" id="poker-buttons"></div>
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
const tg = window.Telegram.WebApp; tg.ready(); tg.expand();
const user = tg.initDataUnsafe?.user;
const BETS = [100, 500, 1000, 5000];
let balance = 10000, inventory = [];
let cowBet = 0, cowRow = 0, cowActive = false, cowMult = 1.0;
let raceBet = 0, raceCar = -1, raceActive = false;
let pokerBet = 0;

const GIFTS = {
  "1": {name:"АЛМАЗ", price:5000, color:"#88eeff", shape:"diamond"},
  "2": {name:"КОРОНА", price:15000, color:"#ffdd44", shape:"crown"},
  "3": {name:"ЧЕРЕП", price:3000, color:"#ff3a5a", shape:"skull"},
  "4": {name:"ЗВЕЗДА", price:25000, color:"#ffaa00", shape:"star"},
  "5": {name:"РАКЕТА", price:50000, color:"#4a3aff", shape:"rocket"},
  "6": {name:"ПЛАНЕТА", price:100000, color:"#4aff8a", shape:"planet"},
};

function svgIcon(shape, c) {
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
  const r = await fetch('/api/balance', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({user_id:user.id, delta})});
  const d = await r.json();
  balance = d.balance; inventory = d.inventory || [];
  updateUI();
}
function updateUI() {
  document.getElementById('balance').textContent = fmt(balance);
}
function goMenu() {
  document.querySelectorAll('.screen').forEach(s=>s.classList.remove('active'));
  document.getElementById('menu').classList.add('active');
  cowActive = false; raceActive = false;
}
function openGame(n) {
  document.querySelectorAll('.screen').forEach(s=>s.classList.remove('active'));
  document.getElementById(n).classList.add('active');
  if(n==='wheel') initWheel();
  if(n==='cow') initCow();
  if(n==='race') initRace();
  if(n==='poker') initPoker();
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

// ===== РУЛЕТКА 36 =====
function initWheel() {
  const wheel=document.getElementById('wheel-el');
  wheel.style.transition='none'; wheel.style.transform='rotate(0deg)';
  setTimeout(()=>wheel.style.transition='transform 5s cubic-bezier(.15,.85,.25,1)',50);
  wheel.innerHTML='';
  const reds=[1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36];
  for(let i=0;i<37;i++){
    const seg=document.createElement('div');
    seg.className='wheel-seg';
    let color='#0a0a0a';
    if(i===0) color='#0a8a3a';
    else if(reds.includes(i)) color='#cc2244';
    else color='#111';
    seg.style.background=color;
    seg.style.transform='rotate('+(i*(360/37))+'deg)';
    wheel.appendChild(seg);
    const num=document.createElement('div');
    num.className='wheel-num';
    num.textContent=i;
    num.style.cssText='position:absolute;top:16px;left:50%;transform:translateX(-50%) rotate('+(i*(360/37)+(360/74))+'deg);';
    seg.appendChild(num);
  }
  document.getElementById('wheel-status').textContent='ВЫБЕРИ СТАВКУ';
  makeBetButtons('wheel-buttons', playWheel);
}
async function playWheel(bet) {
  if(bet>balance){tg.showAlert('Недостаточно средств');return;}
  await changeBalance(-bet);
  document.getElementById('wheel-buttons').innerHTML='';
  document.getElementById('wheel-status').textContent='КРУТИМ...';
  const idx=Math.floor(Math.random()*37);
  const wheel=document.getElementById('wheel-el');
  const targetDeg=360*6+(360-idx*(360/37));
  wheel.style.transform='rotate('+targetDeg+'deg)';
  await new Promise(r=>setTimeout(r,5200));
  // шанс выиграть x30 если угадал сектор (упрощённо)
  const win = Math.random()<0.03 ? bet*30 : 0;
  if(win>0) await changeBalance(win);
  document.getElementById('wheel-status').textContent = win ? 'ВЫПАЛО '+idx+'! ВЫИГРЫШ '+fmt(win)+' ₽' : 'ВЫПАЛО '+idx+'. МИМО';
  setTimeout(initWheel,3000);
}

// ===== КОРОВА =====
function initCow() {
  cowBet = 0; cowRow = 0; cowActive = false; cowMult = 1.0;
  const stage=document.getElementById('cow-stage'); stage.innerHTML='';
  const rows=8;
  for(let i=0;i<rows;i++){
    const road=document.createElement('div'); road.className='road';
    road.style.bottom=(i*50)+'px';
    stage.appendChild(road);
    const badge=document.createElement('div'); badge.className='mult-badge';
    badge.textContent='x'+(1+(i+1)*0.5).toFixed(1);
    badge.style.bottom=(i*50+20)+'px';
    stage.appendChild(badge);
  }
  const cow=document.createElement('div'); cow.className='cow'; cow.textContent='🐄';
  cow.style.bottom='10px'; stage.appendChild(cow);
  document.getElementById('cow-status').textContent='СТАВКА, ПОТОМ «ВПЕРЁД»';
  document.getElementById('cow-forward').style.display='none';
  makeBetButtons('cow-buttons', startCow);
}
async function startCow(bet) {
  if(bet>balance){tg.showAlert('Недостаточно средств');return;}
  if(cowActive) return;
  cowBet = bet; cowRow = 0; cowMult = 1.0; cowActive = true;
  await changeBalance(-bet);
  document.getElementById('cow-buttons').innerHTML='';
  document.getElementById('cow-forward').style.display='block';
  document.getElementById('cow-status').textContent='МНОЖИТЕЛЬ: x1.00 | ЖМИ ВПЕРЁД';
}
async function cowForward() {
  if(!cowActive) return;
  cowRow++;
  cowMult = +(1 + cowRow*0.5).toFixed(2);
  const cow=document.querySelector('#cow-stage .cow');
  cow.style.bottom=(10+cowRow*50)+'px';
  // шанс попасть под машину — растёт с рядом
  if(Math.random() < 0.15 + cowRow*0.05){
    cowActive = false;
    document.getElementById('cow-forward').style.display='none';
    document.getElementById('cow-status').textContent='🚗 СБИЛИ! ПОТЕРЯНО: '+fmt(cowBet)+' ₽';
    setTimeout(initCow,3000);
    return;
  }
  if(cowRow >= 8){
    cowActive = false;
    const win=Math.floor(cowBet*cowMult*3);
    await changeBalance(win);
    document.getElementById('cow-forward').style.display='none';
    document.getElementById('cow-status').textContent='ПЕРЕШЛА! +'+fmt(win)+' ₽';
    setTimeout(initCow,3000);
    return;
  }
  document.getElementById('cow-status').textContent='МНОЖИТЕЛЬ x'+cowMult.toFixed(2)+' | ЖМИ ВПЕРЁД';
}

// ===== ГОНКИ =====
function initRace() {
  raceBet=0; raceCar=-1; raceActive=false;
  const stage=document.getElementById('race-stage'); stage.innerHTML='';
  const cars=['🚗','🚙','🏎️','🚕'];
  for(let i=0;i<4;i++){
    const lane=document.createElement('div'); lane.className='lane';
    lane.style.top=(i*90+20)+'px';
    stage.appendChild(lane);
    const c=document.createElement('div'); c.className='race-car';
    c.textContent=cars[i];
    c.style.top=(i*90+20)+'px';
    c.id='race-car-'+i;
    stage.appendChild(c);
  }
  document.getElementById('race-status').textContent='ВЫБЕРИ МАШИНУ И СТАВКУ';
  makeBetButtons('race-buttons', playRace);
}
function pickCar(i) {
  raceCar = i;
  document.getElementById('race-status').textContent='ВЫБРАНА МАШИНА '+(i+1)+' | ВЫБЕРИ СТАВКУ';
}
async function playRace(bet) {
  if(raceCar<0){tg.showAlert('Выбери машину');return;}
  if(bet>balance){tg.showAlert('Недостаточно средств');return;}
  await changeBalance(-bet);
  document.getElementById('race-buttons').innerHTML='';
  document.getElementById('race-status').textContent='ГОНКА!';
  const positions=[0,0,0,0];
  const speeds=[0,0,0,0].map(()=> 0.5 + Math.random());
  let winner=-1;
  while(winner<0){
    await new Promise(r=>setTimeout(r,100));
    for(let i=0;i<4;i++){
      positions[i] += speeds[i] * (0.5 + Math.random());
      if(positions[i] > 90){ if(winner<0) winner=i; }
      const c=document.getElementById('race-car-'+i);
      if(c) c.style.left = Math.min(90, positions[i]) + '%';
    }
  }
  if(winner === raceCar){
    const win = bet*4;
    await changeBalance(win);
    document.getElementById('race-status').textContent='🏆 ПОБЕДА! +'+fmt(win)+' ₽';
  } else {
    document.getElementById('race-status').textContent='ПРОИГРАЛ. ПОТЕРЯНО '+fmt(bet)+' ₽';
  }
  setTimeout(initRace,3000);
}

// ===== ПОКЕР НА КУБИКАХ =====
function initPoker() {
  pokerBet=0;
  const c=document.getElementById('poker-dice'); c.innerHTML='';
  for(let i=0;i<5;i++){
    const d=document.createElement('div'); d.className='pd'; d.textContent='?';
    c.appendChild(d);
  }
  document.getElementById('poker-status').textContent='БРОСЬ 5 КУБИКОВ';
  makeBetButtons('poker-buttons', playPoker);
}
async function playPoker(bet) {
  if(bet>balance){tg.showAlert('Недостаточно средств');return;}
  await changeBalance(-bet);
  document.getElementById('poker-buttons').innerHTML='';
  const faces=['⚀','⚁','⚂','⚃','⚄','⚅'];
  const vals=[0,0,0,0,0];
  const cells=document.querySelectorAll('#poker-dice .pd');
  for(let i=0;i<5;i++){
    vals[i] = Math.floor(Math.random()*6)+1;
    cells[i].textContent = faces[vals[i]-1];
    await new Promise(r=>setTimeout(r,200));
  }
  // подсчёт комбинации
  const counts={};
  vals.forEach(v=>counts[v]=(counts[v]||0)+1);
  const max=Math.max(...Object.values(counts));
  let mult=0, name='';
  if(max===5){mult=20;name='ПОКЕР';}
  else if(max===4){mult=10;name='КАРЕ';}
  else if(max===3 && Object.values(counts).includes(2)){mult=7;name='ФУЛЛ-ХАУС';}
  else if(max===3){mult=4;name='ТРОЙКА';}
  else if(Object.values(counts).filter(x=>x===2).length===2){mult=3;name='ДВЕ ПАРЫ';}
  else if(max===2){mult=2;name='ПАРА';}
  const win=Math.floor(bet*mult);
  if(win>0) await changeBalance(win);
  document.getElementById('poker-status').textContent = mult ? name+'! +'+fmt(win)+' ₽ (x'+mult+')' : 'НИЧЕГО. ПОТЕРЯНО '+fmt(bet)+' ₽';
  setTimeout(initPoker,3000);
}

// ===== NFT =====
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
    d.innerHTML = svgIcon(n.shape,n.color) + '<div class="nft-name">'+n.name+'</div><div class="nft-price">'+fmt(n.price)+' ₽</div><button class="nft-btn" style="background:#cc2244;" onclick="sellNFT('+i+')">ПРОДАТЬ</button>';
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
