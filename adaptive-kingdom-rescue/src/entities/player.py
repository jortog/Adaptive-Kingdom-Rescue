import pygame
import time as _time
from config import (
    PLAYER_WIDTH, PLAYER_HEIGHT,
    PLAYER_WALK_SPEED, PLAYER_RUN_SPEED, PLAYER_DASH_SPEED,
    PLAYER_DASH_DURATION, PLAYER_DASH_COOLDOWN,
    PLAYER_JUMP_VELOCITY, PLAYER_HOLD_JUMP_BONUS,
    GRAVITY, ACTION_IDLE, ACTION_JUMP, ACTION_RUN, ACTION_DASH, ACTION_ATTACK
)

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, game_state):
        super().__init__()
        self.game_state = game_state
        self.rect = pygame.Rect(x, y, PLAYER_WIDTH, PLAYER_HEIGHT)
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.on_ground = False
        self.facing_right = True

        # Dash
        self.is_dashing    = False
        self.dash_timer    = 0.0
        self.dash_cooldown = 0.0

        # ── Jump (buffered + coyote time) ──────────────────────────
        self.jump_held         = False
        self.jump_held_timer   = 0.0
        self.JUMP_HOLD_MAX     = 0.18
        self.can_double_jump   = False
        self.has_double_jumped = False
        self._jump_buffer_timer = 0.0   # press jump -> buffer 120ms
        self._JUMP_BUFFER_TIME  = 0.12
        self._coyote_timer      = 0.0   # walk off ledge -> still jump 100ms
        self._COYOTE_TIME       = 0.10
        self._was_on_ground     = False

        # Power-ups
        self.size_level   = 1
        self.has_flower   = False
        self.star_timer   = 0.0
        self.shield_count = 0

        # Action recording
        self._action_record_timer    = 0.0
        self._ACTION_RECORD_INTERVAL = 0.2

        # Dummy image for sprite group compatibility
        self.image = pygame.Surface((PLAYER_WIDTH, PLAYER_HEIGHT), pygame.SRCALPHA)

    # ── Input events ──────────────────────────────────────────────────
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_x, pygame.K_LSHIFT):
                self._try_dash()
            if event.key in (pygame.K_z, pygame.K_SPACE):
                # Buffer the jump press
                self._jump_buffer_timer = self._JUMP_BUFFER_TIME
                self.jump_held       = True
                self.jump_held_timer = 0.0
            if event.key in (pygame.K_c, pygame.K_f):
                self._try_attack()
        if event.type == pygame.KEYUP:
            if event.key in (pygame.K_z, pygame.K_SPACE):
                self.jump_held = False

    # ── Main update ───────────────────────────────────────────────────
    def update(self, dt, platforms, game_state):
        keys = pygame.key.get_pressed()

        # 1. Coyote time: grace period after walking off a ledge
        if self._was_on_ground and not self.on_ground:
            self._coyote_timer = self._COYOTE_TIME
        if self.on_ground:
            self._coyote_timer = 0.0
        else:
            self._coyote_timer = max(0.0, self._coyote_timer - dt)

        # 2. Resolve buffered jump
        can_jump = self.on_ground or self._coyote_timer > 0
        if self._jump_buffer_timer > 0 and can_jump:
            self._do_jump()
            self._jump_buffer_timer = 0.0
            self._coyote_timer      = 0.0
        elif self._jump_buffer_timer > 0 and self.can_double_jump and not self.has_double_jumped:
            self._do_jump()
            self.has_double_jumped  = True
            self._jump_buffer_timer = 0.0

        self._jump_buffer_timer = max(0.0, self._jump_buffer_timer - dt)

        # 3. Physics
        self._handle_horizontal(keys, dt)
        self._handle_jump_hold(keys, dt)
        self._apply_gravity(dt)
        self._move_and_collide(platforms, dt)
        self._update_timers(dt)
        self._record_action(dt)

        self._was_on_ground = self.on_ground

    def _do_jump(self):
        self.vel_y         = PLAYER_JUMP_VELOCITY
        self.on_ground     = False
        self.game_state.record_action(ACTION_JUMP)

    def _try_dash(self):
        if self.dash_cooldown <= 0 and not self.is_dashing:
            self.is_dashing    = True
            self.dash_timer    = PLAYER_DASH_DURATION
            self.dash_cooldown = PLAYER_DASH_COOLDOWN
            self.game_state.record_action(ACTION_DASH)

    def _try_attack(self):
        if self.has_flower:
            self.game_state.record_action(ACTION_ATTACK)
            return True
        return False

    def _handle_horizontal(self, keys, dt):
        if self.is_dashing:
            self.vel_x = PLAYER_DASH_SPEED * (1 if self.facing_right else -1)
            return
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x        = -PLAYER_RUN_SPEED
            self.facing_right = False
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x        = PLAYER_RUN_SPEED
            self.facing_right = True
        else:
            self.vel_x = 0

    def _handle_jump_hold(self, keys, dt):
        if self.jump_held:
            if (keys[pygame.K_z] or keys[pygame.K_SPACE]) \
               and self.jump_held_timer < self.JUMP_HOLD_MAX \
               and self.vel_y < 0:
                self.vel_y           += PLAYER_HOLD_JUMP_BONUS * dt / self.JUMP_HOLD_MAX
                self.jump_held_timer += dt
            else:
                self.jump_held = False

    def _apply_gravity(self, dt):
        if not self.on_ground:
            self.vel_y += GRAVITY * dt
            self.vel_y  = min(self.vel_y, 1200)

    def _move_and_collide(self, platforms, dt):
        self.on_ground = False
        self.rect.x   += int(self.vel_x * dt)
        for p in platforms:
            if self.rect.colliderect(p):
                if self.vel_x > 0: self.rect.right = p.left
                elif self.vel_x < 0: self.rect.left = p.right
                self.vel_x = 0
        self.rect.y += int(self.vel_y * dt)
        for p in platforms:
            if self.rect.colliderect(p):
                if self.vel_y > 0:
                    self.rect.bottom = p.top
                    self.on_ground   = True
                    self.vel_y       = 0
                elif self.vel_y < 0:
                    self.rect.top = p.bottom
                    self.vel_y    = 0

    def _update_timers(self, dt):
        if self.is_dashing:
            self.dash_timer -= dt
            if self.dash_timer <= 0:
                self.is_dashing = False
        if self.dash_cooldown > 0:
            self.dash_cooldown -= dt
        if self.star_timer > 0:
            self.star_timer -= dt

    def _record_action(self, dt):
        self._action_record_timer += dt
        if self._action_record_timer >= self._ACTION_RECORD_INTERVAL:
            self._action_record_timer = 0.0
            if abs(self.vel_x) > PLAYER_WALK_SPEED + 10:
                self.game_state.record_action(ACTION_RUN)
            elif self.on_ground:
                self.game_state.record_action(ACTION_IDLE)

    def take_damage(self):
        if self.star_timer > 0:   return False
        if self.shield_count > 0:
            self.shield_count -= 1; return False
        if self.size_level > 1:
            self.size_level -= 1; self.has_flower = False; return False
        return True

    def collect_powerup(self, kind):
        if kind == "mushroom":
            if self.size_level < 2: self.size_level = 2
        elif kind == "flower":
            self.has_flower = True
            if self.size_level < 2: self.size_level = 2
        elif kind == "star":     self.star_timer   = 10.0
        elif kind == "shield":   self.shield_count = min(self.shield_count + 1, 3)
        elif kind == "feather":  self.can_double_jump = True

    # ── Draw ──────────────────────────────────────────────────────────
    def draw(self, surface, camera_offset_x):
        rx = self.rect.x - camera_offset_x
        ry = self.rect.y
        w, h = self.rect.width, self.rect.height

        # Colors
        star_flash = self.star_timer > 0 and int(_time.time() * 10) % 2 == 0
        hat_col    = (255, 210, 0)   if star_flash else (200, 30, 30)
        shirt_col  = (255, 210, 0)   if star_flash else (200, 30, 30)
        skin_col   = (255, 200, 150)
        hair_col   = (120,  70,  20)
        overall    = (30,   80, 200)
        boot_col   = (100,  60,  20)

        # Boots
        boot_h = 7
        boot_y = ry + h - boot_h
        pygame.draw.rect(surface, boot_col, (rx+4, boot_y, (w-10)//2, boot_h), border_radius=2)
        pygame.draw.rect(surface, boot_col, (rx+w//2+2, boot_y, (w-10)//2, boot_h), border_radius=2)

        # Overall legs
        leg_h = h // 4
        pygame.draw.rect(surface, overall, (rx+4, boot_y - leg_h, (w-10)//2, leg_h))
        pygame.draw.rect(surface, overall, (rx+w//2+2, boot_y - leg_h, (w-10)//2, leg_h))

        # Overall bib (body bottom)
        bib_top = ry + h // 2
        pygame.draw.rect(surface, overall, (rx+4, bib_top, w-8, boot_y-leg_h-bib_top+2), border_radius=2)

        # Shirt
        shirt_top = ry + h // 3
        pygame.draw.rect(surface, shirt_col, (rx+5, shirt_top, w-10, h//4+2), border_radius=3)

        # Arms
        arm_y = shirt_top + 2
        arm_h = h // 4
        pygame.draw.rect(surface, shirt_col, (rx+1, arm_y, 6, arm_h), border_radius=2)
        pygame.draw.rect(surface, shirt_col, (rx+w-7, arm_y, 6, arm_h), border_radius=2)
        pygame.draw.circle(surface, skin_col, (rx+4, arm_y+arm_h), 4)
        pygame.draw.circle(surface, skin_col, (rx+w-4, arm_y+arm_h), 4)

        # Head
        head_r  = h // 5 + 2
        head_cx = rx + w // 2
        head_cy = ry + h // 4
        pygame.draw.circle(surface, skin_col, (head_cx, head_cy), head_r)

        # Hat
        hat_h = head_r - 1
        pygame.draw.rect(surface, hat_col, (rx+6, ry+2, w-12, hat_h), border_radius=3)
        pygame.draw.rect(surface, hat_col, (rx+2, ry+hat_h, w-4, 5), border_radius=1)
        pygame.draw.rect(surface, hair_col, (rx+4, head_cy-3, w-8, 6))

        # Eyes
        if self.facing_right:
            pygame.draw.circle(surface, (255,255,255), (head_cx+3, head_cy), 3)
            pygame.draw.circle(surface, (0,0,0),       (head_cx+4, head_cy), 2)
        else:
            pygame.draw.circle(surface, (255,255,255), (head_cx-3, head_cy), 3)
            pygame.draw.circle(surface, (0,0,0),       (head_cx-4, head_cy), 2)

        # Mustache
        msy = head_cy + 4
        pygame.draw.ellipse(surface, hair_col, (head_cx-8, msy, 8, 5))
        pygame.draw.ellipse(surface, hair_col, (head_cx+1, msy, 8, 5))

        # Shield glow
        if self.shield_count > 0:
            pygame.draw.rect(surface, (80, 200, 255),
                             (rx-4, ry-4, w+8, h+8), 2, border_radius=5)
