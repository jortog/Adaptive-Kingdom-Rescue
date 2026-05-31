from src.levels.level_base import LevelBase
from config import TILE_SIZE


class Level02(LevelBase):
    """Level 2: HARD - Many enemies, limited power-ups, challenging platforming"""
    PROCEDURAL = True
    ROWS = 9
    COLS = 30
    N_LOWER = 5  # Limited platforms for harder navigation
    N_UPPER = 2  # Few upper platforms

    def get_princess_position(self) -> tuple[int, int]:
        cols = len(self.TILE_MAP[0])
        rows = len(self.TILE_MAP)
        return ((cols - 2) * TILE_SIZE, (rows - 2) * TILE_SIZE)

    def get_powerup_spawns(self, kinds):
        """Level 2 power-up spawns - limit stars to maximum 1"""
        # Count stars in the kinds list
        star_count = kinds.count("star")

        if star_count > 1:
            # Remove extra stars, keep only 1
            modified_kinds = []
            stars_added = 0
            for kind in kinds:
                if kind == "star" and stars_added >= 1:
                    # Replace extra stars with mushrooms
                    modified_kinds.append("mushroom")
                elif kind == "star":
                    stars_added += 1
                    modified_kinds.append(kind)
                else:
                    modified_kinds.append(kind)
            return super().get_powerup_spawns(modified_kinds)

        return super().get_powerup_spawns(kinds)

    def get_enemy_spawns(self):
        rows = len(self.TILE_MAP)
        ground_y = (rows - 2) * TILE_SIZE
        return [
            # Ground enemy near start - creates early pressure
            {
                "x": 5 * TILE_SIZE,
                "y": ground_y,
                "type": "ground",
                "patrol_left": 3 * TILE_SIZE,
                "patrol_right": 9 * TILE_SIZE,
            },
            # Flying enemy above first platform - attacks from above
            {
                "x": 8 * TILE_SIZE,
                "y": ground_y - 3 * TILE_SIZE,
                "type": "flying",
                "patrol_left": 6 * TILE_SIZE,
                "patrol_right": 12 * TILE_SIZE,
            },
            # Flophopper that mirrors player jumps
            {
                "x": 12 * TILE_SIZE,
                "y": ground_y,
                "type": "flophopper",
                "patrol_left": 10 * TILE_SIZE,
                "patrol_right": 16 * TILE_SIZE,
            },
            # Second flying enemy - increased air threat
            {
                "x": 15 * TILE_SIZE,
                "y": ground_y - 2 * TILE_SIZE,
                "type": "flying",
                "patrol_left": 13 * TILE_SIZE,
                "patrol_right": 19 * TILE_SIZE,
            },
            # Ground enemy in middle section
            {
                "x": 18 * TILE_SIZE,
                "y": ground_y,
                "type": "ground",
                "patrol_left": 16 * TILE_SIZE,
                "patrol_right": 22 * TILE_SIZE,
            },
            # High flying enemy - difficult to reach
            {
                "x": 21 * TILE_SIZE,
                "y": ground_y - 4 * TILE_SIZE,
                "type": "flying",
                "patrol_left": 19 * TILE_SIZE,
                "patrol_right": 25 * TILE_SIZE,
            },
            # Second flophopper - double the jump-mirroring trouble
            {
                "x": 24 * TILE_SIZE,
                "y": ground_y,
                "type": "flophopper",
                "patrol_left": 22 * TILE_SIZE,
                "patrol_right": 28 * TILE_SIZE,
            },
            # Final flying enemy guarding near princess area
            {
                "x": 27 * TILE_SIZE,
                "y": ground_y - 3 * TILE_SIZE,
                "type": "flying",
                "patrol_left": 25 * TILE_SIZE,
                "patrol_right": 30 * TILE_SIZE,
            },
        ]
