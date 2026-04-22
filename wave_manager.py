import pygame
import random
from settings import (
    WAVE_BASE_COUNT, WAVE_COUNT_SCALE,
    WAVE_SPAWN_DELAY, WAVE_BREAK_FRAMES,
    WAVE_SPEED_SCALE, WAVE_HP_SCALE,
    WAVE_RADIUS_SCALE, WAVE_SPEED_MAX,
    ENEMY_SPEED_BASE, ENEMY_HP_BASE, ENEMY_RADIUS_BASE,
    SHIELDED_ENEMY_WAVE_START, SHIELDED_ENEMY_RADIUS,
    SHIELDED_ENEMY_SPEED_MULT,
)
from entities import Enemy, ShieldedEnemy

class WaveManager:

    _BREAK    = "break"
    _SPAWNING = "spawning"

    def __init__(self, player):
        self.player      = player
        self.wave        = 0
        self.state       = self._BREAK
        self.timer       = 0
        self.to_spawn    = 0
        self.spawn_timer = 0
        # queue: list of ("normal"|"shielded") to spawn
        self._queue      = []

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
        return int(min(r, 28))

    def _build_queue(self) -> list:
        """Decide how many shielded vs normal enemies this wave."""
        total = self.enemy_count
        if self.wave < SHIELDED_ENEMY_WAVE_START:
            return ["normal"] * total
        # one shielded per 4 enemies, at least 1 from wave 5
        n_shielded = max(1, total // 4)
        n_normal   = total - n_shielded
        q = ["shielded"] * n_shielded + ["normal"] * n_normal
        random.shuffle(q)
        return q

    def update(self, enemy_group, all_sprites, shielded_group=None) -> bool:
        new_wave_started = False

        if self.state == self._BREAK:
            self.timer += 1
            if self.timer >= WAVE_BREAK_FRAMES:
                self._start_wave()
                new_wave_started = True

        elif self.state == self._SPAWNING:
            self.spawn_timer += 1
            if self._queue and self.spawn_timer >= WAVE_SPAWN_DELAY:
                self.spawn_timer = 0
                self._spawn_one(enemy_group, all_sprites, shielded_group)

            total_alive = len(enemy_group) + (len(shielded_group) if shielded_group else 0)
            if not self._queue and total_alive == 0:
                self.state = self._BREAK
                self.timer = 0

        return new_wave_started

    def _start_wave(self):
        self.wave        += 1
        self._queue       = self._build_queue()
        self.to_spawn     = len(self._queue)
        self.spawn_timer  = WAVE_SPAWN_DELAY
        self.state        = self._SPAWNING

    def _spawn_one(self, enemy_group, all_sprites, shielded_group):
        kind = self._queue.pop(0)
        if kind == "shielded":
            e = ShieldedEnemy(
                self.player,
                speed=self.enemy_speed * SHIELDED_ENEMY_SPEED_MULT,
                hp=max(2, self.enemy_hp + 1),
                radius=SHIELDED_ENEMY_RADIUS,
            )
            enemy_group.add(e)   # for collision detection
            all_sprites.add(e)
            if shielded_group is not None:
                shielded_group.add(e)
        else:
            e = Enemy(
                self.player,
                speed=self.enemy_speed,
                hp=self.enemy_hp,
                radius=self.enemy_radius,
            )
            enemy_group.add(e)
            all_sprites.add(e)

    @property
    def is_break(self) -> bool:
        return self.state == self._BREAK

    @property
    def break_progress(self) -> float:
        if self.state != self._BREAK:
            return 1.0
        return self.timer / WAVE_BREAK_FRAMES

