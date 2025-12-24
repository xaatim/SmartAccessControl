import cv2
import time
from .recognition import process_detected_face
from .camera_utils import handle_camera_failure
from .door_control import open_remote_door  # <--- Door Control Import

def run_restriction_service(stop_event, caps, camera_indices, app_insight, task_queue):
    print(">>> Restriction/Security Service Started (Cam 2)")
    cam_idx = camera_indices[0]
    
    last_alert_time = 0
    
    # --- Door Control Timers ---
    last_door_open_time = 0
    door_cooldown_seconds = 5  # Wait 5 seconds before opening again

    while not stop_event.is_set():
        if len(caps) <= cam_idx:
            print(f"Error: Restriction Camera Index {cam_idx} out of range.")
            time.sleep(5)
            continue

        ret, frame = caps[cam_idx].read()
        
        # --- ORIGINAL CAMERA FAILURE HANDLER (Preserved) ---
        if not ret:
            # Pass stop_event so it can exit loop immediately on Ctrl+C
            recovered_cap = handle_camera_failure(caps[cam_idx], cam_idx, stop_event)
            
            # If user pressed Ctrl+C during recovery, it returns None -> Break Loop
            if recovered_cap is None:
                break 

            caps[cam_idx] = recovered_cap
            continue
        # ---------------------------------------------------

        # Face Analysis
        faces = app_insight.get(frame)
        for face in faces:
            # We capture 'name' here instead of ignoring it with '_'
            last_alert_time, anomaly_detected, name = process_detected_face(
                frame, face, task_queue, last_alert_time, purpose='authorization'
            )
            
            if anomaly_detected:
                print("!!! ALERT: Unauthorized Personnel Detected !!!")
            else:
                # --- DOOR OPENING LOGIC ---
                # 1. Check if name is valid (not Unknown) - though process_detected_face usually handles 'Unknown' as anomaly
                # 2. Check Cooldown to prevent spamming
                current_time = time.time()
                if (current_time - last_door_open_time) > door_cooldown_seconds:
                    print(f">>> Access Granted: {name}. Opening Door...")
                    open_remote_door()
                    last_door_open_time = current_time

        cv2.imshow("Security Feed", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            stop_event.set()
            break
            
    print("Restriction Service Stopped.")