import pygame
import math
from settings import (
    ORBIT_RADIUS, ORBIT_W, ORBIT_H, ORBIT_ROT_SPEED,
    ORBIT_COL, ORBIT_GLOW,
)


class Orbiter(pygame.sprite.Sprite):
    def __init__(self, player, angle_offset: float = 0.0,
                 w: int = ORBIT_W, h: int = ORBIT_H):
        super().__init__()
        self.player       = player
        self.angle        = angle_offset
        self.orbit_radius = ORBIT_RADIUS
        self.rot_speed    = ORBIT_ROT_SPEED
        self.w            = w
        self.h            = h
        self.damage       = 1

        self.base_image = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        self._draw_base()
        self.image = self.base_image.copy()
        self.rect  = self.image.get_rect()
        self.update_position()

    def _draw_base(self):
        self.base_image.fill((0, 0, 0, 0))
        pygame.draw.rect(
            self.base_image, ORBIT_COL,
            (0, 0, self.w, self.h), border_radius=4
        )
        pygame.draw.rect(
            self.base_image, ORBIT_GLOW,
            (1, 1, self.w - 2, self.h - 2), width=2, border_radius=4
        )

    def resize(self, new_w: int, new_h: int):
        self.w = new_w
        self.h = new_h
        self.base_image = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        self._draw_base()

    def update_position(self):
        rad = math.radians(self.angle)
        cx  = self.player.pos.x + self.orbit_radius * math.cos(rad)
        cy  = self.player.pos.y + self.orbit_radius * math.sin(rad)
        self.image = pygame.transform.rotate(self.base_image, -self.angle)
        self.rect  = self.image.get_rect(center=(int(cx), int(cy)))

    def update(self):
        self.angle = (self.angle + self.rot_speed) % 360
        self.update_position()
