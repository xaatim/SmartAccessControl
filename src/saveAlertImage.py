import os
import time
from datetime import datetime
import cv2


def save_alert_image(frame, task_queue):
    alert_dir = os.path.join(
        os.path.dirname(__file__), 
        '.', 
        'images'
    )
    os.makedirs(alert_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    image_path = os.path.join(alert_dir, f"intruder_{timestamp}.jpg")
    
    cv2.imwrite(image_path, frame)
    task_queue.put((image_path, time.time()))