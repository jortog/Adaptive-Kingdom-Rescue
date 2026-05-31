from src.levels.level_base import LevelBase
from config import TILE_SIZE

G = LevelBase.GROUND
P = LevelBase.PLATFORM
E = LevelBase.EMPTY


class Level02(LevelBase):
    TILE_MAP = [
        [E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E],
        [E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E],
        [E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E],
        [E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E],
        [E,E,E,E,P,P,E,E,E,E,E,E,P,P,P,E,E,E,E,E,E,E,P,P,E,E,E,E,P,P,P,E,E,E,E,E],
        [E,E,E,E,E,E,E,E,P,P,P,E,E,E,E,E,E,P,P,E,E,E,E,E,E,E,E,E,E,E,E,E,P,P,E,E],
        [E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E],
        [E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E],
        [G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G,G],
    ]
    def get_princess_position(self):
        cols=len(self.TILE_MAP[0]); rows=len(self.TILE_MAP)
        return ((cols-2)*TILE_SIZE, (rows-2)*TILE_SIZE)
    def get_enemy_spawns(self):
        rows=len(self.TILE_MAP); gy=(rows-2)*TILE_SIZE
        return [
            {"x":7*TILE_SIZE,"y":gy,"type":"ground","patrol_left":5*TILE_SIZE,"patrol_right":11*TILE_SIZE},
            {"x":12*TILE_SIZE,"y":gy-1*TILE_SIZE,"type":"flying","patrol_left":10*TILE_SIZE,"patrol_right":16*TILE_SIZE},
            {"x":5*TILE_SIZE,"y":gy-4*TILE_SIZE,"type":"ground","patrol_left":4*TILE_SIZE,"patrol_right":7*TILE_SIZE},
            {"x":16*TILE_SIZE,"y":gy,"type":"flophopper","patrol_left":14*TILE_SIZE,"patrol_right":19*TILE_SIZE},
            {"x":13*TILE_SIZE,"y":gy-4*TILE_SIZE,"type":"flophopper","patrol_left":12*TILE_SIZE,"patrol_right":15*TILE_SIZE},
            {"x":20*TILE_SIZE,"y":gy-3*TILE_SIZE,"type":"flying","patrol_left":18*TILE_SIZE,"patrol_right":24*TILE_SIZE},
            {"x":24*TILE_SIZE,"y":gy,"type":"ground","patrol_left":22*TILE_SIZE,"patrol_right":27*TILE_SIZE},
            {"x":22*TILE_SIZE,"y":gy-4*TILE_SIZE,"type":"ground","patrol_left":21*TILE_SIZE,"patrol_right":24*TILE_SIZE},
            {"x":28*TILE_SIZE,"y":gy-2*TILE_SIZE,"type":"flying","patrol_left":26*TILE_SIZE,"patrol_right":32*TILE_SIZE},
            {"x":32*TILE_SIZE,"y":gy,"type":"flophopper","patrol_left":30*TILE_SIZE,"patrol_right":34*TILE_SIZE},
        ]
