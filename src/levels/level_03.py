from src.levels.level_base import LevelBase
from config import TILE_SIZE


class Level03(LevelBase):
    PROCEDURAL = True
    ROWS = 9
    COLS = 30
    N_LOWER = 5
    N_UPPER = 2

    def get_princess_position(self):
        cols = len(self.TILE_MAP[0])
        rows = len(self.TILE_MAP)
        return ((cols - 2) * TILE_SIZE, (rows - 2) * TILE_SIZE)

    def get_enemy_spawns(self):
        rows = len(self.TILE_MAP)
        ground_y = (rows - 2) * TILE_SIZE
        return [
            {
                "x": 6 * TILE_SIZE,
                "y": ground_y,
                "type": "ground",
                "patrol_left": 3 * TILE_SIZE,
                "patrol_right": 9 * TILE_SIZE,
            },
            {
                "x": 12 * TILE_SIZE,
                "y": ground_y,
                "type": "flying",
                "patrol_left": 9 * TILE_SIZE,
                "patrol_right": 15 * TILE_SIZE,
            },
            {
                "x": 18 * TILE_SIZE,
                "y": ground_y,
                "type": "ground",
                "patrol_left": 15 * TILE_SIZE,
                "patrol_right": 21 * TILE_SIZE,
            },
            {
                "x": 22 * TILE_SIZE,
                "y": ground_y,
                "type": "flying",
                "patrol_left": 19 * TILE_SIZE,
                "patrol_right": 25 * TILE_SIZE,
            },
            {
                "x": 26 * TILE_SIZE,
                "y": ground_y,
                "type": "ground",
                "patrol_left": 23 * TILE_SIZE,
                "patrol_right": 28 * TILE_SIZE,
            },
        ]
