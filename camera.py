import pygame
from settings import SCREEN_W, SCREEN_H, WORLD_W, WORLD_H


class Camera:
    def __init__(self):
        self.offset = pygame.Vector2(0, 0)

    def update(self, target):

        x = -target.pos.x + SCREEN_W // 2
        y = -target.pos.y + SCREEN_H // 2

        x = max(-(WORLD_W - SCREEN_W), min(0, x))
        y = max(-(WORLD_H - SCREEN_H), min(0, y))

        self.offset.x = x
        self.offset.y = y

    def apply(self, entity) -> pygame.Rect:
        return entity.rect.move(self.offset)

    def apply_pos(self, world_pos: pygame.Vector2) -> tuple:
        return (int(world_pos.x + self.offset.x),
                int(world_pos.y + self.offset.y))
