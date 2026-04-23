# ================== IMPORTS ==================
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import sqlite3, os, time, requests

# ================== CONFIG ==================
TOKEN = "8728108992:AAG81nj5sEHFZASRue-PdgnUZVrUzPo-wIA"
ADMIN_ID = 5492649402
BOT_USERNAME = "hassan2003probot"

# API KEYS
API_LIST = [
    "4693acfd000d76e596cb23645e01b0956f533f0f",
    "da29dbb527117f6da44b53b01d30042642f09339",
    "26b0905f8960ee10ce7b442717c1ce85e062113e"
]

WELCOME_BONUS = 2900
REF_BONUS = 1000

# ================== DATABASE ==================
DB_PATH = "data.db"

if not os.path.exists(DB_PATH):
    open(DB_PATH, 'w').close()

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
user_id INTEGER PRIMARY KEY,
balance INTEGER,
ref INTEGER,
refs INTEGER DEFAULT 0,
banned INTEGER DEFAULT 0,
last_active INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS logs(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
amount INTEGER,
time INTEGER
)
""")

conn.commit()

# ================== FUNCTIONS ==================
def now():
    return int(time.time())

def add_user(uid, ref=None):
    cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users VALUES (?,?,?,?,?,?)",
                    (uid, WELCOME_BONUS, ref, 0, 0, now()))
        conn.commit()

def get_balance(uid):
    cur.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()
    return row[0] if row else 0

def add_balance(uid, amount):
    cur.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (amount, uid))
    cur.execute("INSERT INTO logs (user_id,amount,time) VALUES (?,?,?)",
                (uid, amount, now()))
    conn.commit()

# ================== SHORT LINK ==================
def generate_link():
    api = API_LIST[int(time.time()) % len(API_LIST)]
    url = f"https://example.com/?{time.time()}"
    try:
        r = requests.get(f"https://exe.io/api?api={api}&url={url}")
        return r.json()["shortenedUrl"]
    except:
        return url

# ================== MENU ==================
def menu(uid):
    kb = [
        [InlineKeyboardButton("💰 أرباحي", callback_data="bal")],
        [InlineKeyboardButton("🎁 مشاهدة الإعلانات", callback_data="ads")],
        [InlineKeyboardButton("👥 الإحالة", callback_data="ref")],
        [InlineKeyboardButton("🏦 سحب", callback_data="with")]
    ]
    if uid == ADMIN_ID:
        kb.append([InlineKeyboardButton("⚙️ الإدارة", callback_data="admin")])
    return InlineKeyboardMarkup(kb)

# ================== START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    add_user(uid)

    text = f"""
🎉 تم إضافة بونص {WELCOME_BONUS}

⚠️ ننصح بعدم استخدام VPN أثناء العمل داخل البوت
لتجنب الحظر المؤقت أو الدائم

👇 ابدأ الآن
"""
    await update.message.reply_text(text, reply_markup=menu(uid))

# ================== BUTTONS ==================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    await q.answer()

    if q.data == "bal":
        await q.edit_message_text(f"رصيدك: {get_balance(uid)}", reply_markup=menu(uid))

    elif q.data == "ads":
        link = generate_link()
        await q.edit_message_text(
            f"""🔥 اربح 120 ل.س لكل إعلان

⚠️ يمنع استخدام VPN لتجنب الحظر

اضغط الرابط:
{link}

ثم اضغط تحقق""",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ تحقق", callback_data="check")]
            ])
        )

    elif q.data == "check":
        add_balance(uid, 120)
        await q.edit_message_text("✅ تم إضافة 120 ل.س", reply_markup=menu(uid))

    elif q.data == "admin" and uid == ADMIN_ID:
        cur.execute("SELECT COUNT(*) FROM users")
        total = cur.fetchone()[0]

        cur.execute("SELECT SUM(balance) FROM users")
        total_bal = cur.fetchone()[0] or 0

        await q.edit_message_text(
            f"""⚙️ لوحة الإدارة

👤 المستخدمين: {total}
💰 الأرباح: {total_bal}
""",
            reply_markup=menu(uid)
        )

# ================== RUN ==================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buttons))

print("BOT RUNNING...")
app.run_polling()
