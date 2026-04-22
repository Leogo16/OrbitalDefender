import pygame
import math
import random
from settings import ENEMY_DEAD


class DeathParticle(pygame.sprite.Sprite):
    def __init__(self, x: float, y: float):
        super().__init__()
        self.pos = pygame.Vector2(x, y)

        angle    = random.uniform(0, 360)
        speed    = random.uniform(1.5, 4.0)
        self.vel = pygame.Vector2(
            math.cos(math.radians(angle)),
            math.sin(math.radians(angle))
        ) * speed

        self.life     = random.randint(15, 30)
        self.max_life = self.life
        self._r       = random.randint(4, 8)

        sz         = self._r * 2
        self.image = pygame.Surface((sz, sz), pygame.SRCALPHA)
        self.rect  = self.image.get_rect(center=(int(x), int(y)))
        self._redraw(255)

    def _redraw(self, alpha: int):
        self.image.fill((0, 0, 0, 0))
        pygame.draw.circle(
            self.image, (*ENEMY_DEAD, alpha), (self._r, self._r), self._r
        )

    def update(self):
        self.life -= 1
        if self.life <= 0:
            self.kill()
            return
        self.pos += self.vel
        self.vel *= 0.92
        self._redraw(int(255 * self.life / self.max_life))
        self.rect.center = (int(self.pos.x), int(self.pos.y))
