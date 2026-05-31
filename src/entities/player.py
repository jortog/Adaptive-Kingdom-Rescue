import pygame
import time as _time
from config import (
    PLAYER_WIDTH,
    PLAYER_HEIGHT,
    PLAYER_WALK_SPEED,
    PLAYER_RUN_SPEED,
    PLAYER_JUMP_VELOCITY,
    PLAYER_HOLD_JUMP_BONUS,
    GRAVITY,
    ACTION_IDLE,
    ACTION_JUMP,
    ACTION_RUN,
)

# Keys that trigger / hold a jump.
JUMP_KEYS = (pygame.K_z, pygame.K_SPACE, pygame.K_UP, pygame.K_w)


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, game_state):
        super().__init__()
        self.game_state = game_state
        self.game = None  # Reference to Game instance
        self.rect = pygame.Rect(x, y, PLAYER_WIDTH, PLAYER_HEIGHT)
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.on_ground = False
        self.facing_right = True
        self.jump_held = False
        self.jump_held_timer = 0.0
        self.JUMP_HOLD_MAX = 0.18
        self.can_double_jump = False
        self.has_double_jumped = False
        self._jump_buffer_timer = 0.0
        self._JUMP_BUFFER_TIME = 0.12
        self._coyote_timer = 0.0
        self._COYOTE_TIME = 0.12
        self._was_on_ground = False
        self.size_level = 1
        self.star_timer = 0.0
        self.shield_count = 0
        self._action_record_timer = 0.0
        self._ACTION_RECORD_INTERVAL = 0.2
        self._walk_phase = 0.0
        self.audio = None
        self.image = pygame.Surface(
            (PLAYER_WIDTH, PLAYER_HEIGHT), pygame.SRCALPHA)
        self.invincible_timer = 0.0
        self.INVINCIBLE_DURATION = 1.0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in JUMP_KEYS:
                self._jump_buffer_timer = self._JUMP_BUFFER_TIME
                self.jump_held = True
                self.jump_held_timer = 0.0
        if event.type == pygame.KEYUP:
            if event.key in JUMP_KEYS:
                self.jump_held = False

    def update(self, dt, platforms, enemies=None, level_width=None):
        """
        Update player state
        Args:
            dt: Delta time in seconds
            platforms: List of platform rects
            enemies: List of enemy sprites or None
            level_width: Level width boundary or None
        """
        # Handle incorrectly ordered parameters
        if isinstance(enemies, (int, float)) and level_width is None:
            level_width = enemies
            enemies = None
        elif isinstance(level_width, (list, tuple)) and enemies is None:
            enemies = level_width
            level_width = None
        elif isinstance(level_width, list) and enemies is not None and isinstance(enemies, (int, float)):
            temp = level_width
            level_width = enemies
            enemies = temp

        if enemies is None:
            enemies = []

        # Update invincibility
        if self.invincible_timer > 0:
            self.invincible_timer -= dt

        keys = pygame.key.get_pressed()
        if self._was_on_ground and not self.on_ground:
            self._coyote_timer = self._COYOTE_TIME
        if self.on_ground:
            self._coyote_timer = 0.0
        else:
            self._coyote_timer = max(0.0, self._coyote_timer - dt)

        can_jump = self.on_ground or self._coyote_timer > 0
        if self._jump_buffer_timer > 0 and can_jump:
            self._do_jump()
            self._jump_buffer_timer = 0.0
            self._coyote_timer = 0.0
        elif (
            self._jump_buffer_timer > 0
            and self.can_double_jump
            and not self.has_double_jumped
        ):
            self._do_jump()
            self.has_double_jumped = True
            self._jump_buffer_timer = 0.0
        self._jump_buffer_timer = max(0.0, self._jump_buffer_timer - dt)

        self._handle_horizontal(keys, dt)
        self._handle_jump_hold(keys, dt)
        self._apply_gravity(dt)
        self._move_and_collide(platforms, enemies, dt, level_width)
        self._update_timers(dt)
        self._record_action(dt)

        if abs(self.vel_x) > 10 and self.on_ground:
            self._walk_phase += dt * 12
        else:
            self._walk_phase = 0.0

        self._was_on_ground = self.on_ground

    def _do_jump(self):
        self.vel_y = PLAYER_JUMP_VELOCITY
        self.on_ground = False
        if self.game_state:
            self.game_state.record_action(ACTION_JUMP)
        if self.audio:
            self.audio.play_jump()

    def _handle_horizontal(self, keys, dt):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -PLAYER_RUN_SPEED
            self.facing_right = False
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = PLAYER_RUN_SPEED
            self.facing_right = True
        else:
            self.vel_x = 0

    def _handle_jump_hold(self, keys, dt):
        if self.jump_held:
            if (
                any(keys[k] for k in JUMP_KEYS)
                and self.jump_held_timer < self.JUMP_HOLD_MAX
                and self.vel_y < 0
            ):
                self.vel_y += PLAYER_HOLD_JUMP_BONUS * dt / self.JUMP_HOLD_MAX
                self.jump_held_timer += dt
            else:
                self.jump_held = False

    def _apply_gravity(self, dt):
        if not self.on_ground:
            self.vel_y += GRAVITY * dt
            self.vel_y = min(self.vel_y, 1200)

    def _move_and_collide(self, platforms, enemies, dt, level_width=None):
        # Horizontal movement
        self.rect.x += int(self.vel_x * dt)

        for p in platforms:
            if self.rect.colliderect(p):
                if self.vel_x > 0:
                    self.rect.right = p.left
                elif self.vel_x < 0:
                    self.rect.left = p.right
                self.vel_x = 0

        # Level boundaries
        if self.rect.left < 0:
            self.rect.left = 0
            self.vel_x = max(0, self.vel_x)
        if level_width is not None and self.rect.right > level_width:
            self.rect.right = level_width
            self.vel_x = min(0, self.vel_x)

        # Vertical movement
        self.rect.y += int(self.vel_y * dt)
        self.on_ground = False

        for p in platforms:
            if self.rect.colliderect(p):
                if self.vel_y > 0:
                    self.rect.bottom = p.top
                    self.on_ground = True
                    self.vel_y = 0
                elif self.vel_y < 0:
                    self.rect.top = p.bottom
                    self.vel_y = 0

        # Enemy collision - FIXED VERSION
        if enemies and isinstance(enemies, (list, tuple)):
            for enemy in enemies:
                if not hasattr(enemy, 'is_alive') or not enemy.is_alive:
                    continue

                if self.rect.colliderect(enemy.rect):
                    # Check if player is stomping from above (vel_y positive = falling down)
                    # Made threshold lower from 50 to 20 to make stomping easier
                    is_stomping = self.vel_y > 20 and self.rect.bottom <= enemy.rect.centery + 10

                    if is_stomping:
                        # Player stomps enemy
                        enemy.die()
                        self.vel_y = -400  # Bounce up
                        self.on_ground = False
                        if self.game_state:
                            self.game_state.record_action(ACTION_JUMP)
                        if self.audio and hasattr(self.audio, 'play_enemy_stomp'):
                            self.audio.play_enemy_stomp()
                        if hasattr(self.game_state, 'ai_ensemble') and self.game_state.ai_ensemble:
                            self.game_state.ai_ensemble.record_enemy_outcome(
                                enemy.rect, self.rect, False, True
                            )
                    else:
                        # Enemy hits player - TAKE DAMAGE
                        if self.invincible_timer <= 0:
                            # Apply damage
                            if self.star_timer <= 0:  # Only take damage if not invincible from star
                                damaged = self.take_damage()

                                if damaged:
                                    # Player died
                                    if hasattr(self.game_state, 'lives'):
                                        self.game_state.lives -= 1
                                        self.game_state.player_deaths_this_level += 1
                                        self.game_state.damage_taken_this_level += 1

                                    # Signal death to game
                                    if self.game:
                                        self.game.player_died_from_enemy()
                                    elif self.game_state and hasattr(self.game_state, 'game'):
                                        self.game_state.game.player_died_from_enemy()

                                    if self.audio and hasattr(self.audio, 'play_death'):
                                        self.audio.play_death()
                                else:
                                    # Just lost a power-up or shield
                                    self.invincible_timer = self.INVINCIBLE_DURATION
                                    if self.audio and hasattr(self.audio, 'play_hurt'):
                                        self.audio.play_hurt()
                            else:
                                # Star power - enemy dies instead
                                enemy.die()
                                if self.audio and hasattr(self.audio, 'play_enemy_stomp'):
                                    self.audio.play_enemy_stomp()

                            if hasattr(self.game_state, 'ai_ensemble') and self.game_state.ai_ensemble:
                                self.game_state.ai_ensemble.record_enemy_outcome(
                                    enemy.rect, self.rect, True, False
                                )

    def _update_timers(self, dt):
        if self.star_timer > 0:
            self.star_timer -= dt

    def _record_action(self, dt):
        self._action_record_timer += dt
        if self._action_record_timer >= self._ACTION_RECORD_INTERVAL:
            self._action_record_timer = 0.0
            if abs(self.vel_x) > PLAYER_WALK_SPEED + 10:
                if self.game_state:
                    self.game_state.record_action(ACTION_RUN)
            elif self.on_ground:
                if self.game_state:
                    self.game_state.record_action(ACTION_IDLE)

    def take_damage(self):
        if self.star_timer > 0:
            return False
        if self.shield_count > 0:
            self.shield_count -= 1
            return False
        if self.size_level > 1:
            self.size_level -= 1
            return False
        return True  # Player dies

    def collect_powerup(self, kind):
        """Collect a powerup"""
        if kind == "mushroom":
            if self.size_level < 2:
                self.size_level = 2
                if self.audio and hasattr(self.audio, 'play_power'):
                    self.audio.play_power()
        elif kind == "flower":
            if self.size_level < 2:
                self.size_level = 2
                if self.audio and hasattr(self.audio, 'play_power'):
                    self.audio.play_power()
        elif kind == "star":
            self.star_timer = 10.0
            if self.audio and hasattr(self.audio, 'play_power'):
                self.audio.play_power()
        elif kind == "shield":
            self.shield_count = min(self.shield_count + 1, 3)
            if self.audio and hasattr(self.audio, 'play_power'):
                self.audio.play_power()
        elif kind == "feather":
            self.can_double_jump = True
            if self.audio and hasattr(self.audio, 'play_power'):
                self.audio.play_power()
        elif kind == "oneup":
            if self.audio and hasattr(self.audio, 'play_power'):
                self.audio.play_power()

    def draw(self, surface, camera_offset_x, world_y_offset=0):
        import math

        rx = self.rect.x - camera_offset_x
        ry = self.rect.y + world_y_offset
        w, h = self.rect.width, self.rect.height
        fr = self.facing_right
        flip = 1 if fr else -1
        cx = rx + w // 2

        if self.invincible_timer > 0 and int(_time.time() * 10) % 2 == 0:
            return

        star_flash = self.star_timer > 0 and int(_time.time() * 10) % 2 == 0
        steel_d = (88, 96, 108) if not star_flash else (210, 180, 40)
        steel_m = (140, 150, 164) if not star_flash else (255, 220, 80)
        steel_l = (190, 198, 210) if not star_flash else (255, 245, 160)
        horn = (235, 238, 245)
        leather = (96, 62, 32)

        leg_off = int(math.sin(self._walk_phase) * 3) if self.on_ground else 0

        pygame.draw.rect(
            surface, steel_d, (cx - 9, ry + h - 12 + leg_off, 7, 12), border_radius=2
        )
        pygame.draw.rect(
            surface, steel_d, (cx + 2, ry + h - 12 - leg_off, 7, 12), border_radius=2
        )
        pygame.draw.rect(
            surface, steel_m, (cx - 9, ry + h - 12 + leg_off, 7, 4), border_radius=2
        )
        pygame.draw.rect(
            surface, steel_m, (cx + 2, ry + h - 12 - leg_off, 7, 4), border_radius=2
        )

        body = pygame.Rect(cx - 11, ry + h // 3, 22, h // 2)
        pygame.draw.rect(surface, steel_m, body, border_radius=4)
        pygame.draw.rect(
            surface,
            steel_l,
            (body.x + 2, body.y + 2, body.width - 4, 6),
            border_radius=3,
        )
        pygame.draw.rect(surface, steel_d,
                         (body.x, body.centery, body.width, 2))
        pygame.draw.rect(surface, leather,
                         (body.x, body.bottom - 5, body.width, 5))
        pygame.draw.rect(surface, (210, 180, 60),
                         (cx - 3, body.bottom - 5, 6, 5))

        sh_x = cx - 16 * flip
        pygame.draw.ellipse(
            surface, steel_d, (sh_x - 7, ry + h // 2 - 6, 14, 22))
        pygame.draw.ellipse(
            surface, steel_l, (sh_x - 5, ry + h // 2 - 4, 10, 18))
        pygame.draw.line(
            surface, steel_d, (sh_x, ry + h // 2 -
                               4), (sh_x, ry + h // 2 + 13), 1
        )

        sw_x = cx + 13 * flip
        pygame.draw.line(
            surface, steel_l, (sw_x, ry + h // 2 + 6), (sw_x, ry + h // 4), 3
        )
        pygame.draw.line(
            surface,
            leather,
            (sw_x - 3 * flip, ry + h // 2 + 3),
            (sw_x + 3 * flip, ry + h // 2 + 3),
            3,
        )

        hy = ry + 2
        helm = pygame.Rect(cx - 9, hy, 18, h // 3 + 2)
        pygame.draw.rect(surface, steel_m, helm, border_radius=5)
        pygame.draw.rect(
            surface,
            steel_l,
            (helm.x + 2, helm.y + 1, helm.width - 4, 4),
            border_radius=3,
        )
        pygame.draw.rect(
            surface, (20, 24, 30), (helm.x + 3,
                                    helm.centery, helm.width - 6, 3)
        )
        pygame.draw.rect(
            surface, (20, 24, 30), (cx - 1, helm.y + 5, 2, helm.height - 9)
        )
        pygame.draw.polygon(
            surface,
            horn,
            [(helm.x - 1, hy + 4), (helm.x - 7, hy - 4), (helm.x + 2, hy + 1)],
        )
        pygame.draw.polygon(
            surface,
            horn,
            [
                (helm.right + 1, hy + 4),
                (helm.right + 7, hy - 4),
                (helm.right - 2, hy + 1),
            ],
        )

        if self.shield_count > 0:
            pygame.draw.rect(
                surface,
                (80, 200, 255),
                (rx - 4, ry - 4, w + 8, h + 8),
                2,
                border_radius=6,
            )
