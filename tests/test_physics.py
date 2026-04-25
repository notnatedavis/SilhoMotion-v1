# tests/test_physics.py

# ----- Imports -----
import pytest
from unittest.mock import patch, MagicMock
from physics.simulation import PhysicsWorld, SimulationStepError

# ----- Main -----
def test_step_raises_on_error() :
    # Test that step() raises SimulationStepError when pymunk fails
    world = PhysicsWorld()
    # Make space.step raise an exception
    with patch.object(world.space, 'step', side_effect=Exception("mock error")):
        with pytest.raises(SimulationStepError):
            world.step(0.1)

def test_add_obstacle() :
    # Test that adding a contour does not crash
    world = PhysicsWorld()
    contour = [(10, 20), (30, 40), (50, 60)]
    world.add_obstacle(contour)
    # Simple smoke test: no exception
    assert True