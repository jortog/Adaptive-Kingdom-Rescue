import sys
import random

import pygame

from config import (
    ACTION_JUMP,
    ACTION_RUN,
    ELEVATION_CAMP_FULL,
    FPS,
    LEVEL_TIME_LIMIT,
    PLAYER_MAX_LIVES,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    STAR_LEVEL_PENALTY,
    STAR_MIN_CHANCE,
    STRAT_SPAWN_AERIAL,
    TILE_SIZE,
    TITLE,
)
from src.ai.ensemble import AIEnsemble
from src.entities.enemy import Enemy
from src.entities.player import Player
from src.entities.powerup import PowerUp
from src.entities.princess import Princess
from src.levels.level_01 import Level01
from src.levels.level_02 import Level02
from src.levels.level_03 import Level03
from src.systems.audio import AudioManager
from src.systems.camera import Camera
from src.systems.game_state import GameState
from src.systems.scoring import ScoringSystem
from src.ui.hud import HUD, ai_debug_lines
from src.ui.screens import ScreenManager

SCENE_MENU = "menu"
SCENE_GAME = "game"
SCENE_PAUSE = "pause"
SCENE_SETTINGS = "settings"
SCENE_LEVEL_COMPLETE = "level_complete"
SCENE_GAME_OVER = "game_over"
SCENE_WIN = "win"
LEVELS = [Level01, Level02, Level03]
NUM_LEVELS = 3
MENU_BGM = "menu_music_cropped.mp3"


