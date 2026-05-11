import pygame
import math
from config import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, GOLD, RED, GREEN, YELLOW, SKY_BLUE, BLACK

class ScreenManager:
    def __init__(self, surface):
        self.surface = surface
        pygame.font.init()
        self.font_title = pygame.font.SysFont("Arial", 68, bold=True)
        self.font_sub   = pygame.font.SysFont("Arial", 26, bold=True)
        self.font_large = pygame.font.SysFont("Arial", 36, bold=True)
        self.font_med   = pygame.font.SysFont("Arial", 22)
        self.font_small = pygame.font.SysFont("Arial", 16)
        self._t = 0.0

    def tick(self, dt):
        self._t += dt

    def _center(self, text, font, color, y, shadow=True):
        if shadow:
            s = font.render(text, True, (0,0,0))
            self.surface.blit(s, (SCREEN_WIDTH//2 - s.get_width()//2 + 2, y + 2))
        img = font.render(text, True, color)
        self.surface.blit(img, (SCREEN_WIDTH//2 - img.get_width()//2, y))

    def _draw_block_row(self, y, color=(181,80,40), count=27):
        bw = SCREEN_WIDTH // count
        for i in range(count):
            bx = i * bw
            pygame.draw.rect(self.surface, color, (bx, y, bw-1, 28))
            pygame.draw.rect(self.surface, (220,120,70), (bx, y, bw-1, 6))
            pygame.draw.rect(self.surface, (130,52,18), (bx, y, bw-1, 28), 1)

    def _draw_stars(self, count=30):
        import random
        random.seed(42)
        for _ in range(count):
            sx = random.randint(0, SCREEN_WIDTH)
            sy = random.randint(0, SCREEN_HEIGHT)
            r  = random.randint(1, 3)
            a  = abs(math.sin(self._t * 2 + sx * 0.1))
            col = (int(255*a), int(255*a), int(200*a))
            pygame.draw.circle(self.surface, col, (sx, sy), r)

    def draw_main_menu(self):
        # Sky gradient
        self.surface.fill((70, 120, 220))
        for y in range(SCREEN_HEIGHT):
            ratio = y / SCREEN_HEIGHT
            r = int(70  + 65  * ratio)
            g = int(120 + 86  * ratio)
            b = int(220 + 15  * ratio)
            pygame.draw.line(self.surface, (r,g,b), (0,y), (SCREEN_WIDTH,y))

        # Clouds
        for cx, cy in [(150,80),(400,55),(700,90),(1000,65),(1200,80)]:
            for ox, oy, rw, rh in [(0,14,80,32),(18,0,52,38),(48,10,60,30)]:
                pygame.draw.ellipse(self.surface, (255,255,255), (cx+ox, cy+oy, rw, rh))

        # Ground block row at bottom
        self._draw_block_row(SCREEN_HEIGHT - 56, (106,191,75))
        self._draw_block_row(SCREEN_HEIGHT - 30, (181,101,29))

        # Title (with glow effect)
        glow_col = (255, 180, 0) if int(self._t * 2) % 2 == 0 else (255, 220, 80)
        self._center("ADAPTIVE KINGDOM RESCUE", self.font_title, glow_col, 95)
        self._center("~ Super Enemy of Mario ~", self.font_med, (255,255,200), 182)

        # Blinking ENTER prompt
        if int(self._t * 2) % 2 == 0:
            self._center("PRESS  ENTER  TO START", self.font_large, (80,255,80), 310)
        else:
            self._center("PRESS  ENTER  TO START", self.font_large, (50,200,50), 310)

        self._center("ESC to quit", self.font_small, (200,200,200), 365, shadow=False)

        # Info panel
        info_surf = pygame.Surface((460, 54), pygame.SRCALPHA)
        info_surf.fill((0,0,0,130))
        pygame.draw.rect(info_surf, (200,160,0), (0,0,460,54), 2, border_radius=6)
        self.surface.blit(info_surf, (SCREEN_WIDTH//2-230, 415))
        self._center("AI: Decision Tree  +  RNN/LSTM  +  PPO", self.font_small, (255,220,80), 424)
        self._center("PUP CCIS  ·  COSC 304  ·  Group 1", self.font_small, (180,180,180), 444)

    def draw_level_complete(self, score, level_index):
        self.surface.fill((20, 50, 20))
        self._draw_stars(20)
        self._draw_block_row(SCREEN_HEIGHT - 40)

        self._center("LEVEL COMPLETE!", self.font_title, (255,220,0), 100)
        self._center(f"World {level_index} cleared!", self.font_sub, (100,255,100), 195)

        # Score box
        box = pygame.Surface((340,90), pygame.SRCALPHA)
        box.fill((0,0,0,160))
        pygame.draw.rect(box, (200,160,0), (0,0,340,90), 2, border_radius=8)
        self.surface.blit(box, (SCREEN_WIDTH//2-170, 240))
        self._center(f"SCORE  {score:07d}", self.font_large, (255,215,0), 256)
        self._center("Princess rescued!", self.font_med, (255,160,200), 298)

        if int(self._t * 2) % 2 == 0:
            self._center("PRESS  ENTER  TO CONTINUE", self.font_large, (80,255,80), 375)
        self._center("The enemy army is learning your moves...", self.font_small, (255,100,100), 430)

    def draw_game_over(self, score):
        self.surface.fill((40,5,5))
        self._draw_stars(40)

        # Pulsing red title
        pulse = abs(math.sin(self._t * 3))
        r = int(180 + 75 * pulse)
        self._center("GAME  OVER", self.font_title, (r, 20, 20), 110)
        self._center("The princess still waits...", self.font_sub, (200,150,150), 205)

        box = pygame.Surface((360, 90), pygame.SRCALPHA)
        box.fill((0,0,0,160))
        pygame.draw.rect(box, (160,40,40), (0,0,360,90), 2, border_radius=8)
        self.surface.blit(box, (SCREEN_WIDTH//2-180, 255))
        self._center(f"SCORE  {score:07d}", self.font_large, (255,215,0), 268)
        self._center("The enemy has memorized your tactics.", self.font_small, (255,180,100), 308)

        self._draw_block_row(SCREEN_HEIGHT - 40)
        if int(self._t * 2) % 2 == 0:
            self._center("ENTER to retry   |   ESC to quit", self.font_large, (255,255,255), 390)

    def draw_win_screen(self, score):
        self.surface.fill((10,10,60))
        self._draw_stars(60)

        self._center("YOU  WIN!", self.font_title, (255,220,0), 90)
        self._center("The Kingdom is saved!", self.font_sub, (100,255,100), 190)

        box = pygame.Surface((400,110), pygame.SRCALPHA)
        box.fill((0,0,0,170))
        pygame.draw.rect(box, (180,140,0), (0,0,400,110), 2, border_radius=8)
        self.surface.blit(box, (SCREEN_WIDTH//2-200, 240))
        self._center(f"FINAL SCORE  {score:07d}", self.font_large, (255,215,0), 254)
        self._center("Challenge Mode Unlocked!", self.font_sub, (255,160,80), 294)

        if int(self._t * 2) % 2 == 0:
            self._center("ENTER = Challenge   |   ESC = Menu", self.font_large, (80,255,80), 390)

    def draw_pause(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.surface.blit(overlay, (0, 0))
        box = pygame.Surface((380, 140), pygame.SRCALPHA)
        box.fill((20,20,20,220))
        pygame.draw.rect(box, (180,140,0), (0,0,380,140), 2, border_radius=10)
        self.surface.blit(box, (SCREEN_WIDTH//2-190, SCREEN_HEIGHT//2-80))
        self._center("PAUSED", self.font_title, (255,255,255), SCREEN_HEIGHT//2-72)
        self._center("Press  P  to resume", self.font_large, (80,255,80), SCREEN_HEIGHT//2+14)
