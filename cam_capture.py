import cv2
import threading
import os

lock = threading.Lock()

'''
Gstreamer camera capture.
@gstreamer_str: Gstreamer pipeline string for launching the camera
@name: Variable for naming debug windows
@debug: Flag to enable debug windows
'''
class CameraCapture:
    def __init__(self, gstreamer_str: str, name: str = '', debug=False):
        # os.system('service nvargus-daemon restart')
        # TODO: Add name to associated frame
        self.name = name
        self.video_capture = cv2.VideoCapture(gstreamer_str, cv2.CAP_GSTREAMER)
        # TODO: add debug windows
        self.debug = debug

    def __del__(self):
        self.video_capture.release()
        
    def next_frame(self, encode: bool = False):
        if self.video_capture.isOpened():
            with lock:
                success, frame = self.video_capture.read()
        
        # If successfully read a new frame
        if not success:
            return None
        
        if encode:
            return self.encode_frame(frame)
        else:
            return frame
    
    def encode_frame(self, frame):    
        success_encode, encoded_frame = cv2.imencode('.jpg', frame)
        
        if not success_encode:
            return None
        else:
            return bytearray(encoded_frame)