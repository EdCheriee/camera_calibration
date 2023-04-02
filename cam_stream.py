from flask import Flask, Response
import threading
from queue import Queue

lock = threading.Lock()

class CameraStream():
    def __init__(self, video_stream: str = '/', port: int = 8000, debug = False):
        self.frame_q = Queue(maxsize=1)
        self.stream = False
        self.port = port
        self.debug = debug
        self.video_stream = video_stream
        self.app = Flask(__name__)
        
        @self.app.route('/' + self.video_stream)
        def streaming():
            return Response(self.generate_frame(), mimetype = "multipart/x-mixed-replace; boundary=frame")
    
    def start(self):
        self.stream = True
        self.run()
        
    def stop(self):
        self.stream = False
        self.frame_q.put(None)
        self.app.do_teardown_appcontext()
        print('Stopping stream...')
        
    def __del__(self):
        self.stop()
        
    def run(self, host='0.0.0.0'):
        self.app.run(host=host, port=self.port)
        
    def generate_frame(self):
        while self.stream:
            with lock:
                if self.frame_q.empty():
                    continue
                frame = self.frame_q.get()
                
            if frame is None:
                break
            
            if self.debug:
                print('Streaming')
                
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')    
        
    def push_frame(self, frame):
        with lock:
            if self.frame_q.full():
                self.frame_q.get()
            self.frame_q.put(frame)
            
    
            