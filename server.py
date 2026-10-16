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
        db[k] = {"balance": 10000, "inventory": []}
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

GIFTS = {
    "1": {"name": "АЛМАЗ", "price": 5000, "color": "#88eeff", "emoji": "💎"},
    "2": {"name": "КОРОНА", "price": 15000, "color": "#ffdd44", "emoji": "👑"},
    "3": {"name": "ЧЕРЕП", "price": 3000, "color": "#ff3a5a", "emoji": "💀"},
    "4": {"name": "ЗВЕЗДА", "price": 25000, "color": "#ffaa00", "emoji": "⭐"},
    "5": {"name": "РАКЕТА", "price": 50000, "color": "#4a3aff", "emoji": "🚀"},
    "6": {"name": "ПЛАНЕТА", "price": 100000, "color": "#4aff8a", "emoji": "🪐"},
    "7": {"name": "ОГОНЬ", "price": 8000, "color": "#ff4400", "emoji": "🔥"},
    "8": {"name": "ЛУНА", "price": 12000, "color": "#ccccff", "emoji": "🌙"},
    "9": {"name": "МОЛНИЯ", "price": 20000, "color": "#ffff44", "emoji": "⚡"},
    "10": {"name": "КОМЕТА", "price": 35000, "color": "#88aaff", "emoji": "☄️"}
}

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
.game{background:linear-gradient(160deg,#12122a,#0d0d1f);border-radius:14px;padding:18px 10px;text-align:center;cursor:pointer;border:1px solid #1e1e3a}
.game:active{transform:scale(.96);border-color:#4a3aff}
.game .name{font-size:12px;font-weight:700;letter-spacing:1px}
.game .desc{font-size:9px;opacity:.5;margin-top:4px}
.screen{display:none}.screen.active{display:block}
.back{background:#12122a;border:1px solid #1e1e3a;color:#fff;padding:10px 16px;border-radius:10px;font-size:13px;margin-bottom:14px;cursor:pointer}
h2{font-size:18px;margin-bottom:16px;text-align:center;font-weight:800;letter-spacing:2px}
.bet-buttons{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:14px}
.bet-btn{background:#12122a;border:1px solid #2a2a4a;color:#fff;padding:14px;border-radius:10px;font-size:15px;font-weight:700;cursor:pointer}
.bet-btn:active{background:#2a2a4a}
.big-btn{background:linear-gradient(135deg,#4a3aff,#6a4aff);border:none;color:#fff;padding:16px;border-radius:12px;font-size:15px;font-weight:800;width:100%;margin-top:12px;cursor:pointer}
.big-btn:active{transform:scale(.98)}
.status{text-align:center;font-size:14px;min-height:24px;margin-bottom:8px;font-weight:600}
.emoji-big{font-size:100px;text-align:center;margin:20px 0;min-height:120px;line-height:120px}
.grid-3{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-top:10px}
.grid-4{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-top:10px}

/* Блэкджек */
.bj-cards{display:flex;gap:6px;justify-content:center;margin:14px 0;min-height:90px;flex-wrap:wrap}
.bj-card{width:56px;height:80px;background:#fff;color:#000;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:900;border:2px solid #333}
.bj-card.red{color:#cc2244}
.bj-label{text-align:center;font-size:13px;font-weight:800;margin:6px 0;letter-spacing:1px}

/* Дартс */
.dart-board{position:relative;width:280px;height:280px;margin:20px auto;border-radius:50%;background:radial-gradient(circle,#ff3a5a 0%,#ff3a5a 15%,#fff 15%,#fff 30%,#ff3a5a 30%,#ff3a5a 45%,#fff 45%,#fff 60%,#ff3a5a 60%,#ff3a5a 75%,#fff 75%,#fff 90%,#4a3aff 90%,#4a3aff 100%);border:4px solid #1e1e3a}
.dart-dot{position:absolute;width:16px;height:16px;background:#ffdd44;border-radius:50%;box-shadow:0 0 12px #ffdd44;border:2px solid #000;z-index:5;transform:translate(-50%,-50%)}

/* Пенальти */
.goal{position:relative;width:100%;height:180px;background:linear-gradient(180deg,#2a5a2a,#1a3a1a);border:4px solid #fff;border-radius:8px;margin-top:14px;overflow:hidden}
.goal-net{position:absolute;inset:0;background-image:repeating-linear-gradient(0deg,transparent 0,transparent 18px,rgba(255,255,255,.15) 18px,rgba(255,255,255,.15) 20px),repeating-linear-gradient(90deg,transparent 0,transparent 18px,rgba(255,255,255,.15) 18px,rgba(255,255,255,.15) 20px)}
.keeper{position:absolute;bottom:0;font-size:60px;transition:left .4s;line-height:1;z-index:3}
.ball-pen{position:absolute;bottom:20px;font-size:36px;transition:all .6s;z-index:2}

/* Бокс */
.box-ring{width:100%;height:200px;background:#3a1a1a;border:6px solid #ffdd44;border-radius:8px;position:relative;margin-top:14px;overflow:hidden}
.box-fighter{position:absolute;bottom:20px;font-size:70px;transition:left .2s}
.box-punch{position:absolute;bottom:60px;font-size:40px;opacity:0;transition:opacity .1s}

/* Баскетбол */
.basket{position:relative;width:100%;height:200px;background:#1a1a3a;border-radius:8px;margin-top:14px;overflow:hidden}
.hoop{position:absolute;right:20px;top:40px;font-size:60px}
.basket-ball{position:absolute;left:20px;bottom:20px;font-size:40px;transition:all .8s}

/* Скачки */
.race-track{position:relative;width:100%;height:220px;background:#1a3a1a;border-radius:8px;margin-top:14px;overflow:hidden}
.race-lane{position:absolute;left:0;right:0;height:40px;border-bottom:2px dashed #fff;display:flex;align-items:center;padding-left:6px}
.horse{font-size:32px;transition:transform .1s}

/* Рыбалка */
.fish-pond{position:relative;width:100%;height:220px;background:linear-gradient(180deg,#0a3a5a,#052a4a);border-radius:8px;margin-top:14px;overflow:hidden}
.fish{position:absolute;font-size:32px;transition:left .3s}
.hook{position:absolute;font-size:24px;transition:bottom .5s;left:50%;transform:translateX(-50%)}

/* Кейсы */
.case-row{display:flex;gap:6px;justify-content:center;margin:20px 0;overflow:hidden;padding:10px 0}
.case-item{width:70px;height:90px;background:linear-gradient(160deg,#12122a,#0a0a1a);border:2px solid #2a2a4a;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:36px;flex-shrink:0}
.case-item.win{border-color:#4aff8a;box-shadow:0 0 20px #4aff8a}
.case-pointer{width:0;height:0;border-left:12px solid transparent;border-right:12px solid transparent;border-top:18px solid #ff3a5a;margin:0 auto;z-index:5}

/* Лотерея */
.lotto{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin:20px 0}
.lotto-ball{aspect-ratio:1;background:radial-gradient(circle at 30% 30%,#fff,#bbb);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:18px;font-weight:900;color:#000}
.lotto-ball.hit{background:radial-gradient(circle at 30% 30%,#4aff8a,#2acc6a);color:#fff;box-shadow:0 0 15px #4aff8a}

/* Покер */
.poker-row{display:flex;gap:6px;justify-content:center;margin:20px 0}
.poker-card{width:70px;height:100px;background:#fff;border-radius:8px;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#000;font-weight:900;border:2px solid #333}
.poker-card.red{color:#cc2244}

/* Монетка x3 */
.coin3-row{display:flex;gap:14px;justify-content:center;margin:20px 0}
.coin3{width:90px;height:90px;border-radius:50%;background:radial-gradient(circle,#ffdd44,#cc9900);display:flex;align-items:center;justify-content:center;font-size:26px;font-weight:900;color:#3a2a00;transition:transform .5s}
.coin3.flip{animation:fl3 .4s infinite}
@keyframes fl3{0%{transform:rotateY(0)}100%{transform:rotateY(360deg)}}

/* Бинго */
.bingo-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:6px;margin-top:14px}
.bingo-cell{aspect-ratio:1;background:#12122a;border:1px solid #2a2a4a;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700}
.bingo-cell.marked{background:#2a5a2a;border-color:#4aff8a;color:#4aff8a}

/* Кено */
.keno-grid{display:grid;grid-template-columns:repeat(8,1fr);gap:4px;margin-top:14px}
.keno-cell{aspect-ratio:1;background:#12122a;border:1px solid #2a2a4a;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;cursor:pointer}
.keno-cell.picked{background:#4a3aff;color:#fff}
.keno-cell.hit{background:#4aff8a;color:#000;box-shadow:0 0 10px #4aff8a}

/* Тетрис */
.tetris-stage{position:relative;width:200px;height:340px;margin:14px auto;background:#0a0a1e;border:2px solid #2a2a4a;border-radius:8px;overflow:hidden}
.tetris-block{position:absolute;width:20px;height:20px;border-radius:3px}
</style>
</head>
<body>

<div id="menu" class="screen active">
  <div class="balance"><h1>БАЛАНС</h1><div class="amount"><span id="balance">100.00</span> ₽</div></div>
  <div class="games">
    <div class="game" id="btn-bj"><div class="name">🃏 БЛЭКДЖЕК</div><div class="desc">21</div></div>
    <div class="game" id="btn-dart"><div class="name">🎯 ДАРТС</div><div class="desc">МИШЕНЬ</div></div>
    <div class="game" id="btn-penalty"><div class="name">⚽ ПЕНАЛЬТИ</div><div class="desc">УГАДАЙ УГОЛ</div></div>
    <div class="game" id="btn-box"><div class="name">🥊 БОКС</div><div class="desc">БОЙ</div></div>
    <div class="game" id="btn-basket"><div class="name">🏀 БАСКЕТБОЛ</div><div class="desc">БРОСОК</div></div>
    <div class="game" id="btn-race"><div class="name">🐎 СКАЧКИ</div><div class="desc">СТАВЬ НА ЛОШАДЬ</div></div>
    <div class="game" id="btn-fish"><div class="name">🎣 РЫБАЛКА</div><div class="desc">ПОЙМАЙ</div></div>
    <div class="game" id="btn-case"><div class="name">📦 КЕЙСЫ</div><div class="desc">КРУТИ</div></div>
    <div class="game" id="btn-lotto"><div class="name">🎟️ ЛОТЕРЕЯ</div><div class="desc">БИЛЕТЫ</div></div>
    <div class="game" id="btn-poker"><div class="name">🃏 ПОКЕР</div><div class="desc">ХАЙ-ЛОУ</div></div>
    <div class="game" id="btn-coin3"><div class="name">🪙 3 МОНЕТКИ</div><div class="desc">X7</div></div>
    <div class="game" id="btn-bingo"><div class="name">🅱️ БИНГО</div><div class="desc">ЛИНИЯ</div></div>
    <div class="game" id="btn-keno"><div class="name">🎯 КЕНО</div><div class="desc">ВЫБЕРИ 5</div></div>
    <div class="game" id="btn-tetris"><div class="name">🎮 ТЕТРИС</div><div class="desc">СТАВКА</div></div>
    <div class="game" id="btn-inv"><div class="name">🎁 ИНВЕНТАРЬ</div><div class="desc">ТВОИ NFT</div></div>
  </div>
</div>

<!-- БЛЭКДЖЕК -->
<div id="bj" class="screen">
  <button class="back" id="back-bj">← НАЗАД</button>
  <h2>🃏 БЛЭКДЖЕК</h2>
  <div class="bj-label">ДИЛЕР: <span id="bj-dscore">0</span></div>
  <div class="bj-cards" id="bj-dealer"></div>
  <div class="bj-label">ТЫ: <span id="bj-pscore">0</span></div>
  <div class="bj-cards" id="bj-player"></div>
  <div class="status" id="bj-status">ВЫБЕРИ СТАВКУ</div>
  <div class="bet-buttons" id="bj-buttons"></div>
  <div id="bj-actions" style="display:none;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px;">
    <button class="big-btn" id="bj-hit">ЕЩЁ</button>
    <button class="big-btn" id="bj-stand" style="background:linear-gradient(135deg,#cc2244,#ff3a5a);">ХВАТИТ</button>
  </div>
</div>

<!-- ДАРТС -->
<div id="dart" class="screen">
  <button class="back" id="back-dart">← НАЗАД</button>
  <h2>🎯 ДАРТС</h2>
  <div class="status" id="dart-status">ВЫБЕРИ СТАВКУ</div>
  <div class="bet-buttons" id="dart-buttons"></div>
  <div class="dart-board" id="dart-board"></div>
</div>

<!-- ПЕНАЛЬТИ -->
<div id="penalty" class="screen">
  <button class="back" id="back-penalty">← НАЗАД</button>
  <h2>⚽ ПЕНАЛЬТИ</h2>
  <div class="status" id="penalty-status">ВЫБЕРИ СТАВКУ</div>
  <div class="bet-buttons" id="penalty-buttons"></div>
  <div class="goal" id="goal">
    <div class="goal-net"></div>
    <div class="keeper" id="keeper" style="left:calc(50% - 30px);">🧤</div>
    <div class="ball-pen" id="ball-pen" style="left:calc(50% - 18px);">⚽</div>
  </div>
  <div class="grid-3" id="penalty-zones" style="margin-top:10px;">
    <button class="bet-btn" data-zone="left">← ЛЕВО</button>
    <button class="bet-btn" data-zone="center">ЦЕНТР</button>
    <button class="bet-btn" data-zone="right">ПРАВО →</button>
  </div>
</div>

<!-- БОКС -->
<div id="box" class="screen">
  <button class="back" id="back-box">← НАЗАД</button>
  <h2>🥊 БОКС</h2>
  <div class="status" id="box-status">ВЫБЕРИ СТАВКУ</div>
  <div class="bet-buttons" id="box-buttons"></div>
  <div class="box-ring" id="box-ring">
    <div class="box-fighter" id="box-foe" style="right:20px;">🥊</div>
    <div class="box-fighter" id="box-me" style="left:20px;">🥋</div>
    <div class="box-punch" id="box-punch" style="left:30%;">💥</div>
  </div>
  <div class="grid-4" id="box-actions" style="margin-top:10px;">
    <button class="bet-btn" data-punch="jab">ДЖЕБ</button>
    <button class="bet-btn" data-punch="hook">ХУК</button>
    <button class="bet-btn" data-punch="uppercut">АППЕР</button>
    <button class="bet-btn" data-punch="block">БЛОК</button>
  </div>
</div>

<!-- БАСКЕТБОЛ -->
<div id="basket" class="screen">
  <button class="back" id="back-basket">← НАЗАД</button>
  <h2>🏀 БАСКЕТБОЛ</h2>
  <div class="status" id="basket-status">ВЫБЕРИ СТАВКУ</div>
  <div class="bet-buttons" id="basket-buttons"></div>
  <div class="basket" id="basket-stage">
    <div class="hoop">🏀</div>
    <div class="basket-ball" id="basket-ball">🏀</div>
  </div>
</div>

<!-- СКАЧКИ -->
<div id="race" class="screen">
  <button class="back" id="back-race">← НАЗАД</button>
  <h2>🐎 СКАЧКИ</h2>
  <div class="status" id="race-status">ВЫБЕРИ СТАВКУ</div>
  <div class="bet-buttons" id="race-buttons"></div>
  <div class="race-track" id="race-track"></div>
</div>

<!-- РЫБАЛКА -->
<div id="fish" class="screen">
  <button class="back" id="back-fish">← НАЗАД</button>
  <h2>🎣 РЫБАЛКА</h2>
  <div class="status" id="fish-status">ВЫБЕРИ СТАВКУ</div>
  <div class="bet-buttons" id="fish-buttons"></div>
  <div class="fish-pond" id="fish-pond">
    <div class="hook" id="hook">🎣</div>
  </div>
  <button class="big-btn" id="fish-catch" style="display:none;background:linear-gradient(135deg,#4aff8a,#2acc6a);color:#000;">ПОЙМАТЬ!</button>
</div>

<!-- КЕЙСЫ -->
<div id="case" class="screen">
  <button class="back" id="back-case">← НАЗАД</button>
  <h2>📦 КЕЙСЫ</h2>
  <div class="status" id="case-status">ВЫБЕРИ СТАВКУ</div>
  <div class="bet-buttons" id="case-buttons"></div>
  <div class="case-pointer"></div>
  <div class="case-row" id="case-row"></div>
</div>

<!-- ЛОТЕРЕЯ -->
<div id="lotto" class="screen">
  <button class="back" id="back-lotto">← НАЗАД</button>
  <h2>🎟️ ЛОТЕРЕЯ</h2>
  <div class="status" id="lotto-status">ВЫБЕРИ СТАВКУ</div>
  <div class="bet-buttons" id="lotto-buttons"></div>
  <div class="lotto" id="lotto-grid"></div>
</div>

<!-- ПОКЕР -->
<div id="poker" class="screen">
  <button class="back" id="back-poker">← НАЗАД</button>
  <h2>🃏 ХАЙ-ЛОУ</h2>
  <div class="status" id="poker-status">ВЫБЕРИ СТАВКУ</div>
  <div class="bet-buttons" id="poker-buttons"></div>
  <div class="poker-row" id="poker-row"></div>
  <div class="grid-3" id="poker-actions" style="margin-top:10px;display:none;">
    <button class="bet-btn" data-guess="higher">БОЛЬШЕ ↑</button>
    <button class="bet-btn" data-guess="lower">МЕНЬШЕ ↓</button>
    <button class="bet-btn" data-guess="equal">РАВНО =</button>
  </div>
</div>

<!-- 3 МОНЕТКИ -->
<div id="coin3" class="screen">
  <button class="back" id="back-coin3">← НАЗАД</button>
  <h2>🪙 3 МОНЕТКИ</h2>
  <div class="status" id="coin3-status">ВЫБЕРИ СТАВКУ</div>
  <div class="bet-buttons" id="coin3-buttons"></div>
  <div class="coin3-row">
    <div class="coin3" id="c3-0">?</div>
    <div class="coin3" id="c3-1">?</div>
    <div class="coin3" id="c3-2">?</div>
  </div>
  <div class="grid-3" id="coin3-actions">
    <button class="bet-btn" data-c3="О">ВСЕ ОРЛЫ</button>
    <button class="bet-btn" data-c3="Р">ВСЕ РЕШКИ</button>
    <button class="bet-btn" data-c3="А">ЛЮБОЕ</button>
  </div>
</div>

<!-- БИНГО -->
<div id="bingo" class="screen">
  <button class="back" id="back-bingo">← НАЗАД</button>
  <h2>🅱️ БИНГО</h2>
  <div class="status" id="bingo-status">ВЫБЕРИ СТАВКУ</div>
  <div class="bet-buttons" id="bingo-buttons"></div>
  <div class="bingo-grid" id="bingo-grid"></div>
</div>

<!-- КЕНО -->
<div id="keno" class="screen">
  <button class="back" id="back-keno">← НАЗАД</button>
  <h2>🎯 КЕНО</h2>
  <div class="status" id="keno-status">ВЫБЕРИ 5 ЧИСЕЛ И СТАВКУ</div>
  <div class="bet-buttons" id="keno-buttons"></div>
  <div class="keno-grid" id="keno-grid"></div>
</div>

<!-- ТЕТРИС -->
<div id="tetris" class="screen">
  <button class="back" id="back-tetris">← НАЗАД</button>
  <h2>🎮 ТЕТРИС</h2>
  <div class="status" id="tetris-status">ВЫБЕРИ СТАВКУ</div>
  <div class="bet-buttons" id="tetris-buttons"></div>
  <div class="tetris-stage" id="tetris-stage"></div>
</div>

<!-- ИНВЕНТАРЬ -->
<div id="inv" class="screen">
  <button class="back" id="back-inv">← НАЗАД</button>
  <h2>🎁 ИНВЕНТАРЬ</h2>
  <div class="status" id="inv-status">ТВОИ NFT</div>
  <div class="nft-grid" id="inv-list" style="display:grid;grid-template-columns:1fr 1fr;gap:10px;"></div>
</div>

<script>
var tg = null;
try { tg = window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null; if (tg) { tg.ready(); tg.expand(); } } catch(e){}
var user = (tg && tg.initDataUnsafe && tg.initDataUnsafe.user) ? tg.initDataUnsafe.user : { id: 0 };
var BETS = [100, 500, 1000, 5000];
var balance = 10000;
var inventory = [];

function fmt(k){ return (k/100).toFixed(2); }
function showAlert(m){ if (tg && tg.showAlert) tg.showAlert(m); else alert(m); }
function $(id){ return document.getElementById(id); }
function updateUI(){ var el = $('balance'); if (el) el.textContent = fmt(balance); }

function loadBalance(){
  fetch('/api/balance?user_id='+user.id).then(function(r){return r.json();}).then(function(d){ balance=d.balance; inventory=d.inventory||[]; updateUI(); }).catch(function(e){});
}
function changeBalance(delta){
  return fetch('/api/balance',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user_id:user.id,delta:delta})}).then(function(r){return r.json();}).then(function(d){ balance=d.balance; inventory=d.inventory||[]; updateUI(); });
}
function addNft(){
  var keys = Object.keys(GIFTS);
  var id = keys[Math.floor(Math.random()*keys.length)];
  return fetch('/api/nft',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user_id:user.id,gift_id:id})}).then(function(r){return r.json();}).then(function(d){ if (d.inventory) inventory=d.inventory; return id; });
}
function maybeGiveNft(mult){
  if (Math.random() < 0.12 && mult >= 3) {
    addNft().then(function(id){ var g=GIFTS[id]; if(g) showAlert('🎁 NFT: '+g.emoji+' '+g.name); });
  }
}
function showScreen(id){
  var s = document.querySelectorAll('.screen');
  for (var i=0;i<s.length;i++) s[i].classList.remove('active');
  $(id).classList.add('active');
}
function goMenu(){ showScreen('menu'); }
function makeBetButtons(cid, cb){
  var c = $(cid); if (!c) return; c.innerHTML='';
  for (var i=0;i<BETS.length;i++){(function(bet){
    var b = document.createElement('button'); b.className='bet-btn'; b.textContent=fmt(bet)+' ₽';
    b.addEventListener('click', function(){ cb(bet); }); c.appendChild(b);
  })(BETS[i]);}
}

// ==== МЕНЮ ====
var menuMap = {
  'btn-bj':'bj','btn-dart':'dart','btn-penalty':'penalty','btn-box':'box','btn-basket':'basket',
  'btn-race':'race','btn-fish':'fish','btn-case':'case','btn-lotto':'lotto','btn-poker':'poker',
  'btn-coin3':'coin3','btn-bingo':'bingo','btn-keno':'keno','btn-tetris':'tetris','btn-inv':'inv'
};
for (var k in menuMap){(function(sid){
  var b = $(k); if (b) b.addEventListener('click', function(){ showScreen(sid); initGame(sid); });
})(menuMap[k]);}
['bj','dart','penalty','box','basket','race','fish','case','lotto','poker','coin3','bingo','keno','tetris','inv'].forEach(function(id){
  var b = $('back-'+id); if (b) b.addEventListener('click', goMenu);
});

function initGame(id){
  if (id==='bj') initBJ();
  if (id==='dart') initDart();
  if (id==='penalty') initPenalty();
  if (id==='box') initBox();
  if (id==='basket') initBasket();
  if (id==='race') initRace();
  if (id==='fish') initFish();
  if (id==='case') initCase();
  if (id==='lotto') initLotto();
  if (id==='poker') initPoker();
  if (id==='coin3') initCoin3();
  if (id==='bingo') initBingo();
  if (id==='keno') initKeno();
  if (id==='tetris') initTetris();
  if (id==='inv') renderInv();
}

// ============ БЛЭКДЖЕК ============
var bjBet=0, bjActive=false, bjP=[], bjD=[];
function cardVal(c){ if(c.val==='A') return 11; if(['K','Q','J'].indexOf(c.val)>=0) return 10; return parseInt(c.val); }
function drawCard(){
  var vals = ['A','2','3','4','5','6','7','8','9','10','J','Q','K'];
  var suits = ['♠','♥','♦','♣'];
  var v = vals[Math.floor(Math.random()*vals.length)];
  var s = suits[Math.floor(Math.random()*suits.length)];
  return { val: v, suit: s, red: (s==='♥'||s==='♦') };
}
function bjSum(arr){
  var sum = 0, aces = 0;
  for (var i=0;i<arr.length;i++){ sum += cardVal(arr[i]); if (arr[i].val==='A') aces++; }
  while (sum > 21 && aces > 0){ sum -= 10; aces--; }
  return sum;
}
function renderBJCard(c){
  return '<div class="bj-card'+(c.red?' red':'')+'">'+c.val+'<br>'+c.suit+'</div>';
}
function initBJ(){
  bjBet=0; bjActive=false; bjP=[]; bjD=[];
  $('bj-dealer').innerHTML=''; $('bj-player').innerHTML='';
  $('bj-dscore').textContent='0'; $('bj-pscore').textContent='0';
  $('bj-status').textContent='ВЫБЕРИ СТАВКУ';
  $('bj-buttons').style.display='grid';
  $('bj-actions').style.display='none';
  makeBetButtons('bj-buttons', startBJ);
}
function startBJ(bet){
  if (bet > balance){ showAlert('Недостаточно'); return; }
  bjBet = bet; bjActive = true;
  changeBalance(-bet).then(function(){
    bjP = [drawCard(), drawCard()];
    bjD = [drawCard(), drawCard()];
    renderBJ();
    $('bj-buttons').style.display='none';
    $('bj-actions').style.display='grid';
    $('bj-status').textContent='ТВОЙ ХОД';
  });
}
function renderBJ(){
  $('bj-player').innerHTML = bjP.map(renderBJCard).join('');
  $('bj-dealer').innerHTML = bjD.map(renderBJCard).join('');
  $('bj-pscore').textContent = bjSum(bjP);
  $('bj-dscore').textContent = bjSum(bjD);
}
$('bj-hit').addEventListener('click', function(){
  if (!bjActive) return;
  bjP.push(drawCard());
  renderBJ();
  if (bjSum(bjP) > 21){
    bjActive=false;
    $('bj-status').textContent='ПЕРЕБОР! -'+fmt(bjBet)+' ₽';
    $('bj-actions').style.display='none';
    setTimeout(initBJ, 3000);
  }
});
$('bj-stand').addEventListener('click', function(){
  if (!bjActive) return;
  bjActive=false;
  var d = bjSum(bjD), p = bjSum(bjP);
  while (d < 17){ bjD.push(drawCard()); d = bjSum(bjD); }
  renderBJ();
  if (d > 21 || p > d){
    var win = bjBet*2;
    changeBalance(win).then(function(){
      $('bj-status').textContent='ПОБЕДА! +'+fmt(win)+' ₽';
      if (p === 21) maybeGiveNft(5);
      setTimeout(initBJ, 3000);
    });
  } else if (p === d){
    changeBalance(bjBet).then(function(){ $('bj-status').textContent='НИЧЬЯ'; setTimeout(initBJ,3000); });
  } else {
    $('bj-status').textContent='ПРОИГРАЛ -'+fmt(bjBet)+' ₽';
    setTimeout(initBJ, 3000);
  }
  $('bj-actions').style.display='none';
});

// ============ ДАРТС ============
function initDart(){
  $('dart-status').textContent='ВЫБЕРИ СТАВКУ';
  $('dart-board').innerHTML='';
  makeBetButtons('dart-buttons', playDart);
}
function playDart(bet){
  if (bet > balance){ showAlert('Недостаточно'); return; }
  changeBalance(-bet).then(function(){
    $('dart-buttons').innerHTML='';
    $('dart-status').textContent='БРОСАЕМ...';
    var board = $('dart-board');
    board.innerHTML='';
    var cx=140, cy=140;
    var dist = Math.sqrt(Math.random()) * 140;
    var ang = Math.random() * Math.PI * 2;
    var x = cx + Math.cos(ang)*dist, y = cy + Math.sin(ang)*dist;
    var dot = document.createElement('div'); dot.className='dart-dot';
    dot.style.left = x+'px'; dot.style.top = y+'px';
    board.appendChild(dot);
    var mult = 0, name='МИМО';
    if (dist < 14){ mult = 50; name='В ЯБЛОЧКО x50'; }
    else if (dist < 42){ mult = 10; name='КРАСНОЕ КОЛЬЦО x10'; }
    else if (dist < 70){ mult = 5; name='БЕЛОЕ x5'; }
    else if (dist < 105){ mult = 2; name='СРЕДНЕЕ x2'; }
    else if (dist < 130){ mult = 1.5; name='ВНЕШНЕЕ x1.5'; }
    var win = Math.floor(bet*mult);
    var done = function(){
      $('dart-status').textContent = name + (win ? ' +'+fmt(win)+' ₽' : '');
      if (mult >= 5) maybeGiveNft(mult);
      setTimeout(initDart, 3000);
    };
    if (win > 0) changeBalance(win).then(done); else done();
  });
}

// ============ ПЕНАЛЬТИ ============
var penBusy=false, penZone='';
function initPenalty(){
  penBusy=false; penZone='';
  $('penalty-status').textContent='ВЫБЕРИ СТАВКУ';
  $('keeper').style.left='calc(50% - 30px)';
  $('ball-pen').style.left='calc(50% - 18px)';
  $('ball-pen').style.bottom='20px';
  makeBetButtons('penalty-buttons', playPenalty);
  var zs = document.querySelectorAll('[data-zone]');
  for (var i=0;i<zs.length;i++){(function(b){
    b.onclick = function(){ penZone = b.getAttribute('data-zone'); $('penalty-status').textContent='УГОЛ: '+penZone+' | ВЫБЕРИ СТАВКУ'; };
  })(zs[i]);}
}
function playPenalty(bet){
  if (penBusy) return;
  if (!penZone){ showAlert('Выбери угол'); return; }
  if (bet > balance){ showAlert('Недостаточно'); return; }
  penBusy=true;
  changeBalance(-bet).then(function(){
    $('penalty-buttons').innerHTML='';
    $('penalty-status').textContent='БЬЁМ...';
    var zones = ['left','center','right'];
    var keeperZone = zones[Math.floor(Math.random()*3)];
    var kpos = {left:20, center:'calc(50% - 30px)', right:'calc(100% - 80px)'};
    $('keeper').style.left = kpos[keeperZone];
    var bpos = {left:40, center:'calc(50% - 18px)', right:'calc(100% - 90px)'};
    $('ball-pen').style.left = bpos[penZone];
    $('ball-pen').style.bottom = '120px';
    setTimeout(function(){
      var goal = penZone !== keeperZone;
      var mult = (penZone==='center' && keeperZone!=='center') ? 3 : 2;
      var win = goal ? bet*mult : 0;
      var done = function(){
        $('penalty-status').textContent = goal ? ('ГОЛ! +'+fmt(win)+' ₽ (x'+mult+')') : ('ВРАТАРЬ ВЗЯЛ! -'+fmt(bet)+' ₽');
        if (goal) maybeGiveNft(mult);
        penBusy=false;
        setTimeout(initPenalty, 3000);
      };
      if (win > 0) changeBalance(win).then(done); else done();
    }, 700);
  });
}

// ============ БОКС ============
var boxBusy=false, boxHP=100, boxFoeHP=100, boxBet=0;
function initBox(){
  boxBusy=false; boxHP=100; boxFoeHP=100; boxBet=0;
  $('box-status').textContent='ВЫБЕРИ СТАВКУ';
  $('box-me').textContent='🥋'; $('box-foe').textContent='🥊';
  $('box-me').style.left='20px'; $('box-foe').style.right='20px';
  makeBetButtons('box-buttons', startBox);
}
function startBox(bet){
  if (bet > balance){ showAlert('Недостаточно'); return; }
  boxBet=bet; boxHP=100; boxFoeHP=100; boxBusy=true;
  changeBalance(-bet).then(function(){
    $('box-buttons').innerHTML='';
    $('box-status').textContent='БОЙ! HP: '+boxHP+' | ВРАГ: '+boxFoeHP;
  });
}
var boxBtns = document.querySelectorAll('[data-punch]');
for (var i=0;i<boxBtns.length;i++){(function(b){
  b.addEventListener('click', function(){
    if (!boxBusy) return;
    var p = b.getAttribute('data-punch');
    var dmg = {jab:8, hook:14, uppercut:20, block:0}[p];
    var foeDodge = Math.random() < 0.3;
    if (!foeDodge && dmg > 0) boxFoeHP -= dmg;
    var foeDmg = Math.floor(Math.random()*15) + 5;
    if (p === 'block') foeDmg = Math.floor(foeDmg * 0.3);
    boxHP -= foeDmg;
    $('box-status').textContent = 'HP: '+Math.max(0,boxHP)+' | ВРАГ: '+Math.max(0,boxFoeHP);
    if (boxFoeHP <= 0){
      boxBusy=false;
      var win = boxBet*2;
      changeBalance(win).then(function(){ $('box-status').textContent='НОКАУТ! +'+fmt(win)+' ₽'; maybeGiveNft(2); setTimeout(initBox,3000); });
    } else if (boxHP <= 0){
      boxBusy=false;
      $('box-status').textContent='ТЫ ПРОИГРАЛ -'+fmt(boxBet)+' ₽';
      setTimeout(initBox, 3000);
    }
  });
})(boxBtns[i]);}

// ============ БАСКЕТБОЛ ============
function initBasket(){
  $('basket-status').textContent='ВЫБЕРИ СТАВКУ';
  $('basket-ball').style.left='20px';
  $('basket-ball').style.bottom='20px';
  $('basket-ball').style.top='auto';
  makeBetButtons('basket-buttons', playBasket);
}
function playBasket(bet){
  if (bet > balance){ showAlert('Недостаточно'); return; }
  changeBalance(-bet).then(function(){
    $('basket-buttons').innerHTML='';
    $('basket-status').textContent='БРОСОК...';
    var ball = $('basket-ball');
    ball.style.left = 'calc(100% - 80px)';
    ball.style.bottom = '120px';
    setTimeout(function(){
      var chance = Math.random();
      var mult = 0, name='МИМО';
      if (chance < 0.15){ mult=5; name='ЧИСТЫЙ БРОСОК x5'; }
      else if (chance < 0.45){ mult=2; name='ПОПАЛ x2'; }
      else if (chance < 0.55){ mult=1; name='ЩИТ x1'; }
      var win = bet*mult;
      var done = function(){
        $('basket-status').textContent = name + (win ? ' +'+fmt(win)+' ₽' : '');
        if (mult >= 3) maybeGiveNft(mult);
        setTimeout(initBasket, 3000);
      };
      if (win > 0) changeBalance(win).then(done); else done();
    }, 900);
  });
}

// ============ СКАЧКИ ============
var raceBet=0, raceHorse=0, raceRunning=false, raceLoop=null, racePos=[];
function initRace(){
  if (raceLoop){ clearInterval(raceLoop); raceLoop=null; }
  raceBet=0; raceHorse=0; raceRunning=false; racePos=[0,0,0,0];
  $('race-status').textContent='ВЫБЕРИ ЛОШАДЬ И СТАВКУ';
  var t = $('race-track'); t.innerHTML='';
  var horses = ['🐎','🏇','🦄','🐴'];
  for (var i=0;i<4;i++){
    var lane = document.createElement('div'); lane.className='race-lane';
    lane.style.top = (i*50)+'px';
    lane.innerHTML = '<span class="horse" id="horse-'+i+'">'+horses[i]+'</span>';
    lane.style.cursor='pointer';
    (function(idx){ lane.addEventListener('click', function(){ raceHorse=idx; $('race-status').textContent='ЛОШАДЬ '+(idx+1)+' | ВЫБЕРИ СТАВКУ'; }); })(i);
    t.appendChild(lane);
  }
  makeBetButtons('race-buttons', startRace);
}
function startRace(bet){
  if (!raceHorse && raceHorse !== 0){ showAlert('Выбери лошадь'); return; }
  if (bet > balance){ showAlert('Недостаточно'); return; }
  raceBet=bet; raceRunning=true; racePos=[0,0,0,0];
  changeBalance(-bet).then(function(){
    $('race-buttons').innerHTML='';
    $('race-status').textContent='ЗАЕЗД!';
    var t = $('race-track');
    var fin = t.clientWidth - 60;
    raceLoop = setInterval(function(){
      for (var i=0;i<4;i++){
        racePos[i] += Math.random()*8 + 2;
        var h = $('horse-'+i);
        if (h) h.style.transform = 'translateX('+Math.min(racePos[i], fin)+'px)';
      }
      for (var i=0;i<4;i++){
        if (racePos[i] >= fin){
          clearInterval(raceLoop); raceLoop=null; raceRunning=false;
          var winner = i;
          var mult = (winner === raceHorse) ? 3 : 0;
          var win = bet*mult;
          var done = function(){
            $('race-status').textContent = (winner === raceHorse) ? ('ПОБЕДА! ЛОШАДЬ '+(winner+1)+' +'+fmt(win)+' ₽') : ('ПРОИГРАЛ. Победила лошадь '+(winner+1));
            if (mult) maybeGiveNft(mult);
            setTimeout(initRace, 3000);
          };
          if (win > 0) changeBalance(win).then(done); else done();
          return;
        }
      }
    }, 60);
  });
}

// ============ РЫБАЛКА ============
var fishBet=0, fishRunning=false, fishLoop=null, fishCatchTimer=null;
function initFish(){
  if (fishLoop){ clearInterval(fishLoop); fishLoop=null; }
  if (fishCatchTimer){ clearTimeout(fishCatchTimer); fishCatchTimer=null; }
  fishBet=0; fishRunning=false;
  $('fish-status').textContent='ВЫБЕРИ СТАВКУ';
  $('fish-catch').style.display='none';
  var p = $('fish-pond');
  var olds = p.querySelectorAll('.fish'); for(var i=0;i<olds.length;i++) olds[i].remove();
  makeBetButtons('fish-buttons', startFish);
}
function startFish(bet){
  if (bet > balance){ showAlert('Недостаточно'); return; }
  fishBet=bet; fishRunning=true;
  changeBalance(-bet).then(function(){
    $('fish-buttons').innerHTML='';
    $('fish-status').textContent='ЖДИ ПОКЛЁВКИ...';
    $('fish-catch').style.display='block';
    var p = $('fish-pond');
    var fishes = ['🐟','🐠','🐡','🦈','🐙'];
    var fish = document.createElement('div'); fish.className='fish';
    fish.textContent = fishes[Math.floor(Math.random()*fishes.length)];
    fish.style.top = (30+Math.random()*140)+'px';
    fish.style.left = '100%';
    p.appendChild(fish);
    var x = p.clientWidth;
    fishLoop = setInterval(function(){
      x -= 2; fish.style.left = x+'px';
      if (x < -60){ x = p.clientWidth; }
    }, 30);
    var bite = 1000 + Math.random()*3000;
    fishCatchTimer = setTimeout(function(){
      $('fish-status').textContent='ПОКЛЁВКА! ЖМИ!';
    }, bite);
  });
}
$('fish-catch').addEventListener('click', function(){
  if (!fishRunning) return;
  fishRunning=false;
  if (fishLoop){ clearInterval(fishLoop); fishLoop=null; }
  if (fishCatchTimer){ clearTimeout(fishCatchTimer); fishCatchTimer=null; }
  $('fish-catch').style.display='none';
  var r = Math.random();
  var mult = 0, name='СОРВАЛАСЬ';
  if (r < 0.4){ mult=2; name='ПОЙМАЛ x2'; }
  else if (r < 0.65){ mult=3; name='БОЛЬШАЯ x3'; }
  else if (r < 0.85){ mult=5; name='ГИГАНТ x5'; }
  var win = fishBet*mult;
  var done = function(){
    $('fish-status').textContent = name + (win ? ' +'+fmt(win)+' ₽' : '');
    if (mult >= 3) maybeGiveNft(mult);
    setTimeout(initFish, 3000);
  };
  if (win > 0) changeBalance(win).then(done); else done();
});

// ============ КЕЙСЫ ============
var caseBusy=false;
function initCase(){
  caseBusy=false;
  $('case-status').textContent='ВЫБЕРИ СТАВКУ';
  var row = $('case-row'); row.innerHTML='';
  makeBetButtons('case-buttons', playCase);
}
function playCase(bet){
  if (caseBusy) return;
  if (bet > balance){ showAlert('Недостаточно'); return; }
  caseBusy=true;
  changeBalance(-bet).then(function(){
    $('case-buttons').innerHTML='';
    $('case-status').textContent='КРУТИМ...';
    var row = $('case-row'); row.innerHTML='';
    var prizes = [
      {e:'💎',m:50},{e:'👑',m:20},{e:'⭐',m:10},{e:'🚀',m:5},{e:'🪐',m:3},
      {e:'💀',m:0},{e:'🔥',m:2},{e:'🌙',m:1.5},{e:'⚡',m:2},{e:'☄️',m:4},
      {e:'💀',m:0},{e:'💀',m:0},{e:'💀',m:0},{e:'🍀',m:8},{e:'🎁',m:1}
    ];
    var arr = [];
    for (var i=0;i<40;i++){
      var p = prizes[Math.floor(Math.random()*prizes.length)];
      arr.push(p);
      var d = document.createElement('div'); d.className='case-item'; d.textContent=p.e;
      row.appendChild(d);
    }
    var winner = prizes[Math.floor(Math.random()*prizes.length)];
    var winIdx = 30 + Math.floor(Math.random()*4);
    arr[winIdx] = winner;
    var items = row.children;
    items[winIdx].textContent = winner.e;
    var shift = winIdx * 76 - row.clientWidth/2 + 35;
    row.style.transition = 'transform 4s cubic-bezier(.15,.85,.25,1)';
    row.style.transform = 'translateX(-'+shift+'px)';
    setTimeout(function(){
      items[winIdx].classList.add('win');
      var win = Math.floor(bet*winner.m);
      var done = function(){
        $('case-status').textContent = 'ВЫПАЛО '+winner.e+' x'+winner.m+' → '+(win ? '+'+fmt(win)+' ₽' : 'ПУСТО');
        if (winner.m >= 5) maybeGiveNft(winner.m);
        row.style.transition='none'; row.style.transform='translateX(0)';
        caseBusy=false;
        setTimeout(initCase, 3000);
      };
      if (win > 0) changeBalance(win).then(done); else done();
    }, 4200);
  });
}

// ============ ЛОТЕРЕЯ ============
var lottoBusy=false;
function initLotto(){
  lottoBusy=false;
  $('lotto-status').textContent='ВЫБЕРИ СТАВКУ';
  var g = $('lotto-grid'); g.innerHTML='';
  for (var i=1;i<=20;i++){
    var b = document.createElement('div'); b.className='lotto-ball'; b.textContent=i; g.appendChild(b);
  }
  makeBetButtons('lotto-buttons', playLotto);
}
function playLotto(bet){
  if (lottoBusy) return;
  if (bet > balance){ showAlert('Недостаточно'); return; }
  lottoBusy=true;
  changeBalance(-bet).then(function(){
    $('lotto-buttons').innerHTML='';
    $('lotto-status').textContent='РОЗЫГРЫШ...';
    var balls = $('lotto-grid').children;
    for (var i=0;i<20;i++) balls[i].className='lotto-ball';
    var picks = [];
    while (picks.length < 5){ var n = Math.floor(Math.random()*20); if (picks.indexOf(n)<0) picks.push(n); }
    var hits = 0;
    var step = 0;
    var anim = setInterval(function(){
      if (step < 5){
        balls[picks[step]].classList.add('hit');
        hits++;
        step++;
      } else {
        clearInterval(anim);
        var mult = hits === 5 ? 20 : (hits === 4 ? 5 : (hits === 3 ? 2 : 0));
        var win = bet*mult;
        var done = function(){
          $('lotto-status').textContent = 'СОВПАЛО: '+hits+'/5 → '+(win ? '+'+fmt(win)+' ₽ (x'+mult+')' : 'МИМО');
          if (mult >= 5) maybeGiveNft(mult);
          lottoBusy=false;
          setTimeout(initLotto, 3000);
        };
        if (win > 0) changeBalance(win).then(done); else done();
      }
    }, 400);
  });
}

// ============ ПОКЕР ХАЙ-ЛОУ ============
var pokerBet=0, pokerActive=false, pokerCurrent=null;
function initPoker(){
  pokerBet=0; pokerActive=false; pokerCurrent=null;
  $('poker-status').textContent='ВЫБЕРИ СТАВКУ';
  $('poker-row').innerHTML='';
  $('poker-actions').style.display='none';
  makeBetButtons('poker-buttons', startPoker);
}
function drawPoker(){
  var vals = ['2','3','4','5','6','7','8','9','10','J','Q','K','A'];
  var suits = ['♠','♥','♦','♣'];
  return { v: vals[Math.floor(Math.random()*vals.length)], s: suits[Math.floor(Math.random()*suits.length)], idx:0 };
}
function cardRank(c){ return ['2','3','4','5','6','7','8','9','10','J','Q','K','A'].indexOf(c.v); }
function startPoker(bet){
  if (bet > balance){ showAlert('Недостаточно'); return; }
  pokerBet=bet; pokerActive=true;
  changeBalance(-bet).then(function(){
    $('poker-buttons').innerHTML='';
    pokerCurrent = drawPoker();
    $('poker-row').innerHTML = '<div class="poker-card">'+pokerCurrent.v+'<br>'+pokerCurrent.s+'</div>';
    $('poker-actions').style.display='grid';
    $('poker-status').textContent='БОЛЬШЕ / МЕНЬШЕ / РАВНО?';
  });
}
var pokerBtns = document.querySelectorAll('[data-guess]');
for (var i=0;i<pokerBtns.length;i++){(function(b){
  b.addEventListener('click', function(){
    if (!pokerActive) return;
    var g = b.getAttribute('data-guess');
    var next = drawPoker();
    var curR = cardRank(pokerCurrent), nxtR = cardRank(next);
    var row = $('poker-row');
    row.innerHTML += '<div class="poker-card">'+next.v+'<br>'+next.s+'</div>';
    var correct = false;
    if (g === 'higher' && nxtR > curR) correct = true;
    if (g === 'lower' && nxtR < curR) correct = true;
    if (g === 'equal' && nxtR === curR) correct = true;
    pokerActive=false;
    $('poker-actions').style.display='none';
    if (correct){
      var mult = g === 'equal' ? 10 : 2;
      var win = pokerBet*mult;
      changeBalance(win).then(function(){
        $('poker-status').textContent='УГАДАЛ! +'+fmt(win)+' ₽';
        if (mult >= 5) maybeGiveNft(mult);
        setTimeout(initPoker, 3000);
      });
    } else {
      $('poker-status').textContent='НЕ УГАДАЛ -'+fmt(pokerBet)+' ₽';
      setTimeout(initPoker, 3000);
    }
  });
})(pokerBtns[i]);}

// ============ 3 МОНЕТКИ ============
var coin3Bet=0, coin3Pick='', coin3Busy=false;
function initCoin3(){
  coin3Bet=0; coin3Pick=''; coin3Busy=false;
  $('coin3-status').textContent='ВЫБЕРИ СТАВКУ';
  for (var i=0;i<3;i++){ $('c3-'+i).textContent='?'; $('c3-'+i).classList.remove('flip'); }
  makeBetButtons('coin3-buttons', playCoin3);
}
var c3Btns = document.querySelectorAll('[data-c3]');
for (var i=0;i<c3Btns.length;i++){(function(b){
  b.addEventListener('click', function(){
    coin3Pick = b.getAttribute('data-c3');
    $('coin3-status').textContent='ВЫБРАНО: '+(coin3Pick==='О'?'ВСЕ ОРЛЫ':(coin3Pick==='Р'?'ВСЕ РЕШКИ':'ЛЮБОЕ'))+' | ВЫБЕРИ СТАВКУ';
  });
})(c3Btns[i]);}
function playCoin3(bet){
  if (coin3Busy) return;
  if (!coin3Pick){ showAlert('Выбери вариант'); return; }
  if (bet > balance){ showAlert('Недостаточно'); return; }
  coin3Busy=true;
  changeBalance(-bet).then(function(){
    $('coin3-buttons').innerHTML='';
    $('coin3-status').textContent='БРОСАЕМ...';
    for (var i=0;i<3;i++) $('c3-'+i).classList.add('flip');
    setTimeout(function(){
      var results = [];
      for (var i=0;i<3;i++){
        var r = Math.random() < 0.5 ? 'О' : 'Р';
        results.push(r);
        $('c3-'+i).classList.remove('flip');
        $('c3-'+i).textContent = r === 'О' ? 'ОРЁЛ' : 'РЕШКА';
      }
      var allO = results.every(function(x){return x==='О';});
      var allR = results.every(function(x){return x==='Р';});
      var mult = 0;
      if (coin3Pick === 'О' && allO) mult = 7;
      else if (coin3Pick === 'Р' && allR) mult = 7;
      else if (coin3Pick === 'А' && !allO && !allR) mult = 1.5;
      var win = Math.floor(bet*mult);
      var done = function(){
        $('coin3-status').textContent = mult ? ('ВЫИГРЫШ x'+mult+' +'+fmt(win)+' ₽') : 'МИМО';
        if (mult >= 5) maybeGiveNft(mult);
        coin3Busy=false;
        setTimeout(initCoin3, 3000);
      };
      if (win > 0) changeBalance(win).then(done); else done();
    }, 1200);
  });
}

// ============ БИНГО ============
var bingoBusy=false;
function initBingo(){
  bingoBusy=false;
  $('bingo-status').textContent='ВЫБЕРИ СТАВКУ';
  var g = $('bingo-grid'); g.innerHTML='';
  for (var i=0;i<25;i++){
    var n = i+1;
    var c = document.createElement('div'); c.className='bingo-cell'; c.textContent=n;
    g.appendChild(c);
  }
  makeBetButtons('bingo-buttons', playBingo);
}
function playBingo(bet){
  if (bingoBusy) return;
  if (bet > balance){ showAlert('Недостаточно'); return; }
  bingoBusy=true;
  changeBalance(-bet).then(function(){
    $('bingo-buttons').innerHTML='';
    $('bingo-status').textContent='РОЗЫГРЫШ...';
    var cells = $('bingo-grid').children;
    for (var i=0;i<25;i++) cells[i].className='bingo-cell';
    var drawn = [];
    var wins = 0;
    var step = 0;
    var anim = setInterval(function(){
      if (step < 12){
        var n;
        do { n = Math.floor(Math.random()*25); } while (drawn.indexOf(n) >= 0);
        drawn.push(n);
        cells[n].classList.add('marked');
        step++;
      } else {
        clearInterval(anim);
        var lines = 0;
        for (var r=0;r<5;r++){ var cnt=0; for (var c=0;c<5;c++) if (drawn.indexOf(r*5+c)>=0) cnt++; if (cnt===5) lines++; }
        for (var c=0;c<5;c++){ var cnt=0; for (var r=0;r<5;r++) if (drawn.indexOf(r*5+c)>=0) cnt++; if (cnt===5) lines++; }
        var mult = lines >= 2 ? 10 : (lines === 1 ? 3 : 0);
        var win = bet*mult;
        var done = function(){
          $('bingo-status').textContent = 'ЛИНИЙ: '+lines+' → '+(win ? '+'+fmt(win)+' ₽' : 'МИМО');
          if (mult >= 5) maybeGiveNft(mult);
          bingoBusy=false;
          setTimeout(initBingo, 3000);
        };
        if (win > 0) changeBalance(win).then(done); else done();
      }
    }, 250);
  });
}

// ============ КЕНО ============
var kenoPicks=[], kenoBusy=false;
function initKeno(){
  kenoPicks=[]; kenoBusy=false;
  $('keno-status').textContent='ВЫБЕРИ 5 ЧИСЕЛ И СТАВКУ';
  var g = $('keno-grid'); g.innerHTML='';
  for (var i=1;i<=40;i++){
    (function(n){
      var c = document.createElement('div'); c.className='keno-cell'; c.textContent=n;
      c.addEventListener('click', function(){
        if (kenoBusy) return;
        var idx = kenoPicks.indexOf(n);
        if (idx >= 0){ kenoPicks.splice(idx,1); c.classList.remove('picked'); }
        else if (kenoPicks.length < 5){ kenoPicks.push(n); c.classList.add('picked'); }
        $('keno-status').textContent = 'ВЫБРАНО: '+kenoPicks.length+'/5';
      });
      g.appendChild(c);
    })(i);
  }
  makeBetButtons('keno-buttons', playKeno);
}
function playKeno(bet){
  if (kenoBusy) return;
  if (kenoPicks.length !== 5){ showAlert('Выбери 5 чисел'); return; }
  if (bet > balance){ showAlert('Недостаточно'); return; }
  kenoBusy=true;
  changeBalance(-bet).then(function(){
    $('keno-buttons').innerHTML='';
    $('keno-status').textContent='РОЗЫГРЫШ...';
    var drawn = [];
    while (drawn.length < 10){ var n = Math.floor(Math.random()*40)+1; if (drawn.indexOf(n)<0) drawn.push(n); }
    var cells = $('keno-grid').children;
    var step = 0;
    var anim = setInterval(function(){
      if (step < 10){
        cells[drawn[step]-1].classList.add('hit');
        step++;
      } else {
        clearInterval(anim);
        var hits = 0;
        for (var i=0;i<kenoPicks.length;i++) if (drawn.indexOf(kenoPicks[i])>=0) hits++;
        var mults = {0:0, 1:0, 2:1, 3:3, 4:10, 5:50};
        var mult = mults[hits] || 0;
        var win = bet*mult;
        var done = function(){
          $('keno-status').textContent = 'СОВПАЛО: '+hits+'/5 → '+(win ? '+'+fmt(win)+' ₽ (x'+mult+')' : 'МИМО');
          if (mult >= 5) maybeGiveNft(mult);
          kenoBusy=false;
          setTimeout(initKeno, 3000);
        };
        if (win > 0) changeBalance(win).then(done); else done();
      }
    }, 250);
  });
}

// ============ ТЕТРИС ============
var tetrisBet=0, tetrisActive=false, tetrisLoop=null, tetrisScore=0, tetrisBombAt=0;
function initTetris(){
  if (tetrisLoop){ clearInterval(tetrisLoop); tetrisLoop=null; }
  tetrisBet=0; tetrisActive=false; tetrisScore=0; tetrisBombAt=0;
  $('tetris-status').textContent='ВЫБЕРИ СТАВКУ';
  var s = $('tetris-stage'); s.innerHTML='';
  makeBetButtons('tetris-buttons', startTetris);
}
function startTetris(bet){
  if (bet > balance){ showAlert('Недостаточно'); return; }
  tetrisBet=bet; tetrisActive=true; tetrisScore=0;
  tetrisBombAt = Math.floor(Math.random()*10) + 8;
  changeBalance(-bet).then(function(){
    $('tetris-buttons').innerHTML='';
    var s = $('tetris-stage'); s.innerHTML='';
    var colors = ['#4aff8a','#4a3aff','#ffdd44','#ff3a5a','#88eeff','#ffaa00'];
    tetrisLoop = setInterval(function(){
      if (!tetrisActive) return;
      tetrisScore++;
      var x = Math.floor(Math.random()*(s.clientWidth/20))*20;
      var y = -20;
      var b = document.createElement('div'); b.className='tetris-block';
      b.style.left = x+'px'; b.style.top = y+'px';
      b.style.background = colors[Math.floor(Math.random()*colors.length)];
      s.appendChild(b);
      var fy = y;
      var fall = setInterval(function(){
        fy += 4;
        b.style.top = fy+'px';
        if (fy > s.clientHeight){
          clearInterval(fall);
          b.remove();
        }
      }, 30);
      $('tetris-status').textContent='СЧЁТ: '+tetrisScore+' | x'+(1+tetrisScore*0.1).toFixed(2);
      if (tetrisScore >= tetrisBombAt){
        tetrisActive=false;
        clearInterval(tetrisLoop); tetrisLoop=null;
        var mult = +(1 + tetrisScore*0.15).toFixed(2);
        var win = Math.floor(tetrisBet*mult);
        changeBalance(win).then(function(){
          $('tetris-status').textContent='ДОШЁЛ ДО x'+mult+' → +'+fmt(win)+' ₽';
          if (mult >= 3) maybeGiveNft(mult);
          setTimeout(initTetris, 3000);
        });
      }
    }, 600);
  });
}

// ============ ИНВЕНТАРЬ ============
function renderInv(){
  var c = $('inv-list'); c.innerHTML='';
  if (!inventory || inventory.length === 0){
    c.innerHTML = '<div style="grid-column:1/-1;text-align:center;opacity:.5;padding:40px;">ПУСТО</div>';
    return;
  }
  for (var i=0;i<inventory.length;i++){
    var g = GIFTS[inventory[i]]; if (!g) continue;
    var d = document.createElement('div');
    d.style.cssText='background:linear-gradient(160deg,#12122a,#0a0a1a);border:1px solid #2a2a4a;border-radius:14px;padding:14px;text-align:center';
    d.innerHTML = '<div style="font-size:52px">'+g.emoji+'</div><div style="font-size:12px;font-weight:700">'+g.name+'</div><div style="font-size:11px;color:#4aff8a">'+fmt(g.price)+' ₽</div>';
    c.appendChild(d);
  }
}

window.addEventListener('load', function(){ loadBalance(); });
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
        return web.json_response({"balance": u["balance"], "inventory": u.get("inventory", [])})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def handle_post_balance(request):
    try:
        data = await request.json()
        user_id = int(data.get("user_id", 0))
        delta = int(data.get("delta", 0))
        new = update_balance(user_id, delta)
        u = get_user(user_id)
        return web.json_response({"balance": new, "inventory": u.get("inventory", [])})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def handle_nft(request):
    try:
        data = await request.json()
        user_id = int(data.get("user_id", 0))
        gift_id = str(data.get("gift_id", ""))
        u = get_user(user_id)
        if gift_id in GIFTS:
            u.setdefault("inventory", []).append(gift_id)
            save_user(user_id, u)
        return web.json_response({"inventory": u.get("inventory", [])})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

app = web.Application()
app.router.add_get("/", handle_index)
app.router.add_get("/api/balance", handle_get_balance)
app.router.add_post("/api/balance", handle_post_balance)
app.router.add_post("/api/nft", handle_nft)

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
