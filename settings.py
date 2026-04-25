
# Map
SCREEN_W, SCREEN_H = 900, 600
WORLD_W,  WORLD_H  = 2700, 1800 #3x ecran
FPS   = 60
TITLE = "Orbital Defender"

# Culori
PLAYER_COL = (80,  160, 255)
ORBIT_COL  = (255, 200,  60)
ORBIT_GLOW = (255, 240, 120)
ENEMY_COL  = (220,  50,  40)
ENEMY_GLOW = (255, 100,  80)
ENEMY_DEAD = (255, 180,  60)

# Player
PLAYER_RADIUS = 18
PLAYER_SPEED  = 4.5

# Orbit
ORBIT_RADIUS    = 70
ORBIT_W         = 28
ORBIT_H         = 12
ORBIT_ROT_SPEED = 2.5

# Enemy
ENEMY_RADIUS_BASE = 12
ENEMY_SPEED_BASE  = 1.6
ENEMY_HP_BASE     = 1
SPAWN_MARGIN      = 60

# Wave
WAVE_BASE_COUNT     = 6
WAVE_COUNT_SCALE    = 3
WAVE_SPAWN_DELAY    = 40
WAVE_BREAK_FRAMES   = 180

# Scal per wave
WAVE_SPEED_SCALE    = 0.15
WAVE_HP_SCALE       = 1
WAVE_RADIUS_SCALE   = 1.2
WAVE_SPEED_MAX      = 5.0

# Mastery kills
KILL_PER_LEVEL = 5

# Upgrade limits
MAX_SPEED_UPGRADES  = 1
MAX_SIZE_UPGRADES   = 1
MAX_ORBIT_UPGRADES  = 1

SPEED_BONUS_PER_UPGRADE = 0.8
SIZE_BONUS_PER_UPGRADE  = 6

# Warning
DANGER_DISTANCE = 120

# Highscore
HIGHSCORE_FILE = "highscore.txt"

# Shielded Enemy
SHIELDED_ENEMY_WAVE_START = 5
SHIELDED_ENEMY_RADIUS     = 16
SHIELDED_ENEMY_SPEED_MULT = 1.6
SHIELDED_COL              = (80,  200, 255)
SHIELDED_GLOW             = (150, 230, 255)
SHIELD_DURATION   = 5 * 60   # 5s shield ON
SHIELD_COOLDOWN   = 3 * 60   # 3s shield OFF

# Spells
FREEZE_COOLDOWN   = 15 * 60   # 15 sec in frames
FREEZE_DURATION   = 4  * 60   #  4 sec in frames

BOMB_COOLDOWN     = 10 * 60   # 10 sec in frames
BOMB_FUSE         = 2  * 60   #  2 sec fuse before explosion
BOMB_RADIUS       = 150       # explosion radius in world units

SHOCKWAVE_COOLDOWN  = 25 * 60  # 25 sec in frames
SHOCKWAVE_SPEED     = 6        # pixels per frame expansion
