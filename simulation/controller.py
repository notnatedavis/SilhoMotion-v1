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
import mediapipe as mp
from common import Config
from camera.capture import SilhouetteCapture, CameraNotFoundError
from physics.simulation import PhysicsWorld
from simulation.renderer import Renderer

# ----- Logger -----
logger = logging.getLogger(__name__)

class SimulationController:
    # Manages the full simulation loop: camera -> physics -> rendering.

    def __init__(self, canvas: tk.Canvas, window: tk.Toplevel, config: Config,
                 camera_obj: SilhouetteCapture,
                 on_stop_callback=None):
        try:
            self.mp_pose = mp.solutions
            self.pose = self.mp_pose.Pose(...)
        except AttributeError:
            raise ImportError(
                "MediaPipe 'solutions' module not found. "
                "Ensure mediapipe is installed (pip install mediapipe) and "
                "that no local file shadows the package."
            )
        
        """
        Initialise the simulation controller.

        Args:
            canvas: Tkinter Canvas for rendering.
            window: Toplevel window hosting the canvas.
            config: Configuration object.
            camera_obj: An already connected SilhouetteCapture instance.
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

        # ---- Pose detection with MediaPipe ----
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        logger.info("MediaPipe Pose initialised.")

        # ---- Control flags ----
        self.running = False
        self.paused = False
        self.live_camera = True          # Start with live camera ON by default
        self.draw_skeleton = False
        self.skeleton_color = "Cyan"     # default

        # ---- State variables ----
        self.latest_frame = None          # Raw camera frame (for background)
        self.head_center = None           # (x, y) in canvas coordinates
        self.head_radius = 0.0
        self.pose_landmarks = None        # dict of joint pixel coords (or None)

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

    def _update(self):
        if not self.running:
            return

        # Process capture queue for latest frame and pose data
        try:
            data = self.capture_queue.get_nowait()
            if data is not None:
                self.latest_frame, pose_norm = data
                # Convert normalized landmarks to pixel coordinates
                if pose_norm is not None:
                    self.pose_landmarks = self._normalized_to_pixel(pose_norm)
                else:
                    self.pose_landmarks = None
        except queue.Empty:
            pass

        # Compute head center and radius from pose landmarks
        head_center = None
        head_radius = 0.0
        if self.pose_landmarks is not None:
            head_center, head_radius = self._compute_head_from_pose(self.pose_landmarks)

        # Physics step
        if not self.paused:
            # Update head circle in physics if skeleton is enabled
            if self.draw_skeleton and head_center is not None and head_radius > 0:
                self.physics.set_head_circle(head_center[0], head_center[1], head_radius)
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

        # Prepare pose drawing data (only if skeleton enabled)
        pose_draw = self.pose_landmarks if self.draw_skeleton else None

        # Render everything
        self.renderer.update(
            background_image=bg_frame,
            head_center=head_center if self.draw_skeleton else None,
            head_radius=head_radius if self.draw_skeleton else 0,
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

                # Perform pose detection on the frame (MediaPipe expects RGB)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.pose.process(rgb)

                pose_norm = None
                if results.pose_landmarks:
                    # Extract relevant landmarks with visibility threshold
                    landmarks = results.pose_landmarks.landmark
                    # Map landmark indices to names
                    indices = {
                        'nose': 0,
                        'left_shoulder': 11,
                        'right_shoulder': 12,
                        'left_elbow': 13,
                        'right_elbow': 14,
                        'left_wrist': 15,
                        'right_wrist': 16,
                    }
                    pose_norm = {}
                    for name, idx in indices.items():
                        lm = landmarks[idx]
                        if lm.visibility >= 0.5:
                            pose_norm[name] = (lm.x, lm.y)   # normalized 0..1
                        else:
                            pose_norm[name] = None

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

    def _normalized_to_pixel(self, pose_norm):
        """Convert normalized landmarks (0..1) to pixel coordinates using current canvas size."""
        w = self.renderer.width
        h = self.renderer.height
        if w <= 0 or h <= 0:
            return None
        pixel = {}
        for name, coords in pose_norm.items():
            if coords is not None:
                x, y = coords
                pixel[name] = (x * w, y * h)
            else:
                pixel[name] = None
        return pixel

    def _compute_head_from_pose(self, pose_pixel):
        """Determine head center and radius from pose landmarks (pixel coords)."""
        nose = pose_pixel.get('nose')
        l_shoulder = pose_pixel.get('left_shoulder')
        r_shoulder = pose_pixel.get('right_shoulder')

        # Head center: prefer nose, else midpoint of shoulders
        center = None
        if nose is not None:
            center = nose
        elif l_shoulder is not None and r_shoulder is not None:
            center = ((l_shoulder[0] + r_shoulder[0]) / 2,
                      (l_shoulder[1] + r_shoulder[1]) / 2)

        if center is None:
            return None, 0.0

        # Head radius: based on shoulder distance or default
        radius = 30.0  # fallback
        if l_shoulder is not None and r_shoulder is not None:
            dx = r_shoulder[0] - l_shoulder[0]
            dy = r_shoulder[1] - l_shoulder[1]
            shoulder_dist = (dx*dx + dy*dy) ** 0.5
            if shoulder_dist > 0:
                radius = shoulder_dist * 0.3   # ~30% of shoulder width
                radius = max(15.0, min(80.0, radius))  # clamp
        # If only one shoulder, use default (already set)

        return center, radius