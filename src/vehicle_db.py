import sqlite3
import os

# --- PATH CONFIGURATION ---
DB_DIR = "/home/hatim/Documents/Github/SmartAccessControl/data"
DB_NAME = "vehicles.db"
DB_PATH = os.path.join(DB_DIR, DB_NAME)

# Ensure the folder exists
os.makedirs(DB_DIR, exist_ok=True)

class VehicleDatabase:
    def __init__(self):
        # check_same_thread=False allows access from different threads (GUI/Camera)
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS authorized_vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plate_number TEXT UNIQUE NOT NULL,
                owner_name TEXT
            )
        ''')
        self.conn.commit()

    def add_vehicle(self, plate_number, owner_name):
        """Adds a new authorized vehicle."""
        clean_plate = plate_number.replace(" ", "").upper()
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO authorized_vehicles (plate_number, owner_name) VALUES (?, ?)", 
                           (clean_plate, owner_name))
            self.conn.commit()
            print(f"[DB] Successfully added: {clean_plate} ({owner_name})")
            return True
        except sqlite3.IntegrityError:
            print(f"[DB] Error: Plate {clean_plate} already exists.")
            return False

    def is_authorized(self, plate_number):
        """Returns Owner Name if authorized, else None."""
        if not plate_number: return None
        
        clean_plate = plate_number.replace(" ", "").upper()
        cursor = self.conn.cursor()
        cursor.execute("SELECT owner_name FROM authorized_vehicles WHERE plate_number = ?", (clean_plate,))
        result = cursor.fetchone()
        
        if result:
            return result[0] # Return the owner's name
        return None

# Global Instance
vehicle_db = VehicleDatabase()