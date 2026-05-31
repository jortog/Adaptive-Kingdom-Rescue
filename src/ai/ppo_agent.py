import os
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import PPO as SB3PPO
from config import (
    STRAT_COUNT, STRAT_PATROL,
    PPO_LEARNING_RATE, PPO_GAMMA, PPO_CLIP_RANGE,
    DATA_DIR
)


class KingdomRescueEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, state_dim=8):
        super().__init__()
        self.state_dim = state_dim
        self.action_space = spaces.Discrete(STRAT_COUNT)
        self.observation_space = spaces.Box(low=-1.0, high=1.0, shape=(state_dim,), dtype=np.float32)
        self._state = np.zeros(state_dim, dtype=np.float32)
        self._last_reward = 0.0

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self._state = np.zeros(self.state_dim, dtype=np.float32)
        return self._state, {}

    def step(self, action):
        return self._state, self._last_reward, False, False, {}

    def set_state(self, state):
        self._state = state.astype(np.float32)

    def set_reward(self, reward):
        self._last_reward = float(reward)


class PPOAgent:
    def __init__(self, level_width=5000, level_time=90.0):
        self.level_width = level_width
        self.level_time = level_time
        self.env = KingdomRescueEnv(state_dim=8)
        self._update_timer = 0.0
        self._last_action = STRAT_PATROL
        self.model_path = os.path.join(DATA_DIR, "models", "ppo_agent.zip")
        if os.path.exists(self.model_path):
            try:
                self.model = SB3PPO.load(self.model_path, env=self.env)
            except Exception:
                self.model = self._new_model()
        else:
            self.model = self._new_model()

    def _new_model(self):
        return SB3PPO("MlpPolicy", self.env, learning_rate=PPO_LEARNING_RATE,
                      n_steps=256, batch_size=64, gamma=PPO_GAMMA,
                      clip_range=PPO_CLIP_RANGE, verbose=0)

    def build_state(self, time_elapsed, lives, n_enemies, dist_to_princess,
                    jump_freq, run_freq, player_vx, player_size):
        return np.array([
            time_elapsed / max(self.level_time, 1.0),
            lives / 9.0,
            n_enemies / 10.0,
            dist_to_princess / max(self.level_width, 1.0),
            min(jump_freq, 10) / 10.0,
            min(run_freq, 10) / 10.0,
            np.clip(player_vx / 600.0, -1.0, 1.0),
            (player_size - 1) / 2.0,
        ], dtype=np.float32)

    def get_action(self, state):
        action, _ = self.model.predict(state, deterministic=False)
        self._last_action = int(action)
        self.env.set_state(state)
        return self._last_action

    def tick(self, dt, state):
        self._update_timer += dt
        if self._update_timer >= 10.0:
            self._update_timer = 0.0
            return self.get_action(state)
        return self._last_action

    def reward_prevention(self):
        self.env.set_reward(self.env._last_reward + 1.0 / 60.0)

    def penalty_fast_death(self):
        self.env.set_reward(self.env._last_reward - 0.5)

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            self.model.save(self.model_path)
        except Exception:
            pass
