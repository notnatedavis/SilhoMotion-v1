# SilhoMotion

A creative, interactive system that captures a user’s silhouette via a webcam, feeds it into a real‑time 2D physics simulation, and displays the result in a dedicated window. Control parameters using a companion GUI, and calibrate the camera‑projector alignment with a QR code. Everything runs locally on a single display – you are free to move windows across multiple monitors as you wish.

---

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Project Structure](#project-structure)
- [Usage](#usage)
- [Configuration](#configuration)
- [Additional Info](#additional-info)

---

## Introduction

SilhoMotion turns you into a dynamic obstacle in a physics playground. A camera extracts your silhouette, which becomes a static collision shape in a Pymunk‑based simulation. A resizable window shows the evolving scene – adding balls, forces, or visual effects. A dark‑themed Tkinter control panel lets you pause physics, adjust gravity, and run calibration.

**Core components:**
- **Camera** – OpenCV with background subtraction (MOG2) and contour extraction.
- **Physics** – Pymunk space where each person becomes a collection of static line segments.
- **Rendering** – Custom drawing on a Tkinter Canvas, optimized for real‑time updates.
- **GUI** – CustomTkinter main menu and a separate control window with toggles, sliders, and callback wiring.
- **Calibration** – QR‑code‑based homography to map camera coordinates to the simulation space (future integration).
- **Mapping** – A dedicated `Mapper` class transforms silhouette points from camera space to simulation space using the homography.

Everything runs locally, free of charge, and the code is designed for clarity and extensibility.

---

## Features

- **Real‑time silhouette extraction** via MOG2 background subtractor and contour simplification.
- **2D physics simulation** using Pymunk – turning silhouettes into solid obstacles.
- **Flexible calibration** with QR marker detection (instant) and perspective mapping, driven by the main loop.
- **Independent control GUI** with dark theme, toggles, sliders, and callbacks for all actions.
- **Graceful error handling** – components raise specific exceptions, and the main loop logs and exits cleanly.
- **Lightweight dependencies** – OpenCV, Pymunk, CustomTkinter (built‑in).
- **Single‑display operation** – all windows open on the main screen; you can move them freely.
- **Thread‑safe camera capture** – runs in a separate thread to avoid blocking the GUI.

---

## Project Structure

```bash
SilhoMotion/
├── camera/
│   ├── __init__.py
│   ├── calibrator.py     # QR‑based homography calculator (instant detection)
│   ├── capture.py        # Silhouette extraction + contour finding
│   ├── mapper.py         # Applies homography to contour points
│   └── exceptions.py     # Custom camera errors
├── docs/
│   ├── notes.md
│   ├── Todo.md
│   └── Vision.md
├── gui/
│   ├── __init__.py
│   ├── control_window.py # Tkinter control panel with callback injection
│   ├── main_menu.py      # CustomTkinter main menu (Home + Advanced)
│   └── styles.py         # Dark theme colours & fonts
├── logs/                 # Log files (created at runtime)
├── physics/
│   ├── __init__.py
│   ├── exceptions.py
│   └── simulation.py     # Pymunk physics world with obstacle management
├── simulation/           # NEW: simulation rendering and control
│   ├── __init__.py
│   ├── controller.py     # Orchestrates camera, physics, and GUI updates
│   └── renderer.py       # Draws physics state on a Tkinter Canvas
├── utils/
│   ├── __init__.py
│   ├── logger.py         # Logger w/ console + rotation
│   └── validators.py     # Config validation (checks camera, gravity, etc.)
├── .gitignore
├── common.py             # Central configuration
├── main.py               # Entry point w/ calibration state machine
├── README.md
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

5. **Interact**
- Click **Precheck Scan** to verify your camera is working
- Click **Launch Simulation** to open the physics window and the control panel
- Use the **Control Window** to pause physics, toggle silhouette visibility, adjust gravity, and (in the future) run calibration
- On the **Advanced** page of the main menu, you can tweak simulation parameters (max entities, despawn rate, etc.) – these are placeholders for future enhancements
    
---

## Configuration

All tunable settings are in common.py,
- `CAMERA_INDEX` – webcam index (default 0)
- `PHYSICS_GRAVITY` – gravity vector (default (0, 500))
- `FRAME_RATE` – target simulation rate
- `CALIBRATION_TIMEOUT` – seconds before QR detection times out

---

## Additional-Info

Logging – Logs are written to logs/project.log with rotation (5 MB per file, 2 backups). The console shows INFO level and above, while the file captures DEBUG and above.

Calibration – The QR‑code detection is implemented in camera/calibrator.py but not yet wired into the main loop. Integration is planned for a future update.

Dynamic Objects – Clicking "Launch Simulation" adds a test ball to the physics world. You can extend this with keyboard shortcuts or UI buttons to spawn more objects.

Performance – The camera capture runs in a separate thread, and the main GUI update uses after() to maintain a steady frame rate. The renderer clears and redraws each frame – for better performance, consider using double‑buffering or incremental updates.

Extending – To add new visual effects, modify simulation/renderer.py. To change the physics behaviour, edit physics/simulation.py. New GUI controls can be added to gui/control_window.py.

---