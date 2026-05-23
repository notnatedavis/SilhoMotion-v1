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
- **Lightweight dependencies** – OpenCV, Pymunk, Pygame, Tkinter (built‑in)
- **Multi‑monitor support** – correctly opens fullscreen on the specified projector screen.

---

## Project-Structure

```bash
SilhoMotion/
├── camera/
│   ├── __init__.py
│   ├── calibrator.py     # QR‑based homography calculator (instant detection)
│   ├── capture.py        # Silhouette extraction + contour finding
│   ├── mapper.py         # Applies homography to contour points
│   └── exceptions.py     # Custom camera errors
├── docs/
│   ├── Notes.md
│   ├── Todo.md
│   └── Vision.md
├── gui/
│   ├── __init__.py
│   ├── control_window.py # Tkinter control panel with callback injection
│   ├── main_menu.py
│   └── styles.py         # Dark theme colours & font
├── physics/
│   ├── __init__.py
│   ├── exceptions.py
│   └── simulation.py     # Pymunk physics world with obstacle management
├── projector/
│   ├── __init__.py
│   ├── exceptions.py
│   └── output.py         # Pygame fullscreen projection on chosen monitor
├── utils/
│   ├── __init__.py
│   ├── logger.py         # Logger w/ console + rotation
│   └── validators.py     # Config validation (checks projector resolution)
├── .gitignore            # Excludes logs, venv, .env
├── common.py
├── main.py               # Entry point w/ calibration state machine
├── ReadMe.md             # You are here (hi!)
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
    python -m venv venv || python3 -m venv venv
    venv\Scripts\activate  ||  source venv/bin/activate
    ```

3. **Prerequisites**
    ```bash
   pip install -r requirements.txt
   ```

4. **Start the application**
    ```bash
    python main.py || python3 main.py
    ```
    
---

## Configuration

All tunable settings are in common.py,
- `CAMERA_INDEX` – webcam index (default 0)
- `PROJECTOR_SCREEN` – which display to use for projection (default 1)
- `PROJECTOR_WIDTH` – horizontal resolution of the projector (default 1920)
- `PROJECTOR_HEIGHT` – vertical resolution of the projector (default 1080)
- `PHYSICS_GRAVITY` – gravity vector (default (0, 500))
- `FRAME_RATE` – target simulation rate
- `CALIBRATION_TIMEOUT` – seconds before QR detection times out

---

## Additional-Info

update this

---