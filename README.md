# 🤖 RBSE Test Manager Pro Bot (Ultra Edition)

![Bot Status](https://img.shields.io/badge/Status-Active-brightgreen)
![Python](https://img.shields.io/badge/Language-Python_3.10-blue)
![Telegram](https://img.shields.io/badge/Platform-Telegram-blue)

**RBSE Test Manager** is an advanced, fully automated Telegram bot designed to manage daily quiz tests for student groups. It handles scheduling, broadcasting, attendance tracking, and disciplinary actions (auto-ban on missed tests).

---

## 🚀 Ultra Pro Features

### 1. ⚡ Fully Automated Scheduler
- Automatically sends test links at a fixed time (Default: **4:00 PM**).
- No manual intervention required daily. Just load links once for the whole week!

### 2. 📢 Smart Pre-Alert System
- **2 Minutes Before Test:** Sends a "Get Ready" warning message.
- **Auto-Pin:** Automatically pins the warning message to notify all members.
- **Auto-Delete:** (Optional) Cleans up old announcements.

### 3. 🛡️ Discipline Management
- **Attendance Button:** Students must click "Mark Attendance" after the test.
- **3-Strike Rule:** If a user misses 3 tests consecutively, the bot can **Auto-Kick/Ban** them.

### 4. 🎛️ Dynamic Control Panel
- **Visual Menu:** Interactive buttons for Owners.
- **Time Changer:** Change test timing (4 PM, 7 PM, 8 PM) directly from Telegram buttons.
- **Deep Linking:** Direct contact button for the Owner.

---

## 🛠️ Commands List

### 👑 Owner/Admin Commands

| Command | Description | Example Usage |
| :--- | :--- | :--- |
| `/start` | Opens the Pro Dashboard with Photo & Buttons. | `/start` |
| `/add_group` | Connects a group to the bot (Run inside the group). | `/add_group` |
| `/test_link` | Adds a new test link to the Queue. | `/test_link Day 1 Physics http://link...` |

### 👤 User Commands

| Command | Description |
| :--- | :--- |
| `Button Click` | Users interact via the "Mark Attendance" button. |

---

## ⚙️ Installation & Deployment (Render)

### Step 1: Prepare Files
Ensure you have these 4 files in your repository:
1. `main.py` (The Brain)
2. `database.py` (The Memory)
3. `config.py` (The Settings)
4. `requirements.txt` (The Libraries)

### Step 2: Deploy on Render
1. Create a new **Web Service** or **Background Worker** on Render.
2. Connect your GitHub Repository.
3. **Build Command:** `pip install -r requirements.txt`
4. **Start Command:** `python main.py`

### Step 3: Configure Environment
- Edit `config.py` and add your `BOT_TOKEN` and `OWNER_ID` before deploying.

---

## 📸 How It Works (Workflow)

1. **Setup:** Add the bot to your study group and make it **Admin**.
2. **Connect:** Type `/add_group` in the group.
3. **Load Links:** Go to the bot's private chat and add links for the next few days using `/test_link`.
4. **Relax:** The bot will automatically:
   - Wake up at 4:00 PM.
   - Send a warning.
   - Pin the message.
   - Wait 2 minutes.
   - Send the actual test link.
   - Track attendance.

---

## 👨‍💻 Developer & Credits

- **Owner:** RoyalKing_7X4
- **ID:** `6761345074`
- **Developed for:** RBSE Board Students (Class 12th)

---
*© 2025 RBSE Test Series. All Rights Reserved.*
