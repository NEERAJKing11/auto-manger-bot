import json
import os
from config import DB_FILE, OWNER_ID

DEFAULT_DATA = {
    "groups": [],
    "queue": [],      # {day: "Day 1", link: "http...", added_by: 123}
    "users": {},      # {user_id: {name: "Ram", strikes: 0, last_date: "2024-01-01"}}
    "auth_users": [], # Extra Admins
    "settings": {"time": "16:00"}
}

def load_data():
    if not os.path.exists(DB_FILE):
        save_data(DEFAULT_DATA)
        return DEFAULT_DATA
    try:
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
            # Future proofing keys
            for key in DEFAULT_DATA:
                if key not in data: data[key] = DEFAULT_DATA[key]
            return data
    except:
        return DEFAULT_DATA

def save_data(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def is_admin(user_id):
    data = load_data()
    return user_id == OWNER_ID or user_id in data["auth_users"]
    
