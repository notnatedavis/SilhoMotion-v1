# config.py

# Stores all adjustable parameters (camera index, projector resolution,
#    physics constants, calibration settings) in one place for easy
#    tuning

# ----- Imports -----
import os
from dotenv import load_dotenv
from dataclasses import dataclass
from utils.validators import validate_config

# ----- Load environment -----
load_dotenv()

# ----- Configuration dataclass -----
@dataclass(frozen=True)
class Config :
    # central configuration for SilhoMotion, loaded from environment variables
    CAMERA_INDEX: int = int(os.getenv("CAMERA_INDEX", 0))
    PROJECTOR_SCREEN: int = int(os.getenv("PROJECTOR_SCREEN", 1))
    PROJECTOR_WIDTH: int = int(os.getenv("PROJECTOR_WIDTH", 1920))
    PROJECTOR_HEIGHT: int = int(os.getenv("PROJECTOR_HEIGHT", 1080))
    PHYSICS_GRAVITY: tuple = (0, 500) # pymunk gravity vector (x, y)
    FRAME_RATE: int = 30 # target frames per second
    CALIBRATION_TIMEOUT: int = 10 # seconds before calibration gives up

# ----- Validate on import -----
config = Config()
try :
    validate_config(config)
except ValueError as e :
    raise SystemExit(f"Invalid configuration: {e}")