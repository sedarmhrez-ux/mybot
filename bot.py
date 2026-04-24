from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import sqlite3, time, requests, random

# ================= CONFIG =================
TOKEN = "8728108992:AAG81nj5sEHFZASRue-PdgnUZVrUzPo-wIA"
ADMIN_ID = 5492649402
BOT_USERNAME = "hassan2003probot"

API_LIST = [
    "4693acfd000d76e596cb23645e01b0956f533f0f",
    "da29dbb527117f6da44b53b01d30042642f09339",
    "26b0905f8960ee10ce7b442717c1ce85e062113e",
    "2f32cae87ec3d4f9306f37337a538969141c14ca"
]

WELCOME_BONUS = 2400
REF_BONUS = 250
AD_BONUS = 400
DAILY_BONUS = 300
AD_REWARD = 120
MAX_ADS_PER_DAY = 40

DB = "data.db"
conn = sqlite3.connect(DB, check_same_thread=False)
cur = conn.cursor()

# ================= DATABASE =================
cur.execute("""CREATE TABLE IF NOT EXISTS users(
user_id INTEGER PRIMARY KEY,
balance INTEGER,
refs INTEGER DEFAULT 0,
ref_by INTEGER,
banned INTEGER DEFAULT 0,
last_ad INTEGER DEFAULT 0,
joined INTEGER,
ads_count INTEGER DEFAULT 0
)""")
conn.commit()

# ================= SESSION =================
user_sessions = {}

def create_session(uid):
    code = str(random.randint(1000, 9999))
    user_sessions[uid] = {
        "time": time.time(),
        "verified": False,
        "code": code
    }
    return code

# ================= HELPERS =================
def now(): return int(time.time())

def add_user(uid, ref=None):
    cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users(user_id,balance,refs,ref_by,banned,last_ad,joined) VALUES(?,?,?,?,?,?,?)",
                    (uid, WELCOME_BONUS,0,ref,0,0,now()))
        conn.commit()
        if ref and ref != uid:
            cur.execute("UPDATE users SET balance=balance+?, refs=refs+1 WHERE user_id=?",(REF_BONUS, ref))
            conn.commit()

def get_balance(uid):
    cur.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
    return cur.fetchone()[0]

def add_balance(uid, amount):
    cur.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (amount, uid))
    conn.commit()

def generate_link():
    api = random.choice(API_LIST)
    try:
        r = requests.get(f"https://exe.io/api?api={api}&url=https://google.com")
        return r.json().get("shortenedUrl","https://google.com")
    except:
        return "https://google.com"

# ================= MENUS =================
def menu(uid):
    kb = [
        [InlineKeyboardButton("💰 أرباحي", callback_data="bal")],
        [InlineKeyboardButton("🎁 مشاهدة إعلان واربح 🔥", callback_data="ads")],
        [InlineKeyboardButton("👥 دعوة الأصدقاء", callback_data="ref")],
        [InlineKeyboardButton("🏦 سحب الأرباح", callback_data="with")],
    ]
    if uid == ADMIN_ID:
        kb.append([InlineKeyboardButton("⚙️ لوحة الإدارة", callback_data="admin")])
    return InlineKeyboardMarkup(kb)

def back_btn():
    return InlineKeyboardMarkup([[InlineKeyboardButton("↩️ رجوع", callback_data="home")]])

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    ref = int(context.args[0]) if context.args else None
    add_user(uid, ref)

    await update.message.reply_text(
f"""🎉 أهلاً بك!

💰 تم إضافة {WELCOME_BONUS} ل.س

🚀 ابدأ الربح الآن""",
    reply_markup=menu(uid))

# ================= BUTTONS =================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    await q.answer()

    if q.data == "home":
        await q.edit_message_text("🏠 الرئيسية", reply_markup=menu(uid))

    elif q.data == "bal":
        await q.edit_message_text(f"💰 رصيدك: {get_balance(uid)}", reply_markup=back_btn())

    # ================= ADS LEVEL 6 =================
    elif q.data == "ads":
        cur.execute("SELECT ads_count FROM users WHERE user_id=?", (uid,))
        count = cur.fetchone()[0]

        if count >= MAX_ADS_PER_DAY:
            await q.answer("❌ وصلت الحد اليومي", show_alert=True)
            return

        link = generate_link()
        code = create_session(uid)

        cur.execute("UPDATE users SET last_ad=?, ads_count=ads_count+1 WHERE user_id=?", (time.time(), uid))
        conn.commit()

        await q.edit_message_text(
f"""🔥 اربح {AD_REWARD}

📢 افتح الرابط:
{link}

🔐 رمز:
{code}

⏳ بعد 30 ثانية اضغط تحقق""",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ تحقق", callback_data="check")],
            [InlineKeyboardButton("🔁 إعلان جديد", callback_data="ads")]
        ])
    )

    elif q.data == "check":
        if uid not in user_sessions:
            await q.answer("❌ لا يوجد إعلان", show_alert=True)
            return

        session = user_sessions[uid]

        if time.time() - session["time"] < 30:
            await q.answer("⏳ انتظر 30 ثانية", show_alert=True)
            return

        if session["verified"]:
            await q.answer("❌ تم التحقق مسبقاً", show_alert=True)
            return

        await q.message.reply_text("🔐 أرسل الرمز")

        context.user_data["await_code"] = True

    elif q.data == "ref":
        link = f"https://t.me/{BOT_USERNAME}?start={uid}"
        await q.edit_message_text(f"🔗 رابطك:\n{link}", reply_markup=back_btn())

    elif q.data == "with":
        await q.edit_message_text("💸 السحب قريباً", reply_markup=back_btn())

    elif q.data == "admin" and uid == ADMIN_ID:
        await q.edit_message_text("⚙️ لوحة الإدارة", reply_markup=back_btn())

# ================= CAPTCHA =================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id

    if context.user_data.get("await_code"):
        code = update.message.text.strip()

        if uid not in user_sessions:
            await update.message.reply_text("❌ انتهت الجلسة")
            return

        if user_sessions[uid]["code"] != code:
            await update.message.reply_text("❌ رمز خاطئ")
            return

        add_balance(uid, AD_REWARD)
        user_sessions[uid]["verified"] = True
        context.user_data["await_code"] = False

        cur.execute("SELECT ads_count FROM users WHERE user_id=?", (uid,))
        count = cur.fetchone()[0]

        if count % 5 == 0:
            add_balance(uid, AD_BONUS)
            await update.message.reply_text("🎁 بونص!")

        await update.message.reply_text("✅ تم إضافة الربح", reply_markup=menu(uid))

# ================= RUN =================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("BOT RUNNING...")
app.run_polling()
