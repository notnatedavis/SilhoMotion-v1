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

    def __init__(self, gravity=(0, 500)) :
        self.space = pymunk.Space()
        self.space.gravity = gravity
        logger.info("Physics space created with gravity %s.", gravity)

    def add_obstacle(self, contour_points) :
        # Add a static obstacle from a contour (list of (x,y) tuples).
        # Creates a series of line segments representing the silhouette boundary.
        
        if len(contour_points) < 2 :
            return
        # Convert to list of pymunk.Vec2d
        verts = [pymunk.Vec2d(float(p[0]), float(p[1])) for p in contour_points]
        for i in range(len(verts) - 1):
            seg = pymunk.Segment(self.space.static_body, verts[i], verts[i+1], 2)
            seg.friction = 1.0
            self.space.add(seg)
        logger.debug("Added obstacle with %d segments.", len(verts)-1)

    def step(self, dt) :
        # Advance simulation by dt seconds.
        # On Pymunk error, log and raise SimulationStepError.
        
        try :
            self.space.step(dt)
        except Exception as e :
            logger.exception("Physics step failed.")
            raise SimulationStepError(f"Simulation step error: {e}") from e