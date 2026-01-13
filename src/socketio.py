import time
import cv2
import socketio
import os


class socketio_client():
    def __init__(self):

        self.image_sub = None
        self.mode = "restriction"
        
        self.io = socketio.Client(reconnection=True, reconnection_delay=0)
        self.serialNo = os.getenv("serialNo")
        self.robotKey = os.getenv("robotKey")
        self.serverUrl = os.getenv("serverUrl")

        self.last_status_emit = 0
        self.last_status_value = None
        self.last_frame_time = 0

        self.io.on('robot:videoMode', self.on_mode_switch)
        self.io.connect(
            self.serverUrl,
            auth={'serialNo': self.serialNo, 'robotKey': self.robotKey},
            wait=False,
        )
        self.events()

    def events(self):
        @self.io.event
        def connect():
            print("Connected to server.")

        @self.io.event
        def disconnect():
            print("Disconnected from server.")

    def send_frames(self, recieved_frame):
        if True:
            current_time = time.time()
            if current_time - self.last_frame_time < 0.06:
                return
            self.last_frame_time = current_time
            
            try:
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 60]
                _, buf = cv2.imencode('.jpg', recieved_frame,encode_param)  
                self.io.emit('robot:frame', buf.tobytes())
            except Exception:
                pass

    def send_alert(self, recieved_frame):
        if True:
            try:
                _, buf = cv2.imencode('.jpg', recieved_frame)
                self.io.emit('robot:alert', buf.tobytes())
            except Exception:
                pass

    def on_mode_switch(self, data):
            print(f"recieved Switch Command: {data}")
            self.mode = data
            
            
    def get_mode(self):
        return self.mode