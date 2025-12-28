import json
import os
from config import DB_FILE, OWNER_ID

DEFAULT_DATA = {
    "groups": [],
    "queue": [],      
    "users": {},      
    "auth_users": [], 
    "settings": {"time": "16:00"}
}

def load_data():
    """Data load karta hai"""
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
    """Data save karta hai"""
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def is_admin(user_id):
    """Check karta hai ki user Admin hai ya nahi"""
    data = load_data()
    return user_id == OWNER_ID or user_id in data.get("auth_users", [])

def update_time(new_time):
    """Time update karta hai (Ye missing tha)"""
    data = load_data()
    if "settings" not in data:
        data["settings"] = {}
    data["settings"]["time"] = new_time
    save_data(data)
