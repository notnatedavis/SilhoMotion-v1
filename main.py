# main.py

# Entry point that creates the SilhoMotion main menu.
# From the menu the user can run a precheck (camera + calibration),
# launch the simulation (projector + physics), or adjust advanced
# settings.

# ----- Imports -----
import utils.logger as logsetup
from common import config
import logging
import sys
import threading

# apply the global CustomTkinter appearance before any widget is created
from gui.styles import apply_global_style
apply_global_style()

logger = logsetup.setup_logger("SilhoMotion")

# ----- Main -----
if __name__ == "__main__" :
    logger.info("Starting SilhoMotion Main Menu...")
    try :
        # CustomTkinter availability check
        try :
            from gui.main_menu import MainMenu
        except ImportError as e :
            logger.critical("Tkinter is not available: %s", e)
            sys.exit(
                "Error: Tkinter is not installed.\n"
                "On macOS with Homebrew Python, run:\n"
                "  brew install python-tk@3.14\n"
                "Then re-run the application."
            )

        # ----- Camera and projector globals -----
        camera = None
        projector = None

        # ----- Precheck: connect camera and perform calibration -----
        def precheck() :
            global camera
            from camera.capture import SilhouetteCapture, CameraNotFoundError
            if camera is not None :
                logger.info("Camera already connected.")
                return
            logger.info("Initializing camera for precheck...")
            camera = SilhouetteCapture(config.CAMERA_INDEX)
            logger.info("Camera connected. (Calibration will be added later.)")

        # ----- Launch simulation: open projector window + (future) physics -----
        def launch_simulation() :
            global projector
            from projection.output import ProjectorWindow, ProjectorInitError
            if projector is not None :
                logger.warning("Projector already opened.")
                return
            logger.info("Opening projector window on display %d...",
                        config.PROJECTOR_SCREEN)
            # Pyglet can run in a separate thread – its event loop is not mandatory
            # if we manually call window.dispatch_events() and flip().
            def projector_loop(stop_flag: threading.Event) :
                import pyglet
                proj = ProjectorWindow(config.PROJECTOR_SCREEN,
                                       (config.PROJECTOR_WIDTH, config.PROJECTOR_HEIGHT))
                try :
                    while not stop_flag.is_set() :
                        # Process pending OS events (so the window doesn't freeze)
                        proj.window.dispatch_events()
                        # Render a frame (placeholder for now)
                        proj.draw_frame({})
                        # Throttle – pyglet's clock handles this
                    proj.close()
                except Exception as e :
                    logger.exception("Projector loop error: %s", e)
                finally :
                    proj.close()
                    logger.info("Projection window closed.")
                    global projector
                    projector = None

            stop_flag = threading.Event()
            thread = threading.Thread(target=projector_loop, args=(stop_flag,), daemon=True)
            thread.start()
            global _projector_stop_flag, _projector_thread
            _projector_stop_flag = stop_flag
            _projector_thread = thread
            logger.info("Projector thread started.")

        # ----- Quit: release resources -----
        def quit_app() :
            global camera
            if '_projector_stop_flag' in globals() :
                _projector_stop_flag.set()
                _projector_thread.join(timeout=3)
            if camera :
                camera.release()
                logger.info("Camera released.")
            logger.info("Application exiting.")

        # ----- Build and run the main menu -----
        menu = MainMenu(
            on_precheck=precheck,
            on_launch_simulation=launch_simulation,
            on_quit=quit_app
        )
        menu.run()

    except Exception as e :
        logger.critical("Fatal error during startup: %s", e, exc_info=True)
        sys.exit(1)