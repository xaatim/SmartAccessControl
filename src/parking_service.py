import cv2
import pickle
import numpy as np
import threading
from .camera_utils import handle_camera_failure

POSITIONS_FILE = "data/CarParkPos"

# --- TUNING ---
# If a spot has more than this many keypoints, it is OCCUPIED.
# Adjust this based on your camera resolution.
KEYPOINT_THRESHOLD = 10 

def psdc_classify(image_gray, parking_spots, sift):
    """
    Classifies spots based on the number of SIFT keypoints inside the polygon.
    Source: Adapted from parkingspotdetectornoml MiniProject
    """
    # 1. Detect all features in the whole image (efficient)
    keypoints = sift.detect(image_gray, None)
    
    free_spots = 0
    status_list = []

    for i, poly in enumerate(parking_spots):
        points_inside = 0
        
        # 2. Check which keypoints fall inside this polygon
        # Optimization: Only check keypoints near the polygon bounding rect first could be faster,
        # but for <50 spots, this loop is fine.
        for kp in keypoints:
            if cv2.pointPolygonTest(poly, kp.pt, False) >= 0:
                points_inside += 1
        
        # 3. Decision
        if points_inside < KEYPOINT_THRESHOLD:
            status_list.append({'poly': poly, 'free': True, 'score': points_inside})
            free_spots += 1
        else:
            status_list.append({'poly': poly, 'free': False, 'score': points_inside})

    return free_spots, status_list

def run_parking_smart_service(stop_event, caps, camera_indices):
    print(">>> Smart Feature-Based Parking Service Started")
    cam_idx = camera_indices[-1]
    
    # Initialize SIFT Detector (built into OpenCV)
    sift = cv2.SIFT_create()

    try:
        with open(POSITIONS_FILE, 'rb') as f:
            pos_list = pickle.load(f)
    except:
        print("[Error] No spots defined. Run setup_parking.py!")
        pos_list = []

    while not stop_event.is_set():
        if len(caps) <= cam_idx: break
        ret, frame = caps[cam_idx].read()
        if not ret:
            caps[cam_idx] = handle_camera_failure(caps[cam_idx], cam_idx, stop_event)
            continue

        # Convert to Grayscale for SIFT
        imgGray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Run Classification
        if pos_list:
            count, results = psdc_classify(imgGray, pos_list, sift)
            
            # Draw Results
            for item in results:
                poly = item['poly']
                score = item['score']
                
                if item['free']:
                    color = (0, 255, 0) # Green
                    text = f"Free ({score})"
                else:
                    color = (0, 0, 255) # Red
                    text = f"Busy ({score})"
                
                cv2.polylines(frame, [poly], True, color, 2)
                
                # Draw score for debugging/tuning
                # Calculate center
                M = cv2.moments(poly)
                if M["m00"] != 0:
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                    cv2.putText(frame, str(score), (cX - 10, cY), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

            # Dashboard
            cv2.rectangle(frame, (0, 0), (300, 50), (0,0,0), -1)
            cv2.putText(frame, f"FREE: {count}/{len(pos_list)}", (20, 35), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow("Smart Parking Monitor", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            stop_event.set()
            break

    print("Smart Parking Service Stopped.")