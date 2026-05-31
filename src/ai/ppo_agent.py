"""
PPO reinforcement learning agent.

The game feeds normalized state transitions into a small Gymnasium-compatible
environment wrapper. Stable-Baselines3 PPO consumes those transitions during
periodic updates and returns one of the strategic enemy commands.

State space (8 floats, normalized [0, 1]):
  [0] level_timer_norm        - time elapsed / time limit
  [1] player_lives_norm       - lives / max_lives
  [2] enemy_count_norm        - enemies alive / max_enemies
  [3] dist_to_princess_norm   - player distance to princess / level_width
  [4] jump_freq_norm          - jumps in recent window / 30
  [5] run_freq_norm           - runs in recent window / 30
  [6] player_speed_norm       - abs(player vel_x) / max_speed
  [7] player_route_norm       - player vertical route / level height
"""

import os

import gymnasium as gym
import numpy as np
from gymnasium import spaces
from stable_baselines3 import PPO as SB3PPO

from config import (
    PLAYER_DASH_SPEED,
    PLAYER_MAX_LIVES,
    PPO_BASELINE_MODEL_PATH,
    PPO_MODEL_PATH,
    PPO_UPDATE_INTERVAL,
    STRAT_COUNT,
)


STATE_DIM = 8
MAX_BUFFERED_TRANSITIONS = 2048


class KingdomRescueEnv(gym.Env):
    """Minimal environment shell backed by game-provided transitions."""

    metadata = {"render_modes": []}

    def __init__(self):
        super().__init__()
        self.observation_space = spaces.Box(
            low=0.0, high=1.0, shape=(STATE_DIM,), dtype=np.float32
        )
        self.action_space = spaces.Discrete(STRAT_COUNT)

        self._current_obs = np.zeros(STATE_DIM, dtype=np.float32)
        self._transitions = []

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        return self._current_obs, {}

    def step(self, action):
        if self._transitions:
            obs, reward, done = self._transitions.pop(0)
            self._current_obs = obs
        else:
            obs = self._current_obs
            reward = 0.0
            done = False
        return obs, reward, done, False, {}

    def set_state(self, obs: np.ndarray):
        self._current_obs = obs.astype(np.float32)

    def add_transition(self, next_obs: np.ndarray, reward: float, done: bool):
        self._transitions.append(
            (next_obs.astype(np.float32), float(reward), bool(done))
        )
        if len(self._transitions) > MAX_BUFFERED_TRANSITIONS:
            self._transitions = self._transitions[-MAX_BUFFERED_TRANSITIONS:]


class PPOAgent:
    """Small wrapper around Stable-Baselines3 PPO."""

    def __init__(
        self,
        level_width: int = 5000,
        level_time: float = 90.0,
        max_enemies: int = 10,
    ):
        self.level_width = level_width
        self.level_time = level_time
        self.max_enemies = max_enemies

        self.env = KingdomRescueEnv()

        self.model = self._load_or_create_model()

        self._step_buffer: list[tuple] = []
        self._last_action = 0
        self._has_action = False
        self._update_timer = 0.0

    def build_state(
        self,
        level_timer: float,
        player_lives: int,
        enemy_count: int,
        dist_to_princess: float,
        jump_freq: int,
        run_freq: int,
        player_vel_x: float,
        player_route_y: float,
        level_height: float | None = None,
    ) -> np.ndarray:
        if level_height is None:
            route_norm = player_route_y - 1
        else:
            route_norm = player_route_y / max(level_height, 1)
        return np.array(
            [
                min(level_timer / max(self.level_time, 1), 1.0),
                min(max(player_lives / PLAYER_MAX_LIVES, 0.0), 1.0),
                min(enemy_count / max(self.max_enemies, 1), 1.0),
                min(dist_to_princess / max(self.level_width, 1), 1.0),
                min(jump_freq / 30.0, 1.0),
                min(run_freq / 30.0, 1.0),
                min(abs(player_vel_x) / PLAYER_DASH_SPEED, 1.0),
                min(max(route_norm, 0.0), 1.0),
            ],
            dtype=np.float32,
        )

    def get_action(self, state: np.ndarray) -> int:
        state = np.clip(np.asarray(state, dtype=np.float32), 0.0, 1.0)
        self.env.set_state(state)
        action, _ = self.model.predict(state, deterministic=False)
        self._last_action = int(np.asarray(action).item())
        self._has_action = True
        return self._last_action

    def observe(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool,
    ):
        self._step_buffer.append((state, int(action), reward, next_state, done))
        if len(self._step_buffer) > MAX_BUFFERED_TRANSITIONS:
            self._step_buffer = self._step_buffer[-MAX_BUFFERED_TRANSITIONS:]
        self.env.set_state(state)
        self.env.add_transition(next_state, reward, done)

    def tick(self, dt: float, state: np.ndarray) -> int:
        self.env.set_state(state)
        if not self._has_action:
            return self.get_action(state)

        self._update_timer += dt
        if self._update_timer >= PPO_UPDATE_INTERVAL:
            self._update_timer = 0.0
            self._learn_from_buffer()
            return self.get_action(state)
        return self._last_action

    def save(self):
        self._learn_from_buffer()
        os.makedirs(os.path.dirname(PPO_MODEL_PATH), exist_ok=True)
        self.model.save(PPO_MODEL_PATH)

    def load(self):
        self.model = self._load_or_create_model()

    def _load_or_create_model(self):
        for load_path in (PPO_MODEL_PATH, PPO_BASELINE_MODEL_PATH):
            if os.path.exists(load_path):
                try:
                    return SB3PPO.load(load_path, env=self.env)
                except Exception:
                    pass
        return self._create_model()

    def _create_model(self):
        return SB3PPO(
            "MlpPolicy",
            self.env,
            verbose=0,
            learning_rate=3e-4,
            n_steps=256,
            batch_size=64,
            clip_range=0.2,
            gamma=0.99,
            ent_coef=0.01,
            policy_kwargs=dict(net_arch=[128, 128]),
        )

    def _learn_from_buffer(self):
        if not self._step_buffer:
            return
        try:
            self.model.learn(total_timesteps=64, reset_num_timesteps=False)
            self._step_buffer.clear()
        except Exception:
            pass
