import json
import os

import numpy as np
from config import (
    STRAT_COUNT,
    DT_WEIGHT,
    RNN_WEIGHT,
    PPO_WEIGHT,
    ACTION_IDLE,
    ACTION_JUMP,
    STRAT_PATROL,
    STRAT_CHASE,
    STRAT_SPAWN_AERIAL,
    STRAT_AMBUSH,
    STRAT_RETREAT,
    DIFFICULTY_LEVEL_BASE,
    DIFFICULTY_WARMUP_TIME,
    DIFFICULTY_TRIES_FULL,
    DIFFICULTY_PROGRESS_MAX,
    PROGRESS_PATH,
)
from src.ai.decision_tree import DecisionTreeAI
from src.ai.ppo_agent import PPOAgent
from src.ai.rnn_predictor import RNNPredictor

# Pressure strategies share an aggression budget so adaptation feels smart, not unfair
PRESSURE_STRATS = (STRAT_CHASE, STRAT_AMBUSH, STRAT_SPAWN_AERIAL)

PLAYER_ACTION_TO_STRAT = {
    ACTION_IDLE: STRAT_PATROL,
    ACTION_JUMP: STRAT_SPAWN_AERIAL,
    2: STRAT_AMBUSH,
    3: STRAT_AMBUSH,
    4: STRAT_RETREAT,
}


