import queue
import threading
import time
from queue import Queue
import colorama
from insightface.app import FaceAnalysis
import cv2

# --- Import our modules ---
from src.camera_utils import initialize_cameras
# Assuming you have this file from our previous steps
from src.attendance_service import run_attendance_service 
from src.restriction_service import run_restriction_service  
from src.car_service import run_car_service
from src.socketio import socketio_client                  

# --- Config ---
HOST_IP = '0.0.0.0'
PORT = 65432
NUM_CAMERAS = 3
# Mapping: [Car_Cam, Attendance_Cam, Security_Cam]
# Your old code used index 0 for Car, 1 for Attendance, 2 for Restriction
VIRTUAL_CAMERA_IDS = [9, 10, 11]

express_client = socketio_client()

def main():
    colorama.init()
    
    # 1. AI Initialization
    print("Initializing InsightFace...")
    app_insight = FaceAnalysis(name='antelopev2', allowed_modules=['detection', 'recognition'])
    app_insight.prepare(ctx_id=0, det_size=(640, 640))

    # 2. Camera Initialization
    print(f"Initializing Virtual Cameras: {VIRTUAL_CAMERA_IDS}")
    caps = initialize_cameras(VIRTUAL_CAMERA_IDS)
    
    # Check if we have all cameras
    if not caps or len(caps) < len(VIRTUAL_CAMERA_IDS):
        print("CRITICAL: Not enough cameras found. Is FFmpeg running?")
        # You might want to return here, or continue with what you have

    # 3. Thread Control
    stop_event = threading.Event()
    task_queue = Queue() 

    # --- SERVICE MAPPING ---
    # caps[0] is Video 9  (Car)
    # caps[1] is Video 10 (Attendance)
    # caps[2] is Video 11 (Restriction)

    # We create lists containing the INDEX in 'caps', NOT the hardware ID.
    car_indices = [0]   # Uses caps[0]
    att_indices = [1]   # Uses caps[1]
    sec_indices = [2]   # Uses caps[2]

    try:
        print("Starting All Services...")

        # --- Thread 1: Attendance (Uses Virtual Cam 10) ---
        t_attendance = threading.Thread(
            target=run_attendance_service,
            args=(stop_event, caps, att_indices, app_insight, HOST_IP, PORT),
            name="AttendanceThread"
        )

        # --- Thread 2: Restriction (Uses Virtual Cam 11) ---
        t_restriction = threading.Thread(
            target=run_restriction_service,
            args=(stop_event, caps, sec_indices, app_insight, task_queue, express_client),
            name="RestrictionThread"
        )

        # --- Thread 3: Car (Uses Virtual Cam 9) ---
        t_car = threading.Thread(
            target=run_car_service,
            args=(stop_event, caps, car_indices, express_client, task_queue),
            name="CarThread"
        )
        
        # Start all at once
        # t_car.start()
        # t_restriction.start()
        t_attendance.start() 
        
        print("System Running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping all services...")
        stop_event.set() # Signal all threads to stop

    finally:
        print("Waiting for threads to join...")
        # for t in threads:
        #     t.join()
        

        # t_car.join()
        # t_restriction.join()
        t_attendance.join()

        
        print("Releasing resources...")
        if caps:
            for cap in caps:
                cap.release()
        cv2.destroyAllWindows()
        print("System Shutdown Complete.")

if __name__ == "__main__":
    main()