import pygame
from config import SCREEN_WIDTH

_FONT_PATH = "assets/fonts/SuperPixel-m2L8j.ttf"

def _pf(size):
    try:    return pygame.font.Font(_FONT_PATH, size)
    except: return pygame.font.SysFont("Courier New", size, bold=True)

def _sf(size, bold=False):
    return pygame.font.SysFont("Arial", size, bold=bold)

HUD_H  = 62
C_GOLD  = (255, 215,   0)
C_CREAM = (235, 220, 188)
C_DIM   = (138, 128, 106)
C_RED   = (228,  52,  52)
C_WARN  = (255, 128,  30)
C_WHITE = (255, 255, 255)
C_GREEN = ( 80, 215,  80)

def _heart(surface, cx, cy, size=9):
    r   = size//2
    col = (220, 52, 52)
    pygame.draw.circle(surface, col, (cx-r//2, cy-1), r//2+1)
    pygame.draw.circle(surface, col, (cx+r//2, cy-1), r//2+1)
    pygame.draw.polygon(surface, col, [(cx-r,cy),(cx,cy+r+1),(cx+r,cy)])

def _coin_icon(surface, cx, cy, r=5):
    pygame.draw.circle(surface,(255,215,0),(cx,cy),r)
    pygame.draw.circle(surface,(255,232,100),(cx-1,cy-1),r-2)
    pygame.draw.circle(surface,(195,155,0),(cx,cy),r,1)


class HUD:
    def __init__(self):
        pygame.font.init()
        self.fp_val  = _pf(16)
        self.fp_lbl  = _pf(9)
        self.fp_ai   = _pf(8)
        self.fs_tiny = _sf(12)

    def draw(self, surface, game_state, time_remaining, rnn_confidence):
        # Panel
        panel = pygame.Surface((SCREEN_WIDTH, HUD_H), pygame.SRCALPHA)
        panel.fill((6, 10, 24, 222))
        surface.blit(panel, (0,0))
        pygame.draw.line(surface,(175,138,0),(0,0),(SCREEN_WIDTH,0),2)
        pygame.draw.line(surface,(35,32,22),(0,HUD_H-1),(SCREEN_WIDTH,HUD_H-1),1)

        # SCORE
        lbl = self.fp_lbl.render("RESCUER", True, C_DIM)
        surface.blit(lbl,(14,4))
        surface.blit(self.fp_val.render(f"{game_state.score:07d}", True, C_GOLD),(12,17))

        # COINS
        _coin_icon(surface, 214, 13)
        surface.blit(self.fp_val.render(f"x{(game_state.score//100)%100:02d}", True, C_CREAM),(223,6))

        # WORLD
        wlbl = self.fp_lbl.render("WORLD", True, C_DIM)
        surface.blit(wlbl,(SCREEN_WIDTH//2-wlbl.get_width()//2, 4))
        wval = self.fp_val.render(f"{game_state.level_index+1}-1", True, C_CREAM)
        surface.blit(wval,(SCREEN_WIDTH//2-wval.get_width()//2, 17))

        # LIVES
        llbl = self.fp_lbl.render("LIVES", True, C_DIM)
        lx   = SCREEN_WIDTH//2 + 118
        surface.blit(llbl,(lx, 4))
        for i in range(min(game_state.lives, 5)):
            _heart(surface, lx+i*18, 30, size=10)
        if game_state.lives > 5:
            surface.blit(self.fp_lbl.render(f"+{game_state.lives-5}", True, C_RED),(lx+92, 24))

        # TIME
        tlbl = self.fp_lbl.render("TIME", True, C_DIM)
        surface.blit(tlbl,(SCREEN_WIDTH-94,4))
        t    = max(0, int(time_remaining))
        tcol = C_RED if t<20 else (C_WARN if t<40 else C_CREAM)
        surface.blit(self.fp_val.render(f"{t:03d}", True, tcol),(SCREEN_WIDTH-88,17))

        # AI READ bar
        bw, bh = 255, 8
        bx = SCREEN_WIDTH//2 - bw//2
        by = HUD_H - 14
        pygame.draw.rect(surface,(22,28,48),(bx-1,by-1,bw+2,bh+2),border_radius=3)
        fw = int(bw * rnn_confidence)
        for px2 in range(fw):
            ratio = px2 / max(bw, 1)
            col   = (int(55+200*ratio), int(205-165*ratio), 48)
            pygame.draw.line(surface, col,(bx+px2,by),(bx+px2,by+bh-1))
        pygame.draw.rect(surface,(55,50,36),(bx,by,bw,bh),1,border_radius=3)

        al = self.fp_ai.render("AI READS YOU", True, C_DIM)
        surface.blit(al,(bx+bw+8,by-1))
        pct_col = (225,55,55) if rnn_confidence>0.7 else C_DIM
        pct = self.fp_ai.render(f"{int(rnn_confidence*100)}%", True, pct_col)
        surface.blit(pct,(bx-pct.get_width()-6,by-1))
