import pygame
from config import TILE_SIZE

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y, kind):
        super().__init__()
        self.kind  = kind
        self.size  = TILE_SIZE - 4
        self.rect  = pygame.Rect(x, y, self.size, self.size)
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)

    def draw(self, surface, camera_offset_x):
        rx = self.rect.x - camera_offset_x
        ry = self.rect.y
        s  = self.size
        k  = self.kind
        # Shadow
        shadow = pygame.Surface((s, s), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0,0,0,60), (2, s-6, s-4, 6))
        surface.blit(shadow, (rx, ry))

        if k == "mushroom":
            # White stem
            pygame.draw.rect(surface, (240,230,210), (rx+s//4, ry+s//2, s//2, s//2), border_radius=3)
            pygame.draw.line(surface, (180,170,150), (rx+s//4, ry+s//2), (rx+s//4, ry+s-2), 1)
            # Red cap
            pygame.draw.ellipse(surface, (220,40,40), (rx, ry, s, s*2//3))
            pygame.draw.ellipse(surface, (255,80,80), (rx+4, ry+4, s//4, s//5))
            pygame.draw.circle(surface, (255,255,255), (rx+s*3//4, ry+s//4), s//8)
            pygame.draw.circle(surface, (255,255,255), (rx+s//4, ry+s//3), s//10)

        elif k == "flower":
            # Petals
            petal_col = (255,180,20)
            cx, cy = rx+s//2, ry+s//2
            for angle in range(0, 360, 60):
                import math
                px = cx + int(s//3 * math.cos(math.radians(angle)))
                py = cy + int(s//3 * math.sin(math.radians(angle)))
                pygame.draw.circle(surface, petal_col, (px, py), s//5)
            pygame.draw.circle(surface, (255,60,60),  (cx, cy), s//4)
            pygame.draw.circle(surface, (255,120,120),(cx-2, cy-2), s//8)

        elif k == "star":
            import math
            cx, cy = rx+s//2, ry+s//2+2
            pts_outer, pts_inner = [], []
            for i in range(5):
                a_o = math.radians(-90 + i*72)
                a_i = math.radians(-90 + i*72 + 36)
                pts_outer.append((cx + s//2*math.cos(a_o), cy + s//2*math.sin(a_o)))
                pts_inner.append((cx + s//4*math.cos(a_i), cy + s//4*math.sin(a_i)))
            star_pts = []
            for o, i in zip(pts_outer, pts_inner):
                star_pts.extend([o, i])
            pygame.draw.polygon(surface, (255,220,0), star_pts)
            pygame.draw.polygon(surface, (255,160,0), star_pts, 2)
            pygame.draw.circle(surface, (255,240,150),(cx-2, cy-2), 4)

        elif k == "shield":
            pts = [(rx+s//2, ry+2), (rx+s-4, ry+s//3),
                   (rx+s//2, ry+s-2), (rx+4, ry+s//3)]
            pygame.draw.polygon(surface, (60,120,220),  pts)
            pygame.draw.polygon(surface, (100,180,255), pts, 2)
            pygame.draw.line(surface, (180,220,255), (rx+s//2, ry+8), (rx+s//2, ry+s-8), 2)
            pygame.draw.line(surface, (180,220,255), (rx+s//4+2, ry+s//3), (rx+3*s//4-2, ry+s//3), 2)

        elif k == "feather":
            # Feather quill
            pygame.draw.line(surface, (220,150,50), (rx+s//2, ry+2), (rx+s//2, ry+s-2), 2)
            for i in range(6):
                y_off = ry + 4 + i*5
                pygame.draw.line(surface, (255,180,60), (rx+s//2, y_off), (rx+s//2-10+i, y_off-4), 2)
                pygame.draw.line(surface, (255,180,60), (rx+s//2, y_off), (rx+s//2+10-i, y_off-4), 2)

        elif k == "oneup":
            # Green mushroom
            pygame.draw.rect(surface, (230,240,210), (rx+s//4, ry+s//2, s//2, s//2), border_radius=3)
            pygame.draw.ellipse(surface, (40,180,40),  (rx, ry, s, s*2//3))
            pygame.draw.ellipse(surface, (80,220,80),  (rx+4, ry+4, s//4, s//5))
            pygame.draw.circle(surface, (255,255,255), (rx+s*3//4, ry+s//4), s//8)
            pygame.draw.circle(surface, (255,255,255), (rx+s//4, ry+s//3), s//10)
            font = pygame.font.SysFont("Arial", 10, bold=True)
            lbl  = font.render("1UP", True, (0,0,0))
            surface.blit(lbl, (rx+s//2-lbl.get_width()//2, ry+s//2+4))