# main.py

# Entry point that initializes the camera, physics engine, GUI controls 
#    and projector output; runs the main loop that feeds camera data 
#    into the simulation and renders to the projector

# ----- Imports -----
import utils.logger as logsetup
from config import config
import logging
import time
import traceback
import sys

# ----- Logger -----
logger = logsetup.setup_logger("SilhoMotion")

# ----- Main -----
if __name__ == "__main__" :
    logger.info("Starting SilhoMotion...")
    try :
        from camera.capture import SilhouetteCapture, CameraNotFoundError
        from physics.simulation import PhysicsWorld
        from gui.control_window import ControlWindow
        from projector.output import ProjectorWindow

        # Initialise components
        camera = SilhouetteCapture(config.CAMERA_INDEX)
        physics = PhysicsWorld(config.PHYSICS_GRAVITY)
        projector = ProjectorWindow(config.PROJECTOR_SCREEN)
        gui = ControlWindow()

        running = True

        def main_loop() :
            # Recurring update using tkinter's after() to keep GUI responsive
            nonlocal running
            if not running :
                gui.root.destroy()
                return

            # 1. Grab silhouette
            mask = camera.read_frame()
            # (silhouette processing can be added here)

            # 2. Update physics (if not paused)
            if not gui.pause_var.get():
                physics.step(1/30.0)

            # 3. Render to projector
            projector.draw_frame({})

            # 4. Schedule next iteration
            gui.root.after(33, main_loop) # ~30 FPS

        # Run main loop via Tkinter's event loop
        gui.root.after(0, main_loop)
        gui.root.mainloop()

    except CameraNotFoundError as e :
        logger.critical("Camera error: %s", e)
        sys.exit(1)
    except Exception as e :
        logger.critical("Fatal error: %s\n%s", e, traceback.format_exc())
        sys.exit(1)
    finally :
        try :
            camera.release()
        except NameError :
            pass
        try :
            projector.close()
        except NameError :
            pass
        logger.info("SilhoMotion shut down safely.")