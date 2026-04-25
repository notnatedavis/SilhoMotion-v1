# camera/calibrator.py

# Detects a QR code in a single frame. The homography is later computed
#    using the found corners and the known projector rectangle.

# ----- Imports -----
import cv2
import numpy as np
import logging
from camera.exceptions import CalibrationError

# ----- Logger -----
logger = logging.getLogger(__name__)

class Calibrator :
    # Computes homography between camera image and projector screen using a QR marker

    def __init__(self) :
        self.qr_detector = cv2.QRCodeDetector()
        logger.debug("QR code detector initialised.")

    def detect_qr(self, frame) :
        # Return 4 corner points (Nx2) if a QR code is found, otherwise None.
        # Does not loop – the caller handles frame grabbing and timeout.
        
        data, points, _ = self.qr_detector.detectAndDecode(frame)
        if points is not None :
            logger.info("QR code detected. Data: %s", data)
            return points.reshape((-1, 2))   # 4 corners (x,y)
        return None

    def compute_homography(self, qr_corners, projector_resolution) :
        # Calculate perspective transformation from QR corners (camera space)
        # to the known projector rectangle.
        
        proj_corners = np.array([
            [0, 0],
            [projector_resolution[0], 0],
            [projector_resolution[0], projector_resolution[1]],
            [0, projector_resolution[1]]
        ], dtype=np.float32)

        qr_corners = np.array(qr_corners, dtype=np.float32)
        H, _ = cv2.findHomography(qr_corners, proj_corners)
        logger.debug("Homography computed.")
        return H