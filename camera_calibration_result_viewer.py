import os
from cam_capture import CameraCapture
from cam_stream import CameraStream
from cam_calib import CameraCalibration
import threading
import time
import sys

def create_gstreamer_pipeline(
    sensor_id=0,
    capture_width=1920,
    capture_height=1080,
    display_width=960,
    display_height=540,
    framerate=10,
    flip_method=2,
):
    return (
        "nvarguscamerasrc sensor-id=%d !"
        "video/x-raw(memory:NVMM), width=(int)%d, height=(int)%d, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink"
        % (
            sensor_id,
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
    )

if __name__ == "__main__":
    # Path for calibration results
    file_dir_path = os.path.abspath(os.path.dirname(__file__))
    
    # Create camera calibration object
    cam_calib = CameraCalibration() 
    
    if len(cam_calib.check_for_calibration_files(os.path.join(file_dir_path, 'calib_data'))) != 4:
        print('Missing calibration data. Exiting...')
        sys.exit(-1)
      
    # Create GStreamer pipeline
    g_pipe = create_gstreamer_pipeline()

    # Create Camera capture object
    cam_cap = CameraCapture(g_pipe)
    
    # Create streaming object
    cam_stream = CameraStream()
      
    # Start camera streaming
    # Create a thread and attach the method that captures the image frames, to it
    stream_thread = threading.Thread(target=cam_stream.start, daemon=True)
    capturing_thread = threading.Thread(target=cam_cap.capturing, daemon=True)
    
    # Start the thread
    stream_thread.start()
    capturing_thread.start()
      
    # Collect enough images
    while not cam_calib.finished_collecting_samples():
        try:
            original_frame = cam_cap.latest_frame()

            # TODO: Add undistorsion

            frame = cam_cap.encode_frame(frame=original_frame)
            
            cam_stream.push_frame(frame) 

            # if debug:
            time.sleep(1) 
    # Perform calibration                
        except KeyboardInterrupt:
            cam_stream.stop()
    
    cam_cap.stop()
    cam_stream.stop()

    sys.exit(0)
                