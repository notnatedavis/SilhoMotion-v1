# projector/output.py

# Manages a fullscreen window on the projector (second display)
#    using Pygame; draws the simulation visuals and any
#    calibration overlays

# ----- Imports -----
import pygame
import logging
from projector.exceptions import ProjectorInitError

# ----- Logger -----
logger = logging.getLogger(__name__)

class ProjectorWindow :
    # Manages a fullscreen Pygame window on the selected projector screen

    def __init__(self, screen_index=1, resolution=(1920, 1080)) :
        pygame.init()
        # Use the display keyword to target a specific monitor (0‑based)
        self.screen = None
        try :
            # Some Pygame builds may not support the 'display' argument;
            # fall back to screen 0 if needed.
            self.screen = pygame.display.set_mode(
                resolution, pygame.FULLSCREEN, display=screen_index
            )
        except pygame.error as e :
            raise ProjectorInitError(
                f"Cannot open fullscreen on display {screen_index}: {e}"
            )
        pygame.display.set_caption("SilhoMotion Projector")
        self.clock = pygame.time.Clock()
        logger.info("Projector window initialised on display %d, resolution %s.",
                    screen_index, resolution)

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