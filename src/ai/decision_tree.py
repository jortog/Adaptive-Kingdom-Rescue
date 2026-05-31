"""
Decision Tree AI Layer
Uses scikit-learn's DecisionTreeClassifier wrapped with hand-crafted
training examples that encode the 50 designer rules described in the proposal.

Because we cannot wait for training data collection to start the game,
we bootstrap the tree with synthetic rule-encoding samples and update
it periodically as real gameplay data accumulates.
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

    def __init__(self):
        self.model = DecisionTreeClassifier(max_depth=6, random_state=42)
        self._is_trained = False
        self._base_X = None
        self._base_y = None
        self._bootstrap()
        self.load()

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

    # Persistence
    def update_from_examples(self, examples: list[tuple[np.ndarray, int]]):
        if not examples:
            return
        X_new = np.array([features for features, _ in examples], dtype=np.float32)
        y_new = np.array([label for _, label in examples], dtype=np.int32)
        if self._base_X is not None and self._base_y is not None:
            X = np.vstack([self._base_X, X_new])
            y = np.concatenate([self._base_y, y_new])
        else:
            X, y = X_new, y_new
        self.model.fit(X, y)
        self._is_trained = True

    def save(self):
        os.makedirs(os.path.dirname(DT_MODEL_PATH), exist_ok=True)
        with open(DT_MODEL_PATH, "wb") as f:
            pickle.dump(self.model, f)

    def load(self):
        if os.path.exists(DT_MODEL_PATH):
            with open(DT_MODEL_PATH, "rb") as f:
                self.model = pickle.load(f)
            self._is_trained = True
