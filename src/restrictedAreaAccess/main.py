import time
import colorama
import cv2
from insightface.app import FaceAnalysis
from recognition import process_detected_face
from queue import Queue
from colorama import Fore, Back, Style



colorama.init()

app_insight = FaceAnalysis(
    name='buffalo_sc',
    allowed_modules=['detection', 'recognition']
)
app_insight.prepare(ctx_id=-1)

def initialize_camera():
    """Configure and initialize video capture"""
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG')) #type:ignore
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    return cap

def handle_camera_failure(cap):
    """Attempt to recover from camera failure"""
    print(Fore.RED + "⚠️ Camera failure detected - attempting recovery...")
    cap.release()
    time.sleep(0.5)
    
    for i in range(10):
        print(Fore.WHITE + f"Testing camera index {i}")
        new_cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if new_cap.isOpened():
            return new_cap
    raise RuntimeError(Fore.RED + "Failed to initialize any camera")



def AuthorizedPersonnel(task_queue):
  cap = initialize_camera()
  last_alert_time = 0
    
  try:
      while True:
          ret, frame = cap.read()
          if not ret:
              cap = handle_camera_failure(cap)
              continue
          
          faces = app_insight.get(frame)
          
          for face in faces:
              last_alert_time, anomlay_detected = process_detected_face(
                  frame, face, task_queue, last_alert_time
              )
          cv2.imshow("test",frame)
          if cv2.waitKey(1) & 0xFF == ord('q'):
              break
          cap.release()
          cv2.destroyAllWindows()
              
  finally:
        cap.release()
        print("Camera resources released")
        
  return anomlay_detected 
        
        
AuthorizedPersonnel(task_queue=Queue())