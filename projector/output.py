# projector/output.py

# Manages a fullscreen window on the projector (second display/HDMI) 
#    using Pygame or OpenCV; draws the simulation visuals and any 
#    calibration overlays

# ----- Imports -----
import pygame
import logging
import time
from projector.exceptions import ProjectorInitError

# ----- Logger -----
logger = logging.getLogger(__name__)

class ProjectorWindow :
    # Manages a fullscreen Pygame window on the selected projector screen

    def __init__(self, screen_index=1) :
        pygame.init()
        self.display_info = pygame.display.Info()
        num_displays = self._get_num_displays()
        if screen_index >= num_displays :
            raise ProjectorInitError(
                f"Screen index {screen_index} out of range ({num_displays} available)."
            )
        logger.info("Opening fullscreen on display %d.", screen_index)
        # Set environment variable before initialising display
        import os
        os.environ['SDL_VIDEO_WINDOW_POS'] = f"0,0"   # approximate; for precise placement use pygame.display.set_mode flags
        # Note: pygame doesn't directly support multi‑monitor selection; using fullscreen on screen 0.
        # To target a specific monitor, we rely on the operating system setting that screen as primary.
        # A robust solution would use pyglet or SDL2 directly. For simplicity, we use fullscreen on screen 0.
        self.screen = pygame.display.set_mode(
            (self.display_info.current_w, self.display_info.current_h),
            pygame.FULLSCREEN
        )
        pygame.display.set_caption("SilhoMotion Projector")
        self.clock = pygame.time.Clock()
        logger.info("Projector window initialised.")

    def _get_num_displays(self) :
        # Pygame doesn't have a direct API; assume 1 unless we handle it differently
        return 1   # placeholder – see improvement note (if exists)

    def draw_frame(self, simulation_state: dict) :
        # Render the simulation visual. 'simulation_state' is a placeholder dict
        # that will contain object positions, colours, etc.
        
        # Dark background
        self.screen.fill((46, 46, 46))   # matches BG_COLOUR
        # Draw a simple test shape for now – can be replaced with real rendering
        pygame.draw.circle(self.screen, (200, 200, 200), (400, 300), 50)
        pygame.display.flip()
        self.clock.tick(30)   # limit to 30 FPS; adjust as needed

    def close(self) :
        # Quit Pygame gracefully
        pygame.quit()
        logger.info("Projector window closed.")