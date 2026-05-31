"""LSTM predictor for the player's next action.

It reads the recent action history, predicts the next move, and sends that
probability vector to the ensemble. After each level, it fine-tunes on the
latest player sequences so enemies learn habits such as repeated jumping,
running, idling, or route camping.
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import os
from config import (
    ACTION_COUNT,
    AI_ACTION_HISTORY_LEN,
    RNN_BASELINE_MODEL_PATH,
    RNN_MODEL_PATH,
)


class LSTMModel(nn.Module):
    def __init__(
        self,
        vocab_size: int = ACTION_COUNT,
        embed_dim: int = 16,
        hidden_size: int = 64,
        num_layers: int = 2,
        output_size: int = ACTION_COUNT,
    ):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.lstm = nn.LSTM(
            embed_dim, hidden_size, num_layers=num_layers, batch_first=True
        )
        self.fc1 = nn.Linear(hidden_size, 32)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(32, output_size)

    def forward(self, x: torch.Tensor):
        # Shape notes are kept because this layer is easy to wire incorrectly
        embedded = self.embedding(x)  # (batch, seq_len, embed_dim)
        lstm_out, _ = self.lstm(embedded)  # (batch, seq_len, hidden)
        last_out = lstm_out[:, -1, :]
        out = self.relu(self.fc1(last_out))  # (batch, 32)
        return self.fc2(out)  # (batch, ACTION_COUNT)


class RNNPredictor:
    """Runs prediction, fine-tuning, and persistence for the LSTM."""

    def __init__(self, seq_len: int = AI_ACTION_HISTORY_LEN):
        self.seq_len = seq_len
        self.device = torch.device("cpu")  # CPU keeps real-time inference portable
        self.model = LSTMModel().to(self.device)
        self.optimizer = optim.Adam(self.model.parameters(), lr=1e-3)
        self.loss_fn = nn.CrossEntropyLoss()

        # Cache predictions to avoid running the LSTM every frame
        self._timer = 0.0
        self.INFERENCE_INTERVAL = 0.2
        self._last_probs = np.ones(ACTION_COUNT, dtype=np.float32) / ACTION_COUNT

        self.load()

    def predict(self, action_history: list) -> np.ndarray:
        """Predict the player's next action from recent action ids."""
        # Pad short histories so the LSTM always receives seq_len actions
        if len(action_history) < self.seq_len:
            action_history = [0] * (self.seq_len - len(action_history)) + list(
                action_history
            )
        action_history = action_history[-self.seq_len :]

        tensor = torch.tensor([action_history], dtype=torch.long, device=self.device)
        self.model.eval()
        with torch.no_grad():
            logits = self.model(tensor)
            probs = torch.softmax(logits, dim=-1)
        return probs[0].cpu().numpy()

    def tick(self, dt: float, action_history: list) -> np.ndarray:
        """Return cached prediction, refreshing on a short timer."""
        self._timer += dt
        if self._timer >= self.INFERENCE_INTERVAL:
            self._timer = 0.0
            self._last_probs = self.predict(action_history)
        return self._last_probs

    def fine_tune(self, action_sequences: list[list[int]]):
        """Fine-tune on recent player sequences after a level ends."""
        if not action_sequences:
            return

        self.model.train()
        for seq in action_sequences:
            if len(seq) < self.seq_len + 1:
                continue
            x = torch.tensor(
                [seq[: self.seq_len]], dtype=torch.long, device=self.device
            )
            y = torch.tensor([seq[self.seq_len]], dtype=torch.long, device=self.device)

            self.optimizer.zero_grad()
            out = self.model(x)
            loss = self.loss_fn(out, y)
            loss.backward()
            # Clip updates so new habits do not erase the baseline behavior
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
            self.optimizer.step()

    @staticmethod
    def build_sequences(action_history: list, seq_len: int) -> list[list[int]]:
        """Build sliding windows: seq_len inputs plus the next-action label."""
        seqs = []
        for i in range(len(action_history) - seq_len):
            seqs.append(action_history[i : i + seq_len + 1])
        return seqs

    def save(self):
        os.makedirs(os.path.dirname(RNN_MODEL_PATH), exist_ok=True)
        torch.save(self.model.state_dict(), RNN_MODEL_PATH)

    def load(self):
        load_path = RNN_MODEL_PATH
        if not os.path.exists(load_path):
            load_path = RNN_BASELINE_MODEL_PATH
        if os.path.exists(load_path):
            try:
                state = torch.load(load_path, map_location=self.device)
                self.model.load_state_dict(state)
            except Exception:
                pass  # Corrupt model files fall back to fresh weights
