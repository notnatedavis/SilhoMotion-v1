# tests/test_utils.py

# ----- Imports -----
import pytest
from dataclasses import dataclass
from utils.validators import validate_config

# ----- Main -----
@dataclass
class FakeConfig :
    CAMERA_INDEX: int = 0
    PROJECTOR_SCREEN: int = 1
    PHYSICS_GRAVITY: tuple = (0, 500)

def test_validate_ok() :
    # Valid config should not raise an error
    cfg = FakeConfig()
    validate_config(cfg)  # no exception

def test_bad_camera_index() :
    # Negative camera index should raise ValueError
    cfg = FakeConfig(CAMERA_INDEX=-1)
    with pytest.raises(ValueError):
        validate_config(cfg)

def test_bad_gravity_length() :
    # Invalid gravity tuple length should raise ValueError
    cfg = FakeConfig(PHYSICS_GRAVITY=(1,))
    with pytest.raises(ValueError):
        validate_config(cfg)