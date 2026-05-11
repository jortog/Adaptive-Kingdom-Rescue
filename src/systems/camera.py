# src/systems/camera.py
import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE


class Camera:
    """
    2D side-scrolling camera with linear interpolation.
    Tracks the player horizontally; small vertical deadzone.
    """

    LERP_SPEED    = 8.0
    VERTICAL_DEAD = 3 * TILE_SIZE

    def __init__(self, level_pixel_width: int, level_pixel_height: int):
        self.level_w  = level_pixel_width
        self.level_h  = level_pixel_height
        self.offset_x = 0.0
        self.offset_y = 0.0

    def update(self, target_rect, dt: float):
        desired_x = target_rect.centerx - SCREEN_WIDTH  // 2
        desired_y = target_rect.centery - SCREEN_HEIGHT // 2

        self.offset_x += (desired_x - self.offset_x) * self.LERP_SPEED * dt
        self.offset_y += (desired_y - self.offset_y) * self.LERP_SPEED * dt

        self.offset_x = max(0, min(self.offset_x, self.level_w  - SCREEN_WIDTH))
        self.offset_y = max(0, min(self.offset_y, self.level_h  - SCREEN_HEIGHT))

    @property
    def int_x(self) -> int:
        return int(self.offset_x)

    @property
    def int_y(self) -> int:
        return int(self.offset_y)

    def apply(self, rect) -> pygame.Rect:
        return rect.move(-self.int_x, -self.int_y)