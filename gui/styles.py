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

# ---- Custom colours (rarely needed, but available) ----
DANGER_COLOUR = "#C0392B"   # for critical buttons (quit)