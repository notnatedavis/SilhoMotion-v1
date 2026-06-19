# pose/detector.py

# Pluggable pose detection: MediaPipe or fallback (OpenCV face detection)

import cv2
import logging
import numpy as np

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Base class
# ----------------------------------------------------------------------

class PoseDetector:
    # Abstract interface for pose/head detection
    def detect(self, frame):
        # Return a dict of joint names -> (x, y) pixel coordinates, or None."""
        raise NotImplementedError

    def detect_head(self, frame):
        # Return (center_x, center_y, radius) or (None, None, 0_
        raise NotImplementedError

# ----------------------------------------------------------------------
# MediaPipe implementation
# ----------------------------------------------------------------------

class MediaPipePoseDetector(PoseDetector) :
    def __init__(self, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        self._mp_pose = None
        self._pose = None
        try:
            import mediapipe as mp
            self._mp_pose = mp.solutions.pose
            self._pose = self._mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                min_detection_confidence=min_detection_confidence,
                min_tracking_confidence=min_tracking_confidence
            )
            logger.info("MediaPipe Pose initialised successfully.")
        except (ImportError, AttributeError) as e:
            logger.error("MediaPipe import failed: %s", e)
            raise RuntimeError("MediaPipe not available") from e

    def detect(self, frame):
        # Run MediaPipe pose detection on an RGB frame
        if self._pose is None:
            return None
        results = self._pose.process(frame)
        if not results.pose_landmarks:
            return None
        landmarks = results.pose_landmarks.landmark
        h, w, _ = frame.shape
        # Map landmark names to indices (MediaPipe Pose)
        # Common mappings: 0 nose, 11 left_shoulder, 12 right_shoulder,
        # 13 left_elbow, 14 right_elbow, 15 left_wrist, 16 right_wrist
        idx = {
            'nose': 0,
            'left_shoulder': 11,
            'right_shoulder': 12,
            'left_elbow': 13,
            'right_elbow': 14,
            'left_wrist': 15,
            'right_wrist': 16
        }
        out = {}
        for name, i in idx.items():
            lm = landmarks[i]
            out[name] = (lm.x * w, lm.y * h) if lm.visibility > 0.5 else None
        return out

    def detect_head(self, frame):
        # Use nose and shoulders to estimate head centre and radius
        landmarks = self.detect(frame)
        if not landmarks:
            return None, None, 0
        nose = landmarks.get('nose')
        l_shoulder = landmarks.get('left_shoulder')
        r_shoulder = landmarks.get('right_shoulder')
        if nose is None:
            if l_shoulder is not None and r_shoulder is not None:
                cx = (l_shoulder[0] + r_shoulder[0]) / 2
                cy = (l_shoulder[1] + r_shoulder[1]) / 2
            else:
                return None, None, 0
        else:
            cx, cy = nose
        # Radius: 30% of shoulder width, or a fallback
        radius = 30.0
        if l_shoulder is not None and r_shoulder is not None:
            dx = r_shoulder[0] - l_shoulder[0]
            dy = r_shoulder[1] - l_shoulder[1]
            dist = (dx*dx + dy*dy) ** 0.5
            if dist > 0:
                radius = dist * 0.3
                radius = max(15.0, min(80.0, radius))
        return cx, cy, radius

# ----------------------------------------------------------------------
# Fallback using OpenCV face detection
# ----------------------------------------------------------------------

class FallbackPoseDetector(PoseDetector):
    def __init__(self, cascade_path=None):
        # Use OpenCV's default Haar cascade for face detection
        if cascade_path is None:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        if self.face_cascade.empty():
            logger.warning("Face cascade could not be loaded. Head detection disabled.")
        else:
            logger.info("OpenCV face cascade loaded for fallback head detection.")

    def detect(self, frame):
        # No skeleton landmarks
        return None

    def detect_head(self, frame):
        # Detect the largest face and return its centre and radius
        if self.face_cascade.empty():
            return None, None, 0
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1,
                                                   minNeighbors=5, minSize=(50, 50))
        if len(faces) == 0:
            return None, None, 0
        # Pick the largest face (by area)
        (x, y, w, h) = max(faces, key=lambda rect: rect[2] * rect[3])
        cx = x + w / 2
        cy = y + h / 2
        radius = max(w, h) / 2 * 1.2  # slightly larger
        radius = max(15.0, min(80.0, radius))
        return cx, cy, radius

# ----------------------------------------------------------------------
# Factory
# ----------------------------------------------------------------------

def get_default_detector():
    # Return a PoseDetector instance: MediaPipe if available, otherwise fallback."""
    try:
        detector = MediaPipePoseDetector()
        # Quick test to see if it actually works (optional)
        # We'll assume it works if constructed without error.
        return detector
    except RuntimeError:
        logger.info("MediaPipe not available; using fallback face detector.")
        return FallbackPoseDetector()