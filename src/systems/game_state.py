from config import PLAYER_START_LIVES, AI_ACTION_HISTORY_LEN, AI_ACTION_BUFFER_LEN
from collections import deque
import time


class GameState:
    def __init__(self):
        self.reset_session()

    def reset_session(self):
        self.lives = PLAYER_START_LIVES
        self.score = 0
        self.level_index = 0
        self.total_attempts = 0
        self.challenge_mode = False
        self.level_time_elapsed = 0.0
        self.checkpoints_reached = set()
        self.damage_taken_this_level = 0
        self.player_deaths_this_level = 0
        self.action_history = deque(maxlen=AI_ACTION_BUFFER_LEN)
        self.action_freq_window = []
        self.action_freq_timestamps = []
        self.ppo_experience_buffer = []
        self.enemy_kill_streak = {}
        self.powerup_collect_recent = {}
        self.route_history = []

    def reset_level(self):
        self.level_time_elapsed = 0.0
        self.checkpoints_reached = set()
        self.damage_taken_this_level = 0
        self.player_deaths_this_level = 0
        self.action_freq_window.clear()
        self.action_freq_timestamps.clear()
        self.enemy_kill_streak.clear()
        self.powerup_collect_recent.clear()

    def record_action(self, action_index: int):
        self.action_history.append(action_index)
        now = time.time()
        self.action_freq_window.append(action_index)
        self.action_freq_timestamps.append(now)
        cutoff = now - 10.0
        while self.action_freq_timestamps and self.action_freq_timestamps[0] < cutoff:
            self.action_freq_timestamps.pop(0)
            self.action_freq_window.pop(0)

    def get_action_history_padded(self) -> list:
        hist = list(self.action_history)[-AI_ACTION_HISTORY_LEN:]
        pad_len = AI_ACTION_HISTORY_LEN - len(hist)
        return [0] * pad_len + hist

    def count_recent_action(self, action_index: int) -> int:
        return self.action_freq_window.count(action_index)

    def unique_actions_last_10s(self) -> int:
        return len(set(self.action_freq_window))

    def add_ppo_experience(self, state, action, reward, next_state, done):
        self.ppo_experience_buffer.append((state, action, reward, next_state, done))
        if len(self.ppo_experience_buffer) > 5000:
            self.ppo_experience_buffer = self.ppo_experience_buffer[-5000:]

    def flush_ppo_buffer(self):
        buf = list(self.ppo_experience_buffer)
        self.ppo_experience_buffer.clear()
        return buf
