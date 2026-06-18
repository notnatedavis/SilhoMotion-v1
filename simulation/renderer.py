# simulation/renderer.py

# Renders the physics world onto a Tkinter Canvas.
# Draws obstacle contours and dynamic objects (circles).
# Also draws a stick figure from MediaPipe Pose landmarks.

# ----- Imports -----
import tkinter as tk
import logging
import pymunk
import cv2
import numpy as np
from PIL import Image, ImageTk

# ----- Logger -----
logger = logging.getLogger(__name__)

class Renderer:
    # Draws physics state on a Tkinter Canvas.

    def __init__(self, canvas: tk.Canvas, width: int, height: int):
        self.canvas = canvas
        self.width = width
        self.height = height
        self._bg_image = None          # PhotoImage reference to avoid garbage collection
        logger.debug("Renderer initialised with size %dx%d.", width, height)

    def resize(self, width: int, height: int):
        # Update canvas size (e.g. when window resizes)
        self.width = width
        self.height = height
        logger.debug("Renderer resized to %dx%d.", width, height)

    def draw_background_image(self, frame: np.ndarray):
        """Draw the given camera frame as the background, stretched to canvas size."""
        if frame is None:
            return
        # Resize frame to canvas dimensions
        resized = cv2.resize(frame, (self.width, self.height), interpolation=cv2.INTER_LINEAR)
        # Convert BGR (OpenCV) to RGB for PIL
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        self._bg_image = ImageTk.PhotoImage(pil_img)
        self.canvas.create_image(0, 0, anchor='nw', image=self._bg_image)

    def draw_dynamic_objects(self, objects):
        # objects: list of (body, shape) where shape is a Circle.
        # Draw each circle as a filled circle.
        for body, shape in objects:
            if isinstance(shape, pymunk.Circle):
                pos = body.position
                radius = shape.radius
                x, y = pos.x, pos.y
                self.canvas.create_oval(x - radius, y - radius,
                                        x + radius, y + radius,
                                        fill="orange", outline="darkorange", width=1)

    def draw_head_circle(self, center_x: float, center_y: float, radius: float, color: str = "Cyan"):
        """Draw a circle representing the tracked head with a transparent fill and thick outline."""
        if radius <= 0 or center_x is None or center_y is None:
            return
        x0 = center_x - radius
        y0 = center_y - radius
        x1 = center_x + radius
        y1 = center_y + radius
        self.canvas.create_oval(x0, y0, x1, y1,
                                outline=color, fill="", width=5)

    def draw_pose(self, landmarks: dict, color: str = "Cyan"):
        """
        Draw a stick figure from MediaPipe Pose landmarks.
        landmarks: dict with keys 'nose', 'left_shoulder', etc.
                   Each value is (x, y) in canvas coordinates or None.
        """
        if not landmarks:
            return

        # Helper to get coords (return None if missing)
        def get(name):
            return landmarks.get(name)

        # Joints (circles)
        joint_radius = 6
        for name, pos in landmarks.items():
            if pos is not None:
                x, y = pos
                self.canvas.create_oval(x - joint_radius, y - joint_radius,
                                        x + joint_radius, y + joint_radius,
                                        fill=color, outline="black", width=1)

        # Bones (lines)
        def draw_line(p1, p2):
            if p1 is not None and p2 is not None:
                self.canvas.create_line(p1[0], p1[1], p2[0], p2[1],
                                        fill=color, width=4)

        # Shoulders
        l_shoulder = get('left_shoulder')
        r_shoulder = get('right_shoulder')
        draw_line(l_shoulder, r_shoulder)

        # Left arm
        l_elbow = get('left_elbow')
        l_wrist = get('left_wrist')
        draw_line(l_shoulder, l_elbow)
        draw_line(l_elbow, l_wrist)

        # Right arm
        r_elbow = get('right_elbow')
        r_wrist = get('right_wrist')
        draw_line(r_shoulder, r_elbow)
        draw_line(r_elbow, r_wrist)

        # Optionally draw nose-to-shoulder? Not required.

    def clear(self):
        # Delete all items on the canvas.
        self.canvas.delete("all")

    def update(self, background_image=None, head_center=None, head_radius=0,
               head_color=None, dynamic_objects=None,
               pose_landmarks=None, pose_color=None):
        """
        Clear and redraw everything.
        Args:
            background_image: numpy array (BGR) from camera, or None.
            head_center: (x, y) tuple or None.
            head_radius: float.
            head_color: string color name for the head outline.
            dynamic_objects: list of (body, shape) for balls.
            pose_landmarks: dict of joint pixel coordinates, or None.
            pose_color: string color name for the stick figure.
        """
        self.clear()
        # Draw background (if provided)
        if background_image is not None:
            self.draw_background_image(background_image)
        # Draw dynamic objects (balls)
        if dynamic_objects:
            self.draw_dynamic_objects(dynamic_objects)
        # Draw head circle (topmost) with transparent fill and thick outline
        if head_center is not None and head_radius > 0:
            self.draw_head_circle(head_center[0], head_center[1], head_radius,
                                  color=head_color if head_color else "Cyan")
        # Draw pose (stick figure) if provided
        if pose_landmarks:
            self.draw_pose(pose_landmarks, color=pose_color if pose_color else "Cyan")