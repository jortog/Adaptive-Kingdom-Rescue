import pygame
import math
from config import (
    ENEMY_GROUND_WIDTH,
    ENEMY_GROUND_HEIGHT,
    ENEMY_FLYING_WIDTH,
    ENEMY_FLYING_HEIGHT,
    ENEMY_PATROL_SPEED,
    ENEMY_CHASE_SPEED,
    GRAVITY,
    TILE_SIZE,
    STRAT_PATROL,
    STRAT_CHASE,
    STRAT_AMBUSH,
    STRAT_RETREAT,
    STRAT_BLOCK_UPPER,
    STRAT_BLOCK_LOWER,
    STRAT_SPAWN_AERIAL,
)

_FONT = None
_LBL_CACHE = {}


def _font():
    global _FONT
    if _FONT is None:
        _FONT = pygame.font.SysFont("Arial", 11, bold=True)
    return _FONT


def _badge_label(state):
    if state not in _LBL_CACHE:
        _LBL_CACHE[state] = _font().render(state[:3].upper(), True, (255, 255, 255))
    return _LBL_CACHE[state]


BADGE_COL = {
    "patrol": (100, 100, 100),
    "chase": (210, 40, 40),
    "ambush": (190, 95, 0),
    "retreat": (40, 90, 200),
    "block_upper": (90, 40, 190),
    "block_lower": (90, 40, 190),
}


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, enemy_type="ground", patrol_left=None, patrol_right=None):
        super().__init__()
        self.enemy_type = enemy_type
        if enemy_type == "flying":
            w, h = ENEMY_FLYING_WIDTH, ENEMY_FLYING_HEIGHT
            self.affected_by_gravity = False
        elif enemy_type == "flophopper":
            w, h = ENEMY_GROUND_WIDTH + 4, ENEMY_GROUND_HEIGHT
            self.affected_by_gravity = True
        else:  # ground (Hop-Chop)
            w, h = ENEMY_GROUND_WIDTH, ENEMY_GROUND_HEIGHT
            self.affected_by_gravity = True
        self.rect = pygame.Rect(x, y, w, h)
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        self.vel_x = -ENEMY_PATROL_SPEED
        self.vel_y = 0.0
        self.patrol_left = patrol_left if patrol_left else x - 3 * TILE_SIZE
        self.patrol_right = patrol_right if patrol_right else x + 3 * TILE_SIZE
        self.state = "patrol"
        self.alive = True
        self.on_ground = False
        self.current_command = STRAT_PATROL
        # hop timer for hop-chop and flophopper
        self._hop_timer = 0.0
        self._hop_interval = 0.8 if enemy_type == "ground" else 0.5
        self._anim = 0.0

    def set_command(self, command):
        self.current_command = command
        state_map = {
            STRAT_PATROL: "patrol",
            STRAT_CHASE: "chase",
            STRAT_AMBUSH: "ambush",
            STRAT_RETREAT: "retreat",
            STRAT_BLOCK_UPPER: "block_upper",
            STRAT_BLOCK_LOWER: "block_lower",
            STRAT_SPAWN_AERIAL: "ambush",
        }
        self.state = state_map.get(command, "patrol")

    def mirror_jump(self, player_vel_y):
        """Called externally when player jumps — flophopper mirrors."""
        if self.enemy_type == "flophopper" and self.on_ground:
            self.vel_y = player_vel_y * 0.85
            self.on_ground = False

    def update(self, dt, player_rect, platforms):
        if not self.alive:
            return
        self._anim += dt

        # Hop behavior for ground/flophopper
        if self.enemy_type in ("ground", "flophopper") and self.on_ground:
            self._hop_timer += dt
            if self._hop_timer >= self._hop_interval:
                self._hop_timer = 0.0
                hop = -380 if self.enemy_type == "ground" else -520
                # Leap higher to mount a platform when chasing a player above us.
                if self.state in ("chase", "ambush") and player_rect.bottom < self.rect.top - 8:
                    hop = -640
                self.vel_y = hop
                self.on_ground = False

        # Horizontal behavior by state
        if self.state == "patrol":
            self.rect.x += int(self.vel_x * dt)
        elif self.state == "chase":
            d = 1 if player_rect.centerx > self.rect.centerx else -1
            self.vel_x = ENEMY_CHASE_SPEED * d
            self.rect.x += int(self.vel_x * dt)
            if self.enemy_type == "flying":
                # Home onto the player's height so aerial enemies actually chase
                # the player up onto platforms instead of holding spawn altitude.
                ty = player_rect.centery - self.rect.height // 2
                self.rect.y += int((ty - self.rect.y) * 3.0 * dt)
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
        elif self.state in ("block_upper", "block_lower"):
            d = 1 if player_rect.centerx > self.rect.centerx else -1
            self.vel_x = ENEMY_PATROL_SPEED * 0.6 * d
            self.rect.x += int(self.vel_x * dt)
            if self.enemy_type == "flying":
                target_y = (
                    player_rect.top - 2 * TILE_SIZE
                    if self.state == "block_upper"
                    else player_rect.bottom
                )
                self.rect.y += int((target_y - self.rect.y) * 3.0 * dt)

        # Gravity / collisions
        if self.affected_by_gravity:
            if not self.on_ground:
                self.vel_y += GRAVITY * dt
                self.vel_y = min(self.vel_y, 1200)
            self.on_ground = False
            self.rect.y += int(self.vel_y * (1 / 60))
            for p in platforms:
                if self.rect.colliderect(p) and self.vel_y >= 0:
                    self.rect.bottom = p.top
                    self.on_ground = True
                    self.vel_y = 0

        # Patrol boundary turn
        if self.state == "patrol":
            if self.rect.left < self.patrol_left:
                self.vel_x = ENEMY_PATROL_SPEED
            elif self.rect.right > self.patrol_right:
                self.vel_x = -ENEMY_PATROL_SPEED

    def die(self):
        self.alive = False
        self.kill()

    def draw(self, surface, camera_offset_x, world_y_offset=0):
        if not self.alive:
            return
        rx = self.rect.x - camera_offset_x
        ry = self.rect.y + world_y_offset
        w, h = self.rect.width, self.rect.height
        _cx, cy = rx + w // 2, ry + h // 2

        if self.enemy_type == "ground":
            # Hop-Chop: green/yellow blocky frog
            wob = int(math.sin(self._anim * 8) * 2) if self.on_ground else 0
            # Feet
            pygame.draw.rect(
                surface, (220, 180, 30), (rx + 2, ry + h - 6, 8, 6), border_radius=2
            )
            pygame.draw.rect(
                surface,
                (220, 180, 30),
                (rx + w - 10, ry + h - 6, 8, 6),
                border_radius=2,
            )
            # Body block
            body = pygame.Rect(rx + 1, ry + 6 + wob, w - 2, h - 10)
            pygame.draw.rect(surface, (60, 170, 75), body, border_radius=4)
            pygame.draw.rect(
                surface,
                (95, 210, 100),
                (body.x + 2, body.y + 2, body.width - 4, 6),
                border_radius=2,
            )
            pygame.draw.rect(surface, (35, 110, 45), body, 2, border_radius=4)
            # Yellow belly stripe
            pygame.draw.rect(
                surface,
                (245, 210, 40),
                (body.x + 4, body.bottom - 7, body.width - 8, 5),
            )
            # Spikes on top
            for i in range(3):
                sx = body.x + 6 + i * ((body.width - 12) // 2)
                pygame.draw.polygon(
                    surface,
                    (245, 210, 40),
                    [(sx, body.y), (sx + 4, body.y - 5), (sx + 8, body.y)],
                )
            # Eyes
            ey = body.y + 10
            pygame.draw.circle(surface, (255, 255, 255), (body.x + 8, ey), 3)
            pygame.draw.circle(surface, (255, 255, 255), (body.right - 8, ey), 3)
            pygame.draw.circle(surface, (20, 20, 20), (body.x + 8, ey + 1), 2)
            pygame.draw.circle(surface, (20, 20, 20), (body.right - 8, ey + 1), 2)

        elif self.enemy_type == "flophopper":
            # Flophopper: red dome bug with eyes and yellow feet
            wob = int(math.sin(self._anim * 6) * 1)
            # Yellow feet
            pygame.draw.ellipse(surface, (245, 210, 40), (rx - 2, ry + h - 7, 12, 8))
            pygame.draw.ellipse(
                surface, (245, 210, 40), (rx + w - 10, ry + h - 7, 12, 8)
            )
            # Red dome body
            pygame.draw.ellipse(surface, (195, 40, 40), (rx, ry + wob, w, h - 2))
            pygame.draw.ellipse(
                surface, (235, 90, 90), (rx + 4, ry + 2 + wob, w - 8, h // 2)
            )
            pygame.draw.ellipse(surface, (120, 20, 20), (rx, ry + wob, w, h - 2), 2)
            # Highlight stripe
            pygame.draw.line(
                surface,
                (255, 255, 255),
                (rx + w // 4, ry + 5 + wob),
                (rx + w // 2, ry + 3 + wob),
                2,
            )
            # Big cartoon eyes
            ey = cy - 2 + wob
            pygame.draw.circle(surface, (255, 255, 255), (rx + w // 3, ey), 5)
            pygame.draw.circle(surface, (255, 255, 255), (rx + 2 * w // 3, ey), 5)
            pygame.draw.circle(surface, (20, 20, 20), (rx + w // 3 + 1, ey + 1), 3)
            pygame.draw.circle(surface, (20, 20, 20), (rx + 2 * w // 3 + 1, ey + 1), 3)
            pygame.draw.circle(surface, (255, 255, 255), (rx + w // 3 + 2, ey), 1)
            pygame.draw.circle(surface, (255, 255, 255), (rx + 2 * w // 3 + 2, ey), 1)

        else:  # flying — purple ghost bird
            flap = int(math.sin(self._anim * 10) * 3)
            # Wings (flap)
            pygame.draw.polygon(
                surface,
                (220, 170, 255),
                [(rx - 6, cy - flap), (rx + 4, ry - 2), (rx + 10, cy)],
            )
            pygame.draw.polygon(
                surface,
                (220, 170, 255),
                [(rx + w + 6, cy - flap), (rx + w - 4, ry - 2), (rx + w - 10, cy)],
            )
            pygame.draw.polygon(
                surface,
                (160, 110, 210),
                [(rx - 6, cy - flap), (rx + 4, ry - 2), (rx + 10, cy)],
                1,
            )
            pygame.draw.polygon(
                surface,
                (160, 110, 210),
                [(rx + w + 6, cy - flap), (rx + w - 4, ry - 2), (rx + w - 10, cy)],
                1,
            )
            # Round purple body (ghost shape)
            pygame.draw.ellipse(surface, (140, 90, 200), (rx, ry, w, h + 4))
            pygame.draw.ellipse(
                surface, (180, 130, 230), (rx + 3, ry + 2, w - 6, h // 2)
            )
            pygame.draw.ellipse(surface, (80, 40, 130), (rx, ry, w, h + 4), 2)
            # Eyes (yellow ovals)
            ey = ry + h // 3
            pygame.draw.ellipse(surface, (0, 0, 0), (rx + w // 4 - 3, ey - 4, 8, 10))
            pygame.draw.ellipse(
                surface, (0, 0, 0), (rx + 3 * w // 4 - 5, ey - 4, 8, 10)
            )
            pygame.draw.ellipse(
                surface, (255, 225, 60), (rx + w // 4 - 1, ey - 2, 4, 6)
            )
            pygame.draw.ellipse(
                surface, (255, 225, 60), (rx + 3 * w // 4 - 3, ey - 2, 4, 6)
            )

        # Badge
        bcol = BADGE_COL.get(self.state, (100, 100, 100))
        lbl = _badge_label(self.state)
        bx = rx + w // 2 - lbl.get_width() // 2
        pygame.draw.rect(
            surface, bcol, (bx - 2, ry - 16, lbl.get_width() + 4, 14), border_radius=3
        )
        surface.blit(lbl, (bx, ry - 15))
