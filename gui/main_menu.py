# gui/main_menu.py

# Modern main menu built with CustomTkinter.
# Two pages:
#   1) Home – Precheck Scan & Launch Simulation
#   2) Advanced – Physics simulation settings (inputs with placeholders)
#
# "Launch Simulation" opens a separate, resizable window with
# a black background that will host the simulation view.

# ----- Imports -----
import customtkinter as ctk
import logging
from gui.styles import FONT_HEADING, FONT_BUTTON, FONT_BODY, DANGER_COLOUR

# ----- Logger -----
logger = logging.getLogger(__name__)

# ----- Main Menu -----
class MainMenu :
    """Tkinter main menu with Home and Advanced pages, powered by CustomTkinter."""

    def __init__(self,
                 on_precheck=None,
                 on_launch_simulation=None,
                 on_quit=None) :
        # Configure the root window
        self.root = ctk.CTk()
        self.root.title("SilhoMotion")
        self.root.geometry("500x480")
        self.root.minsize(420, 400)

        # ----- Callbacks -----
        self.on_precheck           = on_precheck           or (lambda: None)
        self.on_launch_simulation  = on_launch_simulation  or (lambda: None)
        self.on_quit               = on_quit               or (lambda: self.root.quit())

        # ----- Store settings variables (advanced page) -----
        self.max_entities_var    = ctk.IntVar(value=10)
        self.despawn_time_var    = ctk.DoubleVar(value=5.0)
        self.gravity_scale_var   = ctk.DoubleVar(value=1.0)

        # ----- Build the two pages -----
        self._build_home_page()
        self._build_advanced_page()

        # Show home page by default
        self._show_home()

    # ----- Home page -----
    def _build_home_page(self) :
        # Construct the Home page frame
        self.home_frame = ctk.CTkFrame(self.root, fg_color="transparent")

        # Title
        ctk.CTkLabel(self.home_frame, text="SilhoMotion",
                     font=FONT_HEADING).pack(pady=(30, 5))
        ctk.CTkLabel(self.home_frame, text="Interactive Silhouette Physics",
                     font=FONT_BODY, text_color="grey").pack(pady=(0, 30))

        # Precheck Scan button
        self.precheck_btn = ctk.CTkButton(
            self.home_frame, text="Precheck Scan",
            font=FONT_BUTTON, height=40, width=200,
            command=self._on_precheck
        )
        self.precheck_btn.pack(pady=10)

        # 'Launch Simulation' button
        self.launch_btn = ctk.CTkButton(
            self.home_frame, text="Launch Simulation",
            font=FONT_BUTTON, height=40, width=200,
            command=self._on_launch_simulation
        )
        self.launch_btn.pack(pady=10)

        # Spacer
        ctk.CTkLabel(self.home_frame, text="").pack(pady=15)

        # Bottom row: Advanced & Quit
        bottom_frame = ctk.CTkFrame(self.home_frame, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", padx=30, pady=20)

        ctk.CTkButton(bottom_frame, text="Advanced", width=90,
                      font=FONT_BODY, command=self._show_advanced
                      ).pack(side="left", padx=5)

        ctk.CTkButton(bottom_frame, text="Quit", width=90,
                      font=FONT_BODY, fg_color=DANGER_COLOUR,
                      hover_color="#A93226", command=self._on_quit
                      ).pack(side="right", padx=5)

    # ----- Advanced page -----
    def _build_advanced_page(self) :
        # Construct the Advanced settings frame with input fields and placeholders
        self.advanced_frame = ctk.CTkFrame(self.root, fg_color="transparent")

        # Title
        ctk.CTkLabel(self.advanced_frame, text="Advanced Settings",
                     font=FONT_HEADING).pack(pady=(20, 10))

        # Subtitle
        ctk.CTkLabel(self.advanced_frame, text="Physics Simulation Settings",
                     font=FONT_BODY, text_color="grey").pack(pady=(0, 15))

        # Settings card (rounded frame)
        card = ctk.CTkFrame(self.advanced_frame, corner_radius=10)
        card.pack(padx=30, pady=10, fill="both", expand=True)

        # ---- Max Entities ----
        ctk.CTkLabel(card, text="Max Entity Count",
                     font=FONT_BODY, anchor="w").pack(padx=20, pady=(15, 2), anchor="w")
        self.max_entities_entry = ctk.CTkEntry(
            card, width=120, font=FONT_BODY,
            textvariable=self.max_entities_var,
            placeholder_text="10",
            validate="key",
            validatecommand=(self.root.register(self._validate_int), '%P')
        )
        self.max_entities_entry.pack(padx=20, pady=(0, 15), anchor="w")

        # ---- Despawn Rate ----
        ctk.CTkLabel(card, text="Entity Despawn Rate (seconds)",
                     font=FONT_BODY, anchor="w").pack(padx=20, pady=(0, 2), anchor="w")
        self.despawn_entry = ctk.CTkEntry(
            card, width=120, font=FONT_BODY,
            textvariable=self.despawn_time_var,
            placeholder_text="5.0",
            validate="key",
            validatecommand=(self.root.register(self._validate_float), '%P')
        )
        self.despawn_entry.pack(padx=20, pady=(0, 15), anchor="w")

        # ---- Gravity Scale ----
        ctk.CTkLabel(card, text="Gravity Scale",
                     font=FONT_BODY, anchor="w").pack(padx=20, pady=(0, 2), anchor="w")
        self.gravity_entry = ctk.CTkEntry(
            card, width=120, font=FONT_BODY,
            textvariable=self.gravity_scale_var,
            placeholder_text="1.0",
            validate="key",
            validatecommand=(self.root.register(self._validate_float), '%P')
        )
        self.gravity_entry.pack(padx=20, pady=(0, 15), anchor="w")

        # ---- Apply button ----
        ctk.CTkButton(card, text="Apply Settings", font=FONT_BUTTON,
                      height=36, width=160,
                      command=self._on_save_settings
                      ).pack(pady=(10, 20))

        # ---- Back button (returns to Home page) ----
        back_frame = ctk.CTkFrame(self.advanced_frame, fg_color="transparent")
        back_frame.pack(side="bottom", fill="x", padx=30, pady=20)
        ctk.CTkButton(back_frame, text="Back", width=90,
                      font=FONT_BODY, command=self._show_home
                      ).pack(side="left")
        ctk.CTkButton(back_frame, text="Quit", width=90,
                      font=FONT_BODY, fg_color=DANGER_COLOUR,
                      hover_color="#A93226", command=self._on_quit
                      ).pack(side="right")
        
    # ----- Page switching -----
    def _show_home(self) :
        # display the Home page
        self.advanced_frame.pack_forget()
        self.home_frame.pack(fill="both", expand=True)

    def _show_advanced(self) :
        # display the Advanced page
        self.home_frame.pack_forget()
        self.advanced_frame.pack(fill="both", expand=True)

    # ----- Validation helpers -----
    @staticmethod
    def _validate_int(new_value: str) -> bool :
        # allow only digits (int) in the max entities entry
        if new_value == "" :
            return True
        return new_value.isdigit()

    @staticmethod
    def _validate_float(new_value: str) -> bool :
        # allow digits and a single dot (float) in numeric entries
        if new_value == "" :
            return True
        # allow only one decimal point and digits
        if new_value.count('.') > 1 :
            return False
        return all(c.isdigit() or c == '.' for c in new_value)

    # ----- Callbacks -----
    def _on_precheck(self) :
        # handle Precheck Scan button
        logger.info("Precheck Scan initiated from GUI.")
        try :
            self.on_precheck()
        except Exception as e :
            logger.exception("Precheck failed.")
            import tkinter.messagebox as msg
            msg.showerror("Precheck Error", str(e))

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

            # keep a reference to prevent garbage collection
            self._simulation_window = sim_win

            # notify external callback (e.g., start camera/projector)
            self.on_launch_simulation()
        except Exception as e :
            logger.exception("Failed to launch simulation.")
            import tkinter.messagebox as msg
            msg.showerror("Launch Error", str(e))

    def _on_save_settings(self) :
        # save (or log) the advanced settings values
        logger.info(
            "Advanced settings saved: max_entities=%d, despawn_time=%.1f, gravity_scale=%.1f",
            self.max_entities_var.get(),
            self.despawn_time_var.get(),
            self.gravity_scale_var.get()
        )
        import tkinter.messagebox as msg
        msg.showinfo("Settings", "Settings applied (simulation restart may be required).")

    def _on_quit(self) :
        # gracefully quit the application
        logger.info("Quit requested from main menu.")
        # destroy the simulation window if it exists
        if hasattr(self, '_simulation_window') and self._simulation_window.winfo_exists():
            self._simulation_window.destroy()
        self.on_quit()
        self.root.quit()
        self.root.destroy()

    def run(self) :
        # start the CustomTkinter main loop
        self.root.mainloop()