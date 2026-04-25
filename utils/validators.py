# utils/validators.py

# ----- Main -----
def validate_config(config) :
    # validate range and types of configuration attributes. Raise ValueError on failure
    if not isinstance(config.CAMERA_INDEX, int) or config.CAMERA_INDEX < 0 :
        raise ValueError("CAMERA_INDEX must be a non‑negative integer.")
    if not isinstance(config.PROJECTOR_SCREEN, int) or config.PROJECTOR_SCREEN < 0 : 
        raise ValueError("PROJECTOR_SCREEN must be a non‑negative integer.")
    if not isinstance(config.PHYSICS_GRAVITY, tuple) or len(config.PHYSICS_GRAVITY) != 2 :
        raise ValueError("PHYSICS_GRAVITY must be a tuple of two numeric values.")
    if not all(isinstance(v, (int, float)) for v in config.PHYSICS_GRAVITY) :
        raise ValueError("Both components of PHYSICS_GRAVITY must be numeric.")
    
    # Future: add checks for projector resolution, etc.