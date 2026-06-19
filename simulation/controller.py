# simulation/controller.py

# Coordinates camera, physics, and rendering in a single loop.
# Runs camera capture in a separate thread to avoid blocking the GUI.

# ----- Imports -----
import threading
import queue
import time
import logging
import tkinter as tk
import cv2
from common import Config
from camera.capture import SilhouetteCapture, CameraNotFoundError
from physics.simulation import PhysicsWorld
from simulation.renderer import Renderer
from pose.detector import PoseDetector, get_default_detector

# ----- Logger -----
logger = logging.getLogger(__name__)

class SimulationController:
    # Manages the full simulation loop: camera -> physics -> rendering.

    def __init__(self, canvas: tk.Canvas, window: tk.Toplevel, config: Config,
                 camera_obj: SilhouetteCapture,
                 pose_detector: PoseDetector = None,
                 on_stop_callback=None):
        """
        Initialise the simulation controller.

        Args:
            canvas: Tkinter Canvas for rendering.
            window: Toplevel window hosting the canvas.
            config: Configuration object.
            camera_obj: An already connected SilhouetteCapture instance.
            pose_detector: Optional PoseDetector instance. If not provided,
                           the default detector (MediaPipe if available) is used.
            on_stop_callback: Optional callable invoked when stop() is called.
        """
        self.canvas = canvas
        self.window = window
        self.config = config
        self.on_stop_callback = on_stop_callback

        # ---- Camera (use the provided object) ----
        self.camera = camera_obj
        if self.camera is None:
            raise ValueError("Camera object must be provided and connected.")

        # ---- Physics ----
        self.physics = PhysicsWorld(gravity=config.PHYSICS_GRAVITY)

        # ---- Renderer ----
        self.renderer = Renderer(canvas, canvas.winfo_width(), canvas.winfo_height())

        # ---- Pose detection (pluggable) ----
        self.pose_detector = pose_detector if pose_detector is not None else get_default_detector()
        logger.info("Pose detector: %s", self.pose_detector.__class__.__name__)

        # ---- Control flags ----
        self.running = False
        self.paused = False
        self.live_camera = True          # Start with live camera ON by default
        self.draw_skeleton = False
        self.skeleton_color = "Cyan"     # default

        # ---- State variables ----
        self.latest_frame = None          # Raw camera frame (for background)
        self.pose_landmarks = None        # dict of joint pixel coords (frame space)

        # ---- Threading ----
        self.capture_queue = queue.Queue(maxsize=1)
        self.stop_event = threading.Event()
        self.capture_thread = None

        # ---- Event bindings ----
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        self._update_id = None
        self.window.protocol("WM_DELETE_WINDOW", self.stop)

        logger.info("SimulationController initialised with provided camera.")

    # ----- Public control methods -----
    def start(self):
        if self.running:
            logger.warning("Simulation already running.")
            return
        self.running = True
        self.stop_event.clear()
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        self._update_walls()
        self._schedule_update()
        logger.info("Simulation loop started.")

    def stop(self):
        if not self.running:
            return
        self.running = False
        self.stop_event.set()
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=2.0)
        # Do NOT release the camera – it is owned by the main menu
        if self._update_id:
            self.canvas.after_cancel(self._update_id)
            self._update_id = None
        try:
            self.window.destroy()
        except tk.TclError:
            pass
        if self.on_stop_callback:
            self.on_stop_callback()
        logger.info("Simulation stopped.")

    def set_paused(self, paused: bool):
        self.paused = paused
        logger.info("Pause set to %s.", paused)

    def set_live_camera(self, enabled: bool):
        self.live_camera = enabled
        logger.info("Live camera background set to %s.", enabled)

    def set_skeleton(self, enabled: bool):
        self.draw_skeleton = enabled
        if not enabled:
            self.physics.clear_head_circle()
        logger.info("Draw skeleton set to %s.", enabled)

    def set_skeleton_color(self, color: str):
        self.skeleton_color = color
        logger.info("Skeleton color set to %s.", color)

    def set_gravity_scale(self, scale: float):
        gx, gy = self.config.PHYSICS_GRAVITY
        self.physics.space.gravity = (gx, gy * scale)
        logger.info("Gravity scale set to %.2f.", scale)

    def set_elasticity(self, value: float):
        self.physics.set_elasticity(value)
        logger.info("Elasticity set to %.2f.", value)

    def add_test_ball(self):
        import random
        x = random.randint(100, self.renderer.width - 100)
        y = random.randint(100, self.renderer.height - 100)
        self.physics.add_ball(x, y, radius=20, mass=2.0)

    # ----- Internal methods -----
    def _update_walls(self):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w > 1 and h > 1:
            self.physics.set_wall_bounds(0, 0, w, h)

    def _on_resize(self, event):
        if not self.running:
            return
        w, h = event.width, event.height
        if w > 1 and h > 1:
            self.physics.set_wall_bounds(0, 0, w, h)
            self.renderer.resize(w, h)

    def _on_canvas_click(self, event):
        if not self.running or self.paused:
            return
        import random
        radius = random.randint(12, 30)
        mass = radius / 10.0
        self.physics.add_ball(event.x, event.y, radius=radius, mass=mass)

    def _schedule_update(self):
        if not self.running:
            return
        interval = int(1000 / self.config.FRAME_RATE)
        self._update_id = self.canvas.after(interval, self._update)

    def _frame_to_canvas(self, point, frame_shape, canvas_shape):
        """Convert a point (x,y) from frame pixel space to canvas pixel space."""
        fx, fy = point
        fh, fw = frame_shape[:2]
        cw, ch = canvas_shape
        if fw <= 0 or fh <= 0:
            return point
        scale_x = cw / fw
        scale_y = ch / fh
        return (fx * scale_x, fy * scale_y)

    def _scale_radius(self, radius, frame_shape, canvas_shape):
        """Scale a radius from frame space to canvas space."""
        fh, fw = frame_shape[:2]
        cw, ch = canvas_shape
        if fw <= 0 or fh <= 0:
            return radius
        scale_x = cw / fw
        scale_y = ch / fh
        # Use average scaling to keep proportions
        return radius * (scale_x + scale_y) / 2.0

    def _update(self):
        if not self.running:
            return

        # Process capture queue for latest frame and pose data
        try:
            data = self.capture_queue.get_nowait()
            if data is not None:
                self.latest_frame, pose_norm = data
                # pose_norm is dict of joint names -> (x, y) in frame pixel coordinates
                self.pose_landmarks = pose_norm  # store raw frame coords
        except queue.Empty:
            pass

        if self.latest_frame is None:
            self._schedule_update()
            return

        frame_shape = self.latest_frame.shape
        canvas_shape = (self.renderer.width, self.renderer.height)

        # ---- Get head from pose detector (frame space) ----
        rgb = cv2.cvtColor(self.latest_frame, cv2.COLOR_BGR2RGB)
        hx, hy, hrad = self.pose_detector.detect_head(rgb)

        head_center_canvas = None
        head_radius_canvas = 0.0
        if hx is not None:
            # Convert head center to canvas coordinates
            head_center_canvas = self._frame_to_canvas((hx, hy), frame_shape, canvas_shape)
            head_radius_canvas = self._scale_radius(hrad, frame_shape, canvas_shape)

        # ---- Convert pose landmarks to canvas coordinates (if any) ----
        pose_landmarks_canvas = None
        if self.pose_landmarks is not None:
            pose_landmarks_canvas = {}
            for name, pos in self.pose_landmarks.items():
                if pos is not None:
                    pose_landmarks_canvas[name] = self._frame_to_canvas(pos, frame_shape, canvas_shape)
                else:
                    pose_landmarks_canvas[name] = None

        # ---- Physics step ----
        if not self.paused:
            # Update head circle in physics if skeleton is enabled and we have a head
            if self.draw_skeleton and head_center_canvas is not None and head_radius_canvas > 0:
                self.physics.set_head_circle(head_center_canvas[0], head_center_canvas[1], head_radius_canvas)
            else:
                self.physics.clear_head_circle()

            # Clear any old silhouette obstacles (we no longer use them)
            self.physics.clear_obstacles()

            dt = 1.0 / self.config.FRAME_RATE
            self.physics.step(dt)

        # Resize renderer if needed
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w > 1 and h > 1 and (w != self.renderer.width or h != self.renderer.height):
            self.renderer.resize(w, h)

        # Prepare background image (if live camera is on)
        bg_frame = self.latest_frame if self.live_camera else None

        # Get dynamic objects
        dynamic_objs = self.physics.get_dynamic_objects()

        # Prepare pose drawing data (only if skeleton enabled and we have landmarks)
        pose_draw = pose_landmarks_canvas if (self.draw_skeleton and pose_landmarks_canvas is not None) else None

        # Render everything
        self.renderer.update(
            background_image=bg_frame,
            head_center=head_center_canvas if self.draw_skeleton else None,
            head_radius=head_radius_canvas if self.draw_skeleton else 0,
            head_color=self.skeleton_color if self.draw_skeleton else None,
            dynamic_objects=dynamic_objs,
            pose_landmarks=pose_draw,
            pose_color=self.skeleton_color if self.draw_skeleton else None
        )

        self._schedule_update()

    def _capture_loop(self):
        logger.debug("Capture loop started.")
        while not self.stop_event.is_set():
            try:
                frame, mask = self.camera.read_frame()
                if frame is None:
                    time.sleep(0.01)
                    continue

                # Perform pose detection on the frame (RGB)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pose_norm = self.pose_detector.detect(rgb)

                # Put the frame and pose data into the queue
                if self.capture_queue.full():
                    try:
                        self.capture_queue.get_nowait()
                    except queue.Empty:
                        pass
                self.capture_queue.put_nowait((frame.copy(), pose_norm))

            except Exception as e:
                logger.exception("Error in capture loop: %s", e)
                time.sleep(0.1)
        logger.debug("Capture loop stopped.")