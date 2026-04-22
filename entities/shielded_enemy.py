import pygame
import random
import math
from settings import (
    WORLD_W, WORLD_H,
    SPAWN_MARGIN,
    SHIELDED_ENEMY_RADIUS,
    SHIELDED_COL, SHIELDED_GLOW,
    SHIELD_DURATION, SHIELD_COOLDOWN,
)


class ShieldedEnemy(pygame.sprite.Sprite):
    def __init__(self, player, speed: float = 2.5, hp: int = 2, radius: int = None):
        super().__init__()
        self.player    = player
        self.speed     = speed
        self.hp        = hp
        self.max_hp    = hp
        self.radius    = radius if radius is not None else SHIELDED_ENEMY_RADIUS

        # Shield: starts ON for 5s, then OFF for 3s, repeating
        self.shielded     = True
        self.shield_timer = SHIELD_DURATION   # countdown current phase
        self._pulse       = 0.0

        self.frozen       = False
        self.freeze_timer = 0

        self.pos = pygame.Vector2(*self._spawn_pos())
        sz = self.radius * 2 + 12   # extra room for shield ring
        self.image = pygame.Surface((sz, sz), pygame.SRCALPHA)
        self.rect  = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        self._draw_surface()

    # ------------------------------------------------------------------ #
    def _spawn_pos(self) -> tuple:
        for _ in range(30):
            side = random.randint(0, 3)
            m = SPAWN_MARGIN
            if side == 0:
                x, y = random.randint(m, WORLD_W - m), m
            elif side == 1:
                x, y = random.randint(m, WORLD_W - m), WORLD_H - m
            elif side == 2:
                x, y = m, random.randint(m, WORLD_H - m)
            else:
                x, y = WORLD_W - m, random.randint(m, WORLD_H - m)
            if (pygame.Vector2(x, y) - self.player.pos).length() > 300:
                return x, y
        return random.randint(m, WORLD_W - m), m

    # ------------------------------------------------------------------ #
    def _draw_surface(self):
        sz = self.radius * 2 + 12
        self.image = pygame.Surface((sz, sz), pygame.SRCALPHA)
        cx = cy = sz // 2

        # Glow
        pygame.draw.circle(self.image, (*SHIELDED_GLOW, 60), (cx, cy), self.radius)

        # HP colour tint
        hp_ratio = self.hp / self.max_hp
        r = int(50 + (1 - hp_ratio) * 80)
        g = int(180 + (1 - hp_ratio) * (-130))
        b = 255
        pygame.draw.circle(self.image, (r, max(0, g), b), (cx, cy), self.radius - 2)

        # HP bar
        if self.max_hp > 1:
            bar_w = self.radius * 2 - 4
            bar_h = 4
            bx = cx - self.radius + 2
            by = cy - self.radius - 6
            pygame.draw.rect(self.image, (20, 40, 80),   (bx, by, bar_w, bar_h))
            fill = int(bar_w * self.hp / self.max_hp)
            pygame.draw.rect(self.image, SHIELDED_COL,   (bx, by, fill,  bar_h))

        # Highlight
        pygame.draw.circle(self.image, (255, 255, 255),
                           (cx + self.radius // 4, cy - self.radius // 4), 3)

        # Shield ring
        if self.shielded:
            self._pulse = (self._pulse + 0.18) % (2 * math.pi)
            alpha = int(160 + 80 * math.sin(self._pulse))
            ring_r = self.radius + 5
            pygame.draw.circle(self.image, (*SHIELDED_COL, alpha), (cx, cy), ring_r, 3)

    # ------------------------------------------------------------------ #
    def take_damage(self, dmg: int = 1) -> bool:
        if self.shielded:
            return False          # absorb hit entirely
        self.hp -= dmg
        if self.hp <= 0:
            self.kill()
            return True
        self._draw_surface()
        return False

    # ------------------------------------------------------------------ #
    def apply_freeze(self, duration: int):
        self.frozen       = True
        self.freeze_timer = duration

    # ------------------------------------------------------------------ #
    def update(self):
        # Freeze
        if self.frozen:
            self.freeze_timer -= 1
            if self.freeze_timer <= 0:
                self.frozen = False
        else:
            direction = self.player.pos - self.pos
            if direction.length() > 0:
                self.pos += direction.normalize() * self.speed
        self.rect.center = (int(self.pos.x), int(self.pos.y))

        # Shield timing: toggle between ON (5s) and OFF (3s)
        self.shield_timer -= 1
        if self.shield_timer <= 0:
            self.shielded     = not self.shielded
            self.shield_timer = SHIELD_DURATION if self.shielded else SHIELD_COOLDOWN

        self._draw_surface()
