# Camera calibration using OpenCV, Gstreamer and Flask
This tool is made for doing calibration on machines that don't have screen and you do not want/can't using xserver for forwarding the output. Instead, using a different machine that is on the same network as the device calibrating, in my case Jetson Nano 4GB, stream the calibration footage to the network using Flask.

## Running the calibration
```cam_script.py``` script is used for running the calibration and ```camera_calibration_result_viewer.py``` is used for applying the results on the footage for inspection.

The calibration script comes with these possible arguments:
```
usage: cam_script.py [-h] [-d] -c CALIBRATION_MODE [-s EDGE_LENGTH]
                     [-vs VERTICAL_SQUARES] [-hs HORIZONTAL_SQUARES]

Camera calibration script.

required argument:
  -c, CALIBRATION MODE  Select operational mode (the integer value) of the calibration 
                        script:
                        - STREAM_CALIBRATION (1) -> performing live calibration using streamed footage.
                        - CALIBRATION_ON_PRERECORDED_IMAGES (2) -> perform calibration using images saved in calib_images directory
                        - COLLECT_CALIBRATION_IMAGES (3) -> collect number of images for using offline calibration afterwards.

optional arguments:
  -h, --help            show this help message and exit.
  -d                    Enable debug options: delays, prints, debug windows.
  -s EDGE_LENGTH, --edge_length EDGE_LENGTH
                        Edge length in cm.
  -vs VERTICAL_SQUARES, --vertical_squares VERTICAL_SQUARES
                        Number of inner squares vertically.
  -hs HORIZONTAL_SQUARES, --horizontal_squares HORIZONTAL_SQUARES
                        Number of inner squares horizontally.
```

## Calibration results
The calibration script will create a folder in a root directory of the repository called **calib_data**. In there you can find matrices and other results gathered through the calibration process. These are being replaced everytime the ```cam_script.py``` is run, so please backup previous runs if you wish so.