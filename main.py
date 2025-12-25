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

# --- Config ---
HOST_IP = '0.0.0.0'
PORT = 65432
NUM_CAMERAS = 3
# Mapping: [Car_Cam, Attendance_Cam, Security_Cam]
# Your old code used index 0 for Car, 1 for Attendance, 2 for Restriction
CAMERA_INDICES = [0, 1, 2] 

def main():
    colorama.init()
    
    # 1. AI Initialization
    print("Initializing InsightFace...")
    app_insight = FaceAnalysis(name='antelopev2', allowed_modules=['detection', 'recognition'])
    app_insight.prepare(ctx_id=-1)

    # 2. Camera Initialization
    print("Initializing Cameras...")
    caps = initialize_cameras(NUM_CAMERAS)
    if not caps or len(caps) < NUM_CAMERAS:
        print("CRITICAL: Not enough cameras found.")
        # If testing with fewer cameras, comment out the return
        # return 

    # 3. Thread Control
    stop_event = threading.Event()
    task_queue = Queue() 

    threads = []

    try:
        print("Starting All Services...")

        # --- Thread 1: Attendance (Socket Server + Cam 1) ---
        t_attendance = threading.Thread(
            target=run_attendance_service,
            # Arguments must match your run_attendance_service definition
            args=(stop_event, caps, CAMERA_INDICES, app_insight, HOST_IP, PORT),
            name="AttendanceThread"
        )
        # threads.append(t_attendance)

        # --- Thread 2: Restriction/Security (Cam 2) ---
        t_restriction = threading.Thread(
            target=run_restriction_service,
            args=(stop_event, caps, CAMERA_INDICES, app_insight, task_queue),
            name="RestrictionThread"
        )
        # threads.append(t_restriction)

        # --- Thread 3: Car Identification (Cam 0) ---
        t_car = threading.Thread(
            target=run_car_service,
            args=(stop_event, caps, CAMERA_INDICES),
            name="CarThread"
        )
        

        # threads.append(t_car)

        # --- Start All Threads ---
        # for t in threads:
        #     t.start()
        # t_car.start()
        # t_attendance.start()
        # t_restriction.start()
        

        
        print("System Running. Press Ctrl+C to stop.")
        while True:
            # We keep the main thread alive to catch KeyboardInterrupt
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping all services...")
        stop_event.set() # Signal all threads to stop

    finally:
        print("Waiting for threads to join...")
        # for t in threads:
        #     t.join()
        
        # t_car.join()
        # t_attendance.join()
        # t_restriction.join()
        
        print("Releasing resources...")
        if caps:
            for cap in caps:
                cap.release()
        cv2.destroyAllWindows()
        print("System Shutdown Complete.")

if __name__ == "__main__":
    main()