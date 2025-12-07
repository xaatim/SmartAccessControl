import time
import colorama
import cv2
from insightface.app import FaceAnalysis
from src.recognition import process_detected_face
from queue import Queue
from colorama import Fore
from datetime import datetime


numCameras = 3
cameraIndex = [0,1,2]
caps = []
colorama.init()
app_insight = FaceAnalysis(
    name='buffalo_s',
    allowed_modules=['detection', 'recognition']
)
app_insight.prepare(ctx_id=-1)


def initialize_cameras():
    for i in range(numCameras):
        camIndex = i
        cap = cv2.VideoCapture(camIndex, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))  # type:ignore
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        caps.append(cap)


def handle_camera_failure(cap, cameraIndex):
    print(Fore.RED + "Camera failure detected - attempting recovery...")
    cap.release()
    time.sleep(0.5)

    for _ in range(10):
        print(Fore.WHITE + f"Testing camera index {cameraIndex}")
        new_cap = cv2.VideoCapture(cameraIndex, cv2.CAP_DSHOW)
        if new_cap.isOpened():
            return new_cap
    raise RuntimeError(Fore.RED + "Failed to initialize any camera")


def controlUnit(task_queue):
    initialize_cameras()
    last_alert_time = 0

    try:
        while True:
            retCam1, frame1 = caps[0].read()
            if not retCam1:
                caps[0] = handle_camera_failure(caps[0], cameraIndex[0])
                continue
            retCam2, frame2 = caps[1].read()
            if not retCam2:
                caps[1] = handle_camera_failure(caps[1], cameraIndex[1])
                continue
            # retCam3, frame3 = caps[2].read()
            # if not retCam3:
            #     caps[2] = handle_camera_failure(caps[2], cameraIndex[2])
            #     continue

            cam1Faces = app_insight.get(frame1)
            cam2Faces = app_insight.get(frame2)

            for cam1face in cam1Faces:
                last_alert_time, cam1_anomlay_detected, cam1label = process_detected_face(
                    frame1, cam1face, task_queue, last_alert_time, purpose='authorization'
                )
                if cam1_anomlay_detected:
                    print("unauthrized personnel")

            for cam2face in cam2Faces:
                _, cam2AnomalyDetected, cam2Labels = process_detected_face(
                    frame2, cam2face, task_queue, last_alert_time, purpose='attendence'
                )
                if cam2AnomalyDetected:
                    print("unregistred employee")
                elif not cam2AnomalyDetected:
                    attendenceTime = datetime.now().strftime('%Y%m%d_%H%M%S')
                    print(f"{cam2Labels}: attended at {attendenceTime}")

            cv2.imshow("test", frame1)
            cv2.imshow("test_frame2", frame2)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                for cap in caps:
                    cap.release()
                    cv2.destroyAllWindows()
                break

    finally:
        for cap in caps:
            cap.release()
            cv2.destroyAllWindows()
        print("Camera resources released")


controlUnit(task_queue=Queue())
