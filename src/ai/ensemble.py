import numpy as np
from config import (
    STRAT_COUNT,
    DT_WEIGHT,
    RNN_WEIGHT,
    ACTION_IDLE,
    ACTION_JUMP,
    STRAT_PATROL,
    STRAT_CHASE,
    STRAT_SPAWN_AERIAL,
    STRAT_AMBUSH,
    STRAT_RETREAT,
)
from src.ai.decision_tree import DecisionTreeAI
from src.ai.rnn_predictor import RNNPredictor

PLAYER_ACTION_TO_STRAT = {
    ACTION_IDLE: STRAT_PATROL,
    ACTION_JUMP: STRAT_SPAWN_AERIAL,
    2: STRAT_AMBUSH,
    3: STRAT_AMBUSH,
    4: STRAT_RETREAT,
}


class AIEnsemble:
    # Strategies that get amplified when challenge (aggressive) mode is on.
    AGGRESSIVE_STRATS = (STRAT_CHASE, STRAT_AMBUSH)
    AGGRESSION_BOOST = 1.5

    def __init__(self, level_width=5000, level_time=90.0):
        self.dt_ai = DecisionTreeAI()
        self.rnn = RNNPredictor()
        self._rnn_probs = np.ones(5, dtype=np.float32) / 5
        self._rnn_strat = np.zeros(STRAT_COUNT, dtype=np.float32)
        self.rnn_confidence = 0.0
        self.rnn_pred_action = ACTION_IDLE
        self.last_fused_probs = np.zeros(STRAT_COUNT, dtype=np.float32)
        self.last_command = STRAT_PATROL
        self.aggressive = False
        self._dt_examples = []

    def set_difficulty(self, challenge):
        """When challenge mode is on, enemies bias toward aggressive strategies."""
        self.aggressive = bool(challenge)

    def pre_frame(self, dt, action_history):
        """Call ONCE per frame. Shared values for all enemies."""
        self._rnn_probs = self.rnn.tick(dt, action_history)
        self.rnn_confidence = float(np.max(self._rnn_probs))
        self.rnn_pred_action = int(np.argmax(self._rnn_probs))
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
        """Call per enemy. Only runs DT — RNN already done in pre_frame."""
        feats = DecisionTreeAI.build_features(
            enemy_rect,
            player_rect,
            player_vel_x,
            jump_freq,
            run_freq,
            enemy_count,
            player_health,
        )
        dt_probs = self.dt_ai.predict_proba(feats)
        dt_conf = float(np.max(dt_probs))
        dt_weight = DT_WEIGHT * max(dt_conf, 0.1)
        rnn_weight = RNN_WEIGHT * max(self.rnn_confidence, 0.1)
        fused = dt_weight * dt_probs + rnn_weight * self._rnn_strat
        if self.aggressive:
            for s in self.AGGRESSIVE_STRATS:
                fused[s] *= self.AGGRESSION_BOOST
        fused /= fused.sum() + 1e-8
        command = int(np.argmax(fused))
        self.last_fused_probs = fused
        self.last_command = command
        self._dt_examples.append((feats, command))
        if len(self._dt_examples) > 2000:
            self._dt_examples = self._dt_examples[-2000:]
        return command

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
        }

    def learn_after_level(self, action_history):
        seqs = RNNPredictor.build_sequences(action_history, self.rnn.seq_len)
        self.rnn.fine_tune(seqs)
        self.dt_ai.update_from_examples(self._dt_examples)
        self._dt_examples.clear()

    def save_all(self):
        self.dt_ai.save()
        self.rnn.save()
