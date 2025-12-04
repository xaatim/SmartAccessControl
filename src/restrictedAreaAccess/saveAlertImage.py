import os
import time
from datetime import datetime
import cv2


def save_alert_image(frame, task_queue):
    """Save intruder image and queue for notification"""
    alert_dir = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'alert_images'
    )
    os.makedirs(alert_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    image_path = os.path.join(alert_dir, f"intruder_{timestamp}.jpg")
    
    cv2.imwrite(image_path, frame)
    task_queue.put((image_path, time.time()))