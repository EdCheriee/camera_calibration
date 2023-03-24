import argparse
from flask import Flask

app = Flask(__name__)

def create_gstreamer_pipeline(
    sensor_id=0,
    capture_width=1920,
    capture_height=1080,
    display_width=960,
    display_height=540,
    framerate=30,
    flip_method=0,
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

def run_arguments():
    
    edge_length = None
    n_height = None
    n_width = None
    output_disp = False
    
    parser = argparse.ArgumentParser(description='Camera calibration script.')
    parser.add_argument('--display_image', help='Display the camera image.')
    parser.add_argument('-s', '--edge_length', type=float, help='Edge length in cm')
    parser.add_argument('-h', '--height_squares', type=int, help='Number of inner squares vertically.')
    parser.add_argument('-w', '--width_squares', type=int, help='Number of inner squares horizontally.')
    
    args = parser.parse_args()

    # Assign passed values
    if args.display_image:
        output_disp = True
    elif args.edge_length != None:
        edge_length = args.edge_length
    elif args.height_squares != None:
        n_height = args.height_squares
    elif args.width_squares != None:
        n_width = args.width_squares
    
    return output_disp, edge_length, n_height, n_width

if __name__ == "__main__":
    # Get runtime arguments
    output_disp, edge_length, n_height, n_width = run_arguments()
    # Create GStreamer pipeline
    g_pipe = create_gstreamer_pipeline()

    cam_stream = CameraStream(g_pipe, True)
    