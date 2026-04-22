
import pygame
from settings import WORLD_W, WORLD_H
from entities import Player, Orbiter

def redistribute_orbiters(orbiters: list):
    n = len(orbiters)
    if n == 0:
        return
    for i, orb in enumerate(orbiters):
        orb.angle = (360 / n) * i


def make_fresh_scene():

    all_sprites    = pygame.sprite.Group()
    orbiter_group  = pygame.sprite.Group()
    enemy_group    = pygame.sprite.Group()
    particle_group = pygame.sprite.Group()

    player = Player(WORLD_W // 2, WORLD_H // 2)
    all_sprites.add(player)

    orb = Orbiter(player, angle_offset=0)
    orbiter_group.add(orb)
    all_sprites.add(orb)

    return player, all_sprites, orbiter_group, enemy_group, particle_group
