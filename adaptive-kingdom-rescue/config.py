# config.py
import os

# ─── DISPLAY ──────────────────────────────────────────────────────────────────
SCREEN_WIDTH  = 1280
SCREEN_HEIGHT = 720
FPS           = 60
TITLE         = "Adaptive Kingdom Rescue"
TILE_SIZE     = 48

# ─── COLORS ───────────────────────────────────────────────────────────────────
WHITE        = (255, 255, 255)
BLACK        = (0,   0,   0  )
RED          = (220, 50,  50 )
GREEN        = (50,  200, 80 )
BLUE         = (50,  100, 220)
YELLOW       = (255, 220, 0  )
ORANGE       = (255, 140, 0  )
PURPLE       = (150, 50,  200)
SKY_BLUE     = (135, 206, 235)
GROUND_BROWN = (139, 90,  43 )
GRAY         = (120, 120, 120)
DARK_GRAY    = (60,  60,  60 )
GOLD         = (255, 215, 0  )
PINK         = (255, 182, 193)

# ─── PLAYER ───────────────────────────────────────────────────────────────────
PLAYER_WIDTH            = 38
PLAYER_HEIGHT           = 38
PLAYER_WALK_SPEED       = 96
PLAYER_RUN_SPEED        = 240
PLAYER_DASH_SPEED       = 384
PLAYER_DASH_DURATION    = 1.0
PLAYER_DASH_COOLDOWN    = 3.0
PLAYER_JUMP_VELOCITY    = -680
PLAYER_HOLD_JUMP_BONUS  = -120
PLAYER_MAX_LIVES        = 9
PLAYER_START_LIVES      = 3
GRAVITY                 = 1800

# ─── ENEMY ────────────────────────────────────────────────────────────────────
ENEMY_GROUND_WIDTH    = 34
ENEMY_GROUND_HEIGHT   = 34
ENEMY_FLYING_WIDTH    = 42
ENEMY_FLYING_HEIGHT   = 24
ENEMY_PATROL_SPEED    = 80
ENEMY_CHASE_SPEED     = 160
ENEMY_STOMP_KILL_ZONE = 0.10

# ─── LEVEL ────────────────────────────────────────────────────────────────────
LEVEL_TIME_LIMIT     = 90
CHECKPOINT_SPACING   = 20 * 48

# ─── SCORING ──────────────────────────────────────────────────────────────────
SCORE_DEFEAT_ENEMY        = 100
SCORE_DEFEAT_JUMP_BONUS   = 50
SCORE_MUSHROOM            = 50
SCORE_FLOWER              = 50
SCORE_STAR                = 100
SCORE_SHIELD              = 75
SCORE_CHECKPOINT          = 200
SCORE_LEVEL_COMPLETE      = 1000
SCORE_TIME_BONUS_RATE     = 10
SCORE_NO_DAMAGE_BONUS     = 500
SCORE_VARIETY_BONUS       = 50
SCORE_EXTRA_LIFE_THRESHOLD = 5000

# ─── AI SYSTEM ────────────────────────────────────────────────────────────────
AI_ACTION_HISTORY_LEN = 30
RNN_INFERENCE_INTERVAL = 0.2
PPO_UPDATE_INTERVAL    = 10.0
DT_WEIGHT  = 0.3
RNN_WEIGHT = 0.3
PPO_WEIGHT = 0.4

# Action indices
ACTION_IDLE   = 0
ACTION_JUMP   = 1
ACTION_RUN    = 2
ACTION_DASH   = 3
ACTION_ATTACK = 4
ACTION_COUNT  = 5
ACTION_NAMES  = ["IDLE", "JUMP", "RUN", "DASH", "ATTACK"]

# Enemy strategic actions
STRAT_PATROL       = 0
STRAT_CHASE        = 1
STRAT_SPAWN_AERIAL = 2
STRAT_BLOCK_UPPER  = 3
STRAT_BLOCK_LOWER  = 4
STRAT_AMBUSH       = 5
STRAT_RETREAT      = 6
STRAT_COUNT        = 7

# ─── PATHS ────────────────────────────────────────────────────────────────────
BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR     = os.path.join(BASE_DIR, "data", "models")
LOGS_DIR       = os.path.join(BASE_DIR, "data", "logs")
ASSETS_DIR     = os.path.join(BASE_DIR, "assets")
SPRITES_DIR    = os.path.join(ASSETS_DIR, "sprites")
SOUNDS_DIR     = os.path.join(ASSETS_DIR, "sounds")
FONTS_DIR      = os.path.join(ASSETS_DIR, "fonts")

RNN_MODEL_PATH = os.path.join(MODELS_DIR, "rnn_predictor.pt")
PPO_MODEL_PATH = os.path.join(MODELS_DIR, "ppo_agent.zip")
DT_MODEL_PATH  = os.path.join(MODELS_DIR, "decision_tree.pkl")