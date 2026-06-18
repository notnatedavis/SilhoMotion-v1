# gui/styles.py

# Central appearance configuration for the SilhoMotion GUI
# CustomTkinter handles most theming, but we keep a few helper constants
# for consistency in custom elements

# ----- Imports -----
import customtkinter as ctk

# ---- Appearance mode & colour theme ----
def apply_global_style() :
    """Apply the global dark theme and default colour palette."""
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")  # built-in themes: "blue", "dark-blue", "green"

# ---- Fonts ----
FONT_HEADING = ("Segoe UI", 16, "bold")
FONT_BUTTON  = ("Segoe UI", 13, "bold")
FONT_BODY    = ("Segoe UI", 12)

# ---- Generic font for Tkinter controls (used in control_window.py) ----
FONT = ("Segoe UI", 11)          # for checkbuttons, labels, scale, etc.

# ---- Custom colours ----
BG_COLOUR = "#2C3E50"            # dark background for the control window
BUTTON_COLOUR = "#3498DB"        # blue for buttons (matching CustomTkinter's "blue" theme)
DANGER_COLOUR = "#C0392B"        # for critical buttons (quit)