# SilhoMotion

A creative, interactive system that captures a user’s silhouette via a webcam, feeds it into a real‑time 2D physics simulation, and projects the result onto a wall or screen. Control parameters using a companion GUI, and calibrate the camera‑projector alignment with a QR code.

---

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Project-Structure](#Project-Structure)
- [Usage](#usage)
- [Configuration](#Configuration)
- [Additional-Info](#Additional-Info)

---

## Introduction

SilhoMotion turns you into a dynamic obstacle in a physics playground. A camera extracts your silhouette, which becomes a static collision shape in a Pymunk‑based simulation. A second display (projector) shows the evolving scene – adding balls, forces, or visual effects. A dark‑themed Tkinter window lets you pause physics, adjust gravity, and run calibration.

**Core components:**
- **Camera** – OpenCV with background subtraction (MOG2) and contour extraction.
- **Physics** – Pymunk space where each person becomes a collection of static line segments.
- **Projector** – Pygame fullscreen window on a chosen monitor (multi‑monitor support).
- **GUI** – Tkinter control panel with toggles, sliders, and callback wiring.
- **Calibration** – QR‑code‑based homography to map camera coordinates to the projector.
- **Mapping** – A dedicated `Mapper` class transforms silhouette points from camera space to projector space using the homography.

Everything runs locally, free of charge, and the code is designed for clarity and extensibility.

---

## Features

- **Real‑time silhouette extraction** via MOG2 background subtractor and contour simplification.
- **2D physics simulation** using Pymunk – turning silhouettes into solid obstacles.
- **Flexible calibration** with QR marker detection (instant) and perspective mapping, driven by the main loop.
- **Independent control GUI** with dark theme, toggles, sliders, and callbacks for all actions.
- **Graceful error handling** – components raise specific exceptions, and the main loop logs and exits cleanly.
- **Lightweight dependencies** – OpenCV, Pymunk, Pygame, Tkinter (built‑in), and dotenv.
- **Multi‑monitor support** – correctly opens fullscreen on the specified projector screen.

---

## Project-Structure

```bash
SilhoMotion/
├── .env.example          # Environment variable template
├── .gitignore            # Excludes logs, venv, .env
├── camera/
│   ├── __init__.py
│   ├── calibrator.py     # QR‑based homography calculator (instant detection)
│   ├── capture.py        # Silhouette extraction + contour finding
│   ├── mapper.py         # Applies homography to contour points
│   └── exceptions.py     # Custom camera errors
├── docs/
│   └── notes.md
├── gui/
│   ├── __init__.py
│   ├── control_window.py # Tkinter control panel with callback injection
│   └── styles.py         # Dark theme colours & font
├── logs/                 # Runtime logs (rotated, not tracked)
├── physics/
│   ├── __init__.py
│   ├── exceptions.py
│   └── simulation.py     # Pymunk physics world with obstacle management
├── projector/
│   ├── __init__.py
│   ├── exceptions.py
│   └── output.py         # Pygame fullscreen projection on chosen monitor
├── scripts/
│   ├── calibrate.sh      # Launch calibration (future)
│   ├── run.sh            # Activate venv & run main
│   └── setup.sh          # Create venv & install deps
├── tests/
│   ├── __init__.py
│   ├── test_camera.py
│   ├── test_physics.py
│   └── test_utils.py
├── utils/
│   ├── __init__.py
│   ├── logger.py         # Logger w/ console + rotation
│   └── validators.py     # Config validation (checks projector resolution)
├── config.py             # all adjustable parameters (projector width/height)
├── main.py               # Entry point w/ calibration state machine
└── requirements.txt      # Python dependencies
```

---

## Usage

1. **Clone & Enter**
   ```bash
   git clone <repo-url> && cd SilhoMotion
    ```

2. **Set up environment**
    ```bash
    cp .env.example .env
    # edit .env if needed
    ```

3. **Run the setup script**
    ```bash
   chmod +x scripts/*.sh
   scripts/setup.sh
   ```

4. **Start the application**
    ```bash
    scripts/run.sh
    ```

5. **Chat with your bot on Telegram**
- Send /start or any message
- Use bash scripts/status.sh to see if it’s alive

---

## Configuration

All tunable settings are in config.py, loaded from environment variables via .env :
- `CAMERA_INDEX` – webcam index (default 0)
- `PROJECTOR_SCREEN` – which display to use for projection (default 1)
- `PROJECTOR_WIDTH` – horizontal resolution of the projector (default 1920)
- `PROJECTOR_HEIGHT` – vertical resolution of the projector (default 1080)
- `PHYSICS_GRAVITY` – gravity vector (default (0, 500))
- `FRAME_RATE` – target simulation rate
- `CALIBRATION_TIMEOUT` – seconds before QR detection times out

Constants can be changed in .env without modifying code

---

## Additional-Info

**Calibration workflow**

1. Press “Start Calibration” in the GUI.
2. Place a QR code in view of the camera.
3. The main loop will detect the code within the configured timeout and compute the homography
4. Once calibrated, your silhouette will be transformed into physics obstacles in projector space.

**Logging & Debugging**
All modules log to both console (INFO) and logs/project.log (DEBUG, rotated).

---

### 5. Next‑Focus Advice

With the core skeleton now functional, prioritise the following to increase robustness and usability:

1. **Full‑fledged calibration**: Link the GUI’s “Start Calibration” button to a calibration routine that uses `Calibrator` and applies the homography to map silhouette coordinates into physics space.  
2. **Projector rendering**: Replace the placeholder `draw_frame` with actual drawing of dynamic objects (e.g., multiple falling balls, the silhouette outline) using the physics state.  
3. **Multi‑display support**: Replace the simple fullscreen assumption with a robust method to target a specific monitor (e.g., using `pygame.RESIZABLE` and setting window position via `SDL_VIDEO_WINDOW_POS` properly).  
4. **Performance monitoring**: Add frame‑time tracking in the main loop and log warnings when FPS drops below a threshold.  
5. **Expand test coverage**: Add integration tests, mock the Tkinter mainloop, and test the full pipeline end‑to‑end.  
6. **Improve silhouette processing**: Apply contour extraction, smoothing, and simplification to reduce the number of physics segments for better performance.  
7. **Documentation**: Add inline docstrings to all public methods and possibly generate API docs with Sphinx.

These steps will turn the prototype into a polished, performant interactive installation.