import pygame
from config import TILE_SIZE

class Princess(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.rect  = pygame.Rect(x, y, TILE_SIZE - 4, TILE_SIZE + 4)
        self.image = pygame.Surface((TILE_SIZE-4, TILE_SIZE+4), pygame.SRCALPHA)
        self._bob  = 0.0

    def update_bob(self, dt):
        self._bob += dt * 2.5

    def draw(self, surface, camera_offset_x):
        import math
        rx = self.rect.x - camera_offset_x
        ry = self.rect.y + int(math.sin(self._bob) * 3)
        w, h = self.rect.width, self.rect.height

        # Dress (pink triangle)
        dress_pts = [(rx+w//2, ry+h-2), (rx+2, ry+h//2), (rx+w-2, ry+h//2)]
        pygame.draw.polygon(surface, (255,105,180), dress_pts)
        pygame.draw.polygon(surface, (220, 60,150), dress_pts, 2)
        # Dress highlight
        pygame.draw.polygon(surface, (255,160,210),
                            [(rx+w//2, ry+h-10),(rx+10, ry+h//2+4),(rx+w//2, ry+h//2+2)])

        # Body
        pygame.draw.rect(surface, (255,140,180),
                         (rx+w//4, ry+h//3, w//2, h//4), border_radius=3)

        # Arms
        pygame.draw.line(surface, (255,200,150), (rx+w//4, ry+h//3+4), (rx+2, ry+h//2), 4)
        pygame.draw.line(surface, (255,200,150), (rx+3*w//4, ry+h//3+4), (rx+w-2, ry+h//2), 4)

        # Head
        cx, cy = rx+w//2, ry+h//5
        pygame.draw.circle(surface, (255,210,170), (cx, cy), h//7+2)

        # Hair
        pygame.draw.ellipse(surface, (220,180,100), (cx-h//7-2, cy-4, h//7*2+4, h//7+4))
        pygame.draw.ellipse(surface, (220,180,100), (cx-h//7, cy+2, 8, 10))
        pygame.draw.ellipse(surface, (220,180,100), (cx+h//7-8, cy+2, 8, 10))

        # Eyes
        pygame.draw.circle(surface, (0,0,0), (cx-4, cy), 2)
        pygame.draw.circle(surface, (0,0,0), (cx+4, cy), 2)
        pygame.draw.circle(surface, (255,255,255), (cx-3, cy-1), 1)
        pygame.draw.circle(surface, (255,255,255), (cx+5, cy-1), 1)
        # Smile
        pygame.draw.arc(surface, (180,60,60),
                        (cx-4, cy+2, 8, 5), 3.6, 5.8, 1)

        # Crown
        crown_pts = [
            (cx-8, cy-h//7-2), (cx-8, cy-h//7-8),
            (cx-4, cy-h//7-5), (cx,   cy-h//7-10),
            (cx+4, cy-h//7-5), (cx+8, cy-h//7-8),
            (cx+8, cy-h//7-2),
        ]
        pygame.draw.polygon(surface, (255,215,0), crown_pts)
        pygame.draw.polygon(surface, (200,160,0), crown_pts, 1)
        # Crown gems
        pygame.draw.circle(surface, (255,80,80),  (cx, cy-h//7-9), 2)
        pygame.draw.circle(surface, (80,180,255), (cx-6, cy-h//7-6), 2)
        pygame.draw.circle(surface, (80,180,255), (cx+6, cy-h//7-6), 2)

        # Sparkles around princess
        import time
        t = time.time()
        for i, (ox, oy) in enumerate([(rx-8,ry+4),(rx+w+4,ry+8),(rx+w//2,ry-8)]):
            if int(t*3 + i) % 2 == 0:
                pygame.draw.circle(surface, (255,255,180), (ox, oy), 3)
                pygame.draw.circle(surface, (255,220,0),   (ox, oy), 1)