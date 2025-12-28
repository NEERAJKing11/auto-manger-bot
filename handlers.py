import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler

from database import load_data, save_data, is_admin
from config import OWNER_ID

# --- CONVERSATION STATES ---
ASK_DAY, ASK_LINK = range(2)

# --- 1. START & DASHBOARD ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if is_admin(user.id):
        txt = (
            f"👑 **Welcome Boss {user.first_name}!**\n\n"
            "**Pro Commands:**\n"
            "✅ `/add_group` - Group me likhein\n"
            "➕ `/add_link` - Interactive Link Add\n"
            "📊 `/status` - Full Report\n"
            "👤 `/add_user <id>` - Make Admin"
        )
    else:
        txt = "🤖 **RBSE Study Bot**\nDaily Test & Discipline Manager."
    
    await update.message.reply_text(txt)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    
    db = load_data()
    txt = (
        "📊 **ULTRA PRO DASHBOARD**\n\n"
        f"🏢 **Total Groups:** {len(db['groups'])}\n"
        f"🔗 **Tests in Queue:** {len(db['queue'])}\n"
        f"👮 **Admins:** {len(db['auth_users']) + 1}\n"
        f"⏰ **Next Test Time:** {db['settings']['time']}"
    )
    await update.message.reply_text(txt)

# --- 2. ADD GROUP ---
async def add_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == "private":
        await update.message.reply_text("❌ Ye Group me likhein.")
        return

    db = load_data()
    if chat.id not in db["groups"]:
        db["groups"].append(chat.id)
        save_data(db)
        # Group Message
        await update.message.reply_text(f"✅ **Connected:** {chat.title}")
        # Owner Private Alert
        await context.bot.send_message(
            chat_id=OWNER_ID, 
            text=f"📢 **New Group Alert!**\nName: {chat.title}\nTotal Groups: {len(db['groups'])}"
        )
    else:
        await update.message.reply_text("ℹ️ Group pehle se list me hai.")

# --- 3. INTERACTIVE ADD LINK (Conversation) ---
async def start_add_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return ConversationHandler.END
    await update.message.reply_text("📝 **Step 1:** Test ka **Day/Topic** batayein.\n(Ex: Day 1 Hindi)")
    return ASK_DAY

async def receive_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['day'] = update.message.text
    await update.message.reply_text("🔗 **Step 2:** Ab **Quiz Link** bhejein.")
    return ASK_LINK

async def receive_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = update.message.text
    day = context.user_data['day']
    
    db = load_data()
    # Queue Object
    entry = {"day": day, "link": link}
    db["queue"].append(entry)
    save_data(db)
    
    await update.message.reply_text(
        f"✅ **Link Saved Successfully!**\n\n📌 Topic: {day}\n🔗 Link: {link}\n\n"
        f"📂 Total Pending: {len(db['queue'])}"
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Process Cancelled.")
    return ConversationHandler.END

# --- 4. ATTENDANCE & FIRST TOPPER ---
async def mark_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    today = str(datetime.now().date())
    uid = str(user.id)
    
    db = load_data()
    if uid not in db["users"]: 
        db["users"][uid] = {"name": user.first_name, "strikes": 0, "last_date": ""}
    
    if db["users"][uid]["last_date"] == today:
        await query.answer("Already Marked! ✋", show_alert=True)
    else:
        db["users"][uid]["last_date"] = today
        db["users"][uid]["name"] = user.first_name
        save_data(db)
        
        # Check if first (Topper Logic)
        # Simple logic: First person to mark today gets a special alert
        await query.answer(f"✅ Attendance Marked: {user.first_name}", show_alert=True)

# --- 5. ADD USER (Auth) ---
async def add_user_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    try:
        new_id = int(context.args[0])
        db = load_data()
        if new_id not in db["auth_users"]:
            db["auth_users"].append(new_id)
            save_data(db)
            await update.message.reply_text(f"✅ User {new_id} ab Admin hai.")
        else:
            await update.message.reply_text("ℹ️ Pehle se Admin hai.")
    except:
        await update.message.reply_text("❌ ID Number dalein.")

# --- CONVERSATION HANDLER OBJECT ---
link_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("add_link", start_add_link)],
    states={
        ASK_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_day)],
        ASK_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_link)],
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)
