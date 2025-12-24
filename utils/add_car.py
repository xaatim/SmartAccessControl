import sys
import os

# Add the parent directory (Root) to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.vehicle_db import vehicle_db

if __name__ == "__main__":
    print("--- Add Authorized Vehicle ---")
    plate = input("Enter License Plate (e.g., JEV8842): ")
    name = input("Enter Owner Name: ")
    
    if plate and name:
        vehicle_db.add_vehicle(plate, name)
    else:
        print("Invalid input.")