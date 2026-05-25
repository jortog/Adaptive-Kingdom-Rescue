import pygame, sys
from config import (SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE, LEVEL_TIME_LIMIT, TILE_SIZE, ACTION_JUMP, STRAT_SPAWN_AERIAL)
from src.systems.game_state import GameState
from src.systems.camera import Camera
from src.systems.scoring import ScoringSystem
from src.entities.player import Player
from src.entities.enemy import Enemy
from src.entities.powerup import PowerUp
from src.entities.princess import Princess
from src.ai.ensemble import AIEnsemble
from src.ui.hud import HUD
from src.ui.screens import ScreenManager
from src.levels.level_01 import Level01
from src.levels.level_02 import Level02
from src.levels.level_03 import Level03
import numpy as np

SCENE_MENU="menu"; SCENE_GAME="game"; SCENE_PAUSE="pause"
SCENE_SETTINGS="settings"; SCENE_LEVEL_COMPLETE="level_complete"
SCENE_GAME_OVER="game_over"; SCENE_WIN="win"
LEVELS=[Level01,Level02,Level03]; NUM_LEVELS=3

class Game:
    def __init__(self):
        pygame.init(); pygame.mixer.init()
        pygame.mixer.music.load("assets/sounds/menu_music_cropped.mp3")
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)
        pygame.mixer.music.set_pos(12)
        self.screen=pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock=pygame.time.Clock()
        self.gs=GameState(); self.hud=HUD()
        self.screens=ScreenManager(self.screen)
        self.scene=SCENE_MENU
        self.level=self.player=self.camera=self.scoring=self.ai_ensemble=self.princess=None
        self.enemies=[]; self.powerups=[]
        self.time_remaining=LEVEL_TIME_LIMIT
        self._aerial_spawn_cd=0.0; self.AERIAL_SPAWN_CD=4.0
        self.selected_level=0
        self.settings={'sound':True,'ai_difficulty':'normal'}
        self._menu_cursor=0; self._pause_cursor=0
        self._settings_cursor=0; self._settings_from=SCENE_MENU

    def load_level(self,idx):
        idx=min(max(idx,0),NUM_LEVELS-1)
        self.level=LEVELS[idx]()
        self.gs.reset_level()
        self.time_remaining=LEVEL_TIME_LIMIT; self._aerial_spawn_cd=0.0
        self.player=Player(self.level.spawn_x,self.level.spawn_y,self.gs)
        self.camera=Camera(self.level.pixel_width,self.level.pixel_height)
        self.scoring=ScoringSystem(self.gs)
        if self.ai_ensemble is None:
            self.ai_ensemble=AIEnsemble(level_width=self.level.pixel_width,level_time=LEVEL_TIME_LIMIT)
        self.enemies=[]
        for sp in self.level.get_enemy_spawns():
            self.enemies.append(Enemy(sp["x"],sp["y"],enemy_type=sp.get("type","ground"),patrol_left=sp.get("patrol_left"),patrol_right=sp.get("patrol_right")))
        px,py=self.level.get_princess_position()
        self.princess=Princess(px,py)
        rows=len(self.level.TILE_MAP); gy=(rows-2)*TILE_SIZE
        self.powerups=[PowerUp(6*TILE_SIZE,gy-TILE_SIZE,"mushroom"),PowerUp(14*TILE_SIZE,gy-TILE_SIZE,"flower"),PowerUp(20*TILE_SIZE,gy-TILE_SIZE,"star")]

    def update_game(self,dt):
        self.time_remaining-=dt; self.gs.level_time_elapsed+=dt
        self.player.update(dt,self.level.platforms,self.gs)
        self.camera.update(self.player.rect,dt)
        jf=self.gs.count_recent_action(ACTION_JUMP); rf=self.gs.count_recent_action(2)
        ah=self.gs.get_action_history_padded()
        ps=self.ai_ensemble.ppo.build_state(self.gs.level_time_elapsed,self.gs.lives,len(self.enemies),abs(self.princess.rect.centerx-self.player.rect.centerx),jf,rf,self.player.vel_x,self.player.size_level)
        self.ai_ensemble.pre_frame(dt,ah,ps)
        for e in self.enemies:
            if not e.alive: continue
            cmd=self.ai_ensemble.get_command(e.rect,self.player.rect,self.player.vel_x,jf,rf,len(self.enemies),self.player.size_level)
            e.set_command(cmd); e.update(dt,self.player.rect,self.level.platforms)
        self._aerial_spawn_cd-=dt
        if self.ai_ensemble._ppo_action==STRAT_SPAWN_AERIAL and self._aerial_spawn_cd<=0 and jf>=3:
            import random; x=self.player.rect.centerx+random.randint(-TILE_SIZE,TILE_SIZE); y=self.player.rect.top-3*TILE_SIZE
            fly=Enemy(x,y,enemy_type="flying"); fly.set_command(1); self.enemies.append(fly)
            self._aerial_spawn_cd=self.AERIAL_SPAWN_CD
        self.ai_ensemble.ppo.reward_prevention()
        for e in list(self.enemies):
            if not e.alive or not self.player.rect.colliderect(e.rect): continue
            stomp=pygame.Rect(e.rect.x,e.rect.y,e.rect.width,e.rect.height*0.10)
            pbot=pygame.Rect(self.player.rect.x,self.player.rect.bottom-4,self.player.rect.width,4)
            if pbot.colliderect(stomp) and self.player.vel_y>0:
                e.die(); self.enemies.remove(e); self.player.vel_y=-400
                self.scoring.award_enemy_defeat(e.enemy_type,not self.player.on_ground)
            else:
                if self.player.take_damage():
                    self.gs.lives-=1
                    if self.gs.level_time_elapsed<5.0: self.ai_ensemble.ppo.penalty_fast_death()
                    self.gs.player_deaths_this_level+=1
                    self.scene=SCENE_GAME_OVER if self.gs.lives<=0 else self.scene
                    if self.gs.lives>0: self.load_level(self.gs.level_index)
                    return
        for hz in self.level.hazards:
            if self.player.rect.colliderect(hz):
                self.gs.lives-=1; self.gs.player_deaths_this_level+=1
                self.scene=SCENE_GAME_OVER if self.gs.lives<=0 else self.scene
                if self.gs.lives>0: self.load_level(self.gs.level_index)
                return
        for pu in list(self.powerups):
            if self.player.rect.colliderect(pu.rect):
                if pu.kind=="oneup": self.gs.lives=min(self.gs.lives+1,9)
                else: self.player.collect_powerup(pu.kind)
                self.scoring.award_powerup(pu.kind); self.powerups.remove(pu)
        if self.player.rect.colliderect(self.princess.rect):
            self.scoring.award_level_complete(self.time_remaining,self.gs.damage_taken_this_level==0)
            self.ai_ensemble.learn_after_level(list(self.gs.action_history)); self.ai_ensemble.save_all()
            self.gs.level_index+=1
            self.scene=SCENE_WIN if self.gs.level_index>=NUM_LEVELS else SCENE_LEVEL_COMPLETE; return
        if self.player.rect.top>self.level.pixel_height+100 or self.time_remaining<=0:
            self.gs.lives-=1; self.gs.player_deaths_this_level+=1
            self.scene=SCENE_GAME_OVER if self.gs.lives<=0 else self.scene
            if self.gs.lives>0: self.load_level(self.gs.level_index)

    def draw_game(self):
        cx=self.camera.int_x
        self.level.draw_tiles(self.screen,cx)
        for pu in self.powerups: pu.draw(self.screen,cx)
        self.princess.update_bob(1/60); self.princess.draw(self.screen,cx)
        for e in self.enemies: e.draw(self.screen,cx)
        self.player.draw(self.screen,cx)
        self.hud.draw(self.screen,self.gs,self.time_remaining,self.ai_ensemble.rnn_confidence if self.ai_ensemble else 0.0)

    def _apply_ai(self):
        if self.ai_ensemble:
            try: self.ai_ensemble.ppo.model.ent_coef=0.005 if self.settings.get('ai_difficulty')=='challenge' else 0.01
            except: pass

    def _settings_key(self,event):
        N=5
        if event.key==pygame.K_UP: self._settings_cursor=(self._settings_cursor-1)%N
        elif event.key==pygame.K_DOWN: self._settings_cursor=(self._settings_cursor+1)%N
        elif event.key==pygame.K_RIGHT:
            c=self._settings_cursor
            if c==0: self.settings['sound']=not self.settings['sound']
            elif c==1: self.selected_level=(self.selected_level+1)%NUM_LEVELS
            elif c==2:
                self.settings['ai_difficulty']='challenge' if self.settings['ai_difficulty']=='normal' else 'normal'
                self._apply_ai()
        elif event.key==pygame.K_LEFT:
            c=self._settings_cursor
            if c==0: self.settings['sound']=not self.settings['sound']
            elif c==1: self.selected_level=(self.selected_level-1)%NUM_LEVELS
            elif c==2:
                self.settings['ai_difficulty']='challenge' if self.settings['ai_difficulty']=='normal' else 'normal'
                self._apply_ai()
        elif event.key==pygame.K_RETURN:
            if self._settings_cursor==4: self.scene=self._settings_from
            elif self._settings_cursor==0: self.settings['sound']=not self.settings['sound']
        elif event.key in (pygame.K_ESCAPE,pygame.K_BACKSPACE): self.scene=self._settings_from

    def run(self):
        while True:
            dt=min(self.clock.tick(FPS)/1000.0,0.033)
            self.screens.tick(dt)
            for event in pygame.event.get():
                if event.type==pygame.QUIT: self._quit()
                elif self.scene==SCENE_MENU and event.type==pygame.KEYDOWN:
                    if event.key==pygame.K_UP: self._menu_cursor=(self._menu_cursor-1)%3
                    elif event.key==pygame.K_DOWN: self._menu_cursor=(self._menu_cursor+1)%3
                    elif event.key==pygame.K_RETURN:
                        if self._menu_cursor==0:
                            pygame.mixer.music.stop(); self.gs.level_index=self.selected_level; self.load_level(self.gs.level_index); self.scene=SCENE_GAME
                        elif self._menu_cursor==1:
                            self._settings_from=SCENE_MENU; self._settings_cursor=0; self.scene=SCENE_SETTINGS
                        elif self._menu_cursor==2: self._quit()
                    elif event.key==pygame.K_ESCAPE: self._quit()
                elif self.scene==SCENE_GAME:
                    if event.type==pygame.KEYDOWN:
                        if event.key==pygame.K_p: self._pause_cursor=0; self.scene=SCENE_PAUSE
                        elif event.key==pygame.K_ESCAPE: self.scene=SCENE_MENU; pygame.mixer.music.play(-1); pygame.mixer.music.set_pos(12)
                    if self.player: self.player.handle_event(event)
                elif self.scene==SCENE_PAUSE and event.type==pygame.KEYDOWN:
                    if event.key==pygame.K_UP: self._pause_cursor=(self._pause_cursor-1)%3
                    elif event.key==pygame.K_DOWN: self._pause_cursor=(self._pause_cursor+1)%3
                    elif event.key==pygame.K_RETURN:
                        if self._pause_cursor==0: self.scene=SCENE_GAME
                        elif self._pause_cursor==1: self._settings_from=SCENE_PAUSE; self._settings_cursor=0; self.scene=SCENE_SETTINGS
                        elif self._pause_cursor==2: self.scene=SCENE_MENU; pygame.mixer.music.play(-1)
                        pygame.mixer.music.set_pos(12)
                    elif event.key in (pygame.K_p,pygame.K_ESCAPE): self.scene=SCENE_GAME
                elif self.scene==SCENE_SETTINGS and event.type==pygame.KEYDOWN:
                    self._settings_key(event)
                elif self.scene in (SCENE_LEVEL_COMPLETE,SCENE_GAME_OVER,SCENE_WIN) and event.type==pygame.KEYDOWN:
                    if event.key==pygame.K_RETURN:
                        if self.scene==SCENE_GAME_OVER: self.gs.lives=3; self.load_level(self.gs.level_index); self.scene=SCENE_GAME
                        elif self.scene==SCENE_LEVEL_COMPLETE: self.load_level(self.gs.level_index); self.scene=SCENE_GAME
                        elif self.scene==SCENE_WIN: self.gs.challenge_mode=True; self.gs.level_index=0; self.load_level(0); self.scene=SCENE_GAME
                    elif event.key==pygame.K_ESCAPE: self.scene=SCENE_MENU; pygame.mixer.music.play(-1)
                    pygame.mixer.music.set_pos(12)

            if self.scene==SCENE_MENU: self.screens.draw_main_menu(self._menu_cursor)
            elif self.scene==SCENE_GAME: self.update_game(dt); self.draw_game()
            elif self.scene==SCENE_PAUSE: self.draw_game(); self.screens.draw_pause(self._pause_cursor)
            elif self.scene==SCENE_SETTINGS:
                if self._settings_from==SCENE_PAUSE: self.draw_game()
                self.screens.draw_settings(self._settings_cursor,self.settings,self.selected_level,NUM_LEVELS,from_game=(self._settings_from==SCENE_PAUSE))
            elif self.scene==SCENE_LEVEL_COMPLETE: self.screens.draw_level_complete(self.gs.score,self.gs.level_index-1)
            elif self.scene==SCENE_GAME_OVER: self.screens.draw_game_over(self.gs.score)
            elif self.scene==SCENE_WIN: self.screens.draw_win_screen(self.gs.score)
            pygame.display.flip()

    def _quit(self):
        if self.ai_ensemble: self.ai_ensemble.save_all()
        pygame.quit(); sys.exit()

if __name__=="__main__":
    Game().run()