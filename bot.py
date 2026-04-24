from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import sqlite3, time, requests, random

# ================= CONFIG =================
TOKEN = "8728108992:AAG81nj5sEHFZASRue-PdgnUZVrUzPo-wIA"
ADMIN_ID = 5492649402
BOT_USERNAME = "hassan2003probot"

SMART_LINK = "https://www.profitablecpmratenetwork.com/u4iric19?key=8c595d0b7efd3561c15b20d650be1295"

AD_REWARD = 150
REF_PERCENT = 0.5
MIN_WITHDRAW = 1000
MAX_ADS_PER_DAY = 40

# ================= DATABASE =================
conn = sqlite3.connect("data.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS users(
user_id INTEGER PRIMARY KEY,
balance INTEGER,
ref_by INTEGER,
ads_count INTEGER DEFAULT 0,
last_ad INTEGER DEFAULT 0
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS withdraw(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
amount INTEGER,
method TEXT,
info TEXT,
time INTEGER
)""")

conn.commit()

# ================= SESSION =================
sessions = {}

def create_session(uid):
    code = str(random.randint(1000,9999))
    sessions[uid] = {"code": code, "time": time.time()}
    return code

# ================= HELPERS =================
def add_user(uid, ref=None):
    cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users(user_id,balance,ref_by) VALUES(?,?,?)",(uid,0,ref))
        conn.commit()

def get_balance(uid):
    cur.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
    return cur.fetchone()[0]

def add_balance(uid, amount):
    cur.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (amount, uid))
    conn.commit()

# ================= MENUS =================
def menu(uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 أرباحي", callback_data="bal")],
        [InlineKeyboardButton("🎁 مشاهدة إعلان", callback_data="ads")],
        [InlineKeyboardButton("👥 الإحالات", callback_data="ref")],
        [InlineKeyboardButton("🏦 سحب", callback_data="with")]
    ])

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    ref = int(context.args[0]) if context.args else None
    add_user(uid, ref)

    await update.message.reply_text("🔥 أهلاً بك في بوت الربح", reply_markup=menu(uid))

# ================= BUTTONS =================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    await q.answer()

    if q.data == "bal":
        await q.edit_message_text(f"💰 رصيدك: {get_balance(uid)}", reply_markup=menu(uid))

    elif q.data == "ads":
        cur.execute("SELECT ads_count FROM users WHERE user_id=?", (uid,))
        if cur.fetchone()[0] >= MAX_ADS_PER_DAY:
            await q.answer("❌ الحد اليومي", show_alert=True)
            return

        code = create_session(uid)
        cur.execute("UPDATE users SET ads_count=ads_count+1,last_ad=? WHERE user_id=?",(time.time(),uid))
        conn.commit()

        await q.edit_message_text(
f"""🔥 شاهد الإعلان واربح

{SMART_LINK}

🔐 رمزك:
{code}

⏳ انتظر 30 ثانية ثم اضغط تحقق""",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ تحقق", callback_data="check")]
        ])
        )

    elif q.data == "check":
        if uid not in sessions:
            await q.answer("❌ لا يوجد جلسة", show_alert=True)
            return

        if time.time() - sessions[uid]["time"] < 30:
            await q.answer("⏳ انتظر 30 ثانية", show_alert=True)
            return

        context.user_data["verify"] = True
        await q.message.reply_text("🔐 ارسل رمز التحقق")

    elif q.data == "ref":
        link = f"https://t.me/{BOT_USERNAME}?start={uid}"
        await q.edit_message_text(
f"""👥 نظام الإحالة

ادعُ أصدقائك واربح 💰

🔥 سوف تحصل على 50% من أرباح كل شخص تدعوه

🔗 رابطك:
{link}""",
        reply_markup=menu(uid))

    elif q.data == "with":
        if get_balance(uid) < MIN_WITHDRAW:
            await q.answer("❌ الحد الأدنى للسحب", show_alert=True)
            return

        context.user_data["withdraw"] = True
        await q.message.reply_text("💰 ارسل المبلغ")

# ================= TEXT =================
async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    msg = update.message.text

    if context.user_data.get("verify"):
        if sessions[uid]["code"] != msg:
            await update.message.reply_text("❌ رمز خطأ")
            return

        reward = AD_REWARD
        add_balance(uid, reward)

        # ربح الإحالة
        cur.execute("SELECT ref_by FROM users WHERE user_id=?", (uid,))
        ref = cur.fetchone()[0]
        if ref:
            add_balance(ref, int(reward * REF_PERCENT))

        context.user_data["verify"] = False
        await update.message.reply_text(f"✅ تم إضافة {reward}", reply_markup=menu(uid))

    elif context.user_data.get("withdraw"):
        amount = int(msg)
        if amount > get_balance(uid):
            await update.message.reply_text("❌ لا يوجد رصيد كافي")
            return

        cur.execute("INSERT INTO withdraw(user_id,amount,time) VALUES(?,?,?)",(uid,amount,time.time()))
        conn.commit()

        await update.message.reply_text("✅ تم إرسال طلب السحب")
        await context.bot.send_message(ADMIN_ID, f"طلب سحب\nID:{uid}\nAmount:{amount}")

        context.user_data["withdraw"] = False

# ================= RUN =================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text))

print("BOT WORKING...")
app.run_polling()
