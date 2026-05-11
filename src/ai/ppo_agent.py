# src/ai/ppo_agent.py
"""
PPO Reinforcement Learning Agent
─────────────────────────────────
Uses Stable-Baselines3's PPO implementation.
The "environment" is a lightweight Gymnasium-compatible wrapper
that the game feeds state/reward into after each PPO update interval.

State space (8 floats, normalized [0,1]):
  [0] level_timer_norm        — time elapsed / time limit
  [1] player_lives_norm       — lives / max_lives
  [2] enemy_count_norm        — enemies alive / max_enemies
  [3] dist_to_princess_norm   — player dist to princess / level_width
  [4] jump_freq_norm          — jumps in last 30s / 30
  [5] run_freq_norm           — runs in last 30s / 30
  [6] player_speed_norm       — |player vel_x| / max_speed
  [7] player_health_norm      — player size_level / 2

Action space: Discrete(STRAT_COUNT) = 7 strategic commands
"""

import numpy as np
import os
import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import PPO as SB3PPO
from stable_baselines3.common.env_util import make_vec_env
from config import STRAT_COUNT, PPO_MODEL_PATH, PLAYER_MAX_LIVES, PLAYER_DASH_SPEED


STATE_DIM = 8


class KingdomRescueEnv(gym.Env):
    """
    Minimal Gymnasium environment shell.
    The actual game fills in state and reward from outside.
    """

    metadata = {"render_modes": []}

    def __init__(self):
        super().__init__()
        self.observation_space = spaces.Box(
            low=0.0, high=1.0, shape=(STATE_DIM,), dtype=np.float32
        )
        self.action_space = spaces.Discrete(STRAT_COUNT)

        self._current_obs    = np.zeros(STATE_DIM, dtype=np.float32)
        self._pending_reward = 0.0
        self._done           = False

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self._current_obs    = np.zeros(STATE_DIM, dtype=np.float32)
        self._pending_reward = 0.0
        self._done           = False
        return self._current_obs, {}

    def step(self, action):
        obs     = self._current_obs
        reward  = self._pending_reward
        done    = self._done
        self._pending_reward = 0.0
        return obs, reward, done, False, {}

    def set_state(self, obs: np.ndarray):
        self._current_obs = obs.astype(np.float32)

    def give_reward(self, reward: float):
        self._pending_reward += reward

    def set_done(self, done: bool):
        self._done = done

    def render(self):
        pass


class PPOAgent:
    """
    Wraps SB3 PPO. Provides:
      - get_action(state) → int
      - give_reward(r)
      - update()         → trains on accumulated steps
      - save/load
    """

    def __init__(self, level_width: int = 5000, level_time: float = 90.0,
                 max_enemies: int = 10):
        self.level_width  = level_width
        self.level_time   = level_time
        self.max_enemies  = max_enemies

        self.env = KingdomRescueEnv()

        if os.path.exists(PPO_MODEL_PATH):
            self.model = SB3PPO.load(PPO_MODEL_PATH, env=self.env)
        else:
            self.model = SB3PPO(
                "MlpPolicy",
                self.env,
                verbose=0,
                learning_rate=3e-4,
                n_steps=256,
                batch_size=64,
                clip_range=0.2,
                gamma=0.99,
                ent_coef=0.01,      # encourage exploration
                policy_kwargs=dict(net_arch=[128, 128])
            )

        # Buffer for collecting experience between updates
        self._step_buffer: list[tuple] = []
        self._last_obs     = np.zeros(STATE_DIM, dtype=np.float32)
        self._last_action  = 0
        self._update_timer = 0.0

    # ── Build normalized state vector ────────────────────────────────
    def build_state(self, level_timer: float, player_lives: int,
                    enemy_count: int, dist_to_princess: float,
                    jump_freq: int, run_freq: int,
                    player_vel_x: float, player_health: int) -> np.ndarray:
        return np.array([
            min(level_timer / max(self.level_time, 1), 1.0),
            player_lives / PLAYER_MAX_LIVES,
            min(enemy_count / max(self.max_enemies, 1), 1.0),
            min(dist_to_princess / max(self.level_width, 1), 1.0),
            min(jump_freq / 30.0, 1.0),
            min(run_freq / 30.0, 1.0),
            min(abs(player_vel_x) / PLAYER_DASH_SPEED, 1.0),
            (player_health - 1) / 1.0,
        ], dtype=np.float32)

    # ── Get action (inference) ────────────────────────────────────────
    def get_action(self, state: np.ndarray) -> int:
        self.env.set_state(state)
        action, _ = self.model.predict(state, deterministic=False)
        self._last_obs    = state
        self._last_action = int(action)
        return self._last_action

    # ── Reward signals (called from game systems) ─────────────────────
    def reward_prevention(self):
        """+1 for each second player hasn't reached princess."""
        self.env.give_reward(1.0)

    def penalty_fast_death(self):
        """-0.5 if player dies within 5 seconds of level start."""
        self.env.give_reward(-0.5)

    def reward_variety(self):
        """+0.2 for each unique enemy formation used in last 10s."""
        self.env.give_reward(0.2)

    # ── Periodic update (call every PPO_UPDATE_INTERVAL seconds) ─────
    def tick(self, dt: float, state: np.ndarray) -> int:
        """
        Returns a strategic action every PPO_UPDATE_INTERVAL seconds.
        Between intervals, returns the last decided action.
        """
        self._update_timer += dt
        if self._update_timer >= 10.0:
            self._update_timer = 0.0
            # Trigger one learning step using SB3's collect_rollouts internals
            # We approximate by calling learn(total_timesteps=1)
            try:
                self.model.learn(total_timesteps=64, reset_num_timesteps=False)
            except Exception:
                pass
            return self.get_action(state)
        return self._last_action

    # ── Persistence ──────────────────────────────────────────────────
    def save(self):
        os.makedirs(os.path.dirname(PPO_MODEL_PATH), exist_ok=True)
        self.model.save(PPO_MODEL_PATH)

    def load(self):
        if os.path.exists(PPO_MODEL_PATH):
            self.model = SB3PPO.load(PPO_MODEL_PATH, env=self.env)