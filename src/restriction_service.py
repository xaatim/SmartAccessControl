import cv2
import time
from .recognition import process_detected_face
from .camera_utils import handle_camera_failure

def run_restriction_service(stop_event, caps, camera_indices, app_insight, task_queue):
    print(">>> Restriction/Security Service Started (Cam 2)")
    cam_idx = camera_indices[0]
    last_alert_time = 0
    
    while not stop_event.is_set():
        if len(caps) <= cam_idx:
            print(f"Error: Restriction Camera Index {cam_idx} out of range.")
            time.sleep(5)
            continue

        ret, frame = caps[cam_idx].read()
        if not ret:
            # --- UPDATED LINE: Pass stop_event ---
            recovered_cap = handle_camera_failure(caps[cam_idx], cam_idx, stop_event)
            
            # If user pressed Ctrl+C during recovery, it returns None
            if recovered_cap is None:
                break 

            caps[cam_idx] = recovered_cap
            continue

        # (Rest of your code remains the same...)
        faces = app_insight.get(frame)
        for face in faces:
            last_alert_time, anomaly_detected, _ = process_detected_face(
                frame, face, task_queue, last_alert_time, purpose='authorization'
            )
            if anomaly_detected:
                print("!!! ALERT: Unauthorized Personnel Detected !!!")

        cv2.imshow("Security Feed", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            stop_event.set()
            break
            
    print("Restriction Service Stopped.")