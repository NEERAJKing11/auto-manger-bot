import logging
import asyncio
from datetime import time
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import BadRequest

# --- IMPORT CONFIG & DATABASE ---
from config import BOT_TOKEN, OWNER_ID, OWNER_USERNAME, START_IMG
from database import load_data, save_data, update_time

# --- LOGGING SETUP ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- COMMAND HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("➕ Add Group (Help)", callback_data='help_group'),
         InlineKeyboardButton("🔗 Add Link (Help)", callback_data='help_link')],
        [InlineKeyboardButton("⏰ Change Test Time", callback_data='menu_timer')],
        [InlineKeyboardButton("👨‍💻 Contact Owner", url=f"https://t.me/{OWNER_USERNAME}")]
    ]
    caption = (
        f"👋 **Hello {user.first_name}!**\n\n"
        "🤖 **I am RBSE Test Manager (Ultra Pro).**\n"
        "Main daily tests, attendance aur discipline manage karta hu.\n\n"
        "👇 **Control Panel:**"
    )
    await update.message.reply_photo(photo=START_IMG, caption=caption, reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'help_group':
        await query.message.reply_text("🛡️ **Group Add:**\n1. Bot ko Admin banayein.\n2. Group me likhein: `/add_group`")
    elif data == 'help_link':
        await query.message.reply_text("🔗 **Link Add:**\nPrivate me bhejein:\n`/test_link Day 1 Topic http://link...`")
    elif data == 'menu_timer':
        if query.from_user.id != OWNER_ID:
            await query.message.reply_text("❌ Sirf Owner permission hai.")
            return
        keyboard = [
            [InlineKeyboardButton("🕓 4:00 PM", callback_data='set_time_16'),
             InlineKeyboardButton("🕖 7:00 PM", callback_data='set_time_19')],
            [InlineKeyboardButton("🕗 8:00 PM", callback_data='set_time_20'),
             InlineKeyboardButton("🕘 9:00 PM", callback_data='set_time_21')]
        ]
        await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
    elif data.startswith('set_time_'):
        hour = int(data.split('_')[2])
        update_time(f"{hour}:00")
        
        # Reschedule Immediately
        await schedule_daily_job(context.application, hour, 0)
        await query.message.edit_caption(caption=f"✅ **Time Updated:** Daily test ab **{hour}:00 PM** baje hoga.")

async def add_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == "private":
        await update.message.reply_text("❌ Group me use karein.")
        return
    db = load_data()
    if chat.id not in db["groups"]:
        db["groups"].append(chat.id)
        save_data(db)
        await update.message.reply_text(f"✅ **Connected:** {chat.title}")
    else:
        await update.message.reply_text("ℹ️ Already Connected.")

async def add_test_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    if not context.args:
        await update.message.reply_text("❌ Usage: `/test_link Topic Link`")
        return
    db = load_data()
    db["queue"].append(" ".join(context.args))
    save_data(db)
    await update.message.reply_text(f"✅ **Saved!** Pending: {len(db['queue'])}")

# --- JOB LOGIC ---

async def send_daily_test(context: ContextTypes.DEFAULT_TYPE):
    db = load_data()
    if not db["queue"]:
        await context.bot.send_message(chat_id=OWNER_ID, text="⚠️ **Alert:** No Test Links in Queue!")
        return

    todays_test = db["queue"].pop(0)
    save_data(db)
    groups = db["groups"]

    # 1. Pre-Alert & Pin
    alert = "🚨 **ALERT:** Test starts in 2 Minutes! Get Ready."
    for gid in groups:
        try:
            m = await context.bot.send_message(chat_id=gid, text=alert)
            await context.bot.pin_chat_message(chat_id=gid, message_id=m.message_id)
        except: pass

    # 2. Wait
    await asyncio.sleep(120)

    # 3. Send Test
    btn = [[InlineKeyboardButton("✅ Mark Attendance", callback_data='attendance_done')]]
    msg = f"🚀 **TEST LIVE** 🚀\n\n📌 {todays_test}\n\n⚠️ **Click button below or Ban!**"
    
    for gid in groups:
        try:
            await context.bot.send_message(chat_id=gid, text=msg, reply_markup=InlineKeyboardMarkup(btn))
        except: pass
    
    await context.bot.send_message(chat_id=OWNER_ID, text=f"✅ Sent: {todays_test}")

async def mark_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    today = str(update.effective_message.date.date())
    db = load_data()
    if uid not in db["users"]: db["users"][uid] = {"last_date": ""}
    
    if db["users"][uid]["last_date"] == today:
        await update.callback_query.answer("Already Marked! ✅", show_alert=True)
    else:
        db["users"][uid]["last_date"] = today
        save_data(db)
        await update.callback_query.answer("Present ✅", show_alert=True)

# --- SCHEDULER HELPER ---
async def schedule_daily_job(app, hour, minute):
    queue = app.job_queue
    # Remove old jobs
    for job in queue.jobs(): job.schedule_removal()
    # Add new job
    queue.run_daily(send_daily_test, time(hour=hour, minute=minute, tzinfo=pytz.timezone('Asia/Kolkata')))

# --- STARTUP LOGIC (NO ERROR GUARANTEE) ---
async def post_init(application: Application):
    """Bot start hote hi database se time check karke job set karega"""
    db = load_data()
    t = db["schedule_time"].split(":")
    await schedule_daily_job(application, int(t[0]), int(t[1]))
    print("✅ Bot Fully Started & Scheduler Active!")

# --- MAIN ---
if __name__ == "__main__":
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add_group", add_group))
    app.add_handler(CommandHandler("test_link", add_test_link))
    app.add_handler(CallbackQueryHandler(button_handler, pattern='^help_|menu_|set_time_'))
    app.add_handler(CallbackQueryHandler(mark_attendance, pattern='attendance_done'))

    print("🚀 Ultra Pro Bot Running...")
    app.run_polling()
