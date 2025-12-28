import logging
import asyncio
from datetime import time
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import BadRequest

# Doosri files se import kar rahe hain
from config import BOT_TOKEN, OWNER_ID, OWNER_USERNAME, START_IMG
from database import load_data, save_data, update_time

# Logging Setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variable to store current job
current_job = None

# --- START MENU & COMMANDS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Pro Buttons
    keyboard = [
        [InlineKeyboardButton("➕ Add Group (Example)", callback_data='help_group'),
         InlineKeyboardButton("🔗 Add Link (Example)", callback_data='help_link')],
        [InlineKeyboardButton("⏰ Change Test Time", callback_data='menu_timer')],
        [InlineKeyboardButton("👨‍💻 Contact Owner", url=f"https://t.me/{OWNER_USERNAME}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    caption = (
        f"👋 **Hello {user.first_name}!**\n\n"
        "🤖 **I am RBSE Test Manager (Ultra Pro).**\n"
        "Main daily tests, attendance aur discipline manage karta hu.\n\n"
        "👇 **Control Panel:**"
    )
    
    # Photo ke sath message
    await update.message.reply_photo(photo=START_IMG, caption=caption, reply_markup=reply_markup)

# --- BUTTON CLICK HANDLING ---

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # 1. HELP: GROUP ADD
    if data == 'help_group':
        txt = (
            "🛡️ **Group Kaise Add Karein?**\n\n"
            "1️⃣ Bot ko Group me **Admin** banayein.\n"
            "2️⃣ Group me likhein: `/add_group`\n\n"
            "✅ *Bot Success message bhejega.*"
        )
        await query.message.reply_text(txt, parse_mode="Markdown")

    # 2. HELP: LINK ADD
    elif data == 'help_link':
        txt = (
            "🔗 **Test Link Kaise Dalein?**\n\n"
            "Mujhe (Bot ko) Private me ye command bhejein:\n"
            "`/test_link <Day/Topic> <Link>`\n\n"
            "📝 **Example:**\n"
            "`/test_link Day 1 Hindi http://t.me/quizbot?start=123`"
        )
        await query.message.reply_text(txt, parse_mode="Markdown")

    # 3. MENU: TIMER SELECTION
    elif data == 'menu_timer':
        if query.from_user.id != OWNER_ID:
            await query.message.reply_text("❌ Sirf Owner time change kar sakta hai.")
            return

        keyboard = [
            [InlineKeyboardButton("🕓 4:00 PM", callback_data='set_time_16'),
             InlineKeyboardButton("🕖 7:00 PM", callback_data='set_time_19')],
            [InlineKeyboardButton("🕗 8:00 PM", callback_data='set_time_20'),
             InlineKeyboardButton("🕘 9:00 PM", callback_data='set_time_21')],
            [InlineKeyboardButton("🔙 Back", callback_data='back_home')]
        ]
        await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))

    # 4. LOGIC: SET TIME
    elif data.startswith('set_time_'):
        hour = int(data.split('_')[2])
        update_time(f"{hour}:00") # DB update
        
        # Reschedule Job
        await schedule_daily_job(context.application, hour, 0)
        
        await query.message.edit_caption(caption=f"✅ **Success!**\nTime update ho gaya hai: **{hour}:00 PM**")

# --- ADMIN COMMANDS ---

async def add_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == "private":
        await update.message.reply_text("❌ Ye command Group me likhein.")
        return

    db = load_data()
    if chat.id not in db["groups"]:
        db["groups"].append(chat.id)
        save_data(db)
        # Demo Message
        await update.message.reply_text("✅ **Group Connected!**\nAb yahan daily test aayega.")
        # Owner ko info
        await context.bot.send_message(chat_id=OWNER_ID, text=f"📢 New Group Added: {chat.title}")
    else:
        await update.message.reply_text("ℹ️ Group pehle se connected hai.")