class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.audio = AudioManager()
        self.audio.play_bgm(MENU_BGM, loop=True, start_pos=12)
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.gs = GameState()
        self.hud = HUD()
        self.screens = ScreenManager(self.screen)
        self.scene = SCENE_MENU
        self._finished_level = 1
        self.level = self.player = self.camera = self.scoring = self.ai_ensemble = (
            self.princess
        ) = None
        self.enemies = []
        self.powerups = []
        self.time_remaining = LEVEL_TIME_LIMIT
        self._max_level_progress = 0.0
        self._aerial_spawn_cd = 0.0
        self.AERIAL_SPAWN_CD = 2.5
        # Time spent camping above ground; feeds anti-camping AI
        self._elevated_time = 0.0
        self._enemy_cap = 99
        self.selected_level = 0
        self.settings = {"sound": True, "music": True}
        self._menu_cursor = 0
        self._pause_cursor = 0
        self._settings_cursor = 0
        self._settings_from = SCENE_MENU
        self.show_ai_debug = False
        self._last_logged_strat = None

    def _start_menu_music(self):
        self.audio.play_bgm(MENU_BGM, loop=True, start_pos=12)

    def load_level(self, idx):
        idx = min(max(idx, 0), NUM_LEVELS - 1)
        # Fresh seed means a new reachable layout each attempt
        self.level = LEVELS[idx](seed=random.randrange(1 << 30))
        self.gs.reset_level()
        self.time_remaining = LEVEL_TIME_LIMIT
        self._max_level_progress = 0.0
        self._aerial_spawn_cd = 0.0
        self._elevated_time = 0.0
        self.player = Player(self.level.spawn_x, self.level.spawn_y, self.gs)
        self.player.audio = self.audio
        self.camera = Camera(self.level.pixel_width, self.level.pixel_height)
        self.scoring = ScoringSystem(self.gs)
        if self.ai_ensemble is None:
            self.ai_ensemble = AIEnsemble(
                level_width=self.level.pixel_width,
                level_time=LEVEL_TIME_LIMIT,
            )
        # Each attempt increases the AI difficulty ramp
        self.ai_ensemble.register_attempt()
        self.enemies = []
        for sp in self.level.get_enemy_spawns():
            self.enemies.append(
                Enemy(
                    sp["x"],
                    sp["y"],
                    enemy_type=sp.get("type", "ground"),
                    patrol_left=sp.get("patrol_left"),
                    patrol_right=sp.get("patrol_right"),
                )
            )
        # Cap live enemies so learned aerial pressure cannot snowball
        self._enemy_cap = len(self.enemies) + 2
        self.ai_ensemble.ppo.max_enemies = max(self._enemy_cap, 1)
        px, py = self.level.get_princess_position()
        self.princess = Princess(px, py)
        # Power-ups are reachable; stars become rarer as AI pressure rises
        prog = self.ai_ensemble.difficulty_progress()
        star_chance = max(
            STAR_MIN_CHANCE, 1.0 - prog - STAR_LEVEL_PENALTY * self.gs.level_index
        )
        third = "star" if random.random() < star_chance else "shield"
        self.powerups = [
            PowerUp(x, y, kind)
            for (x, y, kind) in self.level.get_powerup_spawns(
                ["mushroom", "mushroom", third]
            )
        ]

    def _build_ppo_state(self, jump_freq=None, run_freq=None):
        if jump_freq is None:
            jump_freq = self.gs.count_recent_action(ACTION_JUMP)
        if run_freq is None:
            run_freq = self.gs.count_recent_action(ACTION_RUN)
        alive_count = sum(1 for e in self.enemies if e.alive)
        return self.ai_ensemble.ppo.build_state(
            self.gs.level_time_elapsed,
            self.gs.lives,
            alive_count,
            abs(self.princess.rect.centerx - self.player.rect.centerx),
            jump_freq,
            run_freq,
            self.player.vel_x,
            self.player.rect.centery,
            self.level.pixel_height,
        )

    def _record_ppo_transition(self, state, action, reward, done=False):
        next_state = self._build_ppo_state()
        self.ai_ensemble.ppo.observe(state, action, reward, next_state, done)

    def _lose_life(self, ppo_state, ppo_action, frame_reward):
        """Handle life loss and record the terminal PPO transition."""
        self.gs.lives -= 1
        self.gs.damage_taken_this_level += 1
        frame_reward += 0.75
        self.audio.play_death()
        self.scene = SCENE_GAME_OVER if self.gs.lives <= 0 else self.scene
        self._record_ppo_transition(ppo_state, ppo_action, frame_reward, done=True)
        if self.gs.lives > 0:
            self.load_level(self.gs.level_index)

    def update_game(self, dt):
        self.time_remaining -= dt
        self.gs.level_time_elapsed += dt
        self.player.update(dt, self.level.platforms, self.level.pixel_width)
        self.camera.update(self.player.rect, dt)
        jf = self.gs.count_recent_action(ACTION_JUMP)
        rf = self.gs.count_recent_action(ACTION_RUN)
        ah = self.gs.get_action_history_padded()
        difficulty = self.ai_ensemble.compute_difficulty(
            self.gs.level_index, self.gs.level_time_elapsed
        )
        # Sustained elevation teaches the AI to send flyers and vertical chasers
        ground_top = self.level.pixel_height - TILE_SIZE
        elevation_tiles = max(0.0, (ground_top - self.player.rect.bottom) / TILE_SIZE)
        if elevation_tiles >= 1.5:
            self._elevated_time = min(self._elevated_time + dt, ELEVATION_CAMP_FULL + 1.0)
        else:
            self._elevated_time = max(0.0, self._elevated_time - dt * 1.5)
        aerial_bias = min(self._elevated_time / ELEVATION_CAMP_FULL, 1.0)
        ppo_state = self._build_ppo_state(jf, rf)
        self.ai_ensemble.pre_frame(dt, ah, ppo_state, difficulty, aerial_bias)
        ppo_action = self.ai_ensemble._ppo_action
        frame_reward = dt
        player_jumped = self.player.vel_y < -300 and not self.player.on_ground
        spawn_requested = False
        # Nearby enemies spend the limited aggression budget first
        ordered = sorted(
            (e for e in self.enemies if e.alive),
            key=lambda e: abs(e.rect.centerx - self.player.rect.centerx),
        )
        for e in ordered:
            cmd = self.ai_ensemble.get_command(
                e.rect,
                self.player.rect,
                self.player.vel_x,
                jf,
                rf,
                len(self.enemies),
                self.player.size_level,
            )
            if cmd == STRAT_SPAWN_AERIAL:
                spawn_requested = True
            e.set_command(cmd)
            if player_jumped and abs(e.rect.centerx - self.player.rect.centerx) < 380:
                e.mirror_jump(self.player.vel_y)
            e.update(dt, self.player.rect, self.level.platforms)
        self._aerial_spawn_cd -= dt
        alive_count = sum(1 for e in self.enemies if e.alive)
        # Repeated jumping or camping can trigger a learned aerial counter
        camping_high = self._elevated_time >= 1.2
        if (
            spawn_requested
            and self._aerial_spawn_cd <= 0
            and alive_count < self._enemy_cap
            and ((difficulty >= 0.45 and jf >= 2) or camping_high)
        ):
            x = self.player.rect.centerx + random.randint(-TILE_SIZE, TILE_SIZE)
            y = self.player.rect.top - 3 * TILE_SIZE
            fly = Enemy(x, y, enemy_type="flying")
            fly.set_command(1)
            self.enemies.append(fly)
            self._aerial_spawn_cd = self.AERIAL_SPAWN_CD
        for e in list(self.enemies):
            if not e.alive or not self.player.rect.colliderect(e.rect):
                continue
            stomp = pygame.Rect(
                e.rect.x, e.rect.y - 2, e.rect.width, e.rect.height * 0.55
            )
            pbot = pygame.Rect(
                self.player.rect.x,
                self.player.rect.bottom - 10,
                self.player.rect.width,
                12,
            )
            falling = self.player.vel_y > -50
            above = self.player.rect.centery < e.rect.centery
            if pbot.colliderect(stomp) and falling and above:
                e.die()
                self.enemies.remove(e)
                self.player.vel_y = -400
                self.audio.play_defeat()
                self.scoring.award_enemy_defeat(e.enemy_type, not self.player.on_ground)
                self.gs.enemies_defeated_total += 1
                frame_reward -= 0.4
            else:
                old_size = self.player.size_level
                old_shields = self.player.shield_count
                if self.player.take_damage():
                    # Early deaths reward enemy pressure more
                    if self.gs.level_time_elapsed < 5.0:
                        frame_reward -= 0.5
                    self._lose_life(ppo_state, ppo_action, frame_reward)
                    return
                elif (
                    self.player.size_level < old_size
                    or self.player.shield_count < old_shields
                ):
                    self.gs.damage_taken_this_level += 1
                    frame_reward += 0.25
        for hz in self.level.hazards:
            if self.player.rect.colliderect(hz):
                self._lose_life(ppo_state, ppo_action, frame_reward)
                return
        for pu in list(self.powerups):
            if self.player.rect.colliderect(pu.rect):
                if pu.kind == "oneup":
                    self.gs.lives = min(self.gs.lives + 1, PLAYER_MAX_LIVES)
                else:
                    self.player.collect_powerup(pu.kind)

                self.audio.play_coin()
                self.scoring.award_powerup(pu.kind)
                self.powerups.remove(pu)

        if self.player.rect.colliderect(self.princess.rect):
            frame_reward -= 2.0
            self.scoring.award_level_complete(
                self.time_remaining, self.gs.damage_taken_this_level == 0
            )

            self._record_ppo_transition(ppo_state, ppo_action, frame_reward, done=True)

            self.ai_ensemble.learn_after_level(list(self.gs.action_history))

            self.ai_ensemble.save_all()

            finished_level = self.gs.level_index + 1
            self._finished_level = finished_level

            self.gs.level_index += 1

            if self.gs.level_index >= NUM_LEVELS:
                self.scene = SCENE_WIN
            else:
                self.scene = SCENE_LEVEL_COMPLETE
            return
        if (
            self.player.rect.top > self.level.pixel_height + 100
            or self.time_remaining <= 0
        ):
            self._lose_life(ppo_state, ppo_action, frame_reward)
            return

        self._record_ppo_transition(ppo_state, ppo_action, frame_reward)

    def draw_game(self):
        cx = self.camera.int_x
        y_offset = self.level.render_y
        self.level.draw_tiles(self.screen, cx)
        for pu in self.powerups:
            pu.draw(self.screen, cx, y_offset)
        self.princess.update_bob(1 / 60)
        self.princess.draw(self.screen, cx, y_offset)
        for e in self.enemies:
            e.draw(self.screen, cx, y_offset)
        self.player.draw(self.screen, cx, y_offset)
        current_progress = self.player.rect.centerx / max(self.princess.rect.centerx, 1)
        self._max_level_progress = max(self._max_level_progress, current_progress)
        self.hud.draw(
            self.screen,
            self.gs,
            self.time_remaining,
            self._max_level_progress,
        )
        if self.show_ai_debug and self.ai_ensemble:
            snap = self.ai_ensemble.debug_snapshot()
            recent = list(self.gs.action_history)
            self.hud.draw_ai_debug(self.screen, recent, snap)
            if snap["command"] != self._last_logged_strat:
                self._last_logged_strat = snap["command"]
                lines = ai_debug_lines(recent, snap)
                print("[AI] " + " | ".join(f"{lbl} {val}" for lbl, val in lines))

    def _settings_key(self, event):
        N = 4
        if event.key == pygame.K_UP:
            self._settings_cursor = (self._settings_cursor - 1) % N
        elif event.key == pygame.K_DOWN:
            self._settings_cursor = (self._settings_cursor + 1) % N
        elif event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_RETURN):
            c = self._settings_cursor
            if c == 0:  # Menu Music (BGM)
                self.settings["music"] = not self.settings.get("music", True)
                self.audio.set_music_enabled(self.settings["music"])
            elif c == 1:  # Start Level
                if event.key == pygame.K_RIGHT:
                    self.selected_level = (self.selected_level + 1) % NUM_LEVELS
                elif event.key == pygame.K_LEFT:
                    self.selected_level = (self.selected_level - 1) % NUM_LEVELS
            elif c == 3 and event.key == pygame.K_RETURN:  # Back (c == 2 is Controls)
                self.scene = self._settings_from
        elif event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            self.scene = self._settings_from

    def run(self):
        while True:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.033)
            self.screens.tick(dt)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._quit()
                elif self.scene == SCENE_MENU and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self._menu_cursor = (self._menu_cursor - 1) % 3
                    elif event.key == pygame.K_DOWN:
                        self._menu_cursor = (self._menu_cursor + 1) % 3
                    elif event.key == pygame.K_RETURN:
                        if self._menu_cursor == 0:
                            self.audio.stop_bgm()
                            self.gs.reset_session()
                            self.gs.level_index = self.selected_level
                            self.load_level(self.gs.level_index)
                            self.scene = SCENE_GAME
                        elif self._menu_cursor == 1:
                            self._settings_from = SCENE_MENU
                            self._settings_cursor = 0
                            self.scene = SCENE_SETTINGS
                        elif self._menu_cursor == 2:
                            self._quit()
                    elif event.key == pygame.K_ESCAPE:
                        self._quit()
                elif self.scene == SCENE_GAME:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_p:
                            self._pause_cursor = 0
                            self.scene = SCENE_PAUSE
                        elif event.key == pygame.K_ESCAPE:
                            self.scene = SCENE_MENU
                            self._start_menu_music()
                        elif event.key == pygame.K_F1:
                            self.show_ai_debug = not self.show_ai_debug
                    if self.player:
                        self.player.handle_event(event)
                elif self.scene == SCENE_PAUSE and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self._pause_cursor = (self._pause_cursor - 1) % 3
                    elif event.key == pygame.K_DOWN:
                        self._pause_cursor = (self._pause_cursor + 1) % 3
                    elif event.key == pygame.K_RETURN:
                        if self._pause_cursor == 0:
                            self.scene = SCENE_GAME
                        elif self._pause_cursor == 1:
                            self._settings_from = SCENE_PAUSE
                            self._settings_cursor = 0
                            self.scene = SCENE_SETTINGS
                        elif self._pause_cursor == 2:
                            self.scene = SCENE_MENU
                            self._start_menu_music()
                    elif event.key in (pygame.K_p, pygame.K_ESCAPE):
                        self.scene = SCENE_GAME
                elif self.scene == SCENE_SETTINGS and event.type == pygame.KEYDOWN:
                    self._settings_key(event)
                elif (
                    self.scene in (SCENE_LEVEL_COMPLETE, SCENE_GAME_OVER, SCENE_WIN)
                    and event.type == pygame.KEYDOWN
                ):
                    if event.key == pygame.K_RETURN:
                        if self.scene == SCENE_GAME_OVER:
                            retry_level = self.gs.level_index
                            self.gs.reset_session()
                            self.gs.level_index = retry_level
                            self.load_level(retry_level)
                            self.scene = SCENE_GAME
                        elif self.scene == SCENE_LEVEL_COMPLETE:
                            self.load_level(self.gs.level_index)
                            self.scene = SCENE_GAME
                        elif self.scene == SCENE_WIN:
                            # Replay keeps learned AI pressure
                            self.gs.reset_session()
                            self.gs.level_index = 0
                            self.load_level(0)
                            self.scene = SCENE_GAME
                    elif event.key == pygame.K_ESCAPE:
                        self.scene = SCENE_MENU
                        self._start_menu_music()

            if self.scene == SCENE_MENU:
                self.screens.draw_main_menu(self._menu_cursor)
            elif self.scene == SCENE_GAME:
                self.update_game(dt)
                self.draw_game()
            elif self.scene == SCENE_PAUSE:
                self.draw_game()
                self.screens.draw_pause(self._pause_cursor)
            elif self.scene == SCENE_SETTINGS:
                if self._settings_from == SCENE_PAUSE:
                    self.draw_game()
                self.screens.draw_settings(
                    self._settings_cursor,
                    self.settings,
                    self.selected_level,
                    NUM_LEVELS,
                    from_game=(self._settings_from == SCENE_PAUSE),
                )
            elif self.scene == SCENE_LEVEL_COMPLETE:
                self.screens.draw_level_complete(
                    self.gs.score,
                    getattr(self, "_finished_level", self.gs.level_index),
                )
            elif self.scene == SCENE_GAME_OVER:
                self.screens.draw_game_over(self.gs.score)
            elif self.scene == SCENE_WIN:
                self.screens.draw_win_screen(self.gs.score)
            pygame.display.flip()

    def _quit(self):
        if self.ai_ensemble:
            self.ai_ensemble.save_all()
        pygame.quit()
        sys.exit()
