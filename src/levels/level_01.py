from src.levels.level_base import LevelBase
from config import TILE_SIZE

G = LevelBase.GROUND
P = LevelBase.PLATFORM
E = LevelBase.EMPTY


class Level01(LevelBase):
    TILE_MAP = [
        [E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E],
        [E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E],
        [E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E],
        [E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E,E],
        [E,E,E,E,P,P,E,E,E,E,E,E,E,E,P,P,P,E,E,E,E,E,E,P,P,E,E,E,E,E,E,P,P,P,E,E,E,E,E,E],
        [E,E,E,E,E,E,E,E,E,E,P,P,P,E,E,E,E,E,E,P,P,P,E,E,E,E,E,E,P,P,E,E,E,E,E,E,E,E,E,E],
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
            {"x":7*TILE_SIZE, "y":gy,"type":"ground","patrol_left":5*TILE_SIZE,"patrol_right":10*TILE_SIZE},
            # Flyer over platforms (stops speed-running across them)
            {"x":12*TILE_SIZE,"y":gy-5*TILE_SIZE,"type":"flying","patrol_left":10*TILE_SIZE,"patrol_right":17*TILE_SIZE},
            {"x":14*TILE_SIZE,"y":gy,"type":"flophopper","patrol_left":12*TILE_SIZE,"patrol_right":17*TILE_SIZE},
            # Ground enemy ON platform
            {"x":15*TILE_SIZE,"y":gy-4*TILE_SIZE,"type":"ground","patrol_left":14*TILE_SIZE,"patrol_right":17*TILE_SIZE},
            {"x":20*TILE_SIZE,"y":gy,"type":"ground","patrol_left":18*TILE_SIZE,"patrol_right":23*TILE_SIZE},
            # Flyer over middle platforms
            {"x":22*TILE_SIZE,"y":gy-5*TILE_SIZE,"type":"flying","patrol_left":19*TILE_SIZE,"patrol_right":26*TILE_SIZE},
            {"x":27*TILE_SIZE,"y":gy,"type":"flophopper","patrol_left":25*TILE_SIZE,"patrol_right":30*TILE_SIZE},
            {"x":33*TILE_SIZE,"y":gy-2*TILE_SIZE,"type":"flying","patrol_left":31*TILE_SIZE,"patrol_right":37*TILE_SIZE},
        ]
