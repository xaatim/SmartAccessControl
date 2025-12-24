import cv2
import time
from colorama import Fore

def initialize_cameras(num_cameras):
    caps = []
    try:
        for i in range(num_cameras):
            cap = cv2.VideoCapture(i,cv2.CAP_V4L2)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            caps.append(cap)
        return caps
    except Exception as e:
        print(f"Error initializing cameras: {e}")
        return []

def handle_camera_failure(cap, cam_index, stop_event=None):
    """
    Attempts to recover a disconnected camera.
    Accepts 'stop_event' to allow immediate cancellation during sleep.
    """
    trials = 0
    print(Fore.RED + f"Camera {cam_index} failure detected - attempting recovery...")
    if cap.isOpened():
        cap.release()
    
    time.sleep(0.5)

    while trials <= 30:
        # 1. Check stop signal immediately at start of loop
        if stop_event and stop_event.is_set():
            return None

        print(Fore.WHITE + f"Testing camera index {cam_index} (Attempt {trials+1}/30)")
        new_cap = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW)

        if new_cap.isOpened():
            new_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            new_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            print(Fore.GREEN + f"Camera {cam_index} recovered!")
            return new_cap
        
        # 2. SMART SLEEP: Sleep in small chunks to verify stop_event
        # Instead of time.sleep(5), we sleep 0.1s fifty times.
        sleep_duration = trials + 1
        for _ in range(int(sleep_duration * 10)): 
            if stop_event and stop_event.is_set():
                print(Fore.YELLOW + "Recovery cancelled by user.")
                return None
            time.sleep(0.1)

        trials += 1
        
    raise RuntimeError(Fore.RED + f"Failed to recover camera {cam_index}")