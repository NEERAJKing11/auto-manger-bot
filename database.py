import json
import os
from config import DB_FILE

DEFAULT_DATA = {
    "groups": [],           # Connected Groups
    "queue": [],            # Test Links
    "schedule_time": "16:00", # Default Time (4 PM)
    "users": {}             # Attendance Record
}

def load_data():
    """Data load karta hai"""
    if not os.path.exists(DB_FILE):
        save_data(DEFAULT_DATA)
        return DEFAULT_DATA
    
    try:
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
            # Ensure keys exist (Migration safety)
            for key in DEFAULT_DATA:
                if key not in data:
                    data[key] = DEFAULT_DATA[key]
            return data
    except:
        return DEFAULT_DATA

def save_data(data):
    """Data save karta hai"""
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def update_time(new_time):
    """Time update karta hai"""
    data = load_data()
    data["schedule_time"] = new_time
    save_data(data)
