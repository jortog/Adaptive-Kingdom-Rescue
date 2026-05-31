"""Decision-tree AI layer for readable enemy behavior rules.

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

    def __init__(self):
        self.model = DecisionTreeClassifier(max_depth=6, random_state=42)
        self._base_X = None
        self._base_y = None
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

    def predict_proba(self, features: np.ndarray) -> np.ndarray:
        """Return a probability distribution over all enemy strategies."""
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

    def update_from_examples(self, examples: list[tuple[np.ndarray, int]]):
        """Re-fit with baseline rules plus new player-specific examples."""
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

    def save(self):
        os.makedirs(os.path.dirname(DT_MODEL_PATH), exist_ok=True)
        with open(DT_MODEL_PATH, "wb") as f:
            pickle.dump(self.model, f)

    def load(self):
        load_path = DT_MODEL_PATH
        if not os.path.exists(load_path):
            load_path = DT_BASELINE_MODEL_PATH
        if os.path.exists(load_path):
            with open(load_path, "rb") as f:
                self.model = pickle.load(f)
