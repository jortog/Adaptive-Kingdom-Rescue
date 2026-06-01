import pygame
from config import TILE_SIZE
import math

_FONT_CACHE = {}
def _f(size):
    if size not in _FONT_CACHE:
        _FONT_CACHE[size] = pygame.font.SysFont("Arial", size, bold=True)
    return _FONT_CACHE[size]


class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y, kind):
        super().__init__()
        self.kind = kind
        self.size = TILE_SIZE - 4
        self.rect = pygame.Rect(x, y, self.size, self.size)
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)

    def draw(self, surface, camera_offset_x, world_y_offset=0):
        rx = self.rect.x - camera_offset_x
        ry = self.rect.y + world_y_offset
        s = self.size
        pygame.draw.ellipse(surface, (0, 0, 0, 60), (rx + 2, ry + s - 6, s - 4, 6))

        if self.kind == "mushroom":
            pygame.draw.rect(surface,(240,230,210),(rx+s//4,ry+s//2,s//2,s//2),border_radius=3)
            pygame.draw.ellipse(surface,(220,40,40),(rx,ry,s,s*2//3))
            pygame.draw.ellipse(surface,(255,80,80),(rx+4,ry+4,s//4,s//5))
            pygame.draw.circle(surface,(255,255,255),(rx+s*3//4,ry+s//4),s//8)
            pygame.draw.circle(surface,(255,255,255),(rx+s//4,ry+s//3),s//10)

        elif self.kind == "flower":
            # Blue fire-flower (matches your icon): blue petals, white-blue center
            cx,cy = rx+s//2, ry+s//2-2
            for angle in range(0,360,72):
                px=cx+int(s//3*math.cos(math.radians(angle)))
                py=cy+int(s//3*math.sin(math.radians(angle)))
                pygame.draw.circle(surface,(70,150,255),(px,py),s//5)
                pygame.draw.circle(surface,(150,210,255),(px,py),s//8)
            pygame.draw.circle(surface,(240,250,255),(cx,cy),s//4)
            pygame.draw.circle(surface,(90,170,255),(cx,cy),s//7)
            # green stem
            pygame.draw.line(surface,(60,170,70),(cx,cy+s//4),(cx,ry+s-2),3)

        elif self.kind == "star":
            cx,cy = rx+s//2, ry+s//2+2
            pts=[]
            for i in range(5):
                ao=math.radians(-90+i*72); ai=math.radians(-90+i*72+36)
                pts.append((cx+s//2*math.cos(ao),cy+s//2*math.sin(ao)))
                pts.append((cx+s//4*math.cos(ai),cy+s//4*math.sin(ai)))
            pygame.draw.polygon(surface,(255,220,0),pts)
            pygame.draw.polygon(surface,(255,160,0),pts,2)

        elif self.kind == "shield":
            # Glossy 3D blue crest shield
            top = ry + 3
            outer = [
                (rx+s//2, top),(rx+s-5, top+5),(rx+s-6, ry+s//2),
                (rx+s//2, ry+s-3),(rx+6, ry+s//2),(rx+5, top+5),
            ]
            pygame.draw.polygon(surface,(60,120,225),outer)
            inner = [
                (rx+s//2, top+4),(rx+s-9, top+8),(rx+s-9, ry+s//2),
                (rx+s//2, ry+s-7),(rx+9, ry+s//2),(rx+9, top+8),
            ]
            pygame.draw.polygon(surface,(140,195,255),inner)
            gloss = [
                (rx+s//2, top+5),(rx+s//2, ry+s-9),(rx+11, ry+s//2),(rx+11, top+9),
            ]
            pygame.draw.polygon(surface,(215,238,255),gloss)
            pygame.draw.polygon(surface,(35,85,185),outer,2)

        elif self.kind == "feather":
            pygame.draw.line(surface,(220,150,50),(rx+s//2,ry+2),(rx+s//2,ry+s-2),2)
            for i in range(6):
                yo=ry+4+i*5
                pygame.draw.line(surface,(255,180,60),(rx+s//2,yo),(rx+s//2-10+i,yo-4),2)
                pygame.draw.line(surface,(255,180,60),(rx+s//2,yo),(rx+s//2+10-i,yo-4),2)

        elif self.kind == "oneup":
            pygame.draw.rect(surface,(230,240,210),(rx+s//4,ry+s//2,s//2,s//2),border_radius=3)
            pygame.draw.ellipse(surface,(40,180,40),(rx,ry,s,s*2//3))
            pygame.draw.circle(surface,(255,255,255),(rx+s*3//4,ry+s//4),s//8)
            lbl=_f(10).render("1UP",True,(0,0,0))
            surface.blit(lbl,(rx+s//2-lbl.get_width()//2,ry+s//2+4))