class AIEnsemble:
    def __init__(self, level_width=5000, level_time=90.0):
        self.dt_ai = DecisionTreeAI()
        self.rnn = RNNPredictor()
        self.ppo = PPOAgent(level_width=level_width, level_time=level_time)
        self._rnn_probs = np.ones(5, dtype=np.float32) / 5
        self._ppo_action = STRAT_PATROL
        self._ppo_strat = np.zeros(STRAT_COUNT, dtype=np.float32)
        self._rnn_strat = np.zeros(STRAT_COUNT, dtype=np.float32)
        self.rnn_confidence = 0.0
        self.rnn_pred_action = ACTION_IDLE
        self.last_fused_probs = np.zeros(STRAT_COUNT, dtype=np.float32)
        self.last_command = STRAT_PATROL
        self._dt_examples = []
        # Persisted attempts let the AI increase pressure across retries/sessions
        self.tries = self._load_tries()
        # Frame-level AI state shared by all enemies
        self._difficulty = 0.5
        self._aggro_budget = 1
        # 0..1 anti-camping signal for high-platform players
        self._aerial_bias = 0.0

    def compute_difficulty(self, level_index, level_elapsed):
        """Return 0..1 pressure from level, warmup time, and player attempts."""
        idx = max(0, min(int(level_index), len(DIFFICULTY_LEVEL_BASE) - 1))
        base = DIFFICULTY_LEVEL_BASE[idx]
        progress = min(self.tries / DIFFICULTY_TRIES_FULL, 1.0)
        warm = 0.4 + 0.6 * min(level_elapsed / DIFFICULTY_WARMUP_TIME, 1.0)
        d = (base + progress * DIFFICULTY_PROGRESS_MAX) * warm
        return max(0.0, min(d, 1.0))

    def register_attempt(self):
        """Count one level attempt for adaptive difficulty."""
        self.tries += 1

    def difficulty_progress(self):
        """Return progress toward max retry-based difficulty."""
        return min(self.tries / DIFFICULTY_TRIES_FULL, 1.0)

    def pre_frame(self, dt, action_history, ppo_state, difficulty=0.5, aerial_bias=0.0):
        """Update shared AI predictions once per frame before enemies query commands."""
        self._difficulty = max(0.0, min(difficulty, 1.0))
        self._aerial_bias = max(0.0, min(aerial_bias, 1.0))
        # More learned pressure allows more attackers, capped to prevent swarms
        self._aggro_budget = 1 + int(self._difficulty * 2 + 1e-6)
        self._rnn_probs = self.rnn.tick(dt, action_history)
        self._ppo_action = self.ppo.tick(dt, ppo_state)
        self.rnn_confidence = float(np.max(self._rnn_probs))
        self.rnn_pred_action = int(np.argmax(self._rnn_probs))
        self._ppo_strat = self._one_hot(self._ppo_action, STRAT_COUNT)
        self._rnn_strat = self._rnn_to_strat(self._rnn_probs)

    def get_command(
        self,
        enemy_rect,
        player_rect,
        player_vel_x,
        jump_freq,
        run_freq,
        enemy_count,
        player_health,
    ):
        """Fuse DT, RNN, and PPO decisions into one enemy command."""
        feats = DecisionTreeAI.build_features(
            enemy_rect,
            player_rect,
            player_vel_x,
            jump_freq,
            run_freq,
            enemy_count,
            player_health,
        )
        d = self._difficulty
        dt_probs = self.dt_ai.predict_proba(feats)
        dt_conf = float(np.max(dt_probs))
        dt_weight = DT_WEIGHT * max(dt_conf, 0.1)
        rnn_weight = RNN_WEIGHT * max(self.rnn_confidence, 0.1)
        # PPO gains influence as retries teach the AI which pressure works
        ppo_weight = PPO_WEIGHT * (0.2 + 0.8 * d)
        fused = (
            dt_weight * dt_probs
            + rnn_weight * self._rnn_strat
            + ppo_weight * self._ppo_strat
        )
        # Difficulty shapes fused votes before the aggression budget is applied
        aggro_scale = 0.6 + 0.8 * d
        for s in PRESSURE_STRATS:
            fused[s] *= aggro_scale
        fused[STRAT_PATROL] *= 1.0 + 0.5 * (1.0 - d)
        # Anti-camping bias converts repeated high-platform play into flyers and chasers
        if self._aerial_bias > 0:
            fused[STRAT_SPAWN_AERIAL] += 0.8 * self._aerial_bias
            fused[STRAT_CHASE] += 0.3 * self._aerial_bias
        fused /= fused.sum() + 1e-8
        intended = int(np.argmax(fused))
        self.last_fused_probs = fused
        # Store intended responses so the DT learns the player's behavior trend
        self._dt_examples.append((feats, intended))
        if len(self._dt_examples) > 2000:
            self._dt_examples = self._dt_examples[-2000:]
        # Throttle pressure so learned behavior stays playable
        command = intended
        if intended in PRESSURE_STRATS:
            if self._aggro_budget > 0:
                self._aggro_budget -= 1
            else:
                command = STRAT_PATROL
        self.last_command = command
        return command

    def _rnn_to_strat(self, rnn_probs):
        strat = np.zeros(STRAT_COUNT, dtype=np.float32)
        for idx, prob in enumerate(rnn_probs):
            s = PLAYER_ACTION_TO_STRAT.get(idx, STRAT_PATROL)
            strat[s] += prob
        return strat

    @staticmethod
    def _one_hot(idx, size):
        v = np.zeros(size, dtype=np.float32)
        if 0 <= idx < size:
            v[idx] = 1.0
        return v

    def debug_snapshot(self):
        """Read-only AI state for the demo overlay / console log."""
        return {
            "rnn_pred_action": self.rnn_pred_action,
            "rnn_confidence": self.rnn_confidence,
            "ppo_action": self._ppo_action,
            "command": self.last_command,
        }

    def learn_after_level(self, action_history):
        seqs = RNNPredictor.build_sequences(action_history, self.rnn.seq_len)
        self.rnn.fine_tune(seqs)
        self.dt_ai.update_from_examples(self._dt_examples)
        self._dt_examples.clear()

    def save_all(self):
        self.dt_ai.save()
        self.rnn.save()
        self.ppo.save()
        self._save_tries()

    def _load_tries(self):
        try:
            if os.path.exists(PROGRESS_PATH):
                with open(PROGRESS_PATH) as f:
                    return max(0, int(json.load(f).get("tries", 0)))
        except Exception:
            pass
        return 0

    def _save_tries(self):
        try:
            os.makedirs(os.path.dirname(PROGRESS_PATH), exist_ok=True)
            with open(PROGRESS_PATH, "w") as f:
                json.dump({"tries": self.tries}, f)
        except Exception:
            pass
