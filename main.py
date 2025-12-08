import time

import colorama
import cv2
from insightface.app import FaceAnalysis
from src.recognition import process_detected_face
from queue import Queue
from colorama import Fore
from datetime import datetime
from src.car_identification import IdentifyCar
from src.save_alert_image import go

numCameras = 3
cameraIndex = [0, 1, 2]
caps = []
stop_threads = False
colorama.init()
app_insight = FaceAnalysis(
    name='buffalo_s',
    allowed_modules=['detection', 'recognition']
)
app_insight.prepare(ctx_id=-1)

last_alert_time = 0


def initialize_cameras():

    try:
        for i in range(numCameras):
            camIndex = i
            cap = cv2.VideoCapture(camIndex, cv2.CAP_DSHOW)
            # cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))  # type:ignore
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            caps.append(cap)

    except Exception as e:
        print(e)


def handle_camera_failure(cap, cameraIndex):
    global last_alert_time

    trials = 0
    print(Fore.RED + "Camera failure detected - attempting recovery...")
    cap.release()
    time.sleep(0.5)

    while trials <= 30:
        print(Fore.WHITE + f"Testing camera index {cameraIndex}")
        new_cap = cv2.VideoCapture(cameraIndex, cv2.CAP_DSHOW)

        if new_cap.isOpened():
            return new_cap
        time.sleep(trials+1)
        trials += 1
    raise RuntimeError(Fore.RED + "Failed to initialize any camera")


def restriction_handler(task_queue):
    global last_alert_time
    global stop_threads
    while not stop_threads:
        ret, frame = caps[0].read()
        if not ret:
            caps[0] = handle_camera_failure(caps[0], cameraIndex[0])
            continue

        Faces = app_insight.get(frame)

        for face in Faces:
            last_alert_time, anomlay_detected, _ = process_detected_face(
                frame, face, task_queue, last_alert_time, purpose='authorization')

            if anomlay_detected:
                print("unauthrized personnel")

        cv2.imshow("test", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            stop_threads = True
            break


def attendence_handler(task_queue):
    global stop_threads
    global last_alert_time
    while not stop_threads:
        ret, frame = caps[1].read()
        if not ret:
            caps[1] = handle_camera_failure(caps[1], cameraIndex[1])
            continue

        Faces = app_insight.get(frame)

        for face in Faces:
            last_alert_time, AnomalyDetected, Labels = process_detected_face(
                frame, face, task_queue, last_alert_time, purpose='attendence'
            )

            if AnomalyDetected:
                print("unregistred employee")
            elif not AnomalyDetected:
                attendenceTime = datetime.now().strftime('%Y%m%d_%H%M%S')
                print(f"{Labels}: attended at {attendenceTime}")

        cv2.imshow("test_frame2", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            stop_threads = True
            break


def car_identification_handler():
    global stop_threads
    global last_alert_time
    while not stop_threads:
        retCam3, frame3 = caps[2].read()
        if not retCam3:
            caps[2] = handle_camera_failure(caps[2], cameraIndex[2])
            continue
        IdentifyCar(frame3)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            stop_threads = True
            break


def controlUnit(task_queue):
    initialize_cameras()

    try:
        try:
            t1 = go(restriction_handler, task_queue)
            t2 = go(attendence_handler, task_queue)
            t3 = go(car_identification_handler)

            t1.join()
            t2.join()
            t3.join()

        except Exception as e:
            print(e)

    finally:
        for cap in caps:
            cap.release()
            cv2.destroyAllWindows()
        print("Camera resources released")


controlUnit(task_queue=Queue())
