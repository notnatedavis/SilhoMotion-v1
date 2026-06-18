# main.py

# Entry point that creates the SilhoMotion main menu.
# From the menu the user can run a precheck (camera + calibration),
# launch the simulation (physics + rendering in a new window),
# and control it via the Advanced tab of the main menu.

# ----- Imports -----
import utils.logger as logsetup
from common import config
import logging
import sys
import tkinter.messagebox as msg

# apply the global CustomTkinter appearance before any widget is created
from gui.styles import apply_global_style
apply_global_style()

logger = logsetup.setup_logger("SilhoMotion")

# Global reference to the simulation controller (for cleanup)
_simulation_controller = None

# ----- Simulation startup -----
def start_simulation(canvas, window, main_menu, camera_obj) :
    """Called when the simulation window is created.
       Sets up camera, physics, and GUI, and attaches controls to main_menu.
    """
    global _simulation_controller

    from simulation.controller import SimulationController

    logger.info("Starting simulation controller with provided camera object...")

    # Callback for when the controller stops (so we can update the UI)
    def on_controller_stop() :
        logger.info("Controller stopped; updating main menu status.")
        main_menu.set_simulation_status(False)
        global _simulation_controller
        _simulation_controller = None

    # Create controller with the camera object and stop callback
    try :
        controller = SimulationController(
            canvas, window, config,
            camera_obj=camera_obj,
            on_stop_callback=on_controller_stop
        )
    except Exception as e :
        logger.critical("Failed to initialise simulation: %s", e, exc_info=True)
        msg.showerror("Simulation Error", f"Could not start simulation:\n{e}")
        return

    _simulation_controller = controller
    main_menu.set_simulation_controller(controller)
    controller.start()
    main_menu.set_simulation_status(True)
    window.after(500, controller.add_test_ball)

    logger.info("Simulation and control are running.")

# ----- Precheck (camera only) -----
def precheck(camera_index) :
    """Connect to camera and verify it works."""
    from camera.capture import SilhouetteCapture, CameraNotFoundError

    try :
        cam = SilhouetteCapture(camera_index)
        logger.info("Camera connected successfully (index %d).", camera_index)
        cam.release()
        msg.showinfo("Precheck", f"Camera {camera_index} is working.")
    except CameraNotFoundError as e :
        logger.error("Precheck failed: %s", e)
        msg.showerror("Precheck Error", f"Camera not found:\n{e}")
    except Exception as e :
        logger.exception("Precheck unexpected error.")
        msg.showerror("Precheck Error", f"Unexpected error:\n{e}")

# ----- Quit -----
def quit_app() :
    # clean up resources and exit
    global _simulation_controller
    logger.info("Quitting application...")
    if _simulation_controller :
        _simulation_controller.stop()
        _simulation_controller = None
    logger.info("Application exited.")

# ----- Main -----
if __name__ == "__main__" :
    logger.info("Starting SilhoMotion Main Menu...")
    try :
        from gui.main_menu import MainMenu

        menu = MainMenu(
            on_precheck=precheck,
            on_launch_simulation=lambda: logger.info("Simulation window opened."),
            on_simulation_start=lambda canvas, win, cam: start_simulation(canvas, win, menu, cam),
            on_quit=quit_app
        )
        menu.run()

    except Exception as e :
        logger.critical("Fatal error during startup: %s", e, exc_info=True)
        sys.exit(1)