import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE

# ── Palette ────────────────────────────────────────────────────────────────────
SKY_TOP     = (108, 180, 255)
SKY_BOT     = ( 64, 130, 230)
CLOUD_WHITE = (255, 255, 255)
CLOUD_SHAD  = (210, 215, 240)
HILL_LT     = ( 92, 185,  60)
HILL_DK     = ( 58, 140,  35)
HILL_SPOT   = (120, 210,  75)
GRASS_TOP   = (108, 196,  78)
GRASS_DRK   = ( 74, 152,  48)
DIRT_MID    = (185, 105,  32)
DIRT_DRK    = (135,  72,  18)
BRICK_MAIN  = (192,  90,  44)
BRICK_HIGH  = (230, 130,  75)
BRICK_DRK   = (132,  54,  20)

# ── Cached surfaces (built once) ───────────────────────────────────────────────
_sky_surf:   pygame.Surface | None = None
_tile_cache: dict = {}   # (tile_type, w, h) -> Surface

def _build_sky():
    """Pre-render the sky gradient into a surface once."""
    global _sky_surf
    _sky_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    for y in range(SCREEN_HEIGHT):
        t   = y / SCREEN_HEIGHT
        r   = int(SKY_TOP[0] + (SKY_BOT[0]-SKY_TOP[0])*t)
        g   = int(SKY_TOP[1] + (SKY_BOT[1]-SKY_TOP[1])*t)
        b   = int(SKY_TOP[2] + (SKY_BOT[2]-SKY_TOP[2])*t)
        pygame.draw.line(_sky_surf, (r,g,b), (0,y),(SCREEN_WIDTH,y))

def _get_tile_surface(tile_type: str) -> pygame.Surface:
    """Return a cached pre-rendered tile surface."""
    if tile_type in _tile_cache:
        return _tile_cache[tile_type]

    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
    if tile_type == "ground":
        surf.fill(DIRT_MID)
        # Grass cap
        pygame.draw.rect(surf, GRASS_TOP,  (0, 0, TILE_SIZE, 13))
        pygame.draw.rect(surf, GRASS_DRK,  (0,10, TILE_SIZE, 3))
        # Dirt lines
        pygame.draw.line(surf, DIRT_DRK,   (0, TILE_SIZE//2),(TILE_SIZE,TILE_SIZE//2),1)
        pygame.draw.line(surf, DIRT_DRK,   (TILE_SIZE//2,14),(TILE_SIZE//2,TILE_SIZE),1)
        pygame.draw.rect(surf, DIRT_DRK,   (0,0,TILE_SIZE,TILE_SIZE),1)
    elif tile_type == "platform":
        surf.fill(BRICK_MAIN)
        pygame.draw.rect(surf, BRICK_HIGH, (0,0,TILE_SIZE,6))
        pygame.draw.rect(surf, BRICK_HIGH, (0,0,4,TILE_SIZE))
        pygame.draw.line(surf, BRICK_DRK,  (0,TILE_SIZE//2),(TILE_SIZE,TILE_SIZE//2),2)
        pygame.draw.line(surf, BRICK_DRK,  (TILE_SIZE//2,0),(TILE_SIZE//2,TILE_SIZE),2)
        pygame.draw.rect(surf, BRICK_DRK,  (0,0,TILE_SIZE,TILE_SIZE),1)

    _tile_cache[tile_type] = surf
    return surf

def _cloud(surface: pygame.Surface, cx: int, cy: int, scale: float = 1.0):
    parts = [
        (int(cx),          int(cy+14*scale), int(78*scale), int(30*scale)),
        (int(cx+16*scale), int(cy),          int(54*scale), int(38*scale)),
        (int(cx+46*scale), int(cy+10*scale), int(60*scale), int(28*scale)),
    ]
    for r in parts:
        pygame.draw.ellipse(surface, CLOUD_SHAD,(r[0]+2,r[1]+3,r[2],r[3]))
    for r in parts:
        pygame.draw.ellipse(surface, CLOUD_WHITE, r)

def _hill(surface: pygame.Surface, cx: int, base_y: int, rx: int, ry: int):
    pygame.draw.ellipse(surface, HILL_DK,   (cx-rx, base_y-ry, rx*2, ry*2))
    pygame.draw.ellipse(surface, HILL_LT,   (cx-rx+10, base_y-ry+10, rx*2-20, ry*2-20))
    pygame.draw.circle(surface, HILL_SPOT,  (cx-rx//3, base_y-ry//3), 12)
    pygame.draw.circle(surface, HILL_SPOT,  (cx+rx//4, base_y-ry//2), 8)

# ── Public API ─────────────────────────────────────────────────────────────────
def draw_background(surface: pygame.Surface, camera_x: int):
    """Draw sky + parallax hills + clouds. Sky is cached; hills/clouds use camera offset."""
    global _sky_surf
    if _sky_surf is None:
        _build_sky()

    # Blit pre-rendered sky (O(1) — single surface copy)
    surface.blit(_sky_surf, (0, 0))

    # Hills (parallax: 1/5 of camera speed)
    hill_off = (camera_x // 5) % 320
    ground_y = SCREEN_HEIGHT - 68
    for i in range(-1, SCREEN_WIDTH // 320 + 3):
        hx = i * 320 - hill_off
        _hill(surface, hx + 160, ground_y, 155, 95)
        _hill(surface, hx + 10,  ground_y - 20, 90, 62)

    # Clouds (parallax: 1/8 of camera speed)
    CLOUD_DEFS = [
        (80, 52,1.05),(300,30,0.85),(560,68,1.20),(830,42,0.90),
        (1060,60,1.10),(1290,36,0.80),(1490,72,1.00),
    ]
    cloud_period = SCREEN_WIDTH + 220
    for cx, cy, sc in CLOUD_DEFS:
        ox = (cx - camera_x // 8) % cloud_period - 110
        _cloud(surface, ox, cy, sc)

def draw_ground_tile(surface: pygame.Surface, rect: pygame.Rect):
    """Blit a cached ground tile — O(1) per tile."""
    surface.blit(_get_tile_surface("ground"), rect)

def draw_platform_tile(surface: pygame.Surface, rect: pygame.Rect):
    """Blit a cached platform tile — O(1) per tile."""
    surface.blit(_get_tile_surface("platform"), rect)
