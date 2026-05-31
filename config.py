import os

# Display
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TITLE = "Adaptive Kingdom Rescue"
TILE_SIZE = 48

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 50, 50)
GREEN = (50, 200, 80)
BLUE = (50, 100, 220)
YELLOW = (255, 220, 0)
ORANGE = (255, 140, 0)
PURPLE = (150, 50, 200)
SKY_BLUE = (135, 206, 235)
GROUND_BROWN = (139, 90, 43)
GRAY = (120, 120, 120)
DARK_GRAY = (60, 60, 60)
GOLD = (255, 215, 0)
PINK = (255, 182, 193)

# Player
PLAYER_WIDTH = 38
PLAYER_HEIGHT = 38
PLAYER_WALK_SPEED = 96
PLAYER_RUN_SPEED = 240
PLAYER_DASH_SPEED = 384
PLAYER_DASH_DURATION = 1.0
PLAYER_DASH_COOLDOWN = 3.0
PLAYER_JUMP_VELOCITY = -680
PLAYER_HOLD_JUMP_BONUS = -120
PLAYER_MAX_LIVES = 9
PLAYER_START_LIVES = 3
GRAVITY = 1800

# Enemy
ENEMY_GROUND_WIDTH = 34
ENEMY_GROUND_HEIGHT = 34
ENEMY_FLYING_WIDTH = 42
ENEMY_FLYING_HEIGHT = 24
ENEMY_PATROL_SPEED = 80
ENEMY_CHASE_SPEED = 160
ENEMY_STOMP_KILL_ZONE = 0.10

# Level
LEVEL_TIME_LIMIT = 90
CHECKPOINT_SPACING = 20 * 48

# Scoring
SCORE_DEFEAT_ENEMY = 100
SCORE_DEFEAT_JUMP_BONUS = 50
SCORE_MUSHROOM = 50
SCORE_FLOWER = 50
SCORE_STAR = 100
SCORE_SHIELD = 75
SCORE_CHECKPOINT = 200
SCORE_LEVEL_COMPLETE = 1000
SCORE_TIME_BONUS_RATE = 10
SCORE_NO_DAMAGE_BONUS = 500
SCORE_VARIETY_BONUS = 50
SCORE_EXTRA_LIFE_THRESHOLD = 5000

# AI system
AI_ACTION_HISTORY_LEN = 30
AI_ACTION_BUFFER_LEN = 300
RNN_INFERENCE_INTERVAL = 0.2
DT_WEIGHT = 0.5
RNN_WEIGHT = 0.5

# Adaptive difficulty
# Per-level base pressure (0..1) before any tries. Kept very low so the first
# several attempts are really easy (enemies barely chase).
DIFFICULTY_LEVEL_BASE = [0.05, 0.12, 0.20]
# Seconds at the start of every level where enemies stay calmer (breathing room).
DIFFICULTY_WARMUP_TIME = 12.0
# Difficulty ramps with the number of TRIES (attempts) the player has made, so it
# climbs even if the player keeps dying/retrying. Peaks after this many tries.
DIFFICULTY_TRIES_FULL = 16
# How much the tries-progress adds on top of the per-level base at the peak.
DIFFICULTY_PROGRESS_MAX = 0.85

# Action indices
ACTION_IDLE = 0
ACTION_JUMP = 1
ACTION_RUN = 2
ACTION_DASH = 3
ACTION_ATTACK = 4
ACTION_COUNT = 5
ACTION_NAMES = ["IDLE", "JUMP", "RUN", "DASH", "ATTACK"]

# Enemy strategic actions
STRAT_PATROL = 0
STRAT_CHASE = 1
STRAT_SPAWN_AERIAL = 2
STRAT_BLOCK_UPPER = 3
STRAT_BLOCK_LOWER = 4
STRAT_AMBUSH = 5
STRAT_RETREAT = 6
STRAT_COUNT = 7
STRAT_NAMES = [
    "PATROL",
    "CHASE",
    "SPAWN_AERIAL",
    "BLOCK_UPPER",
    "BLOCK_LOWER",
    "AMBUSH",
    "RETREAT",
]

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Baseline models are optional shipped defaults. Runtime models are local,
# ignored saves that carry the player's adapted behavior across launches.
BASELINE_MODELS_DIR = os.path.join(BASE_DIR, "data", "models")
RUNTIME_MODELS_DIR = os.path.join(BASE_DIR, "data", "runtime_models")
LOGS_DIR = os.path.join(BASE_DIR, "data", "logs")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
SPRITES_DIR = os.path.join(ASSETS_DIR, "sprites")
SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")

RNN_BASELINE_MODEL_PATH = os.path.join(BASELINE_MODELS_DIR, "rnn_predictor.pt")
DT_BASELINE_MODEL_PATH = os.path.join(BASELINE_MODELS_DIR, "decision_tree.pkl")

RNN_MODEL_PATH = os.path.join(RUNTIME_MODELS_DIR, "rnn_predictor.pt")
DT_MODEL_PATH = os.path.join(RUNTIME_MODELS_DIR, "decision_tree.pkl")
PROGRESS_PATH = os.path.join(RUNTIME_MODELS_DIR, "progress.json")
