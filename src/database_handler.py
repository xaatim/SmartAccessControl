import os
import sqlite3
from datetime import datetime


DB_NAME = "attendance.db"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
DB_PATH = os.path.join(DATA_DIR, 'attendance.db')



def init_db():
    """Creates the table if it doesn't exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # We store: ID, Name, Date (YYYY-MM-DD), Check-In Time, Check-Out Time
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT NOT NULL,
            date TEXT NOT NULL,
            check_in_time TEXT,
            check_out_time TEXT,
            UNIQUE(user_name, date)
        )
    ''')
    conn.commit()
    conn.close()
    print(f"[DB] Database initialized at: {DB_PATH}")

def log_user_attendance(name):
    """
    Logic:
    1. If no record for today -> INSERT (Check-In)
    2. If record exists -> UPDATE check_out_time (Check-Out)
    3. Returns a status string to display/send to ESP32
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    now = datetime.now()
    today_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")

    # 1. Check if a row exists for this person TODAY
    cursor.execute("SELECT check_in_time, check_out_time FROM attendance WHERE user_name = ? AND date = ?", (name, today_date))
    row = cursor.fetchone()

    status_message = ""

    if row is None:
        # --- CASE 1: First scan of the day (CHECK IN) ---
        cursor.execute("INSERT INTO attendance (user_name, date, check_in_time) VALUES (?, ?, ?)", 
                      (name, today_date, current_time))
        status_message = f"Welcome {name}"
        print(f"[DB] {name} Checked IN at {current_time}")

    else:
        # --- CASE 2: Already scanned today (CHECK OUT) ---
        check_in_str = row[0]
        last_out_str = row[1] if row[1] else check_in_str
        
        # COOLDOWN CHECK: Calculate time since last scan to prevent accidental double-taps
        # Convert strings back to datetime objects for math
        last_scan_time = datetime.strptime(f"{today_date} {last_out_str}", "%Y-%m-%d %H:%M:%S")
        time_diff = (now - last_scan_time).total_seconds()

        if time_diff < 60: # 60 Seconds Cooldown
            status_message = f"Already Scanned"
            print(f"[DB] {name} scanned too quickly (Ignored)")
        else:
            # Update the Check-Out time to NOW
            cursor.execute("UPDATE attendance SET check_out_time = ? WHERE user_name = ? AND date = ?", 
                          (current_time, name, today_date))
            status_message = f"Goodbye {name}"
            print(f"[DB] {name} Checked OUT at {current_time}")

    conn.commit()
    conn.close()
    return status_message

# Run this once when module loads to ensure DB exists
init_db()