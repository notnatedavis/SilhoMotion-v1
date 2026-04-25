# camera/capture.py

# Handles real-time frame grabbing from the camera (OpenCV VideoCapture), 
#    applies background subtraction to extract the user’s 
#    silhouette/contour

# ----- Imports -----
import cv2
import numpy as np
import logging
from camera.exceptions import CameraNotFoundError

# ----- Logger -----
logger = logging.getLogger(__name__)

# ----- Custom exception -----
class VideoCaptureError(CameraNotFoundError) :
    # Raised when video capture cannot be initialised
    pass

# ----- Silhouette Capture -----
class SilhouetteCapture :
    # Handles real‑time frame grabbing and silhouette extraction using background subtraction

    def __init__(self, camera_index=0) :
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            raise CameraNotFoundError(f"Cannot open camera index {camera_index}")
        logger.info("Camera %d opened successfully.", camera_index)

        # Background subtractor (Mixture of Gaussians)
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500, varThreshold=16, detectShadows=False
        )
        logger.debug("Background subtractor initialised.")

    def read_frame(self) :
        # Capture a frame and return the silhouette binary mask
        ret, frame = self.cap.read()
        if not ret:
            logger.warning("Failed to grab frame.")
            return None

        # Apply background subtraction
        fg_mask = self.bg_subtractor.apply(frame)
        # Optional: morphological cleanup to reduce noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        cleaned = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        return cleaned

    def release(self) :
        # Release the camera resource
        if self.cap.isOpened() :
            self.cap.release()
            logger.info("Camera released.")