import pygame
from config import SCREEN_WIDTH, ACTION_NAMES, STRAT_NAMES

_FONT_PATH = "assets/fonts/SuperPixel-m2L8j.ttf"

# Human-readable enemy response per strategy (for the AI demo overlay/log).
STRAT_RESPONSE = {
    0: "Patrolling",
    1: "Chasing player",
    2: "Flying enemy activated",
    3: "Guarding upper route",
    4: "Guarding lower route",
    5: "Ambush prepared ahead",
    6: "Backing off",
}

# Detected-pattern label that drove the chosen strategy.
STRAT_RULE = {
    0: "No strong pattern",
    1: "Player nearby",
    2: "Frequent jumping detected",
    3: "Aerial pressure / route repeat",
    4: "Route repetition detected",
    5: "Fast running detected",
    6: "Player attacking / outnumbered",
}


def ai_debug_lines(recent_actions, snapshot):
    """Build the 4 demo lines shared by the overlay and the console log."""
    recent = [ACTION_NAMES[a] for a in recent_actions[-6:] if 0 <= a < len(ACTION_NAMES)]
    pred = snapshot.get("rnn_pred_action", 0)
    pred_name = ACTION_NAMES[pred] if 0 <= pred < len(ACTION_NAMES) else "?"
    conf = snapshot.get("rnn_confidence", 0.0)
    cmd = snapshot.get("command", 0)
    return [
        ("Recent Actions:", ", ".join(recent) if recent else "(none)"),
        ("RNN Prediction:", f"{pred_name} with {conf * 100:.0f}% confidence"),
        ("Decision Tree Rule:", STRAT_RULE.get(cmd, STRAT_NAMES[cmd] if 0 <= cmd < len(STRAT_NAMES) else "?")),
        ("Enemy Response:", STRAT_RESPONSE.get(cmd, "?")),
    ]


def _pf(size):
    try:
        return pygame.font.Font(_FONT_PATH, size)
    except Exception:
        return pygame.font.SysFont("Courier New", size, bold=True)


HUD_H = 56
C_GOLD = (255, 215, 0)
C_GOLD_D = (140, 98, 0)
C_CREAM = (238, 222, 188)
C_DIM = (165, 150, 118)
C_RED = (228, 52, 52)
C_RED_D = (110, 18, 18)
C_WHITE = (255, 255, 255)
C_BLACK = (0, 0, 0)


