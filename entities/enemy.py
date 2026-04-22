import pygame
import random
from settings import (
    WORLD_W, WORLD_H,
    ENEMY_RADIUS_BASE,
    ENEMY_GLOW,
    SPAWN_MARGIN,
)

class Enemy(pygame.sprite.Sprite):
    def __init__(self, player, speed: float = 1.6, hp: int = 1, radius: int = None):
        super().__init__()
        self.player = player
        self.speed  = speed
        self.hp     = hp
        self.max_hp = hp
        self.radius = radius if radius is not None else ENEMY_RADIUS_BASE

        # Spawn pos
        self.pos = pygame.Vector2(*self._spawn_pos())

        sz = self.radius * 2
        self.image = pygame.Surface((sz, sz), pygame.SRCALPHA)
        self.rect  = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        self._draw_surface()

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

    def _draw_surface(self):

        sz = self.radius * 2
        self.image = pygame.Surface((sz, sz), pygame.SRCALPHA)
        cx = cy = self.radius

        # Glow
        pygame.draw.circle(self.image, (*ENEMY_GLOW, 70), (cx, cy), self.radius)

        hp_ratio = self.hp / self.max_hp
        r = int(220)
        g = int(50 + (1 - hp_ratio) * 80)
        b = 50
        pygame.draw.circle(self.image, (r, g, b), (cx, cy), self.radius - 2)

        # Bară HP
        if self.max_hp > 1:
            bar_w = sz - 4
            bar_h = 4
            bx, by = 2, 2
            pygame.draw.rect(self.image, (80, 0, 0),      (bx, by, bar_w, bar_h))
            fill = int(bar_w * self.hp / self.max_hp)
            pygame.draw.rect(self.image, (220, 60, 60),   (bx, by, fill,  bar_h))

        # Highlight
        pygame.draw.circle(self.image, (255, 255, 255), (cx + self.radius // 4, cy - self.radius // 4), 3)

    def take_damage(self, dmg: int = 1) -> bool:
        self.hp -= dmg
        if self.hp <= 0:
            self.kill()
            return True
        self._draw_surface()
        return False

    def update(self):
        direction = self.player.pos - self.pos
        if direction.length() > 0:
            self.pos += direction.normalize() * self.speed
        self.rect.center = (int(self.pos.x), int(self.pos.y))
