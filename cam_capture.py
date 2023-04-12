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
        self.frame = None

    def __del__(self):
        self.video_capture.release()
    
    def capturing(self):
        while self.video_capture.isOpened():
            with lock:
                if self.debug:
                    print('Capturing frame.')
                success, self.frame = self.video_capture.read()
    
    def stop(self):
        self.video_capture.release()
        
    def latest_frame(self, encode: bool = False):
        # If successfully read a new frame
        with lock:
            if self.frame is None:
                return None
            
            if encode:
                return self.encode_frame(self.frame)
            else:
                return self.frame
    
    def encode_frame(self, frame):
        if frame is not None:  
            success_encode, encoded_frame = cv2.imencode('.jpg', frame)
            
            if self.debug:
                print('Encoding frame.')
            
            if not success_encode:
                return None
            else:
                return bytearray(encoded_frame)
            
    def load_image(self, image_path):
        return cv2.imread(image_path)
    
    def save_image(self, image_name, path_to_save_in):

        with lock:
            if self.frame is not None: 
                calibration_image_path =  os.path.join(path_to_save_in, image_name)  
                cv2.imwrite(calibration_image_path, self.frame, [cv2.IMWRITE_PNG_COMPRESSION, 3])
                return True
            else:
                return False