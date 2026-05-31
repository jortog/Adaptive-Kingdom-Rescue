import pygame
import math
import random
from config import SCREEN_WIDTH, SCREEN_HEIGHT

_FONT_PATH = "assets/fonts/SuperPixel-m2L8j.ttf"


def _pf(size):
    try:
        return pygame.font.Font(_FONT_PATH, size)
    except Exception:
        return pygame.font.Font(None, size)


def _sf(size, bold=False):
    return pygame.font.SysFont("Arial", size, bold=bold)


C_BG_TOP = (8, 12, 28)
C_BG_MID = (12, 18, 40)
C_BG_BOT = (3, 5, 12)
C_MOON = (255, 248, 210)
C_MOONGL = (255, 240, 180)
C_STAR = (200, 215, 255)
C_CASTLE = (16, 20, 32)
C_CAST_H = (28, 36, 52)
C_WINDOW = (175, 138, 55)
C_FOG = (22, 42, 65)
C_GOLD = (255, 215, 0)
C_GOLD2 = (220, 175, 20)
C_CREAM = (238, 222, 188)
C_DIM = (145, 132, 108)
C_VDIM = (70, 65, 52)
C_WHITE = (255, 255, 255)
C_BLACK = (0, 0, 0)
C_GREEN = (80, 220, 80)
C_RED = (225, 50, 50)

