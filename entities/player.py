import pygame
import math
from settings import (
    WORLD_W, WORLD_H,
    PLAYER_RADIUS, PLAYER_SPEED,
    PLAYER_COL, DANGER_DISTANCE,
)


class Player(pygame.sprite.Sprite):
    def __init__(self, x: float, y: float):
        super().__init__()
        self.pos    = pygame.Vector2(x, y)
        self.speed  = PLAYER_SPEED
        self.radius = PLAYER_RADIUS

        self._danger = False
        self._pulse  = 0.0

        self.image = pygame.Surface(
            (PLAYER_RADIUS * 2, PLAYER_RADIUS * 2), pygame.SRCALPHA
        )
        self.rect = self.image.get_rect(center=(int(x), int(y)))
        self._draw_surface(danger=False)

    def _draw_surface(self, danger: bool):
        self.image.fill((0, 0, 0, 0))
        cx = cy = PLAYER_RADIUS
        if danger:
            alpha = int(60 + 60 * math.sin(self._pulse))
            pygame.draw.circle(self.image, (220, 40, 40, alpha), (cx, cy), PLAYER_RADIUS + 3)
        pygame.draw.circle(self.image, (40, 100, 200, 80), (cx, cy), PLAYER_RADIUS)
        pygame.draw.circle(self.image, PLAYER_COL,          (cx, cy), PLAYER_RADIUS - 2)
        pygame.draw.circle(self.image, (255, 255, 255),               (cx - 4, cy - 4), 4)

    def set_danger(self, enemy_group):
        in_danger = any(
            (e.pos - self.pos).length() < DANGER_DISTANCE
            for e in enemy_group
        )
        self._danger = in_danger
        if in_danger:
            self._pulse = (self._pulse + 0.18) % (2 * math.pi)
        self._draw_surface(danger=in_danger)

    def update(self, keys):
        dx = dy = 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:    dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:  dy += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:  dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += 1

        if dx or dy:
            self.pos += pygame.Vector2(dx, dy).normalize() * self.speed

        self.pos.x = max(PLAYER_RADIUS, min(WORLD_W - PLAYER_RADIUS, self.pos.x))
        self.pos.y = max(PLAYER_RADIUS, min(WORLD_H - PLAYER_RADIUS, self.pos.y))
        self.rect.center = (int(self.pos.x), int(self.pos.y))