def _heart3d(surface, cx, cy, size=11):
    pygame.draw.circle(surface, C_RED_D, (cx - size // 4, cy), size // 2 + 1)
    pygame.draw.circle(surface, C_RED_D, (cx + size // 4, cy), size // 2 + 1)
    pygame.draw.polygon(
        surface,
        C_RED_D,
        [(cx - size // 2 - 1, cy), (cx, cy + size // 2 + 2), (cx + size // 2 + 1, cy)],
    )
    pygame.draw.circle(surface, C_RED, (cx - size // 4, cy - 1), size // 2)
    pygame.draw.circle(surface, C_RED, (cx + size // 4, cy - 1), size // 2)
    pygame.draw.polygon(
        surface,
        C_RED,
        [(cx - size // 2, cy - 1), (cx, cy + size // 2), (cx + size // 2, cy - 1)],
    )
    pygame.draw.circle(surface, (255, 180, 180), (cx - size // 4 - 1, cy - 3), 2)


def _text3d(surface, text, font, col, shadow_col, x, y, depth=2):
    for d in range(depth, 0, -1):
        surface.blit(font.render(text, True, shadow_col), (x + d, y + d))
    surface.blit(font.render(text, True, col), (x, y))


def _clamp01(value):
    return max(0.0, min(float(value), 1.0))


class HUD:
    def __init__(self):
        pygame.font.init()
        self.fp_val = _pf(18)
        self.fp_lbl = _pf(9)
        self.time_font = pygame.font.SysFont("Courier New", 23, bold=True)
        self.ai_lbl = pygame.font.SysFont("Courier New", 13, bold=True)
        self.ai_val = pygame.font.SysFont("Courier New", 13)

    def draw(self, surface, gs, time_remaining, level_progress):
        # Panel
        panel = pygame.Surface((SCREEN_WIDTH, HUD_H), pygame.SRCALPHA)
        for y in range(HUD_H):
            t = y / HUD_H
            r = int(8 + 12 * t)
            g = int(12 + 18 * t)
            b = int(28 + 32 * t)
            pygame.draw.line(panel, (r, g, b, 235), (0, y), (SCREEN_WIDTH, y))
        surface.blit(panel, (0, 0))
        pygame.draw.line(surface, (255, 235, 120), (0, 0), (SCREEN_WIDTH, 0), 1)
        pygame.draw.line(surface, (180, 140, 0), (0, 2), (SCREEN_WIDTH, 2), 1)
        pygame.draw.line(
            surface, (50, 38, 18), (0, HUD_H - 2), (SCREEN_WIDTH, HUD_H - 2), 1
        )
        pygame.draw.line(
            surface, (0, 0, 0), (0, HUD_H - 1), (SCREEN_WIDTH, HUD_H - 1), 1
        )

        # SCORE (left)
        _text3d(surface, "SCORE", self.fp_lbl, C_DIM, C_BLACK, 14, 5)
        _text3d(surface, f"{gs.score:07d}", self.fp_val, C_GOLD, C_GOLD_D, 12, 16)

        # LEVEL (center)
        wlbl = self.fp_lbl.render("LEVEL", True, C_DIM)
        _text3d(
            surface,
            "LEVEL",
            self.fp_lbl,
            C_DIM,
            C_BLACK,
            SCREEN_WIDTH // 2 - wlbl.get_width() // 2,
            5,
        )
        lv = f"{gs.level_index + 1}"
        wval = self.fp_val.render(lv, True, C_CREAM)
        _text3d(
            surface,
            lv,
            self.fp_val,
            C_CREAM,
            (60, 50, 30),
            SCREEN_WIDTH // 2 - wval.get_width() // 2,
            16,
        )

        # LIVES
        lx = SCREEN_WIDTH // 2 + 118
        _text3d(surface, "LIVES", self.fp_lbl, C_DIM, C_BLACK, lx, 5)
        for i in range(min(gs.lives, 5)):
            _heart3d(surface, lx + i * 18, 30, size=11)
        if gs.lives > 5:
            _text3d(
                surface, f"+{gs.lives - 5}", self.fp_lbl, C_RED, C_BLACK, lx + 92, 24
            )

        # TIME (right)
        time_label = self.fp_lbl.render("TIME", True, C_DIM)
        time_label_x = SCREEN_WIDTH - time_label.get_width() - 18
        _text3d(surface, "TIME", self.fp_lbl, C_DIM, C_BLACK, time_label_x, 5)
        total_seconds = max(0, int(time_remaining))
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        tcol = (
            C_RED
            if total_seconds < 20
            else (255, 165, 40)
            if total_seconds < 40
            else C_CREAM
        )
        tsh = (
            C_RED_D
            if total_seconds < 20
            else (110, 75, 0)
            if total_seconds < 40
            else (60, 50, 30)
        )
        time_text = f"{minutes}:{seconds:02d}"
        time_img = self.time_font.render(time_text, True, tcol)
        time_box = pygame.Rect(SCREEN_WIDTH - 82, 17, 64, 25)
        pygame.draw.rect(surface, (3, 5, 14, 160), time_box, border_radius=3)
        _text3d(
            surface,
            time_text,
            self.time_font,
            tcol,
            tsh,
            time_box.right - time_img.get_width() - 4,
            time_box.y - 1,
        )

        # Level progress bar
        bw, bh = 200, 5
        bx = SCREEN_WIDTH // 2 - bw // 2
        by = HUD_H - 10
        pygame.draw.rect(
            surface, (0, 0, 0), (bx - 1, by - 1, bw + 2, bh + 2), border_radius=2
        )
        progress = _clamp01(level_progress)
        fw = int(bw * progress)
        if fw > 0:
            fill = pygame.Rect(bx, by, fw, bh)
            pygame.draw.rect(surface, (70, 210, 90), fill, border_radius=2)
            pygame.draw.rect(surface, C_GOLD, (bx, by, min(fw, 5), bh), border_radius=2)
        pygame.draw.line(surface, (255, 255, 255, 90), (bx, by), (bx + bw, by), 1)

    def draw_ai_debug(self, surface, recent_actions, snapshot):
        """Translucent panel showing the live AI decision (toggle with F1)."""
        lines = ai_debug_lines(recent_actions, snapshot)
        pad = 8
        lh = 18
        w = 430
        h = pad * 2 + lh * (len(lines) + 1)
        x, y = 12, HUD_H + 10
        panel = pygame.Surface((w, h), pygame.SRCALPHA)
        panel.fill((6, 10, 22, 205))
        pygame.draw.rect(panel, (90, 150, 230), panel.get_rect(), 1)
        surface.blit(panel, (x, y))
        ty = y + pad
        surface.blit(self.ai_lbl.render("AI DEBUG  [F1]", True, (120, 200, 120)), (x + pad, ty))
        ty += lh
        for label, value in lines:
            surface.blit(self.ai_lbl.render(label, True, (150, 180, 220)), (x + pad, ty))
            surface.blit(self.ai_val.render(value, True, C_WHITE), (x + pad + 150, ty))
            ty += lh
