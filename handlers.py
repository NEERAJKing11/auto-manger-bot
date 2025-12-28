from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from database import load_data, save_data, is_admin, update_time, get_queue_list
from config import OWNER_ID, START_IMG
from datetime import datetime, time  # <--- Ye add kiya hai
import pytz                          # <--- Ye add kiya hai
from jobs import job_send_test, execute_test_logic

ASK_DAY, ASK_LINK = range(2)

# --- START MENU ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if is_admin(user.id):
        caption = f"👑 **Owner Panel: {user.first_name}**\nSelect option:"
        keyboard = [
            [InlineKeyboardButton("🚀 QUICK START (Testing)", callback_data='menu_quick_start')],
            [InlineKeyboardButton("➕ Add Link", callback_data='add_link_flow'),
             InlineKeyboardButton("📢 Broadcast", callback_data='help_broadcast')],
            [InlineKeyboardButton("⏰ Set Timer", callback_data='menu_timer'),
             InlineKeyboardButton("📊 Dashboard", callback_data='status_check')]
        ]
    else:
        caption = "🤖 **RBSE Manager Bot**\nDaily Quiz & Attendance System."
        keyboard = [[InlineKeyboardButton("👨‍💻 Contact Admin", url="https://t.me/RoyalKing_7X4")]]

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
        await update.message.reply_text("❌ **Usage:** `/broadcast Hello Everyone`")
        return
    
    msg = " ".join(context.args)
    db = load_data()
    sent = 0
    for gid in db["groups"]:
        try:
            await context.bot.send_message(gid, f"📢 **ANNOUNCEMENT:**\n\n{msg}")
            sent += 1
        except: pass
    await update.message.reply_text(f"✅ Sent to {sent} Groups.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    db = load_data()
    txt = f"📊 **STATUS**\nGroups: {len(db['groups'])}\nQueue: {len(db['queue'])}\nTime: {db['settings']['time']}"
    await update.message.reply_text(txt)

# --- BUTTON LOGIC (Fixed) ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() # Pop-up hatane ke liye
    data = query.data
    db = load_data()

    # 1. TIMER MENU SHOW
    if data == 'menu_timer':
        btns = [
            [InlineKeyboardButton("🕓 4 PM", callback_data='time_16'),
             InlineKeyboardButton("🕔 5 PM", callback_data='time_17')],
            [InlineKeyboardButton("🕕 6 PM", callback_data='time_18'),
             InlineKeyboardButton("🕖 7 PM", callback_data='time_19')],
            [InlineKeyboardButton("🕗 8 PM", callback_data='time_20'),
             InlineKeyboardButton("🕘 9 PM", callback_data='time_21')],
            [InlineKeyboardButton("🔙 Back", callback_data='back_home')]
        ]
        await query.message.edit_reply_markup(InlineKeyboardMarkup(btns))

    # 2. TIMER SET LOGIC (FIXED)
    elif data.startswith('time_'):
        h = int(data.split('_')[1])
        update_time(f"{h}:00")
        
        # Job Reschedule Logic
        q = context.application.job_queue
        # Remove old jobs
        for job in q.jobs():
            if job.callback.__name__ == 'job_send_test':
                job.schedule_removal()
        
        # Add new job
        q.run_daily(job_send_test, time(hour=h, minute=0, tzinfo=pytz.timezone('Asia/Kolkata')))
        
        await query.message.edit_caption(caption=f"✅ **Success!**\nTime Updated to: **{h}:00 PM**")

    # 3. BACK HOME
    elif data == 'back_home':
        # Re-show start menu
        await start(query, context)

    # 4. QUICK START MENU
    elif data == 'menu_quick_start':
        queue = get_queue_list()
        if not queue:
            await query.message.reply_text("⚠️ Queue Empty! `/add_link` karein.")
            return
        btns = []
        for i, item in enumerate(queue):
            btns.append([InlineKeyboardButton(f"🚀 Fire: {item['day']}", callback_data=f"fire_{i}")])
        await query.message.reply_text("👇 **Select Test to Launch:**", reply_markup=InlineKeyboardMarkup(btns))

    # 5. FIRE TEST
    elif data.startswith('fire_'):
        index = int(data.split('_')[1])
        queue = get_queue_list()
        if index >= len(queue):
            await query.message.reply_text("❌ Error: Link not found.")
            return
        test_to_run = queue[index]
        await query.message.reply_text(f"⏳ **Starting {test_to_run['day']}...**")
        for gid in db["groups"]:
            context.application.create_task(execute_test_logic(context, gid, test_to_run))

    # 6. OTHERS
    elif data == 'help_broadcast':
        await query.message.reply_text("📢 Msg: `/broadcast Hello`")
    elif data == 'add_link_flow':
        await query.message.reply_text("Msg: `/add_link`")
    elif data == 'status_check':
        await status(query, context)

# --- ATTENDANCE ---
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

# --- CONVERSATION HELPERS ---
async def start_add_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return ConversationHandler.END
    await update.message.reply_text("📝 **Topic Name?**")
    return ASK_DAY

async def receive_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['day'] = update.message.text
    await update.message.reply_text("🔗 **Link?**")
    return ASK_LINK

async def receive_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = update.message.text
    day = context.user_data['day']
    db = load_data()
    db["queue"].append({"day": day, "link": link})
    save_data(db)
    await update.message.reply_text(f"✅ **Saved!** {day}")
    return ConversationHandler.END

async def cancel(u, c): 
    await u.message.reply_text("❌ Cancelled")
    return ConversationHandler.END
