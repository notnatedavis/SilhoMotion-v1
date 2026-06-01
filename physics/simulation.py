# physics/simulation.py

# Contains a 2D physics world (e.g. Pymunk) that updates object positions, \
#    reacts to user “obstacle” regions derived from the camera, and 
#    provides updated scene data for rendering

# ----- Imports -----
import pymunk
import logging
import tkinter.messagebox as msg
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
        # Creates a series of line segments representing the silhouette boundary,
        # including the closing edge from last to first vertex.
        
        if len(contour_points) < 2 :
            return
        # Convert to list of pymunk.Vec2d
        verts = [pymunk.Vec2d(float(p[0]), float(p[1])) for p in contour_points]
        # Add segments between consecutive vertices
        for i in range(len(verts) - 1):
            seg = pymunk.Segment(self.space.static_body, verts[i], verts[i+1], 2)
            seg.friction = 1.0
            self.space.add(seg)
        # Close the polygon: segment from last vertex back to the first
        seg = pymunk.Segment(self.space.static_body, verts[-1], verts[0], 2)
        seg.friction = 1.0
        self.space.add(seg)
        logger.debug("Added closed obstacle with %d vertices.", len(verts))

    def step(self, dt) :
        # Advance simulation by dt seconds.
        # On Pymunk error, log and raise SimulationStepError.
        
        try :
            self.space.step(dt)
        except Exception as e :
            logger.exception("Physics step failed.")
            raise SimulationStepError(f"Simulation step error: {e}") from e

    def _on_launch_simulation(self) :
        # open the simulation window (separate resizable window) and call the launch callback
        logger.info("Launch Simulation requested.")
        try :
            # create a new resizable top-level window with black background
            sim_win = ctk.CTkToplevel(self.root)
            sim_win.title("SilhoMotion Simulation")
            sim_win.configure(fg_color="black")
            sim_win.geometry("800x600")
            sim_win.minsize(400, 300)

            # black canvas for future simulation rendering
            import tkinter as tk
            canvas = tk.Canvas(sim_win, bg="black", highlightthickness=0)
            canvas.pack(fill="both", expand=True)

            # keep references to prevent garbage collection and allow later drawing
            self._simulation_window = sim_win
            self._simulation_canvas = canvas

            # notify external callback (e.g., start camera/projector)
            self.on_launch_simulation()
        except Exception as e :
            logger.exception("Failed to launch simulation.")
            import tkinter.messagebox as msg
            msg.showerror("Launch Error", str(e))