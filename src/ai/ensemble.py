import json
import os
import numpy as np
from config import (
    STRAT_COUNT,
    DT_WEIGHT,
    RNN_WEIGHT,
    ACTION_IDLE,
    ACTION_JUMP,
    ACTION_RUN,
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
from src.ai.rnn_predictor import RNNPredictor

# Strategies that actively close in on the player
PRESSURE_STRATS = (STRAT_CHASE, STRAT_AMBUSH, STRAT_SPAWN_AERIAL)

PLAYER_ACTION_TO_STRAT = {
    ACTION_IDLE: STRAT_PATROL,
    ACTION_JUMP: STRAT_SPAWN_AERIAL,
    ACTION_RUN: STRAT_AMBUSH,
}


class AIEnsemble:
    def __init__(self, level_width=5000, level_time=90.0):
        self.dt_ai = DecisionTreeAI()
        self.rnn = RNNPredictor()

        # Adaptive weights
        self.dt_weight = DT_WEIGHT
        self.rnn_weight = RNN_WEIGHT
        self.min_weight = 0.2
        self.max_weight = 2.0

        self._rnn_probs = np.ones(5, dtype=np.float32) / 5
        self._rnn_strat = np.zeros(STRAT_COUNT, dtype=np.float32)
        self.rnn_confidence = 0.0
        self.rnn_pred_action = ACTION_IDLE
        self.last_fused_probs = np.zeros(STRAT_COUNT, dtype=np.float32)
        self.last_command = STRAT_PATROL
        self._dt_examples = []
        self._dt_outcomes = []  # Track success/failure of predictions

        # Track actual game outcomes
        self._enemy_hit_player = False
        self._player_hit_enemy = False
        self._enemy_damage_dealt = 0
        self._frame_predictions = []  # Store (features, command) per frame

        # Number of tries (attempts) the player has made
        self.tries = self._load_tries()
        self._difficulty = 0.5
        self._aggro_budget = 1

    def compute_difficulty(self, level_index, level_elapsed):
        """0..1 pressure scalar"""
        idx = max(0, min(int(level_index), len(DIFFICULTY_LEVEL_BASE) - 1))
        base = DIFFICULTY_LEVEL_BASE[idx]
        progress = min(self.tries / DIFFICULTY_TRIES_FULL, 1.0)
        warm = 0.4 + 0.6 * min(level_elapsed / DIFFICULTY_WARMUP_TIME, 1.0)
        d = (base + progress * DIFFICULTY_PROGRESS_MAX) * warm
        return max(0.0, min(d, 1.0))

    def register_attempt(self):
        """Count one try (a level attempt)."""
        self.tries += 1

    def pre_frame(self, dt, action_history, difficulty=0.5):
        """Call ONCE per frame. Shared values for all enemies."""
        self._difficulty = max(0.0, min(difficulty, 1.0))
        self._aggro_budget = 1 + int(self._difficulty * 2 + 1e-6)
        self._rnn_probs = self.rnn.tick(dt, action_history)
        self.rnn_confidence = float(np.max(self._rnn_probs))
        self.rnn_pred_action = int(np.argmax(self._rnn_probs))
        self._rnn_strat = self._rnn_to_strat(self._rnn_probs)

        # Reset frame tracking
        self._enemy_hit_player = False
        self._player_hit_enemy = False

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
        """Call per enemy."""
        feats = DecisionTreeAI.build_features(
            enemy_rect,
            player_rect,
            player_vel_x,
            jump_freq,
            run_freq,
            enemy_count,
            player_health,
        )

        # Get predictions with adaptive weights
        dt_probs = self.dt_ai.predict_proba(feats)
        dt_conf = float(np.max(dt_probs))

        # Calculate dynamic weights based on recent performance
        dt_accuracy = self.dt_ai.get_accuracy()
        rnn_accuracy = self.rnn.get_accuracy()

        # Adjust weights based on accuracy
        total_accuracy = dt_accuracy + rnn_accuracy + 0.001
        adaptive_dt_weight = self.dt_weight * (dt_accuracy / total_accuracy)
        adaptive_rnn_weight = self.rnn_weight * (rnn_accuracy / total_accuracy)

        # Clamp weights
        adaptive_dt_weight = max(self.min_weight, min(
            self.max_weight, adaptive_dt_weight))
        adaptive_rnn_weight = max(self.min_weight, min(
            self.max_weight, adaptive_rnn_weight))

        # Fuse predictions
        fused = adaptive_dt_weight * dt_probs + adaptive_rnn_weight * self._rnn_strat

        # Difficulty shaping
        d = self._difficulty
        aggro_scale = 0.6 + 0.8 * d
        for s in PRESSURE_STRATS:
            fused[s] *= aggro_scale
        fused[STRAT_PATROL] *= 1.0 + 0.5 * (1.0 - d)
        fused /= fused.sum() + 1e-8

        intended = int(np.argmax(fused))
        self.last_fused_probs = fused

        # Store for later learning (with features)
        self._frame_predictions.append((feats, intended, enemy_rect.copy()))

        # Throttle aggression
        command = intended
        if intended in PRESSURE_STRATS:
            if self._aggro_budget > 0:
                self._aggro_budget -= 1
            else:
                command = STRAT_PATROL

        self.last_command = command
        return command

    def record_enemy_outcome(self, enemy_rect, player_rect, enemy_hit_player, player_hit_enemy):
        """Record whether an enemy's action was successful"""
        self._enemy_hit_player = self._enemy_hit_player or enemy_hit_player
        self._player_hit_enemy = self._player_hit_enemy or player_hit_enemy

        if enemy_hit_player:
            self._enemy_damage_dealt += 1

    def _process_frame_outcomes(self):
        """Evaluate success of AI decisions after each frame"""
        if not self._frame_predictions:
            return

        # Determine if the decisions were successful
        # Success = enemy hit player OR enemy avoided being hit
        was_successful = self._enemy_hit_player or not self._player_hit_enemy

        for features, command, _ in self._frame_predictions:
            # Store for learning (use actual outcome, not prediction)
            self._dt_examples.append((features, command))
            self._dt_outcomes.append(1 if was_successful else 0)

            # Record for RNN accuracy tracking
            self.rnn.record_prediction_accuracy(self.rnn_pred_action,
                                                self._get_actual_player_action())

        # Clear frame predictions
        self._frame_predictions = []

    def _get_actual_player_action(self):
        """Determine the actual player action from game state"""
        # This should be implemented to get the actual action the player took
        # For now, return a default
        return ACTION_IDLE

    def _rnn_to_strat(self, rnn_probs):
        strat = np.zeros(STRAT_COUNT, dtype=np.float32)
        for idx, prob in enumerate(rnn_probs):
            s = PLAYER_ACTION_TO_STRAT.get(idx, STRAT_PATROL)
            strat[s] += prob
        return strat

    def debug_snapshot(self):
        """Read-only AI state for the demo overlay / console log."""
        return {
            "rnn_pred_action": self.rnn_pred_action,
            "rnn_confidence": self.rnn_confidence,
            "command": self.last_command,
            "dt_weight": self.dt_weight,
            "rnn_weight": self.rnn_weight,
        }

    def learn_after_level(self, action_history):
        """Called after level completion to update AI based on actual outcomes"""
        # Process outcomes from the level
        self._process_frame_outcomes()

        # Train RNN on player action sequences
        if len(action_history) > self.rnn.seq_len:
            seqs = RNNPredictor.build_sequences(
                action_history, self.rnn.seq_len)
            self.rnn.fine_tune(seqs, epochs=2)

        # Train Decision Tree with weighted examples based on success
        if self._dt_examples and len(self._dt_examples) > 10:
            # Use outcomes as weights for training (successful examples weighted more)
            self.dt_ai.update_from_examples(
                self._dt_examples, self._dt_outcomes)

        # Update ensemble weights based on performance
        dt_acc = self.dt_ai.get_accuracy()
        rnn_acc = self.rnn.get_accuracy()

        # Gradually adjust weights (slow adaptation)
        self.dt_weight = 0.95 * self.dt_weight + 0.05 * (dt_acc * 2.0)
        self.rnn_weight = 0.95 * self.rnn_weight + 0.05 * (rnn_acc * 2.0)

        # Normalize weights to keep total reasonable
        total = self.dt_weight + self.rnn_weight
        self.dt_weight = self.dt_weight / total * (DT_WEIGHT + RNN_WEIGHT)
        self.rnn_weight = self.rnn_weight / total * (DT_WEIGHT + RNN_WEIGHT)

        # Clear training data for next level
        self._dt_examples.clear()
        self._dt_outcomes.clear()
        self._frame_predictions.clear()
        self._enemy_damage_dealt = 0

    def save_all(self):
        self.dt_ai.save()
        self.rnn.save()
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
