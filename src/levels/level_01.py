# src/levels/level_01.py
from src.levels.level_base import LevelBase
from config import TILE_SIZE

G = LevelBase.GROUND
P = LevelBase.PLATFORM
E = LevelBase.EMPTY
S = LevelBase.SPIKE


class Level01(LevelBase):
    """
    Level 1: Introduction level — 30 columns wide.
    Teaches basic jumping and introduces adaptive enemies.
    """

    TILE_MAP = [
        [E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E],
        [E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E],
        [E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E],
        [E,E,E,E,E,E,P,P,P,E,E,E,E,E,P,P,P,E,E,E,E,E,E,E,E,E,E,E,E,E],
        [E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,P,P,P,E,E,E,E,E,E,E],
        [E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E],
        [E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E],
        [E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E],
        [G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G],
    ]

    def get_princess_position(self):
        # Far right, ground level
        cols = len(self.TILE_MAP[0])
        rows = len(self.TILE_MAP)
        return ((cols - 2) * TILE_SIZE, (rows - 2) * TILE_SIZE)

    def get_enemy_spawns(self):
        rows = len(self.TILE_MAP)
        ground_y = (rows - 2) * TILE_SIZE
        return [
            {"x": 10 * TILE_SIZE, "y": ground_y, "type": "ground",
             "patrol_left": 8 * TILE_SIZE, "patrol_right": 13 * TILE_SIZE},
            {"x": 18 * TILE_SIZE, "y": ground_y, "type": "ground",
             "patrol_left": 16 * TILE_SIZE, "patrol_right": 22 * TILE_SIZE},
            {"x": 24 * TILE_SIZE, "y": ground_y, "type": "ground",
             "patrol_left": 22 * TILE_SIZE, "patrol_right": 27 * TILE_SIZE},
        ]