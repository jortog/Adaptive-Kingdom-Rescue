import pygame
from config import (
    ENEMY_GROUND_WIDTH, ENEMY_GROUND_HEIGHT,
    ENEMY_FLYING_WIDTH, ENEMY_FLYING_HEIGHT,
    ENEMY_PATROL_SPEED, ENEMY_CHASE_SPEED,
    GRAVITY, TILE_SIZE,
    STRAT_PATROL, STRAT_CHASE, STRAT_AMBUSH, STRAT_RETREAT,
    STRAT_BLOCK_UPPER, STRAT_BLOCK_LOWER
)

_FONT       = None
_LBL_CACHE  = {}

def _font():
    global _FONT
    if _FONT is None:
        _FONT = pygame.font.SysFont("Arial", 11, bold=True)
    return _FONT

def _badge_label(state):
    if state not in _LBL_CACHE:
        _LBL_CACHE[state] = _font().render(state[:3].upper(), True, (255,255,255))
    return _LBL_CACHE[state]

BADGE_COL = {
    "patrol": (100,100,100), "chase":   (210,40,40),
    "ambush": (190,95,0),    "retreat": (40,90,200), "block": (90,40,190),
}


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, enemy_type="ground", patrol_left=None, patrol_right=None):
        super().__init__()
        self.enemy_type = enemy_type
        if enemy_type == "flying":
            w, h = ENEMY_FLYING_WIDTH, ENEMY_FLYING_HEIGHT
            self.affected_by_gravity = False
        else:
            w, h = ENEMY_GROUND_WIDTH, ENEMY_GROUND_HEIGHT
            self.affected_by_gravity = True
        self.rect  = pygame.Rect(x, y, w, h)
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        self.vel_x = -ENEMY_PATROL_SPEED
        self.vel_y = 0.0
        self.patrol_left  = patrol_left  if patrol_left  else x - 3*TILE_SIZE
        self.patrol_right = patrol_right if patrol_right else x + 3*TILE_SIZE
        self.state     = "patrol"
        self.alive     = True
        self.on_ground = False
        self.current_command = STRAT_PATROL

    def set_command(self, command):
        self.current_command = command
        state_map = {
            STRAT_PATROL:"patrol", STRAT_CHASE:"chase",
            STRAT_AMBUSH:"ambush", STRAT_RETREAT:"retreat",
            STRAT_BLOCK_UPPER:"block", STRAT_BLOCK_LOWER:"block",
        }
        self.state = state_map.get(command, "patrol")

    def update(self, dt, player_rect, platforms):
        if not self.alive:
            return
        if self.state == "patrol":
            self.rect.x += int(self.vel_x * dt)
        elif self.state == "chase":
            d = 1 if player_rect.centerx > self.rect.centerx else -1
            self.vel_x = ENEMY_CHASE_SPEED * d
            self.rect.x += int(self.vel_x * dt)
        elif self.state == "ambush":
            d = 1 if player_rect.centerx > self.rect.centerx else -1
            self.vel_x = ENEMY_CHASE_SPEED * 1.3 * d
            self.rect.x += int(self.vel_x * dt)
            if self.enemy_type == "flying":
                ty = player_rect.top - self.rect.height - TILE_SIZE
                self.rect.y += int((ty - self.rect.y) * 4.0 * dt)
        elif self.state == "retreat":
            d = -1 if player_rect.centerx > self.rect.centerx else 1
            self.vel_x = ENEMY_PATROL_SPEED * d
            self.rect.x += int(self.vel_x * dt)
        elif self.state == "block":
            self.vel_x = 0
        if self.affected_by_gravity:
            if not self.on_ground:
                self.vel_y += GRAVITY * dt
                self.vel_y  = min(self.vel_y, 1200)
            self.on_ground = False
            self.rect.y   += int(self.vel_y * (1/60))
            for p in platforms:
                if self.rect.colliderect(p) and self.vel_y >= 0:
                    self.rect.bottom = p.top
                    self.on_ground   = True
                    self.vel_y       = 0
        if self.state == "patrol":
            if self.rect.left  < self.patrol_left:   self.vel_x =  ENEMY_PATROL_SPEED
            elif self.rect.right > self.patrol_right: self.vel_x = -ENEMY_PATROL_SPEED

    def die(self):
        self.alive = False
        self.kill()

    def draw(self, surface, camera_offset_x):
        if not self.alive:
            return
        rx = self.rect.x - camera_offset_x
        ry = self.rect.y
        w, h = self.rect.width, self.rect.height
        if self.enemy_type == "ground":
            pygame.draw.ellipse(surface,(55,28,5),(rx-3,ry+h-10,w//2+4,11))
            pygame.draw.ellipse(surface,(55,28,5),(rx+w//2-3,ry+h-10,w//2+4,11))
            pygame.draw.rect(surface,(160,105,42),(rx+3,ry+h//3,w-6,2*h//3),border_radius=5)
            pygame.draw.rect(surface,(200,145,75),(rx+5,ry+h//3+3,w-10,8),border_radius=3)
            pygame.draw.ellipse(surface,(115,62,18),(rx,ry,w,h*2//3+6))
            pygame.draw.ellipse(surface,(170,105,48),(rx+5,ry+h//4,w-10,h//2))
            ey = ry+h*2//5
            for ex in (rx+w//3, rx+2*w//3):
                pygame.draw.circle(surface,(255,255,255),(ex,ey),5)
                pygame.draw.circle(surface,(0,0,0),(ex,ey+1),3)
            pygame.draw.line(surface,(40,18,0),(rx+w//3-6,ey-8),(rx+w//3+5,ey-4),2)
            pygame.draw.line(surface,(40,18,0),(rx+2*w//3-5,ey-4),(rx+2*w//3+6,ey-8),2)
        else:
            pygame.draw.polygon(surface,(255,255,200),[(rx-18,ry+h//2),(rx-2,ry+3),(rx+8,ry+h//2)])
            pygame.draw.polygon(surface,(255,255,200),[(rx+w+18,ry+h//2),(rx+w+2,ry+3),(rx+w-8,ry+h//2)])
            pygame.draw.polygon(surface,(200,200,140),[(rx-18,ry+h//2),(rx-2,ry+3),(rx+8,ry+h//2)],1)
            pygame.draw.polygon(surface,(200,200,140),[(rx+w+18,ry+h//2),(rx+w+2,ry+3),(rx+w-8,ry+h//2)],1)
            pygame.draw.ellipse(surface,(45,140,45),(rx,ry+h//3,w,2*h//3+2))
            pygame.draw.ellipse(surface,(80,195,80),(rx+4,ry+h//3+4,w-8,2*h//3-6))
            pygame.draw.circle(surface,(45,140,45),(rx+w//2,ry+h//2+h//6),h//5)
            pygame.draw.ellipse(surface,(200,220,90),(rx+w//4,ry,w//2,h//2+4))
            pygame.draw.circle(surface,(0,0,0),(rx+w//2+3,ry+h//5),3)
            pygame.draw.circle(surface,(255,255,255),(rx+w//2+2,ry+h//5-1),1)
        bcol = BADGE_COL.get(self.state,(100,100,100))
        lbl  = _badge_label(self.state)
        bx   = rx + w//2 - lbl.get_width()//2
        pygame.draw.rect(surface, bcol,(bx-2,ry-16,lbl.get_width()+4,14),border_radius=3)
        surface.blit(lbl,(bx,ry-15))
