import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import load_data, save_data
from config import OWNER_ID
from datetime import datetime

# --- CORE FUNCTION: SEND TEST (Ye function har jagah use hoga) ---
async def execute_test_logic(context, chat_id, test_data):
    # 1. PRE-ALERT & PIN
    try:
        alert_text = f"🚨 **ALERT:** Test starts in 2 Minutes!\n📌 Topic: {test_data['day']}\n⚡ Get Ready!"
        msg = await context.bot.send_message(chat_id=chat_id, text=alert_text)
        try:
            await context.bot.pin_chat_message(chat_id=chat_id, message_id=msg.message_id)
        except:
            await context.bot.send_message(chat_id=chat_id, text="⚠️ *Admin Note:* Main Pin nahi kar pa raha. Mujhe 'Pin Messages' ki permission dein.")
    except Exception as e:
        print(f"Alert Failed for {chat_id}: {e}")

    # 2. WAIT 2 MINUTES
    await asyncio.sleep(120)

    # 3. SEND LINK
    try:
        btn = [[InlineKeyboardButton("✅ MARK ATTENDANCE", callback_data='attendance_done')]]
        main_text = (
            "🚀 **TEST LIVE NOW** 🚀\n\n"
            f"📌 **Topic:** {test_data['day']}\n"
            f"🔗 **LINK:** {test_data['link']}\n\n"
            "👇 **Attendance Lagayein!**"
        )
        await context.bot.send_message(chat_id=chat_id, text=main_text, reply_markup=InlineKeyboardMarkup(btn))
    except Exception as e:
        print(f"Test Failed for {chat_id}: {e}")


# --- AUTOMATIC SCHEDULED JOB ---
async def job_send_test(context):
    db = load_data()
    if not db["queue"]:
        await context.bot.send_message(chat_id=OWNER_ID, text="⚠️ **Auto-Job Failed:** Queue Empty!")
        return

    # Queue se nikalo
    test_data = db["queue"].pop(0) 
    save_data(db)
    
    # Sabhi groups me chalao
    for gid in db["groups"]:
        # Background task banakar chalao taki delay na ho
        asyncio.create_task(execute_test_logic(context, gid, test_data))

    await context.bot.send_message(chat_id=OWNER_ID, text=f"✅ Auto-Test Sent: {test_data['day']}")

# --- NIGHT REPORT JOB ---
async def job_nightly_report(context):
    db = load_data()
    today = str(datetime.now().date())
    
    absent = []
    kicked = []
    
    # Logic
    for uid, info in db["users"].items():
        if int(uid) == OWNER_ID or int(uid) in db["auth_users"]: continue
        
        if info["last_date"] != today:
            info["strikes"] += 1
            absent.append(f"{info['name']} (Miss: {info['strikes']})")
            if info["strikes"] >= 3:
                kicked.append(info['name'])
                info["strikes"] = 0 # Reset
                # Ban loop
                for gid in db["groups"]:
                    try:
                        await context.bot.ban_chat_member(gid, int(uid))
                        await context.bot.unban_chat_member(gid, int(uid))
                    except: pass
        else:
            pass # Present
            
    save_data(db)
    
    report = "🌙 **NIGHT REPORT** 🌙\n\n"
    if absent: report += "❌ **ABSENT:**\n" + "\n".join(absent) + "\n\n"
    else: report += "✅ **All Present!**\n\n"
    if kicked: report += "🚫 **BANNED:**\n" + "\n".join(kicked)

    for gid in db["groups"]:
        try: await context.bot.send_message(chat_id=gid, text=report)
        except: pass
