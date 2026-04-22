
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
        self.font_title   = pygame.font.SysFont("consolas", 26, bold=True)
        self.font_name    = pygame.font.SysFont("consolas", 18, bold=True)
        self.font_desc    = pygame.font.SysFont("consolas", 13)
        self.font_pts     = pygame.font.SysFont("consolas", 14)
        self.font_rebirth = pygame.font.SysFont("consolas", 16, bold=True)
        self.font_max     = pygame.font.SysFont("consolas", 48, bold=True)
        self.font_max_sub = pygame.font.SysFont("consolas", 16)

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

        # Rebirth button (shown when all maxed and rebirths still available)
        self.rebirth_rect = pygame.Rect(
            SCREEN_W // 2 - 120, SCREEN_H // 2 + CARD_H // 2 + 50, 240, 46
        )

    # ── helpers ─────────────────────────────────────────────────────────
    @staticmethod
    def all_maxed(upgrades: dict) -> bool:
        return (upgrades.get("speed", 0) >= MAX_SPEED_UPGRADES and
                upgrades.get("orbit", 0) >= MAX_ORBIT_UPGRADES and
                upgrades.get("size",  0) >= MAX_SIZE_UPGRADES)

    # ── draw ────────────────────────────────────────────────────────────
    def draw(self, screen: pygame.Surface, mastery_pts: int, upgrades: dict,
             rebirth_count: int = 0, can_rebirth: bool = False):

        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

        # ── Truly maxed out — no more upgrades, no more rebirths ────────
        if self.all_maxed(upgrades) and not can_rebirth:
            self._draw_max_screen(screen, rebirth_count)
            return

        # ── Normal upgrade screen ────────────────────────────────────────
        title = self.font_title.render("─── MASTERY UPGRADE ───", True, (200, 220, 255))
        screen.blit(title, title.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - CARD_H // 2 - 30)))

        pts_surf = self.font_pts.render(f"Puncte disponibile: {mastery_pts}", True, (180, 255, 180))
        screen.blit(pts_surf, pts_surf.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - CARD_H // 2 - 5)))

        if rebirth_count > 0:
            rb_lbl = self.font_pts.render(f"Rebirths: {rebirth_count}", True, (255, 180, 60))
            screen.blit(rb_lbl, rb_lbl.get_rect(topright=(SCREEN_W - 16, 12)))

        mouse_pos = pygame.mouse.get_pos()

        for card in self.cards:
            current = upgrades.get(card["id"], 0)
            maxed   = current >= card["max"]
            hovered = card["rect"].collidepoint(mouse_pos) and not maxed

            bg_col = CARD_MAXED if maxed else (CARD_HOVER if hovered else CARD_BG)
            pygame.draw.rect(screen, bg_col,        card["rect"], border_radius=10)
            pygame.draw.rect(screen, card["color"] if not maxed else (60, 60, 70),
                             card["rect"], width=2, border_radius=10)

            rx, ry = card["rect"].x, card["rect"].y

            col_text = TEXT_MAXED if maxed else card["color"]
            lbl = self.font_name.render(card["label"], True, col_text)
            screen.blit(lbl, lbl.get_rect(centerx=rx + CARD_W // 2, top=ry + 18))

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

            for j, line in enumerate(card["desc"]):
                d = self.font_desc.render(line, True, (160, 160, 160) if maxed else (200, 210, 230))
                screen.blit(d, d.get_rect(centerx=rx + CARD_W // 2, top=ry + 95 + j * 18))

            if maxed:
                st = self.font_pts.render("MAXED", True, TEXT_MAXED)
            elif hovered:
                st = self.font_pts.render("Click for upgrade", True, (255, 255, 255))
            else:
                st = self.font_pts.render("Click for upgrade", True, (100, 120, 160))
            screen.blit(st, st.get_rect(centerx=rx + CARD_W // 2, top=ry + CARD_H - 28))

        # ── Rebirth button (only if can rebirth) ─────────────────────────
        if self.all_maxed(upgrades) and can_rebirth:
            rb_hov = self.rebirth_rect.collidepoint(mouse_pos)
            rb_bg  = (80, 40, 10) if rb_hov else (50, 25, 5)
            rb_brd = (255, 160, 40) if rb_hov else (180, 100, 20)
            pygame.draw.rect(screen, rb_bg,  self.rebirth_rect, border_radius=10)
            pygame.draw.rect(screen, rb_brd, self.rebirth_rect, width=2, border_radius=10)
            rb_txt = self.font_rebirth.render("REBIRTH  -  Unlock a Spell", True,
                                              (255, 200, 60) if rb_hov else (200, 140, 40))
            screen.blit(rb_txt, rb_txt.get_rect(center=self.rebirth_rect.center))

    def _draw_max_screen(self, screen, rebirth_count: int):
        """Shown when player has truly maxed everything with no rebirths left."""
        cx, cy = SCREEN_W // 2, SCREEN_H // 2

        max_surf = self.font_max.render("MAX", True, (255, 215, 60))
        screen.blit(max_surf, max_surf.get_rect(center=(cx, cy - 40)))

        lines = [
            "Toate upgrade-urile sunt la maxim.",
            "Nu mai exista rebirths disponibile.",
            f"Rebirths efectuate: {rebirth_count}",
            "",
            "Continua sa joci!  (apasa ESC pentru meniu)",
        ]
        for i, line in enumerate(lines):
            col  = (255, 180, 60) if i == 2 else (160, 170, 200)
            surf = self.font_max_sub.render(line, True, col)
            screen.blit(surf, surf.get_rect(center=(cx, cy + 20 + i * 22)))

    # ── event handling ──────────────────────────────────────────────────
    def handle_event(self, event: pygame.event.Event, upgrades: dict,
                     can_rebirth: bool = False) -> str | None:
        """Returns upgrade id, 'rebirth', 'dismiss_max', or None."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Rebirth button
            if self.all_maxed(upgrades) and can_rebirth:
                if self.rebirth_rect.collidepoint(event.pos):
                    return "rebirth"
            # Normal upgrade card
            if not (self.all_maxed(upgrades) and not can_rebirth):
                for card in self.cards:
                    current = upgrades.get(card["id"], 0)
                    if card["rect"].collidepoint(event.pos) and current < card["max"]:
                        return card["id"]
        # On max screen: any key/click dismisses back to playing
        if self.all_maxed(upgrades) and not can_rebirth:
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                return "dismiss_max"
        return None


