"""
Decision-tree AI layer for readable enemy behavior rules.

The tree starts from synthetic examples that encode the designer rules, then
re-fits after each level with real player-behavior examples collected by the
ensemble. This keeps enemy decisions explainable while adapting to how the
current player jumps, runs, retreats, or camps.
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
    """Wrap scikit-learn's DecisionTreeClassifier for strategy choices.

    Input features (7 values):
        [0] distance_x        - horizontal distance to player
        [1] distance_y        - vertical distance; negative means player is above
        [2] player_vel_x      - player horizontal velocity
        [3] jump_freq_10s     - jumps in the last 10 seconds
        [4] run_freq_10s      - run actions in the last 10 seconds
        [5] enemy_count       - active enemies
        [6] player_health     - player size level

    Output: enemy strategy id in [0, STRAT_COUNT).
    """

    FEATURE_COUNT = 7
    MAX_TRAINING_SAMPLES = 5000
    BASE_SAMPLES_KEEP = 1000

    def __init__(self):
        self.model = DecisionTreeClassifier(max_depth=6, random_state=42)
        self._is_trained = False
        self._base_X = None
        self._base_y = None
        self._prediction_history = []
        self._outcome_history = []
        self._bootstrap()
        self.load()

    def _bootstrap(self):
        """
        Create starting samples that map player patterns to enemy responses.
        """
        X, y = [], []

        # Jumping near enemies teaches aerial pressure
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

        # Close players should be chased
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

        # Fast runners get ambushed
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

        # Quiet distant players keep enemies patrolling
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

        # Crowded screens shift enemies into route blocking
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

        # Vulnerable players receive stronger chase pressure
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

        # Low enemy count can produce retreat behavior
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

    def predict(self, features: np.ndarray) -> int:
        """Return the single best strategy for the given features."""
        assert len(features) == self.FEATURE_COUNT, (
            f"Expected {self.FEATURE_COUNT} features, got {len(features)}"
        )
        pred = self.model.predict(features.reshape(1, -1))
        return int(pred[0])

    def predict_proba(self, features: np.ndarray) -> np.ndarray:
        """Return a probability distribution over all enemy strategies."""
        # Ensure model is loaded and valid
        if self.model is None:
            self.load()

        proba = self.model.predict_proba(features.reshape(1, -1))[0]
        # Keep output shape stable even if training omitted a class
        full = np.zeros(STRAT_COUNT, dtype=np.float32)
        for i, cls in enumerate(self.model.classes_):
            full[cls] = proba[i]
        return full

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
        dist_y = player_rect.centery - enemy_rect.centery  # negative means above
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

    def update_from_examples(self, examples: list[tuple[np.ndarray, int]], performance_weights=None):
        """Re-fit with baseline rules plus new player-specific examples."""
        if not examples:
            return

        X_new = np.array(
            [features for features, _ in examples], dtype=np.float32)
        y_new = np.array([label for _, label in examples], dtype=np.int32)

        # Apply performance weights if provided
        if performance_weights is not None:
            weights = np.array(performance_weights, dtype=np.float32)
            indices = np.random.choice(len(X_new), size=min(
                len(X_new), 2000), p=weights/weights.sum())
            X_new = X_new[indices]
            y_new = y_new[indices]

        # Keep only recent base samples + new examples
        if self._base_X is not None and self._base_y is not None:
            keep_indices = np.random.choice(len(self._base_X),
                                            size=min(
                                                self.BASE_SAMPLES_KEEP, len(self._base_X)),
                                            replace=False)
            X_base_trimmed = self._base_X[keep_indices]
            y_base_trimmed = self._base_y[keep_indices]
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
        self._base_X = combined_X
        self._base_y = combined_y

    def record_outcome(self, features, predicted_action, was_successful):
        """Record whether a prediction led to a successful outcome"""
        self._prediction_history.append(predicted_action)
        self._outcome_history.append(1 if was_successful else 0)

        if len(self._prediction_history) > 1000:
            self._prediction_history = self._prediction_history[-1000:]
            self._outcome_history = self._outcome_history[-1000:]

    def get_accuracy(self):
        """Return recent prediction accuracy"""
        if len(self._outcome_history) < 10:
            return 0.5
        return sum(self._outcome_history[-100:]) / min(100, len(self._outcome_history))

    def save(self):
        """Save the model and base data"""
        os.makedirs(os.path.dirname(DT_MODEL_PATH), exist_ok=True)
        with open(DT_MODEL_PATH, "wb") as f:
            pickle.dump((self.model, self._base_X, self._base_y), f)

    def load(self):
        """Load the model and base data from disk"""
        load_path = DT_MODEL_PATH
        if not os.path.exists(load_path):
            load_path = DT_BASELINE_MODEL_PATH

        if os.path.exists(load_path):
            try:
                with open(load_path, "rb") as f:
                    data = pickle.load(f)
                    if isinstance(data, tuple):
                        # Data is (model, base_X, base_y)
                        self.model, self._base_X, self._base_y = data
                    else:
                        # Old format - just the model
                        self.model = data
                        self._base_X = None
                        self._base_y = None
                    self._is_trained = True
                    print(f"Decision Tree loaded from {load_path}")
            except Exception as e:
                print(f"Warning: Could not load Decision Tree model: {e}")
                # If loading fails, ensure model is initialized
                if self.model is None:
                    self.model = DecisionTreeClassifier(
                        max_depth=6, random_state=42)
        else:
            print("No saved Decision Tree model found, using bootstrapped model")
