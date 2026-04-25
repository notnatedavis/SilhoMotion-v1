# camera/mapper.py

# Applies a projective transformation to contour points, mapping them
#    from camera image space to the projector screen coordinate system.

# ----- Imports -----
import cv2
import numpy as np
import logging

# ----- Logger -----
logger = logging.getLogger(__name__)

class Mapper :
    # Transforms points using a previously computed homography matrix

    def __init__(self, homography) :
        self.H = homography
        logger.debug("Mapper initialised with homography matrix.")

    def map_points(self, contour_points) :
        # Transform a list of (x,y) contour points into projector coordinates.
        # Returns a list of (x,y) tuples in the same order.
        
        if not contour_points :
            return []
        pts = np.array(contour_points, dtype=np.float32).reshape(-1, 1, 2)
        transformed = cv2.perspectiveTransform(pts, self.H)
        result = [tuple(pt[0]) for pt in transformed]
        logger.debug("Mapped %d points.", len(result))
        return result