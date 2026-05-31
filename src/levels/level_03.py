from src.levels.level_base import LevelBase
from config import TILE_SIZE


class Level03(LevelBase):
    """Level 3: NIGHTMARE - Maximum enemies, NO star power-ups, minimal platforms"""
    PROCEDURAL = True
    ROWS = 9
    COLS = 28
    N_LOWER = 2  # Almost no platforms - very dangerous
    N_UPPER = 0  # No upper platforms at all

    def get_princess_position(self) -> tuple[int, int]:
        cols = len(self.TILE_MAP[0])
        rows = len(self.TILE_MAP)
        return ((cols - 2) * TILE_SIZE, (rows - 2) * TILE_SIZE)

    def get_powerup_spawns(self, kinds):
        """Override to remove star power-ups from Level 3"""
        # Only spawn mushrooms and shields, NO stars
        modified_kinds = [k for k in kinds if k != "star"]
        return super().get_powerup_spawns(modified_kinds)

    def get_enemy_spawns(self):
        rows = len(self.TILE_MAP)
        ground_y = (rows - 2) * TILE_SIZE
        return [
            # Early pressure - ground enemy right at start
            {
                "x": 3 * TILE_SIZE,
                "y": ground_y,
                "type": "ground",
                "patrol_left": 2 * TILE_SIZE,
                "patrol_right": 7 * TILE_SIZE,
            },
            # Flying enemy above start
            {
                "x": 5 * TILE_SIZE,
                "y": ground_y - 3 * TILE_SIZE,
                "type": "flying",
                "patrol_left": 3 * TILE_SIZE,
                "patrol_right": 9 * TILE_SIZE,
            },
            # Flophopper - mirrors your jumps
            {
                "x": 8 * TILE_SIZE,
                "y": ground_y,
                "type": "flophopper",
                "patrol_left": 6 * TILE_SIZE,
                "patrol_right": 12 * TILE_SIZE,
            },
            # Second flying enemy
            {
                "x": 10 * TILE_SIZE,
                "y": ground_y - 2 * TILE_SIZE,
                "type": "flying",
                "patrol_left": 8 * TILE_SIZE,
                "patrol_right": 14 * TILE_SIZE,
            },
            # Ground enemy in middle
            {
                "x": 13 * TILE_SIZE,
                "y": ground_y,
                "type": "ground",
                "patrol_left": 11 * TILE_SIZE,
                "patrol_right": 17 * TILE_SIZE,
            },
            # High flying enemy
            {
                "x": 15 * TILE_SIZE,
                "y": ground_y - 4 * TILE_SIZE,
                "type": "flying",
                "patrol_left": 13 * TILE_SIZE,
                "patrol_right": 19 * TILE_SIZE,
            },
            # Second flophopper
            {
                "x": 18 * TILE_SIZE,
                "y": ground_y,
                "type": "flophopper",
                "patrol_left": 16 * TILE_SIZE,
                "patrol_right": 22 * TILE_SIZE,
            },
            # Flying enemy near princess
            {
                "x": 21 * TILE_SIZE,
                "y": ground_y - 3 * TILE_SIZE,
                "type": "flying",
                "patrol_left": 19 * TILE_SIZE,
                "patrol_right": 25 * TILE_SIZE,
            },
            # Final ground enemy guarding princess
            {
                "x": 24 * TILE_SIZE,
                "y": ground_y,
                "type": "ground",
                "patrol_left": 22 * TILE_SIZE,
                "patrol_right": 27 * TILE_SIZE,
            },
            # Extra flying enemy for chaos
            {
                "x": 26 * TILE_SIZE,
                "y": ground_y - 2 * TILE_SIZE,
                "type": "flying",
                "patrol_left": 24 * TILE_SIZE,
                "patrol_right": 28 * TILE_SIZE,
            },
        ]
