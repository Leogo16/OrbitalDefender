
import pygame
from settings import (
    SCREEN_W, SCREEN_H,
    MAX_SPEED_UPGRADES, MAX_SIZE_UPGRADES, MAX_ORBIT_UPGRADES,
)

# Culorile cardurilor
CARD_BG      = (25,  30,  55)
CARD_BORDER  = (70,  90, 160)
CARD_HOVER   = (40,  55,  100)
CARD_MAXED   = (35,  35,  45)
TEXT_MAXED   = (90,  90,  90)
COL_SPEED    = (80,  200, 255)
COL_ORBIT    = (255, 200,  60)
COL_SIZE     = (120, 255, 140)

CARD_W, CARD_H = 220, 180
GAP            = 30


class UpgradeMenu:

    def __init__(self):
        self.font_title = pygame.font.SysFont("consolas", 26, bold=True)
        self.font_name  = pygame.font.SysFont("consolas", 18, bold=True)
        self.font_desc  = pygame.font.SysFont("consolas", 13)
        self.font_pts   = pygame.font.SysFont("consolas", 14)

        # Centrare carduri
        total_w = CARD_W * 3 + GAP * 2
        start_x = (SCREEN_W - total_w) // 2
        cy      = SCREEN_H // 2 - CARD_H // 2 + 20

        self.cards = [
            {
                "id":    "speed",
                "label": "SPEED",
                "desc":  ["+viteza de movement"],
                "color": COL_SPEED,
                "rect":  pygame.Rect(start_x, cy, CARD_W, CARD_H),
                "max":   MAX_SPEED_UPGRADES,
            },
            {
                "id":    "orbit",
                "label": "ORBITE",
                "desc":  ["+1 orbita nou"],
                "color": COL_ORBIT,
                "rect":  pygame.Rect(start_x + CARD_W + GAP, cy, CARD_W, CARD_H),
                "max":   MAX_ORBIT_UPGRADES,
            },
            {
                "id":    "size",
                "label": "SIZE",
                "desc":  ["+dimensiune orbita"],
                "color": COL_SIZE,
                "rect":  pygame.Rect(start_x + (CARD_W + GAP) * 2, cy, CARD_W, CARD_H),
                "max":   MAX_SIZE_UPGRADES,
            },
        ]

    def draw(self, screen: pygame.Surface, mastery_pts: int, upgrades: dict):

        # Overlay
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

        # Titlu
        title = self.font_title.render("─── MASTERY UPGRADE ───", True, (200, 220, 255))
        screen.blit(title, title.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - CARD_H // 2 - 30)))

        pts_surf = self.font_pts.render(f"Puncte disponibile: {mastery_pts}", True, (180, 255, 180))
        screen.blit(pts_surf, pts_surf.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - CARD_H // 2 - 5)))

        mouse_pos = pygame.mouse.get_pos()

        for card in self.cards:
            current = upgrades.get(card["id"], 0)
            maxed   = current >= card["max"]
            hovered = card["rect"].collidepoint(mouse_pos) and not maxed

            # Fond card
            bg_col = CARD_MAXED if maxed else (CARD_HOVER if hovered else CARD_BG)
            pygame.draw.rect(screen, bg_col,        card["rect"], border_radius=10)
            pygame.draw.rect(screen, card["color"] if not maxed else (60, 60, 70),
                             card["rect"], width=2, border_radius=10)

            rx, ry = card["rect"].x, card["rect"].y

            # Label
            col_text = TEXT_MAXED if maxed else card["color"]
            lbl = self.font_name.render(card["label"], True, col_text)
            screen.blit(lbl, lbl.get_rect(centerx=rx + CARD_W // 2, top=ry + 18))

            # Bara de progres
            bar_x = rx + 20
            bar_y = ry + 55
            bar_w = CARD_W - 40
            bar_h = 10
            pygame.draw.rect(screen, (50, 50, 70), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
            fill = int(bar_w * current / card["max"])
            if fill > 0:
                pygame.draw.rect(screen, card["color"] if not maxed else (80, 80, 80),
                                 (bar_x, bar_y, fill, bar_h), border_radius=4)
            lvl_txt = self.font_pts.render(f"{current} / {card['max']}", True, col_text)
            screen.blit(lvl_txt, lvl_txt.get_rect(centerx=rx + CARD_W // 2, top=bar_y + 14))

            # Desc
            for j, line in enumerate(card["desc"]):
                d = self.font_desc.render(line, True, (160, 160, 160) if maxed else (200, 210, 230))
                screen.blit(d, d.get_rect(centerx=rx + CARD_W // 2, top=ry + 95 + j * 18))

            # Status
            if maxed:
                st = self.font_pts.render("MAXED", True, TEXT_MAXED)
            elif hovered:
                st = self.font_pts.render("Click for upgrade", True, (255, 255, 255))
            else:
                st = self.font_pts.render("Click for upgrade", True, (100, 120, 160))
            screen.blit(st, st.get_rect(centerx=rx + CARD_W // 2, top=ry + CARD_H - 28))

    def handle_event(self, event: pygame.event.Event, upgrades: dict) -> str | None:

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for card in self.cards:
                current = upgrades.get(card["id"], 0)
                if card["rect"].collidepoint(event.pos) and current < card["max"]:
                    return card["id"]
        return None
