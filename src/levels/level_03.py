from src.levels.level_base import LevelBase
from config import TILE_SIZE


class Level03(LevelBase):
    """Level 3: NIGHTMARE - Maximum enemies, 1 power-up, minimal platforms, spike hazards"""
    PROCEDURAL = True
    ROWS = 9
    COLS = 35  # Longer level to give breathing room at start
    N_LOWER = 3  # Few platforms but enough to survive
    N_UPPER = 1  # One upper platform for tactical advantage

    def get_princess_position(self) -> tuple[int, int]:
        cols = len(self.TILE_MAP[0])
        rows = len(self.TILE_MAP)
        return ((cols - 2) * TILE_SIZE, (rows - 2) * TILE_SIZE)

    def get_powerup_spawns(self, kinds):
        """Level 3 - Only 1 shield power-up at a strategic location"""
        return super().get_powerup_spawns(["shield"])

    def get_enemy_spawns(self):
        rows = len(self.TILE_MAP)
        ground_y = (rows - 2) * TILE_SIZE
        return [
            # Enemy 1 - Ground further away from spawn (was 3, now 6)
            {
                "x": 8 * TILE_SIZE,
                "y": ground_y,
                "type": "ground",
                "patrol_left": 6 * TILE_SIZE,
                "patrol_right": 12 * TILE_SIZE,
            },
            # Enemy 2 - Flying further away
            {
                "x": 10 * TILE_SIZE,
                "y": ground_y - 3 * TILE_SIZE,
                "type": "flying",
                "patrol_left": 8 * TILE_SIZE,
                "patrol_right": 14 * TILE_SIZE,
            },
            # Enemy 3 - Flophopper with more space
            {
                "x": 13 * TILE_SIZE,
                "y": ground_y,
                "type": "flophopper",
                "patrol_left": 11 * TILE_SIZE,
                "patrol_right": 17 * TILE_SIZE,
            },
            # Enemy 4 - Second flying
            {
                "x": 16 * TILE_SIZE,
                "y": ground_y - 2 * TILE_SIZE,
                "type": "flying",
                "patrol_left": 14 * TILE_SIZE,
                "patrol_right": 20 * TILE_SIZE,
            },
            # Enemy 5 - Ground in middle section
            {
                "x": 18 * TILE_SIZE,
                "y": ground_y,
                "type": "ground",
                "patrol_left": 16 * TILE_SIZE,
                "patrol_right": 22 * TILE_SIZE,
            },
            # Enemy 6 - High flying enemy
            {
                "x": 21 * TILE_SIZE,
                "y": ground_y - 4 * TILE_SIZE,
                "type": "flying",
                "patrol_left": 19 * TILE_SIZE,
                "patrol_right": 25 * TILE_SIZE,
            },
            # Enemy 7 - Second flophopper
            {
                "x": 23 * TILE_SIZE,
                "y": ground_y,
                "type": "flophopper",
                "patrol_left": 21 * TILE_SIZE,
                "patrol_right": 27 * TILE_SIZE,
            },
            # Enemy 8 - Third flying enemy
            {
                "x": 25 * TILE_SIZE,
                "y": ground_y - 3 * TILE_SIZE,
                "type": "flying",
                "patrol_left": 23 * TILE_SIZE,
                "patrol_right": 29 * TILE_SIZE,
            },
            # Enemy 9 - Ground guarding middle
            {
                "x": 27 * TILE_SIZE,
                "y": ground_y,
                "type": "ground",
                "patrol_left": 25 * TILE_SIZE,
                "patrol_right": 31 * TILE_SIZE,
            },
            # Enemy 10 - Flying near princess
            {
                "x": 29 * TILE_SIZE,
                "y": ground_y - 3 * TILE_SIZE,
                "type": "flying",
                "patrol_left": 27 * TILE_SIZE,
                "patrol_right": 33 * TILE_SIZE,
            },
            # Enemy 11 - Final ground enemy guarding princess
            {
                "x": 31 * TILE_SIZE,
                "y": ground_y,
                "type": "ground",
                "patrol_left": 29 * TILE_SIZE,
                "patrol_right": 35 * TILE_SIZE,
            },
            # Enemy 12 - Extra flying enemy for chaos
            {
                "x": 33 * TILE_SIZE,
                "y": ground_y - 2 * TILE_SIZE,
                "type": "flying",
                "patrol_left": 31 * TILE_SIZE,
                "patrol_right": 35 * TILE_SIZE,
            },
        ]

    def _generate_tilemap(self, rng):
        """Override to create hard but possible layout with strategic platforms"""
        rows, cols = self.ROWS, self.COLS
        grid = [[self.EMPTY] * cols for _ in range(rows)]
        ground_row = rows - 1

        # Safe starting area - no spikes for first 5 columns
        for c in range(cols):
            # Add spike pits after the safe starting zone
            if c >= 8 and ((12 <= c <= 13) or (20 <= c <= 21) or (28 <= c <= 29)):
                grid[ground_row][c] = self.SPIKE
            else:
                grid[ground_row][c] = self.GROUND

        # Add lower platforms (3 platforms, well-spaced, starting further in)
        lower_row = ground_row - 2
        # (start, end) columns - moved right
        platforms = [(10, 12), (18, 20), (26, 28)]
        for start, end in platforms:
            for c in range(start, end + 1):
                if 1 < c < cols - 1:
                    grid[lower_row][c] = self.PLATFORM

        # Add one upper platform for tactical positioning
        upper_row = ground_row - 4
        for c in range(22, 25):
            if 1 < c < cols - 1:
                grid[upper_row][c] = self.PLATFORM

        return grid
