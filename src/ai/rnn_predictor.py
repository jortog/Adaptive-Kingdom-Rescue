# src/ai/rnn_predictor.py
"""
RNN (LSTM) Predictor
────────────────────
Architecture:
  Input  → Embedding(ACTION_COUNT, 16)
  LSTM   → 64 hidden units, 2 layers
  Dense  → 32 (ReLU)
  Output → Softmax over ACTION_COUNT (5 action classes)

Predicts the player's most likely next action.
Runs every 0.2 seconds; output is a probability vector fed to the ensemble.
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import os
from config import ACTION_COUNT, AI_ACTION_HISTORY_LEN, RNN_MODEL_PATH


class LSTMModel(nn.Module):
    def __init__(self, vocab_size: int = ACTION_COUNT,
                 embed_dim: int = 16,
                 hidden_size: int = 64,
                 num_layers: int = 2,
                 output_size: int = ACTION_COUNT):
        super().__init__()
        self.embedding   = nn.Embedding(vocab_size, embed_dim)
        self.lstm        = nn.LSTM(embed_dim, hidden_size,
                                   num_layers=num_layers, batch_first=True)
        self.fc1         = nn.Linear(hidden_size, 32)
        self.relu        = nn.ReLU()
        self.fc2         = nn.Linear(32, output_size)
        self.softmax     = nn.Softmax(dim=-1)

    def forward(self, x: torch.Tensor):
        # x: (batch, seq_len) — integer action indices
        embedded = self.embedding(x)             # (batch, seq_len, embed_dim)
        lstm_out, _ = self.lstm(embedded)        # (batch, seq_len, hidden)
        last_out = lstm_out[:, -1, :]            # take last time step
        out = self.relu(self.fc1(last_out))      # (batch, 32)
        logits = self.fc2(out)                   # (batch, ACTION_COUNT)
        return self.softmax(logits)              # (batch, ACTION_COUNT)


class RNNPredictor:
    """
    Wrapper around LSTMModel with:
      - predict()    → returns probability np.ndarray (ACTION_COUNT,)
      - fine_tune()  → online update on recent action sequences
      - save/load    → persist weights to disk
    """

    def __init__(self, seq_len: int = AI_ACTION_HISTORY_LEN):
        self.seq_len = seq_len
        self.device  = torch.device("cpu")   # CPU only for real-time inference
        self.model   = LSTMModel().to(self.device)
        self.optimizer = optim.Adam(self.model.parameters(), lr=1e-3)
        self.loss_fn   = nn.CrossEntropyLoss()

        # Inference timer
        self._timer           = 0.0
        self.INFERENCE_INTERVAL = 0.2   # seconds
        self._last_probs      = np.ones(ACTION_COUNT, dtype=np.float32) / ACTION_COUNT

        self.load()  # load saved weights if they exist

    # ── Predict (called from ensemble) ───────────────────────────────
    def predict(self, action_history: list) -> np.ndarray:
        """
        action_history: list of integers (last N actions, padded to seq_len)
        Returns: np.ndarray of shape (ACTION_COUNT,)
        """
        # Ensure correct length
        if len(action_history) < self.seq_len:
            action_history = [0] * (self.seq_len - len(action_history)) + list(action_history)
        action_history = action_history[-self.seq_len:]

        tensor = torch.tensor([action_history], dtype=torch.long, device=self.device)
        self.model.eval()
        with torch.no_grad():
            probs = self.model(tensor)  # (1, ACTION_COUNT)
        return probs[0].cpu().numpy()

    # ── Timer-gated update ────────────────────────────────────────────
    def tick(self, dt: float, action_history: list) -> np.ndarray:
        """
        Call this every frame. Returns cached prediction.
        Only re-runs inference every INFERENCE_INTERVAL seconds.
        """
        self._timer += dt
        if self._timer >= self.INFERENCE_INTERVAL:
            self._timer = 0.0
            self._last_probs = self.predict(action_history)
        return self._last_probs

    # ── Fine-tune on recent player sequences ─────────────────────────
    def fine_tune(self, action_sequences: list[list[int]]):
        """
        action_sequences: list of sequences. Each sequence is seq_len+1 actions.
        The first seq_len are inputs; the last is the target label.
        Called after each level to adapt to this specific player.
        """
        if not action_sequences:
            return

        self.model.train()
        for seq in action_sequences:
            if len(seq) < self.seq_len + 1:
                continue
            x = torch.tensor([seq[:self.seq_len]], dtype=torch.long, device=self.device)
            y = torch.tensor([seq[self.seq_len]], dtype=torch.long, device=self.device)

            self.optimizer.zero_grad()
            out    = self.model(x)               # (1, ACTION_COUNT)
            loss   = self.loss_fn(out, y)
            loss.backward()
            # Gradient clip to prevent catastrophic forgetting
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
            self.optimizer.step()

    # ── Build training sequences from game state buffer ───────────────
    @staticmethod
    def build_sequences(action_history: list, seq_len: int) -> list[list[int]]:
        seqs = []
        for i in range(len(action_history) - seq_len):
            seqs.append(action_history[i: i + seq_len + 1])
        return seqs

    # ── Persistence ──────────────────────────────────────────────────
    def save(self):
        os.makedirs(os.path.dirname(RNN_MODEL_PATH), exist_ok=True)
        torch.save(self.model.state_dict(), RNN_MODEL_PATH)

    def load(self):
        if os.path.exists(RNN_MODEL_PATH):
            try:
                state = torch.load(RNN_MODEL_PATH, map_location=self.device)
                self.model.load_state_dict(state)
            except Exception:
                pass  # Start fresh if model file is corrupted