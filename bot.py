from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import sqlite3, time, requests, random

# ================= CONFIG =================
TOKEN = "8728108992:AAG81nj5sEHFZASRue-PdgnUZVrUzPo-wIA"
ADMIN_ID = 5492649402
BOT_USERNAME = "hassan2003probot"

SMART_LINK = "https://www.profitablecpmratenetwork.com/u4iric19?key=8c595d0b7efd3561c15b20d650be1295"

# فقط المواقع اللي ممكن تشتغل
API_LIST = [
    ("https://exe.io/api", "4693acfd000d76e596cb23645e01b0956f533f0f"),
    ("https://clks.pro/api", "26b0905f8960ee10ce7b442717c1ce85e062113e"),
    ("https://droplink.co/api", "2f32cae87ec3d4f9306f37337a538969141c14ca")
]

WELCOME_BONUS = 2400
REF_BONUS = 250
AD_BONUS = 400
DAILY_BONUS = 300
AD_REWARD = 120
MAX_ADS_PER_DAY = 40
MIN_WITHDRAW = 1000

DB = "data.db"
conn = sqlite3.connect(DB, check_same_thread=False)
cur = conn.cursor()

# ================= DATABASE =================
cur.execute("""CREATE TABLE IF NOT EXISTS users(
user_id INTEGER PRIMARY KEY,
balance INTEGER,
refs INTEGER DEFAULT 0,
ref_by INTEGER,
last_ad INTEGER DEFAULT 0,
ads_count INTEGER DEFAULT 0,
daily_bonus INTEGER DEFAULT 0
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS withdraw(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
amount INTEGER,
method TEXT,
time INTEGER
)""")

conn.commit()

# ================= SESSION =================
user_sessions = {}
last_api_index = 0

def create_session(uid):
    code = str(random.randint(1000, 9999))
    user_sessions[uid] = {
        "time": time.time(),
        "verified": False,
        "code": code
    }
    return code

# ================= HELPERS =================
def add_user(uid, ref=None):
    cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users(user_id,balance,refs,ref_by) VALUES(?,?,?,?)",
                    (uid, WELCOME_BONUS,0,ref))
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

# 🔥 توليد الرابط (Rotation + Smartlink)
def generate_link():
    global last_api_index

    for i in range(len(API_LIST)):
        api_url, api_key = API_LIST[(last_api_index + i) % len(API_LIST)]

        try:
            r = requests.get(
                f"{api_url}?api={api_key}&url={SMART_LINK}",
                timeout=5
            )
            data = r.json()

            link = data.get("shortenedUrl") or data.get("shortened_url") or data.get("url")

            if link and link.startswith("http"):
                last_api_index = (last_api_index + i + 1) % len(API_LIST)
                return link

        except:
            continue

    return SMART_LINK

# ================= MENUS =================
def menu(uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 أرباحي", callback_data="bal")],
        [InlineKeyboardButton("🎁 مشاهدة إعلان", callback_data="ads")],
        [InlineKeyboardButton("🎁 بونص يومي", callback_data="daily")],
        [InlineKeyboardButton("👥 دعوة الأصدقاء", callback_data="ref")],
        [InlineKeyboardButton("🏦 سحب الأرباح", callback_data="with")],
        [InlineKeyboardButton("📞 تواصل معنا", url="https://t.me/hassanhasan12")]
    ])

def back_btn():
    return InlineKeyboardMarkup([[InlineKeyboardButton("↩️ رجوع", callback_data="home")]])

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    ref = int(context.args[0]) if context.args else None
    add_user(uid, ref)

    await update.message.reply_text(
f"""🎉 أهلاً وسهلاً بالمشترك الجديد!
💰 تم إضافة بونص مجاني بقيمة {WELCOME_BONUS} ل.س

🚀 اربح بسهولة من الإعلانات!
🏆 مكافآت:
- كل 5 إعلانات → {AD_BONUS}
- دعوة صديق → {REF_BONUS}
- يومي → {DAILY_BONUS}

👇 ابدأ الآن
""", reply_markup=menu(uid))

# ================= BUTTONS =================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    await q.answer()

    if q.data == "home":
        await q.edit_message_text("🏠 القائمة", reply_markup=menu(uid))

    elif q.data == "bal":
        await q.edit_message_text(f"💰 رصيدك: {get_balance(uid)}", reply_markup=back_btn())

    elif q.data == "ads":
        cur.execute("SELECT ads_count FROM users WHERE user_id=?", (uid,))
        count = cur.fetchone()[0]

        if count >= MAX_ADS_PER_DAY:
            await q.answer("❌ الحد اليومي", show_alert=True)
            return

        link = generate_link()
        code = create_session(uid)

        cur.execute("UPDATE users SET ads_count=ads_count+1 WHERE user_id=?", (uid,))
        conn.commit()

        await q.edit_message_text(
f"""🔥 اربح {AD_REWARD}

{link}

🔐 {code}
⏳ انتظر 30 ثانية ثم تحقق""",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ تحقق", callback_data="check")]
        ])
    )

    elif q.data == "check":
        if uid not in user_sessions:
            await q.answer("❌ لا يوجد إعلان", show_alert=True)
            return

        if time.time() - user_sessions[uid]["time"] < 30:
            await q.answer("⏳ انتظر", show_alert=True)
            return

        await q.answer("📩 أرسل الرمز")
        context.user_data["await_code"] = True

    elif q.data == "daily":
        cur.execute("SELECT daily_bonus FROM users WHERE user_id=?", (uid,))
        last = cur.fetchone()[0]

        if time.time() - last < 86400:
            await q.answer("❌ استلمت اليوم", show_alert=True)
            return

        add_balance(uid, DAILY_BONUS)
        cur.execute("UPDATE users SET daily_bonus=? WHERE user_id=?", (time.time(), uid))
        conn.commit()

        await q.edit_message_text("🎁 تم استلام البونص", reply_markup=back_btn())

# ================= TEXT =================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    text = update.message.text

    if context.user_data.get("await_code"):
        if user_sessions[uid]["code"] != text:
            await update.message.reply_text("❌ خطأ")
            return

        add_balance(uid, AD_REWARD)
        context.user_data["await_code"] = False

        await update.message.reply_text("✅ تم الربح", reply_markup=menu(uid))

# ================= RUN =================
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("BOT RUNNING...")
app.run_polling()
