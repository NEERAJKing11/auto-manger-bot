from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from database import load_data, save_data, is_admin, update_time
from config import OWNER_ID, START_IMG
from datetime import datetime
from jobs import job_send_test # For timer reschedule

ASK_DAY, ASK_LINK = range(2)

# --- START MENU ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if is_admin(user.id):
        caption = f"👑 **Welcome Boss {user.first_name}!**\nSelect an option below:"
        keyboard = [
            [InlineKeyboardButton("➕ Add Link (Step-by-Step)", callback_data='add_link_flow')],
            [InlineKeyboardButton("⏰ Set Timer", callback_data='menu_timer'),
             InlineKeyboardButton("📢 Broadcast", callback_data='menu_broadcast')],
            [InlineKeyboardButton("📊 Dashboard", callback_data='status_check')]
        ]
    else:
        caption = "🤖 **RBSE Study Bot**\nDaily Test Manager."
        keyboard = [[InlineKeyboardButton("👨‍💻 Contact Owner", url="https://t.me/RoyalKing_7X4")]]

    await update.message.reply_photo(photo=START_IMG, caption=caption, reply_markup=InlineKeyboardMarkup(keyboard))

# --- COMMANDS ---
async def add_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == "private": return
    db = load_data()
    if chat.id not in db["groups"]:
        db["groups"].append(chat.id)
        save_data(db)
        await update.message.reply_text(f"✅ **Connected:** {chat.title}")
        await context.bot.send_message(OWNER_ID, f"📢 New Group: {chat.title}")

async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("❌ Usage: `/broadcast Hello Students`")
        return
    
    msg = " ".join(context.args)
    db = load_data()
    count = 0
    # Send to Groups
    for gid in db["groups"]:
        try:
            await context.bot.send_message(gid, f"📢 **ANNOUNCEMENT:**\n\n{msg}")
            count += 1
        except: pass
    await update.message.reply_text(f"✅ Broadcast sent to {count} groups.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    db = load_data()
    txt = (
        "📊 **BOT STATUS**\n"
        f"Groups: {len(db['groups'])}\n"
        f"Queue: {len(db['queue'])}\n"
        f"Time: {db['settings']['time']}"
    )
    await update.message.reply_text(txt)

# --- LINK CONVERSATION ---
async def start_add_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return ConversationHandler.END
    await update.message.reply_text("📝 **Step 1:** Topic/Day batao? (e.g. Day 5 Physics)")
    return ASK_DAY

async def receive_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['day'] = update.message.text
    await update.message.reply_text("🔗 **Step 2:** Ab Link bhejo.")
    return ASK_LINK

async def receive_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = update.message.text
    day = context.user_data['day']
    db = load_data()
    db["queue"].append({"day": day, "link": link})
    save_data(db)
    await update.message.reply_text(f"✅ **Saved!**\nDay: {day}\nPending: {len(db['queue'])}")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Cancelled.")
    return ConversationHandler.END

# --- CALLBACKS (Buttons) ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'menu_timer':
        btns = [
            [InlineKeyboardButton("🕓 4 PM", callback_data='time_16'),
             InlineKeyboardButton("🕔 5 PM", callback_data='time_17')],
            [InlineKeyboardButton("🕕 6 PM", callback_data='time_18'),
             InlineKeyboardButton("🕖 7 PM", callback_data='time_19')],
            [InlineKeyboardButton("🕗 8 PM", callback_data='time_20'),
             InlineKeyboardButton("🕘 9 PM", callback_data='time_21')]
        ]
        await query.message.edit_reply_markup(InlineKeyboardMarkup(btns))

    elif data.startswith('time_'):
        h = int(data.split('_')[1])
        update_time(f"{h}:00")
        # Reschedule Job
        from datetime import time
        import pytz
        q = context.application.job_queue
        # Clear daily jobs (Hack: removing all to allow new one)
        for job in q.jobs(): 
             if job.callback.__name__ == 'job_send_test': job.schedule_removal()
        
        q.run_daily(job_send_test, time(hour=h, minute=0, tzinfo=pytz.timezone('Asia/Kolkata')))
        await query.message.edit_text(f"✅ **Time Updated:** {h}:00 PM")

    elif data == 'status_check':
        await status(query, context)

    elif data == 'add_link_flow':
        await query.message.reply_text("Type `/add_link` to start adding.")

async def mark_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = str(query.from_user.id)
    today = str(datetime.now().date())
    db = load_data()
    
    if uid not in db["users"]: db["users"][uid] = {"name": query.from_user.first_name, "strikes": 0, "last_date": ""}
    
    if db["users"][uid]["last_date"] == today:
        await query.answer("Already Marked! ✅", show_alert=True)
    else:
        db["users"][uid]["last_date"] = today
        db["users"][uid]["name"] = query.from_user.first_name
        save_data(db)
        await query.answer("✅ Attendance Marked!", show_alert=True)
