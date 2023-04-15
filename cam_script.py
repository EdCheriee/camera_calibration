import argparse
from cam_capture import CameraCapture
from cam_stream import CameraStream
from cam_calib import CameraCalibration
import threading
import time
import sys
import os
from enum import Enum
import select
import sys
import termios
import tty
import shutil


script_dir = os.path.abspath(os.path.dirname(__file__))

class ScriptRunningModes(Enum):
    STREAM_CALIBRATION = 1
    CALIBRATION_ON_PRERECORDED_IMAGES = 2
    COLLECT_CALIBRATION_IMAGES = 3

def run_arguments():
    edge_length = None
    n_height = None
    n_width = None
    calibration_mode = None
    debug = False
    
    parser = argparse.ArgumentParser(description='Camera calibration script.')
    parser.add_argument('-d', help='Enable debug options: delays, prints, debug windows.', action='store_true')
    parser.add_argument('-c', '--calibration_mode', type=int, help='Run calibration in either of the three modes: streaming live (1), pre-recorder (2), collect calibration images (3)', required=True)
    parser.add_argument('-s', '--edge_length', type=float, help='Edge length in cm')
    parser.add_argument('-vs', '--vertical_squares', type=int, help='Number of inner squares vertically.')
    parser.add_argument('-hs', '--horizontal_squares', type=int, help='Number of inner squares horizontally.')
    
    args = parser.parse_args()

    # Assign passed values
    if args.d:
        debug = True
    elif args.calibration_mode != None:
        calibration_mode = ScriptRunningModes(args.calibration_mode)
        if calibration_mode not in ScriptRunningModes:
            calibration_mode = None
    elif args.edge_length != None:
        edge_length = args.edge_length
    elif args.vertical_squares != None:
        n_height = args.vertical_squares
    elif args.horizontal_squares != None:
        n_width = args.horizontal_squares
    
    return debug, calibration_mode, edge_length, n_height, n_width

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

def calibration_and_encoding(original_frame, cam_calib, cam_cap):
    cam_calib.find_checkerboard_corners(original_frame)
    ret, corner_frame = cam_calib.get_corner_image()
    
    if ret:
        frame = cam_cap.encode_frame(frame=corner_frame)
    else:
        frame = cam_cap.encode_frame(frame=original_frame)
    
    return frame


def run_live_calibration(cam_cap, cam_calib, cam_stream):
    # Collect enough images
    while not cam_calib.finished_collecting_samples():
        try:
            original_frame = cam_cap.latest_frame()

            frame = calibration_and_encoding(original_frame, cam_calib, cam_cap)
            
            cam_stream.push_frame(frame) 

            time.sleep(2)
            
        except KeyboardInterrupt:
            cam_stream.stop()
            cam_cap.stop()
            sys.exit(-1)

    return cam_cap.latest_frame()

def run_prerecorded_calibration(cam_cap, cam_calib, cam_stream):
    images = load_images(cam_cap)
    
    for image in images:   
        try:
            
            frame = calibration_and_encoding(image, cam_calib, cam_cap)
            
            cam_stream.push_frame(frame) 

            time.sleep(2)
            
        except KeyboardInterrupt:
            cam_stream.stop()
            cam_cap.stop()
            sys.exit(-1)
    
    return image

def run_collect_images(cam_cap, cam_stream):
    
    # Set the terminal to raw mode to read keys without waiting for Enter to be pressed
    old_settings = termios.tcgetattr(sys.stdin)
    tty.setraw(sys.stdin.fileno())
    
    try:
        calibration_image_directory = os.path.join(script_dir, 'calib_images')
        
        if os.path.exists(calibration_image_directory):
            shutil.rmtree(calibration_image_directory)
            
        os.mkdir(calibration_image_directory)
        
        saved_images = 0
        
        while saved_images < 50:
            original_frame = cam_cap.latest_frame()
            frame = cam_cap.encode_frame(frame=original_frame)
            cam_stream.push_frame(frame)
            
            if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
                key = sys.stdin.read(1)
                if key == 's':
                    calibration_image_name = 'image_' + str(saved_images) + '.jpg'
                    if cam_cap.save_image(calibration_image_name, calibration_image_directory):
                        saved_images += 1
                    print('\rNumber of saved images: %d' % saved_images)
                elif key == 'q':
                    print('\rQuit command received early, this will exit the script...')
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                    sys.exit(0)
                
            time.sleep(0.2)
        
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        
    except OSError as e:
        print(e)
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        sys.exit(-1)
    
    except KeyboardInterrupt:
        cam_stream.stop()
        cam_cap.stop()
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        sys.exit(-1)
    


def load_images(cam_cap):
    image_extensions = ['.jpg', '.jpeg', '.bmp', '.png']
    recorded_images_for_calib = os.path.join(script_dir, 'calib_images')
    
    if not os.path.exists(recorded_images_for_calib):
        print('calib_images directory does not exist. Check that calib_images directory exists')
        sys.exit(-1)
    elif len(os.listdir(recorded_images_for_calib)) == 0:
        print('No images found in calib_images.')
        sys.exit(-1)
    else:
        images = [cam_cap.load_image(os.path.join(recorded_images_for_calib, image)) for image in os.listdir(recorded_images_for_calib)]

        return images

if __name__ == "__main__":
    # Get runtime arguments
    debug, calibration_mode, edge_length, n_height, n_width = run_arguments()
    
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
    
    # Run selected mode
    if calibration_mode is ScriptRunningModes.STREAM_CALIBRATION:
        last_image = run_live_calibration(cam_cap, cam_calib, cam_stream)
    elif calibration_mode is ScriptRunningModes.CALIBRATION_ON_PRERECORDED_IMAGES:
        last_image = run_prerecorded_calibration(cam_cap, cam_calib, cam_stream)
    elif calibration_mode is ScriptRunningModes.COLLECT_CALIBRATION_IMAGES:
        run_collect_images(cam_cap, cam_stream)
    else:
        print('Incorrect mode selected. Exiting...')
        sys.exit(-1)
       
    # Perform calibration                
    cam_cap.stop()
    cam_stream.stop()
    
    if calibration_mode is not ScriptRunningModes.COLLECT_CALIBRATION_IMAGES:
        cam_calib.calibration(last_image)
        cam_calib.reprojection_error()

    sys.exit(0)
                