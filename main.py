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
        from camera.calibrator import Calibrator
        from camera.mapper import Mapper
        from physics.simulation import PhysicsWorld
        from gui.control_window import ControlWindow
        from projector.output import ProjectorWindow

        # Initialise components
        camera = SilhouetteCapture(config.CAMERA_INDEX)
        physics = PhysicsWorld(config.PHYSICS_GRAVITY)
        projector = ProjectorWindow(
            config.PROJECTOR_SCREEN,
            (config.PROJECTOR_WIDTH, config.PROJECTOR_HEIGHT)
        )

        # Central state
        mapper = None
        calibrating = False
        calibration_start = 0
        calibrator = Calibrator()

        # ----- GUI callbacks -----
        def on_pause_toggle(paused) :
            logger.debug("Pause set to %s", paused)

        def on_silhouette_toggle(show) :
            logger.debug("Show silhouette set to %s", show)

        def on_gravity_change(scale) :
            base = config.PHYSICS_GRAVITY
            physics.space.gravity = (base[0], base[1] * scale)
            logger.debug("Gravity updated to %s", physics.space.gravity)

        def on_calibrate() :
            nonlocal calibrating, calibration_start
            logger.info("Entering calibration mode.")
            calibrating = True
            calibration_start = time.time()

        def on_quit() :
            logger.info("Quit callback triggered.")

        gui = ControlWindow(
            on_pause_toggle=on_pause_toggle,
            on_silhouette_toggle=on_silhouette_toggle,
            on_gravity_change=on_gravity_change,
            on_calibrate=on_calibrate,
            on_quit=on_quit
        )

        running = True

        def main_loop() :
            nonlocal running, calibrating, mapper
            if not running :
                gui.root.destroy()
                return

            # 1. Grab frame and silhouette mask
            mask = camera.read_frame()
            if mask is None :
                gui.root.after(33, main_loop)
                return

            # 2. Calibration routine (if active)
            if calibrating :
                # Capture a frame from camera for QR detection
                ret, calib_frame = camera.cap.read()   # need the raw frame, not mask
                if ret :
                    corners = calibrator.detect_qr(calib_frame)
                    if corners is not None :
                        H = calibrator.compute_homography(
                            corners, (config.PROJECTOR_WIDTH, config.PROJECTOR_HEIGHT)
                        )
                        mapper = Mapper(H)
                        logger.info("Calibration succeeded. Homography stored.")
                        calibrating = False
                    elif time.time() - calibration_start > config.CALIBRATION_TIMEOUT :
                        logger.warning("Calibration timed out.")
                        calibrating = False
                # Continue regular loop (or we could pause physics) – we'll still update
                gui.root.after(33, main_loop)
                return

            # 3. Extract silhouette contour if mapper available
            contour = camera.extract_contour(mask)
            if contour and mapper :
                # Map to projector coordinates
                mapped_contour = mapper.map_points(contour)
                # Update physics obstacle
                physics.clear_obstacles()
                physics.add_obstacle(mapped_contour)

            # 4. Update physics (if not paused)
            if not gui.pause_var.get():
                physics.step(1/30.0)

            # 5. Render to projector (placeholder visualisation)
            projector.draw_frame({})

            # 6. Schedule next iteration
            gui.root.after(33, main_loop)   # ~30 FPS

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