random.seed(55)
_STARS = [
    (
        random.randint(0, SCREEN_WIDTH),
        random.randint(0, int(SCREEN_HEIGHT * 0.65)),
        random.random(),
        random.randint(1, 2),
    )
    for _ in range(80)
]
random.seed(22)
_FIREFLIES = [
    (
        random.randint(50, SCREEN_WIDTH - 50),
        random.randint(int(SCREEN_HEIGHT * 0.5), SCREEN_HEIGHT - 80),
        random.random() * 6.28,
        0.6 + random.random() * 1.6,
    )
    for _ in range(18)
]
random.seed(33)
_TREES = [
    (tx, random.randint(55, 115))
    for tx in range(SCREEN_WIDTH // 2 - 60, SCREEN_WIDTH + 30, 32)
]

_BG_CACHE = None
_CASTLE_CACHE = None


def _build_bg():
    surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    for y in range(SCREEN_HEIGHT):
        t = y / SCREEN_HEIGHT
        if t < 0.5:
            r = int(C_BG_TOP[0] + (C_BG_MID[0] - C_BG_TOP[0]) * t * 2)
            g = int(C_BG_TOP[1] + (C_BG_MID[1] - C_BG_TOP[1]) * t * 2)
            b = int(C_BG_TOP[2] + (C_BG_MID[2] - C_BG_TOP[2]) * t * 2)
        else:
            t2 = (t - 0.5) * 2
            r = int(C_BG_MID[0] + (C_BG_BOT[0] - C_BG_MID[0]) * t2)
            g = int(C_BG_MID[1] + (C_BG_BOT[1] - C_BG_MID[1]) * t2)
            b = int(C_BG_MID[2] + (C_BG_BOT[2] - C_BG_MID[2]) * t2)
        pygame.draw.line(surf, (r, g, b), (0, y), (SCREEN_WIDTH, y))
    return surf


def _build_castle():
    surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    bx = SCREEN_WIDTH - 460
    by = SCREEN_HEIGHT

    def rect(x, y, w, h, col=C_CASTLE):
        pygame.draw.rect(surf, col, (x, y, w, h))

    def battlements(sx, top_y, count, cell=14, notch=10, nw=9):
        for i in range(count):
            pygame.draw.rect(surf, C_CASTLE, (sx + i * cell, top_y - notch, nw, notch))

    rect(bx - 90, by - 115, 28, 115)
    battlements(bx - 90, by - 115, 3, 10, 14, 7)
    lx, ly = bx - 18, by - 235
    rect(lx, ly, 68, by - ly)
    rect(lx, ly, 68, 8, C_CAST_H)
    battlements(lx, ly, 5, 13, 18, 9)
    pygame.draw.rect(surf, C_WINDOW, (lx + 20, ly + 38, 14, 22))
    pygame.draw.circle(surf, C_WINDOW, (lx + 27, ly + 38), 7)
    glow = pygame.Surface((32, 40), pygame.SRCALPHA)
    glow.fill((*C_WINDOW, 35))
    surf.blit(glow, (lx + 13, ly + 30))
    mx, my = bx + 55, by - 355
    rect(mx, my, 112, by - my)
    rect(mx, my, 112, 10, C_CAST_H)
    battlements(mx, my, 8, 14, 22, 10)
    for wy, wh in [(my + 38, 30), (my + 100, 30), (my + 165, 24)]:
        pygame.draw.rect(surf, C_WINDOW, (mx + 32, wy, 20, wh))
        pygame.draw.circle(surf, C_WINDOW, (mx + 42, wy), 10)
        pygame.draw.rect(surf, (0, 0, 0), (mx + 32, wy, 20, wh), 1)
    pygame.draw.rect(surf, (4, 5, 8), (mx + 39, by - 58, 34, 58))
    pygame.draw.circle(surf, (4, 5, 8), (mx + 56, by - 58), 17)
    rx2, ry2 = bx + 172, by - 272
    rect(rx2, ry2, 72, by - ry2)
    rect(rx2, ry2, 72, 8, C_CAST_H)
    battlements(rx2, ry2, 5, 14, 18, 10)
    pygame.draw.rect(surf, C_WINDOW, (rx2 + 22, ry2 + 34, 14, 22))
    pygame.draw.rect(surf, C_WINDOW, (rx2 + 22, ry2 + 80, 14, 18))
    wall_y = by - 185
    rect(lx + 68, wall_y, mx - lx - 68, by - wall_y)
    rect(mx + 112, wall_y, rx2 - mx - 112, by - wall_y)
    battlements(lx + 68, wall_y, 4, 14, 16, 10)
    battlements(mx + 112, wall_y, 3, 14, 16, 10)
    for tx, th in _TREES:
        pygame.draw.rect(surf, (8, 12, 20), (tx + 3, by - th, 8, th))
        pygame.draw.polygon(
            surf,
            (10, 16, 26),
            [(tx + 7, by - th - 32), (tx - 8, by - th + 12), (tx + 22, by - th + 12)],
        )
    return surf


def _blit_bg(surface):
    global _BG_CACHE
    if _BG_CACHE is None:
        _BG_CACHE = _build_bg()
    surface.blit(_BG_CACHE, (0, 0))


def _blit_castle(surface):
    global _CASTLE_CACHE
    if _CASTLE_CACHE is None:
        _CASTLE_CACHE = _build_castle()
    surface.blit(_CASTLE_CACHE, (0, 0))


def _draw_stars(surface, t):
    for sx, sy, phase, size in _STARS:
        bright = 0.3 + 0.7 * abs(math.sin(t * 0.7 + phase * 6.28))
        col = (
            int(C_STAR[0] * bright),
            int(C_STAR[1] * bright),
            min(255, int(C_STAR[2] * bright)),
        )
        pygame.draw.circle(surface, col, (sx, sy), size)


def _draw_moon(surface, cx, cy, r=52):
    for i in range(5, 0, -1):
        gl = pygame.Surface((r * 2 + i * 18, r * 2 + i * 18), pygame.SRCALPHA)
        pygame.draw.circle(gl, (*C_MOONGL, 18), (r + i * 9, r + i * 9), r + i * 9)
        surface.blit(gl, (cx - r - i * 9, cy - r - i * 9))
    pygame.draw.circle(surface, C_MOON, (cx, cy), r)
    pygame.draw.circle(surface, (248, 242, 215), (cx + 6, cy - 6), r - 4)
    for crx, cry, crr in [(-14, 10, 8), (10, 16, 6), (-6, -14, 5)]:
        pygame.draw.circle(surface, (244, 236, 200), (cx + crx, cy + cry), crr)


def _draw_fog(surface, t):
    for i, yb in enumerate([SCREEN_HEIGHT - 50, SCREEN_HEIGHT - 25]):
        fog = pygame.Surface((SCREEN_WIDTH, 55), pygame.SRCALPHA)
        off = int(math.sin(t * 0.28 + i) * 18)
        alpha = 65 + int(math.sin(t * 0.45 + i * 1.5) * 18)
        for fx in range(-60, SCREEN_WIDTH + 60, 90):
            pygame.draw.ellipse(fog, (*C_FOG, alpha), (fx + off, 6, 130, 42))
        surface.blit(fog, (0, yb))


def _draw_fireflies(surface, t):
    for bx, by2, phase, speed in _FIREFLIES:
        angle = t * speed + phase
        fx = int(bx + math.sin(angle * 1.3) * 38)
        fy = int(by2 + math.cos(angle) * 18)
        bright = 0.3 + 0.7 * abs(math.sin(t * 2.2 + phase))
        if bright > 0.45:
            gl = pygame.Surface((14, 14), pygame.SRCALPHA)
            pygame.draw.circle(gl, (170, 255, 110, int(140 * bright)), (7, 7), 7)
            surface.blit(gl, (fx - 7, fy - 7))
            pygame.draw.circle(surface, (200, 255, 150), (fx, fy), 2)


def _outline(surface, text, font, col, x, y, n=2, sc=C_BLACK):
    for dx in range(-n, n + 1):
        for dy in range(-n, n + 1):
            if dx == 0 and dy == 0:
                continue
            surface.blit(font.render(text, True, sc), (x + dx, y + dy))
    surface.blit(font.render(text, True, col), (x, y))


def _center_outline(surface, text, font, col, y, n=2, sc=C_BLACK):
    img = font.render(text, True, col)
    _outline(
        surface, text, font, col, SCREEN_WIDTH // 2 - img.get_width() // 2, y, n, sc
    )


def _center(surface, text, font, col, y):
    img = font.render(text, True, col)
    surface.blit(img, (SCREEN_WIDTH // 2 - img.get_width() // 2, y))


class ScreenManager:
    def __init__(self, surface):
        self.surface = surface
        pygame.font.init()
        self.fp_title = _pf(36)
        self.fp_large = _pf(20)
        self.fp_med = _pf(14)
        self.fp_small = _pf(10)
        self.fs_med = _sf(18, bold=True)
        self.fs_small = _sf(14)
        self.fs_tiny = _sf(12)
        self._t = 0.0

    def tick(self, dt):
        self._t += dt

    def draw_main_menu(self, cursor=0):
        t = self._t
        _blit_bg(self.surface)
        _draw_stars(self.surface, t)
        _draw_moon(self.surface, SCREEN_WIDTH - 195, 108)
        _blit_castle(self.surface)
        _draw_fog(self.surface, t)
        _draw_fireflies(self.surface, t)

        dv = pygame.Surface((1, SCREEN_HEIGHT), pygame.SRCALPHA)
        dv.fill((*C_GOLD, 22))
        div_x = SCREEN_WIDTH // 2 - 40
        self.surface.blit(dv, (div_x, 0))

        M = 58
        _outline(
            self.surface, "ADAPTIVE", self.fp_title, C_GOLD, M, 82, n=2, sc=(75, 48, 0)
        )
        _outline(
            self.surface,
            "KINGDOM RESCUE",
            self.fp_title,
            C_GOLD,
            M,
            130,
            n=2,
            sc=(75, 48, 0),
        )

        sub = self.fp_small.render("~ Super Enemy of Mario ~", True, C_DIM)
        self.surface.blit(sub, (M, 180))
        pygame.draw.line(self.surface, (*C_GOLD2, 120), (M, 200), (div_x - 16, 200), 1)

        ITEMS = ["START GAME", "SETTINGS", "QUIT"]
        for i, item in enumerate(ITEMS):
            iy = 290 + i * 58
            sel = i == cursor
            if sel:
                gbar = pygame.Surface((div_x - M - 20, 38), pygame.SRCALPHA)
                gbar.fill((*C_GOLD, 16))
                self.surface.blit(gbar, (M - 4, iy - 4))
                arr = self.fp_large.render(">", True, C_GOLD)
                self.surface.blit(arr, (M - 22, iy))
                _outline(
                    self.surface,
                    item,
                    self.fp_large,
                    C_GOLD,
                    M,
                    iy,
                    n=2,
                    sc=(75, 48, 0),
                )
            else:
                self.surface.blit(self.fp_large.render(item, True, C_DIM), (M, iy))

        self.surface.blit(
            self.fp_small.render("UP / DOWN   ENTER to select", True, C_VDIM), (M, 466)
        )
        pygame.draw.line(
            self.surface,
            (45, 40, 30),
            (M, SCREEN_HEIGHT - 52),
            (div_x - 16, SCREEN_HEIGHT - 52),
            1,
        )

        tags = [
            ("Decision Tree", (85, 215, 85)),
            ("  +  RNN/LSTM", (85, 155, 255)),
            ("  +  PPO", (255, 160, 65)),
        ]
        fx = M
        for ltxt, lcol in tags:
            img = self.fp_small.render(ltxt, True, lcol)
            self.surface.blit(
                self.fp_small.render(ltxt, True, C_BLACK),
                (fx + 1, SCREEN_HEIGHT - 44 + 1),
            )
            self.surface.blit(img, (fx, SCREEN_HEIGHT - 44))
            fx += img.get_width()

        grp = self.fp_small.render(
            "PUP CCIS  |  Group One  |  Prof. Ria A. Sagum", True, C_WHITE
        )
        self.surface.blit(grp, (M, SCREEN_HEIGHT - 26))

    def draw_settings(
        self, cursor=0, settings=None, selected_level=0, num_levels=3, from_game=False
    ):
        if settings is None:
            settings = {}
        t = self._t

        if not from_game:
            _blit_bg(self.surface)
            _draw_stars(self.surface, t)

        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 175 if from_game else 90))
        self.surface.blit(ov, (0, 0))

        pw, ph = 580, 490
        px, py = SCREEN_WIDTH // 2 - pw // 2, SCREEN_HEIGHT // 2 - ph // 2
        psurf = pygame.Surface((pw, ph), pygame.SRCALPHA)
        psurf.fill((8, 12, 28, 238))
        pygame.draw.rect(psurf, (*C_GOLD, 190), (0, 0, pw, ph), 2, border_radius=8)
        pygame.draw.line(psurf, (*C_GOLD, 65), (8, 8), (pw - 9, 8), 1)
        self.surface.blit(psurf, (px, py))

        timg = self.fp_large.render("SETTINGS", True, C_GOLD)
        _outline(
            self.surface,
            "SETTINGS",
            self.fp_large,
            C_GOLD,
            px + pw // 2 - timg.get_width() // 2,
            py + 18,
            n=2,
            sc=(75, 48, 0),
        )
        pygame.draw.line(
            self.surface, (55, 50, 38), (px + 20, py + 56), (px + pw - 20, py + 56), 1
        )

        level_names = ["ONE", "TWO", "THREE"]
        level_label = f"LEVEL  {level_names[selected_level]}"

        options = [
            ("Menu Music", "ON" if settings.get("music", True) else "OFF"),
            ("Start Level", level_label),
            ("Controls", "VIEW"),
            ("Back", ""),
        ]

        oy = py + 72
        for i, (label, value) in enumerate(options):
            sel = i == cursor
            lc = C_GOLD if sel else C_DIM
            vc = C_CREAM if sel else (115, 108, 90)
            row_y = oy + i * 60

            if sel:
                hbar = pygame.Surface((pw - 36, 40), pygame.SRCALPHA)
                hbar.fill((*C_GOLD, 18))
                self.surface.blit(hbar, (px + 18, row_y - 4))
                self.surface.blit(
                    self.fp_med.render(">", True, C_GOLD), (px + 20, row_y + 2)
                )

            self.surface.blit(self.fp_med.render(label, True, lc), (px + 44, row_y + 2))

            if value:
                show_arrows = sel and label not in ("Controls", "Back")
                vtxt = f"<  {value}  >" if show_arrows else value
                vi = self.fp_med.render(vtxt, True, vc)
                self.surface.blit(vi, (px + pw - vi.get_width() - 28, row_y + 2))

        if cursor == 2:
            ctrls = [
                ("Move", "A / D  or  Arrows"),
                ("Jump", "SPACE / W / UP / Z"),
                ("Pause", "P"),
            ]
            cy2 = oy + 4 * 60 - 12
            for ci, (act, key) in enumerate(ctrls):
                self.surface.blit(
                    self.fs_tiny.render(act, True, (110, 104, 88)),
                    (px + 46, cy2 + ci * 20),
                )
                self.surface.blit(
                    self.fs_tiny.render(key, True, (165, 158, 132)),
                    (px + 175, cy2 + ci * 20),
                )

        hnt = self.fp_small.render(
            "UP/DOWN move   LEFT/RIGHT change   ESC back", True, C_VDIM
        )
        self.surface.blit(hnt, (px + pw // 2 - hnt.get_width() // 2, py + ph - 26))

    def draw_pause(self, cursor=0):
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 165))
        self.surface.blit(ov, (0, 0))

        pw, ph = 360, 255
        px, py = SCREEN_WIDTH // 2 - pw // 2, SCREEN_HEIGHT // 2 - ph // 2
        ps = pygame.Surface((pw, ph), pygame.SRCALPHA)
        ps.fill((8, 12, 28, 240))
        pygame.draw.rect(ps, (*C_GOLD, 195), (0, 0, pw, ph), 2, border_radius=10)
        pygame.draw.line(ps, (*C_GOLD, 65), (6, 6), (pw - 7, 6), 1)
        self.surface.blit(ps, (px, py))

        timg = self.fp_large.render("PAUSED", True, C_GOLD)
        _outline(
            self.surface,
            "PAUSED",
            self.fp_large,
            C_GOLD,
            px + pw // 2 - timg.get_width() // 2,
            py + 18,
            n=2,
            sc=(75, 48, 0),
        )
        pygame.draw.line(
            self.surface, (50, 45, 32), (px + 20, py + 56), (px + pw - 20, py + 56), 1
        )

        for i, item in enumerate(["RESUME", "SETTINGS", "BACK TO MENU"]):
            sel = i == cursor
            iy2 = py + 72 + i * 52
            if sel:
                self.surface.blit(self.fp_med.render(">", True, C_GOLD), (px + 24, iy2))
            self.surface.blit(
                self.fp_med.render(item, True, C_GOLD if sel else C_DIM), (px + 46, iy2)
            )

        hnt = self.fp_small.render("UP/DOWN   ENTER", True, C_VDIM)
        self.surface.blit(hnt, (px + pw // 2 - hnt.get_width() // 2, py + ph - 24))

    def draw_level_complete(self, score, level_index):
        t = self._t
        _blit_bg(self.surface)
        _draw_stars(self.surface, t)
        _draw_moon(self.surface, SCREEN_WIDTH - 195, 108)
        _draw_fog(self.surface, t)

        # Vignette
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 80))
        self.surface.blit(ov, (0, 0))

        # Title plate
        bw, bh = 720, 110
        bx, by = SCREEN_WIDTH // 2 - bw // 2, 100
        # Shadow
        sh = pygame.Surface((bw + 8, bh + 8), pygame.SRCALPHA)
        sh.fill((0, 0, 0, 140))
        self.surface.blit(sh, (bx + 6, by + 8))
        # Panel
        pn = pygame.Surface((bw, bh), pygame.SRCALPHA)
        for yy in range(bh):
            tt = yy / bh
            r = int(20 + 45 * tt)
            g = int(28 + 55 * tt)
            b = int(60 + 90 * tt)
            pygame.draw.line(pn, (r, g, b, 235), (0, yy), (bw, yy))
        pygame.draw.rect(pn, (255, 225, 80, 255), (0, 0, bw, bh), 3, border_radius=10)
        pygame.draw.line(pn, (255, 245, 160, 180), (4, 4), (bw - 5, 4), 1)
        pygame.draw.line(pn, (60, 40, 0, 200), (4, bh - 3), (bw - 5, bh - 3), 1)
        self.surface.blit(pn, (bx, by))

        # Extruded title
        bob = int(math.sin(t * 2) * 3)
        for d in range(5, 0, -1):
            shimg = self.fp_title.render("LEVEL COMPLETE", True, (60, 40, 0))
            self.surface.blit(
                shimg,
                (SCREEN_WIDTH // 2 - shimg.get_width() // 2 + d, by + 22 + bob + d),
            )
        ti = self.fp_title.render("LEVEL COMPLETE", True, C_GOLD)
        self.surface.blit(ti, (SCREEN_WIDTH // 2 - ti.get_width() // 2, by + 22 + bob))

        # Score plate
        sw, sh2 = 360, 84
        sx, sy = SCREEN_WIDTH // 2 - sw // 2, 250
        shadow = pygame.Surface((sw + 6, sh2 + 6), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 140))
        self.surface.blit(shadow, (sx + 4, sy + 6))
        sp = pygame.Surface((sw, sh2), pygame.SRCALPHA)
        for yy in range(sh2):
            tt = yy / sh2
            r = int(15 + 30 * tt)
            g = int(22 + 40 * tt)
            b = int(50 + 70 * tt)
            pygame.draw.line(sp, (r, g, b, 225), (0, yy), (sw, yy))
        pygame.draw.rect(sp, (255, 215, 80, 220), (0, 0, sw, sh2), 2, border_radius=8)
        pygame.draw.line(sp, (255, 245, 160, 160), (4, 4), (sw - 5, 4), 1)
        self.surface.blit(sp, (sx, sy))

        for d in range(3, 0, -1):
            scsh = self.fp_large.render(f"SCORE {score:07d}", True, (60, 40, 0))
            self.surface.blit(
                scsh, (SCREEN_WIDTH // 2 - scsh.get_width() // 2 + d, sy + 22 + d)
            )
        sci = self.fp_large.render(f"SCORE {score:07d}", True, C_GOLD)
        self.surface.blit(sci, (SCREEN_WIDTH // 2 - sci.get_width() // 2, sy + 22))

        for d in range(2, 0, -1):
            wsh = self.fp_small.render(f"WORLD {level_index} CLEARED", True, (0, 30, 0))
            self.surface.blit(
                wsh, (SCREEN_WIDTH // 2 - wsh.get_width() // 2 + d, sy + 58 + d)
            )
        wi = self.fp_small.render(f"WORLD {level_index} CLEARED", True, (120, 255, 120))
        self.surface.blit(wi, (SCREEN_WIDTH // 2 - wi.get_width() // 2, sy + 58))

        # Blinking prompt
        if int(t * 2) % 2 == 0:
            py2 = 400
            for d in range(3, 0, -1):
                psh = self.fp_med.render("PRESS ENTER TO CONTINUE", True, (0, 40, 0))
                self.surface.blit(
                    psh, (SCREEN_WIDTH // 2 - psh.get_width() // 2 + d, py2 + d)
                )
            pi = self.fp_med.render("PRESS ENTER TO CONTINUE", True, C_GREEN)
            self.surface.blit(pi, (SCREEN_WIDTH // 2 - pi.get_width() // 2, py2))

    def draw_game_over(self, score):
        t = self._t
        _blit_bg(self.surface)
        _draw_stars(self.surface, t)
        _blit_castle(self.surface)
        _draw_fog(self.surface, t)

        pulse = 0.5 + 0.5 * math.sin(t * 3)
        rv = int(180 + 75 * pulse)

        _center_outline(
            self.surface,
            "GAME  OVER",
            self.fp_title,
            (rv, 18, 18),
            116,
            n=2,
            sc=(58, 0, 0),
        )
        _center(self.surface, "The princess still waits...", self.fp_small, C_DIM, 218)

        _center_outline(
            self.surface,
            f"SCORE  {score:07d}",
            self.fp_large,
            C_GOLD,
            265,
            n=2,
            sc=(75, 48, 0),
        )
        _center(
            self.surface,
            "The enemy has memorized your tactics.",
            self.fp_small,
            (198, 118, 75),
            308,
        )
        if int(t * 2) % 2 == 0:
            _center_outline(
                self.surface,
                "ENTER to retry   |   ESC to quit",
                self.fp_med,
                C_CREAM,
                388,
                n=2,
                sc=C_BLACK,
            )

    def draw_win_screen(self, score):
        t = self._t
        _blit_bg(self.surface)
        _draw_stars(self.surface, t)
        _draw_moon(self.surface, SCREEN_WIDTH // 2, 105, r=68)
        _draw_fireflies(self.surface, t)
        _draw_fog(self.surface, t)

        for i in range(14):
            ang = t * 1.8 + i * math.pi / 7
            rad = 58 + 16 * math.sin(t + i)
            pygame.draw.circle(
                self.surface,
                C_GOLD,
                (
                    SCREEN_WIDTH // 2 + int(rad * math.cos(ang)),
                    118 + int(rad * math.sin(ang)),
                ),
                5 + int(2 * abs(math.sin(t * 2 + i))),
            )

        _center_outline(
            self.surface, "YOU  WIN!", self.fp_title, C_GOLD, 196, n=2, sc=(75, 48, 0)
        )

        _center(
            self.surface, "The Kingdom is Saved!", self.fp_small, (110, 245, 110), 304
        )
        _center_outline(
            self.surface,
            f"FINAL  {score:07d}",
            self.fp_large,
            C_GOLD,
            326,
            n=2,
            sc=(75, 48, 0),
        )
        _center(
            self.surface, "Enemies adapt - tougher every run!", self.fp_small, (252, 162, 65), 366
        )
        if int(t * 2) % 2 == 0:
            _center_outline(
                self.surface,
                "ENTER = Play Again   |   ESC = Menu",
                self.fp_med,
                C_GREEN,
                428,
                n=2,
                sc=(0, 55, 0),
            )
