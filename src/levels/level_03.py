from src.levels.level_base import LevelBase
from config import TILE_SIZE

G = LevelBase.GROUND
P = LevelBase.PLATFORM
E = LevelBase.EMPTY


class Level03(LevelBase):
    TILE_MAP = [
        [E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E],
        [E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E],
        [E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E],
        [E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E],
        [E,E,P,P,E,E,E,E,E,E,P,P,P,E,E,E,E,E,E,E,E,E,P,P,P,E,E,E,E,E,E,P,P,E,E,E,E,P,P,E],
        [E,E,E,E,E,E,P,P,P,E,E,E,E,E,E,P,P,E,E,P,P,E,E,E,E,E,P,P,P,E,E,E,E,E,E,P,P,E,E,E],
        [E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E],
        [E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E],
        [G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G],
    ]
    def get_princess_position(self):
        cols=len(self.TILE_MAP[0]); rows=len(self.TILE_MAP)
        return ((cols-2)*TILE_SIZE, (rows-2)*TILE_SIZE)
    def get_enemy_spawns(self):
        rows=len(self.TILE_MAP); gy=(rows-2)*TILE_SIZE
        return [
            {"x":6*TILE_SIZE,"y":gy,"type":"ground","patrol_left":4*TILE_SIZE,"patrol_right":10*TILE_SIZE},
            {"x":10*TILE_SIZE,"y":gy-2*TILE_SIZE,"type":"flying","patrol_left":8*TILE_SIZE,"patrol_right":14*TILE_SIZE},
            {"x":3*TILE_SIZE,"y":gy-4*TILE_SIZE,"type":"ground","patrol_left":2*TILE_SIZE,"patrol_right":5*TILE_SIZE},
            {"x":13*TILE_SIZE,"y":gy,"type":"flophopper","patrol_left":11*TILE_SIZE,"patrol_right":16*TILE_SIZE},
            {"x":7*TILE_SIZE,"y":gy-4*TILE_SIZE,"type":"flophopper","patrol_left":6*TILE_SIZE,"patrol_right":9*TILE_SIZE},
            {"x":17*TILE_SIZE,"y":gy-1*TILE_SIZE,"type":"flying","patrol_left":15*TILE_SIZE,"patrol_right":21*TILE_SIZE},
            {"x":21*TILE_SIZE,"y":gy,"type":"ground","patrol_left":19*TILE_SIZE,"patrol_right":25*TILE_SIZE},
            {"x":11*TILE_SIZE,"y":gy-4*TILE_SIZE,"type":"ground","patrol_left":10*TILE_SIZE,"patrol_right":13*TILE_SIZE},
            {"x":24*TILE_SIZE,"y":gy-3*TILE_SIZE,"type":"flying","patrol_left":22*TILE_SIZE,"patrol_right":28*TILE_SIZE},
            {"x":23*TILE_SIZE,"y":gy-4*TILE_SIZE,"type":"flophopper","patrol_left":22*TILE_SIZE,"patrol_right":25*TILE_SIZE},
            {"x":27*TILE_SIZE,"y":gy,"type":"flophopper","patrol_left":25*TILE_SIZE,"patrol_right":30*TILE_SIZE},
            {"x":31*TILE_SIZE,"y":gy-1*TILE_SIZE,"type":"flying","patrol_left":29*TILE_SIZE,"patrol_right":35*TILE_SIZE},
            {"x":35*TILE_SIZE,"y":gy,"type":"ground","patrol_left":33*TILE_SIZE,"patrol_right":38*TILE_SIZE},
        ]
