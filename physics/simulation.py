# physics/simulation.py

# Contains a 2D physics world (e.g. Pymunk) that updates object positions, \
#    reacts to user “obstacle” regions derived from the camera, and 
#    provides updated scene data for rendering

# ----- Imports -----
import pymunk
import logging
from physics.exceptions import SimulationStepError

# ----- Logger -----
logger = logging.getLogger(__name__)

class PhysicsWorld :
    # 2D physics world using Pymunk, reacting to silhouette obstacles

    def __init__(self, gravity=(0, 500), elasticity=0.8) :
        self.space = pymunk.Space()
        self.space.gravity = gravity
        self._obstacle_shapes = []   # keep track of added segment shapes
        self._dynamic_bodies = []    # list of (body, shape) for dynamic objects

        # Wall management
        self._wall_shapes = []       # store wall segment shapes
        self._wall_bounds = None     # (x, y, width, height) for current walls
        self.elasticity = elasticity # default bounce factor for all shapes

        # Head circle (single static circle)
        self._head_circle_shape = None

        logger.info("Physics space created with gravity %s and elasticity %.2f.",
                    gravity, elasticity)

    # ----- Wall management -----
    def set_wall_bounds(self, x, y, width, height) :
        """
        Define the rectangular boundaries of the simulation area.
        Creates four static wall segments (left, right, top, bottom).
        Replaces any existing walls.
        """
        # Remove old walls
        self._clear_walls()

        # Ensure minimum size to avoid invalid segments
        if width < 5 or height < 5 :
            logger.warning("Wall bounds too small (%dx%d), skipping.", width, height)
            return

        # Offset slightly to avoid balls getting stuck at edges
        margin = 1.0
        left = x + margin
        right = x + width - margin
        top = y + margin
        bottom = y + height - margin

        # Define four segments using the static body
        static = self.space.static_body
        segments = [
            ((left, top), (right, top)),       # top
            ((right, top), (right, bottom)),   # right
            ((right, bottom), (left, bottom)), # bottom
            ((left, bottom), (left, top))      # left
        ]

        for a, b in segments :
            seg = pymunk.Segment(static, a, b, radius=0)
            seg.friction = 1.0
            seg.elasticity = self.elasticity
            self.space.add(seg)
            self._wall_shapes.append(seg)

        self._wall_bounds = (x, y, width, height)
        logger.debug("Walls updated: %dx%d at (%d,%d)", width, height, x, y)

    def _clear_walls(self) :
        """Remove all wall shapes from the space."""
        for shape in self._wall_shapes :
            self.space.remove(shape)
        self._wall_shapes.clear()
        self._wall_bounds = None

    # ----- Obstacle (silhouette) management (DEPRECATED, kept for compatibility) -----
    def add_obstacle(self, contour_points) :
        # Add a static obstacle from a contour (list of (x,y) tuples).
        # Creates a series of line segments representing the silhouette boundary,
        # including the closing edge from last to first vertex.
        # This method is kept for backward compatibility but is not used in the new head-tracking flow.
        if len(contour_points) < 2 :
            return
        verts = [pymunk.Vec2d(float(p[0]), float(p[1])) for p in contour_points]
        for i in range(len(verts) - 1):
            seg = pymunk.Segment(self.space.static_body, verts[i], verts[i+1], 2)
            seg.friction = 1.0
            seg.elasticity = self.elasticity
            self.space.add(seg)
            self._obstacle_shapes.append(seg)
        seg = pymunk.Segment(self.space.static_body, verts[-1], verts[0], 2)
        seg.friction = 1.0
        seg.elasticity = self.elasticity
        self.space.add(seg)
        self._obstacle_shapes.append(seg)
        logger.debug("Added closed obstacle with %d vertices.", len(verts))

    def clear_obstacles(self) :
        # Remove all previously added obstacle shapes from the space.
        for shape in self._obstacle_shapes :
            self.space.remove(shape)
        self._obstacle_shapes.clear()
        logger.debug("Cleared all obstacle segments.")

    # ----- Head circle (new) -----
    def set_head_circle(self, center_x, center_y, radius) :
        """
        Replace the head circle obstacle with a new one at the given position and radius.
        If radius <= 0, removes the circle.
        """
        self.clear_head_circle()
        if radius <= 0 or center_x is None or center_y is None:
            return
        static_body = self.space.static_body
        circle = pymunk.Circle(static_body, radius, offset=(center_x, center_y))
        circle.friction = 1.0
        circle.elasticity = self.elasticity
        self.space.add(circle)
        self._head_circle_shape = circle
        logger.debug("Head circle set at (%.1f, %.1f) radius %.1f", center_x, center_y, radius)

    def clear_head_circle(self) :
        """Remove the head circle from the physics space."""
        if self._head_circle_shape is not None:
            self.space.remove(self._head_circle_shape)
            self._head_circle_shape = None
            logger.debug("Head circle removed.")

    # ----- Dynamic objects (balls) -----
    def add_ball(self, x, y, radius=20, mass=2.0) :
        # Add a dynamic circle at (x, y) with given radius and mass.
        body = pymunk.Body(mass, pymunk.moment_for_circle(mass, 0, radius))
        body.position = (x, y)
        shape = pymunk.Circle(body, radius)
        shape.friction = 0.5
        shape.elasticity = self.elasticity
        self.space.add(body, shape)
        self._dynamic_bodies.append((body, shape))
        logger.debug("Added ball at (%.1f, %.1f) radius %.1f", x, y, radius)
        return body, shape

    def get_dynamic_objects(self) :
        # Return a list of (body, shape) for all dynamic objects currently in the world.
        return self._dynamic_bodies

    def clear_dynamic_objects(self) :
        # Remove all dynamic bodies and shapes.
        for body, shape in self._dynamic_bodies :
            self.space.remove(body, shape)
        self._dynamic_bodies.clear()
        logger.debug("Cleared all dynamic objects.")

    # ----- Elasticity control -----
    def set_elasticity(self, value) :
        """
        Update the global elasticity factor.
        Applies to existing walls, obstacles, and dynamic objects.
        """
        self.elasticity = float(value)
        # Update walls
        for shape in self._wall_shapes :
            shape.elasticity = self.elasticity
        # Update obstacles (silhouette segments) – if any
        for shape in self._obstacle_shapes :
            shape.elasticity = self.elasticity
        # Update head circle if present
        if self._head_circle_shape:
            self._head_circle_shape.elasticity = self.elasticity
        # Update dynamic objects (balls)
        for body, shape in self._dynamic_bodies :
            shape.elasticity = self.elasticity
        logger.info("Elasticity updated to %.2f", self.elasticity)

    # ----- Simulation step -----
    def step(self, dt) :
        # Advance simulation by dt seconds.
        # On Pymunk error, log and raise SimulationStepError.
        try :
            self.space.step(dt)
        except Exception as e :
            logger.exception("Physics step failed.")
            raise SimulationStepError(f"Simulation step error: {e}") from e