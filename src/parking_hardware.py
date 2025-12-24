import serial
import time

# --- CONFIGURATION (LINUX) ---
# Common ports: '/dev/ttyACM0' (Uno) or '/dev/ttyUSB0' (Nano/Clones)
ARDUINO_PORT = '/dev/ttyUSB0' 
BAUD_RATE = 9600

class ParkingController:
    def __init__(self):
        self.ser = None
        try:
            # Initialize Serial Connection
            self.ser = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
            time.sleep(2) # Give Arduino time to reset after connection
            print(f"[Hardware] Connected to Parking Gate on {ARDUINO_PORT}")
        except Exception as e:
            print(f"[Hardware] Warning: Could not connect to Gate: {e}")

    def authorize_entry(self):
        """Sends 'A' to Arduino. Arduino then waits for the car to approach."""
        if self.ser:
            try:
                self.ser.write(b'A')
                print("[Hardware] Sent Authorization Signal (A) to Gate.")
            except Exception as e:
                print(f"[Hardware] Serial Write Error: {e}")
        else:
            print("[Hardware] Simulation: Authorization 'A' sent (No Hardware)")

    def close(self):
        if self.ser:
            self.ser.close()

# Create a single global instance
parking_gate = ParkingController()