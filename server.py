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
    "1": {"name": "АЛМАЗ", "price": 5000, "emoji": "💎"},
    "2": {"name": "КОРОНА", "price": 15000, "emoji": "👑"},
    "3": {"name": "ЧЕРЕП", "price": 3000, "emoji": "💀"},
    "4": {"name": "ЗВЕЗДА", "price": 25000, "emoji": "⭐"},
    "5": {"name": "РАКЕТА", "price": 50000, "emoji": "🚀"},
    "6": {"name": "ПЛАНЕТА", "price": 100000, "emoji": "🪐"},
    "7": {"name": "ОГОНЬ", "price": 8000, "emoji": "🔥"},
    "8": {"name": "ЛУНА", "price": 12000, "emoji": "🌙"},
    "9": {"name": "МОЛНИЯ", "price": 20000, "emoji": "⚡"},
    "10": {"name": "КОМЕТА", "price": 35000, "emoji": "☄️"},
    "11": {"name": "ДЖОКЕР", "price": 60000, "emoji": "🃏"},
    "12": {"name": "ФЕНИКС", "price": 80000, "emoji": "🦅"}
}

HTML_PAGE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>🎰 VEGAS CASINO</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent;font-family:-apple-system,sans-serif}
body{background:radial-gradient(circle at 50% 0%,#1a0a2a,#05050f 70%);color:#e8e8f0;min-height:100vh;padding:14px}
.balance{background:linear-gradient(135deg,#2a1a0a,#3a2a1a);border:2px solid #d4af37;padding:16px;border-radius:14px;text-align:center;margin-bottom:14px;position:relative;overflow:hidden}
.balance::before{content:'';position:absolute;inset:0;background:linear-gradient(45deg,transparent 40%,rgba(212,175,55,.15) 50%,transparent 60%);animation:shine 3s infinite}
@keyframes shine{0%{transform:translateX(-100%)}100%{transform:translateX(100%)}}
.balance h1{font-size:11px;opacity:.7;letter-spacing:3px;color:#d4af37;position:relative}
.balance .amount{font-size:30px;font-weight:900;color:#ffdd44;text-shadow:0 0 20px #d4af37;position:relative}
.games{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.game{background:linear-gradient(160deg,#1a0a2a,#0a0515);border-radius:14px;padding:16px 10px;text-align:center;cursor:pointer;border:2px solid #2a1a4a;position:relative;overflow:hidden}
.game:active{transform:scale(.95);border-color:#d4af37;box-shadow:0 0 20px rgba(212,175,55,.5)}
.game .name{font-size:12px;font-weight:800;letter-spacing:1px;color:#fff}
.game .desc{font-size:9px;opacity:.5;margin-top:3px}
.screen{display:none}.screen.active{display:block}
.back{background:#1a0a2a;border:1px solid #d4af37;color:#ffdd44;padding:10px 16px;border-radius:10px;font-size:13px;margin-bottom:14px;cursor:pointer;font-weight:700}
h2{font-size:20px;margin-bottom:16px;text-align:center;font-weight:900;letter-spacing:3px;color:#ffdd44;text-shadow:0 0 20px #d4af37}
.bet-buttons{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:14px}
.bet-btn{background:linear-gradient(135deg,#1a0a2a,#2a1a4a);border:1px solid #4a3aff;color:#fff;padding:14px;border-radius:10px;font-size:15px;font-weight:800;cursor:pointer}
.bet-btn:active{background:#4a3aff;box-shadow:0 0 15px #4a3aff}
.big-btn{background:linear-gradient(135deg,#d4af37,#ffdd44);border:none;color:#1a0a2a;padding:16px;border-radius:12px;font-size:15px;font-weight:900;width:100%;margin-top:12px;cursor:pointer;letter-spacing:1px}
.big-btn:active{transform:scale(.98)}
.green-btn{background:linear-gradient(135deg,#4aff8a,#2acc6a)!important;color:#000!important}
.status{text-align:center;font-size:14px;min-height:24px;margin-bottom:8px;font-weight:700;color:#ffdd44}
.card{background:#fff;border-radius:8px;color:#000;font-weight:900;display:inline-flex;flex-direction:column;align-items:center;justify-content:center;border:2px solid #333;box-shadow:0 4px 8px rgba(0,0,0,.5)}
.card.red{color:#cc2244}
.card-big{width:60px;height:88px;font-size:22px;margin:4px}
.card-small{width:44px;height:64px;font-size:16px;margin:3px}
.cards-row{display:flex;flex-wrap:wrap;justify-content:center;min-height:96px;margin:14px 0}
.emoji-big{font-size:110px;text-align:center;margin:20px 0;min-height:130px;line-height:130px}
.grid-3{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-top:10px}
.grid-4{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-top:10px}
.grid-6{display:grid;grid-template-columns:repeat(6,1fr);gap:5px;margin-top:10px}
.roulette-wrap{position:relative;width:290px;height:290px;margin:20px auto}
.roulette{width:100%;height:100%;border-radius:50%;border:10px solid #d4af37;position:relative;transition:transform 5s cubic-bezier(.15,.85,.25,1);overflow:hidden;box-shadow:0 0 30px rgba(212,175,55,.5)}
.roulette-num{position:absolute;font-size:9px;font-weight:900;color:#fff}
.pointer{position:absolute;top:-16px;left:50%;transform:translateX(-50%);width:0;height:0;border-left:14px solid transparent;border-right:14px solid transparent;border-top:26px solid #ffdd44;z-index:10;filter:drop-shadow(0 0 8px #d4af37)}
.roulette-center{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:56px;height:56px;background:radial-gradient(circle,#d4af37,#8a6a1a);border-radius:50%;border:3px solid #ffdd44;z-index:5;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:900;color:#1a0a2a}
.slot-row{display:flex;justify-content:center;gap:10px;margin:30px 0}
.slot-cell{width:80px;height:110px;background:linear-gradient(180deg,#1a1a2e,#0a0a15);border:3px solid #d4af37;border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:48px;box-shadow:inset 0 0 20px rgba(212,175,55,.3)}
.slot-cell.spin{animation:sp .08s infinite}
@keyframes sp{0%,100%{transform:translateY(-10px)}50%{transform:translateY(10px)}}
.mines-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:6px;margin-top:12px}
.mine-cell{aspect-ratio:1;background:linear-gradient(160deg,#1a0a2a,#0a0515);border:1px solid #2a1a4a;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:22px;cursor:pointer}
.mine-cell.opened{background:linear-gradient(160deg,#2a1a4a,#1a0a2a)}
.mine-cell.mine{background:#3a0a0a;border-color:#ff3a5a;box-shadow:0 0 15px #ff3a5a}
.plinko-stage{position:relative;height:400px;background:radial-gradient(circle at 50% 0%,#1a0a2a,#05050f);border-radius:14px;overflow:hidden;border:2px solid #d4af37;margin-top:10px}
.peg{position:absolute;width:8px;height:8px;background:#d4af37;border-radius:50%;box-shadow:0 0 6px #d4af37}
.ball{position:absolute;width:18px;height:18px;background:radial-gradient(circle at 30% 30%,#ffdd44,#d4af37);border-radius:50%;box-shadow:0 0 20px #ffdd44;z-index:5}
.plinko-bottom{position:absolute;bottom:0;width:100%;display:flex}
.plinko-slot{flex:1;text-align:center;font-size:10px;padding:8px 0;color:#1a0a2a;font-weight:900}
.crash-stage{position:relative;height:250px;background:#0a0515;border-radius:14px;overflow:hidden;border:2px solid #d4af37;margin-top:10px}
.crash-graph{position:absolute;bottom:0;left:0;right:0;top:0}
.crash-line{position:absolute;bottom:0;left:0;height:100%;width:0;background:linear-gradient(90deg,#4aff8a,#ffdd44,#ff3a5a);clip-path:polygon(0 100%,100% 0,100% 100%);transition:width .1s linear}
.crash-mult{position:absolute;top:20px;left:50%;transform:translateX(-50%);font-size:52px;font-weight:900;color:#4aff8a;text-shadow:0 0 30px #4aff8a;z-index:10}
.crash-mult.crashed{color:#ff3a5a;text-shadow:0 0 30px #ff3a5a}
.wheel-wrap{position:relative;width:300px;height:300px;margin:20px auto}
.fortune-wheel{width:100%;height:100%;border-radius:50%;border:12px solid #d4af37;position:relative;overflow:hidden;box-shadow:0 0 30px rgba(212,175,55,.5)}
.wheel-seg{position:absolute;top:50%;left:50%;width:50%;height:50%;transform-origin:0% 0%;display:flex;align-items:flex-start;justify-content:center;padding-top:8px;font-size:14px;font-weight:900;color:#fff}
.wheel-pointer{position:absolute;top:-18px;left:50%;transform:translateX(-50%);width:0;height:0;border-left:16px solid transparent;border-right:16px solid transparent;border-top:28px solid #ffdd44;z-index:20;filter:drop-shadow(0 0 10px #d4af37)}
.keno-grid{display:grid;grid-template-columns:repeat(8,1fr);gap:4px;margin-top:14px}
.keno-cell{aspect-ratio:1;background:linear-gradient(160deg,#1a0a2a,#0a0515);border:1px solid #2a1a4a;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;cursor:pointer}
.keno-cell.picked{background:#4a3aff;color:#fff;border-color:#6a4aff}
.keno-cell.hit{background:#4aff8a;color:#000;box-shadow:0 0 10px #4aff8a}
.poker-hand{display:flex;justify-content:center;margin:14px 0;flex-wrap:wrap}
.case-strip{display:flex;gap:6px;overflow:hidden;padding:14px 0;margin:20px 0;border-top:2px solid #d4af37;border-bottom:2px solid #d4af37}
.case-item{width:70px;height:90px;background:linear-gradient(160deg,#1a0a2a,#0a0515);border:2px solid #2a1a4a;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:36px;flex-shrink:0;transition:transform .3s}
.case-item.win{border-color:#ffdd44;box-shadow:0 0 25px #ffdd44;transform:scale(1.15)}
.goal{position:relative;width:100%;height:180px;background:linear-gradient(180deg,#0a3a0a,#051a05);border:4px solid #fff;border-radius:8px;margin-top:14px;overflow:hidden}
.goal-net{position:absolute;inset:0;background-image:repeating-linear-gradient(0deg,transparent 0,transparent 18px,rgba(255,255,255,.15) 18px,rgba(255,255,255,.15) 20px),repeating-linear-gradient(90deg,transparent 0,transparent 18px,rgba(255,255,255,.15) 18px,rgba(255,255,255,.15) 20px)}
.keeper{position:absolute;bottom:0;font-size:60px;transition:left .4s;line-height:1;z-index:3}
.ball-pen{position:absolute;bottom:20px;font-size:36px;transition:all .6s;z-index:2}
.race-track{position:relative;width:100%;height:220px;background:linear-gradient(180deg,#1a3a1a,#0a1a0a);border-radius:8px;margin-top:14px;overflow:hidden;border:2px solid #d4af37}
.race-lane{position:absolute;left:0;right:0;height:50px;border-bottom:2px dashed rgba(255,255,255,.3);display:flex;align-items:center;padding-left:6px;cursor:pointer}
.race-lane.selected{background:rgba(212,175,55,.2)}
.horse{font-size:32px;transition:transform .1s}
.blackjack-table{background:radial-gradient(ellipse at center,#0a5a2a,#052a15);border:4px solid #d4af37;border-radius:14px;padding:14px;margin-top:14px}
.dice-table{display:flex;gap:8px;justify-content:center;margin:20px 0;flex-wrap:wrap}
.die{width:70px;height:70px;background:#fff;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:40px;font-weight:900;color:#1a0a2a;border:2px solid #333;box-shadow:0 4px 8px rgba(0,0,0,.5)}
.die.rolled{animation:roll .3s}
@keyframes roll{0%{transform:rotate(0)}50%{transform:rotate(180deg) scale(1.2)}100%{transform:rotate(360deg)}}
</style>
</head>
<body>

<div id="menu" class="screen active">
  <div class="balance"><h1>💰 БАЛАНС</h1><div class="amount"><span id="balance">100.00</span> ₽</div></div>
  <div class="games">
    <div class="game" id="btn-slots"><div class="name">🎰 СЛОТЫ</div><div class="desc">777</div></div>
    <div class="game" id="btn-roulette"><div class="name">🎡 РУЛЕТКА</div><div class="desc">36+0</div></div>
    <div class="game" id="btn-blackjack"><div class="name">🃏 БЛЭКДЖЕК</div><div class="desc">21</div></div>
    <div class="game" id="btn-poker"><div class="name">♠️ ПОКЕР</div><div class="desc">ТЕХАС ХОЛДЕМ</div></div>
    <div class="game" id="btn-baccarat"><div class="name">🎴 БАККАРА</div><div class="desc">9</div></div>
    <div class="game" id="btn-dice"><div class="name">🎲 КРАПС</div><div class="desc">КОСТИ</div></div>
    <div class="game" id="btn-crash"><div class="name">📈 КРАШ</div><div class="desc">УСПЕЙ</div></div>
    <div class="game" id="btn-mines"><div class="name">💣 МИНЫ</div><div class="desc">5x5</div></div>
    <div class="game" id="btn-plinko"><div class="name">🎯 ПЛИНКО</div><div class="desc">ШАРИК</div></div>
    <div class="game" id="btn-fortune"><div class="name">🎡 КОЛЕСО</div><div class="desc">ФОРТУНЫ</div></div>
    <div class="game" id="btn-keno"><div class="name">🎯 КЕНО</div><div class="desc">5/40</div></div>
    <div class="game" id="btn-case"><div class="name">📦 КЕЙСЫ</div><div class="desc">КРУТИ</div></div>
    <div class="game" id="btn-penalty"><div class="name">⚽ ПЕНАЛЬТИ</div><div class="desc">ГОЛ</div></div>
    <div class="game" id="btn-race"><div class="name">🐎 СКАЧКИ</div><div class="desc">ЗАЕЗД</div></div>
    <div class="game" id="btn-hilo"><div class="name">🃏 ХАЙ-ЛОУ</div><div class="desc">БОЛЬШЕ/МЕНЬШЕ</div></div>
    <div class="game" id="btn-lucky"><div class="name">🍀 УДАЧА</div><div class="desc">СЧАСТЛИВОЕ ЧИСЛО</div></div>
    <div class="game" id="btn-inv"><div class="name">🎁 ИНВЕНТАРЬ</div><div class="desc">ТВОИ NFT</div></div>
  </div>
</div>

<!-- СЛОТЫ -->
<div id="slots" class="screen">
  <button class="back" id="back-slots">← НАЗАД</button>
  <h2>🎰 СЛОТЫ</h2>
  <div class="slot-row">
    <div class="slot-cell" id="s0">🍒</div>
    <div class="slot-cell" id="s1">🍒</div>
    <div class="slot-cell" id="s2">🍒</div>
  </div>
  <div class="slot-row" style="margin-top:-20px;">
    <div class="slot-cell" id="s3">🍒</div>
    <div class="slot-cell" id="s4">🍒</div>
    <div class="slot-cell" id="s5">🍒</div>
  </div>
  <div class="status" id="slots-status">ВЫБЕРИ СТАВКУ</div>
  <div class="bet-buttons" id="slots-buttons"></div>
</div>

<!-- РУЛЕТКА -->
<div id="roulette" class="screen">
  <button class="back" id="back-roulette">← НАЗАД</button>
  <h2>🎡 РУЛЕТКА</h2>
  <div class="roulette-wrap">
    <div class="pointer"></div>
    <div class="roulette" id="roulette-el"></div>
    <div class="roulette-center">SPIN</div>
  </div>
  <div class="status" id="roulette-status">ВЫБЕРИ СТАВКУ</div>
  <div class="bet-buttons" id="roulette-buttons"></div>
  <div class="grid-3" style="margin-top:10px;">
    <button class="bet-btn" data-rl="red" style="background:#8a1a2a;">КРАСНОЕ x2</button>
    <button class="bet-btn" data-rl="black" style="background:#1a1a1a;">ЧЁРНОЕ x2</button>
    <button class="bet-btn" data-rl="green" style="background:#0a5a2a;">ЗЕРО x35</button>
  </div>
</div>

<!-- БЛЭКДЖЕК -->
<div id="blackjack" class="screen">
  <button class="back" id="back-blackjack">← НАЗАД</button>
  <h2>🃏 БЛЭКДЖЕК</h2>
  <div class="blackjack-table">
    <div style="text-align:center;font-size:13px;font-weight:900;color:#ffdd44;">ДИЛЕР: <span id="bj-dscore">0</span></div>
    <div class="cards-row" id="bj-dealer"></div>
    <div style="text-align:center;font-size:13px;font-weight:900;color:#ffdd44;">ТЫ: <span id="bj-pscore">0</span></div>
    <div class="cards-row" id="bj-player"></div>
  </div>
  <div class="status" id="bj-status">ВЫБЕРИ СТАВКУ</div>
  <div class="bet-buttons" id="bj-buttons"></div>
  <div id="bj-actions" style="display:none;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:12px;">
    <button class="big-btn" id="bj-hit">ЕЩЁ</button>
    <button class="big-btn" id="bj-stand" style="background:linear-gradient(135deg,#ff3a5a,#cc2244);color:#fff;">СТОП</button>
    <button class="big-btn" id="bj-double" style="background:linear-gradient(135deg,#4aff8a,#2acc6a);color:#000;">X2</button>
  </div>
</div>

<!-- ПОКЕР -->
<div id="poker" class="screen">
  <button class="back" id="back-poker">← НАЗАД</button>
  <h2>♠️ ПОКЕР</h2>
  <div class="status" id="poker-status">ВЫБЕРИ СТАВКУ</div>
  <div class="bet-buttons" id="poker-buttons"></div>
  <div style="text-align:center;font-size:12px;color:#ffdd44;font-weight:900;margin-top:14px;">ТВОИ КАРТЫ</div>
  <div class="poker-hand" id="poker-my"></div>
  <div style="text-align:center;font-size:12px;color:#ffdd44;font-weight:900;">СТОЛ</div>
  <div class="poker-hand" id="poker-table"></div>
  <div id="poker-actions" style="display:none;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px;">
    <button class="big-btn" id="poker-call" style="background:linear-gradient(135deg,#4a3aff,#6a4aff);">УРАВНЯТЬ</button>
    <button class="big-btn" id="poker-fold" style="background:linear-gradient(135deg,#ff3a5a,#cc2244);color:#fff;">СБРОС</button>
  </div>
</div>

<!-- БАККАРА -->
<div id="baccarat" class="screen">
  <button class="back" id="back-baccarat">← НАЗАД</button>
  <h2>🎴 БАККАРА</h2>
  <div class="blackjack-table">
    <div style="text-align:center;font-size:13px;font-weight:900;color:#ffdd44;">ИГРОК: <span id="bac-pscore">0</span></div>
    <div class="cards-row" id="bac-player"></div>
    <div style="text-align:center;font-size:13px;font-weight:900;color:#ffdd44;">БАНКИР: <span id="bac-bscore">0</span></div>
    <div class="cards-row" id="bac-banker"></div>
  </div>
  <div class="status" id="bac-status">ВЫБЕРИ СТАВКУ</div>
  <div class="bet-buttons" id="bac-buttons"></div>
  <div class="grid-3" style="margin-top:10px;">
    <button class="bet-btn" data-bac="P">ИГРОК x2</button>
    <button class="bet-btn" data-bac="B">БАНКИР x1.95</button>
    <button class="bet-btn" data-bac="T">НИЧЬЯ x8</button>
  </div>
</div>

<!-- КРАПС -->
<div id="craps" class="screen">
  <button class="back" id="back-craps">← НАЗАД</button>
  <h2>🎲 КРАПС</h2>
  <div class="dice-table" id="dice-table">
    <div class="die" id="die1">⚀</div>
    <div class="die" id="die2">⚀</div>
  </div>
  <div class="status" id="craps-status">ВЫБЕРИ СТАВКУ</div>
  <div class="bet-buttons" id="craps-buttons"></div>
</div>

<!-- КРАШ -->
<div id="crash" class="screen">
  <button class="back" id="back-crash">← НАЗАД</button>
  <h2>📈 КРАШ</h2>
  <div class="crash-stage">
    <div class="crash-graph"><div class="crash-line" id="crash-line"></div></div>
    <div class="crash-mult" id="crash-mult">x1.00</div>
  </div>
  <div class="status" id="crash-status">ВЫБЕРИ СТАВКУ</div>
  <div class="bet-buttons" id="crash-buttons"></div>
  <button class="big-btn green-btn" id="crash-cashout" style="display:none;">ЗАБРАТЬ</button>
</div>

<!-- МИНЫ -->
<div id="mines" class="screen">
  <button class="back" id="back-mines">← НАЗАД</button>
  <h2>💣 МИНЫ</h2>
  <div class="status" id="mines-status">ВЫБЕРИ СТАВКУ</div>
  <div class="bet-buttons" id="mines-buttons"></div>
  <div class="mines-grid" id="mines-grid"></div>
  <button class="big-btn green-btn" id="mines-cashout" style="display:none;">ЗАБРАТЬ</button>
</div>

<!-- ПЛИНКО -->
<div id="plinko" class="screen">
  <button class="back" id="back-plinko">← НАЗАД</button>
  <h2>🎯 ПЛИНКО</h2>
  <div class="plinko-stage" id="plinko-stage"><div class="plinko-bottom" id="plinko-bottom"></div></div>
  <div class="status" id="plinko-status">ВЫБЕРИ СТАВКУ</div>
  <div class="bet-buttons" id="plinko-buttons"></div>
</div>

<!-- КОЛЕСО ФОРТУНЫ -->
<div id="fortune" class="screen">
  <button class="back" id="back-fortune">← НАЗАД</button>
  <h2>🎡 КОЛЕСО ФОРТУНЫ</h2>
  <div class="wheel-wrap">
    <div class="wheel-pointer"></div>
    <div class="fortune-wheel" id="fortune-wheel"></div>
  </div>
  <div class="status" id="fortune-status">ВЫБЕРИ СТАВКУ</div>
  <div class="bet-buttons" id="fortune-buttons"></div>
</div>

<!-- КЕНО -->
<div id="keno" class="screen">
  <button class="back" id="back-keno">← НАЗАД</button>
  <h2>🎯 КЕНО</h2>
  <div class="status" id="keno-status">ВЫБЕРИ 5 ЧИСЕЛ</div>
  <div class="bet-buttons" id="keno-buttons"></div>
  <div class="keno-grid" id="keno-grid"></div>
</div>

<!-- КЕЙСЫ -->
<div id="case" class="screen">
  <button class="back" id="back-case">← НАЗАД</button>
  <h2>📦 КЕЙСЫ</h2>
  <div class="status" id="case-status">ВЫБЕРИ СТАВКУ</div>
  <div class="bet-buttons" id="case-buttons"></div>
  <div class="case-strip" id="case-strip"></div>
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

<!-- СКАЧКИ -->
<div id="race" class="screen">
  <button class="back" id="back-race">← НАЗАД</button>
  <h2>🐎 СКАЧКИ</h2>
  <div class="status" id="race-status">ВЫБЕРИ ЛОШАДЬ</div>
  <div class="bet-buttons" id="race-buttons"></div>
  <div class="race-track" id="race-track"></div>
</div>

<!-- ХАЙ-ЛОУ -->
<div id="hilo" class="screen">
  <button class="back" id="back-hilo">← НАЗАД</button>
  <h2>🃏 ХАЙ-ЛОУ</h2>
  <div class="status" id="hilo-status">ВЫБЕРИ СТАВКУ</div>
  <div class="bet-buttons" id="hilo-buttons"></div>
  <div class="cards-row" id="hilo-cards"></div>
  <div id="hilo-actions" style="display:none;grid-template-columns:1fr 1fr;gap:8px;">
    <button class="big-btn" data-hilo="higher">БОЛЬШЕ ↑</button>
    <button class="big-btn" data-hilo="lower">МЕНЬШЕ ↓</button>
  </div>
</div>

<!-- УДАЧА -->
<div id="lucky" class="screen">
  <button class="back" id="back-lucky">← НАЗАД</button>
  <h2>🍀 СЧАСТЛИВОЕ ЧИСЛО</h2>
  <div class="emoji-big" id="lucky-display">🍀</div>
  <div class="status" id="lucky-status">ВЫБЕРИ ЧИСЛО 1-10</div>
  <div class="grid-6" style="grid-template-columns:repeat(5,1fr);">
    <button class="bet-btn" data-lucky="1">1</button>
    <button class="bet-btn" data-lucky="2">2</button>
    <button class="bet-btn" data-lucky="3">3</button>
    <button class="bet-btn" data-lucky="4">4</button>
    <button class="bet-btn" data-lucky="5">5</button>
    <button class="bet-btn" data-lucky="6">6</button>
    <button class="bet-btn" data-lucky="7">7</button>
    <button class="bet-btn" data-lucky="8">8</button>
    <button class="bet-btn" data-lucky="9">9</button>
    <button class="bet-btn" data-lucky="10">10</button>
  </div>
  <div class="bet-buttons" id="lucky-buttons"></div>
</div>

<!-- ИНВЕНТАРЬ -->
<div id="inv" class="screen">
  <button class="back" id="back-inv">← НАЗАД</button>
  <h2>🎁 ИНВЕНТАРЬ</h2>
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
  if (Math.random() < 0.15 && mult >= 3) {
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
  'btn-slots':'slots','btn-roulette':'roulette','btn-blackjack':'blackjack','btn-poker':'poker',
  'btn-baccarat':'baccarat','btn-dice':'craps','btn-crash':'crash','btn-mines':'mines',
  'btn-plinko':'plinko','btn-fortune':'fortune','btn-keno':'keno','btn-case':'case',
  'btn-penalty':'penalty','btn-race':'race','btn-hilo':'hilo','btn-lucky':'lucky','btn-inv':'inv'
};
for (var k in menuMap){(function(sid){
  var b = $(k); if (b) b.addEventListener('click', function(){ showScreen(sid); initGame(sid); });
})(menuMap[k]);}
['slots','roulette','blackjack','poker','baccarat','craps','crash','mines','plinko','fortune','keno','case','penalty','race','hilo','lucky','inv'].forEach(function(id){
  var b = $('back-'+id); if (b) b.addEventListener('click', goMenu);
});

function initGame(id){
  if (id==='slots') initSlots();
  if (id==='roulette') initRoulette();
  if (id==='blackjack') initBJ();
  if (id==='poker') initPoker();
  if (id==='baccarat') initBaccarat();
  if (id==='craps') initCraps();
  if (id==='crash') initCrash();
  if (id==='mines') initMines();
  if (id==='plinko') initPlinko();
  if (id==='fortune') initFortune();
  if (id==='keno') initKeno();
  if (id==='case') initCase();
  if (id==='penalty') initPenalty();
  if (id==='race') initRace();
  if (id==='hilo') initHilo();
  if (id==='lucky') initLucky();
  if (id==='inv') renderInv();
}

// ============ СЛОТЫ 3x2 ============
var slotsBusy = false;
function initSlots(){
  slotsBusy = false;
  $('slots-status').textContent = 'ВЫБЕРИ СТАВКУ';
  for (var i=0;i<6;i++) $('s'+i).textContent = '🍒';
  makeBetButtons('slots-buttons', playSlots);
}
function playSlots(bet){
  if (slotsBusy) return;
  if (bet > balance){ showAlert('Недостаточно'); return; }
  slotsBusy = true;
  changeBalance(-bet).then(function(){
    var syms = ['🍒','🍋','🍊','💎','7️⃣','⭐','🔔'];
    $('slots-buttons').innerHTML='';
    $('slots-status').textContent='КРУТИМ...';
    for (var i=0;i<6;i++) $('s'+i).classList.add('spin');
    var final = [];
    for (var i=0;i<6;i++) final.push(syms[Math.floor(Math.random()*syms.length)]);
    var finish = 0;
    for (var i=0;i<6;i++){(function(idx){
      setTimeout(function(){
        $('s'+idx).classList.remove('spin');
        $('s'+idx).textContent = final[idx];
        finish++;
        if (finish === 6){
          var mult = 0;
          // Проверяем линии: верх (0,1,2) и низ (3,4,5)
          for (var row=0;row<2;row++){
            var a=final[row*3], b=final[row*3+1], c=final[row*3+2];
            if (a===b && b===c){
              var m = a==='7️⃣' ? 20 : (a==='💎' ? 10 : (a==='⭐' ? 8 : (a==='🔔' ? 5 : 3)));
              if (m > mult) mult = m;
            }
            if (a===b || b===c || a===c){
              if (2 > mult) mult = 2;
            }
          }
          var win = Math.floor(bet * mult);
          var done = function(){
            $('slots-status').textContent = mult ? ('🎉 ВЫИГРЫШ +'+fmt(win)+' ₽ (x'+mult+')') : 'НЕ ПОВЕЗЛО';
            if (mult >= 3) maybeGiveNft(mult);
            slotsBusy = false;
            setTimeout(initSlots, 2500);
          };
          if (win > 0) changeBalance(win).then(done); else done();
        }
      }, 700 + idx*180);
    })(i);}
  });
}

// ============ РУЛЕТКА ============
var rouletteBet=0, rouletteColor='';
function initRoulette(){
  rouletteBet=0; rouletteColor='';
  var wheel = $('roulette-el');
  wheel.style.transition='none'; wheel.style.transform='rotate(0deg)';
  setTimeout(function(){ wheel.style.transition='transform 5s cubic-bezier(.15,.85,.25,1)'; }, 50);
  wheel.innerHTML='';
  var reds = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36];
  for (var i=0;i<37;i++){
    var seg = document.createElement('div');
    var color = i===0?'#0a5a2a':(reds.indexOf(i)>=0?'#8a1a2a':'#0a0a0a');
    seg.style.cssText = 'position:absolute;width:50%;height:50%;top:0;left:50%;transform-origin:0% 100%;transform:rotate('+(i*(360/37))+'deg);background:'+color+';clip-path:polygon(0 0,100% 0,0 100%);';
    wheel.appendChild(seg);
    var num = document.createElement('div'); num.className='roulette-num'; num.textContent=i;
    num.style.cssText = 'position:absolute;top:16px;left:50%;transform:translateX(-50%) rotate('+(i*(360/37)+(360/74))+'deg);';
    seg.appendChild(num);
  }
  $('roulette-status').textContent = 'ВЫБЕРИ СТАВКУ';
  makeBetButtons('roulette-buttons', playRoulette);
}
var rlBtns = document.querySelectorAll('[data-rl]');
for (var i=0;i<rlBtns.length;i++){(function(b){
  b.addEventListener('click', function(){
    rouletteColor = b.getAttribute('data-rl');
    $('roulette-status').textContent = 'ЦВЕТ: '+rouletteColor+' | ВЫБЕРИ СТАВКУ';
  });
})(rlBtns[i]);}
function playRoulette(bet){
  if (!rouletteColor){ showAlert('Выбери цвет'); return; }
  if (bet > balance){ showAlert('Недостаточно'); return; }
  changeBalance(-bet).then(function(){
    $('roulette-buttons').innerHTML='';
    $('roulette-status').textContent='КРУТИМ...';
    var idx = Math.floor(Math.random()*37);
    var wheel = $('roulette-el');
    wheel.style.transform = 'rotate('+(360*8 + (360 - idx*(360/37)))+'deg)';
    setTimeout(function(){
      var reds = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36];
      var resultColor = idx===0?'green':(reds.indexOf(idx)>=0?'red':'black');
      var mult = 0;
      if (rouletteColor === resultColor){
        mult = resultColor === 'green' ? 35 : 2;
      }
      var win = Math.floor(bet*mult);
      var done = function(){
        $('roulette-status').textContent = 'ВЫПАЛО '+idx+' ('+resultColor+') '+(win ? '+'+fmt(win)+' ₽' : 'МИМО');
        if (mult >= 5) maybeGiveNft(mult);
        setTimeout(initRoulette, 3000);
      };
      if (win > 0) changeBalance(win).then(done); else done();
    }, 5200);
  });
}

// ============ БЛЭКДЖЕК ============
var bjBet=0, bjActive=false, bjP=[], bjD=[], bjDoubled=false;
function newCard(){
  var v = ['A','2','3','4','5','6','7','8','9','10','J','Q','K'];
  var s = ['♠','♥','♦','♣'];
  var vv = v[Math.floor(Math.random()*v.length)];
  var ss = s[Math.floor(Math.random()*s.length)];
  return { v: vv, s: ss, red: (ss==='♥'||ss==='♦') };
}
function cardVal(c){ if (c.v==='A') return 11; if (['K','Q','J'].indexOf(c.v)>=0) return 10; return parseInt(c.v); }
function bjSum(arr){
  var sum=0, aces=0;
  for (var i=0;i<arr.length;i++){ sum+=cardVal(arr[i]); if (arr[i].v==='A') aces++; }
  while (sum>21 && aces>0){ sum-=10; aces--; }
  return sum;
}
function renderHand(id, cards, hide){
  var html = '';
  for (var i=0;i<cards.length;i++){
    if (hide && i===1){ html += '<div class="card card-big" style="background:linear-gradient(135deg,#1a0a2a,#d4af37);color:#ffdd44;">?</div>'; continue; }
    var c = cards[i];
    html += '<div class="card card-big'+(c.red?' red':'')+'">'+c.v+'<div style="font-size:20px;">'+c.s+'</div></div>';
  }
  $(id).innerHTML = html;
}
function initBJ(){
  bjBet=0; bjActive=false; bjP=[]; bjD=[]; bjDoubled=false;
  $('bj-dealer').innerHTML=''; $('bj-player').innerHTML='';
  $('bj-dscore').textContent='0'; $('bj-pscore').textContent='0';
  $('bj-status').textContent='ВЫБЕРИ СТАВКУ';
  $('bj-buttons').style.display='grid';
  $('bj-actions').style.display='none';
  makeBetButtons('bj-buttons', startBJ);
}
function startBJ(bet){
  if (bet > balance){ showAlert('Недостаточно'); return; }
  bjBet=bet; bjActive=true; bjDoubled=false;
  changeBalance(-bet).then(function(){
    bjP=[newCard(),newCard()];
    bjD=[newCard(),newCard()];
    renderHand('bj-player', bjP, false);
    renderHand('bj-dealer', bjD, true);
    $('bj-pscore').textContent = bjSum(bjP);
    $('bj-dscore').textContent = cardVal(bjD[0]);
    $('bj-buttons').style.display='none';
    $('bj-actions').style.display='grid';
    $('bj-status').textContent='ТВОЙ ХОД';
    if (bjSum(bjP) === 21){
      setTimeout(function(){ bjStand(); }, 500);
    }
  });
}
$('bj-hit').addEventListener('click', function(){
  if (!bjActive) return;
  bjP.push(newCard());
  renderHand('bj-player', bjP, false);
  $('bj-pscore').textContent = bjSum(bjP);
  if (bjSum(bjP) > 21){
    bjActive=false;
    $('bj-status').textContent='💥 ПЕРЕБОР -'+fmt(bjBet)+' ₽';
    $('bj-actions').style.display='none';
    setTimeout(initBJ, 3000);
  }
});
$('bj-stand').addEventListener('click', function(){ bjStand(); });
function bjStand(){
  if (!bjActive) return;
  bjActive=false;
  var d = bjSum(bjD), p = bjSum(bjP);
  while (d < 17){ bjD.push(newCard()); d = bjSum(bjD); }
  renderHand('bj-dealer', bjD, false);
  $('bj-dscore').textContent = d;
  var finalBet = bjDoubled ? bjBet*2 : bjBet;
  if (d > 21 || p > d){
    var win = Math.floor(finalBet * 2);
    changeBalance(win).then(function(){
      $('bj-status').textContent='🎉 ПОБЕДА +'+fmt(win)+' ₽';
      if (p === 21 && bjP.length === 2) maybeGiveNft(5);
      setTimeout(initBJ, 3000);
    });
  } else if (p === d){
    changeBalance(finalBet).then(function(){ $('bj-status').textContent='НИЧЬЯ'; setTimeout(initBJ,3000); });
  } else {
    $('bj-status').textContent='ПРОИГРАЛ -'+fmt(finalBet)+' ₽';
    setTimeout(initBJ, 3000);
  }
  $('bj-actions').style.display='none';
}
$('bj-double').addEventListener('click', function(){
  if (!bjActive || bjP.length !== 2) return;
  if (bjBet > balance){ showAlert('Недостаточно для удвоения'); return; }
  changeBalance(-bjBet).then(function(){
    bjDoubled = true;
    bjP.push(newCard());
    renderHand('bj-player', bjP, false);
    $('bj-pscore').textContent = bjSum(bjP);
    if (bjSum(bjP) > 21){
      bjActive=false;
      $('bj-status').textContent='💥 ПЕРЕБОР -'+fmt(bjBet*2)+' ₽';
      $('bj-actions').style.display='none';
      setTimeout(initBJ, 3000);
    } else {
      setTimeout(bjStand, 300);
    }
  });
});

// ============ ПОКЕР (упрощённый) ============
var pokerBet=0, pokerActive=false;
function drawCard(){
  var v = ['2','3','4','5','6','7','8','9','10','J','Q','K','A'];
  var s = ['♠','♥','♦','♣'];
  var vv = v[Math.floor(Math.random()*v.length)];
  var ss = s[Math.floor(Math.random()*s.length)];
  return { v: vv, s: ss, red: (ss==='♥'||ss==='♦') };
}
function renderPokerCard(c){
  return '<div class="card card-small'+(c.red?' red':'')+'">'+c.v+'<div style="font-size:14px;">'+c.s+'</div></div>';
}
function initPoker(){
  pokerBet=0; pokerActive=false;
  $('poker-status').textContent='ВЫБЕРИ СТАВКУ';
  $('poker-my').innerHTML=''; $('poker-table').innerHTML='';
  $('poker-actions').style.display='none';
  makeBetButtons('poker-buttons', startPoker);
}
function startPoker(bet){
  if (bet > balance){ showAlert('Недостаточно'); return; }
  pokerBet=bet; pokerActive=true;
  changeBalance(-bet).then(function(){
    var my = [drawCard(), drawCard()];
    var table = [drawCard(), drawCard(), drawCard()];
    $('poker-my').innerHTML = my.map(renderPokerCard).join('');
    $('poker-table').innerHTML = table.map(renderPokerCard).join('');
    $('poker-buttons').innerHTML='';
    $('poker-actions').style.display='grid';
    $('poker-status').textContent='УРАВНЯТЬ ИЛИ СБРОС?';
    // Шанс победы ~45%
    window._pokerWin = Math.random() < 0.45;
  });
}
$('poker-call').addEventListener('click', function(){
  if (!pokerActive) return;
  pokerActive=false;
  $('poker-actions').style.display='none';
  // Добираем 2 карты на стол
  var table = [drawCard(), drawCard()];
  $('poker-table').innerHTML += table.map(renderPokerCard).join('');
  if (window._pokerWin){
    var win = pokerBet*2;
    changeBalance(win).then(function(){
      $('poker-status').textContent='🎉 ПОБЕДА +'+fmt(win)+' ₽';
      maybeGiveNft(2);
      setTimeout(initPoker, 3000);
    });
  } else {
    $('poker-status').textContent='ПРОИГРАЛ -'+fmt(pokerBet)+' ₽';
    setTimeout(initPoker, 3000);
  }
});
$('poker-fold').addEventListener('click', function(){
  if (!pokerActive) return;
  pokerActive=false;
  var back = Math.floor(pokerBet * 0.5);
  changeBalance(back).then(function(){
    $('poker-status').textContent='СБРОС. Вернулось '+fmt(back)+' ₽';
    $('poker-actions').style.display='none';
    setTimeout(initPoker, 3000);
  });
});

// ============ БАККАРА ============
var bacBet=0, bacPick='';
function bacCard(){
  var v = [1,2,3,4,5,6,7,8,9,0,0,0,0];
  return v[Math.floor(Math.random()*v.length)];
}
function bacSum(arr){ return arr.reduce(function(a,b){return (a+b)%10;},0); }
function initBaccarat(){
  bacBet=0; bacPick='';
  $('bac-player').innerHTML=''; $('bac-banker').innerHTML='';
  $('bac-pscore').textContent='0'; $('bac-bscore').textContent='0';
  $('bac-status').textContent='ВЫБЕРИ СТАВКУ';
  makeBetButtons('bac-buttons', playBaccarat);
}
var bacBtns = document.querySelectorAll('[data-bac]');
for (var i=0;i<bacBtns.length;i++){(function(b){
  b.addEventListener('click', function(){
    bacPick = b.getAttribute('data-bac');
    $('bac-status').textContent = 'ВЫБРАНО: '+bacPick+' | ВЫБЕРИ СТАВКУ';
  });
})(bacBtns[i]);}
function playBaccarat(bet){
  if (!bacPick){ showAlert('Выбери ставку'); return; }
  if (bet > balance){ showAlert('Недостаточно'); return; }
  changeBalance(-bet).then(function(){
    $('bac-buttons').innerHTML='';
    $('bac-status').textContent='РАЗДАЧА...';
    var p = [bacCard(), bacCard()];
    var b = [bacCard(), bacCard()];
    var renderBac = function(id, cards){
      var html = '';
      for (var i=0;i<cards.length;i++) html += '<div class="card card-big">'+cards[i]+'</div>';
      $(id).innerHTML = html;
    };
    renderBac('bac-player', p);
    renderBac('bac-banker', b);
    $('bac-pscore').textContent = bacSum(p);
    $('bac-bscore').textContent = bacSum(b);
    setTimeout(function(){
      var ps = bacSum(p), bs = bacSum(b);
      // Правила добора
      if (ps <= 5) p.push(bacCard());
      if (bs <= 5) b.push(bacCard());
      renderBac('bac-player', p);
      renderBac('bac-banker', b);
      ps = bacSum(p); bs = bacSum(b);
      $('bac-pscore').textContent = ps;
      $('bac-bscore').textContent = bs;
      var winner = (ps > bs) ? 'P' : (bs > ps ? 'B' : 'T');
      var mult = 0;
      if (bacPick === winner){
        if (winner === 'P') mult = 2;
        else if (winner === 'B') mult = 1.95;
        else mult = 8;
      }
      var win = Math.floor(bet*mult);
      var done = function(){
        $('bac-status').textContent = 'ПОБЕДА: '+winner+' → '+(win ? '+'+fmt(win)+' ₽' : 'МИМО');
        if (mult >= 5) maybeGiveNft(mult);
        setTimeout(initBaccarat, 3000);
      };
      if (win > 0) changeBalance(win).then(done); else done();
    }, 800);
  });
}

// ============ КРАПС ============
function initCraps(){
  $('craps-status').textContent='ВЫБЕРИ СТАВКУ';
  $('die1').textContent='⚀'; $('die2').textContent='⚀';
  makeBetButtons('craps-buttons', playCraps);
}
function playCraps(bet){
  if (bet > balance){ showAlert('Недостаточно'); return; }
  changeBalance(-bet).then(function(){
    $('craps-buttons').innerHTML='';
    $('craps-status').textContent='БРОСАЕМ...';
    var faces = ['⚀','⚁','⚂','⚃','⚄','⚅'];
    var d1 = Math.floor(Math.random()*6)+1;
    var d2 = Math.floor(Math.random()*6)+1;
    var rollAnim = 0;
    var anim = setInterval(function(){
      $('die1').textContent = faces[Math.floor(Math.random()*6)];
      $('die2').textContent = faces[Math.floor(Math.random()*6)];
      rollAnim++;
      if (rollAnim > 10){
        clearInterval(anim);
        $('die1').textContent = faces[d1-1];
        $('die2').textContent = faces[d2-1];
        var total = d1+d2;
        var mult = 0;
        if (total === 7 || total === 11) mult = 2;
        else if (total === 2 || total === 3 || total === 12) mult = 0;
        else if (total === 4 || total === 10) mult = 1.5;
        else if (total === 5 || total === 9) mult = 1.2;
        else if (total === 6 || total === 8) mult = 1;
        var win = Math.floor(bet*mult);
        var done = function(){
          $('craps-status').textContent = 'СУММА '+total+' → '+(win ? '+'+fmt(win)+' ₽' : 'ПРОИГРАЛ');
          if (mult >= 2) maybeGiveNft(mult);
          setTimeout(initCraps, 3000);
        };
        if (win > 0) changeBalance(win).then(done); else done();
      }
    }, 80);
  });
}

// ============ КРАШ ============
var crashBet=0, crashRunning=false, crashMult=1, crashLoop=null, crashCrashPoint=0;
function initCrash(){
  if (crashLoop){ clearInterval(crashLoop); crashLoop=null; }
  crashBet=0; crashRunning=false; crashMult=1;
  $('crash-mult').textContent='x1.00';
  $('crash-mult').classList.remove('crashed');
  $('crash-line').style.width='0%';
  $('crash-status').textContent='ВЫБЕРИ СТАВКУ';
  $('crash-cashout').style.display='none';
  makeBetButtons('crash-buttons', startCrash);
}
function startCrash(bet){
  if (bet > balance){ showAlert('Недостаточно'); return; }
  crashBet=bet; crashMult=1; crashRunning=true;
  crashCrashPoint = 1 + Math.random()*Math.random()*20 + 0.3;
  changeBalance(-bet).then(function(){
    $('crash-buttons').innerHTML='';
    $('crash-cashout').style.display='block';
    $('crash-status').textContent='ЛЕТИМ!';
    crashLoop = setInterval(function(){
      crashMult = +(crashMult + 0.05 + Math.random()*0.1).toFixed(2);
      $('crash-mult').textContent = 'x'+crashMult.toFixed(2);
      var pct = Math.min(100, (crashMult / 20) * 100);
      $('crash-line').style.width = pct+'%';
      if (crashMult >= crashCrashPoint){
        crashRunning = false;
        clearInterval(crashLoop); crashLoop=null;
        $('crash-mult').classList.add('crashed');
        $('crash-status').textContent='💥 КРАХ НА x'+crashMult.toFixed(2)+'! -'+fmt(crashBet)+' ₽';
        $('crash-cashout').style.display='none';
        setTimeout(initCrash, 3000);
      }
    }, 80);
  });
}
$('crash-cashout').addEventListener('click', function(){
  if (!crashRunning) return;
  crashRunning=false;
  clearInterval(crashLoop); crashLoop=null;
  var win = Math.floor(crashBet * crashMult);
  changeBalance(win).then(function(){
    $('crash-status').textContent='💰 ЗАБРАЛ +'+fmt(win)+' ₽ (x'+crashMult.toFixed(2)+')';
    $('crash-cashout').style.display='none';
    if (crashMult >= 3) maybeGiveNft(crashMult);
    setTimeout(initCrash, 3000);
  });
});

// ============ МИНЫ ============
var minesBet=0, minesField=[], minesOpened=0, minesMult=1, minesActive=false;
function initMines(){
  minesBet=0; minesField=[]; minesOpened=0; minesMult=1; minesActive=false;
  $('mines-status').textContent='ВЫБЕРИ СТАВКУ';
  $('mines-grid').innerHTML='';
  $('mines-cashout').style.display='none';
  makeBetButtons('mines-buttons', startMines);
}
function startMines(bet){
  if (bet > balance){ showAlert('Недостаточно'); return; }
  if (minesActive) return;
  minesBet=bet; minesOpened=0; minesMult=1; minesActive=true;
  changeBalance(-bet).then(function(){
    $('mines-buttons').innerHTML='';
    $('mines-cashout').style.display='block';
    minesField=[];
    for (var i=0;i<22;i++) minesField.push('gem');
    for (var i=0;i<3;i++) minesField.push('mine');
    for (var i=minesField.length-1;i>0;i--){
      var j = Math.floor(Math.random()*(i+1));
      var t = minesField[i]; minesField[i]=minesField[j]; minesField[j]=t;
    }
    var c = $('mines-grid'); c.innerHTML='';
    for (var i=0;i<25;i++){(function(idx){
      var cell = document.createElement('div'); cell.className='mine-cell';
      cell.addEventListener('click', function(){ openMine(idx, cell); });
      c.appendChild(cell);
    })(i);}
    $('mines-status').textContent = '3 МИНЫ | x'+minesMult.toFixed(2);
  });
}
function openMine(i, cell){
  if (!minesActive || cell.classList.contains('opened')) return;
  cell.classList.add('opened');
  if (minesField[i] === 'mine'){
    cell.classList.add('mine'); cell.textContent='💥';
    minesActive=false;
    $('mines-status').textContent='💣 БУМ! -'+fmt(minesBet)+' ₽';
    $('mines-cashout').style.display='none';
    var cells = document.querySelectorAll('#mines-grid .mine-cell');
    for (var k=0;k<minesField.length;k++) if (minesField[k]==='mine') cells[k].textContent='💣';
    setTimeout(initMines, 3000);
    return;
  }
  cell.textContent='💎';
  minesOpened++;
  minesMult = +(1 + minesOpened * 0.4).toFixed(2);
  $('mines-status').textContent='x'+minesMult.toFixed(2)+' | 💰 '+fmt(Math.floor(minesBet*minesMult))+' ₽';
}
$('mines-cashout').addEventListener('click', function(){
  if (!minesActive) return;
  minesActive=false;
  var win = Math.floor(minesBet * minesMult);
  changeBalance(win).then(function(){
    $('mines-cashout').style.display='none';
    $('mines-status').textContent='💰 ЗАБРАЛ +'+fmt(win)+' ₽ (x'+minesMult.toFixed(2)+')';
    if (minesMult >= 3) maybeGiveNft(minesMult);
    setTimeout(initMines, 3000);
  });
});

// ============ ПЛИНКО ============
var plinkoBusy=false;
function initPlinko(){
  plinkoBusy=false;
  var stage = $('plinko-stage');
  var olds = stage.querySelectorAll('.peg,.ball');
  for (var i=0;i<olds.length;i++) olds[i].remove();
  var rows=8;
  for (var r=0;r<rows;r++){
    var cnt = r+3;
    for (var i=0;i<cnt;i++){
      var peg = document.createElement('div'); peg.className='peg';
      peg.style.top = (30+r*38)+'px';
      peg.style.left = 'calc(50% + '+((i-(cnt-1)/2)*30)+'px)';
      stage.appendChild(peg);
    }
  }
  var mults = [0.2,0.5,1,2,5,10,25,10,5,2,1,0.5,0.2];
  var bottom = $('plinko-bottom'); bottom.innerHTML='';
  for (var i=0;i<mults.length;i++){
    var d = document.createElement('div'); d.className='plinko-slot';
    d.textContent = 'x'+mults[i];
    d.style.background = mults[i]>=5 ? '#ff3a5a' : (mults[i]>=2 ? '#ffaa00' : '#4a3aff');
    bottom.appendChild(d);
  }
  $('plinko-status').textContent='ВЫБЕРИ СТАВКУ';
  makeBetButtons('plinko-buttons', playPlinko);
}
function playPlinko(bet){
  if (plinkoBusy) return;
  if (bet > balance){ showAlert('Недостаточно'); return; }
  plinkoBusy=true;
  changeBalance(-bet).then(function(){
    $('plinko-buttons').innerHTML='';
    $('plinko-status').textContent='ШАРИК ПАДАЕТ...';
    var stage = $('plinko-stage');
    var ball = document.createElement('div'); ball.className='ball';
    ball.style.left='calc(50% - 9px)'; ball.style.top='10px';
    stage.appendChild(ball);
    var mults=[0.2,0.5,1,2,5,10,25,10,5,2,1,0.5,0.2];
    var weights=[15,15,12,10,6,3,1,3,6,10,12,15,15];
    var total=0; for (var i=0;i<weights.length;i++) total+=weights[i];
    var rnd = Math.random()*total, idx=0;
    for (var i=0;i<weights.length;i++){ rnd-=weights[i]; if (rnd<=0){ idx=i; break; } }
    var finalX = (idx/(mults.length-1))*100;
    var step=0, steps=28;
    var anim = setInterval(function(){
      step++;
      var y = 10 + (step/steps)*(stage.clientHeight-50);
      var x = 50 + (finalX-50)*(step/steps) + (Math.random()-0.5)*14;
      ball.style.top = y+'px';
      ball.style.left = 'calc('+x+'% - 9px)';
      if (step >= steps){
        clearInterval(anim); ball.remove();
        var mult = mults[idx];
        var win = Math.floor(bet*mult);
        var done = function(){
          $('plinko-status').textContent = 'x'+mult+' → '+(win ? '+'+fmt(win)+' ₽' : 'МИМО');
          if (mult >= 5) maybeGiveNft(mult);
          plinkoBusy=false;
          setTimeout(initPlinko, 3000);
        };
        if (win > 0) changeBalance(win).then(done); else done();
      }
    }, 55);
  });
}

// ============ КОЛЕСО ФОРТУНЫ ============
function initFortune(){
  var wheel = $('fortune-wheel'); wheel.innerHTML='';
  var prizes = [0, 1.5, 2, 0, 3, 5, 0, 2, 10, 0, 1.5, 25];
  for (var i=0;i<prizes.length;i++){
    var ang = (360/prizes.length)*i;
    var seg = document.createElement('div');
    seg.className='wheel-seg';
    var color = prizes[i]===0 ? '#3a0a0a' : (prizes[i]>=10 ? '#8a6a1a' : (prizes[i]>=5 ? '#6a2a0a' : '#2a1a4a'));
    seg.style.background = color;
    seg.style.transform = 'rotate('+ang+'deg)';
    seg.textContent = prizes[i] ? 'x'+prizes[i] : '0';
    wheel.appendChild(seg);
  }
  window._fortunePrizes = prizes;
  $('fortune-status').textContent = 'ВЫБЕРИ СТАВКУ';
  makeBetButtons('fortune-buttons', playFortune);
}
function playFortune(bet){
  if (bet > balance){ showAlert('Недостаточно'); return; }
  changeBalance(-bet).then(function(){
    $('fortune-buttons').innerHTML='';
    $('fortune-status').textContent='КРУТИМ...';
    var prizes = window._fortunePrizes;
    var idx = Math.floor(Math.random()*prizes.length);
    var wheel = $('fortune-wheel');
    var rotation = 360*8 + (360 - idx*(360/prizes.length));
    wheel.style.transition = 'transform 5s cubic-bezier(.15,.85,.25,1)';
    wheel.style.transform = 'rotate('+rotation+'deg)';
    setTimeout(function(){
      var mult = prizes[idx];
      var win = Math.floor(bet*mult);
      var done = function(){
        $('fortune-status').textContent = 'ВЫПАЛО x'+mult+' → '+(win ? '+'+fmt(win)+' ₽' : 'ПУСТО');
        if (mult >= 5) maybeGiveNft(mult);
        setTimeout(initFortune, 3000);
      };
      if (win > 0) changeBalance(win).then(done); else done();
    }, 5200);
  });
}

// ============ КЕНО ============
var kenoPicks=[], kenoBusy=false;
function initKeno(){
  kenoPicks=[]; kenoBusy=false;
  $('keno-status').textContent='ВЫБЕРИ 5 ЧИСЕЛ (1-40)';
  var g = $('keno-grid'); g.innerHTML='';
  for (var i=1;i<=40;i++){(function(n){
    var c = document.createElement('div'); c.className='keno-cell'; c.textContent=n;
    c.addEventListener('click', function(){
      if (kenoBusy) return;
      var idx = kenoPicks.indexOf(n);
      if (idx>=0){ kenoPicks.splice(idx,1); c.classList.remove('picked'); }
      else if (kenoPicks.length < 5){ kenoPicks.push(n); c.classList.add('picked'); }
      $('keno-status').textContent = 'ВЫБРАНО: '+kenoPicks.length+'/5';
    });
    g.appendChild(c);
  })(i);}
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
    var drawn=[];
    while (drawn.length<10){ var n=Math.floor(Math.random()*40)+1; if (drawn.indexOf(n)<0) drawn.push(n); }
    var cells = $('keno-grid').children;
    var step=0;
    var anim = setInterval(function(){
      if (step<10){ cells[drawn[step]-1].classList.add('hit'); step++; }
      else {
        clearInterval(anim);
        var hits=0;
        for (var i=0;i<kenoPicks.length;i++) if (drawn.indexOf(kenoPicks[i])>=0) hits++;
        var mults = {0:0,1:0,2:1,3:3,4:10,5:100};
        var mult = mults[hits] || 0;
        var win = bet*mult;
        var done = function(){
          $('keno-status').textContent = 'СОВПАЛО: '+hits+'/5 → '+(win ? '+'+fmt(win)+' ₽' : 'МИМО');
          if (mult >= 5) maybeGiveNft(mult);
          kenoBusy=false;
          setTimeout(initKeno, 3000);
        };
        if (win > 0) changeBalance(win).then(done); else done();
      }
    }, 250);
  });
}

// ============ КЕЙСЫ ============
var caseBusy=false;
function initCase(){
  caseBusy=false;
  $('case-status').textContent='ВЫБЕРИ СТАВКУ';
  $('case-strip').innerHTML='';
  makeBetButtons('case-buttons', playCase);
}
function playCase(bet){
  if (caseBusy) return;
  if (bet > balance){ showAlert('Недостаточно'); return; }
  caseBusy=true;
  changeBalance(-bet).then(function(){
    $('case-buttons').innerHTML='';
    $('case-status').textContent='КРУТИМ...';
    var strip = $('case-strip'); strip.innerHTML='';
    var prizes = [
      {e:'💎',m:50},{e:'👑',m:20},{e:'⭐',m:10},{e:'🚀',m:5},{e:'🪐',m:3},
      {e:'🃏',m:25},{e:'🦅',m:40},{e:'🔥',m:2},{e:'🌙',m:1.5},{e:'⚡',m:2},{e:'☄️',m:4},
      {e:'💀',m:0},{e:'💀',m:0},{e:'💀',m:0},{e:'💀',m:0},{e:'🍀',m:8},{e:'🎁',m:1}
    ];
    var arr = [];
    for (var i=0;i<50;i++){
      var p = prizes[Math.floor(Math.random()*prizes.length)];
      arr.push(p);
      var d = document.createElement('div'); d.className='case-item'; d.textContent=p.e;
      strip.appendChild(d);
    }
    var winner = prizes[Math.floor(Math.random()*prizes.length)];
    var winIdx = 40;
    arr[winIdx] = winner;
    strip.children[winIdx].textContent = winner.e;
    var shift = winIdx * 76 - strip.clientWidth/2 + 35;
    strip.style.transition = 'transform 4s cubic-bezier(.15,.85,.25,1)';
    strip.style.transform = 'translateX(-'+shift+'px)';
    setTimeout(function(){
      strip.children[winIdx].classList.add('win');
      var win = Math.floor(bet*winner.m);
      var done = function(){
        $('case-status').textContent = 'ВЫПАЛО '+winner.e+' x'+winner.m+' → '+(win ? '+'+fmt(win)+' ₽' : 'ПУСТО');
        if (winner.m >= 5) maybeGiveNft(winner.m);
        strip.style.transition='none'; strip.style.transform='translateX(0)';
        caseBusy=false;
        setTimeout(initCase, 3000);
      };
      if (win > 0) changeBalance(win).then(done); else done();
    }, 4200);
  });
}

// ============ ПЕНАЛЬТИ ============
var penBusy=false, penZone='';
function initPenalty(){
  penBusy=false; penZone='';
  $('penalty-status').textContent='ВЫБЕРИ УГОЛ И СТАВКУ';
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
    var zones=['left','center','right'];
    var keeperZone = zones[Math.floor(Math.random()*3)];
    var kpos = {left:'20px', center:'calc(50% - 30px)', right:'calc(100% - 80px)'};
    $('keeper').style.left = kpos[keeperZone];
    var bpos = {left:'40px', center:'calc(50% - 18px)', right:'calc(100% - 90px)'};
    $('ball-pen').style.left = bpos[penZone];
    $('ball-pen').style.bottom = '120px';
    setTimeout(function(){
      var goal = penZone !== keeperZone;
      var mult = goal ? (penZone==='center' ? 3 : 2) : 0;
      var win = bet*mult;
      var done = function(){
        $('penalty-status').textContent = goal ? ('⚽ ГОЛ! +'+fmt(win)+' ₽ (x'+mult+')') : '🧤 ВРАТАРЬ ВЗЯЛ!';
        if (goal && mult >= 3) maybeGiveNft(mult);
        penBusy=false;
        setTimeout(initPenalty, 3000);
      };
      if (win > 0) changeBalance(win).then(done); else done();
    }, 700);
  });
}

// ============ СКАЧКИ ============
var raceHorse=-1, raceLoop=null, racePos=[], raceRunning=false;
function initRace(){
  if (raceLoop){ clearInterval(raceLoop); raceLoop=null; }
  raceHorse=-1; racePos=[0,0,0,0,0]; raceRunning=false;
  $('race-status').textContent='ВЫБЕРИ ЛОШАДЬ И СТАВКУ';
  var t = $('race-track'); t.innerHTML='';
  var horses = ['🐎','🏇','🦄','🐴','🦓'];
  for (var i=0;i<5;i++){
    var lane = document.createElement('div'); lane.className='race-lane';
    lane.style.top = (i*44)+'px'; lane.style.height='44px';
    lane.innerHTML = '<span class="horse" id="horse-'+i+'">'+horses[i]+'</span>';
    (function(idx){ lane.addEventListener('click', function(){
      raceHorse=idx;
      var lanes = document.querySelectorAll('.race-lane');
      for (var j=0;j<lanes.length;j++) lanes[j].classList.remove('selected');
      lane.classList.add('selected');
      $('race-status').textContent='ЛОШАДЬ '+(idx+1)+' | ВЫБЕРИ СТАВКУ';
    }); })(i);
    t.appendChild(lane);
  }
  makeBetButtons('race-buttons', startRace);
}
function startRace(bet){
  if (raceHorse < 0){ showAlert('Выбери лошадь'); return; }
  if (bet > balance){ showAlert('Недостаточно'); return; }
  raceRunning=true; racePos=[0,0,0,0,0];
  changeBalance(-bet).then(function(){
    $('race-buttons').innerHTML='';
    $('race-status').textContent='🏁 ЗАЕЗД!';
    var t = $('race-track');
    var fin = t.clientWidth - 80;
    raceLoop = setInterval(function(){
      for (var i=0;i<5;i++){
        racePos[i] += Math.random()*10 + 2;
        var h = $('horse-'+i);
        if (h) h.style.transform = 'translateX('+Math.min(racePos[i], fin)+'px)';
      }
      for (var i=0;i<5;i++){
        if (racePos[i] >= fin){
          clearInterval(raceLoop); raceLoop=null; raceRunning=false;
          var winner = i;
          var mult = (winner === raceHorse) ? 5 : 0;
          var win = bet*mult;
          var done = function(){
            $('race-status').textContent = (winner === raceHorse) ? ('🏆 ПОБЕДА! +'+fmt(win)+' ₽') : ('🐎 Победила лошадь '+(winner+1)+'. -'+fmt(bet)+' ₽');
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

// ============ ХАЙ-ЛОУ ============
var hiloBet=0, hiloActive=false, hiloCard=null, hiloStreak=0;
function initHilo(){
  hiloBet=0; hiloActive=false; hiloCard=null; hiloStreak=0;
  $('hilo-status').textContent='ВЫБЕРИ СТАВКУ';
  $('hilo-cards').innerHTML='';
  $('hilo-actions').style.display='none';
  makeBetButtons('hilo-buttons', startHilo);
}
function rankOf(c){ return ['2','3','4','5','6','7','8','9','10','J','Q','K','A'].indexOf(c.v); }
function startHilo(bet){
  if (bet > balance){ showAlert('Недостаточно'); return; }
  hiloBet=bet; hiloActive=true; hiloStreak=0;
  changeBalance(-bet).then(function(){
    hiloCard = drawCard();
    $('hilo-cards').innerHTML = '<div class="card card-big'+(hiloCard.red?' red':'')+'">'+hiloCard.v+'<div style="font-size:20px;">'+hiloCard.s+'</div></div>';
    $('hilo-buttons').innerHTML='';
    $('hilo-actions').style.display='grid';
    $('hilo-status').textContent='БОЛЬШЕ ИЛИ МЕНЬШЕ?';
  });
}
var hiloBtns = document.querySelectorAll('[data-hilo]');
for (var i=0;i<hiloBtns.length;i++){(function(b){
  b.addEventListener('click', function(){
    if (!hiloActive) return;
    var guess = b.getAttribute('data-hilo');
    var next = drawCard();
    $('hilo-cards').innerHTML += '<div class="card card-big'+(next.red?' red':'')+'">'+next.v+'<div style="font-size:20px;">'+next.s+'</div></div>';
    var cur = rankOf(hiloCard), nxt = rankOf(next);
    var correct = (guess==='higher' && nxt > cur) || (guess==='lower' && nxt < cur);
    if (correct){
      hiloStreak++;
      hiloCard = next;
      var mult = 1 + hiloStreak * 0.5;
      var potential = Math.floor(hiloBet * mult);
      $('hilo-status').textContent = '✅ x'+mult.toFixed(2)+' | Потенциал: '+fmt(potential)+' ₽ | Продолжить?';
    } else {
      hiloActive=false;
      $('hilo-status').textContent='❌ НЕ УГАДАЛ! -'+fmt(hiloBet)+' ₽';
      $('hilo-actions').style.display='none';
      setTimeout(initHilo, 3000);
    }
  });
})(hiloBtns[i]);}

// ============ УДАЧА ============
var luckyPick=0, luckyBusy=false;
function initLucky(){
  luckyPick=0; luckyBusy=false;
  $('lucky-display').textContent='🍀';
  $('lucky-status').textContent='ВЫБЕРИ ЧИСЛО 1-10';
  makeBetButtons('lucky-buttons', playLucky);
  var nums = document.querySelectorAll('[data-lucky]');
  for (var i=0;i<nums.length;i++){(function(b){
    b.addEventListener('click', function(){
      luckyPick = parseInt(b.getAttribute('data-lucky'));
      $('lucky-status').textContent='ВЫБРАНО: '+luckyPick+' | ВЫБЕРИ СТАВКУ';
    });
  })(nums[i]);}
}
function playLucky(bet){
  if (luckyBusy) return;
  if (!luckyPick){ showAlert('Выбери число'); return; }
  if (bet > balance){ showAlert('Недостаточно'); return; }
  luckyBusy=true;
  changeBalance(-bet).then(function(){
    $('lucky-buttons').innerHTML='';
    $('lucky-status').textContent='КРУТИМ...';
    var wins = [10, 8, 5, 3, 2];
    var anim = setInterval(function(){
      $('lucky-display').textContent = Math.floor(Math.random()*10)+1;
    }, 80);
    setTimeout(function(){
      clearInterval(anim);
      var result = Math.floor(Math.random()*10)+1;
      $('lucky-display').textContent = result;
      var diff = Math.abs(result - luckyPick);
      var mult = 0;
      if (diff === 0) mult = 10;
      else if (diff === 1) mult = 3;
      else if (diff === 2) mult = 1.5;
      var win = Math.floor(bet*mult);
      var done = function(){
        $('lucky-status').textContent = 'ВЫПАЛО: '+result+' → '+(win ? '+'+fmt(win)+' ₽ (x'+mult+')' : 'МИМО');
        if (mult >= 5) maybeGiveNft(mult);
        luckyBusy=false;
        setTimeout(initLucky, 3000);
      };
      if (win > 0) changeBalance(win).then(done); else done();
    }, 1500);
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
    d.style.cssText='background:linear-gradient(160deg,#1a0a2a,#0a0515);border:2px solid #d4af37;border-radius:14px;padding:14px;text-align:center';
    d.innerHTML = '<div style="font-size:52px">'+g.emoji+'</div><div style="font-size:12px;font-weight:700;color:#ffdd44">'+g.name+'</div>';
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
    await message.answer("🎰 <b>VEGAS CASINO</b>\n\n💰 Баланс: 100 ₽\n🎲 17 азартных игр\n🎁 NFT за выигрыш\n\nНажми кнопку:", reply_markup=kb, parse_mode="HTML")

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
