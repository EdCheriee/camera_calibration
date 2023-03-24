from cam_capture import CameraCapture
from cam_stream import CameraStream

class CameraCalib:
    def __init__(self, gstreamer_str: str, calib_image_stream: str = '/calibration_image', camera_image_stream: str = '/camera_raw'):
        self.cam = CameraCapture(gstreamer_str=gstreamer_str)
        
        
    def run(self):
        
        frame = self.cam.next_frame()
        