async def add_test_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    if not context.args:
        await update.message.reply_text("❌ **Error!**\nSahi Tareeka:\n`/test_link Day 1 Topic http://link.com`")
        return

    full_text = " ".join(context.args)
    db = load_data()
    db["queue"].append(full_text)
    save_data(db)
    
    await update.message.reply_text(f"✅ **Link Saved!**\nQueue: {len(db['queue'])} Tests pending.")

# --- THE CORE: DAILY TEST SENDER ---

async def send_daily_test(context: ContextTypes.DEFAULT_TYPE):
    db = load_data()
    groups = db["groups"]
    
    # Agar Queue khali hai
    if not db["queue"]:
        await context.bot.send_message(chat_id=OWNER_ID, text="⚠️ **Alert:** Test Links khatam ho gaye!")
        return

    # Link Nikalo
    todays_test = db["queue"].pop(0)
    save_data(db)

    # STEP 1: PRE-ALERT (2 Min Pehle)
    alert_text = "🚨 **ALERT: TEST STARTING SOON** 🚨\n\nSirf 2 Minute bache hain!\nSab log ready ho jao."
    
    for group_id in groups:
        try:
            msg = await context.bot.send_message(chat_id=group_id, text=alert_text)
            try:
                await context.bot.pin_chat_message(chat_id=group_id, message_id=msg.message_id)
            except:
                pass # Agar Pin ki permission nahi hai to ignore kare
        except Exception as e:
            print(f"Failed group {group_id}: {e}")

    # STEP 2: WAIT (2 Minutes)
    await asyncio.sleep(120)

    # STEP 3: SEND MAIN TEST
    keyboard = [[InlineKeyboardButton("✅ ATTENDANCE (Click Here)", callback_data='attendance_done')]]
    markup = InlineKeyboardMarkup(keyboard)
    
    test_msg = (
        "🚀 **RBSE TEST LIVE NOW** 🚀\n\n"
        f"📌 {todays_test}\n\n"
        "🛑 **Instruction:** Link open karke test dein aur wapis aakar button dabayein.\n"
        "⚠️ **3 Miss = Group Ban**"
    )

    for group_id in groups:
        try:
            await context.bot.send_message(chat_id=group_id, text=test_msg, reply_markup=markup)
        except Exception as e:
            print(f"Failed group {group_id}: {e}")
            
    await context.bot.send_message(chat_id=OWNER_ID, text=f"✅ Test Sent: {todays_test}")

# --- ATTENDANCE ---
async def mark_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    today = str(update.effective_message.date.date())
    db = load_data()
    
    if user_id not in db["users"]:
        db["users"][user_id] = {"last_date": ""}

    if db["users"][user_id]["last_date"] == today:
        await query.answer("Attendance Already Marked! ✅", show_alert=True)
    else:
        db["users"][user_id]["last_date"] = today
        save_data(db)
        await query.answer("✅ Present Marked!", show_alert=True)

# --- DYNAMIC SCHEDULER ---
async def schedule_daily_job(application, hour, minute):
    job_queue = application.job_queue
    # Purani job hatao
    jobs = job_queue.jobs()
    for job in jobs:
        job.schedule_removal()
    
    # Nayi Job Lagao
    india_tz = pytz.timezone('Asia/Kolkata')
    job_queue.run_daily(send_daily_test, time(hour=hour, minute=minute, tzinfo=india_tz))
    print(f"⏰ Timer Set for: {hour}:{minute}")

# --- MAIN ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add_group", add_group))
    app.add_handler(CommandHandler("test_link", add_test_link))
    app.add_handler(CallbackQueryHandler(button_handler, pattern='^help_|menu_|set_time_|back_'))
    app.add_handler(CallbackQueryHandler(mark_attendance, pattern='attendance_done'))

    # Start hote hi Database se time padhkar Job set karega
    db = load_data()
    saved_time = db["schedule_time"].split(":") # e.g. ["16", "00"]
    hour = int(saved_time[0])
    minute = int(saved_time[1])
    
    # Job Queue Init (Hack to access loop)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(schedule_daily_job(app, hour, minute))

    print("🚀 Ultra Pro Bot Started...")
    app.run_polling()

if __name__ == "__main__":
    main()
