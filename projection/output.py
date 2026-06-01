# projection/output.py

# Manages a fullscreen window on the projector (second display)
#    using Pyglet; draws the simulation visuals and any
#    calibration overlays

# ----- Imports -----
import pyglet
import logging
from projection.exceptions import ProjectorInitError

# ----- Logger -----
logger = logging.getLogger(__name__)

class ProjectorWindow :
    # Manages a fullscreen Pyglet window on the selected projector screen

    def __init__(self, screen_index=1, resolution=(1920, 1080)) :
        # Locate the target display (0‑based)
        displays = pyglet.canvas.get_display().get_screens()
        if screen_index >= len(displays) :
            raise ProjectorInitError(
                f"Requested display {screen_index} but only {len(displays)} display(s) found."
            )
        self._target_screen = displays[screen_index]

        # Create a fullscreen window on the chosen screen
        try :
            self.window = pyglet.window.Window(
                fullscreen=True,
                screen=self._target_screen,
                caption="SilhoMotion Projector"
            )
        except Exception as e :
            raise ProjectorInitError(f"Cannot open fullscreen window: {e}")

        # Internal clock to control frame rate
        self.clock = pyglet.clock.Clock()
        self.fps_limit = 30   # target FPS

        # Setup basic window events
        @self.window.event
        def on_draw() :
            # This will be overridden externally if needed
            self.window.clear()

        logger.info("Projector window initialised on display %d, resolution %s.",
                    screen_index, self.window.get_size())

    def draw_frame(self, simulation_state: dict) :
        # Render one frame. 'simulation_state' is a dict placeholder
        # that will contain object positions, colours, etc.
        # Pyglet uses on_draw for rendering; we can push manual drawing here.
        self.window.clear()
        # Draw a simple test circle – replace with real rendering later
        batch = pyglet.graphics.Batch()
        circle = pyglet.shapes.Circle(
            400, 300, 50,
            color=(200, 200, 200),
            batch=batch
        )
        batch.draw()
        self.window.flip()

        # Enforce frame rate cap
        self.clock.tick()

    def close(self) :
        # Close the window and clean up
        if self.window :
            self.window.close()
        logger.info("Projector window closed.")