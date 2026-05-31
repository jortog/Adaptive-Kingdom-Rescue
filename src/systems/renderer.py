import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE

# Night palette
SKY_TOP = (14, 18, 48)
SKY_MID = (28, 34, 78)
SKY_BOT = (52, 58, 104)
MOON_C = (248, 246, 220)
MOON_G = (220, 228, 255)

HILL_FAR_L = (34, 46, 86)
HILL_FAR_D = (24, 34, 68)
HILL_MID_L = (30, 54, 70)
HILL_MID_D = (20, 40, 54)
HILL_MID_S = (46, 78, 92)
BUSH_L = (28, 60, 46)
BUSH_D = (18, 44, 34)
BUSH_S = (44, 86, 62)

GRASS_T = (54, 120, 70)
GRASS_T2 = (74, 148, 92)
GRASS_D = (34, 84, 48)
DIRT_M = (96, 66, 40)
DIRT_L = (120, 86, 54)
DIRT_D = (64, 42, 24)
BRICK_M = (110, 60, 46)
BRICK_H = (150, 88, 66)
BRICK_D = (70, 38, 26)

_sky_surf = None
_tile_cache = {}
_cloud_cache = None
_STARS = None


def _build_sky():
    surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    for y in range(SCREEN_HEIGHT):
        t = y / SCREEN_HEIGHT
        if t < 0.55:
            tt = t / 0.55
            r = int(SKY_TOP[0] + (SKY_MID[0] - SKY_TOP[0]) * tt)
            g = int(SKY_TOP[1] + (SKY_MID[1] - SKY_TOP[1]) * tt)
            b = int(SKY_TOP[2] + (SKY_MID[2] - SKY_TOP[2]) * tt)
        else:
            tt = (t - 0.55) / 0.45
            r = int(SKY_MID[0] + (SKY_BOT[0] - SKY_MID[0]) * tt)
            g = int(SKY_MID[1] + (SKY_BOT[1] - SKY_MID[1]) * tt)
            b = int(SKY_MID[2] + (SKY_BOT[2] - SKY_MID[2]) * tt)
        pygame.draw.line(surf, (r, g, b), (0, y), (SCREEN_WIDTH, y))
    # Stars
    import random as _r

    _r.seed(11)
    for _ in range(90):
        sx = _r.randint(0, SCREEN_WIDTH)
        sy = _r.randint(0, int(SCREEN_HEIGHT * 0.6))
        c = _r.randint(150, 255)
        pygame.draw.circle(surf, (c, c, min(255, c + 20)), (sx, sy), _r.randint(1, 2))
    # Moon
    mx, my = int(SCREEN_WIDTH * 0.82), int(SCREEN_HEIGHT * 0.18)
    for i in range(8, 0, -1):
        gl = pygame.Surface((i * 54, i * 54), pygame.SRCALPHA)
        pygame.draw.circle(gl, (*MOON_G, 10), (i * 27, i * 27), i * 27)
        surf.blit(gl, (mx - i * 27, my - i * 27), special_flags=pygame.BLEND_RGBA_ADD)
    pygame.draw.circle(surf, MOON_C, (mx, my), 40)
    pygame.draw.circle(surf, (232, 230, 205), (mx - 12, my + 8), 9)
    pygame.draw.circle(surf, (232, 230, 205), (mx + 10, my + 14), 6)
    return surf


def _make_cloud(scale=1.0):
    w, h = int(150 * scale), int(70 * scale)
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    lumps = [
        (0.18, 0.55, 0.34),
        (0.34, 0.30, 0.40),
        (0.54, 0.26, 0.42),
        (0.74, 0.50, 0.32),
        (0.46, 0.58, 0.38),
    ]
    for lx, ly, lr in lumps:
        pygame.draw.circle(
            s,
            (60, 68, 110, 150),
            (
                int(w * lx),
                int(h * ly),
            ),
            int(h * lr),
        )
    for lx, ly, lr in lumps:
        pygame.draw.circle(
            s, (78, 88, 135, 180), (int(w * lx), int(h * ly)), int(h * lr)
        )
    return s


