from config import (
    SCORE_DEFEAT_ENEMY, SCORE_AIRBORNE_DEFEAT_BONUS,
    SCORE_MUSHROOM, SCORE_FLOWER, SCORE_STAR, SCORE_SHIELD,
    SCORE_CHECKPOINT, SCORE_LEVEL_COMPLETE,
    SCORE_TIME_BONUS_RATE, SCORE_NO_DAMAGE_BONUS,
    SCORE_VARIETY_BONUS, SCORE_EXTRA_LIFE_THRESHOLD
)


class ScoringSystem:
    """
    Stateless wrapper — tracks score directly on game_state so it persists
    across level/death respawns. No internal duplicate self.score.
    """
    def __init__(self, gs):
        self.gs = gs
        # Initialize counters that track diminishing returns / variety only
        self._enemy_kill_streak = {}

    def award_enemy_defeat(self, enemy_type: str, was_airborne: bool) -> int:
        pts = SCORE_DEFEAT_ENEMY
        if was_airborne:
            pts += SCORE_AIRBORNE_DEFEAT_BONUS
        # Diminishing returns
        n = self._enemy_kill_streak.get(enemy_type, 0)
        if n >= 5:
            factor = max(0.5, 1.0 - (n - 4) * 0.10)
            pts = int(pts * factor)
        self._enemy_kill_streak[enemy_type] = n + 1
        self._add(pts)
        return pts

    def award_powerup(self, kind: str) -> int:
        pts = 0
        if kind == "mushroom": pts = SCORE_MUSHROOM
        elif kind == "flower": pts = SCORE_FLOWER
        elif kind == "star":   pts = SCORE_STAR
        elif kind == "shield": pts = SCORE_SHIELD
        self._add(pts)
        return pts

    def award_checkpoint(self) -> int:
        self._add(SCORE_CHECKPOINT)
        return SCORE_CHECKPOINT

    def award_level_complete(self, time_remaining: float,
                              took_no_damage: bool) -> int:
        pts = SCORE_LEVEL_COMPLETE
        pts += max(0, int(time_remaining * SCORE_TIME_BONUS_RATE))
        if took_no_damage:
            pts += SCORE_NO_DAMAGE_BONUS
        unique = self.gs.unique_actions_last_10s()
        pts += min(unique * SCORE_VARIETY_BONUS, 200)
        self._add(pts)
        return pts

    def _add(self, pts: int):
        self.gs.score += pts
        threshold = SCORE_EXTRA_LIFE_THRESHOLD
        while self.gs.score >= threshold and self.gs.lives < 9:
            self.gs.lives += 1
            threshold += SCORE_EXTRA_LIFE_THRESHOLD
