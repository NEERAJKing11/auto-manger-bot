import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import load_data, save_data
from config import OWNER_ID
from datetime import datetime

# --- JOB 1: SEND TEST (Alert + Pin + Link) ---
async def job_send_test(context):
    db = load_data()
    if not db["queue"]:
        await context.bot.send_message(chat_id=OWNER_ID, text="⚠️ **Alert:** Queue Empty! Aaj test nahi gaya.")
        return

    # Link Nikalo
    test_data = db["queue"].pop(0) # {day:.., link:..}
    save_data(db)
    
    # 1. PRE-ALERT (2 Mins Pehle)
    for gid in db["groups"]:
        try:
            alert_msg = await context.bot.send_message(
                chat_id=gid, 
                text=f"🚨 **ALERT:** Test starts in 2 Minutes!\nTopic: {test_data['day']}\nGet Ready! ⏱️"
            )
            await context.bot.pin_chat_message(chat_id=gid, message_id=alert_msg.message_id)
        except: pass
    
    # Wait 2 Minutes
    await asyncio.sleep(120)

    # 2. SEND MAIN TEST
    btn = [[InlineKeyboardButton("✅ MARK ATTENDANCE", callback_data='attendance_done')]]
    msg = (
        "🚀 **TEST STARTED NOW** 🚀\n\n"
        f"📌 **Day/Topic:** {test_data['day']}\n"
        f"🔗 **Click to Start:** {test_data['link']}\n\n"
        "👇 **Test dekar Attendance Button dabayein!**\n"
        "⚠️ _(3 Miss = Group Ban)_"
    )
    
    for gid in db["groups"]:
        try:
            await context.bot.send_message(chat_id=gid, text=msg, reply_markup=InlineKeyboardMarkup(btn))
        except: pass

    await context.bot.send_message(chat_id=OWNER_ID, text=f"✅ Test Sent: {test_data['day']}")

# --- JOB 2: NIGHT CHECK (9:30 PM) ---
async def job_nightly_report(context):
    db = load_data()
    today = str(datetime.now().date())
    
    absent = []
    kicked = []
    early_bird = "None"
    
    # Find Early Bird (Sabse pehla present user)
    # (Simple logic: List me pehla valid user jisne aaj mark kiya)
    for uid, info in db["users"].items():
        if info["last_date"] == today:
            early_bird = info["name"]
            break 

    # Check Logic
    for uid, info in db["users"].items():
        if int(uid) == OWNER_ID or int(uid) in db["auth_users"]: continue
        
        if info["last_date"] != today:
            info["strikes"] += 1
            absent.append(f"{info['name']} (Missed: {info['strikes']})")
            
            if info["strikes"] >= 3:
                kicked.append(info['name'])
                info["strikes"] = 0
                for gid in db["groups"]:
                    try:
                        await context.bot.ban_chat_member(gid, int(uid))
                        await context.bot.unban_chat_member(gid, int(uid))
                    except: pass
        else:
            # Present logic handled in attendance
            pass
            
    save_data(db)
    
    # Report
    report = "🌙 **DAILY REPORT (9:30 PM)** 🌙\n\n"
    report += f"🦅 **Early Bird Topper:** {early_bird}\n\n"
    
    if absent:
        report += "❌ **ABSENT LIST:**\n" + "\n".join(absent) + "\n\n"
    else:
        report += "✅ **All Present!**\n\n"
        
    if kicked:
        report += "🚫 **BANNED USERS:**\n" + "\n".join(kicked)

    for gid in db["groups"]:
        try:
            await context.bot.send_message(chat_id=gid, text=report)
        except: pass
