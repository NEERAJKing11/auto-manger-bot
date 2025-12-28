import logging
import asyncio
from datetime import time
import pytz
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Imports form other files
from config import BOT_TOKEN, OWNER_ID
from database import load_data, save_data, update_time
from handlers import (
    start, add_group, status, add_user_cmd, mark_attendance, 
    link_conv_handler
)

# --- FLASK SERVER (Keep Alive) ---
app_web = Flask('')
@app_web.route('/')
def home(): return "Ultra Bot Running 🚀"
def run_http(): app_web.run(host='0.0.0.0', port=8080)
def keep_alive(): t = Thread(target=run_http); t.start()

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- JOB 1: SEND TEST (Dynamic Time) ---
async def job_send_test(context: ContextTypes.DEFAULT_TYPE):
    db = load_data()
    if not db["queue"]:
        await context.bot.send_message(chat_id=OWNER_ID, text="⚠️ **Alert:** Queue Empty! Aaj test nahi gaya.")
        return

    # Get Top Test
    test_data = db["queue"].pop(0) # {day:.., link:..}
    save_data(db)
    
    # 1. Alert & Pin
    for gid in db["groups"]:
        try:
            m = await context.bot.send_message(chat_id=gid, text=f"🚨 **ALERT:** {test_data['day']} Test starts in 2 Mins!")
            await context.bot.pin_chat_message(chat_id=gid, message_id=m.message_id)
        except: pass
    
    await asyncio.sleep(120) # 2 Min Wait

    # 2. Send Link
    btn = [[InlineKeyboardButton("✅ MARK ATTENDANCE", callback_data='attendance_done')]]
    msg = (
        "🚀 **TEST STARTED NOW** 🚀\n\n"
        f"📌 **Topic:** {test_data['day']}\n"
        f"🔗 **Link:** {test_data['link']}\n\n"
        "👇 **Attendance Lagayein! (3 Miss = Kick)**"
    )
    
    for gid in db["groups"]:
        try:
            await context.bot.send_message(chat_id=gid, text=msg, reply_markup=InlineKeyboardMarkup(btn))
        except: pass

    await context.bot.send_message(chat_id=OWNER_ID, text=f"✅ Test Sent: {test_data['day']}")

# --- JOB 2: NIGHTLY REPORT (9:30 PM) ---
async def job_nightly_report(context: ContextTypes.DEFAULT_TYPE):
    db = load_data()
    from datetime import datetime
    today = str(datetime.now().date())
    
    absent_list = []
    kicked_list = []
    
    # Check Logic
    for uid, info in db["users"].items():
        # Admins ko skip karo
        if int(uid) == OWNER_ID or int(uid) in db["auth_users"]: continue
        
        if info["last_date"] != today:
            # ABSENT
            info["strikes"] += 1
            absent_list.append(f"{info['name']} (Missed: {info['strikes']})")
            
            # KICK LOGIC
            if info["strikes"] >= 3:
                kicked_list.append(info['name'])
                info["strikes"] = 0 # Reset
                # Ban User from all groups
                for gid in db["groups"]:
                    try:
                        await context.bot.ban_chat_member(gid, int(uid))
                        await context.bot.unban_chat_member(gid, int(uid)) # Unban taki fine dekar aa sake
                    except: pass
        else:
            # PRESENT
            pass
            
    save_data(db)
    
    # Report Message
    report = "🌙 **DAILY REPORT (9:30 PM)** 🌙\n\n"
    if absent_list:
        report += "❌ **ABSENT STUDENTS:**\n" + "\n".join(absent_list) + "\n\n"
    else:
        report += "✅ **All Present!** Great Job.\n\n"
        
    if kicked_list:
        report += "🚫 **KICKED (3 Strikes):**\n" + "\n".join(kicked_list) + "\n_Contact Admin for Re-entry_"

    # Send to Groups
    for gid in db["groups"]:
        try:
            await context.bot.send_message(chat_id=gid, text=report)
        except: pass

# --- TIMER SETUP ---
async def setup_scheduler(app):
    db = load_data()
    t = db["settings"]["time"].split(":")
    
    # 1. Daily Test Job
    app.job_queue.run_daily(job_send_test, time(hour=int(t[0]), minute=int(t[1]), tzinfo=pytz.timezone('Asia/Kolkata')))
    
    # 2. Nightly Report Job (Fixed 21:30)
    app.job_queue.run_daily(job_nightly_report, time(hour=21, minute=30, tzinfo=pytz.timezone('Asia/Kolkata')))

# --- SET TIMER COMMAND ---
async def set_timer_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    try:
        new_time = context.args[0] # Format HH:MM
        # Validation
        h, m = map(int, new_time.split(":"))
        
        db = load_data()
        db["settings"]["time"] = new_time
        save_data(db)
        
        # Restart Logic (User needs to restart bot or we implement complex reschedule)
        await update.message.reply_text(f"✅ Time Set: {new_time}\n(Note: Render restart hone par apply hoga)")
    except:
        await update.message.reply_text("❌ Format: `/set_timer 16:00`")

if __name__ == "__main__":
    keep_alive()
    
    app = Application.builder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add_group", add_group))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("add_user", add_user_cmd))
    app.add_handler(CommandHandler("set_timer", set_timer_cmd))
    
    # Conversation (Link Add)
    app.add_handler(link_conv_handler)
    
    # Callback
    app.add_handler(CallbackQueryHandler(mark_attendance, pattern='attendance_done'))

    # Scheduler Init
    loop = asyncio.get_event_loop()
    loop.run_until_complete(setup_scheduler(app))

    print("🔥 Ultra Pro Bot Running...")
    app.run_polling()
