# common.py

# Central configuration for SilhoMotion
# Edit the values below directly

# ----- Imports -----
from dataclasses import dataclass
from utils.validators import validate_config

# ----- Main -----
@dataclass(frozen=True)
class Config :
    # Application‑wide constants
    CAMERA_INDEX: int = 0             # webcam device index
    PROJECTOR_SCREEN: int = 1         # projector display index (0 = primary)
    PROJECTOR_WIDTH: int = 1920       # projector horizontal resolution
    PROJECTOR_HEIGHT: int = 1080      # projector vertical resolution
    PHYSICS_GRAVITY: tuple = (0, 500) # pymunk gravity vector (x, y)
    FRAME_RATE: int = 30              # target frames per second
    CALIBRATION_TIMEOUT: int = 10     # seconds before calibration gives up

# validate the configuration immediately so that errors surface early
config = Config()
try :
    validate_config(config)
except ValueError as e :
    raise SystemExit(f"Invalid configuration: {e}")