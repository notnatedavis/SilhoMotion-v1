# camera/calibrator.py

# Uses a QR code or similar marker to compute the homography between 
#    camera image space and projector screen space, enabling spatial 
#    mapping of user position onto the simulation

# ----- Imports -----
import cv2
import numpy as np
import time
import logging
from camera.exceptions import CalibrationError

# ----- Logger -----
logger = logging.getLogger(__name__)

class Calibrator :
    # Computes homography between camera image and projector screen using a QR marker

    def __init__(self) :
        self.qr_detector = cv2.QRCodeDetector()
        logger.debug("QR code detector initialised.")

    def detect_qr_with_timeout(self, frame, timeout_sec=10) :
        # Attempt to detect a QR code in the frame within a time window.
        # Returns the bounding box corners if found, else raises CalibrationError.
        
        start = time.time()
        while time.time() - start < timeout_sec :
            data, points, _ = self.qr_detector.detectAndDecode(frame)
            if points is not None :
                logger.info("QR code detected. Data: %s", data)
                return points.reshape((-1, 2)) # 4 corners (x,y)
            time.sleep(0.1) # small delay to avoid busy‑waiting
        raise CalibrationError(f"QR code not found within {timeout_sec} seconds.")

    def compute_homography(self, qr_corners, projector_resolution) :
        # Calculate perspective transformation from QR corners (camera space)
        # to the known projector rectangle.
        
        # Projector rectangle corners in screen coordinates (order: top‑left to bottom‑left)
        proj_corners = np.array([
            [0, 0],
            [projector_resolution[0], 0],
            [projector_resolution[0], projector_resolution[1]],
            [0, projector_resolution[1]]
        ], dtype=np.float32)

        # Ensure QR corners are float32
        qr_corners = np.array(qr_corners, dtype=np.float32)
        H, _ = cv2.findHomography(qr_corners, proj_corners)
        logger.debug("Homography computed.")
        return H