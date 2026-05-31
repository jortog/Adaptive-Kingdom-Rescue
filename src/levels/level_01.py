from src.levels.level_base import LevelBase
from config import TILE_SIZE

G = LevelBase.GROUND
P = LevelBase.PLATFORM
E = LevelBase.EMPTY


class Level01(LevelBase):
    """
    Level 1: now harder. Platforms are real (jumpable), 5 enemies including
    a flying ambusher and a flophopper that matches your jumps.
    """
    TILE_MAP = [
        [E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E],
        [E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E],
        [E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E],
        [E,E,E,E,E,P,P,P,E,E,E,E,E,P,P,P,P,E,E,E,E,E,E,P,P,P,E,E,E,E,E,P,P,P,E,E],
        [E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E],
        [E,E,E,E,E,E,E,E,E,E,P,P,P,E,E,E,E,E,E,P,P,P,E,E,E,E,E,E,P,P,E,E,E,E,E,E],
        [E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E],
        [E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E],
        [G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G],
    ]

    def get_princess_position(self):
        cols = len(self.TILE_MAP[0])
        rows = len(self.TILE_MAP)
        return ((cols - 2) * TILE_SIZE, (rows - 2) * TILE_SIZE)

    def get_enemy_spawns(self):
        rows = len(self.TILE_MAP)
        gy = (rows - 2) * TILE_SIZE
        return [
            {
                "x": 8 * TILE_SIZE,
                "y": gy,
                "type": "ground",
                "patrol_left": 6 * TILE_SIZE,
                "patrol_right": 12 * TILE_SIZE,
            },
            {
                "x": 14 * TILE_SIZE,
                "y": gy,
                "type": "flophopper",
                "patrol_left": 13 * TILE_SIZE,
                "patrol_right": 17 * TILE_SIZE,
            },
            {
                "x": 20 * TILE_SIZE,
                "y": gy,
                "type": "ground",
                "patrol_left": 18 * TILE_SIZE,
                "patrol_right": 24 * TILE_SIZE,
            },
            {
                "x": 26 * TILE_SIZE,
                "y": gy - 3 * TILE_SIZE,
                "type": "flying",
                "patrol_left": 23 * TILE_SIZE,
                "patrol_right": 30 * TILE_SIZE,
            },
            {
                "x": 30 * TILE_SIZE,
                "y": gy,
                "type": "ground",
                "patrol_left": 28 * TILE_SIZE,
                "patrol_right": 33 * TILE_SIZE,
            },
        ]
