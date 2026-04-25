# tests/test_camera.py

# ----- Imports -----
import pytest
from unittest.mock import patch, MagicMock
from camera.capture import SilhouetteCapture, CameraNotFoundError

# ----- Main -----
def test_camera_init_success() :
    # Test that SilhouetteCapture opens a valid camera
    with patch('cv2.VideoCapture') as mock_cap:
        instance = mock_cap.return_value
        instance.isOpened.return_value = True
        capture = SilhouetteCapture(0)
        assert capture.cap is not None

def test_camera_init_failure() :
    # Test that CameraNotFoundError is raised when camera fails to open
    with patch('cv2.VideoCapture') as mock_cap:
        instance = mock_cap.return_value
        instance.isOpened.return_value = False
        with pytest.raises(CameraNotFoundError):
            SilhouetteCapture(0)

def test_read_frame() :
    # Test that read_frame returns a binary mask
    with patch('cv2.VideoCapture') as mock_cap, \
         patch('cv2.createBackgroundSubtractorMOG2') as mock_bg:
        instance = mock_cap.return_value
        instance.isOpened.return_value = True
        instance.read.return_value = (True, MagicMock())
        capture = SilhouetteCapture(0)
        mask = capture.read_frame()
        assert mask is not None