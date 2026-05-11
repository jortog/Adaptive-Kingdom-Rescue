# src/systems/scoring.py
"""
Scoring system with AI-driven dynamic adjustments.
All modifiers are explained in config.py comments and the proposal Section 2.2.B.
"""

import time
from config import (
    SCORE_DEFEAT_ENEMY, SCORE_DEFEAT_JUMP_BONUS,
    SCORE_MUSHROOM, SCORE_FLOWER, SCORE_STAR, SCORE_SHIELD,
    SCORE_CHECKPOINT, SCORE_LEVEL_COMPLETE, SCORE_TIME_BONUS_RATE,
    SCORE_NO_DAMAGE_BONUS, SCORE_VARIETY_BONUS, SCORE_EXTRA_LIFE_THRESHOLD,
    ACTION_JUMP
)


class ScoringSystem:
    def __init__(self, game_state):
        self.gs = game_state
        self.score = 0
        self._kill_streak: dict[str, int] = {}
        self._powerup_recent: dict[str, list] = {}
        self._checkpoint_route_bonus_active = True

    def award_enemy_defeat(self, enemy_type: str, was_airborne: bool) -> int:
        streak = self._kill_streak.get(enemy_type, 0) + 1
        self._kill_streak[enemy_type] = streak

        pts = SCORE_DEFEAT_ENEMY
        if was_airborne:
            pts += SCORE_DEFEAT_JUMP_BONUS

        # AI adjustment: diminishing returns after 5 same-type kills
        if streak > 5:
            reduction = min(0.5, 0.1 * (streak - 5))
            pts = int(pts * (1.0 - reduction))

        pts = max(pts, SCORE_DEFEAT_ENEMY // 2)
        self._add(pts)
        return pts

    def award_powerup(self, kind: str) -> int:
        base_map = {
            "mushroom": SCORE_MUSHROOM, "flower": SCORE_FLOWER,
            "star": SCORE_STAR, "shield": SCORE_SHIELD,
        }
        pts = base_map.get(kind, 0)

        # AI adjustment: same power-up 3× in 30s = 0 points
        now = time.time()
        times = self._powerup_recent.get(kind, [])
        times = [t for t in times if now - t < 30]
        times.append(now)
        self._powerup_recent[kind] = times
        if len(times) >= 3:
            pts = 0

        self._add(pts)
        return pts

    def award_checkpoint(self, route: str = "middle") -> int:
        pts = SCORE_CHECKPOINT
        # AI adjustment: repeated route = 50% reduction + 100 alt bonus
        if route in self.gs.route_history[-5:] and \
           self.gs.route_history.count(route) >= 3:
            pts = pts // 2
        else:
            pts += 100  # exploration bonus
        self.gs.route_history.append(route)
        self._add(pts)
        return pts

    def award_level_complete(self, time_remaining: float,
                              took_no_damage: bool) -> int:
        pts = SCORE_LEVEL_COMPLETE
        pts += max(0, int(time_remaining * SCORE_TIME_BONUS_RATE))
        if took_no_damage:
            pts += SCORE_NO_DAMAGE_BONUS
        # Variety bonus
        unique = self.gs.unique_actions_last_10s()
        pts += min(unique * SCORE_VARIETY_BONUS, 200)
        self._add(pts)
        return pts

    def _add(self, pts: int):
        self.score += pts
        self.gs.score = self.score
        # Extra life threshold
        threshold = SCORE_EXTRA_LIFE_THRESHOLD
        while self.score >= threshold and self.gs.lives < 9:
            self.gs.lives += 1
            threshold += SCORE_EXTRA_LIFE_THRESHOLD