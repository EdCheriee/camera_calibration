import cv2
import numpy as np
import threading
import os
import sys

lock = threading.Lock()

class CameraCalibration:
    def __init__(self, edge_length: float = 0.108, n_calib_images: int = 30, n_vertical: int = 8, n_horizontal: int = 6, save_calib: bool = False, run_with_cuda: bool = False, debug: bool = False):
        self.save_calib = save_calib
        self.run_with_cuda = run_with_cuda
        self.debug = debug
        self.frame = None
        self.checkerboard_size = (n_horizontal, n_vertical)
        self.found_corners = False
        # Finishing criteria
        self.criteria = (cv2.TermCriteria_EPS + cv2.TERM_CRITERIA_MAX_ITER, n_calib_images, 0.001)
        self.calib_image_goal = n_calib_images
        self.image_counter = 0
        # Checkerboard matrix setup
        self.objp = np.zeros((n_horizontal * n_vertical, 3), np.float32)
        self.objp[:, :2] = np.mgrid[0:n_horizontal, 0:n_vertical].T.reshape(-1, 2)
        
        # Multiply each point of checkerboard matrix by edge length
        self.objp = self.objp * edge_length
        
        # Create arrays to store object points and image points from all calibration frames
        self.objpoints = [] # 3D points in real world space
        self.imgpoints = [] # 2D points in image plane
        
        # List of names for saving calibration files
        self.calibration_file_names = ['cam_matrix.txt', 'dist_coeffs.txt', 'r_vecs.txt', 't_vecs.txt'] 
        
        # Calibration matrices
        self.newcammat = None
        self.cam_mat = None
        self.dist_coeff = None
        self.rvecs = None
        self.rvecs = None
            
    def find_checkerboard_corners(self, frame):
        if self.run_with_cuda:
        
            # TODO: Add cuda version of finding corners
            print("TODO: Cuda")
        
        else:
            self._find_checkerboard_corners(frame)

            
    def draw_checkerboard_corners(self, frame, corners, ret):
        self.frame = cv2.drawChessboardCorners(frame, self.checkerboard_size, corners, ret)
      
        
    def _find_checkerboard_corners(self, frame):
    
        # Convert to grayscale
        gray_scale_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
        # Locate the corners
        ret, corners = cv2.findChessboardCorners(gray_scale_frame, self.checkerboard_size, None)
        
        # If corners are found, add object points and image points
        if ret == True:
            # if self.debug:
            print("Found corners.")
            self.objpoints.append(self.objp)
            corners2 = cv2.cornerSubPix(gray_scale_frame, corners, (11, 11), (-1, -1), self.criteria)
            self.imgpoints.append(corners2)

            self.image_counter+=1
            
            # Draw and display the corners
            self.draw_checkerboard_corners(gray_scale_frame, corners2, ret)
            self.found_corners = True
        else:
            # if self.debug:
            print("Not found corners.")

    def get_new_cam_matrix(self, root_folder_path: str = '', width: int = 1920, height: int = 1080):
        if not root_folder_path:
            print('UNDISTORT: No path provided.')
            sys.exit(-1)
        
        if width <= 0 and height <= 0:
            print('UNDISTORT: Incorrect image size provided.')
            sys.exit(-1)
            
        self.cam_mat, self.dist_coeff, self.rvecs, self.rvecs = self._load_calib(root_folder_path=root_folder_path)
        
        self.newcammat = cv2.getOptimalNewCameraMatrix(self.cam_mat, self.dist_coeff, (width, height), 1, (width, height))
                   
    def undistortion(self, frame):
        if self.cam_mat is not None and self.dist_coeff is not None and self.newcammat is not None:
            undistorted_frame = cv2.undistort(frame, self.cam_mat, self.dist_coeff)
            return undistorted_frame           
        else:
            return None
        
    # def reprojection_error(self, undistorted_frame):
        

    def calibration(self, frame):
        if len(frame.shape) > 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        print('Performing calibration...')
        ret, camera_mtx, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(self.objpoints, self.imgpoints, frame.shape[::-1], None, None)
        print('Calibration complete')   
        if self.save_calib:
            if self.debug:
                print('Saving calibration')
            self._save_calib(ret, camera_mtx, dist_coeffs, rvecs, tvecs)      

    def _save_calib(self, ret, cam_mat, dist_coef, rvecs, tvecs):
        file_dir_path = os.path.abspath(os.path.dirname(__file__))
        calib_data_path = os.path.join(file_dir_path, 'calib_data')

        
        if not os.path.exists(calib_data_path):
            os.mkdir(calib_data_path)

        # Remove old files of previous calibrations
        calibration_file_paths = self.check_for_calibration_files(root_folder_path=calib_data_path, remove_file=True)
        
        if calibration_file_paths != None or len(calibration_file_paths) > 0:
            print('RMS: ', ret)
            np.savetxt(calibration_file_paths[0], cam_mat, delimiter=',')
            np.savetxt(calibration_file_paths[1], dist_coef, delimiter=',')  
            np.savetxt(calibration_file_paths[2], rvecs, delimiter=',') 
            np.savetxt(calibration_file_paths[3], tvecs, delimiter=',')
        else:
            print('Failed to save calibration files. Check paths for saving data.')
        
    def _load_calib(self, root_folder_path: str = ''):
        
        calibration_file_paths = self.check_for_calibration_files(root_folder_path=root_folder_path)
        
        if calibration_file_paths is not None or len(calibration_file_paths) > 0:
            cam_mat = np.loadtxt(calibration_file_paths[0], dtype=float, delimiter=',')
            dist_coeff = np.loadtxt(calibration_file_paths[1], dtype=float, delimiter=',')
            rvecs = np.loadtxt(calibration_file_paths[2], dtype=float, delimiter=',')
            tvecs = np.loadtxt(calibration_file_paths[3], dtype=float, delimiter=',')
            return [cam_mat, dist_coeff, rvecs, tvecs]
        else:
            return [None, None, None, None]
          

    def check_for_calibration_files(self, root_folder_path: str = '', remove_file: bool = False):
        calibration_file_paths = []
        
        if not os.path.exists(root_folder_path):
            return None
        
        for file in self.calibration_file_names:
            file_path = os.path.join(root_folder_path, file)
            if os.path.exists(file_path) and remove_file:
                os.remove(file_path)
            calibration_file_paths.append(file_path)
            
        return calibration_file_paths
    
    
    def finished_collecting_samples(self):
        if self.image_counter >= self.calib_image_goal:
            if self.debug:
                print('Complete')
            return True
        else:
            return False

    def get_corner_image(self):
        frame = None
        image_found = False
        if self.found_corners:
            frame = self.frame.copy()
            self.found_corners = False
            image_found = True
            
        return image_found, frame