# main.py
"""
Adaptive Kingdom Rescue — Main Entry Point
==========================================
Run with:  python main.py
"""

import pygame
import sys
import time

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE,
    LEVEL_TIME_LIMIT, TILE_SIZE,
    ACTION_JUMP, ACTION_COUNT,
    STRAT_SPAWN_AERIAL, STRAT_COUNT
)
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
from src.levels.level_base import LevelBase

import numpy as np


# ─── Scene Constants ──────────────────────────────────────────────────────────
SCENE_MENU    = "menu"
SCENE_GAME    = "game"
SCENE_PAUSE   = "pause"
SCENE_LEVEL_COMPLETE = "level_complete"
SCENE_GAME_OVER = "game_over"
SCENE_WIN     = "win"

LEVELS = [Level01, Level02, Level03]

class Game:
    def __init__(self):
        pygame.init()
        self.screen  = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock   = pygame.time.Clock()

        self.gs      = GameState()
        self.hud     = HUD()
        self.screens = ScreenManager(self.screen)
        self.scene   = SCENE_MENU

        self.level        = None
        self.player       = None
        self.enemies      = []
        self.powerups     = []
        self.princess     = None
        self.camera       = None
        self.scoring      = None
        self.ai_ensemble  = None
        self.time_remaining = LEVEL_TIME_LIMIT

        # Flying enemy spawn cooldown
        self._aerial_spawn_cooldown = 0.0
        self.AERIAL_SPAWN_CD = 4.0

    # ── Load a level ──────────────────────────────────────────────────
    def load_level(self, level_index: int):
        level_cls     = LEVELS[min(level_index, len(LEVELS) - 1)]
        self.level    = level_cls()
        self.gs.reset_level()
        self.time_remaining = LEVEL_TIME_LIMIT
        self._aerial_spawn_cooldown = 0.0

        # Player
        self.player = Player(
            self.level.spawn_x, self.level.spawn_y, self.gs
        )

        # Camera
        self.camera = Camera(self.level.pixel_width, self.level.pixel_height)

        # Scoring
        self.scoring = ScoringSystem(self.gs)

        # AI Ensemble (persists across level reloads = AI keeps learning)
        if self.ai_ensemble is None:
            self.ai_ensemble = AIEnsemble(
                level_width=self.level.pixel_width,
                level_time=LEVEL_TIME_LIMIT
            )

        # Spawn enemies
        self.enemies = []
        for spawn in self.level.get_enemy_spawns():
            e = Enemy(
                spawn["x"], spawn["y"],
                enemy_type=spawn.get("type", "ground"),
                patrol_left=spawn.get("patrol_left"),
                patrol_right=spawn.get("patrol_right"),
            )
            self.enemies.append(e)

        # Princess
        px, py = self.level.get_princess_position()
        self.princess = Princess(px, py)

        # Scatter a few power-ups
        self.powerups = self._place_default_powerups()

    def _place_default_powerups(self) -> list:
        rows = len(self.level.TILE_MAP)
        ground_y = (rows - 2) * TILE_SIZE
        return [
            PowerUp(6  * TILE_SIZE, ground_y - TILE_SIZE, "mushroom"),
            PowerUp(14 * TILE_SIZE, ground_y - TILE_SIZE, "flower"),
            PowerUp(20 * TILE_SIZE, ground_y - TILE_SIZE, "star"),
        ]

    # ── Main game update ──────────────────────────────────────────────
    def update_game(self, dt: float):
        self.time_remaining -= dt
        self.gs.level_time_elapsed += dt

        # Player update
        self.player.update(dt, self.level.platforms, self.gs)

        # Camera update
        self.camera.update(self.player.rect, dt)

        # ── AI: build state and decide per enemy ──────────────────
        jump_freq = self.gs.count_recent_action(ACTION_JUMP)
        run_freq  = self.gs.count_recent_action(2)   # ACTION_RUN = 2
        action_hist = self.gs.get_action_history_padded()

        ppo_state = self.ai_ensemble.ppo.build_state(
            self.gs.level_time_elapsed,
            self.gs.lives,
            len(self.enemies),
            abs(self.princess.rect.centerx - self.player.rect.centerx),
            jump_freq, run_freq,
            self.player.vel_x,
            self.player.size_level,
        )

        for enemy in self.enemies:
            if not enemy.alive:
                continue
            cmd = self.ai_ensemble.decide(
                enemy.rect, self.player.rect,
                self.player.vel_x,
                jump_freq, run_freq,
                len(self.enemies),
                self.player.size_level,
                action_hist, dt, ppo_state
            )
            enemy.set_command(cmd)
            enemy.update(dt, self.player.rect, self.level.platforms)

        # ── Spawn aerial enemy if AI commands it ─────────────────
        self._aerial_spawn_cooldown -= dt
        if (self.ai_ensemble._ppo_action == STRAT_SPAWN_AERIAL
                and self._aerial_spawn_cooldown <= 0
                and jump_freq >= 3):
            self._spawn_aerial_enemy()
            self._aerial_spawn_cooldown = self.AERIAL_SPAWN_CD

        # ── PPO rewards ──────────────────────────────────────────
        self.ai_ensemble.ppo.reward_prevention()
        if self.ai_ensemble.ppo._update_timer < dt * 2:
            if jump_freq > 2 and run_freq > 2:
                self.ai_ensemble.ppo.reward_variety()

        # ── Collision: player ↔ enemies ───────────────────────────
        self._check_player_enemy_collisions()

        # ── Collision: player ↔ hazards ───────────────────────────
        for hz in self.level.hazards:
            if self.player.rect.colliderect(hz):
                self._player_die()
                return

        # ── Collision: player ↔ power-ups ────────────────────────
        for pu in list(self.powerups):
            if self.player.rect.colliderect(pu.rect):
                if pu.kind == "oneup":
                    self.gs.lives = min(self.gs.lives + 1, 9)
                else:
                    self.player.collect_powerup(pu.kind)
                self.scoring.award_powerup(pu.kind)
                self.powerups.remove(pu)

        # ── Win: player touches princess ──────────────────────────
        if self.player.rect.colliderect(self.princess.rect):
            self._level_complete()
            return

        # ── Lose: fall off screen ────────────────────────────────
        if self.player.rect.top > self.level.pixel_height + 100:
            self._player_die()
            return

        # ── Lose: time up ─────────────────────────────────────────
        if self.time_remaining <= 0:
            self._player_die()

    def _check_player_enemy_collisions(self):
        for enemy in list(self.enemies):
            if not enemy.alive:
                continue
            if not self.player.rect.colliderect(enemy.rect):
                continue

            # Stomp detection: player bottom overlaps top 10% of enemy
            stomp_zone_height = enemy.rect.height * 0.10
            stomp_zone = pygame.Rect(
                enemy.rect.x,
                enemy.rect.y,
                enemy.rect.width,
                stomp_zone_height
            )
            player_bottom_rect = pygame.Rect(
                self.player.rect.x,
                self.player.rect.bottom - 4,
                self.player.rect.width, 4
            )

            if player_bottom_rect.colliderect(stomp_zone) and self.player.vel_y > 0:
                # Stomp!
                was_airborne = not self.player.on_ground
                enemy.die()
                self.enemies.remove(enemy)
                self.player.vel_y = -400  # bounce
                pts = self.scoring.award_enemy_defeat(enemy.enemy_type, was_airborne)
            else:
                # Damage player
                died = self.player.take_damage()
                if died:
                    self.gs.lives -= 1
                    self._player_die()

    def _spawn_aerial_enemy(self):
        import random
        x = self.player.rect.centerx + random.randint(-TILE_SIZE, TILE_SIZE)
        y = self.player.rect.top - 3 * TILE_SIZE
        fly = Enemy(x, y, enemy_type="flying")
        fly.set_command(1)  # Chase immediately
        self.enemies.append(fly)

    def _player_die(self):
        if self.gs.level_time_elapsed < 5.0:
            self.ai_ensemble.ppo.penalty_fast_death()
        self.gs.player_deaths_this_level += 1
        if self.gs.lives <= 0:
            self.scene = SCENE_GAME_OVER
        else:
            # Restart level; AI keeps learning
            lv = self.gs.level_index
            self.load_level(lv)

    def _level_complete(self):
        self.scoring.award_level_complete(
            self.time_remaining,
            self.gs.damage_taken_this_level == 0
        )
        self.ai_ensemble.learn_after_level(
            list(self.gs.action_history)
        )
        self.ai_ensemble.save_all()
        self.gs.level_index += 1
        if self.gs.level_index >= len(LEVELS):
            self.scene = SCENE_WIN
        else:
            self.scene = SCENE_LEVEL_COMPLETE

    # ── Draw everything ───────────────────────────────────────────────
    def draw_game(self):
        cam_x = self.camera.int_x
        self.level.draw_tiles(self.screen, cam_x)

        # Power-ups
        for pu in self.powerups:
            pu.draw(self.screen, cam_x)

        # Princess
        self.princess.update_bob(1/60)
        self.princess.draw(self.screen, cam_x)

        # Enemies
        for e in self.enemies:
            e.draw(self.screen, cam_x)

        # Player
        self.player.draw(self.screen, cam_x)

        # HUD
        self.hud.draw(
            self.screen, self.gs,
            self.time_remaining,
            self.ai_ensemble.rnn_confidence if self.ai_ensemble else 0.0
        )

    # ── Main loop ─────────────────────────────────────────────────────
    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0  # seconds
            dt = min(dt, 0.05)
            self.screens.tick(dt)
            # ── Event handling ────────────────────────────────────
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._quit()

                if self.scene == SCENE_MENU:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            self.load_level(self.gs.level_index)
                            self.scene = SCENE_GAME
                        elif event.key == pygame.K_ESCAPE:
                            self._quit()

                elif self.scene == SCENE_GAME:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_p:
                            self.scene = SCENE_PAUSE
                        elif event.key == pygame.K_ESCAPE:
                            self.scene = SCENE_MENU
                    if self.player:
                        self.player.handle_event(event)

                elif self.scene == SCENE_PAUSE:
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                        self.scene = SCENE_GAME

                elif self.scene in (SCENE_LEVEL_COMPLETE, SCENE_GAME_OVER, SCENE_WIN):
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            if self.scene == SCENE_GAME_OVER:
                                self.gs.lives = 3
                                self.load_level(self.gs.level_index)
                                self.scene = SCENE_GAME
                            elif self.scene == SCENE_LEVEL_COMPLETE:
                                self.load_level(self.gs.level_index)
                                self.scene = SCENE_GAME
                            elif self.scene == SCENE_WIN:
                                self.gs.challenge_mode = True
                                self.gs.level_index = 0
                                self.load_level(0)
                                self.scene = SCENE_GAME
                        elif event.key == pygame.K_ESCAPE:
                            self.scene = SCENE_MENU

            # ── Scene rendering ───────────────────────────────────
            if self.scene == SCENE_MENU:
                self.screens.draw_main_menu()

            elif self.scene == SCENE_GAME:
                self.update_game(dt)
                self.draw_game()

            elif self.scene == SCENE_PAUSE:
                self.draw_game()
                self.screens.draw_pause()

            elif self.scene == SCENE_LEVEL_COMPLETE:
                self.screens.draw_level_complete(self.gs.score, self.gs.level_index - 1)

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


import pygame  # already imported above — needed here for Rect in collision
if __name__ == "__main__":
    Game().run()