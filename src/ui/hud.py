import pygame
from config import SCREEN_WIDTH

_FONT_PATH="assets/fonts/SuperPixel-m2L8j.ttf"
def _pf(size):
    try: return pygame.font.Font(_FONT_PATH,size)
    except: return pygame.font.SysFont("Courier New",size,bold=True)

def _sf(size):
    return pygame.font.SysFont("Arial Black", size, bold=True)

HUD_H=72
C_GOLD=(255,215,0); C_GOLD_D=(140,98,0)
C_CREAM=(238,222,188); C_DIM=(165,150,118)
C_RED=(228,52,52); C_RED_D=(110,18,18)
C_WHITE=(255,255,255); C_BLACK=(0,0,0)

def _heart3d(surface,cx,cy,size=11):
    pygame.draw.circle(surface,C_RED_D,(cx-size//4,cy),size//2+1)
    pygame.draw.circle(surface,C_RED_D,(cx+size//4,cy),size//2+1)
    pygame.draw.polygon(surface,C_RED_D,[(cx-size//2-1,cy),(cx,cy+size//2+2),(cx+size//2+1,cy)])
    pygame.draw.circle(surface,C_RED,(cx-size//4,cy-1),size//2)
    pygame.draw.circle(surface,C_RED,(cx+size//4,cy-1),size//2)
    pygame.draw.polygon(surface,C_RED,[(cx-size//2,cy-1),(cx,cy+size//2),(cx+size//2,cy-1)])
    pygame.draw.circle(surface,(255,180,180),(cx-size//4-1,cy-3),2)

def _text3d(surface,text,font,col,shadow_col,x,y,depth=2):
    for d in range(depth,0,-1):
        surface.blit(font.render(text,True,shadow_col),(x+d,y+d))
    surface.blit(font.render(text,True,col),(x,y))


class HUD:
    def __init__(self):
        pygame.font.init()
        self.fp_val=_pf(16)
        self.fp_lbl=_pf(9)
        self.fp_warn=_pf(8)
        self.fs_roman=_sf(18)
        self._adapt_progress=0.0
        # Cached renders so score/time never re-render unless value changes
        self._score_cache_val=None
        self._score_cache_img=None
        self._time_cache_val=None
        self._time_cache_img=None

    def _get_score_img(self, score):
        if score != self._score_cache_val:
            self._score_cache_val = score
            self._score_cache_img = self.fp_val.render(str(score), True, C_GOLD)
        return self._score_cache_img

    def _get_time_img(self, ts, color):
        key = (ts, color)
        if key != self._time_cache_val:
            self._time_cache_val = key
            self._time_cache_img = self.fp_val.render(str(ts), True, color)
        return self._time_cache_img

    def draw(self, surface, gs, time_remaining, rnn_confidence):
        panel=pygame.Surface((SCREEN_WIDTH,HUD_H),pygame.SRCALPHA)
        for y in range(HUD_H):
            t=y/HUD_H
            r=int(8+12*t); g=int(12+18*t); b=int(28+32*t)
            pygame.draw.line(panel,(r,g,b,235),(0,y),(SCREEN_WIDTH,y))
        surface.blit(panel,(0,0))
        pygame.draw.line(surface,(255,235,120),(0,0),(SCREEN_WIDTH,0),1)
        pygame.draw.line(surface,(180,140,0), (0,2),(SCREEN_WIDTH,2),1)
        pygame.draw.line(surface,(50,38,18),(0,HUD_H-2),(SCREEN_WIDTH,HUD_H-2),1)
        pygame.draw.line(surface,(0,0,0),    (0,HUD_H-1),(SCREEN_WIDTH,HUD_H-1),1)

        # SCORE — flat, cached, no 3D shadow
        surface.blit(self.fp_lbl.render("SCORE", True, C_DIM), (14, 4))
        surface.blit(self._get_score_img(gs.score), (12, 15))

        # LEVEL
        lbl=self.fp_lbl.render("LEVEL",True,C_DIM)
        surface.blit(lbl, (SCREEN_WIDTH//2-lbl.get_width()//2, 4))
        n = gs.level_index + 1
        lv = "I" if n == 1 else str(n)
        val=self.fs_roman.render(lv,True,C_CREAM)
        surface.blit(val, (SCREEN_WIDTH//2-val.get_width()//2, 14))

        # LIVES
        lx=SCREEN_WIDTH//2+118
        surface.blit(self.fp_lbl.render("LIVES", True, C_DIM), (lx, 4))
        for i in range(min(gs.lives,5)):
            _heart3d(surface,lx+i*16,22,size=10)
        if gs.lives>5:
            surface.blit(self.fp_lbl.render(f"+{gs.lives-5}", True, C_RED), (lx+82, 18))

        # TIME — flat, cached
        surface.blit(self.fp_lbl.render("TIME", True, C_DIM), (SCREEN_WIDTH-94, 4))
        import math
        ts = max(0, math.ceil(time_remaining))
        tcol = C_RED if ts < 10 else C_CREAM
        surface.blit(self._get_time_img(ts, tcol), (SCREEN_WIDTH-88, 15))

        # AI ADAPT BAR
        conf=max(0.0,min(1.0,float(rnn_confidence)))
        target = min(1.0, (gs.enemies_defeated_total*0.30) + (gs.player_deaths_this_level*0.22) + conf*0.65)
        self._adapt_progress += (target - self._adapt_progress) * 0.18
        prog = max(0.0, min(1.0, self._adapt_progress))

        warn="AI HAS ADAPTED!" if prog>=0.95 else ("AI ADAPTING..." if prog>0.35 else "AI READING YOU")
        wcol=(255,90,90) if prog>0.35 else C_DIM
        wimg=self.fp_warn.render(warn,True,wcol)
        surface.blit(wimg, (SCREEN_WIDTH//2-wimg.get_width()//2, 42))

        bw,bh=360,8
        bx=SCREEN_WIDTH//2-bw//2; by=56
        pygame.draw.rect(surface,(0,0,0),(bx-1,by-1,bw+2,bh+2),border_radius=2)
        fw=int(bw*prog)
        for px2 in range(fw):
            ratio=px2/max(bw,1)
            col=(int(55+200*ratio),int(205-165*ratio),48)
            pygame.draw.line(surface,col,(bx+px2,by),(bx+px2,by+bh-1))
        pygame.draw.rect(surface,(80,80,90),(bx,by,bw,bh),1,border_radius=2)
