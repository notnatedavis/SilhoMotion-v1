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

    def __init__(self, camera_index=0, varThreshold=16, detectShadows=False,
                 history=500, min_area=500, epsilon_factor=0.005) :
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            raise CameraNotFoundError(f"Cannot open camera index {camera_index}")
        logger.info("Camera %d opened successfully.", camera_index)

        # Background subtractor (Mixture of Gaussians)
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=history, varThreshold=varThreshold, detectShadows=detectShadows
        )
        # Store parameters for later updates
        self.varThreshold = varThreshold
        self.detectShadows = detectShadows
        self.history = history
        self.min_area = min_area
        self.epsilon_factor = epsilon_factor
        logger.debug("Background subtractor initialised (varThresh=%.1f, shadows=%s, hist=%d).",
                     varThreshold, detectShadows, history)

    def read_frame(self) :
        # Capture a frame and return (raw_frame, silhouette_binary_mask)
        ret, frame = self.cap.read()
        if not ret:
            logger.warning("Failed to grab frame.")
            return None, None

        # Apply background subtraction
        fg_mask = self.bg_subtractor.apply(frame)
        # Optional: morphological cleanup to reduce noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        cleaned = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        return frame, cleaned

    def extract_contour(self, mask) :
        # Find the largest external contour from the binary mask.
        # Returns a list of (x, y) points after simplification.
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours :
            return []
        # Largest contour
        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) < self.min_area :
            return []
        # Simplify polygon
        epsilon = self.epsilon_factor * cv2.arcLength(largest, True)
        approx = cv2.approxPolyDP(largest, epsilon, True)
        points = [tuple(pt[0]) for pt in approx]
        logger.debug("Extracted contour with %d points.", len(points))
        return points

    def release(self) :
        # Release the camera resource
        if self.cap.isOpened() :
            self.cap.release()
            logger.info("Camera released.")

    # ----- Live parameter updates -----
    def update_bg_params(self, varThreshold=None, detectShadows=None, history=None) :
        """Update background subtractor parameters on the fly."""
        if varThreshold is not None :
            self.bg_subtractor.setVarThreshold(float(varThreshold))
            self.varThreshold = varThreshold
        if detectShadows is not None :
            self.bg_subtractor.setDetectShadows(bool(detectShadows))
            self.detectShadows = detectShadows
        if history is not None :
            self.bg_subtractor.setHistory(int(history))
            self.history = history
        logger.debug("BG parameters updated: varThresh=%.1f, shadows=%s, hist=%d",
                     self.varThreshold, self.detectShadows, self.history)

    def update_contour_params(self, min_area=None, epsilon_factor=None) :
        """Update contour extraction parameters."""
        if min_area is not None :
            self.min_area = int(min_area)
        if epsilon_factor is not None :
            self.epsilon_factor = float(epsilon_factor)
        logger.debug("Contour params updated: min_area=%d, epsilon=%.4f",
                     self.min_area, self.epsilon_factor)