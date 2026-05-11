import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, RED, GREEN, GOLD, BLACK

# HUD palette
HUD_BG   = (0,   0,   0)
HUD_GOLD = (255, 215,  0)
HUD_RED  = (220,  40,  40)
HUD_GRN  = (80,  200,  80)
HUD_WHT  = (255, 255, 255)
HUD_GRAY = (180, 180, 180)
HUD_H    = 72   # height of top HUD bar

def _draw_coin(surface, cx, cy, r=6):
    pygame.draw.circle(surface, (255,215,0), (cx, cy), r)
    pygame.draw.circle(surface, (255,240,120),(cx-1, cy-1), r-2)
    pygame.draw.circle(surface, (200,160,0), (cx, cy), r, 1)

def _draw_heart(surface, cx, cy, size=8, color=(220,40,40)):
    r = size // 2
    pygame.draw.circle(surface, color, (cx - r//2, cy - 1), r//2+1)
    pygame.draw.circle(surface, color, (cx + r//2, cy - 1), r//2+1)
    pts = [(cx - r, cy), (cx, cy + r + 1), (cx + r, cy)]
    pygame.draw.polygon(surface, color, pts)

class HUD:
    def __init__(self):
        pygame.font.init()
        self.font_label = pygame.font.SysFont("Arial", 13, bold=True)
        self.font_value = pygame.font.SysFont("Arial", 22, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 12)
        self.font_ai    = pygame.font.SysFont("Arial", 11, bold=True)

    def draw(self, surface, game_state, time_remaining, rnn_confidence):
        # ── Dark panel ─────────────────────────────────────────────
        panel = pygame.Surface((SCREEN_WIDTH, HUD_H), pygame.SRCALPHA)
        panel.fill((10, 10, 10, 210))
        surface.blit(panel, (0, 0))

        # Thin gold border at bottom of HUD
        pygame.draw.line(surface, (180,140,0), (0, HUD_H-1), (SCREEN_WIDTH, HUD_H-1), 1)

        # ── Section: RESCUER (left) ─────────────────────────────────
        lbl = self.font_label.render("RESCUER", True, HUD_GRAY)
        surface.blit(lbl, (18, 6))
        score_txt = self.font_value.render(f"{game_state.score:07d}", True, HUD_GOLD)
        surface.blit(score_txt, (12, 20))

        # ── Section: COINS ──────────────────────────────────────────
        _draw_coin(surface, 205, 14)
        pygame.draw.line(surface, HUD_WHT, (214,10),(220,10), 1)
        pygame.draw.line(surface, HUD_WHT, (214,10),(214,18), 1)
        coin_val = self.font_value.render(f"×{game_state.score // 100:02d}", True, HUD_WHT)
        surface.blit(coin_val, (222, 4))

        # ── Section: WORLD (center-left) ────────────────────────────
        wlbl = self.font_label.render("WORLD", True, HUD_GRAY)
        surface.blit(wlbl, (SCREEN_WIDTH//2 - 60, 6))
        wval = self.font_value.render(f"{game_state.level_index+1}-1", True, HUD_WHT)
        surface.blit(wval, (SCREEN_WIDTH//2 - 55, 20))

        # ── Section: LIVES (center-right) ───────────────────────────
        llbl = self.font_label.render("LIVES", True, HUD_GRAY)
        surface.blit(llbl, (SCREEN_WIDTH//2 + 20, 6))
        for i in range(min(game_state.lives, 9)):
            hx = SCREEN_WIDTH//2 + 22 + i * 16
            if hx + 14 < SCREEN_WIDTH - 120:
                _draw_heart(surface, hx, 31, size=10)
        if game_state.lives > 5:
            lv_txt = self.font_value.render(f"×{game_state.lives}", True, HUD_RED)
            surface.blit(lv_txt, (SCREEN_WIDTH//2 + 24, 20))

        # ── Section: TIME (right) ────────────────────────────────────
        tlbl = self.font_label.render("TIME", True, HUD_GRAY)
        surface.blit(tlbl, (SCREEN_WIDTH - 90, 6))
        t     = max(0, int(time_remaining))
        tcol  = (255, 60, 60) if t < 20 else HUD_WHT
        tval  = self.font_value.render(f"{t:03d}", True, tcol)
        surface.blit(tval, (SCREEN_WIDTH - 85, 20))

        # ── AI READ bar (bottom of HUD) ──────────────────────────────
        bar_w, bar_h = 260, 10
        bx = SCREEN_WIDTH // 2 - bar_w // 2
        by = HUD_H - 20

        pygame.draw.rect(surface, (40, 40, 40), (bx-1, by-1, bar_w+2, bar_h+2), border_radius=4)
        fill_w = int(bar_w * rnn_confidence)

        # Gradient fill: green → yellow → red based on confidence
        for px in range(fill_w):
            ratio = px / max(bar_w, 1)
            r = int(80  + 175 * ratio)
            g = int(200 - 150 * ratio)
            b = 40
            pygame.draw.line(surface, (r, g, b), (bx+px, by), (bx+px, by+bar_h-1))

        pygame.draw.rect(surface, (100,100,100), (bx, by, bar_w, bar_h), 1, border_radius=3)

        ai_lbl = self.font_ai.render("AI READS YOU", True, HUD_GRAY)
        surface.blit(ai_lbl, (bx + bar_w + 6, by - 1))
        pct = self.font_ai.render(f"{int(rnn_confidence*100)}%", True,
                                   (255,80,80) if rnn_confidence > 0.7 else HUD_GRAY)
        surface.blit(pct, (bx - pct.get_width() - 4, by - 1))
