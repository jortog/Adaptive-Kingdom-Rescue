from src.levels.level_base import LevelBase
from config import TILE_SIZE

G = LevelBase.GROUND
P = LevelBase.PLATFORM
E = LevelBase.EMPTY


class Level02(LevelBase):
    TILE_MAP = [
        [E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E],
        [E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E],
        [E,E,E,E,P,P,E,E,E,E,E,E,P,P,P,E,E,E,E,E,E,E,P,P,E,E,E,E,E,E],
        [E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E],
        [E,E,E,E,E,E,E,E,P,P,P,E,E,E,E,E,E,P,P,E,E,E,E,E,E,E,E,E,E,E],
        [E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E],
        [E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E],
        [E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E],
        [G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G],
    ]

    def get_princess_position(self):
        cols = len(self.TILE_MAP[0])
        rows = len(self.TILE_MAP)
        return ((cols - 2) * TILE_SIZE, (rows - 2) * TILE_SIZE)

    def get_enemy_spawns(self):
        rows = len(self.TILE_MAP)
        ground_y = (rows - 2) * TILE_SIZE
        return [
            {
                "x": 8 * TILE_SIZE,
                "y": ground_y,
                "type": "ground",
                "patrol_left": 5 * TILE_SIZE,
                "patrol_right": 12 * TILE_SIZE,
            },
            {
                "x": 16 * TILE_SIZE,
                "y": ground_y,
                "type": "flying",
                "patrol_left": 13 * TILE_SIZE,
                "patrol_right": 20 * TILE_SIZE,
            },
            {
                "x": 22 * TILE_SIZE,
                "y": ground_y,
                "type": "ground",
                "patrol_left": 19 * TILE_SIZE,
                "patrol_right": 26 * TILE_SIZE,
            },
            {
                "x": 26 * TILE_SIZE,
                "y": ground_y,
                "type": "flying",
                "patrol_left": 23 * TILE_SIZE,
                "patrol_right": 28 * TILE_SIZE,
            },
        ]
