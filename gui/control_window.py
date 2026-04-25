# gui/control_window.py

# Creates a separate control panel (Tkinter) with toggles, sliders,
#    and buttons to adjust simulation parameters, start/stop calibration,
#    and manage fullscreen projection

# ----- Imports -----
import tkinter as tk
import logging
from gui.styles import BG_COLOUR, FONT, BUTTON_COLOUR

# ----- Logger -----
logger = logging.getLogger(__name__)

class ControlWindow :
    # Tkinter control panel for simulation toggles, sliders, and actions

    def __init__(self, on_pause_toggle=None, on_silhouette_toggle=None,
                 on_gravity_change=None, on_calibrate=None, on_quit=None) :
        self.root = tk.Tk()
        self.root.title("SilhoMotion Control")
        self.root.configure(bg=BG_COLOUR)

        # Callbacks – default no‑op if not supplied
        self.on_pause_toggle = on_pause_toggle or (lambda v: None)
        self.on_silhouette_toggle = on_silhouette_toggle or (lambda v: None)
        self.on_gravity_change = on_gravity_change or (lambda v: None)
        self.on_calibrate = on_calibrate or (lambda: None)
        self.on_quit = on_quit or (lambda: self.root.quit())

        # ----- Control variables -----
        self.pause_var = tk.BooleanVar(value=False)
        self.show_silhouette_var = tk.BooleanVar(value=True)
        self.gravity_scale = tk.DoubleVar(value=1.0)

        # ----- Build UI -----
        self._build_widgets()

    def _build_widgets(self) :
        # Pause toggle
        pause_btn = tk.Checkbutton(
            self.root, text="Pause Physics", variable=self.pause_var,
            bg=BG_COLOUR, fg="white", font=FONT, selectcolor=BUTTON_COLOUR,
            command=self._on_pause_toggle
        )
        pause_btn.pack(pady=5, anchor="w")

        # Show silhouette toggle
        sil_btn = tk.Checkbutton(
            self.root, text="Show Silhouette", variable=self.show_silhouette_var,
            bg=BG_COLOUR, fg="white", font=FONT, selectcolor=BUTTON_COLOUR,
            command=self._on_silhouette_toggle
        )
        sil_btn.pack(pady=5, anchor="w")

        # Gravity scale slider
        scale_frame = tk.Frame(self.root, bg=BG_COLOUR)
        scale_frame.pack(pady=5, fill="x")
        tk.Label(
            scale_frame, text="Gravity Scale", bg=BG_COLOUR, fg="white", font=FONT
        ).pack(side="left")
        tk.Scale(
            scale_frame, from_=0.1, to=2.0, resolution=0.1, orient=tk.HORIZONTAL,
            variable=self.gravity_scale, bg=BUTTON_COLOUR, fg="white",
            font=FONT, command=self._on_gravity_change
        ).pack(side="right", fill="x", expand=True)

        # Buttons frame
        btn_frame = tk.Frame(self.root, bg=BG_COLOUR)
        btn_frame.pack(pady=10)
        tk.Button(
            btn_frame, text="Start Calibration", bg=BUTTON_COLOUR, fg="white",
            font=FONT, command=self._on_calibrate
        ).pack(side="left", padx=5)
        tk.Button(
            btn_frame, text="Quit", bg=BUTTON_COLOUR, fg="white",
            font=FONT, command=self._on_quit
        ).pack(side="left", padx=5)

    # ----- Callbacks with logging -----
    def _on_pause_toggle(self) :
        logger.info("Pause physics toggled: %s", self.pause_var.get())
        self.on_pause_toggle(self.pause_var.get())

    def _on_silhouette_toggle(self) :
        logger.info("Show silhouette toggled: %s", self.show_silhouette_var.get())
        self.on_silhouette_toggle(self.show_silhouette_var.get())

    def _on_gravity_change(self, value) :
        logger.info("Gravity scale changed to: %s", value)
        self.on_gravity_change(float(value))

    def _on_calibrate(self) :
        try :
            logger.info("Calibration started from GUI.")
            self.on_calibrate()
        except Exception as e :
            logger.exception("Calibration error.")

    def _on_quit(self) :
        logger.info("Quit requested from GUI.")
        self.on_quit()
        self.root.quit()
        self.root.destroy()

    def update(self) :
        # Process pending GUI events
        self.root.update_idletasks()
        self.root.update()