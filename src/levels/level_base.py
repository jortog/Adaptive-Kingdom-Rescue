import random

import pygame
from config import TILE_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT
from src.systems.renderer import draw_background, draw_ground_tile, draw_platform_tile


class LevelBase:
    EMPTY = 0
    GROUND = 1
    PLATFORM = 2
    SPIKE = 3
    TILE_MAP = []

    # Procedural layout. When PROCEDURAL is True the tile map is generated per
    # instance from a seed instead of using the hardcoded TILE_MAP, so every
    # attempt looks different while staying jump-reachable.
    PROCEDURAL = False
    ROWS = 9
    COLS = 30
    N_LOWER = 4  # platforms one hop above the ground
    N_UPPER = 1  # platforms one hop above a lower platform
    # Keep this many columns clear to the LEFT of the princess so no platform
    # hugs her — otherwise the player can vault off it and skip past her guards.
    PRINCESS_CLEAR_COLS = 5

    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        if self.PROCEDURAL:
            self.TILE_MAP = self._generate_tilemap(self.rng)
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

    def _generate_tilemap(self, rng):
        """Build a fresh tile map: a solid ground row plus platforms placed only
        at jump-reachable heights and spread out across the level. Lower
        platforms sit 2 tiles above the ground; upper platforms sit 2 tiles
        above a nearby lower platform so you can always hop up step by step."""
        rows, cols = self.ROWS, self.COLS
        grid = [[self.EMPTY] * cols for _ in range(rows)]
        ground_row = rows - 1
        for c in range(cols):
            grid[ground_row][c] = self.GROUND
        lower_row = ground_row - 2
        upper_row = ground_row - 4
        # Leave the player spawn (left) clear, and a wider gap before the princess
        # (right) so no platform hugs her and lets the player skip her guards.
        c_min, c_max = 3, cols - 2 - self.PRINCESS_CLEAR_COLS
        lower = self._scatter_row(grid, rng, lower_row, self.N_LOWER, c_min, c_max)
        self._place_supported_row(
            grid, rng, upper_row, self.N_UPPER, c_min, c_max, lower
        )
        return grid

    def _scatter_row(self, grid, rng, row, count, c_min, c_max):
        """Place `count` platforms, one per evenly-sized slot across the row, so
        they stay spread out instead of clumping. Returns [(c0, c1), ...]."""
        placed = []
        span = c_max - c_min + 1
        if count <= 0 or span < 2:
            return placed
        step = span / count
        max_w = max(2, min(4, int(step) - 1))
        for i in range(count):
            center = c_min + (i + 0.5) * step
            width = rng.randint(2, max_w)
            c0 = int(round(center - width / 2)) + rng.randint(-1, 1)
            c0 = max(c_min, min(c0, c_max - width + 1))
            # Keep at least a 2-tile gap from the previous platform.
            if placed and c0 <= placed[-1][1] + 2:
                c0 = placed[-1][1] + 3
            c1 = c0 + width - 1
            if c1 > c_max:
                continue
            for c in range(c0, c1 + 1):
                grid[row][c] = self.PLATFORM
            placed.append((c0, c1))
        return placed

    def _place_supported_row(self, grid, rng, row, count, c_min, c_max, supports):
        """Place upper platforms, each hovering just above one of `supports` (a
        lower platform) so it's always reachable with a single step-up hop."""
        placed = []
        if count <= 0 or not supports:
            return placed
        for (s0, s1) in rng.sample(supports, min(count, len(supports))):
            center = (s0 + s1) // 2
            width = rng.randint(2, 3)
            c0 = center - width // 2 + rng.randint(-1, 1)
            c0 = max(c_min, min(c0, c_max - width + 1))
            c1 = c0 + width - 1
            # Don't overlap or touch another upper platform.
            if any(not (c1 < p0 - 1 or c0 > p1 + 1) for (p0, p1) in placed):
                continue
            for c in range(c0, c1 + 1):
                grid[row][c] = self.PLATFORM
            placed.append((c0, c1))
        return placed

    def _platform_clusters(self):
        """Contiguous PLATFORM tiles grouped per row as (row, c0, c1)."""
        clusters = []
        for r, row in enumerate(self.TILE_MAP):
            c = 0
            while c < len(row):
                if row[c] == self.PLATFORM:
                    c0 = c
                    while c < len(row) and row[c] == self.PLATFORM:
                        c += 1
                    clusters.append((r, c0, c - 1))
                else:
                    c += 1
        return clusters

    def get_powerup_spawns(self, kinds):
        """Random but always-reachable power-up positions, re-rolled per attempt
        like the platforms. Each rests on the ground or on top of a (reachable)
        platform. Returns [(x, y, kind), ...]."""
        rows = len(self.TILE_MAP)
        cols = len(self.TILE_MAP[0]) if rows else 0
        ground_row = rows - 1
        pu_size = TILE_SIZE - 4
        # Candidate surfaces (column, y-resting-on-top).
        slots = [
            ((c0 + c1) // 2, r * TILE_SIZE - pu_size)
            for (r, c0, c1) in self._platform_clusters()
        ]
        slots += [
            (c, ground_row * TILE_SIZE - pu_size) for c in range(4, cols - 4, 3)
        ]
        self.rng.shuffle(slots)
        spawns = []
        chosen_cols = []
        for kind in kinds:
            # Prefer a slot spaced out from the ones already chosen.
            pick = next(
                (s for s in slots if all(abs(s[0] - c) >= 3 for c in chosen_cols)),
                slots[0] if slots else None,
            )
            if pick is None:
                continue
            slots.remove(pick)
            col, y = pick
            chosen_cols.append(col)
            spawns.append((col * TILE_SIZE, y, kind))
        return spawns

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
