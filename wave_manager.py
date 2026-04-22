import pygame
from settings import (
    WAVE_BASE_COUNT, WAVE_COUNT_SCALE,
    WAVE_SPAWN_DELAY, WAVE_BREAK_FRAMES,
    WAVE_SPEED_SCALE, WAVE_HP_SCALE,
    WAVE_RADIUS_SCALE, WAVE_SPEED_MAX,
    ENEMY_SPEED_BASE, ENEMY_HP_BASE, ENEMY_RADIUS_BASE,
)
from entities import Enemy

class WaveManager:

    _BREAK   = "break"
    _SPAWNING = "spawning"

    def __init__(self, player):
        self.player      = player
        self.wave        = 0
        self.state       = self._BREAK
        self.timer       = 0
        self.to_spawn    = 0
        self.spawn_timer = 0

    @property
    def enemy_count(self) -> int:
        return WAVE_BASE_COUNT + self.wave * WAVE_COUNT_SCALE

    @property
    def enemy_speed(self) -> float:
        return min(ENEMY_SPEED_BASE + self.wave * WAVE_SPEED_SCALE, WAVE_SPEED_MAX)

    @property
    def enemy_hp(self) -> int:
        return ENEMY_HP_BASE + self.wave * WAVE_HP_SCALE

    @property
    def enemy_radius(self) -> int:
        r = ENEMY_RADIUS_BASE * (WAVE_RADIUS_SCALE ** (self.wave * 0.4))
        return int(min(r, 28))   # cap la 28px


    def update(self, enemy_group, all_sprites) -> bool:
        new_wave_started = False

        if self.state == self._BREAK:
            self.timer += 1
            if self.timer >= WAVE_BREAK_FRAMES:
                self._start_wave()
                new_wave_started = True

        elif self.state == self._SPAWNING:

            self.spawn_timer += 1
            if self.to_spawn > 0 and self.spawn_timer >= WAVE_SPAWN_DELAY:
                self.spawn_timer = 0
                self._spawn_one(enemy_group, all_sprites)

            if self.to_spawn == 0 and len(enemy_group) == 0:
                self.state = self._BREAK
                self.timer = 0

        return new_wave_started

    def _start_wave(self):
        self.wave       += 1
        self.to_spawn    = self.enemy_count
        self.spawn_timer = WAVE_SPAWN_DELAY
        self.state       = self._SPAWNING

    def _spawn_one(self, enemy_group, all_sprites):
        e = Enemy(
            self.player,
            speed=self.enemy_speed,
            hp=self.enemy_hp,
            radius=self.enemy_radius,
        )
        enemy_group.add(e)
        all_sprites.add(e)
        self.to_spawn -= 1

    @property
    def is_break(self) -> bool:
        return self.state == self._BREAK

    @property
    def break_progress(self) -> float:
        if self.state != self._BREAK:
            return 1.0
        return self.timer / WAVE_BREAK_FRAMES
