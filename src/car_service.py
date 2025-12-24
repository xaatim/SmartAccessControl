import cv2
import time
from colorama import Fore, Style
from .car_identification import IdentifyCar, plate_list
from .camera_utils import handle_camera_failure
from .vehicle_db import vehicle_db         # <--- DB
from .parking_hardware import parking_gate   # <--- HARDWARE

def run_car_service(stop_event, caps, camera_indices):
    print(">>> Car Identification Service Started (Cam 0)")
    
    cam_idx = camera_indices[0]
    last_detected_plate = None
    
    # Cooldown to prevent spamming the Arduino with 'A' 'A' 'A'
    gate_cooldown_start = 0
    GATE_COOLDOWN_SECONDS = 15 

    while not stop_event.is_set():
        if len(caps) <= cam_idx:
            print(f"Error: Car Camera Index {cam_idx} out of range.")
            time.sleep(5)
            continue

        ret, frame = caps[cam_idx].read()
        if not ret:
            recovered_cap = handle_camera_failure(caps[cam_idx], cam_idx, stop_event)
            if recovered_cap is None: break
            caps[cam_idx] = recovered_cap
            continue

        # 1. Detect Plate using your existing Logic
        detected_plate = IdentifyCar(frame)

        # 2. Process Detection
        if detected_plate:
            # Only process if it's a new plate OR we haven't seen it in a while
            if detected_plate != last_detected_plate:
                
                print(Fore.CYAN + f"Scanning Plate: {detected_plate}..." + Fore.RESET)
                
                # 3. Check Database
                owner = vehicle_db.is_authorized(detected_plate)
                
                if owner:
                    print(Fore.GREEN + f"ACCESS GRANTED: {owner} ({detected_plate})" + Fore.RESET)
                    
                    # 4. Open Gate (Check Cooldown)
                    if time.time() - gate_cooldown_start > GATE_COOLDOWN_SECONDS:
                        parking_gate.authorize_entry()
                        gate_cooldown_start = time.time()
                    else:
                        print(f"Gate is busy/cooling down. Wait {int(GATE_COOLDOWN_SECONDS - (time.time() - gate_cooldown_start))}s")
                        
                else:
                    print(Fore.RED + f"ACCESS DENIED: Unknown Vehicle ({detected_plate})" + Fore.RESET)

                last_detected_plate = detected_plate
        
        # Reset state if the deque is empty (Car left the frame)
        if detected_plate is None and len(plate_list) == 0:
            last_detected_plate = None

        cv2.imshow("Car Feed", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            stop_event.set()
            break
            
    print("Car Service Stopped.")