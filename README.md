# 🦅 RBSE Ultra Pro Test Manager Bot (v4.0)

![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge&logo=telegram)
![Python](https://img.shields.io/badge/Language-Python_3.11-blue?style=for-the-badge&logo=python)
![Platform](https://img.shields.io/badge/Deploy-Render-violet?style=for-the-badge&logo=render)

**The Ultimate Automation Solution for Coaching Groups.**
Designed to manage daily quizzes, track attendance, maintain discipline, and generate nightly reports automatically.

---

## 🌟 Key Features (Ultra Pro)

### 🤖 Automation & Management
* **⚡ Auto-Scheduler:** Sends test links automatically at the set time (e.g., 4 PM, 8 PM).
* **🚨 Pre-Alert System:** Sends a warning message **2 minutes before** the test and **Pins** it.
* **📅 Interactive Queue:** Add test links for days in advance using a step-by-step conversation.
* **📢 Broadcast:** Send announcements to all connected groups with one click.

### 🛡️ Discipline & Tracking
* **📝 Attendance System:** Students must click the "Mark Attendance" button after the test.
* **🦅 Early Bird Topper:** Identifies the first student to complete the test daily.
* **🌙 Nightly Report (9:30 PM):**
    * Generates a list of **Absent Students**.
    * **Auto-Kick:** Automatically bans users who miss **3 tests** in a row.
* **👮 Admin Control:** Owner can authorize other admins to manage the bot.

### 💻 Technical Superiority
* **🟢 Zero Downtime:** Integrated `Flask` server to keep the bot alive on Render Free Tier.
* **📂 Modular Code:** Split into 6 files for maximum stability and speed.
* **📊 Dashboard:** Real-time status report for the owner.

---

## 🛠️ Commands List

| Command | Description | Access |
| :--- | :--- | :--- |
| `/start` | Open the **Interactive Menu** (Dashboard) | Everyone |
| `/add_group` | Connect a study group to the bot | Admin (in Group) |
| `/add_link` | Add a new test link (Interactive Mode) | Admin (Private) |
| `/broadcast` | Send a message to all groups | Owner Only |
| `/status` | View Total Groups, Queue & Settings | Admin Only |
| `/set_timer` | Change daily test time (e.g., `/set_timer 20:00`) | Owner Only |

---

## 🚀 Deployment Guide (Render.com)

This bot is optimized for **Render Free Tier**.

### Step 1: Prepare Files
Ensure your GitHub repository has these **6 Files**:
1.  `main.py` (The Brain)
2.  `config.py` (Settings)
3.  `database.py` (Storage)
4.  `handlers.py` (Commands)
5.  `jobs.py` (Automation)
6.  `requirements.txt` (Libraries)

### Step 2: Configure `config.py`
Edit `config.py` and add your details:
```python
BOT_TOKEN = "123456:ABC-DEF..."  # Get from @BotFather
OWNER_ID = 123456789             # Your Telegram User ID
