import pygame
from config import TILE_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT
from src.systems.renderer import draw_background, draw_ground_tile, draw_platform_tile


class LevelBase:
    EMPTY = 0
    GROUND = 1
    PLATFORM = 2
    SPIKE = 3
    TILE_MAP = []

    def __init__(self):
        self.platforms = []
        self.hazards = []
        self.spawn_x = TILE_SIZE
        self.spawn_y = 0
        self._build_from_tilemap()
        self.pixel_width = (
            len(self.TILE_MAP[0]) * TILE_SIZE if self.TILE_MAP else SCREEN_WIDTH
        )
        self.pixel_height = (
            len(self.TILE_MAP) * TILE_SIZE if self.TILE_MAP else SCREEN_HEIGHT
        )
        self.render_y = max(0, SCREEN_HEIGHT - self.pixel_height)

    def _build_from_tilemap(self):
        for row_idx, row in enumerate(self.TILE_MAP):
            for col_idx, tile in enumerate(row):
                x = col_idx * TILE_SIZE
                y = row_idx * TILE_SIZE
                rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
                if tile in (self.GROUND, self.PLATFORM):
                    self.platforms.append(rect)
                elif tile == self.SPIKE:
                    self.hazards.append(rect)
        if self.TILE_MAP:
            for row_idx in range(len(self.TILE_MAP) - 1, -1, -1):
                if self.TILE_MAP[row_idx][1] in (self.GROUND, self.PLATFORM):
                    self.spawn_x = TILE_SIZE
                    self.spawn_y = row_idx * TILE_SIZE - TILE_SIZE
                    break

    def draw_tiles(self, surface, camera_offset_x, camera_offset_y=0):
        draw_background(surface, camera_offset_x)
        for row_idx, row in enumerate(self.TILE_MAP):
            for col_idx, tile in enumerate(row):
                if tile == self.EMPTY:
                    continue
                rect = pygame.Rect(
                    col_idx * TILE_SIZE - camera_offset_x,
                    row_idx * TILE_SIZE + self.render_y - camera_offset_y,
                    TILE_SIZE,
                    TILE_SIZE,
                )
                if tile == self.GROUND:
                    draw_ground_tile(surface, rect)
                elif tile == self.PLATFORM:
                    draw_platform_tile(surface, rect)
                elif tile == self.SPIKE:
                    pygame.draw.rect(surface, (200, 50, 50), rect)

    def get_princess_position(self):
        return (self.pixel_width - 2 * TILE_SIZE, TILE_SIZE)

    def get_enemy_spawns(self):
        return []
