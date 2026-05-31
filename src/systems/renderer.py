import pygame
import math
from config import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE

# Current theme — set by load_level via set_theme()
_theme = "night"

# Three full theme palettes
THEMES = {
    "night": {
        "sky_top":(14,18,48),"sky_mid":(28,34,78),"sky_bot":(52,58,104),
        "hill_far_l":(34,46,86),"hill_far_d":(24,34,68),
        "hill_mid_l":(30,54,70),"hill_mid_d":(20,40,54),"hill_mid_s":(46,78,92),
        "bush_l":(28,60,46),"bush_d":(18,44,34),"bush_s":(44,86,62),
        "grass_t":(54,120,70),"grass_t2":(74,148,92),"grass_d":(34,84,48),
        "dirt_m":(96,66,40),"dirt_l":(120,86,54),"dirt_d":(64,42,24),
        "brick_m":(110,60,46),"brick_h":(150,88,66),"brick_d":(70,38,26),
        "accent":(255,238,180),"star_count":90,
    },
    "storm": {
        "sky_top":(28,28,52),"sky_mid":(60,55,80),"sky_bot":(95,90,115),
        "hill_far_l":(80,72,95),"hill_far_d":(50,46,68),
        "hill_mid_l":(95,90,108),"hill_mid_d":(58,55,75),"hill_mid_s":(120,115,135),
        "bush_l":(75,90,75),"bush_d":(45,58,48),"bush_s":(105,125,105),
        "grass_t":(95,110,80),"grass_t2":(120,135,100),"grass_d":(60,75,52),
        "dirt_m":(85,82,75),"dirt_l":(110,108,100),"dirt_d":(58,55,50),
        "brick_m":(95,95,110),"brick_h":(135,135,150),"brick_d":(60,60,72),
        "accent":(220,220,255),"star_count":30,
    },
    "volcano": {
        "sky_top":(48,8,20),"sky_mid":(110,30,30),"sky_bot":(178,72,40),
        "hill_far_l":(95,40,30),"hill_far_d":(60,22,18),
        "hill_mid_l":(115,55,38),"hill_mid_d":(70,28,20),"hill_mid_s":(160,75,40),
        "bush_l":(80,40,30),"bush_d":(50,22,18),"bush_s":(180,80,30),
        "grass_t":(140,70,30),"grass_t2":(190,100,40),"grass_d":(80,38,18),
        "dirt_m":(110,55,32),"dirt_l":(150,80,45),"dirt_d":(70,32,18),
        "brick_m":(140,52,32),"brick_h":(200,90,55),"brick_d":(80,28,18),
        "accent":(255,180,90),"star_count":0,
    },
}

_sky_surf=None; _tile_cache={}; _cloud_cache=None

def set_theme(name):
    global _theme, _sky_surf, _tile_cache, _cloud_cache
    if name in THEMES and name != _theme:
        _theme = name
        _sky_surf = None
        _tile_cache = {}
        _cloud_cache = None

def _t():
    return THEMES[_theme]

def _build_sky():
    th=_t()
    surf=pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT))
    for y in range(SCREEN_HEIGHT):
        tt=y/SCREEN_HEIGHT
        if tt<0.55:
            k=tt/0.55
            r=int(th["sky_top"][0]+(th["sky_mid"][0]-th["sky_top"][0])*k)
            g=int(th["sky_top"][1]+(th["sky_mid"][1]-th["sky_top"][1])*k)
            b=int(th["sky_top"][2]+(th["sky_mid"][2]-th["sky_top"][2])*k)
        else:
            k=(tt-0.55)/0.45
            r=int(th["sky_mid"][0]+(th["sky_bot"][0]-th["sky_mid"][0])*k)
            g=int(th["sky_mid"][1]+(th["sky_bot"][1]-th["sky_mid"][1])*k)
            b=int(th["sky_mid"][2]+(th["sky_bot"][2]-th["sky_mid"][2])*k)
        pygame.draw.line(surf,(r,g,b),(0,y),(SCREEN_WIDTH,y))
    # Stars only on night theme
    if th["star_count"]>0:
        import random as _r; _r.seed(11)
        for _ in range(th["star_count"]):
            sx=_r.randint(0,SCREEN_WIDTH); sy=_r.randint(0,int(SCREEN_HEIGHT*0.6))
            c=_r.randint(150,255)
            pygame.draw.circle(surf,(c,c,min(255,c+20)),(sx,sy),_r.randint(1,2))
    # Moon / sun glow upper-right
    mx,my=int(SCREEN_WIDTH*0.82),int(SCREEN_HEIGHT*0.18)
    for i in range(8,0,-1):
        gl=pygame.Surface((i*54,i*54),pygame.SRCALPHA)
        pygame.draw.circle(gl,(*th["accent"],10),(i*27,i*27),i*27)
        surf.blit(gl,(mx-i*27,my-i*27),special_flags=pygame.BLEND_RGBA_ADD)
    pygame.draw.circle(surf,th["accent"],(mx,my),40)
    return surf

def _make_cloud(scale=1.0):
    th=_t()
    if _theme=="volcano":
        col=(70,30,30,180); shade=(40,18,18,150)
    elif _theme=="storm":
        col=(58,58,75,200); shade=(35,35,50,170)
    else:
        col=(78,88,135,180); shade=(60,68,110,150)
    w,h=int(150*scale),int(70*scale)
    s=pygame.Surface((w,h),pygame.SRCALPHA)
    lumps=[(0.18,0.55,0.34),(0.34,0.30,0.40),(0.54,0.26,0.42),(0.74,0.50,0.32),(0.46,0.58,0.38)]
    for lx,ly,lr in lumps:
        pygame.draw.circle(s,shade,(int(w*lx),int(h*ly)),int(h*lr))
    for lx,ly,lr in lumps:
        pygame.draw.circle(s,col,(int(w*lx),int(h*ly)),int(h*lr))
    return s

