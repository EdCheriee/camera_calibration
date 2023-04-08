import argparse
from cam_capture import CameraCapture
from cam_stream import CameraStream
from cam_calib import CameraCalibration
import threading
import time
import sys

def run_arguments():
    edge_length = None
    n_height = None
    n_width = None
    save_calib = False
    debug = False
    
    parser = argparse.ArgumentParser(description='Camera calibration script.')
    parser.add_argument('-d', help='Enable debug options: delays, prints, debug windows.', action='store_true')
    parser.add_argument('-s', '--edge_length', type=float, help='Edge length in cm')
    parser.add_argument('-vs', '--vertical_squares', type=int, help='Number of inner squares vertically.')
    parser.add_argument('-hs', '--horizontal_squares', type=int, help='Number of inner squares horizontally.')
    parser.add_argument('--save_calib', help='Save calibration images.')
    
    args = parser.parse_args()

    # Assign passed values
    if args.d:
        debug = True
    elif args.edge_length != None:
        edge_length = args.edge_length
    elif args.vertical_squares != None:
        n_height = args.vertical_squares
    elif args.horizontal_squares != None:
        n_width = args.horizontal_squares
    elif args.save_calib != None:
        save_calib = True
    
    return debug, edge_length, n_height, n_width, save_calib

def create_gstreamer_pipeline(
    sensor_id=0,
    capture_width=1920,
    capture_height=1080,
    display_width=1920,
    display_height=1080,
    framerate=30,
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
    # Get runtime arguments
    debug, edge_length, n_height, n_width, save_calib = run_arguments()
    
    # Create GStreamer pipeline
    g_pipe = create_gstreamer_pipeline()

    # Create Camera capture object
    cam_cap = CameraCapture(g_pipe, debug=debug)
    
    # Create streaming object
    cam_stream = CameraStream(debug=debug)
    
    # Create camera calibration object
    cam_calib = CameraCalibration(save_calib = True, debug=debug)
        
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

            cam_calib.find_checkerboard_corners(original_frame)
            ret, corner_frame = cam_calib.get_corner_image()
            
            if ret:
                frame = cam_cap.encode_frame(frame=corner_frame)
            else:
                frame = cam_cap.encode_frame(frame=original_frame)
            
            cam_stream.push_frame(frame) 

            time.sleep(1)
            
        except KeyboardInterrupt:
            cam_stream.stop()
            cam_cap.stop()
            sys.exit(-1)
       
    # Perform calibration                
    cam_cap.stop()
    cam_stream.stop()
    cam_calib.calibration(original_frame)

    sys.exit(0)
                