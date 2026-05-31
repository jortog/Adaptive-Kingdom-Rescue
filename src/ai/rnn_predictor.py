"""
RNN (LSTM) Predictor
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
from collections import deque
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
        self.dropout = nn.Dropout(0.2)

    def forward(self, x: torch.Tensor):
        # x: (batch, seq_len) — integer action indices
        embedded = self.embedding(x)  # (batch, seq_len, embed_dim)
        embedded = self.dropout(embedded)
        lstm_out, _ = self.lstm(embedded)  # (batch, seq_len, hidden)
        last_out = lstm_out[:, -1, :]  # take last time step
        out = self.relu(self.fc1(last_out))  # (batch, 32)
        out = self.dropout(out)
        logits = self.fc2(out)  # (batch, ACTION_COUNT)
        return logits  # (batch, ACTION_COUNT)


class RNNPredictor:
    """
    Wrapper around LSTMModel with:
      - predict()    → returns probability np.ndarray (ACTION_COUNT,)
      - fine_tune()  → online update on recent action sequences
      - save/load    → persist weights to disk
    """

    def __init__(self, seq_len: int = AI_ACTION_HISTORY_LEN):
        self.seq_len = seq_len
        self.device = torch.device("cpu")  # CPU only for real-time inference
        self.model = LSTMModel().to(self.device)
        self.optimizer = optim.Adam(self.model.parameters(), lr=1e-3)
        self.loss_fn = nn.CrossEntropyLoss()

        # For tracking adaptation
        self.prediction_history = deque(maxlen=500)
        self.actual_history = deque(maxlen=500)
        self.accuracy_window = deque(maxlen=100)

        # Inference timer
        self._timer = 0.0
        self.INFERENCE_INTERVAL = 0.2  # seconds
        self._last_probs = np.ones(
            ACTION_COUNT, dtype=np.float32) / ACTION_COUNT

        self.load()  # load saved weights if they exist

    # Predict (called from ensemble)
    def predict(self, action_history: list) -> np.ndarray:
        """
        action_history: list of integers (last N actions, padded to seq_len)
        Returns: np.ndarray of shape (ACTION_COUNT,)
        """
        # Ensure correct length
        if len(action_history) < self.seq_len:
            action_history = [0] * (self.seq_len - len(action_history)) + list(
                action_history
            )
        action_history = action_history[-self.seq_len:]

        tensor = torch.tensor(
            [action_history], dtype=torch.long, device=self.device)
        self.model.eval()
        with torch.no_grad():
            logits = self.model(tensor)  # (1, ACTION_COUNT)
            probs = torch.softmax(logits, dim=-1)
        return probs[0].cpu().numpy()

    # Timer-gated update
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

    # Fine-tune on recent player sequences with batching
    def fine_tune(self, action_sequences: list[list[int]], epochs=3, batch_size=32):
        """
        action_sequences: list of sequences. Each sequence is seq_len+1 actions.
        The first seq_len are inputs; the last is the target label.
        Called after each level to adapt to this specific player.
        """
        if not action_sequences or len(action_sequences) < 10:
            return

        # Prepare data
        valid_sequences = []
        for seq in action_sequences:
            if len(seq) >= self.seq_len + 1:
                valid_sequences.append(seq)

        if not valid_sequences:
            return

        X = torch.tensor([seq[:self.seq_len] for seq in valid_sequences],
                         dtype=torch.long, device=self.device)
        y = torch.tensor([seq[self.seq_len] for seq in valid_sequences],
                         dtype=torch.long, device=self.device)

        self.model.train()

        # Multiple epochs for better learning
        for epoch in range(epochs):
            # Shuffle data
            indices = torch.randperm(len(X))
            X_shuffled = X[indices]
            y_shuffled = y[indices]

            # Batch processing
            for i in range(0, len(X_shuffled), batch_size):
                batch_X = X_shuffled[i:i+batch_size]
                batch_y = y_shuffled[i:i+batch_size]

                self.optimizer.zero_grad()
                out = self.model(batch_X)
                loss = self.loss_fn(out, batch_y)
                loss.backward()
                # Gradient clip to prevent catastrophic forgetting
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                self.optimizer.step()

        # Small learning rate decay for stability
        for param_group in self.optimizer.param_groups:
            param_group['lr'] = max(1e-5, param_group['lr'] * 0.95)

    def record_prediction_accuracy(self, predicted_action, actual_action):
        """Track prediction accuracy for ensemble weight adaptation"""
        self.prediction_history.append(predicted_action)
        self.actual_history.append(actual_action)
        is_correct = 1 if predicted_action == actual_action else 0
        self.accuracy_window.append(is_correct)

    def get_accuracy(self):
        """Return recent prediction accuracy (last 100 predictions)"""
        if len(self.accuracy_window) < 10:
            return 0.5
        return sum(self.accuracy_window) / len(self.accuracy_window)

    # Build training sequences from game state buffer
    @staticmethod
    def build_sequences(action_history: list, seq_len: int) -> list[list[int]]:
        seqs = []
        for i in range(len(action_history) - seq_len):
            seqs.append(action_history[i: i + seq_len + 1])
        return seqs

    # Persistence
    def save(self):
        os.makedirs(os.path.dirname(RNN_MODEL_PATH), exist_ok=True)
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
        }, RNN_MODEL_PATH)

    def load(self):
        """Load the RNN model from disk"""
        load_path = RNN_MODEL_PATH
        if not os.path.exists(load_path):
            load_path = RNN_BASELINE_MODEL_PATH
        if os.path.exists(load_path):
            try:
                checkpoint = torch.load(load_path, map_location=self.device)
                # Handle both old and new save formats
                if isinstance(checkpoint, dict):
                    if 'model_state_dict' in checkpoint:
                        self.model.load_state_dict(
                            checkpoint['model_state_dict'])
                        if 'optimizer_state_dict' in checkpoint and hasattr(self, 'optimizer'):
                            try:
                                self.optimizer.load_state_dict(
                                    checkpoint['optimizer_state_dict'])
                            except:
                                pass  # Optimizer state might not match, that's fine
                    else:
                        # Old format - just the state dict
                        self.model.load_state_dict(checkpoint)
                else:
                    # Very old format
                    self.model.load_state_dict(checkpoint)
                print("RNN model loaded successfully")
            except Exception as e:
                print(f"Warning: Could not load RNN model: {e}")
                print("Starting with fresh RNN model")
                # Initialize fresh model instead of failing
                self.model = LSTMModel().to(self.device)
                self.optimizer = torch.optim.Adam(
                    self.model.parameters(), lr=1e-3)
