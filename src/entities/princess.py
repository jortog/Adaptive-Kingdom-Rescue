import pygame
import math
import time
from config import TILE_SIZE

class Princess(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # Keep collision box one tile tall, aligned to ground like before
        self.rect  = pygame.Rect(x, y, TILE_SIZE - 4, TILE_SIZE)
        self.image = pygame.Surface((TILE_SIZE-4, TILE_SIZE), pygame.SRCALPHA)
        self._bob  = 0.0

    def update_bob(self, dt):
        self._bob += dt * 2.5

    def draw(self, surface, camera_offset_x):
        # Draw region is taller than collision box; anchor sprite bottom to rect bottom
        DRAW_H = TILE_SIZE + 14
        rx = self.rect.x - camera_offset_x
        ry = self.rect.bottom - DRAW_H + int(math.sin(self._bob)*2)
        w  = self.rect.width
        h  = DRAW_H
        cx = rx + w//2

        robe_d=(24,52,120); robe_m=(40,80,170); robe_l=(70,120,215)
        gold=(235,190,60); gold_l=(255,225,130)
        skin=(250,215,180); hair=(40,32,28); gem=(90,210,235)

        robe=[(cx,ry+h//4),(cx-w//2+4,ry+h-2),(cx+w//2-4,ry+h-2)]
        pygame.draw.polygon(surface,robe_d,robe)
        inner=[(cx,ry+h//4+4),(cx-w//2+9,ry+h-4),(cx+w//2-9,ry+h-4)]
        pygame.draw.polygon(surface,robe_m,inner)
        pygame.draw.line(surface,gold,(cx,ry+h//3),(cx,ry+h-4),3)
        pygame.draw.polygon(surface,gold,[(cx,ry+h-14),(cx-5,ry+h-4),(cx+5,ry+h-4)])
        pygame.draw.line(surface,robe_l,(cx-3,ry+h//3),(cx-w//2+10,ry+h-6),2)

        pygame.draw.rect(surface,gold,(cx-13,ry+h//4,26,7),border_radius=3)
        pygame.draw.rect(surface,gold_l,(cx-13,ry+h//4,26,3),border_radius=3)

        pygame.draw.polygon(surface,robe_m,[(cx-12,ry+h//4+2),(cx-16,ry+h//2+6),(cx-8,ry+h//2)])
        pygame.draw.polygon(surface,robe_m,[(cx+12,ry+h//4+2),(cx+16,ry+h//2+6),(cx+8,ry+h//2)])
        pygame.draw.circle(surface,skin,(cx-13,ry+h//2+5),3)
        pygame.draw.circle(surface,skin,(cx+13,ry+h//2+5),3)

        pygame.draw.line(surface,gold,(cx+15,ry+h//4),(cx+15,ry+h//2+8),2)
        pygame.draw.circle(surface,gold_l,(cx+15,ry+h//4-2),4)
        pygame.draw.circle(surface,gem,(cx+15,ry+h//4-2),2)

        ny=ry+h//5
        pygame.draw.rect(surface,skin,(cx-3,ny+6,6,6))
        pygame.draw.circle(surface,skin,(cx,ny),h//8+2)

        pygame.draw.ellipse(surface,hair,(cx-h//8-3,ny-6,(h//8+3)*2,h//8+8))
        pygame.draw.circle(surface,skin,(cx,ny+1),h//8)
        pygame.draw.rect(surface,hair,(cx-h//8-2,ny,4,h//4))
        pygame.draw.rect(surface,hair,(cx+h//8-2,ny,4,h//4))

        pygame.draw.circle(surface,(40,40,50),(cx-3,ny),1)
        pygame.draw.circle(surface,(40,40,50),(cx+3,ny),1)
        pygame.draw.arc(surface,(190,90,90),(cx-3,ny+2,6,4),3.6,5.8,1)

        cyt=ny-h//8-4
        crown=[(cx-9,cyt+4),(cx-9,cyt-2),(cx-5,cyt+1),(cx,cyt-6),(cx+5,cyt+1),(cx+9,cyt-2),(cx+9,cyt+4)]
        pygame.draw.polygon(surface,gold,crown)
        pygame.draw.polygon(surface,gold_l,crown,1)
        pygame.draw.circle(surface,gem,(cx,cyt-3),2)
        pygame.draw.circle(surface,(255,120,120),(cx-6,cyt),1)
        pygame.draw.circle(surface,(255,120,120),(cx+6,cyt),1)

        t=time.time()
        for i,(ox,oy) in enumerate([(rx-6,ry+8),(rx+w+2,ry+12),(cx,ry-6)]):
            if int(t*3+i)%2==0:
                pygame.draw.circle(surface,(255,255,190),(ox,oy),3)
                pygame.draw.circle(surface,(255,225,70),(ox,oy),1)
