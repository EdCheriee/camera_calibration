from flask import Flask, Response
import threading
from queue import Queue

lock = threading.Lock()

app = Flask(__name__)


class CameraStream():
    def __init__(self, source_name: str, video_stream: str = '/', debug = False):
        self.frame_q = Queue(maxsize=1)
        self.source_name = source_name
        self.stream = False
        self.debug = debug
        self.video_stream = video_stream
    
    def start(self):
        self.stream = True
        
        
    def stop(self):
        self.stream = False
        self.frame_q.put(None)
        
    def generate_frame(self):
        while self.stream:
            frame = self.frame_q.get()
            if frame is None:
                break
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')    
        
    def push_frame(self, frame):
        with lock:
            self.frame_q.put(frame)
            
    def define_routes(self):
        @app.route(self.video_stream)
        def stream():
            return Response(self.generate_frame(), mimetype = "multipart/x-mixed-replace; boundary=frame")
                