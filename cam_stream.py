import cv2
import sys
import os
import threading
from flask import Response, Flask

# Image frame sent to the Flask object
video_frame = None

# Use locks for thread-safe viewing of frames in multiple browsers
thread_lock = threading.Lock()

# Create the Flask object for the application
app = Flask(__name__)

def create_gstreamer_pipeline(
    sensor_id=0,
    capture_width=1920,
    capture_height=1080,
    display_width=960,
    display_height=540,
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


def captureFrames():
    global video_frame, thread_lock

    # Video capturing from OpenCV
    video_capture = cv2.VideoCapture(create_gstreamer_pipeline(), cv2.CAP_GSTREAMER)

    while True and video_capture.isOpened():
        return_key, frame = video_capture.read()
        if not return_key:
            break

        # Create a copy of the frame and store it in the global variable,
        # with thread safe access
        with thread_lock:
            video_frame = frame.copy()
        
        key = cv2.waitKey(30) & 0xff
        if key == 27:
            break

    video_capture.release()
        
def encodeFrame():
    global thread_lock
    while True:
        # Acquire thread_lock to access the global video_frame object
        with thread_lock:
            global video_frame
            if video_frame is None:
                continue
            return_key, encoded_image = cv2.imencode(".jpg", video_frame)
            if not return_key:
                continue

        # Output image as a byte array
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
            bytearray(encoded_image) + b'\r\n')

@app.route("/")
def streamFrames():
    return Response(encodeFrame(), mimetype = "multipart/x-mixed-replace; boundary=frame")

# check to see if this is the main thread of execution
if __name__ == '__main__':
    try:
        os.system('service nvargus-daemon restart')
        # Create a thread and attach the method that captures the image frames
        process_thread = threading.Thread(target=captureFrames)
        process_thread.daemon = True

        # Start the thread
        process_thread.start()

        # start the stream using Flask
        # While it can be run on any feasible IP, IP = 0.0.0.0 renders the web app on
        # the host machine's localhost and is discoverable by other machines on the same network 
        app.run("0.0.0.0", port="8000")
    except (KeyboardInterrupt, SystemExit):
        os.system('service nvargus-daemon restart')
        sys.exit()