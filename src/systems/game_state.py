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
        self.level_time_elapsed = 0.0
        self.damage_taken_this_level = 0
        # Long-term action log used by the RNN to learn player habits
        self.action_history = deque(maxlen=AI_ACTION_BUFFER_LEN)
        # Recent-window counts feed DT/PPO features such as jump/run frequency
        self.action_freq_window = []
        self.action_freq_timestamps = []

    def reset_level(self):
        self.level_time_elapsed = 0.0
        self.damage_taken_this_level = 0
        self.action_freq_window.clear()
        self.action_freq_timestamps.clear()

    def record_action(self, action_index: int):
        """Record one player action for AI prediction and pattern counts."""
        self.action_history.append(action_index)
        now = time.time()
        self.action_freq_window.append(action_index)
        self.action_freq_timestamps.append(now)
        cutoff = now - 10.0
        while self.action_freq_timestamps and self.action_freq_timestamps[0] < cutoff:
            self.action_freq_timestamps.pop(0)
            self.action_freq_window.pop(0)

    def get_action_history_padded(self) -> list:
        """Return fixed-length action history for the RNN."""
        hist = list(self.action_history)[-AI_ACTION_HISTORY_LEN:]
        pad_len = AI_ACTION_HISTORY_LEN - len(hist)
        return [0] * pad_len + hist

    def count_recent_action(self, action_index: int) -> int:
        """Count one action type in the current 10-second feature window."""
        return self.action_freq_window.count(action_index)

    def unique_actions_last_10s(self) -> int:
        return len(set(self.action_freq_window))
