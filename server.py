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
.game{background:linear-gradient(160deg,#12122a,#0d0d1f);border-radius:14px;padding:22px 10px;text-align:center;cursor:pointer;border:1px solid #1e1e3a}
.game:active{transform:scale(.96);border-color:#4a3aff}
.game .name{font-size:13px;font-weight:700;letter-spacing:1px}
.game .desc{font-size:10px;opacity:.5;margin-top:4px}
.screen{display:none}.screen.active{display:block}
.back{background:#12122a;border:1px solid #1e1e3a;color:#fff;padding:10px 16px;border-radius:10px;font-size:13px;margin-bottom:14px;cursor:pointer}
h2{font-size:18px;margin-bottom:16px;text-align:center;font-weight:800;letter-spacing:2px}
.bet-buttons{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:14px}
.bet-btn{background:#12122a;border:1px solid #2a2a4a;color:#fff;padding:14px;border-radius:10px;font-size:15px;font-weight:700;cursor:pointer}
.bet-btn:active{background:#2a2a4a}
.slots{display:flex;justify-content:center;gap:10px;margin:30px 0}
.slot{width:90px;height:120px;background:linear-gradient(180deg,#1a1a2e,#0f0f1e);border:2px solid #4a3aff;border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:52px}
.slot.spinning{animation:sp .1s infinite}
@keyframes sp{0%,100%{transform:translateY(-8px)}50%{transform:translateY(8px)}}
.dice-display{font-size:110px;text-align:center;margin:30px 0;min-height:120px}
.status{text-align:center;font-size:14px;min-height:24px;margin-bottom:8px;font-weight:600}
.num-buttons{display:grid;grid-template-columns:repeat(6,1fr);gap:6px;margin-top:10px}
</style>
</head>
<body>

<div id="menu" class="screen active">
  <div class="balance"><h1>БАЛАНС</h1><div class="amount"><span id="balance">100.00</span> ₽</div></div>
  <div class="games">
    <div class="game" id="btn-slots"><div class="name">🎰 СЛОТЫ</div><div class="desc">3 БАРАБАНА</div></div>
    <div class="game" id="btn-dice"><div class="name">🎲 КОСТИ</div><div class="desc">УГАДАЙ ЧИСЛО</div></div>
  </div>
</div>

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

<script>
// ==== ИНИЦИАЛИЗАЦИЯ ====
var tg = null;
try {
  tg = window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null;
  if (tg) { tg.ready(); tg.expand(); }
} catch(e) { console.log('TG error:', e); }

var user = (tg && tg.initDataUnsafe && tg.initDataUnsafe.user) ? tg.initDataUnsafe.user : { id: 0 };
console.log('USER:', user);

var BETS = [100, 500, 1000, 5000];
var balance = 10000;
var dicePick = 0;

function fmt(k) { return (k / 100).toFixed(2); }
function showAlert(msg) { if (tg && tg.showAlert) { tg.showAlert(msg); } else { alert(msg); } }

function updateUI() {
  var el = document.getElementById('balance');
  if (el) el.textContent = fmt(balance);
}

function loadBalance() {
  fetch('/api/balance?user_id=' + user.id)
    .then(function(r) { return r.json(); })
    .then(function(d) {
      balance = d.balance;
      updateUI();
    })
    .catch(function(e) { console.log('loadBalance:', e); });
}

function changeBalance(delta) {
  return fetch('/api/balance', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: user.id, delta: delta })
  })
    .then(function(r) { return r.json(); })
    .then(function(d) {
      balance = d.balance;
      updateUI();
    })
    .catch(function(e) { console.log('changeBalance:', e); });
}

function showScreen(id) {
  var screens = document.querySelectorAll('.screen');
  for (var i = 0; i < screens.length; i++) { screens[i].classList.remove('active'); }
  document.getElementById(id).classList.add('active');
}

function goMenu() { showScreen('menu'); }

// ==== КНОПКИ МЕНЮ ====
document.getElementById('btn-slots').addEventListener('click', function() {
  showScreen('slots');
  initSlots();
});
document.getElementById('btn-dice').addEventListener('click', function() {
  showScreen('dice');
  initDice();
});
document.getElementById('back-slots').addEventListener('click', goMenu);
document.getElementById('back-dice').addEventListener('click', goMenu);

// ==== КНОПКИ СТАВОК ====
function makeBetButtons(containerId, callback) {
  var c = document.getElementById(containerId);
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

// ==== СЛОТЫ ====
var slotsBusy = false;

function initSlots() {
  slotsBusy = false;
  document.getElementById('slots-status').textContent = 'ВЫБЕРИ СТАВКУ';
  document.getElementById('slot0').textContent = '🍒';
  document.getElementById('slot1').textContent = '🍒';
  document.getElementById('slot2').textContent = '🍒';
  makeBetButtons('slots-buttons', playSlots);
}

function playSlots(bet) {
  if (slotsBusy) return;
  if (bet > balance) { showAlert('Недостаточно средств'); return; }
  slotsBusy = true;

  changeBalance(-bet).then(function() {
    var symbols = ['🍒', '🍋', '🍊', '💎', '7️⃣'];
    document.getElementById('slots-buttons').innerHTML = '';
    document.getElementById('slots-status').textContent = 'КРУТИМ...';

    for (var i = 0; i < 3; i++) {
      document.getElementById('slot' + i).classList.add('spinning');
    }

    var final = [
      symbols[Math.floor(Math.random() * 5)],
      symbols[Math.floor(Math.random() * 5)],
      symbols[Math.floor(Math.random() * 5)]
    ];

    setTimeout(function() {
      document.getElementById('slot0').classList.remove('spinning');
      document.getElementById('slot0').textContent = final[0];
    }, 700);

    setTimeout(function() {
      document.getElementById('slot1').classList.remove('spinning');
      document.getElementById('slot1').textContent = final[1];
    }, 1200);

    setTimeout(function() {
      document.getElementById('slot2').classList.remove('spinning');
      document.getElementById('slot2').textContent = final[2];

      var mult = 0;
      if (final[0] === final[1] && final[1] === final[2]) {
        mult = final[0] === '7️⃣' ? 10 : 5;
      } else if (final[0] === final[1] || final[1] === final[2] || final[0] === final[2]) {
        mult = 2;
      }

      var win = Math.floor(bet * mult);
      var done = function() {
        document.getElementById('slots-status').textContent = mult
          ? ('ВЫИГРЫШ: +' + fmt(win) + ' ₽ (x' + mult + ')')
          : 'НЕ ПОВЕЗЛО';
        setTimeout(initSlots, 2500);
      };

      if (win > 0) { changeBalance(win).then(done); } else { done(); }
    }, 1700);
  });
}

// ==== КОСТИ ====
var diceBusy = false;

function initDice() {
  diceBusy = false;
  dicePick = 0;
  document.getElementById('dice-display').textContent = '🎲';
  document.getElementById('dice-status').textContent = 'ВЫБЕРИ ЧИСЛО И СТАВКУ';
  makeBetButtons('dice-buttons', playDice);
}

var diceBtns = document.querySelectorAll('[data-dice]');
for (var i = 0; i < diceBtns.length; i++) {
  (function(btn) {
    btn.addEventListener('click', function() {
      dicePick = parseInt(btn.getAttribute('data-dice'));
      document.getElementById('dice-status').textContent = 'ВЫБРАНО: ' + dicePick + ' | ВЫБЕРИ СТАВКУ';
    });
  })(diceBtns[i]);
}

function playDice(bet) {
  if (diceBusy) return;
  if (!dicePick) { showAlert('Выбери число'); return; }
  if (bet > balance) { showAlert('Недостаточно средств'); return; }
  diceBusy = true;

  changeBalance(-bet).then(function() {
    document.getElementById('dice-buttons').innerHTML = '';
    document.getElementById('dice-status').textContent = 'БРОСАЕМ...';

    setTimeout(function() {
      var result = Math.floor(Math.random() * 6) + 1;
      var faces = ['', '⚀', '⚁', '⚂', '⚃', '⚄', '⚅'];
      document.getElementById('dice-display').textContent = faces[result];

      if (result === dicePick) {
        var win = bet * 6;
        changeBalance(win).then(function() {
          document.getElementById('dice-status').textContent = 'ВЫПАЛО ' + result + '! +' + fmt(win) + ' ₽';
          setTimeout(initDice, 3000);
        });
      } else {
        document.getElementById('dice-status').textContent = 'ВЫПАЛО ' + result + '. МИМО';
        setTimeout(initDice, 3000);
      }
    }, 1000);
  });
}

// ==== ЗАПУСК ====
window.addEventListener('load', function() {
  loadBalance();
});
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
