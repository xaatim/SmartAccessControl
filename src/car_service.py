import cv2
import time
from colorama import Fore
from .car_identification import IdentifyCar, plate_list
from .camera_utils import handle_camera_failure

def run_car_service(stop_event, caps, camera_indices):
    print(">>> Car Identification Service Started (Cam 0)")
    
    # Car ID uses Camera Index 0 (based on your old code)
    cam_idx = camera_indices[0]
    
    last_detected_plate = None
    
    while not stop_event.is_set():
        # Safety check
        if len(caps) <= cam_idx:
            print(f"Error: Car Camera Index {cam_idx} out of range.")
            time.sleep(5)
            continue

        ret, frame = caps[cam_idx].read()
        if not ret:
            caps[cam_idx] = handle_camera_failure(caps[cam_idx], cam_idx)
            continue

        detected_plate = IdentifyCar(frame)

        if detected_plate and detected_plate != last_detected_plate:
            print(Fore.GREEN + f"CAR DETECTED: {detected_plate}" + Fore.RESET)
            last_detected_plate = detected_plate
        
        # Reset if list is cleared
        if detected_plate is None and len(plate_list) == 0:
            last_detected_plate = None

        # Optional: Show feed
        cv2.imshow("Car Feed", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            stop_event.set()
            break
            
    print("Car Service Stopped.")