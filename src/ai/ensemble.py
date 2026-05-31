import numpy as np
from config import (
    STRAT_COUNT,
    DT_WEIGHT,
    RNN_WEIGHT,
    PPO_WEIGHT,
    ACTION_IDLE,
    ACTION_JUMP,
    STRAT_PATROL,
    STRAT_SPAWN_AERIAL,
    STRAT_AMBUSH,
    STRAT_RETREAT,
)
from src.ai.decision_tree import DecisionTreeAI
from src.ai.rnn_predictor import RNNPredictor
from src.ai.ppo_agent import PPOAgent

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
        self.last_fused_probs = np.zeros(STRAT_COUNT, dtype=np.float32)
        self._dt_examples = []

    def pre_frame(self, dt, action_history, ppo_state):
        """Call ONCE per frame. Shared values for all enemies."""
        self._rnn_probs = self.rnn.tick(dt, action_history)
        self._ppo_action = self.ppo.tick(dt, ppo_state)
        self.rnn_confidence = float(np.max(self._rnn_probs))
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
        """Call per enemy. Only runs DT — RNN/PPO already done in pre_frame."""
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
        ppo_weight = PPO_WEIGHT
        fused = (
            dt_weight * dt_probs
            + rnn_weight * self._rnn_strat
            + ppo_weight * self._ppo_strat
        )
        fused /= fused.sum() + 1e-8
        command = int(np.argmax(fused))
        self.last_fused_probs = fused
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

    @staticmethod
    def _one_hot(idx, size):
        v = np.zeros(size, dtype=np.float32)
        if 0 <= idx < size:
            v[idx] = 1.0
        return v

    def learn_after_level(self, action_history):
        seqs = RNNPredictor.build_sequences(action_history, self.rnn.seq_len)
        self.rnn.fine_tune(seqs)
        self.dt_ai.update_from_examples(self._dt_examples)
        self._dt_examples.clear()

    def save_all(self):
        self.dt_ai.save()
        self.rnn.save()
        self.ppo.save()
