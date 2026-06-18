# gui/main_menu.py

# Modern main menu built with CustomTkinter.
# Two pages:
#   1) Home – Precheck Scan, Connect Camera, Launch/Stop Simulation, status indicators
#   2) Advanced – Simulation controls (pause, live camera, skeleton, gravity, bounce)

# ----- Imports -----
import customtkinter as ctk
import logging
import tkinter as tk
from gui.styles import FONT_HEADING, FONT_BUTTON, FONT_BODY, DANGER_COLOUR
from camera.capture import SilhouetteCapture, CameraNotFoundError
import cv2

# Suppress OpenCV verbose logging (if available)
if hasattr(cv2, 'setLogLevel'):
    cv2.setLogLevel(cv2.LOG_LEVEL_ERROR)

# ----- Logger -----
logger = logging.getLogger(__name__)

# ----- Main Menu -----
class MainMenu :
    """Tkinter main menu with Home and Advanced pages, powered by CustomTkinter."""

    def __init__(self,
                 on_precheck=None,               # called with camera_index
                 on_launch_simulation=None,      # called when "Launch" clicked
                 on_simulation_start=None,       # called with canvas, window, camera_obj
                 on_quit=None) :
        # Configure the root window
        self.root = ctk.CTk()
        self.root.title("SilhoMotion")
        self.root.geometry("500x800")              # increased height for more controls
        self.root.minsize(420, 600)

        # ----- Callbacks -----
        self.on_precheck           = on_precheck           or (lambda idx: None)
        self.on_launch_simulation  = on_launch_simulation  or (lambda: None)
        self.on_simulation_start   = on_simulation_start   or (lambda canvas, window, cam: None)
        self.on_quit               = on_quit               or (lambda: self.root.quit())

        # ----- Simulation state -----
        self.simulation_controller = None
        self.simulation_running = False

        # ----- Camera state -----
        self.camera_connected = False
        self.camera_obj = None
        self.selected_camera_index = 0
        self.available_cameras = []

        # ----- Control variables (simulation) -----
        self.pause_var = tk.BooleanVar(value=False)
        self.live_camera_var = tk.BooleanVar(value=False)
        self.skeleton_var = tk.BooleanVar(value=False)
        self.skeleton_color_var = tk.StringVar(value="Cyan")
        self.gravity_scale_var = tk.DoubleVar(value=1.0)
        self.elasticity_var = tk.DoubleVar(value=0.8)

        # ----- Advanced settings (simulation) -----
        self.max_entities_var    = tk.IntVar(value=10)
        self.despawn_time_var    = tk.DoubleVar(value=5.0)

        # ----- Build pages -----
        self._build_home_page()
        self._build_advanced_page()

        # Scan cameras and populate dropdown
        self._scan_cameras()
        self._populate_camera_dropdown()

        self._show_home()

    # ----- Home page -----
    def _build_home_page(self) :
        self.home_frame = ctk.CTkFrame(self.root, fg_color="transparent")

        ctk.CTkLabel(self.home_frame, text="SilhoMotion",
                     font=FONT_HEADING).pack(pady=(30, 5))
        ctk.CTkLabel(self.home_frame, text="Interactive Silhouette Physics",
                     font=FONT_BODY, text_color="grey").pack(pady=(0, 30))

        self.precheck_btn = ctk.CTkButton(
            self.home_frame, text="Precheck Scan",
            font=FONT_BUTTON, height=40, width=200,
            command=self._on_precheck
        )
        self.precheck_btn.pack(pady=10)

        # Camera controls (dropdown + connect)
        camera_frame = ctk.CTkFrame(self.home_frame, fg_color="transparent")
        camera_frame.pack(pady=10, fill="x", padx=30)

        self.camera_dropdown_var = tk.StringVar(value="No camera")
        self.camera_dropdown = ctk.CTkOptionMenu(
            camera_frame,
            variable=self.camera_dropdown_var,
            values=["No camera"],
            font=FONT_BODY,
            width=120,
            command=self._on_camera_selected
        )
        self.camera_dropdown.pack(side="left", padx=(0, 10))

        connect_frame = ctk.CTkFrame(camera_frame, fg_color="transparent")
        connect_frame.pack(side="left", fill="x", expand=True)

        self.camera_status_label = ctk.CTkLabel(
            connect_frame, text="●", font=("Segoe UI", 20), text_color="gray"
        )
        self.camera_status_label.pack(side="left", padx=(0, 10))

        self.connect_btn = ctk.CTkButton(
            connect_frame, text="Connect Camera",
            font=FONT_BUTTON, height=40, width=160,
            command=self._toggle_camera_connection
        )
        self.connect_btn.pack(side="left")

        # Launch simulation controls
        sim_frame = ctk.CTkFrame(self.home_frame, fg_color="transparent")
        sim_frame.pack(pady=10)

        self.status_label = ctk.CTkLabel(
            sim_frame, text="●", font=("Segoe UI", 20), text_color="gray"
        )
        self.status_label.pack(side="left", padx=(0, 10))

        self.launch_btn = ctk.CTkButton(
            sim_frame, text="Launch Simulation",
            font=FONT_BUTTON, height=40, width=180,
            command=self._toggle_simulation
        )
        self.launch_btn.pack(side="left")

        ctk.CTkLabel(self.home_frame, text="").pack(pady=15)

        bottom_frame = ctk.CTkFrame(self.home_frame, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", padx=30, pady=20)

        ctk.CTkButton(bottom_frame, text="Advanced", width=90,
                      font=FONT_BODY, command=self._show_advanced
                      ).pack(side="left", padx=5)

        ctk.CTkButton(bottom_frame, text="Quit", width=90,
                      font=FONT_BODY, fg_color=DANGER_COLOUR,
                      hover_color="#A93226", command=self._on_quit
                      ).pack(side="right", padx=5)

    # ----- Advanced page (scrollable) -----
    def _build_advanced_page(self) :
        # Use a scrollable frame as the main container
        self.advanced_frame = ctk.CTkScrollableFrame(self.root, fg_color="transparent")
        # We'll pack later when showing.

        # Title (inside scrollable frame)
        ctk.CTkLabel(self.advanced_frame, text="Advanced Controls",
                     font=FONT_HEADING).pack(pady=(20, 5))
        ctk.CTkLabel(self.advanced_frame, text="Control the running simulation",
                     font=FONT_BODY, text_color="grey").pack(pady=(0, 15))

        # ---- Simulation Controls card ----
        controls_card = ctk.CTkFrame(self.advanced_frame, corner_radius=10)
        controls_card.pack(padx=30, pady=5, fill="x")

        self.pause_switch = ctk.CTkSwitch(
            controls_card, text="Pause Physics",
            variable=self.pause_var,
            command=self._on_pause_toggle,
            font=FONT_BODY,
            state="disabled"
        )
        self.pause_switch.pack(padx=20, pady=(10, 5), anchor="w")

        self.live_camera_switch = ctk.CTkSwitch(
            controls_card, text="Set Live Camera",
            variable=self.live_camera_var,
            command=self._on_live_camera_toggle,
            font=FONT_BODY,
            state="disabled"
        )
        self.live_camera_switch.pack(padx=20, pady=5, anchor="w")

        self.skeleton_switch = ctk.CTkSwitch(
            controls_card, text="Draw Skeleton",
            variable=self.skeleton_var,
            command=self._on_skeleton_toggle,
            font=FONT_BODY,
            state="disabled"
        )
        self.skeleton_switch.pack(padx=20, pady=5, anchor="w")

        # Skeleton color dropdown (placed below skeleton switch)
        color_frame = ctk.CTkFrame(controls_card, fg_color="transparent")
        color_frame.pack(padx=20, pady=(0, 10), fill="x")
        ctk.CTkLabel(color_frame, text="Skeleton Color", font=FONT_BODY, width=120).pack(side="left")
        self.skeleton_color_menu = ctk.CTkOptionMenu(
            color_frame,
            values=["Cyan", "White", "Red", "Green", "Blue", "Yellow", "Magenta"],
            variable=self.skeleton_color_var,
            font=FONT_BODY,
            width=100,
            state="disabled",
            command=self._on_skeleton_color_change
        )
        self.skeleton_color_menu.pack(side="left", padx=(10, 0))

        # Gravity
        grav_frame = ctk.CTkFrame(controls_card, fg_color="transparent")
        grav_frame.pack(padx=20, pady=5, fill="x")
        ctk.CTkLabel(grav_frame, text="Gravity Scale", font=FONT_BODY).pack(side="left")
        self.gravity_slider = ctk.CTkSlider(
            grav_frame, from_=0.1, to=2.0, number_of_steps=19,
            variable=self.gravity_scale_var,
            command=self._on_gravity_change,
            state="disabled"
        )
        self.gravity_slider.pack(side="left", padx=(10, 5), fill="x", expand=True)
        self.gravity_value_label = ctk.CTkLabel(grav_frame, text="1.0", font=FONT_BODY, width=40)
        self.gravity_value_label.pack(side="left")

        # Bounce
        bounce_frame = ctk.CTkFrame(controls_card, fg_color="transparent")
        bounce_frame.pack(padx=20, pady=5, fill="x")
        ctk.CTkLabel(bounce_frame, text="Bounce", font=FONT_BODY).pack(side="left")
        self.elasticity_slider = ctk.CTkSlider(
            bounce_frame, from_=0.0, to=1.0, number_of_steps=20,
            variable=self.elasticity_var,
            command=self._on_elasticity_change,
            state="disabled"
        )
        self.elasticity_slider.pack(side="left", padx=(10, 5), fill="x", expand=True)
        self.elasticity_value_label = ctk.CTkLabel(bounce_frame, text="0.8", font=FONT_BODY, width=40)
        self.elasticity_value_label.pack(side="left")

        # Calibration placeholder
        self.calibrate_btn = ctk.CTkButton(
            controls_card, text="Start Calibration",
            font=FONT_BODY, height=30, width=140,
            command=self._on_calibrate,
            state="disabled"
        )
        self.calibrate_btn.pack(padx=20, pady=(5, 5), anchor="w")

        self.stop_btn = ctk.CTkButton(
            controls_card, text="Stop Simulation",
            font=FONT_BODY, height=30, width=140,
            fg_color=DANGER_COLOUR,
            hover_color="#A93226",
            command=self._stop_simulation,
            state="disabled"
        )
        self.stop_btn.pack(padx=20, pady=(5, 10), anchor="w")

        # ---- Simulation Settings card ----
        settings_card = ctk.CTkFrame(self.advanced_frame, corner_radius=10)
        settings_card.pack(padx=30, pady=15, fill="x")

        ctk.CTkLabel(settings_card, text="Simulation Settings",
                     font=FONT_BODY, anchor="w").pack(padx=20, pady=(10, 5), anchor="w")

        ctk.CTkLabel(settings_card, text="Max Entity Count",
                     font=FONT_BODY, anchor="w").pack(padx=20, pady=(5, 2), anchor="w")
        self.max_entities_entry = ctk.CTkEntry(
            settings_card, width=120, font=FONT_BODY,
            textvariable=self.max_entities_var,
            placeholder_text="10",
            validate="key",
            validatecommand=(self.root.register(self._validate_int), '%P')
        )
        self.max_entities_entry.pack(padx=20, pady=(0, 10), anchor="w")

        ctk.CTkLabel(settings_card, text="Entity Despawn Rate (seconds)",
                     font=FONT_BODY, anchor="w").pack(padx=20, pady=(0, 2), anchor="w")
        self.despawn_entry = ctk.CTkEntry(
            settings_card, width=120, font=FONT_BODY,
            textvariable=self.despawn_time_var,
            placeholder_text="5.0",
            validate="key",
            validatecommand=(self.root.register(self._validate_float), '%P')
        )
        self.despawn_entry.pack(padx=20, pady=(0, 10), anchor="w")

        ctk.CTkButton(settings_card, text="Apply Settings", font=FONT_BUTTON,
                      height=36, width=160,
                      command=self._on_save_settings
                      ).pack(pady=(5, 15))

        # Bottom bar (Main Menu & Quit) - placed inside scrollable frame
        back_frame = ctk.CTkFrame(self.advanced_frame, fg_color="transparent")
        back_frame.pack(side="bottom", fill="x", padx=30, pady=20)
        ctk.CTkButton(back_frame, text="Main Menu", width=90,
                      font=FONT_BODY, command=self._show_home
                      ).pack(side="left")
        ctk.CTkButton(back_frame, text="Quit", width=90,
                      font=FONT_BODY, fg_color=DANGER_COLOUR,
                      hover_color="#A93226", command=self._on_quit
                      ).pack(side="right")

    # ----- Page switching -----
    def _show_home(self) :
        self.advanced_frame.pack_forget()
        self.home_frame.pack(fill="both", expand=True)

    def _show_advanced(self) :
        self.home_frame.pack_forget()
        self.advanced_frame.pack(fill="both", expand=True)

    # ----- Camera management (scanning with suppressed errors) -----
    def _scan_cameras(self, max_index=10) :
        available = []
        for idx in range(max_index) :
            try :
                cap = cv2.VideoCapture(idx)
                if cap.isOpened() :
                    available.append(idx)
                    cap.release()
                else :
                    cap.release()
            except Exception :
                # Some backends may raise exceptions; ignore and continue
                pass
        self.available_cameras = available
        logger.debug("Scanned cameras: found %d", len(available))
        if not available :
            logger.warning("No cameras found.")
        if self.available_cameras :
            from common import config
            if config.CAMERA_INDEX in self.available_cameras :
                self.selected_camera_index = config.CAMERA_INDEX
            else :
                self.selected_camera_index = self.available_cameras[0]
        else :
            self.selected_camera_index = 0

    def _populate_camera_dropdown(self) :
        if not self.available_cameras :
            values = ["No camera"]
            default = "No camera"
        else :
            values = [f"Camera {idx}" for idx in self.available_cameras]
            default_str = f"Camera {self.selected_camera_index}"
            if default_str not in values :
                default_str = values[0]
                self.selected_camera_index = self.available_cameras[0]
        self.camera_dropdown.configure(values=values)
        self.camera_dropdown_var.set(default_str)

    def _on_camera_selected(self, choice) :
        if choice == "No camera" :
            return
        try :
            idx = int(choice.split()[1])
        except (IndexError, ValueError) :
            return
        self.selected_camera_index = idx
        logger.info("Camera selection changed to index %d", idx)

    def _connect_camera(self) :
        if self.camera_connected :
            return
        try :
            cam = SilhouetteCapture(self.selected_camera_index)
            self.camera_obj = cam
            self.camera_connected = True
            self.camera_status_label.configure(text_color="green")
            self.connect_btn.configure(text="Disconnect Camera")
            logger.info("Camera %d connected successfully.", self.selected_camera_index)
        except CameraNotFoundError as e :
            logger.error("Failed to connect camera %d: %s", self.selected_camera_index, e)
            import tkinter.messagebox as msg
            msg.showerror("Camera Error", f"Could not connect to camera {self.selected_camera_index}:\n{e}")
            self.camera_connected = False
            self.camera_status_label.configure(text_color="red")
            self.connect_btn.configure(text="Connect Camera")
        except Exception as e :
            logger.exception("Unexpected error during camera connection.")
            import tkinter.messagebox as msg
            msg.showerror("Camera Error", f"Unexpected error:\n{e}")
            self.camera_connected = False
            self.camera_status_label.configure(text_color="red")
            self.connect_btn.configure(text="Connect Camera")

    def _disconnect_camera(self) :
        if self.camera_obj :
            try :
                self.camera_obj.release()
            except Exception as e :
                logger.warning("Error releasing camera: %s", e)
            self.camera_obj = None
        self.camera_connected = False
        self.camera_status_label.configure(text_color="gray")
        self.connect_btn.configure(text="Connect Camera")
        logger.info("Camera disconnected.")

    def _toggle_camera_connection(self) :
        if self.simulation_running :
            import tkinter.messagebox as msg
            msg.showinfo("Simulation Running", "Cannot change camera while simulation is running.")
            return
        if self.camera_connected :
            self._disconnect_camera()
        else :
            self._connect_camera()

    # ----- Simulation control methods -----
    def set_simulation_controller(self, controller) :
        self.simulation_controller = controller
        self.pause_switch.configure(state="normal")
        self.live_camera_switch.configure(state="normal")
        self.skeleton_switch.configure(state="normal")
        self.skeleton_color_menu.configure(state="normal")
        self.gravity_slider.configure(state="normal")
        self.elasticity_slider.configure(state="normal")
        self.calibrate_btn.configure(state="normal")
        self.stop_btn.configure(state="normal")
        self.camera_dropdown.configure(state="disabled")
        self.connect_btn.configure(state="disabled")
        logger.info("Simulation controller attached to main menu.")

    def set_simulation_status(self, online: bool) :
        self.simulation_running = online
        if online :
            self.status_label.configure(text_color="green")
            self.launch_btn.configure(text="Stop Simulation")
            self.camera_dropdown.configure(state="disabled")
            self.connect_btn.configure(state="disabled")
        else :
            self.status_label.configure(text_color="red")
            self.launch_btn.configure(text="Launch Simulation")
            self.pause_switch.configure(state="disabled")
            self.live_camera_switch.configure(state="disabled")
            self.skeleton_switch.configure(state="disabled")
            self.skeleton_color_menu.configure(state="disabled")
            self.gravity_slider.configure(state="disabled")
            self.elasticity_slider.configure(state="disabled")
            self.calibrate_btn.configure(state="disabled")
            self.stop_btn.configure(state="disabled")
            self.camera_dropdown.configure(state="normal")
            self.connect_btn.configure(state="normal")

    def _toggle_simulation(self) :
        if self.simulation_running :
            self._stop_simulation()
        else :
            self._start_simulation()

    def _start_simulation(self) :
        logger.info("Launch Simulation requested.")
        # Ensure camera is connected
        if not self.camera_connected or self.camera_obj is None:
            import tkinter.messagebox as msg
            msg.showerror("Camera Required", "Please connect a camera before launching the simulation.")
            return

        try :
            sim_win = ctk.CTkToplevel(self.root)
            sim_win.title("SilhoMotion Simulation")
            sim_win.configure(fg_color="black")
            sim_win.geometry("800x600")
            sim_win.minsize(400, 300)

            canvas = tk.Canvas(sim_win, bg="black", highlightthickness=0)
            canvas.pack(fill="both", expand=True)

            self._simulation_window = sim_win

            # Pass the existing camera object to the simulation
            self.on_simulation_start(canvas, sim_win, self.camera_obj)
            self.on_launch_simulation()

            # Set live camera toggle to ON by default (reflect in GUI)
            self.live_camera_var.set(True)
            # Optionally set skeleton toggle to OFF (default)
            # self.skeleton_var.set(False)

        except Exception as e :
            logger.exception("Failed to launch simulation.")
            import tkinter.messagebox as msg
            msg.showerror("Launch Error", str(e))

    def _stop_simulation(self) :
        if self.simulation_controller :
            self.simulation_controller.stop()
        else :
            self.set_simulation_status(False)

    # ----- Control widget callbacks -----
    def _on_pause_toggle(self) :
        if self.simulation_controller :
            self.simulation_controller.set_paused(self.pause_var.get())

    def _on_live_camera_toggle(self) :
        if self.simulation_controller :
            self.simulation_controller.set_live_camera(self.live_camera_var.get())

    def _on_skeleton_toggle(self) :
        if self.simulation_controller :
            self.simulation_controller.set_skeleton(self.skeleton_var.get())

    def _on_skeleton_color_change(self, color) :
        if self.simulation_controller :
            self.simulation_controller.set_skeleton_color(color)

    def _on_gravity_change(self, value) :
        self.gravity_value_label.configure(text=f"{float(value):.1f}")
        if self.simulation_controller :
            self.simulation_controller.set_gravity_scale(float(value))

    def _on_elasticity_change(self, value) :
        self.elasticity_value_label.configure(text=f"{float(value):.2f}")
        if self.simulation_controller :
            self.simulation_controller.set_elasticity(float(value))

    # ----- Other callbacks -----
    def _on_precheck(self) :
        logger.info("Precheck with camera index %d.", self.selected_camera_index)
        try :
            self.on_precheck(self.selected_camera_index)
        except Exception as e :
            logger.exception("Precheck failed.")
            import tkinter.messagebox as msg
            msg.showerror("Precheck Error", str(e))

    def _on_save_settings(self) :
        logger.info("Advanced settings saved: max_entities=%d, despawn_time=%.1f",
                    self.max_entities_var.get(), self.despawn_time_var.get())
        import tkinter.messagebox as msg
        msg.showinfo("Settings", "Settings applied (simulation restart may be required).")

    def _on_calibrate(self) :
        logger.info("Calibration requested.")
        import tkinter.messagebox as msg
        msg.showinfo("Calibration", "Calibration not yet implemented.")

    def _on_quit(self) :
        logger.info("Quit requested.")
        if self.simulation_controller :
            self.simulation_controller.stop()
        if hasattr(self, '_simulation_window') and self._simulation_window.winfo_exists():
            self._simulation_window.destroy()
        if self.camera_connected :
            self._disconnect_camera()
        self.on_quit()
        self.root.quit()
        self.root.destroy()

    def run(self) :
        self.root.mainloop()

    # ----- Validation helpers -----
    @staticmethod
    def _validate_int(new_value: str) -> bool :
        if new_value == "" :
            return True
        return new_value.isdigit()

    @staticmethod
    def _validate_float(new_value: str) -> bool :
        if new_value == "" :
            return True
        if new_value.count('.') > 1 :
            return False
        return all(c.isdigit() or c == '.' for c in new_value)