import pygame
import math
from settings import SCREEN_W, SCREEN_H, ORBIT_COL, PLAYER_COL


class MainMenu:

    def __init__(self):
        self.font_title  = pygame.font.SysFont("consolas", 52, bold=True)
        self.font_sub    = pygame.font.SysFont("consolas", 20)
        self.font_small  = pygame.font.SysFont("consolas", 15)
        self.font_hs     = pygame.font.SysFont("consolas", 18, bold=True)
        self._tick       = 0

    def draw(self, screen: pygame.Surface, highscore: int):
        self._tick += 1

        screen.fill((10, 10, 20))

        # BG
        for x in range(0, SCREEN_W, 50):
            pygame.draw.line(screen, (20, 20, 35), (x, 0), (x, SCREEN_H))
        for y in range(0, SCREEN_H, 50):
            pygame.draw.line(screen, (20, 20, 35), (0, y), (SCREEN_W, y))

        cx, cy = SCREEN_W // 2, SCREEN_H // 2

        for i in range(3):
            angle = math.radians(self._tick * 1.5 + i * 120)
            ox = cx + math.cos(angle) * 90
            oy = cy + math.sin(angle) * 90
            pygame.draw.circle(screen, ORBIT_COL, (int(ox), int(oy)), 8)

        pygame.draw.circle(screen, (40, 60, 100), (cx, cy), 90, 1)

        pulse = abs(math.sin(self._tick * 0.04)) * 0.3 + 0.7
        r = int(22 * pulse)
        pygame.draw.circle(screen, (40, 100, 200, 80), (cx, cy), r + 4)
        pygame.draw.circle(screen, PLAYER_COL, (cx, cy), r)

        # Titlu
        title  = self.font_title.render("ORBITAL", True, (100, 180, 255))
        title2 = self.font_title.render("DEFENDER", True, ORBIT_COL)
        screen.blit(title,  title.get_rect(center=(cx, cy - 160)))
        screen.blit(title2, title2.get_rect(center=(cx, cy - 105)))

        pygame.draw.line(screen, (50, 70, 120),
                         (cx - 200, cy - 75), (cx + 200, cy - 75), 1)

        # Instrucțiuni start
        blink = (self._tick // 35) % 2 == 0
        if blink:
            start = self.font_sub.render("PRESS SPACE TO START", True, (180, 220, 255))
            screen.blit(start, start.get_rect(center=(cx, cy + 110)))

        # Controls
        controls = [
            "WASD – Movement",
        ]
        for i, line in enumerate(controls):
            s = self.font_small.render(line, True, (80, 100, 140))
            screen.blit(s, s.get_rect(center=(cx, cy + 155 + i * 22)))

        # Highscore
        if highscore > 0:
            hs = self.font_hs.render(f"BEST: {highscore} kills", True, (255, 215, 60))
            screen.blit(hs, hs.get_rect(center=(cx, cy + 70)))

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return True
        return False