def _get_tile(kind):
    if kind in _tile_cache: return _tile_cache[kind]
    th=_t()
    s=pygame.Surface((TILE_SIZE,TILE_SIZE),pygame.SRCALPHA)
    if kind=="ground":
        for y in range(TILE_SIZE):
            t=y/TILE_SIZE
            r=int(th["dirt_l"][0]+(th["dirt_d"][0]-th["dirt_l"][0])*t)
            g=int(th["dirt_l"][1]+(th["dirt_d"][1]-th["dirt_l"][1])*t)
            b=int(th["dirt_l"][2]+(th["dirt_d"][2]-th["dirt_l"][2])*t)
            pygame.draw.line(s,(r,g,b),(0,y),(TILE_SIZE,y))
        import random as _r; _r.seed(7)
        for _ in range(10):
            pygame.draw.circle(s,th["dirt_d"],(_r.randint(2,TILE_SIZE-3),_r.randint(16,TILE_SIZE-3)),1)
        pygame.draw.rect(s,th["grass_d"],(0,0,TILE_SIZE,16))
        pygame.draw.rect(s,th["grass_t"],(0,0,TILE_SIZE,12))
        pygame.draw.rect(s,th["grass_t2"],(0,0,TILE_SIZE,5))
        for bx in range(2,TILE_SIZE,8):
            pygame.draw.circle(s,th["grass_t2"],(bx,4),3)
        pygame.draw.rect(s,th["dirt_d"],(0,0,TILE_SIZE,TILE_SIZE),1)
    elif kind=="platform":
        for y in range(TILE_SIZE):
            t=y/TILE_SIZE
            r=int(th["brick_h"][0]+(th["brick_d"][0]-th["brick_h"][0])*t)
            g=int(th["brick_h"][1]+(th["brick_d"][1]-th["brick_h"][1])*t)
            b=int(th["brick_h"][2]+(th["brick_d"][2]-th["brick_h"][2])*t)
            pygame.draw.line(s,(r,g,b),(0,y),(TILE_SIZE,y))
        pygame.draw.rect(s,th["brick_h"],(0,0,TILE_SIZE,5))
        pygame.draw.rect(s,th["brick_h"],(0,0,4,TILE_SIZE))
        pygame.draw.line(s,th["brick_d"],(0,TILE_SIZE//2),(TILE_SIZE,TILE_SIZE//2),2)
        pygame.draw.line(s,th["brick_d"],(TILE_SIZE//2,0),(TILE_SIZE//2,TILE_SIZE),2)
        pygame.draw.rect(s,th["brick_d"],(0,0,TILE_SIZE,TILE_SIZE),1)
    _tile_cache[kind]=s
    return s

def _blit_sky(surface):
    global _sky_surf
    if _sky_surf is None: _sky_surf=_build_sky()
    surface.blit(_sky_surf,(0,0))

def _hill(surface,cx,by,rx,ry,lt,dk,spot=None):
    pygame.draw.ellipse(surface,dk,(cx-rx,by-ry,rx*2,ry*2))
    pygame.draw.ellipse(surface,lt,(cx-rx+12,by-ry+10,rx*2-24,ry*2-20))
    if spot:
        pygame.draw.circle(surface,spot,(cx-rx//3,by-ry//3),max(6,rx//12))
        pygame.draw.circle(surface,spot,(cx+rx//4,by-ry//2),max(4,rx//16))

CLOUD_DEFS=[(110,70,1.15),(360,42,0.85),(640,86,1.30),(920,52,0.95),(1180,72,1.10),(1460,46,0.80)]

def draw_background(surface,camera_x):
    global _cloud_cache
    if _cloud_cache is None:
        _cloud_cache={round(sc,2):_make_cloud(sc) for _,_,sc in CLOUD_DEFS}
    _blit_sky(surface)
    th=_t()
    gy=SCREEN_HEIGHT-68
    off1=(camera_x//6)%360
    for i in range(-1,SCREEN_WIDTH//360+3):
        _hill(surface,i*360-off1+180,gy+20,200,120,th["hill_far_l"],th["hill_far_d"])
    off2=(camera_x//4)%300
    for i in range(-1,SCREEN_WIDTH//300+3):
        _hill(surface,i*300-off2+150,gy+10,165,100,th["hill_mid_l"],th["hill_mid_d"],th["hill_mid_s"])
    period=SCREEN_WIDTH+260
    for cx,cy,sc in CLOUD_DEFS:
        ox=(cx-camera_x//8)%period-130
        surface.blit(_cloud_cache[round(sc,2)],(ox,cy))
    off4=(camera_x//2)%220
    for i in range(-1,SCREEN_WIDTH//220+3):
        _hill(surface,i*220-off4+110,gy+4,120,70,th["bush_l"],th["bush_d"],th["bush_s"])

def draw_ground_tile(surface,rect):
    surface.blit(_get_tile("ground"),rect)

def draw_platform_tile(surface,rect):
    sh=pygame.Surface((rect.width,6),pygame.SRCALPHA); sh.fill((0,0,0,70))
    surface.blit(sh,(rect.x,rect.bottom))
    surface.blit(_get_tile("platform"),rect)
