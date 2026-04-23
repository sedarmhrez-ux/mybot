from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import sqlite3, time, threading, shutil

TOKEN = "8728108992:AAG81nj5sEHFZASRue-PdgnUZVrUzPo-wIA"
ADMIN_ID = 5492649402
ADMIN_USERNAME = "@hassanhasan12"
BOT_USERNAME = "hassan2003probot"

WELCOME_BONUS = 2900
REF_BONUS = 1000

DB_PATH = "/storage/emulated/0/mybot/data.db"

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cur = conn.cursor()

# ====== إنشاء الجداول ======
cur.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance INTEGER, ref INTEGER, refs INTEGER DEFAULT 0, banned INTEGER DEFAULT 0)")
cur.execute("CREATE TABLE IF NOT EXISTS withdraw (id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,amount INTEGER,method TEXT,info TEXT)")
conn.commit()

def add_user(uid, ref=None):
    cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users VALUES (?,?,?,?,?)", (uid, WELCOME_BONUS, ref, 0, 0))
        conn.commit()
        if ref:
            cur.execute("UPDATE users SET balance=balance+?, refs=refs+1 WHERE user_id=?", (REF_BONUS, ref))
            conn.commit()

def get_balance(uid):
    cur.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
    return cur.fetchone()[0]

def get_refs(uid):
    cur.execute("SELECT refs FROM users WHERE user_id=?", (uid,))
    return cur.fetchone()[0]

def is_banned(uid):
    cur.execute("SELECT banned FROM users WHERE user_id=?", (uid,))
    return cur.fetchone()[0] == 1

# ====== الواجهة ======
def menu(uid):
    kb = [
        [InlineKeyboardButton("💰 أرباحي", callback_data="bal")],
        [InlineKeyboardButton("🎁 مشاهدة الإعلانات", callback_data="ads")],
        [InlineKeyboardButton("👥 نظام الإحالة", callback_data="ref")],
        [InlineKeyboardButton("🏦 سحب الأرباح", callback_data="with")],
        [InlineKeyboardButton("✉️ تواصل معنا", url=f"https://t.me/{ADMIN_USERNAME.replace('@','')}")]
    ]
    if uid == ADMIN_ID:
        kb.append([InlineKeyboardButton("⚙️ لوحة الإدارة", callback_data="admin")])
    return InlineKeyboardMarkup(kb)

def back():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅ رجوع", callback_data="home")]])

# ====== START ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    ref = int(context.args[0]) if context.args else None

    add_user(uid, ref)

    if is_banned(uid):
        await update.message.reply_text("🚫 تم حظرك بسبب استخدام VPN لمدة 15 دقيقة")
        return

    text = f"""
🎉 مبروك تم إضافة بونص {WELCOME_BONUS} ل.س

📢 شاهد الإعلانات
👥 شارك رابطك
💰 واربح يومياً

👇 اختر من القائمة
"""
    await update.message.reply_text(text, reply_markup=menu(uid))

# ====== الأزرار ======
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    await q.answer()

    if q.data == "home":
        await q.edit_message_text("القائمة:", reply_markup=menu(uid))

    elif q.data == "bal":
        await q.edit_message_text(f"💰 رصيدك: {get_balance(uid)} ل.س", reply_markup=back())

    elif q.data == "ads":
        await q.edit_message_text(
            "🔥 كل إعلان تربح 120 ل.س 💸\n\nاضغط وشاهد واربح فوراً!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("▶️ مشاهدة إعلان", callback_data="watch")]
            ])
        )

    elif q.data == "watch":
        # محاكاة
        await q.edit_message_text("⏳ انتظر 30 ثانية ثم اضغط تحقق", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ تحقق", callback_data="check")]
        ]))

    elif q.data == "check":
        cur.execute("UPDATE users SET balance=balance+120 WHERE user_id=?", (uid,))
        conn.commit()
        await q.edit_message_text("✅ تم إضافة 120 ل.س", reply_markup=back())

    elif q.data == "ref":
        link = f"https://t.me/{BOT_USERNAME}?start={uid}"
        await q.edit_message_text(
            f"👥 رابطك:\n{link}\n\n🎁 كل شخص يعمل 15 دقيقة = {REF_BONUS} ل.س\n📊 عدد الإحالات: {get_refs(uid)}",
            reply_markup=back()
        )

    elif q.data == "with":
        await q.edit_message_text(
            """💳 طرق السحب:

📱 Syriatel cash (الحد الأدنى 77000)
💲 USDT (الحد الأدنى 10$)
💲 TON (الحد الأدنى 10$)
💲 Coinex (الحد الأدنى 10$)

✍️ اكتب:
withdraw المبلغ الطريقة الرقم
""",
            reply_markup=back()
        )

    elif q.data == "admin" and uid == ADMIN_ID:
        cur.execute("SELECT COUNT(*) FROM users")
        users = cur.fetchone()[0]
        await q.edit_message_text(f"👤 المستخدمين: {users}", reply_markup=back())

# ====== السحب ======
async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    args = context.args

    if len(args) < 3:
        await update.message.reply_text("❌ الصيغة:\nwithdraw 1000 USDT wallet")
        return

    amount = int(args[0])
    method = args[1]
    info = args[2]

    if get_balance(uid) < amount:
        await update.message.reply_text("❌ رصيدك لا يكفي")
        return

    # تحقق من الحد الأدنى
    if method.lower() == "syriatel" and amount < 77000:
        await update.message.reply_text("❌ الحد الأدنى 77000")
        return

    if method.lower() in ["usdt","ton","coinex"] and amount < 10:
        await update.message.reply_text("❌ الحد الأدنى 10$")
        return

    cur.execute("UPDATE users SET balance=balance-? WHERE user_id=?", (amount, uid))
    cur.execute("INSERT INTO withdraw (user_id,amount,method,info) VALUES (?,?,?,?)",
                (uid, amount, method, info))
    conn.commit()

    # إرسال لك
    await context.bot.send_message(
        ADMIN_ID,
        f"💸 طلب سحب جديد\n\nID: {uid}\nالمبلغ: {amount}\nالطريقة: {method}\nالبيانات: {info}"
    )

    await update.message.reply_text("✅ تم إرسال طلبك")

# ====== تشغيل ======
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("withdraw", withdraw))
app.add_handler(CallbackQueryHandler(buttons))

print("RUNNING...")
app.run_polling()
