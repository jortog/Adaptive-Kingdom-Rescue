import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE

# ── Palette ────────────────────────────────────────────────────────────────────
SKY_COL     = (92,  148, 252)
CLOUD_WHITE = (255, 255, 255)
CLOUD_SHAD  = (210, 210, 235)
HILL_GREEN  = (86,  168,  48)
HILL_DARK   = (55,  120,  28)
HILL_SPOT   = (120, 200,  70)
GRASS_TOP   = (106, 191,  75)
GRASS_DARK  = (72,  148,  48)
DIRT_MID    = (181, 101,  29)
DIRT_DARK   = (130,  72,  18)
BRICK_MAIN  = (190,  88,  42)
BRICK_HIGH  = (230, 130,  75)
BRICK_DARK  = (130,  52,  18)

_CLOUDS = [(120,55),(380,35),(680,65),(980,40),(1280,60),(1600,45),(1900,70)]

def draw_background(surface: pygame.Surface, camera_x: int):
    surface.fill(SKY_COL)
    hill_off = (camera_x // 4) % 340
    for i in range(-1, SCREEN_WIDTH // 340 + 3):
        hx = i * 340 - hill_off
        _hill(surface, hx + 170, SCREEN_HEIGHT - 70, 165, 105)
        _hill(surface, hx + 10,  SCREEN_HEIGHT - 50, 100,  70)
    cloud_off = (camera_x // 7) % (SCREEN_WIDTH + 250)
    for cx, cy in _CLOUDS:
        dx = (cx - cloud_off) % (SCREEN_WIDTH + 250) - 125
        _cloud(surface, dx, cy)

def _hill(surface, cx, base_y, rx, ry):
    pygame.draw.ellipse(surface, HILL_GREEN, (cx-rx, base_y-ry, rx*2, ry*2))
    pygame.draw.ellipse(surface, HILL_DARK,  (cx-rx+18, base_y-ry+18, rx*2-36, ry*2-36))
    pygame.draw.circle(surface, HILL_SPOT,   (cx - rx//3, base_y - ry//3), 9)
    pygame.draw.circle(surface, HILL_SPOT,   (cx + rx//4, base_y - ry//2), 6)

def _cloud(surface, x, y):
    parts = [(x, y+16, 72, 32), (x+20, y, 48, 38), (x+46, y+10, 54, 30)]
    for r in parts:
        pygame.draw.ellipse(surface, CLOUD_SHAD, (r[0]+2, r[1]+3, r[2], r[3]))
    for r in parts:
        pygame.draw.ellipse(surface, CLOUD_WHITE, r)

def draw_ground_tile(surface: pygame.Surface, rect: pygame.Rect):
    pygame.draw.rect(surface, DIRT_MID, rect)
    row = rect.y // TILE_SIZE
    half = TILE_SIZE // 2
    for bx in range(rect.x, rect.right + 1, TILE_SIZE):
        off = half if row % 2 == 0 else 0
        pygame.draw.line(surface, DIRT_DARK,
                         (bx + off, rect.y + 14), (bx + off, rect.bottom), 1)
    pygame.draw.line(surface, DIRT_DARK,
                     (rect.x, rect.centery), (rect.right, rect.centery), 1)
    pygame.draw.rect(surface, GRASS_TOP,  (rect.x, rect.y, rect.width, 13))
    pygame.draw.rect(surface, GRASS_DARK, (rect.x, rect.y + 10, rect.width, 3))
    pygame.draw.rect(surface, DIRT_DARK, rect, 1)

def draw_platform_tile(surface: pygame.Surface, rect: pygame.Rect):
    pygame.draw.rect(surface, BRICK_MAIN, rect)
    pygame.draw.rect(surface, BRICK_HIGH, (rect.x, rect.y, rect.width, 6))
    pygame.draw.rect(surface, BRICK_HIGH, (rect.x, rect.y, 4, rect.height))
    pygame.draw.line(surface, BRICK_DARK,
                     (rect.x, rect.centery), (rect.right, rect.centery), 2)
    row = rect.y // TILE_SIZE
    off = (TILE_SIZE // 2) if row % 2 == 0 else 0
    for bx in range(rect.x + off, rect.right, TILE_SIZE):
        rel = bx - rect.x
        if 0 < rel < rect.width:
            pygame.draw.line(surface, BRICK_DARK, (bx, rect.y), (bx, rect.bottom), 2)
    pygame.draw.rect(surface, BRICK_DARK, rect, 1)
