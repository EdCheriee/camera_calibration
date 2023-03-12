# MIT License
# Copyright (c) 2019-2022 JetsonHacks

# Using a CSI camera (such as the Raspberry Pi Version 2) connected to a
# NVIDIA Jetson Nano Developer Kit using OpenCV
# Drivers for the camera and OpenCV are included in the base image

import cv2
import argparse
import numpy as np
import sys

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

def show_camera(enable_display=False, frame=None):
    
    if enable_display and frame is not None:
        window_title = 'Calibration image'
        window_handle = cv2.namedWindow(window_title, cv2.WINDOW_AUTOSIZE)
        while True:
            # Check to see if the user closed the window
            # Under GTK+ (Jetson Default), WND_PROP_VISIBLE does not work correctly. Under Qt it does
            # GTK - Substitute WND_PROP_AUTOSIZE to detect if window has been closed by user
            if cv2.getWindowProperty(window_title, cv2.WND_PROP_AUTOSIZE) >= 0:
                cv2.imshow(window_title, frame)
            else:
                break 
            keyCode = cv2.waitKey(10) & 0xFF
            # Stop the program on the ESC key or 'q'
            if keyCode == 27 or keyCode == ord('q'):
                break

        
        
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

def calibration(cam):
    ret_val, frame = cam.read()
    
    return frame

         
if __name__ == "__main__":
    # Get runtime arguments
    output_disp, edge_length, n_height, n_width = run_arguments()
    # Create GStreamer pipeline
    g_pipe = create_gstreamer_pipeline()
    # Open the camera
    cam = cv2.VideoCapture(g_pipe)
    
    try:
        if cam.isOpened():
            frame = calibration(cam)
        else:
            print("Error: Unable to open camera")
            sys.exit(-1)
    finally:     
        cam.release()
        cv2.destroyAllWindows()