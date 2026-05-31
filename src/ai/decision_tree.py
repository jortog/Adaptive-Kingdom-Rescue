"""
Decision Tree AI Layer
Uses scikit-learn's DecisionTreeClassifier wrapped with hand-crafted
training examples that encode the 50 designer rules described in the proposal.
"""

import numpy as np
import pickle
import os
from sklearn.tree import DecisionTreeClassifier
from config import (
    STRAT_PATROL,
    STRAT_CHASE,
    STRAT_SPAWN_AERIAL,
    STRAT_BLOCK_UPPER,
    STRAT_AMBUSH,
    STRAT_RETREAT,
    STRAT_COUNT,
    DT_MODEL_PATH,
    DT_BASELINE_MODEL_PATH,
)


class DecisionTreeAI:
    """
    Wraps a scikit-learn DecisionTreeClassifier.

    Input features (7 values):
        [0] distance_x          — horizontal pixel distance to player
        [1] distance_y          — vertical pixel distance to player (neg = player above)
        [2] player_vel_x        — player horizontal velocity (px/s)
        [3] jump_freq_10s       — number of jumps in last 10 seconds
        [4] run_freq_10s        — number of run actions in last 10 seconds
        [5] enemy_count         — active enemies on screen
        [6] player_health       — player size_level (1 or 2)

    Output: integer in [0, STRAT_COUNT)
    """

    FEATURE_COUNT = 7
    MAX_TRAINING_SAMPLES = 5000
    BASE_SAMPLES_KEEP = 1000

    def __init__(self):
        self.model = DecisionTreeClassifier(max_depth=6, random_state=42)
        self._is_trained = False
        self._base_X = None
        self._base_y = None
        self._bootstrap()
        self.load()
        self._prediction_history = []  # Track prediction accuracy
        self._outcome_history = []     # Track actual outcomes

    # Bootstrap with synthetic rule-encoding data
    def _bootstrap(self):
        """
        Encode the designer's 50 rules as synthetic training samples.
        Each sample is one scenario → intended action pair.
        """
        X, y = [], []

        # Rule: close + player jumping → spawn aerial
        for _ in range(80):
            X.append(
                [
                    np.random.uniform(0, 150),
                    np.random.uniform(-200, 50),
                    np.random.uniform(-300, 300),
                    np.random.randint(3, 10),
                    np.random.randint(0, 5),
                    np.random.randint(1, 6),
                    1,
                ]
            )
            y.append(STRAT_SPAWN_AERIAL)

        # Rule: very close → chase
        for _ in range(100):
            X.append(
                [
                    np.random.uniform(0, 80),
                    np.random.uniform(-100, 100),
                    np.random.uniform(-100, 100),
                    np.random.randint(0, 3),
                    np.random.randint(0, 3),
                    np.random.randint(1, 4),
                    1,
                ]
            )
            y.append(STRAT_CHASE)

        # Rule: fast-running player → ambush
        for _ in range(80):
            X.append(
                [
                    np.random.uniform(100, 400),
                    np.random.uniform(-100, 100),
                    np.random.uniform(200, 400),
                    np.random.randint(0, 2),
                    np.random.randint(5, 15),
                    np.random.randint(1, 6),
                    1,
                ]
            )
            y.append(STRAT_AMBUSH)

        # Rule: far + player not moving much → patrol
        for _ in range(100):
            X.append(
                [
                    np.random.uniform(300, 800),
                    np.random.uniform(-50, 50),
                    np.random.uniform(-50, 50),
                    np.random.randint(0, 2),
                    np.random.randint(0, 2),
                    np.random.randint(1, 8),
                    1,
                ]
            )
            y.append(STRAT_PATROL)

        # Rule: many enemies alive → block upper path
        for _ in range(60):
            X.append(
                [
                    np.random.uniform(100, 500),
                    np.random.uniform(-300, -100),
                    np.random.uniform(100, 300),
                    np.random.randint(4, 15),
                    np.random.randint(0, 5),
                    np.random.randint(4, 8),
                    1,
                ]
            )
            y.append(STRAT_BLOCK_UPPER)

        # Rule: player low health → aggressive chase
        for _ in range(60):
            X.append(
                [
                    np.random.uniform(50, 250),
                    np.random.uniform(-100, 100),
                    np.random.uniform(-200, 200),
                    np.random.randint(0, 5),
                    np.random.randint(0, 5),
                    np.random.randint(1, 6),
                    1,
                ]
            )
            y.append(STRAT_CHASE)

        # Rule: enemy outnumbered → retreat
        for _ in range(40):
            X.append(
                [
                    np.random.uniform(200, 500),
                    np.random.uniform(-100, 100),
                    np.random.uniform(-300, 300),
                    np.random.randint(0, 5),
                    np.random.randint(0, 5),
                    1,
                    2,
                ]
            )
            y.append(STRAT_RETREAT)

        X = np.array(X, dtype=np.float32)
        y = np.array(y, dtype=np.int32)
        self._base_X = X
        self._base_y = y
        self.model.fit(X, y)
        self._is_trained = True

    # Predict
    def predict(self, features: np.ndarray) -> int:
        """
        features: 1D numpy array of shape (FEATURE_COUNT,)
        Returns: integer action index
        """
        assert len(features) == self.FEATURE_COUNT, (
            f"Expected {self.FEATURE_COUNT} features, got {len(features)}"
        )
        pred = self.model.predict(features.reshape(1, -1))
        return int(pred[0])

    def predict_proba(self, features: np.ndarray) -> np.ndarray:
        """
        Returns probability distribution over STRAT_COUNT actions.
        Shape: (STRAT_COUNT,)
        """
        proba = self.model.predict_proba(features.reshape(1, -1))[0]
        # Pad to STRAT_COUNT if some classes were missing in training
        full = np.zeros(STRAT_COUNT, dtype=np.float32)
        for i, cls in enumerate(self.model.classes_):
            full[cls] = proba[i]
        return full

    # Build feature vector from game state
    @staticmethod
    def build_features(
        enemy_rect,
        player_rect,
        player_vel_x: float,
        jump_freq: int,
        run_freq: int,
        enemy_count: int,
        player_health: int,
    ) -> np.ndarray:
        dist_x = abs(player_rect.centerx - enemy_rect.centerx)
        dist_y = player_rect.centery - enemy_rect.centery  # neg = player above
        return np.array(
            [
                dist_x,
                dist_y,
                player_vel_x,
                jump_freq,
                run_freq,
                enemy_count,
                player_health,
            ],
            dtype=np.float32,
        )

    # Persistence with improved training
    def update_from_examples(self, examples: list[tuple[np.ndarray, int]], performance_weights=None):
        """
        Update the decision tree with new examples.
        Args:
            examples: List of (features, outcome) pairs
            performance_weights: Optional weights for each example based on success
        """
        if not examples:
            return

        X_new = np.array(
            [features for features, _ in examples], dtype=np.float32)
        y_new = np.array([label for _, label in examples], dtype=np.int32)

        # Apply performance weights if provided
        if performance_weights is not None:
            weights = np.array(performance_weights, dtype=np.float32)
            # Weighted sampling for training
            indices = np.random.choice(len(X_new), size=min(
                len(X_new), 2000), p=weights/weights.sum())
            X_new = X_new[indices]
            y_new = y_new[indices]

        # Keep only recent base samples + new examples to prevent unlimited growth
        if self._base_X is not None and self._base_y is not None:
            # Keep last BASE_SAMPLES_KEEP from base
            keep_indices = np.random.choice(len(self._base_X),
                                            size=min(
                                                self.BASE_SAMPLES_KEEP, len(self._base_X)),
                                            replace=False)
            X_base_trimmed = self._base_X[keep_indices]
            y_base_trimmed = self._base_y[keep_indices]

            # Combine base (limited) with new samples
            combined_X = np.vstack([X_base_trimmed, X_new])
            combined_y = np.concatenate([y_base_trimmed, y_new])
        else:
            combined_X = X_new
            combined_y = y_new

        # Limit total samples
        if len(combined_X) > self.MAX_TRAINING_SAMPLES:
            indices = np.random.choice(
                len(combined_X), self.MAX_TRAINING_SAMPLES, replace=False)
            combined_X = combined_X[indices]
            combined_y = combined_y[indices]

        # Retrain model
        self.model.fit(combined_X, combined_y)
        self._is_trained = True

        # Store trimmed base for next update
        self._base_X = combined_X
        self._base_y = combined_y

    def record_outcome(self, features, predicted_action, was_successful):
        """Record whether a prediction led to a successful outcome"""
        self._prediction_history.append(predicted_action)
        self._outcome_history.append(1 if was_successful else 0)

        # Keep only last 1000 outcomes
        if len(self._prediction_history) > 1000:
            self._prediction_history = self._prediction_history[-1000:]
            self._outcome_history = self._outcome_history[-1000:]

    def get_accuracy(self):
        """Return recent prediction accuracy"""
        if len(self._outcome_history) < 10:
            return 0.5
        return sum(self._outcome_history[-100:]) / min(100, len(self._outcome_history))

    def save(self):
        os.makedirs(os.path.dirname(DT_MODEL_PATH), exist_ok=True)
        with open(DT_MODEL_PATH, "wb") as f:
            pickle.dump((self.model, self._base_X, self._base_y), f)

    def load(self):
        load_path = DT_MODEL_PATH
        if not os.path.exists(load_path):
            load_path = DT_BASELINE_MODEL_PATH
        if os.path.exists(load_path):
            with open(load_path, "rb") as f:
                data = pickle.load(f)
                if isinstance(data, tuple):
                    self.model, self._base_X, self._base_y = data
                else:
                    self.model = data
            self._is_trained = True