def _get_tile(kind):
    if kind in _tile_cache:
        return _tile_cache[kind]
    s = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    if kind == "ground":
        for y in range(TILE_SIZE):
            t = y / TILE_SIZE
            r = int(DIRT_L[0] + (DIRT_D[0] - DIRT_L[0]) * t)
            g = int(DIRT_L[1] + (DIRT_D[1] - DIRT_L[1]) * t)
            b = int(DIRT_L[2] + (DIRT_D[2] - DIRT_L[2]) * t)
            pygame.draw.line(s, (r, g, b), (0, y), (TILE_SIZE, y))
        import random as _r

        _r.seed(7)
        for _ in range(10):
            pygame.draw.circle(
                s,
                DIRT_D,
                (_r.randint(2, TILE_SIZE - 3), _r.randint(16, TILE_SIZE - 3)),
                1,
            )
        pygame.draw.rect(s, GRASS_D, (0, 0, TILE_SIZE, 16))
        pygame.draw.rect(s, GRASS_T, (0, 0, TILE_SIZE, 12))
        pygame.draw.rect(s, GRASS_T2, (0, 0, TILE_SIZE, 5))
        for bx in range(2, TILE_SIZE, 8):
            pygame.draw.circle(s, GRASS_T2, (bx, 4), 3)
        pygame.draw.rect(s, DIRT_D, (0, 0, TILE_SIZE, TILE_SIZE), 1)
    elif kind == "platform":
        for y in range(TILE_SIZE):
            t = y / TILE_SIZE
            r = int(BRICK_H[0] + (BRICK_D[0] - BRICK_H[0]) * t)
            g = int(BRICK_H[1] + (BRICK_D[1] - BRICK_H[1]) * t)
            b = int(BRICK_H[2] + (BRICK_D[2] - BRICK_H[2]) * t)
            pygame.draw.line(s, (r, g, b), (0, y), (TILE_SIZE, y))
        pygame.draw.rect(s, BRICK_H, (0, 0, TILE_SIZE, 5))
        pygame.draw.rect(s, BRICK_H, (0, 0, 4, TILE_SIZE))
        pygame.draw.line(
            s, BRICK_D, (0, TILE_SIZE // 2), (TILE_SIZE, TILE_SIZE // 2), 2
        )
        pygame.draw.line(
            s, BRICK_D, (TILE_SIZE // 2, 0), (TILE_SIZE // 2, TILE_SIZE), 2
        )
        pygame.draw.rect(s, BRICK_D, (0, 0, TILE_SIZE, TILE_SIZE), 1)
    _tile_cache[kind] = s
    return s


def _blit_sky(surface):
    global _sky_surf
    if _sky_surf is None:
        _sky_surf = _build_sky()
    surface.blit(_sky_surf, (0, 0))


def _hill(surface, cx, by, rx, ry, lt, dk, spot=None):
    pygame.draw.ellipse(surface, dk, (cx - rx, by - ry, rx * 2, ry * 2))
    pygame.draw.ellipse(
        surface, lt, (cx - rx + 12, by - ry + 10, rx * 2 - 24, ry * 2 - 20)
    )
    if spot:
        pygame.draw.circle(
            surface, spot, (cx - rx // 3, by - ry // 3), max(6, rx // 12)
        )
        pygame.draw.circle(
            surface, spot, (cx + rx // 4, by - ry // 2), max(4, rx // 16)
        )


CLOUD_DEFS = [
    (110, 70, 1.15),
    (360, 42, 0.85),
    (640, 86, 1.30),
    (920, 52, 0.95),
    (1180, 72, 1.10),
    (1460, 46, 0.80),
]


def draw_background(surface, camera_x):
    global _cloud_cache
    if _cloud_cache is None:
        _cloud_cache = {round(sc, 2): _make_cloud(sc) for _, _, sc in CLOUD_DEFS}
    _blit_sky(surface)
    gy = SCREEN_HEIGHT - 68
    off1 = (camera_x // 6) % 360
    for i in range(-1, SCREEN_WIDTH // 360 + 3):
        _hill(surface, i * 360 - off1 + 180, gy + 20, 200, 120, HILL_FAR_L, HILL_FAR_D)
    off2 = (camera_x // 4) % 300
    for i in range(-1, SCREEN_WIDTH // 300 + 3):
        _hill(
            surface,
            i * 300 - off2 + 150,
            gy + 10,
            165,
            100,
            HILL_MID_L,
            HILL_MID_D,
            HILL_MID_S,
        )
    period = SCREEN_WIDTH + 260
    for cx, cy, sc in CLOUD_DEFS:
        ox = (cx - camera_x // 8) % period - 130
        surface.blit(_cloud_cache[round(sc, 2)], (ox, cy))
    off4 = (camera_x // 2) % 220
    for i in range(-1, SCREEN_WIDTH // 220 + 3):
        _hill(surface, i * 220 - off4 + 110, gy + 4, 120, 70, BUSH_L, BUSH_D, BUSH_S)


def draw_ground_tile(surface, rect):
    surface.blit(_get_tile("ground"), rect)


def draw_platform_tile(surface, rect):
    sh = pygame.Surface((rect.width, 6), pygame.SRCALPHA)
    sh.fill((0, 0, 0, 70))
    surface.blit(sh, (rect.x, rect.bottom))
    surface.blit(_get_tile("platform"), rect)
