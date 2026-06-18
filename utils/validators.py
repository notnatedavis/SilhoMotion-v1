# utils/validators.py

# ----- Main -----
def validate_config(config) :
    # validate range and types of configuration attributes. Raise ValueError on failure
    if not isinstance(config.CAMERA_INDEX, int) or config.CAMERA_INDEX < 0 :
        raise ValueError("CAMERA_INDEX must be a non‑negative integer.")
    if not isinstance(config.PHYSICS_GRAVITY, tuple) or len(config.PHYSICS_GRAVITY) != 2 :
        raise ValueError("PHYSICS_GRAVITY must be a tuple of two numeric values.")
    if not all(isinstance(v, (int, float)) for v in config.PHYSICS_GRAVITY) :
        raise ValueError("Both components of PHYSICS_GRAVITY must be numeric.")
    if not isinstance(config.FRAME_RATE, int) or config.FRAME_RATE <= 0 :
        raise ValueError("FRAME_RATE must be a positive integer.")
    if not isinstance(config.CALIBRATION_TIMEOUT, int) or config.CALIBRATION_TIMEOUT <= 0 :
        raise ValueError("CALIBRATION_TIMEOUT must be a positive integer.")