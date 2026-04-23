from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import sqlite3, time, requests

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
VPN_API_URL = "https://vpncheck.example.com/api?ip="

DB = "data.db"
conn = sqlite3.connect(DB, check_same_thread=False)
cur = conn.cursor()

# ======== DATABASE TABLES ========
cur.execute("""CREATE TABLE IF NOT EXISTS users(
user_id INTEGER PRIMARY KEY,
balance INTEGER,
refs INTEGER DEFAULT 0,
ref_by INTEGER,
banned INTEGER DEFAULT 0,
last_ad INTEGER DEFAULT 0,
joined INTEGER,
ads_count INTEGER DEFAULT 0,
daily_bonus_claimed INTEGER DEFAULT 0,
ref_bonus_claimed INTEGER DEFAULT 0
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS ads(
id INTEGER PRIMARY KEY AUTOINCREMENT,
link TEXT
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS withdraw(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
amount INTEGER,
method TEXT,
info TEXT,
time INTEGER
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS logs(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
amount INTEGER,
time INTEGER
)""")
conn.commit()

# ======== HELPERS ========
def now(): return int(time.time())

def add_user(uid, ref=None):
    cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users(user_id,balance,refs,ref_by,banned,last_ad,joined) VALUES(?,?,?,?,?,?,?)",
                    (uid, WELCOME_BONUS, 0, ref, 0, 0, now()))
        conn.commit()
        if ref and ref != uid:
            cur.execute("UPDATE users SET balance=balance+?, refs=refs+1, ref_bonus_claimed=1 WHERE user_id=?",(REF_BONUS, ref))
            conn.commit()

def get_balance(uid):
    cur.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()
    return row[0] if row else 0

def add_balance(uid, amount):
    cur.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (amount, uid))
    cur.execute("INSERT INTO logs(user_id,amount,time) VALUES(?,?,?)", (uid, amount, now()))
    conn.commit()

def generate_link():
    api = API_LIST[int(time.time()) % len(API_LIST)]
    try:
        r = requests.get(f"https://exe.io/api?api={api}&url=https://google.com")
        return r.json().get("shortenedUrl","https://google.com")
    except:
        return "https://google.com"

def check_vpn(ip):
    try:
        r = requests.get(VPN_API_URL+ip)
        return r.json().get("vpn", False)
    except:
        return False

# ======== MENUS ========
def menu(uid):
    kb = [
        [InlineKeyboardButton("💰 أرباحي", callback_data="bal")],
        [InlineKeyboardButton("🎁 مشاهدة إعلان واربح 120🔥", callback_data="ads")],
        [InlineKeyboardButton("👥 دعوة الأصدقاء = أرباح ⚡", callback_data="ref")],
        [InlineKeyboardButton("🏦 سحب أرباحك الآن 💸", callback_data="with")],
        [InlineKeyboardButton("✉️ تواصل معنا", url=f"https://t.me/hassanhasan12")]
    ]
    if uid == ADMIN_ID:
        kb.append([InlineKeyboardButton("⚙️ لوحة الإدارة المتقدمة", callback_data="admin")])
    return InlineKeyboardMarkup(kb)

def back_btn(callback="home"):
    return InlineKeyboardMarkup([[InlineKeyboardButton("↩️ السابق", callback_data=callback)]])

def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 إحصائيات", callback_data="stats")],
        [InlineKeyboardButton("📢 إدارة الإعلانات", callback_data="ads_admin")],
        [InlineKeyboardButton("🚫 المستخدمين المحظورين", callback_data="ban_menu")],
        [InlineKeyboardButton("↩️ السابق", callback_data="home")]
    ])

# ======== START ========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    ref = int(context.args[0]) if context.args else None
    add_user(uid, ref)
    await update.message.reply_text(
f"""🎉 أهلاً وسهلاً بالمشترك الجديد!
💰 تم إضافة بونص مجاني بقيمة {WELCOME_BONUS} ل.س

🚀 اربح بسهولة من الإعلانات واختصار الروابط!
⚡ تابع، شارك، وكن من الأوائل في جني الأرباح!

🏆 مكافآت إضافية:
- مشاهدة 5 إعلانات → بونص {AD_BONUS} ل.س
- دعوة صديق → بونص {REF_BONUS} ل.س
- تسجيل يومي → بونص {DAILY_BONUS} ل.س

⚠️ يرجى عدم استخدام VPN لتجنب الحظر.

👇 اختر من القائمة للبدء
""", reply_markup=menu(uid))

# ======== BUTTONS ========
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    await q.answer()

    # الرئيسية
    if q.data == "home":
        await q.edit_message_text("🏠 القائمة الرئيسية", reply_markup=menu(uid))
        return

    elif q.data == "bal":
        await q.edit_message_text(f"💰 رصيدك: {get_balance(uid)}", reply_markup=back_btn())

    elif q.data == "ads":
        cur.execute("SELECT ads_count FROM users WHERE user_id=?", (uid,))
        count = cur.fetchone()[0]
        if count >= 40:
            await q.answer("❌ وصلت الحد اليومي للإعلانات", show_alert=True)
            return
        ip = uid
        if check_vpn(str(ip)):
            cur.execute("UPDATE users SET banned=1 WHERE user_id=?", (uid,))
            conn.commit()
            await q.edit_message_text("🚫 تم حظرك 15 دقيقة بسبب VPN")
            return
        link = generate_link()
        cur.execute("UPDATE users SET last_ad=?, ads_count=ads_count+1 WHERE user_id=?", (time.time(), uid))
        conn.commit()
        await q.edit_message_text(
f"""🔥 كل إعلان يضيف {AD_REWARD} ل.س

⚠️ يمنع استخدام VPN

افتح الرابط وانتظر 30 ثانية ثم تحقق
{link}""",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ تحقق الآن", callback_data="check")]]))

    elif q.data == "check":
        cur.execute("SELECT last_ad FROM users WHERE user_id=?", (uid,))
        last = cur.fetchone()[0]
        if time.time() - last < 30:
            await q.answer("❌ يجب الانتظار 30 ثانية", show_alert=True)
            return
        add_balance(uid, AD_REWARD)
        await q.edit_message_text(f"✅ تم إضافة {AD_REWARD} ل.س", reply_markup=back_btn())

    elif q.data == "ref":
        link = f"https://t.me/{BOT_USERNAME}?start={uid}"
        await q.edit_message_text(f"🔗 رابطك الشخصي:\n{link}", reply_markup=back_btn())

    # لوحة الإدارة
    elif q.data == "admin" and uid == ADMIN_ID:
        await q.edit_message_text("⚙️ لوحة الإدارة المتقدمة", reply_markup=admin_menu())

    elif q.data == "stats" and uid == ADMIN_ID:
        cur.execute("SELECT COUNT(*) FROM users")
        total_users = cur.fetchone()[0]
        cur.execute("SELECT SUM(balance) FROM users")
        total_balance = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(*) FROM users WHERE banned=1")
        banned = cur.fetchone()[0]
        await q.edit_message_text(
f"""📊 إحصائيات البوت
👤 المستخدمين: {total_users}
💰 الأرباح الكلية: {total_balance}
🚫 المحظورين: {banned}""", reply_markup=admin_menu())
