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
.red-btn{background:linear-gradient(135deg,#ff3a5a,#cc2244)!important;color:#fff!important}
.status{text-align:center;font-size:14px;min-height:24px;margin-bottom:8px;font-weight:700;color:#ffdd44}
.card{background:#fff;border-radius:8px;color:#000;font-weight:900;display:inline-flex;flex-direction:column;align-items:center;justify-content:center;border:2px solid #333;box-shadow:0 4px 8px rgba(0,0,0,.5)}
.card.red{color:#cc2244}
.card-big{width:56px;height:80px;font-size:20px;margin:3px}
.card-small{width:44px;height:64px;font-size:16px;margin:3px}
.cards-row{display:flex;flex-wrap:wrap;justify-content:center;min-height:96px;margin:14px 0}
.grid-3{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-top:10px}
.grid-4{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-top:10px}
.custom-bet{margin-top:12px;background:#0f0f20;border:1px solid #2a2a4a;border-radius:12px;padding:12px}
.custom-bet label{display:block;font-size:11px;opacity:.6;margin-bottom:6px;letter-spacing:1px}
.custom-bet .row{display:flex;gap:8px}
.custom-bet input{flex:1;background:#05050f;border:1px solid #2a2a4a;color:#fff;padding:12px;border-radius:10px;font-size:15px;font-weight:700;text-align:center}
.custom-bet button{background:linear-gradient(135deg,#d4af37,#ffdd44);border:none;color:#1a0a2a;padding:12px 20px;border-radius:10px;font-size:14px;font-weight:900;cursor:pointer}
.roulette-scene{position:relative;width:100%;height:340px;margin:14px auto;display:flex;align-items:center;justify-content:center}
.roulette-wheel{width:300px;height:300px;border-radius:50%;border:12px solid #d4af37;position:relative;transition:transform 8s cubic-bezier(.1,.8,.2,1);box-shadow:0 0 40px rgba(212,175,55,.6),inset 0 0 40px rgba(0,0,0,.8);overflow:hidden}
.roulette-seg{position:absolute;top:0;left:50%;width:50%;height:50%;transform-origin:0% 100%;display:flex;align-items:flex-start;justify-content:center;padding-top:6px;font-size:10px;font-weight:900;color:#fff;text-shadow:0 0 3px #000}
.roulette-pointer{position:absolute;top:6px;left:50%;transform:translateX(-50%);width:0;height:0;border-left:14px solid transparent;border-right:14px solid transparent;border-top:26px solid #ffdd44;z-index:20;filter:drop-shadow(0 0 10px #d4af37)}
.roulette-ball{position:absolute;width:14px;height:14px;background:radial-gradient(circle at 30% 30%,#fff,#ccc);border-radius:50%;box-shadow:0 0 10px #fff;z-index:15;transition:all .5s}
.roulette-center{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:60px;height:60px;background:radial-gradient(circle,#d4af37,#8a6a1a);border-radius:50%;border:3px solid #ffdd44;z-index:10;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:900;color:#1a0a2a;text-align:center}
.roulette-table{margin-top:10px;background:#0a3a0a;border:2px solid #d4af37;border-radius:10px;padding:8px}
.roulette-numbers{display:grid;grid-template-columns:repeat(6,1fr);gap:3px}
.rn{aspect-ratio:1.4;background:#1a1a1a;border:1px solid #444;border-radius:4px;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:900;color:#fff;cursor:pointer}
.rn.red{background:#8a1a2a}
.rn.black{background:#0a0a0a}
.rn.green{background:#0a5a2a}
.rn.selected{border-color:#ffdd44;box-shadow:0 0 10px #ffdd44;transform:scale(1.05)}
.rn:active{transform:scale(.9)}
.roulette-outside{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-top:8px}
.roulette-outside button{padding:12px;font-size:12px;font-weight:800;border-radius:8px;cursor:pointer;border:1px solid #444;color:#fff}
.roulette-outside button.sel{outline:3px solid #ffdd44;box-shadow:0 0 15px #ffdd44}
.roulette-history{display:flex;gap:4px;justify-content:center;margin-top:8px;flex-wrap:wrap;min-height:26px}
.hist-ball{width:24px;height:24px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:900;color:#fff;border:1px solid #444}
.hist-ball.red{background:#8a1a2a}
.hist-ball.black{background:#0a0a0a}
.hist-ball.green{background:#0a5a2a}
.slot-row{display:flex;justify-content:center;gap:10px;margin:20px 0}
.slot-cell{width:80px;height:110px;background:linear-gradient(180deg,#1a1a2e,#0a0a15);border:3px solid #d4af37;border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:48px;box-shadow:inset 0 0 20px rgba(212,175,55,.3)}
.slot-cell.spin{animation:sp .08s infinite}
@keyframes sp{0%,100%{transform:translateY(-10px)}50%{transform:translateY(10px)}}
.mines-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:6px;margin-top:12px}
.mine-cell{aspect-ratio:1;background:linear-gradient(160deg,#1a0a2a,#0a0515);border:1px solid #2a1a4a;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:22px;cursor:pointer}
.mine-cell.opened{background:linear-gradient(160deg,#2a1a4a,#1a0a2a)}
.mine-cell.mine{background:#3a0a0a;border-color:#ff3a5a;box-shadow:0 0 15px #ff3a5a}
.crash-stage{position:relative;height:250px;background:#0a0515;border-radius:14px;overflow:hidden;border:2px solid #d4af37;margin-top:10px}
.crash-line{position:absolute;bottom:0;left:0;height:100%;width:0;background:linear-gradient(90deg,#4aff8a,#ffdd44,#ff3a5a);clip-path:polygon(0 100%,100% 0,100% 100%);transition:width .1s linear}
.crash-mult{position:absolute;top:20px;left:50%;transform:translateX(-50%);font-size:52px;font-weight:900;color:#4aff8a;text-shadow:0 0 30px #4aff8a;z-index:10}
.crash-mult.crashed{color:#ff3a5a;text-shadow:0 0 30px #ff3a5a}
.blackjack-table{background:radial-gradient(ellipse at center,#0a5a2a,#052a15);border:4px solid #d4af37;border-radius:14px;padding:14px;margin-top:14px}
.bj-score{text-align:center;font-size:13px;font-weight:900;color:#ffdd44}
.dice-table{display:flex;gap:8px;justify-content:center;margin:20px 0;flex-wrap:wrap}
.die{width:70px;height:70px;background:#fff;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:40px;font-weight:900;color:#1a0a2a;border:2px solid #333;box-shadow:0 4px 8px rgba(0,0,0,.5)}
.poker-table{background:radial-gradient(ellipse at center,#0a5a2a,#052a15);border:4px solid #d4af37;border-radius:14px;padding:14px;margin-top:14px}
.poker-seat{text-align:center;font-size:12px;color:#ffdd44;font-weight:900;margin-bottom:6px}
.poker-bet-info{text-align:center;font-size:13px;color:#fff;margin:8px 0;font-weight:700}
.wheel-wrap{position:relative;width:300px;height:300px;margin:20px auto}
.fortune-wheel{width:100%;height:100%;border-radius:50%;border:12px solid #d4af37;position:relative;overflow:hidden;box-shadow:0 0 30px rgba(212,175,55,.5);transition:transform 6s cubic-bezier(.1,.8,.2,1)}
.wheel-seg{position:absolute;top:50%;left:50%;width:50%;height:50%;transform-origin:0% 0%;display:flex;align-items:flex-start;justify-content:center;padding-top:8px;font-size:14px;font-weight:900;color:#fff}
.wheel-pointer{position:absolute;top:-18px;left:50%;transform:translateX(-50%);width:0;height:0;border-left:16px solid transparent;border-right:16px solid transparent;border-top:28px solid #ffdd44;z-index:20;filter:drop-shadow(0 0 10px #d4af37)}
.ladder-stage{margin:14px 0}
.ladder-level{display:flex;align-items:center;justify-content:center;gap:10px;padding:10px;margin:4px 0;background:linear-gradient(90deg,#1a0a2a,#2a1a4a);border:1px solid #2a1a4a;border-radius:10px;font-weight:900;font-size:14px;color:#ffdd44}
.ladder-level.active{border-color:#4aff8a;box-shadow:0 0 20px #4aff8a}
.ladder-level.done{opacity:.4}
.dice3-stage{margin:14px 0;text-align:center}
.dice3-die{display:inline-flex;align-items:center;justify-content:center;width:70px;height:70px;background:#fff;border-radius:12px;font-size:40px;font-weight:900;color:#1a0a2a;margin:0 6px;border:2px solid #333;box-shadow:0 4px 8px rgba(0,0,0,.5)}
.hi-lo-stage{margin-top:14px}
.bj-multi{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:14px}
.keno-grid{display:grid;grid-template-columns:repeat(8,1fr);gap:4px;margin-top:14px}
.keno-cell{aspect-ratio:1;background:linear-gradient(160deg,#1a0a2a,#0a0515);border:1px solid #2a1a4a;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;cursor:pointer}
.keno-cell.picked{background:#4a3aff;color:#fff;border-color:#6a4aff}
.keno-cell.hit{background:#4aff8a;color:#000;box-shadow:0 0 10px #4aff8a}
.nft-card{background:linear-gradient(160deg,#1a0a2a,#0a0515);border:2px solid #d4af37;border-radius:14px;padding:14px;text-align:center}
</style>
</head>
<body>

<div id="menu" class="screen active">
  <div class="balance"><h1>💰 БАЛАНС</h1><div class="amount"><span id="balance">100.00</span> ₽</div></div>
  <div class="games">
    <div class="game" id="btn-roulette"><div class="name">🎡 РУЛЕТКА</div><div class="desc">0-36</div></div>
    <div class="game" id="btn-blackjack"><div class="name">🃏 БЛЭКДЖЕК</div><div class="desc">21</div></div>
    <div class="game" id="btn-poker"><div class="name">♠️ ПОКЕР vs ИИ</div><div class="desc">РЕЖИМЫ</div></div>
    <div class="game" id="btn-baccarat"><div class="name">🎴 БАККАРА</div><div class="desc">9</div></div>
    <div class="game" id="btn-craps"><div class="name">🎲 КРАПС</div><div class="desc">КОСТИ</div></div>
    <div class="game" id="btn-crash"><div class="name">📈 КРАШ</div><div class="desc">УСПЕЙ</div></div>
    <div class="game" id="btn-mines"><div class="name">💣 МИНЫ</div><div class="desc">5x5</div></div>
    <div class="game" id="btn-slots"><div class="name">🎰 СЛОТЫ</div><div class="desc">777</div></div>
    <div class="game" id="btn-hilo"><div class="name">🃏 ХАЙ-ЛОУ</div><div class="desc">БОЛЬШЕ/МЕНЬШЕ</div></div>
    <div class="game" id="btn-fortune"><div class="name">🎡 КОЛЕСО</div><div class="desc">ФОРТУНЫ</div></div>
    <div class="game" id="btn-ladder"><div class="name">🪜 ЛЕСТНИЦА</div><div class="desc">ДО X50</div></div>
    <div class="game" id="btn-dice3"><div class="name">🎲 3 КОСТИ</div><div class="desc">СУММА</div></div>
    <div class="game" id="btn-war"><div class="name">⚔️ ВОЙНА</div><div class="desc">КАРТЫ</div></div>
    <div class="game" id="btn-sicbo"><div class="name">🎲 СИК-БО</div><div class="desc">3 КОСТИ</div></div>
    <div class="game" id="btn-keno"><div class="name">🎯 КЕНО</div><div class="desc">5/40</div></div>
    <div class="game" id="btn-21plus"><div class="name">🃏 21+3</div><div class="desc">БЛЭКДЖЕК+</div></div>
    <div class="game" id="btn-inv"><div class="name">🎁 ИНВЕНТАРЬ</div><div class="desc">NFT</div></div>
  </div>
</div>

<!-- РУЛЕТКА (как было) -->
<div id="roulette" class="screen">
  <button class="back" id="back-roulette">← НАЗАД</button>
  <h2>🎡 РУЛЕТКА</h2>
  <div class="roulette-scene">
    <div class="roulette-pointer"></div>
    <div class="roulette-wheel" id="roulette-wheel"></div>
    <div class="roulette-ball" id="roulette-ball" style="display:none;"></div>
    <div class="roulette-center" id="roulette-center">SPIN</div>
  </div>
  <div class="status" id="roulette-status">СДЕЛАЙ СТАВКУ</div>
  <div class="roulette-history" id="roulette-history"></div>
  <div class="roulette-table">
    <div class="roulette-numbers" id="roulette-numbers"></div>
    <div class="roulette-outside" id="roulette-outside">
      <button data-rl="red" style="background:#8a1a2a;">🔴 КРАСНОЕ x2</button>
      <button data-rl="black" style="background:#0a0a0a;">⚫ ЧЁРНОЕ x2</button>
      <button data-rl="green" style="background:#0a5a2a;">🟢 ЗЕРО x35</button>
      <button data-rl="even" style="background:#2a2a4a;">ЧЁТ x2</button>
      <button data-rl="odd" style="background:#2a2a4a;">НЕЧЁТ x2</button>
      <button data-rl="low" style="background:#2a2a4a;">1-18 x2</button>
      <button data-rl="high" style="background:#2a2a4a;">19-36 x2</button>
      <button data-rl="dozen1" style="background:#3a1a1a;">1-12 x3</button>
      <button data-rl="dozen2" style="background:#3a1a1a;">13-24 x3</button>
      <button data-rl="dozen3" style="background:#3a1a1a;">25-36 x3</button>
    </div>
  </div>
  <div class="bet-buttons" id="roulette-buttons"></div>
  <div class="custom-bet"><label>СВОЯ СТАВКА</label><div class="row"><input type="number" id="custom-roulette" placeholder="100" min="1"><button id="custom-roulette-go">ИГРАТЬ</button></div></div>
</div>

<!-- БЛЭКДЖЕК -->
<div id="blackjack" class="screen">
  <button class="back" id="back-blackjack">← НАЗАД</button>
  <h2>🃏 БЛЭКДЖЕК</h2>
  <div class="blackjack-table">
    <div class="bj-score">ДИЛЕР: <span id="bj-dscore">0</span></div>
    <div class="cards-row" id="bj-dealer"></div>
    <div class="bj-score">ТЫ: <span id="bj-pscore">0</span></div>
    <div class="cards-row" id="bj-player"></div>
  </div>
  <div class="status" id="bj-status">ВЫБЕРИ СТАВКУ</div>
  <div class="bet-buttons" id="bj-buttons"></div>
  <div class="custom-bet"><label>СВОЯ СТАВКА</label><div class="row"><input type="number" id="custom-bj" placeholder="100" min="1"><button id="custom-bj-go">ИГРАТЬ</button></div></div>
  <div id="bj-actions" style="display:none;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:12px;">
    <button class="big-btn" id="bj-hit">ЕЩЁ</button>
    <button class="big-btn red-btn" id="bj-stand">СТОП</button>
    <button class="big-btn green-btn" id="bj-double">X2</button>
  </div>
</div>

<!-- ПОКЕР vs ИИ -->
<div id="poker" class="screen">
  <button class="back" id="back-poker">← НАЗАД</button>
  <h2>♠️ ПОКЕР vs ИИ</h2>
  <div class="poker-table">
    <div class="poker-seat">🤖 ИИ: <span id="poker-ai-name">Ожидание</span></div>
    <div class="cards-row" id="poker-ai"></div>
    <div class="poker-bet-info" id="poker-pot">БАНК: 0 ₽</div>
    <div class="cards-row" id="poker-table-cards"></div>
    <div class="poker-seat">👤 ТЫ</div>
    <div class="cards-row" id="poker-my"></div>
  </div>
  <div class="status" id="poker-status">ВЫБЕРИ РЕЖИМ И СТАВКУ</div>
  <div class="grid-3" id="poker-modes" style="margin-top:10px;">
    <button class="bet-btn" data-mode="easy">ЛЁГКИЙ</button>
    <button class="bet-btn" data-mode="medium">СРЕДНИЙ</button>
    <button class="bet-btn" data-mode="hard">СЛОЖНЫЙ</button>
  </div>
  <div class="bet-buttons" id="poker-buttons"></div>
  <div class="custom-bet"><label>СВОЯ СТАВКА</label><div class="row"><input type="number" id="custom-poker" placeholder="100" min="1"><button id="custom-poker-go">ИГРАТЬ</button></div></div>
  <div id="poker-actions" style="display:none;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:12px;">
    <button class="big-btn" id="poker-check">ЧЕК</button>
    <button class="big-btn" id="poker-raise">РЕЙЗ x2</button>
    <button class="big-btn red-btn" id="poker-fold">ФОЛД</button>
  </div>
</div>

<!-- БАККАРА -->
<div id="baccarat" class="screen">
  <button class="back" id="back-baccarat">← НАЗАД</button>
  <h2>🎴 БАККАРА</h2>
  <div class="blackjack-table">
    <div class="bj-score">ИГРОК: <span id="bac-pscore">0</span></div>
    <div class="cards-row" id="bac-player"></div>
    <div class="bj-score">БАНКИР: <span id="bac-bscore">0</span></div>
    <div class="cards-row" id="bac-banker"></div>
  </div>
  <div class="status" id="bac-status">ВЫБЕРИ СТАВКУ</div>
  <div class="grid-3" id="bac-picks">
    <button class="bet-btn" data-bac="P">ИГРОК x2</button>
    <button class="bet-btn" data-bac="B">БАНКИР x1.95</button>
    <button class="bet-btn" data-bac="T">НИЧЬЯ x8</button>
  </div>
  <div class="bet-buttons" id="bac-buttons"></div>
  <div class="custom-bet"><label>СВОЯ СТАВКА</label><div class="row"><input type="number" id="custom-bac" placeholder="100" min="1"><button id="custom-bac-go">ИГРАТЬ</button></div></div>
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
  <div class="custom-bet"><label>СВОЯ СТАВКА</label><div class="row"><input type="number" id="custom-craps" placeholder="100" min="1"><button id="custom-craps-go">ИГРАТЬ</button></div></div>
</div>

<!-- КРАШ -->
<div id="crash" class="screen">
  <button class="back" id="back-crash">← НАЗАД</button>
  <h2>📈 КРАШ</h2>
  <div class="crash-stage">
    <div class="crash-line" id="crash-line"></div>
    <div class="crash-mult" id="crash-mult">x1.00</div>
  </div>
  <div class="status" id="crash-status">ВЫБЕРИ СТАВКУ</div>
  <div class="bet-buttons" id="crash-buttons"></div>
  <div class="custom-bet"><label>СВОЯ СТАВКА</label><div class="row"><input type="number" id="custom-crash" placeholder="100" min="1"><button id="custom-crash-go">ИГРАТЬ</button></div></div>
  <button class="big-btn green-btn" id="crash-cashout" style="display:none;">ЗАБРАТЬ</button>
</div>

<!-- МИНЫ -->
<div id="mines" class="screen">
  <button class="back" id="back-mines">← НАЗАД</button>
  <h2>💣 МИНЫ</h2>
  <div class="status" id="mines-status">ВЫБЕРИ СТАВКУ</div>
  <div class="grid-3" id="mines-levels" style="margin-bottom:10px;">
    <button class="bet-btn" data-mines="1">1 МИНА</button>
    <button class="bet-btn" data-mines="3">3 МИНЫ</button>
    <button class="bet-btn" data-mines="5">5 МИН</button>
  </div>
  <div class="bet-buttons" id="mines-buttons"></div>
  <div class="custom-bet"><label>СВОЯ СТАВКА</label><div class="row"><input type="number" id="custom-mines" placeholder="100" min="1"><button id="custom-mines-go">ИГРАТЬ</button></div></div>
  <div class="mines-grid" id="mines-grid"></div>
  <button class="big-btn green-btn" id="mines-cashout" style="display:none;">ЗАБРАТЬ</button>
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
  <div class="custom-bet"><label>СВОЯ СТАВКА</label><div class="row"><input type="number" id="custom-slots" placeholder="100" min="1"><button id="custom-slots-go">ИГРАТЬ</button></div></div>
</div>

<!-- ХАЙ-ЛОУ -->
<div id="hilo" class="screen">
  <button class="back" id="back-hilo">← НАЗАД</button>
  <h2>🃏 ХАЙ-ЛОУ</h2>
  <div class="status" id="hilo-status">ВЫБЕРИ СТАВКУ</div>
  <div class="cards-row" id="hilo-cards"></div>
  <div class="bet-buttons" id="hilo-buttons"></div>
  <div class="custom-bet"><label>СВОЯ СТАВКА</label><div class="row"><input type="number" id="custom-hilo" placeholder="100" min="1"><button id="custom-hilo-go">ИГРАТЬ</button></div></div>
  <div id="hilo-actions" style="display:none;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px;">
    <button class="big-btn" data-hilo="higher">БОЛЬШЕ ↑</button>
    <button class="big-btn" data-hilo="lower">МЕНЬШЕ ↓</button>
  </div>
  <button class="big-btn green-btn" id="hilo-cashout" style="display:none;">ЗАБРАТЬ</button>
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
  <div class="custom-bet"><label>СВОЯ СТАВКА</label><div class="row"><input type="number" id="custom-fortune" placeholder="100" min="1"><button id="custom-fortune-go">ИГРАТЬ</button></div></div>
</div>

<!-- ЛЕСТНИЦА -->
<div id="ladder" class="screen">
  <button class="back" id="back-ladder">← НАЗАД</button>
  <h2>🪜 ЛЕСТНИЦА</h2>
  <div class="ladder-stage" id="ladder-stage"></div>
  <div class="status" id="ladder-status">ВЫБЕРИ СТАВКУ</div>
  <div class="bet-buttons" id="ladder-buttons"></div>
  <div class="custom-bet"><label>СВОЯ СТАВКА</label><div class="row"><input type="number" id="custom-ladder" placeholder="100" min="1"><button id="custom-ladder-go">ИГРАТЬ</button></div></div>
  <button class="big-btn" id="ladder-next" style="display:none;">СЛЕДУЮЩИЙ ШАГ</button>
  <button class="big-btn green-btn" id="ladder-cashout" style="display:none;">ЗАБРАТЬ</button>
</div>

<!-- 3 КОСТИ (больше/меньше) -->
<div id="dice3" class="screen">
  <button class="back" id="back-dice3">← НАЗАД</button>
  <h2>🎲 3 КОСТИ</h2>
  <div class="dice3-stage" id="dice3-stage">
    <div class="dice3-die" id="d31">⚀</div>
    <div class="dice3-die" id="d32">⚀</div>
    <div class="dice3-die" id="d33">⚀</div>
  </div>
  <div class="status" id="dice3-status">ВЫБЕРИ 4-10 ИЛИ 11-17</div>
  <div class="grid-4" id="dice3-picks">
    <button class="bet-btn" data-d3="low">4-10 x2</button>
    <button class="bet-btn" data-d3="mid">11-17 x2</button>
    <button class="bet-btn" data-d3="triple">ТРОЙНОЙ x30</button>
    <button class="bet-btn" data-d3="pair">ПАРА x8</button>
  </div>
  <div class="bet-buttons" id="dice3-buttons"></div>
  <div class="custom-bet"><label>СВОЯ СТАВКА</label><div class="row"><input type="number" id="custom-dice3" placeholder="100" min="1"><button id="custom-dice3-go">ИГРАТЬ</button></div></div>
</div>

<!-- ВОЙНА (карты) -->
<div id="war" class="screen">
  <button class="back" id="back-war">← НАЗАД</button>
  <h2>⚔️ ВОЙНА</h2>
  <div class="blackjack-table">
    <div class="bj-score">🤖 ИИ</div>
    <div class="cards-row" id="war-ai"></div>
    <div class="bj-score">👤 ТЫ</div>
    <div class="cards-row" id="war-my"></div>
  </div>
  <div class="status" id="war-status">ВЫБЕРИ СТАВКУ</div>
  <div class="bet-buttons" id="war-buttons"></div>
  <div class="custom-bet"><label>СВОЯ СТАВКА</label><div class="row"><input type="number" id="custom-war" placeholder="100" min="1"><button id="custom-war-go">ИГРАТЬ</button></div></div>
</div>

<!-- СИК-БО -->
<div id="sicbo" class="screen">
  <button class="back" id="back-sicbo">← НАЗАД</button>
  <h2>🎲 СИК-БО</h2>
  <div class="dice-table" id="sicbo-dice">
    <div class="die" id="sb1">⚀</div>
    <div class="die" id="sb2">⚀</div>
    <div class="die" id="sb3">⚀</div>
  </div>
  <div class="status" id="sicbo-status">ВЫБЕРИ СТАВКУ</div>
  <div class="grid-4" id="sicbo-picks">
    <button class="bet-btn" data-sb="small">МАЛО 4-10 x2</button>
    <button class="bet-btn" data-sb="big">БОЛЬШО 11-17 x2</button>
    <button class="bet-btn" data-sb="even">ЧЁТ x2</button>
    <button class="bet-btn" data-sb="odd">НЕЧЁТ x2</button>
    <button class="bet-btn" data-sb="one">1 = 3x</button>
    <button class="bet-btn" data-sb="pair">ПАРА x8</button>
    <button class="bet-btn" data-sb="triple">ТРОЙНОЙ x30</button>
    <button class="bet-btn" data-sb="total4">СУММА 4 x60</button>
  </div>
  <div class="bet-buttons" id="sicbo-buttons"></div>
  <div class="custom-bet"><label>СВОЯ СТАВКА</label><div class="row"><input type="number" id="custom-sicbo" placeholder="100" min="1"><button id="custom-sicbo-go">ИГРАТЬ</button></div></div>
</div>

<!-- КЕНО -->
<div id="keno" class="screen">
  <button class="back" id="back-keno">← НАЗАД</button>
  <h2>🎯 КЕНО</h2>
  <div class="status" id="keno-status">ВЫБЕРИ 5 ЧИСЕЛ</div>
  <div class="bet-buttons" id="keno-buttons"></div>
  <div class="custom-bet"><label>СВОЯ СТАВКА</label><div class="row"><input type="number" id="custom-keno" placeholder="100" min="1"><button id="custom-keno-go">ИГРАТЬ</button></div></div>
  <div class="keno-grid" id="keno-grid"></div>
</div>

<!-- 21+3 -->
<div id="twentyone" class="screen">
  <button class="back" id="back-twentyone">← НАЗАД</button>
  <h2>🃏 21+3 БЛЭКДЖЕК+</h2>
  <div class="blackjack-table">
    <div class="bj-score">ДИЛЕР: <span id="bj21-dscore">0</span></div>
    <div class="cards-row" id="bj21-dealer"></div>
    <div class="bj-score">ТЫ: <span id="bj21-pscore">0</span></div>
    <div class="cards-row" id="bj21-player"></div>
  </div>
  <div class="status" id="bj21-status">ВЫБЕРИ СТАВКУ</div>
  <div class="bet-buttons" id="bj21-buttons"></div>
  <div class="custom-bet"><label>СВОЯ СТАВКА</label><div class="row"><input type="number" id="custom-bj21" placeholder="100" min="1"><button id="custom-bj21-go">ИГРАТЬ</button></div></div>
  <div id="bj21-actions" style="display:none;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px;">
    <button class="big-btn" id="bj21-hit">ЕЩЁ</button>
    <button class="big-btn red-btn" id="bj21-stand">СТОП</button>
  </div>
</div>

<!-- ИНВЕНТАРЬ -->
<div id="inv" class="screen">
  <button class="back" id="back-inv">← НАЗАД</button>
  <h2>🎁 ИНВЕНТАРЬ</h2>
  <div id="inv-list" style="display:grid;grid-template-columns:1fr 1fr;gap:10px;"></div>
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
function bindCustom(inputId, btnId, cb){
  $(btnId).addEventListener('click', function(){
    var v = parseInt($(inputId).value);
    if (!v || v < 1){ showAlert('Введи ставку больше 0'); return; }
    if (v > balance){ showAlert('Недостаточно средств'); return; }
    cb(v);
  });
}

var menuMap = {
  'btn-roulette':'roulette','btn-blackjack':'blackjack','btn-poker':'poker','btn-baccarat':'baccarat',
  'btn-craps':'craps','btn-crash':'crash','btn-mines':'mines','btn-slots':'slots','btn-hilo':'hilo',
  'btn-fortune':'fortune','btn-ladder':'ladder','btn-dice3':'dice3','btn-war':'war','btn-sicbo':'sicbo',
  'btn-keno':'keno','btn-21plus':'twentyone','btn-inv':'inv'
};
for (var k in menuMap){(function(sid){
  var b = $(k); if (b) b.addEventListener('click', function(){ showScreen(sid); initGame(sid); });
})(menuMap[k]);}
['roulette','blackjack','poker','baccarat','craps','crash','mines','slots','hilo','fortune','ladder','dice3','war','sicbo','keno','twentyone','inv'].forEach(function(id){
  var b = $('back-'+id); if (b) b.addEventListener('click', goMenu);
});
function initGame(id){
  if (id==='roulette') initRoulette();
  if (id==='blackjack') initBJ();
  if (id==='poker') initPoker();
  if (id==='baccarat') initBaccarat();
  if (id==='craps') initCraps();
  if (id==='crash') initCrash();
  if (id==='mines') initMines();
  if (id==='slots') initSlots();
  if (id==='hilo') initHilo();
  if (id==='fortune') initFortune();
  if (id==='ladder') initLadder();
  if (id==='dice3') initDice3();
  if (id==='war') initWar();
  if (id==='sicbo') initSicbo();
  if (id==='keno') initKeno();
  if (id==='twentyone') initBJ21();
  if (id==='inv') renderInv();
}

// Рулетка (сокращённая, как была)
var REDS=[1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36];
var roulettePick={type:null,value:null};
var rouletteHistory=[], rouletteBusy=false;
function rouletteColorOf(n){ if(n===0)return 'green'; return REDS.indexOf(n)>=0?'red':'black'; }
function initRoulette(){
  rouletteBusy=false; roulettePick={type:null,value:null};
  buildRouletteWheel(); buildRouletteNumbers();
  $('roulette-status').textContent='СДЕЛАЙ СТАВКУ';
  $('roulette-ball').style.display='none'; $('roulette-center').textContent='SPIN';
  $('roulette-wheel').style.transform='rotate(0deg)';
  makeBetButtons('roulette-buttons', playRoulette);
  bindCustom('custom-roulette','custom-roulette-go', playRoulette);
  var outs=document.querySelectorAll('[data-rl]');
  for(var i=0;i<outs.length;i++){(function(b){
    b.onclick=function(){
      var t=b.getAttribute('data-rl');
      roulettePick={type:'outside',value:t};
      for(var j=0;j<outs.length;j++) outs[j].classList.remove('sel');
      b.classList.add('sel');
      $('roulette-status').textContent='ВЫБРАНО: '+b.textContent+' | ВЫБЕРИ СТАВКУ';
    };
  })(outs[i]);}
}
function buildRouletteWheel(){
  var wheel=$('roulette-wheel');
  var order=[0,32,15,19,4,21,2,25,17,34,6,27,13,36,11,30,8,23,10,5,24,16,33,1,20,14,31,9,22,18,29,7,28,12,35,3,26];
  wheel.innerHTML='';
  for(var i=0;i<37;i++){
    var n=order[i]; var ang=(360/37)*i; var color=rouletteColorOf(n);
    var bg=color==='green'?'#0a5a2a':(color==='red'?'#8a1a2a':'#0a0a0a');
    var seg=document.createElement('div'); seg.className='roulette-seg';
    seg.style.background=bg; seg.style.transform='rotate('+ang+'deg)'; seg.textContent=n;
    wheel.appendChild(seg);
  }
}
function buildRouletteNumbers(){
  var cont=$('roulette-numbers'); cont.innerHTML='';
  var z=document.createElement('div'); z.className='rn green'; z.textContent='0'; z.style.gridColumn='span 6';
  z.addEventListener('click',function(){ roulettePick={type:'number',value:0}; var rns=document.querySelectorAll('.rn'); for(var j=0;j<rns.length;j++) rns[j].classList.remove('selected'); z.classList.add('selected'); $('roulette-status').textContent='ВЫБРАНО: 0 (x35) | ВЫБЕРИ СТАВКУ'; });
  cont.appendChild(z);
  for(var n=1;n<=36;n++){
    var d=document.createElement('div'); d.className='rn '+rouletteColorOf(n); d.textContent=n;
    (function(num){ d.addEventListener('click',function(){ roulettePick={type:'number',value:num}; var rns=document.querySelectorAll('.rn'); for(var j=0;j<rns.length;j++) rns[j].classList.remove('selected'); d.classList.add('selected'); $('roulette-status').textContent='ВЫБРАНО: '+num+' (x35) | ВЫБЕРИ СТАВКУ'; }); })(n);
    cont.appendChild(d);
  }
}
function playRoulette(bet){
  if(rouletteBusy) return;
  if(!roulettePick.type){ showAlert('Сделай ставку'); return; }
  if(bet>balance){ showAlert('Недостаточно'); return; }
  rouletteBusy=true;
  changeBalance(-bet).then(function(){
    $('roulette-buttons').innerHTML='';
    $('roulette-status').textContent='🎡 КРУТИМ...';
    var result=Math.floor(Math.random()*37);
    var order=[0,32,15,19,4,21,2,25,17,34,6,27,13,36,11,30,8,23,10,5,24,16,33,1,20,14,31,9,22,18,29,7,28,12,35,3,26];
    var idx=order.indexOf(result);
    var wheel=$('roulette-wheel');
    wheel.style.transition='transform 8s cubic-bezier(.1,.8,.2,1)';
    wheel.style.transform='rotate('+(360*15-idx*(360/37))+'deg)';
    var ball=$('roulette-ball'); ball.style.display='block';
    var cx=150,cy=150,r=130,step=0,total=100;
    var anim=setInterval(function(){
      step++;
      var a=(step*30)*Math.PI/180;
      var rad=r-(step/total)*(r-95);
      ball.style.left=(cx+Math.cos(a)*rad)+'px';
      ball.style.top=(cy+Math.sin(a)*rad)+'px';
      if(step>=total){ clearInterval(anim); setTimeout(function(){ ball.style.display='none'; finishRoulette(result,bet); },800); }
    },30);
  });
}
function finishRoulette(result,bet){
  var color=rouletteColorOf(result);
  rouletteHistory.unshift(result); if(rouletteHistory.length>12) rouletteHistory.pop();
  renderRouletteHistory();
  var mult=0, p=roulettePick;
  if(p.type==='number'){ if(result===p.value) mult=35; }
  else { var v=p.value;
    if(v==='red'&&color==='red') mult=2; else if(v==='black'&&color==='black') mult=2;
    else if(v==='green'&&result===0) mult=35;
    else if(v==='even'&&result!==0&&result%2===0) mult=2; else if(v==='odd'&&result%2===1) mult=2;
    else if(v==='low'&&result>=1&&result<=18) mult=2; else if(v==='high'&&result>=19) mult=2;
    else if(v==='dozen1'&&result>=1&&result<=12) mult=3; else if(v==='dozen2'&&result>=13&&result<=24) mult=3;
    else if(v==='dozen3'&&result>=25&&result<=36) mult=3;
  }
  var win=Math.floor(bet*mult);
  var cn=color==='red'?'🔴':(color==='black'?'⚫':'🟢');
  var done=function(){
    $('roulette-status').textContent=cn+' ВЫПАЛО: '+result+' → '+(win?'🎉 +'+fmt(win)+' ₽ (x'+mult+')':'❌ МИМО');
    if(mult>=5) maybeGiveNft(mult);
    $('roulette-center').textContent='SPIN'; rouletteBusy=false;
    setTimeout(initRoulette,4000);
  };
  if(win>0) changeBalance(win).then(done); else done();
}
function renderRouletteHistory(){
  var h=$('roulette-history'); h.innerHTML='';
  for(var i=0;i<rouletteHistory.length;i++){ var b=document.createElement('div'); b.className='hist-ball '+rouletteColorOf(rouletteHistory[i]); b.textContent=rouletteHistory[i]; h.appendChild(b); }
}

// Карточные утилиты
function newCard(){
  var v=['A','2','3','4','5','6','7','8','9','10','J','Q','K'];
  var s=['♠','♥','♦','♣'];
  var vv=v[Math.floor(Math.random()*v.length)], ss=s[Math.floor(Math.random()*s.length)];
  return {v:vv,s:ss,red:(ss==='♥'||ss==='♦')};
}
function cardVal(c){ if(c.v==='A')return 11; if(['K','Q','J'].indexOf(c.v)>=0)return 10; return parseInt(c.v); }

// Блэкджек
var bjBet=0,bjActive=false,bjP=[],bjD=[],bjDoubled=false;
function bjSum(arr){ var sum=0,aces=0; for(var i=0;i<arr.length;i++){sum+=cardVal(arr[i]);if(arr[i].v==='A')aces++;} while(sum>21&&aces>0){sum-=10;aces--;} return sum; }
function renderHand(id,cards,hide){ var html=''; for(var i=0;i<cards.length;i++){ if(hide&&i===1){ html+='<div class="card card-big" style="background:linear-gradient(135deg,#1a0a2a,#d4af37);color:#ffdd44;">?</div>'; continue;} var c=cards[i]; html+='<div class="card card-big'+(c.red?' red':'')+'">'+c.v+'<div style="font-size:18px;">'+c.s+'</div></div>'; } $(id).innerHTML=html; }
function initBJ(){
  bjBet=0;bjActive=false;bjP=[];bjD=[];bjDoubled=false;
  $('bj-dealer').innerHTML='';$('bj-player').innerHTML='';
  $('bj-dscore').textContent='0';$('bj-pscore').textContent='0';
  $('bj-status').textContent='ВЫБЕРИ СТАВКУ';
  $('bj-buttons').style.display='grid';$('bj-actions').style.display='none';
  makeBetButtons('bj-buttons',startBJ); bindCustom('custom-bj','custom-bj-go',startBJ);
}
function startBJ(bet){
  if(bet>balance){ showAlert('Недостаточно'); return; }
  bjBet=bet;bjActive=true;bjDoubled=false;
  changeBalance(-bet).then(function(){
    bjP=[newCard(),newCard()];bjD=[newCard(),newCard()];
    renderHand('bj-player',bjP,false);renderHand('bj-dealer',bjD,true);
    $('bj-pscore').textContent=bjSum(bjP);$('bj-dscore').textContent=cardVal(bjD[0]);
    $('bj-buttons').style.display='none';$('bj-actions').style.display='grid';
    $('bj-status').textContent='ТВОЙ ХОД';
    if(bjSum(bjP)===21) setTimeout(function(){bjStand();},500);
  });
}
$('bj-hit').addEventListener('click',function(){
  if(!bjActive)return; bjP.push(newCard()); renderHand('bj-player',bjP,false); $('bj-pscore').textContent=bjSum(bjP);
  if(bjSum(bjP)>21){ bjActive=false; $('bj-status').textContent='💥 ПЕРЕБОР -'+fmt(bjBet)+' ₽'; $('bj-actions').style.display='none'; setTimeout(initBJ,3000); }
});
$('bj-stand').addEventListener('click',function(){bjStand();});
function bjStand(){
  if(!bjActive)return; bjActive=false;
  var d=bjSum(bjD),p=bjSum(bjP);
  while(d<17){ bjD.push(newCard()); d=bjSum(bjD); }
  renderHand('bj-dealer',bjD,false); $('bj-dscore').textContent=d;
  var finalBet=bjDoubled?bjBet*2:bjBet;
  if(d>21||p>d){ var win=Math.floor(finalBet*2); changeBalance(win).then(function(){ $('bj-status').textContent='🎉 ПОБЕДА +'+fmt(win)+' ₽'; if(p===21&&bjP.length===2) maybeGiveNft(5); setTimeout(initBJ,3000); }); }
  else if(p===d){ changeBalance(finalBet).then(function(){ $('bj-status').textContent='НИЧЬЯ'; setTimeout(initBJ,3000); }); }
  else { $('bj-status').textContent='ПРОИГРАЛ -'+fmt(finalBet)+' ₽'; setTimeout(initBJ,3000); }
  $('bj-actions').style.display='none';
}
$('bj-double').addEventListener('click',function(){
  if(!bjActive||bjP.length!==2)return;
  if(bjBet>balance){ showAlert('Недостаточно'); return; }
  changeBalance(-bjBet).then(function(){
    bjDoubled=true; bjP.push(newCard()); renderHand('bj-player',bjP,false); $('bj-pscore').textContent=bjSum(bjP);
    if(bjSum(bjP)>21){ bjActive=false; $('bj-status').textContent='💥 ПЕРЕБОР -'+fmt(bjBet*2)+' ₽'; $('bj-actions').style.display='none'; setTimeout(initBJ,3000); }
    else setTimeout(bjStand,300);
  });
});

// Покер vs ИИ
var pokerBet=0,pokerActive=false,pokerMode='medium',pokerPot=0,pokerMyHand=[],pokerAIHand=[],pokerTableCards=[],pokerStage=0;
function drawCard(){ return newCard(); }
function renderPokerCard(c){ return '<div class="card card-small'+(c.red?' red':'')+'">'+c.v+'<div style="font-size:14px;">'+c.s+'</div></div>'; }
function initPoker(){
  pokerBet=0;pokerActive=false;pokerPot=0;pokerStage=0;
  pokerMyHand=[];pokerAIHand=[];pokerTableCards=[];
  $('poker-status').textContent='ВЫБЕРИ РЕЖИМ И СТАВКУ';
  $('poker-my').innerHTML='';$('poker-ai').innerHTML='';$('poker-table-cards').innerHTML='';
  $('poker-pot').textContent='БАНК: 0 ₽'; $('poker-ai-name').textContent='Ожидание';
  $('poker-actions').style.display='none'; $('poker-buttons').innerHTML='';
  makeBetButtons('poker-buttons',startPoker);
  bindCustom('custom-poker','custom-poker-go',startPoker);
  var modes=document.querySelectorAll('[data-mode]');
  for(var i=0;i<modes.length;i++){(function(b){
    b.addEventListener('click',function(){
      pokerMode=b.getAttribute('data-mode');
      for(var j=0;j<modes.length;j++) modes[j].style.outline='';
      b.style.outline='2px solid #ffdd44';
      $('poker-status').textContent='РЕЖИМ: '+pokerMode.toUpperCase()+' | ВЫБЕРИ СТАВКУ';
    });
  })(modes[i]);}
}
function startPoker(bet){
  if(bet>balance){ showAlert('Недостаточно'); return; }
  pokerBet=bet;pokerActive=true;pokerPot=bet*2;pokerStage=0;
  changeBalance(-bet).then(function(){
    pokerMyHand=[newCard(),newCard()]; pokerAIHand=[newCard(),newCard()]; pokerTableCards=[];
    $('poker-my').innerHTML=pokerMyHand.map(renderPokerCard).join('');
    $('poker-ai').innerHTML='<div class="card card-small" style="background:linear-gradient(135deg,#1a0a2a,#d4af37);color:#ffdd44;">?</div><div class="card card-small" style="background:linear-gradient(135deg,#1a0a2a,#d4af37);color:#ffdd44;">?</div>';
    $('poker-table-cards').innerHTML='';
    $('poker-pot').textContent='БАНК: '+fmt(pokerPot)+' ₽';
    $('poker-buttons').innerHTML=''; $('poker-actions').style.display='grid';
    $('poker-status').textContent='ТВОЙ ХОД'; $('poker-ai-name').textContent='ИИ ('+pokerMode+')';
  });
}
function revealFlop(){ for(var i=0;i<3;i++) pokerTableCards.push(newCard()); $('poker-table-cards').innerHTML=pokerTableCards.map(renderPokerCard).join(''); pokerStage=1; }
$('poker-check').addEventListener('click',function(){
  if(!pokerActive)return;
  if(pokerStage===0){ revealFlop(); $('poker-status').textContent='ФЛОП. ТВОЙ ХОД'; }
  else if(pokerStage===1){ pokerTableCards.push(newCard()); $('poker-table-cards').innerHTML=pokerTableCards.map(renderPokerCard).join(''); pokerStage=2; $('poker-status').textContent='ТЁРН. ТВОЙ ХОД'; }
  else if(pokerStage===2){ pokerTableCards.push(newCard()); $('poker-table-cards').innerHTML=pokerTableCards.map(renderPokerCard).join(''); pokerStage=3; setTimeout(showdown,800); }
});
$('poker-raise').addEventListener('click',function(){
  if(!pokerActive)return;
  if(pokerBet>balance){ showAlert('Недостаточно'); return; }
  changeBalance(-pokerBet).then(function(){
    pokerPot+=pokerBet*2; $('poker-pot').textContent='БАНК: '+fmt(pokerPot)+' ₽';
    if(pokerStage===0){ revealFlop(); pokerStage=1; }
    else if(pokerStage===1){ pokerTableCards.push(newCard()); $('poker-table-cards').innerHTML=pokerTableCards.map(renderPokerCard).join(''); pokerStage=2; }
    else if(pokerStage===2){ pokerTableCards.push(newCard()); $('poker-table-cards').innerHTML=pokerTableCards.map(renderPokerCard).join(''); pokerStage=3; setTimeout(showdown,800); }
    else { setTimeout(showdown,300); }
  });
});
$('poker-fold').addEventListener('click',function(){
  if(!pokerActive)return; pokerActive=false;
  $('poker-actions').style.display='none'; $('poker-status').textContent='ФОЛД. -'+fmt(pokerBet)+' ₽';
  setTimeout(initPoker,3000);
});
function handStrength(cards){
  var vals=cards.map(function(c){ return ['2','3','4','5','6','7','8','9','10','J','Q','K','A'].indexOf(c.v); });
  var suits=cards.map(function(c){ return c.s; });
  vals.sort(function(a,b){return a-b;});
  var flush=suits.every(function(s){ return s===suits[0]; });
  var straight=true;
  for(var i=1;i<vals.length;i++) if(vals[i]!==vals[i-1]+1) straight=false;
  var counts={}; vals.forEach(function(v){counts[v]=(counts[v]||0)+1;});
  var maxC=0; for(var k in counts) if(counts[k]>maxC) maxC=counts[k];
  if(flush&&straight&&vals[0]===8) return 10;
  if(flush&&straight) return 9;
  if(maxC===4) return 8;
  if(maxC===3&&Object.keys(counts).length===2) return 7;
  if(flush) return 6;
  if(straight) return 5;
  if(maxC===3) return 4;
  if(maxC===2&&Object.keys(counts).length===3) return 3;
  if(maxC===2) return 2;
  return vals[vals.length-1];
}
function showdown(){
  pokerActive=false; $('poker-actions').style.display='none';
  $('poker-ai').innerHTML=pokerAIHand.map(renderPokerCard).join('');
  var myAll=pokerMyHand.concat(pokerTableCards), aiAll=pokerAIHand.concat(pokerTableCards);
  var myS=handStrength(myAll), aiS=handStrength(aiAll);
  var aiBoost=pokerMode==='hard'?2:(pokerMode==='easy'?-1:0); aiS+=aiBoost;
  var name=function(s){ if(s>=10)return 'РОЯЛ'; if(s>=9)return 'СТРИТ-ФЛЕШ'; if(s>=8)return 'КАРЕ'; if(s>=7)return 'ФУЛЛ'; if(s>=6)return 'ФЛЕШ'; if(s>=5)return 'СТРИТ'; if(s>=4)return 'СЕТ'; if(s>=3)return '2 ПАРЫ'; if(s>=2)return 'ПАРА'; return 'СТАРШАЯ'; };
  if(myS>aiS){ changeBalance(pokerPot).then(function(){ $('poker-status').textContent='🎉 ТЫ ВЫИГРАЛ '+name(myS)+' vs '+name(aiS)+'! +'+fmt(pokerPot)+' ₽'; if(pokerPot>=10000) maybeGiveNft(5); setTimeout(initPoker,4000); }); }
  else if(myS===aiS){ changeBalance(Math.floor(pokerPot/2)).then(function(){ $('poker-status').textContent='НИЧЬЯ ('+name(myS)+')'; setTimeout(initPoker,3000); }); }
  else { $('poker-status').textContent='❌ ПРОИГРАЛ. ИИ: '+name(aiS)+' vs '+name(myS); setTimeout(initPoker,4000); }
}

// Баккара
var bacPick='';
function bacCard(){ var v=[1,2,3,4,5,6,7,8,9,0,0,0,0]; return v[Math.floor(Math.random()*v.length)]; }
function bacSum(arr){ return arr.reduce(function(a,b){return (a+b)%10;},0); }
function initBaccarat(){
  bacPick='';
  $('bac-player').innerHTML='';$('bac-banker').innerHTML='';
  $('bac-pscore').textContent='0';$('bac-bscore').textContent='0';
  $('bac-status').textContent='ВЫБЕРИ СТАВКУ';
  makeBetButtons('bac-buttons',playBaccarat); bindCustom('custom-bac','custom-bac-go',playBaccarat);
  var btns=document.querySelectorAll('[data-bac]');
  for(var i=0;i<btns.length;i++){(function(b){
    b.addEventListener('click',function(){ bacPick=b.getAttribute('data-bac'); for(var j=0;j<btns.length;j++) btns[j].style.outline=''; b.style.outline='2px solid #ffdd44'; $('bac-status').textContent='ВЫБРАНО: '+bacPick+' | ВЫБЕРИ СТАВКУ'; });
  })(btns[i]);}
}
function playBaccarat(bet){
  if(!bacPick){ showAlert('Выбери'); return; }
  if(bet>balance){ showAlert('Недостаточно'); return; }
  changeBalance(-bet).then(function(){
    $('bac-buttons').innerHTML=''; $('bac-status').textContent='РАЗДАЧА...';
    var p=[bacCard(),bacCard()], b=[bacCard(),bacCard()];
    var rb=function(id,cards){ var h=''; for(var i=0;i<cards.length;i++) h+='<div class="card card-big">'+cards[i]+'</div>'; $(id).innerHTML=h; };
    rb('bac-player',p); rb('bac-banker',b);
    $('bac-pscore').textContent=bacSum(p);$('bac-bscore').textContent=bacSum(b);
    setTimeout(function(){
      if(bacSum(p)<=5) p.push(bacCard());
      if(bacSum(b)<=5) b.push(bacCard());
      rb('bac-player',p); rb('bac-banker',b);
      var ps=bacSum(p),bs=bacSum(b);
      $('bac-pscore').textContent=ps;$('bac-bscore').textContent=bs;
      var w=(ps>bs)?'P':(bs>ps?'B':'T');
      var mult=0; if(bacPick===w){ if(w==='P')mult=2; else if(w==='B')mult=1.95; else mult=8; }
      var win=Math.floor(bet*mult);
      var done=function(){ $('bac-status').textContent='ПОБЕДА: '+w+' → '+(win?'+'+fmt(win)+' ₽':'МИМО'); if(mult>=5) maybeGiveNft(mult); setTimeout(initBaccarat,3000); };
      if(win>0) changeBalance(win).then(done); else done();
    },800);
  });
}

// Крапс
function initCraps(){
  $('craps-status').textContent='ВЫБЕРИ СТАВКУ'; $('die1').textContent='⚀'; $('die2').textContent='⚀';
  makeBetButtons('craps-buttons',playCraps); bindCustom('custom-craps','custom-craps-go',playCraps);
}
function playCraps(bet){
  if(bet>balance){ showAlert('Недостаточно'); return; }
  changeBalance(-bet).then(function(){
    $('craps-buttons').innerHTML=''; $('craps-status').textContent='БРОСАЕМ...';
    var faces=['⚀','⚁','⚂','⚃','⚄','⚅'];
    var d1=Math.floor(Math.random()*6)+1,d2=Math.floor(Math.random()*6)+1,c=0;
    var anim=setInterval(function(){ $('die1').textContent=faces[Math.floor(Math.random()*6)]; $('die2').textContent=faces[Math.floor(Math.random()*6)]; c++; if(c>10){ clearInterval(anim); $('die1').textContent=faces[d1-1]; $('die2').textContent=faces[d2-1]; var t=d1+d2,mult=0; if(t===7||t===11)mult=2; else if(t===2||t===3||t===12)mult=0; else if(t===4||t===10)mult=1.5; else if(t===5||t===9)mult=1.2; else if(t===6||t===8)mult=1; var win=Math.floor(bet*mult); var done=function(){ $('craps-status').textContent='СУММА '+t+' → '+(win?'+'+fmt(win)+' ₽':'ПРОИГРАЛ'); if(mult>=2) maybeGiveNft(mult); setTimeout(initCraps,3000); }; if(win>0) changeBalance(win).then(done); else done(); } },80);
  });
}

// Краш
var crashBet=0,crashRunning=false,crashMult=1,crashLoop=null,crashPoint=0;
function initCrash(){
  if(crashLoop){clearInterval(crashLoop);crashLoop=null;}
  crashBet=0;crashRunning=false;crashMult=1;
  $('crash-mult').textContent='x1.00';$('crash-mult').classList.remove('crashed');$('crash-line').style.width='0%';
  $('crash-status').textContent='ВЫБЕРИ СТАВКУ';$('crash-cashout').style.display='none';
  makeBetButtons('crash-buttons',startCrash); bindCustom('custom-crash','custom-crash-go',startCrash);
}
function startCrash(bet){
  if(bet>balance){ showAlert('Недостаточно'); return; }
  crashBet=bet;crashMult=1;crashRunning=true;crashPoint=1+Math.random()*Math.random()*20+0.3;
  changeBalance(-bet).then(function(){
    $('crash-buttons').innerHTML='';$('crash-cashout').style.display='block';$('crash-status').textContent='ЛЕТИМ!';
    crashLoop=setInterval(function(){
      crashMult=+(crashMult+0.05+Math.random()*0.1).toFixed(2);
      $('crash-mult').textContent='x'+crashMult.toFixed(2);
      $('crash-line').style.width=Math.min(100,(crashMult/20)*100)+'%';
      if(crashMult>=crashPoint){ crashRunning=false;clearInterval(crashLoop);crashLoop=null;$('crash-mult').classList.add('crashed');$('crash-status').textContent='💥 КРАХ x'+crashMult.toFixed(2)+'! -'+fmt(crashBet)+' ₽';$('crash-cashout').style.display='none';setTimeout(initCrash,3000); }
    },80);
  });
}
$('crash-cashout').addEventListener('click',function(){
  if(!crashRunning)return;crashRunning=false;clearInterval(crashLoop);crashLoop=null;
  var win=Math.floor(crashBet*crashMult);
  changeBalance(win).then(function(){ $('crash-status').textContent='💰 +'+fmt(win)+' ₽ (x'+crashMult.toFixed(2)+')';$('crash-cashout').style.display='none';if(crashMult>=3) maybeGiveNft(crashMult);setTimeout(initCrash,3000); });
});

// Мины
var minesBet=0,minesField=[],minesOpened=0,minesMult=1,minesActive=false,minesCount=3;
function initMines(){
  minesBet=0;minesField=[];minesOpened=0;minesMult=1;minesActive=false;minesCount=3;
  $('mines-status').textContent='ВЫБЕРИ СТАВКУ';$('mines-grid').innerHTML='';$('mines-cashout').style.display='none';
  makeBetButtons('mines-buttons',startMines); bindCustom('custom-mines','custom-mines-go',startMines);
  var lvls=document.querySelectorAll('[data-mines]');
  for(var i=0;i<lvls.length;i++){(function(b){
    b.addEventListener('click',function(){ minesCount=parseInt(b.getAttribute('data-mines'));for(var j=0;j<lvls.length;j++) lvls[j].style.outline='';b.style.outline='2px solid #ffdd44';$('mines-status').textContent=minesCount+' МИН | ВЫБЕРИ СТАВКУ'; });
  })(lvls[i]);}
}
function startMines(bet){
  if(bet>balance){ showAlert('Недостаточно'); return; }
  if(minesActive) return;
  minesBet=bet;minesOpened=0;minesMult=1;minesActive=true;
  changeBalance(-bet).then(function(){
    $('mines-buttons').innerHTML='';$('mines-cashout').style.display='block';
    minesField=[];
    for(var i=0;i<25-minesCount;i++) minesField.push('gem');
    for(var i=0;i<minesCount;i++) minesField.push('mine');
    for(var i=minesField.length-1;i>0;i--){ var j=Math.floor(Math.random()*(i+1));var t=minesField[i];minesField[i]=minesField[j];minesField[j]=t; }
    var c=$('mines-grid');c.innerHTML='';
    for(var i=0;i<25;i++){(function(idx){ var cell=document.createElement('div');cell.className='mine-cell';cell.addEventListener('click',function(){openMine(idx,cell);});c.appendChild(cell); })(i);}
    $('mines-status').textContent=minesCount+' МИН | x'+minesMult.toFixed(2);
  });
}
function openMine(i,cell){
  if(!minesActive||cell.classList.contains('opened')) return;
  cell.classList.add('opened');
  if(minesField[i]==='mine'){ cell.classList.add('mine');cell.textContent='💥';minesActive=false;$('mines-status').textContent='💣 БУМ! -'+fmt(minesBet)+' ₽';$('mines-cashout').style.display='none'; var cells=document.querySelectorAll('#mines-grid .mine-cell');for(var k=0;k<minesField.length;k++) if(minesField[k]==='mine') cells[k].textContent='💣';setTimeout(initMines,3000);return; }
  cell.textContent='💎';minesOpened++;minesMult=+(1+minesOpened*(minesCount*0.15+0.2)).toFixed(2);
  $('mines-status').textContent='x'+minesMult.toFixed(2)+' | 💰 '+fmt(Math.floor(minesBet*minesMult))+' ₽';
}
$('mines-cashout').addEventListener('click',function(){
  if(!minesActive)return;minesActive=false;
  var win=Math.floor(minesBet*minesMult);
  changeBalance(win).then(function(){ $('mines-cashout').style.display='none';$('mines-status').textContent='💰 +'+fmt(win)+' ₽';if(minesMult>=3) maybeGiveNft(minesMult);setTimeout(initMines,3000); });
});

// Слоты
var slotsBusy=false;
function initSlots(){
  slotsBusy=false;$('slots-status').textContent='ВЫБЕРИ СТАВКУ';
  for(var i=0;i<6;i++) $('s'+i).textContent='🍒';
  makeBetButtons('slots-buttons',playSlots); bindCustom('custom-slots','custom-slots-go',playSlots);
}
function playSlots(bet){
  if(slotsBusy)return; if(bet>balance){ showAlert('Недостаточно'); return; }
  slotsBusy=true;
  changeBalance(-bet).then(function(){
    var syms=['🍒','🍋','🍊','💎','7️⃣','⭐','🔔'];
    $('slots-buttons').innerHTML='';$('slots-status').textContent='КРУТИМ...';
    for(var i=0;i<6;i++) $('s'+i).classList.add('spin');
    var final=[];for(var i=0;i<6;i++) final.push(syms[Math.floor(Math.random()*syms.length)]);
    var fin=0;
    for(var i=0;i<6;i++){(function(idx){ setTimeout(function(){ $('s'+idx).classList.remove('spin');$('s'+idx).textContent=final[idx];fin++; if(fin===6){ var mult=0; for(var row=0;row<2;row++){ var a=final[row*3],b=final[row*3+1],c=final[row*3+2]; if(a===b&&b===c){ var m=a==='7️⃣'?20:(a==='💎'?10:(a==='⭐'?8:(a==='🔔'?5:3)));if(m>mult)mult=m; } if(a===b||b===c||a===c){ if(2>mult)mult=2; } } var win=Math.floor(bet*mult); var done=function(){ $('slots-status').textContent=mult?('🎉 +'+fmt(win)+' ₽ (x'+mult+')'):'НЕ ПОВЕЗЛО';if(mult>=3) maybeGiveNft(mult);slotsBusy=false;setTimeout(initSlots,2500); }; if(win>0) changeBalance(win).then(done); else done(); } },700+idx*180); })(i);}
  });
}

// Хай-Лоу
var hiloBet=0,hiloActive=false,hiloCard=null,hiloStreak=0,hiloMult=1;
function initHilo(){
  hiloBet=0;hiloActive=false;hiloCard=null;hiloStreak=0;hiloMult=1;
  $('hilo-status').textContent='ВЫБЕРИ СТАВКУ';$('hilo-cards').innerHTML='';$('hilo-actions').style.display='none';$('hilo-cashout').style.display='none';
  makeBetButtons('hilo-buttons',startHilo); bindCustom('custom-hilo','custom-hilo-go',startHilo);
}
function rankOf(c){ return ['2','3','4','5','6','7','8','9','10','J','Q','K','A'].indexOf(c.v); }
function startHilo(bet){
  if(bet>balance){ showAlert('Недостаточно'); return; }
  hiloBet=bet;hiloActive=true;hiloStreak=0;hiloMult=1;
  changeBalance(-bet).then(function(){
    hiloCard=newCard();$('hilo-cards').innerHTML='<div class="card card-big'+(hiloCard.red?' red':'')+'">'+hiloCard.v+'<div style="font-size:18px;">'+hiloCard.s+'</div></div>';
    $('hilo-buttons').innerHTML='';$('hilo-actions').style.display='grid';$('hilo-cashout').style.display='block';$('hilo-status').textContent='БОЛЬШЕ ИЛИ МЕНЬШЕ?';
  });
}
var hiloBtns=document.querySelectorAll('[data-hilo]');
for(var i=0;i<hiloBtns.length;i++){(function(b){
  b.addEventListener('click',function(){
    if(!hiloActive)return;
    var guess=b.getAttribute('data-hilo');var next=newCard();
    $('hilo-cards').innerHTML+='<div class="card card-big'+(next.red?' red':'')+'">'+next.v+'<div style="font-size:18px;">'+next.s+'</div></div>';
    var cur=rankOf(hiloCard),nxt=rankOf(next);
    var correct=(guess==='higher'&&nxt>cur)||(guess==='lower'&&nxt<cur);
    if(correct){ hiloStreak++;hiloMult=+(1+hiloStreak*0.7).toFixed(2);hiloCard=next;var pot=Math.floor(hiloBet*hiloMult);$('hilo-status').textContent='✅ x'+hiloMult.toFixed(2)+' | '+fmt(pot)+' ₽'; }
    else { hiloActive=false;$('hilo-status').textContent='❌ НЕ УГАДАЛ! -'+fmt(hiloBet)+' ₽';$('hilo-actions').style.display='none';$('hilo-cashout').style.display='none';setTimeout(initHilo,3000); }
  });
})(hiloBtns[i]);}
$('hilo-cashout').addEventListener('click',function(){
  if(!hiloActive)return;hiloActive=false;
  var win=Math.floor(hiloBet*hiloMult);
  changeBalance(win).then(function(){ $('hilo-cashout').style.display='none';$('hilo-actions').style.display='none';$('hilo-status').textContent='💰 +'+fmt(win)+' ₽';if(hiloMult>=3) maybeGiveNft(hiloMult);setTimeout(initHilo,3000); });
});

// Колесо фортуны (усилено)
var fortuneBusy=false;
function initFortune(){
  fortuneBusy=false;
  var wheel=$('fortune-wheel');wheel.innerHTML='';
  var prizes=[0,1.5,2,3,5,0,10,2,1.5,25,0,100];
  for(var i=0;i<prizes.length;i++){
    var ang=(360/prizes.length)*i;var seg=document.createElement('div');seg.className='wheel-seg';
    var color=prizes[i]===0?'#3a0a0a':(prizes[i]>=10?'#8a6a1a':(prizes[i]>=5?'#6a2a0a':'#2a1a4a'));
    seg.style.background=color;seg.style.transform='rotate('+ang+'deg)';seg.textContent=prizes[i]?'x'+prizes[i]:'0';
    wheel.appendChild(seg);
  }
  window._fp=prizes;
  $('fortune-status').textContent='ВЫБЕРИ СТАВКУ';
  makeBetButtons('fortune-buttons',playFortune); bindCustom('custom-fortune','custom-fortune-go',playFortune);
}
function playFortune(bet){
  if(fortuneBusy)return;if(bet>balance){ showAlert('Недостаточно'); return; }
  fortuneBusy=true;
  changeBalance(-bet).then(function(){
    $('fortune-buttons').innerHTML='';$('fortune-status').textContent='КРУТИМ...';
    var prizes=window._fp;var idx=Math.floor(Math.random()*prizes.length);
    var wheel=$('fortune-wheel');
    wheel.style.transform='rotate('+(360*10+idx*(360/prizes.length))+'deg)';
    setTimeout(function(){
      var mult=prizes[idx];var win=Math.floor(bet*mult);
      var done=function(){ $('fortune-status').textContent='ВЫПАЛО x'+mult+' → '+(win?'+'+fmt(win)+' ₽':'ПУСТО');if(mult>=5) maybeGiveNft(mult);fortuneBusy=false;setTimeout(initFortune,3000); };
      if(win>0) changeBalance(win).then(done); else done();
    },6200);
  });
}

// ЛЕСТНИЦА
var ladderBet=0,ladderLevel=0,ladderActive=false;
function initLadder(){
  ladderBet=0;ladderLevel=0;ladderActive=false;
  var stage=$('ladder-stage');stage.innerHTML='';
  var mults=[1.5,2,3,5,10,25,50];
  for(var i=mults.length-1;i>=0;i--){
    var d=document.createElement('div');d.className='ladder-level';d.id='lvl-'+i;
    d.textContent='ШАГ '+(i+1)+' → x'+mults[i];
    stage.appendChild(d);
  }
  $('ladder-status').textContent='ВЫБЕРИ СТАВКУ';
  $('ladder-next').style.display='none';$('ladder-cashout').style.display='none';
  makeBetButtons('ladder-buttons',startLadder); bindCustom('custom-ladder','custom-ladder-go',startLadder);
}
function startLadder(bet){
  if(bet>balance){ showAlert('Недостаточно'); return; }
  ladderBet=bet;ladderLevel=0;ladderActive=true;
  changeBalance(-bet).then(function(){
    $('ladder-buttons').innerHTML='';
    $('ladder-next').style.display='block';$('ladder-cashout').style.display='block';
    var st=$('lvl-0'); if(st) st.classList.add('active');
    $('ladder-status').textContent='ШАГ 1 | ВЫИГРЫШ x1.5';
  });
}
$('ladder-next').addEventListener('click',function(){
  if(!ladderActive)return;
  var chance=0.75-Math.min(0.4,ladderLevel*0.08);
  var mults=[1.5,2,3,5,10,25,50];
  if(ladderLevel>=mults.length-1){ changeBalance(Math.floor(ladderBet*mults[ladderLevel])).then(function(){ $('ladder-status').textContent='🏆 ПОБЕДИЛ! x'+mults[ladderLevel];ladderActive=false;$('ladder-next').style.display='none';$('ladder-cashout').style.display='none';maybeGiveNft(50);setTimeout(initLadder,3000); }); return; }
  if(Math.random()<chance){
    ladderLevel++;
    var el=$('lvl-'+ladderLevel); if(el){ el.classList.add('active'); }
    $('ladder-status').textContent='ШАГ '+(ladderLevel+1)+' | x'+mults[ladderLevel];
  } else {
    ladderActive=false;
    $('ladder-status').textContent='💥 УПАЛ! -'+fmt(ladderBet)+' ₽';
    $('ladder-next').style.display='none';$('ladder-cashout').style.display='none';
    setTimeout(initLadder,3000);
  }
});
$('ladder-cashout').addEventListener('click',function(){
  if(!ladderActive)return;ladderActive=false;
  var mults=[1.5,2,3,5,10,25,50];
  var win=Math.floor(ladderBet*mults[ladderLevel]);
  changeBalance(win).then(function(){ $('ladder-status').textContent='💰 +'+fmt(win)+' ₽ (x'+mults[ladderLevel]+')';$('ladder-next').style.display='none';$('ladder-cashout').style.display='none';if(mults[ladderLevel]>=5) maybeGiveNft(mults[ladderLevel]);setTimeout(initLadder,3000); });
});

// 3 КОСТИ
var dice3Pick='',dice3Busy=false;
function initDice3(){
  dice3Pick='';dice3Busy=false;
  $('d31').textContent='⚀';$('d32').textContent='⚀';$('d33').textContent='⚀';
  $('dice3-status').textContent='ВЫБЕРИ 4-10 ИЛИ 11-17';
  makeBetButtons('dice3-buttons',playDice3); bindCustom('custom-dice3','custom-dice3-go',playDice3);
  var btns=document.querySelectorAll('[data-d3]');
  for(var i=0;i<btns.length;i++){(function(b){
    b.addEventListener('click',function(){ dice3Pick=b.getAttribute('data-d3');for(var j=0;j<btns.length;j++) btns[j].style.outline='';b.style.outline='2px solid #ffdd44';$('dice3-status').textContent='ВЫБРАНО: '+b.textContent; });
  })(btns[i]);}
}
function playDice3(bet){
  if(dice3Busy)return;if(!dice3Pick){ showAlert('Выбери'); return; }
  if(bet>balance){ showAlert('Недостаточно'); return; }
  dice3Busy=true;
  changeBalance(-bet).then(function(){
    $('dice3-buttons').innerHTML='';$('dice3-status').textContent='БРОСАЕМ...';
    var faces=['⚀','⚁','⚂','⚃','⚄','⚅'];
    var r1=Math.floor(Math.random()*6)+1,r2=Math.floor(Math.random()*6)+1,r3=Math.floor(Math.random()*6)+1;
    var c=0;
    var anim=setInterval(function(){
      $('d31').textContent=faces[Math.floor(Math.random()*6)];
      $('d32').textContent=faces[Math.floor(Math.random()*6)];
      $('d33').textContent=faces[Math.floor(Math.random()*6)];
      c++;
      if(c>12){
        clearInterval(anim);
        $('d31').textContent=faces[r1-1];$('d32').textContent=faces[r2-1];$('d33').textContent=faces[r3-1];
        var sum=r1+r2+r3;
        var triple=(r1===r2&&r2===r3);
        var pair=(r1===r2||r2===r3||r1===r3)&&!triple;
        var mult=0;
        if(dice3Pick==='low'&&sum>=4&&sum<=10) mult=2;
        else if(dice3Pick==='mid'&&sum>=11&&sum<=17) mult=2;
        else if(dice3Pick==='triple'&&triple) mult=30;
        else if(dice3Pick==='pair'&&pair) mult=8;
        var win=Math.floor(bet*mult);
        var done=function(){ $('dice3-status').textContent='СУММА '+sum+' → '+(win?'+'+fmt(win)+' ₽ (x'+mult+')':'МИМО');if(mult>=5) maybeGiveNft(mult);dice3Busy=false;setTimeout(initDice3,3000); };
        if(win>0) changeBalance(win).then(done); else done();
      }
    },80);
  });
}

// ВОЙНА
var warBusy=false;
function initWar(){
  warBusy=false;
  $('war-ai').innerHTML='';$('war-my').innerHTML='';
  $('war-status').textContent='ВЫБЕРИ СТАВКУ';
  makeBetButtons('war-buttons',playWar); bindCustom('custom-war','custom-war-go',playWar);
}
function playWar(bet){
  if(warBusy)return;if(bet>balance){ showAlert('Недостаточно'); return; }
  warBusy=true;
  changeBalance(-bet).then(function(){
    $('war-buttons').innerHTML='';$('war-status').textContent='ВОЙНА...';
    var my=newCard(), ai=newCard();
    $('war-my').innerHTML='<div class="card card-big'+(my.red?' red':'')+'">'+my.v+'<div style="font-size:18px;">'+my.s+'</div></div>';
    $('war-ai').innerHTML='<div class="card card-big" style="background:linear-gradient(135deg,#1a0a2a,#d4af37);color:#ffdd44;">?</div>';
    setTimeout(function(){
      $('war-ai').innerHTML='<div class="card card-big'+(ai.red?' red':'')+'">'+ai.v+'<div style="font-size:18px;">'+ai.s+'</div></div>';
      var rk=function(c){ return ['2','3','4','5','6','7','8','9','10','J','Q','K','A'].indexOf(c.v); };
      var mr=rk(my),ar=rk(ai);
      var mult=0;
      if(mr>ar) mult=2;
      else if(mr===ar) mult=1;
      var win=Math.floor(bet*mult);
      var done=function(){ $('war-status').textContent=mr>ar?'🎉 ПОБЕДА +'+fmt(win)+' ₽':(mr===ar?'НИЧЬЯ':'❌ ПРОИГРАЛ -'+fmt(bet)+' ₽');if(mr>ar) maybeGiveNft(2);warBusy=false;setTimeout(initWar,3000); };
      if(win>0) changeBalance(win).then(done); else done();
    },1200);
  });
}

// СИК-БО
var sicboPick='',sicboBusy=false;
function initSicbo(){
  sicboPick='';sicboBusy=false;
  $('sb1').textContent='⚀';$('sb2').textContent='⚀';$('sb3').textContent='⚀';
  $('sicbo-status').textContent='ВЫБЕРИ СТАВКУ';
  makeBetButtons('sicbo-buttons',playSicbo); bindCustom('custom-sicbo','custom-sicbo-go',playSicbo);
  var btns=document.querySelectorAll('[data-sb]');
  for(var i=0;i<btns.length;i++){(function(b){
    b.addEventListener('click',function(){ sicboPick=b.getAttribute('data-sb');for(var j=0;j<btns.length;j++) btns[j].style.outline='';b.style.outline='2px solid #ffdd44';$('sicbo-status').textContent='ВЫБРАНО: '+b.textContent; });
  })(btns[i]);}
}
function playSicbo(bet){
  if(sicboBusy)return;if(!sicboPick){ showAlert('Выбери'); return; }
  if(bet>balance){ showAlert('Недостаточно'); return; }
  sicboBusy=true;
  changeBalance(-bet).then(function(){
    $('sicbo-buttons').innerHTML='';$('sicbo-status').textContent='БРОСАЕМ...';
    var faces=['⚀','⚁','⚂','⚃','⚄','⚅'];
    var r=[1,2,3].map(function(){return Math.floor(Math.random()*6)+1;});
    var c=0;
    var anim=setInterval(function(){
      $('sb1').textContent=faces[Math.floor(Math.random()*6)];
      $('sb2').textContent=faces[Math.floor(Math.random()*6)];
      $('sb3').textContent=faces[Math.floor(Math.random()*6)];
      c++;
      if(c>12){
        clearInterval(anim);
        $('sb1').textContent=faces[r[0]-1];$('sb2').textContent=faces[r[1]-1];$('sb3').textContent=faces[r[2]-1];
        var sum=r[0]+r[1]+r[2];
        var triple=(r[0]===r[1]&&r[1]===r[2]);
        var pair=(r[0]===r[1]||r[1]===r[2]||r[0]===r[2])&&!triple;
        var mult=0;
        if(sicboPick==='small'&&sum>=4&&sum<=10&&!triple) mult=2;
        else if(sicboPick==='big'&&sum>=11&&sum<=17&&!triple) mult=2;
        else if(sicboPick==='even'&&sum%2===0&&!triple) mult=2;
        else if(sicboPick==='odd'&&sum%2===1&&!triple) mult=2;
        else if(sicboPick==='one'&&(r[0]===1||r[1]===1||r[2]===1)) mult=3;
        else if(sicboPick==='pair'&&pair) mult=8;
        else if(sicboPick==='triple'&&triple) mult=30;
        else if(sicboPick==='total4'&&sum===4) mult=60;
        var win=Math.floor(bet*mult);
        var done=function(){ $('sicbo-status').textContent='СУММА '+sum+' → '+(win?'+'+fmt(win)+' ₽':'МИМО');if(mult>=5) maybeGiveNft(mult);sicboBusy=false;setTimeout(initSicbo,3000); };
        if(win>0) changeBalance(win).then(done); else done();
      }
    },80);
  });
}

// КЕНО
var kenoPicks=[],kenoBusy=false;
function initKeno(){
  kenoPicks=[];kenoBusy=false;
  $('keno-status').textContent='ВЫБЕРИ 5 ЧИСЕЛ (1-40)';
  var g=$('keno-grid');g.innerHTML='';
  for(var i=1;i<=40;i++){(function(n){
    var c=document.createElement('div');c.className='keno-cell';c.textContent=n;
    c.addEventListener('click',function(){
      if(kenoBusy)return;
      var idx=kenoPicks.indexOf(n);
      if(idx>=0){ kenoPicks.splice(idx,1);c.classList.remove('picked'); }
      else if(kenoPicks.length<5){ kenoPicks.push(n);c.classList.add('picked'); }
      $('keno-status').textContent='ВЫБРАНО: '+kenoPicks.length+'/5';
    });
    g.appendChild(c);
  })(i);}
  makeBetButtons('keno-buttons',playKeno); bindCustom('custom-keno','custom-keno-go',playKeno);
}
function playKeno(bet){
  if(kenoBusy)return;if(kenoPicks.length!==5){ showAlert('Выбери 5'); return; }
  if(bet>balance){ showAlert('Недостаточно'); return; }
  kenoBusy=true;
  changeBalance(-bet).then(function(){
    $('keno-buttons').innerHTML='';$('keno-status').textContent='РОЗЫГРЫШ...';
    var drawn=[];while(drawn.length<10){ var n=Math.floor(Math.random()*40)+1;if(drawn.indexOf(n)<0) drawn.push(n); }
    var cells=$('keno-grid').children;var step=0;
    var anim=setInterval(function(){
      if(step<10){ cells[drawn[step]-1].classList.add('hit');step++; }
      else {
        clearInterval(anim);
        var hits=0;for(var i=0;i<kenoPicks.length;i++) if(drawn.indexOf(kenoPicks[i])>=0) hits++;
        var mults={0:0,1:0,2:1,3:3,4:10,5:100};var mult=mults[hits]||0;var win=bet*mult;
        var done=function(){ $('keno-status').textContent='СОВПАЛО: '+hits+'/5 → '+(win?'+'+fmt(win)+' ₽':'МИМО');if(mult>=5) maybeGiveNft(mult);kenoBusy=false;setTimeout(initKeno,3000); };
        if(win>0) changeBalance(win).then(done); else done();
      }
    },250);
  });
}

// 21+3
var bj21Bet=0,bj21Active=false,bj21P=[],bj21D=[];
function initBJ21(){
  bj21Bet=0;bj21Active=false;bj21P=[];bj21D=[];
  $('bj21-dealer').innerHTML='';$('bj21-player').innerHTML='';
  $('bj21-dscore').textContent='0';$('bj21-pscore').textContent='0';
  $('bj21-status').textContent='ВЫБЕРИ СТАВКУ';$('bj21-actions').style.display='none';
  makeBetButtons('bj21-buttons',startBJ21); bindCustom('custom-bj21','custom-bj21-go',startBJ21);
}
function startBJ21(bet){
  if(bet>balance){ showAlert('Недостаточно'); return; }
  bj21Bet=bet;bj21Active=true;
  changeBalance(-bet).then(function(){
    bj21P=[newCard(),newCard()];bj21D=[newCard(),newCard()];
    renderHand('bj21-player',bj21P,false);renderHand('bj21-dealer',bj21D,true);
    $('bj21-pscore').textContent=bjSum(bj21P);$('bj21-dscore').textContent=cardVal(bj21D[0]);
    $('bj21-buttons').style.display='none';$('bj21-actions').style.display='grid';$('bj21-status').textContent='ТВОЙ ХОД';
    if(bjSum(bj21P)===21) setTimeout(function(){bj21Stand();},500);
  });
}
$('bj21-hit').addEventListener('click',function(){
  if(!bj21Active)return;bj21P.push(newCard());renderHand('bj21-player',bj21P,false);$('bj21-pscore').textContent=bjSum(bj21P);
  if(bjSum(bj21P)>21){ bj21Active=false;$('bj21-status').textContent='💥 ПЕРЕБОР -'+fmt(bj21Bet)+' ₽';$('bj21-actions').style.display='none';setTimeout(initBJ21,3000); }
});
$('bj21-stand').addEventListener('click',function(){ bj21Stand(); });
function bj21Stand(){
  if(!bj21Active)return;bj21Active=false;
  var d=bjSum(bj21D),p=bjSum(bj21P);
  while(d<17){ bj21D.push(newCard()); d=bjSum(bj21D); }
  renderHand('bj21-dealer',bj21D,false);$('bj21-dscore').textContent=d;
  if(d>21||p>d){ var win=Math.floor(bj21Bet*2);changeBalance(win).then(function(){ $('bj21-status').textContent='🎉 +'+fmt(win)+' ₽';if(p===21&&bj21P.length===2) maybeGiveNft(5);setTimeout(initBJ21,3000); }); }
  else if(p===d){ changeBalance(bj21Bet).then(function(){ $('bj21-status').textContent='НИЧЬЯ';setTimeout(initBJ21,3000); }); }
  else { $('bj21-status').textContent='ПРОИГРАЛ -'+fmt(bj21Bet)+' ₽';setTimeout(initBJ21,3000); }
  $('bj21-actions').style.display='none';
}

// Инвентарь
function renderInv(){
  var c=$('inv-list');c.innerHTML='';
  if(!inventory||inventory.length===0){ c.innerHTML='<div style="grid-column:1/-1;text-align:center;opacity:.5;padding:40px;">ПУСТО</div>';return; }
  for(var i=0;i<inventory.length;i++){ var g=GIFTS[inventory[i]];if(!g) continue;var d=document.createElement('div');d.className='nft-card';d.innerHTML='<div style="font-size:52px">'+g.emoji+'</div><div style="font-size:12px;font-weight:700;color:#ffdd44">'+g.name+'</div>';c.appendChild(d); }
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
    await message.answer("🎰 <b>VEGAS CASINO</b>\n\n💰 100 ₽\n🎲 17 игр\n🃏 Покер vs ИИ\n\nЖми:", reply_markup=kb, parse_mode="HTML")

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
