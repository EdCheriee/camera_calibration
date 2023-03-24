import cv2
import threading

lock = threading.Lock()

class CameraCapture:
    def __init__(self, gstreamer_str: str, name: str = '', debug=False):
        # TODO: Add name to associated frame
        self.name = name
        self.video_capture = cv2.VideoCapture(gstreamer_str, cv2.CAP_GSTREAMER)
        # TODO: add debug windows
        self.debug = debug

    def __del__(self):
        self.video_capture.release()
        
    def next_frame(self):
        if self.video_capture.isOpen():
            with lock:
                success, frame = self.video_capture.read()
        
        if not success:
            return None
        else:
            return frame
    
    def encode_frame(self, frame):    
        success_encode, encoded_frame = cv2.imencode('.jpg', frame)
        
        if not success_encode:
            return bytearray()
        else:
            return bytearray(encoded_frame)