# src/ai/ensemble.py
"""
AI Ensemble — Weighted Fusion
──────────────────────────────
Combines:
  Decision Tree  → probability vector (one-hot or predict_proba)
  RNN            → probability vector (softmax output)
  PPO            → one-hot of chosen strategic action

Fusion weights: DT=0.3, RNN=0.3, PPO=0.4
Final action = argmax of weighted sum.
"""

import numpy as np
from config import (
    STRAT_COUNT, DT_WEIGHT, RNN_WEIGHT, PPO_WEIGHT,
    ACTION_COUNT, ACTION_IDLE, ACTION_JUMP,
    STRAT_PATROL, STRAT_CHASE, STRAT_SPAWN_AERIAL,
    STRAT_AMBUSH, STRAT_RETREAT, STRAT_BLOCK_UPPER, STRAT_BLOCK_LOWER
)
from src.ai.decision_tree import DecisionTreeAI
from src.ai.rnn_predictor import RNNPredictor
from src.ai.ppo_agent import PPOAgent


# Map player action predictions → enemy strategic response
# When RNN predicts player will JUMP → spawn aerial blockers, etc.
PLAYER_ACTION_TO_STRAT = {
    ACTION_IDLE:   STRAT_PATROL,
    ACTION_JUMP:   STRAT_SPAWN_AERIAL,
    2:             STRAT_AMBUSH,    # RUN → ambush
    3:             STRAT_AMBUSH,    # DASH → ambush
    4:             STRAT_RETREAT,   # ATTACK → retreat first
}


class AIEnsemble:
    """
    The master AI controller. One instance per game session.
    """

    def __init__(self, level_width: int = 5000, level_time: float = 90.0):
        self.dt_ai  = DecisionTreeAI()
        self.rnn    = RNNPredictor()
        self.ppo    = PPOAgent(level_width=level_width, level_time=level_time)

        self._rnn_probs    = np.ones(ACTION_COUNT, dtype=np.float32) / ACTION_COUNT
        self._ppo_action   = STRAT_PATROL
        self._dt_probs     = np.zeros(STRAT_COUNT, dtype=np.float32)

        # Confidence tracking (exposed to HUD)
        self.rnn_confidence = 0.0    # 0=random, 1=very confident

    # ── Main decision call (per enemy, per frame) ─────────────────────
    def decide(self,
               enemy_rect, player_rect,
               player_vel_x: float,
               jump_freq: int, run_freq: int,
               enemy_count: int, player_health: int,
               action_history: list,
               dt: float,
               ppo_state: np.ndarray) -> int:
        """
        Returns final strategic action integer for this enemy.
        """

        # 1. Decision Tree → probability over STRAT_COUNT
        dt_features = DecisionTreeAI.build_features(
            enemy_rect, player_rect, player_vel_x,
            jump_freq, run_freq, enemy_count, player_health
        )
        self._dt_probs = self.dt_ai.predict_proba(dt_features)

        # 2. RNN → probability over ACTION_COUNT (player actions)
        #    Convert to STRAT_COUNT by mapping player actions to enemy strategies
        self._rnn_probs = self.rnn.tick(dt, action_history)
        rnn_strat_probs = self._rnn_to_strat(self._rnn_probs)

        # 3. PPO → one-hot over STRAT_COUNT
        self._ppo_action = self.ppo.tick(dt, ppo_state)
        ppo_strat_probs  = self._one_hot(self._ppo_action, STRAT_COUNT)

        # 4. Weighted fusion
        fused = (DT_WEIGHT  * self._dt_probs
               + RNN_WEIGHT * rnn_strat_probs
               + PPO_WEIGHT * ppo_strat_probs)

        fused /= fused.sum() + 1e-8   # normalize

        # 5. RNN confidence (entropy-based)
        self.rnn_confidence = float(np.max(self._rnn_probs))

        return int(np.argmax(fused))

    # ── Helper: map RNN player-action probs → enemy strategy probs ────
    def _rnn_to_strat(self, rnn_probs: np.ndarray) -> np.ndarray:
        strat = np.zeros(STRAT_COUNT, dtype=np.float32)
        for action_idx, prob in enumerate(rnn_probs):
            s = PLAYER_ACTION_TO_STRAT.get(action_idx, STRAT_PATROL)
            strat[s] += prob
        return strat

    # ── Helper: one-hot encode ────────────────────────────────────────
    @staticmethod
    def _one_hot(idx: int, size: int) -> np.ndarray:
        v = np.zeros(size, dtype=np.float32)
        if 0 <= idx < size:
            v[idx] = 1.0
        return v

    # ── Post-level learning ───────────────────────────────────────────
    def learn_after_level(self, action_history: list):
        """Call once after each level completion or game over."""
        # Fine-tune RNN on player sequences
        seqs = RNNPredictor.build_sequences(action_history, self.rnn.seq_len)
        self.rnn.fine_tune(seqs)
        # PPO learning is handled inside ppo.tick() automatically

    # ── Save all models ───────────────────────────────────────────────
    def save_all(self):
        self.dt_ai.save()
        self.rnn.save()
        self.ppo.save()