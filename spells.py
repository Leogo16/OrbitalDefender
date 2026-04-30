import pygame
import math
from settings import (
    SCREEN_W, SCREEN_H,
    FREEZE_COOLDOWN, FREEZE_DURATION,
    BOMB_COOLDOWN, BOMB_FUSE, BOMB_RADIUS,
    SHOCKWAVE_COOLDOWN, SHOCKWAVE_SPEED,
    WORLD_W, WORLD_H,
)


# ═══════════════════════════════════════════════════
#  SPELL BASE INTERFACE
# ═══════════════════════════════════════════════════

class _BaseSpell:
    ID    = ""
    NAME  = ""
    DESC  = ""
    COLOR = (200, 200, 200)
    KEY   = None

    def __init__(self, cooldown_max: int):
        self.cooldown_max   = cooldown_max
        self.cooldown_timer = 0

    @property
    def ready(self) -> bool:
        return self.cooldown_timer <= 0

    @property
    def cooldown_pct(self) -> float:
        if self.cooldown_timer <= 0:
            return 1.0
        return 1.0 - self.cooldown_timer / self.cooldown_max

    @property
    def cd_seconds(self) -> int:
        return max(0, self.cooldown_timer // 60)

    def update(self):
        if self.cooldown_timer > 0:
            self.cooldown_timer -= 1


# ═══════════════════════════════════════════════════
#  1. FREEZE SPELL
# ═══════════════════════════════════════════════════

class FreezeSpell(_BaseSpell):
    ID    = "freeze"
    NAME  = "FREEZE"
    DESC  = "Freezes all enemies for 4s"
    COLOR = (100, 220, 255)
    KEY   = pygame.K_q
    ICON  = "❄"

    def __init__(self):
        super().__init__(FREEZE_COOLDOWN)

    def cast(self, enemy_group, shielded_group=None, spell_objects=None, player=None):
        if not self.ready:
            return False
        for e in enemy_group:
            e.apply_freeze(FREEZE_DURATION)
        if shielded_group:
            for e in shielded_group:
                e.apply_freeze(FREEZE_DURATION)
        self.cooldown_timer = self.cooldown_max
        return True


# ═══════════════════════════════════════════════════
#  2. BOMB SPELL
# ═══════════════════════════════════════════════════

class BombObject(pygame.sprite.Sprite):
    """A static bomb placed in the world; explodes after BOMB_FUSE frames."""

    def __init__(self, wx: float, wy: float):
        super().__init__()
        self.world_pos  = pygame.Vector2(wx, wy)
        self.fuse_timer = BOMB_FUSE
        self.exploded   = False
        self._pulse     = 0.0

        sz = 28
        self.image = pygame.Surface((sz, sz), pygame.SRCALPHA)
        self.rect  = self.image.get_rect(center=(int(wx), int(wy)))
        self._draw(1.0)

    def _draw(self, fuse_ratio: float):
        sz = 28
        self.image = pygame.Surface((sz, sz), pygame.SRCALPHA)
        # body — orange-red, pulses faster near explosion
        self._pulse += 0.15 + (1 - fuse_ratio) * 0.3
        glow_a = int(60 + 60 * abs(math.sin(self._pulse)))
        pygame.draw.circle(self.image, (255, 100, 20, glow_a), (14, 14), 14)
        pygame.draw.circle(self.image, (220, 60, 10), (14, 14), 10)
        # fuse line
        pygame.draw.line(self.image, (255, 220, 80), (14, 4), (20, 0), 2)

    def update(self):
        if not self.exploded:
            self.fuse_timer -= 1
            ratio = self.fuse_timer / BOMB_FUSE
            self._draw(max(0.0, ratio))

    def explode(self, enemy_group, shielded_group, particle_group, all_sprites):
        """Kill all enemies within BOMB_RADIUS. Returns kill count."""
        self.exploded = True
        count = 0
        for group in (enemy_group, shielded_group):
            for e in list(group):
                if (e.pos - self.world_pos).length() <= BOMB_RADIUS:
                    # spawn particles
                    from entities import DeathParticle
                    for _ in range(8):
                        p = DeathParticle(e.pos.x, e.pos.y)
                        particle_group.add(p)
                        all_sprites.add(p)
                    e.kill()
                    count += 1
        self.kill()
        return count

    def draw_explosion_ring(self, screen, camera):
        """Draw a fading explosion ring in world-space."""
        pass  # handled separately in main via ExplosionRing


class ExplosionRing(pygame.sprite.Sprite):
    """Visual-only expanding ring after bomb detonation."""

    def __init__(self, wx: float, wy: float):
        super().__init__()
        self.world_pos = pygame.Vector2(wx, wy)
        self.radius    = BOMB_RADIUS
        self.life      = 30   # frames
        self.max_life  = 30
        sz = int(self.radius * 2) + 4
        self.image = pygame.Surface((sz, sz), pygame.SRCALPHA)
        self.rect  = self.image.get_rect(center=(int(wx), int(wy)))

    def update(self):
        self.life -= 1
        if self.life <= 0:
            self.kill()

    def draw_world(self, screen, camera):
        if self.life <= 0:
            return
        alpha  = int(255 * self.life / self.max_life)
        radius = int(BOMB_RADIUS + (self.max_life - self.life) * 1.5)
        cx, cy = camera.apply_pos(self.world_pos)
        surf = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(surf, (255, 140, 20, alpha),
                           (radius + 2, radius + 2), radius, 3)
        pygame.draw.circle(surf, (255, 220, 80, alpha // 3),
                           (radius + 2, radius + 2), radius)
        screen.blit(surf, (cx - radius - 2, cy - radius - 2))


class BombSpell(_BaseSpell):
    ID    = "bomb"
    NAME  = "BOMB"
    DESC  = "Places a bomb (2s fuse, r=50)"
    COLOR = (255, 140, 20)
    KEY   = pygame.K_q
    ICON  = "💣"

    def __init__(self):
        super().__init__(BOMB_COOLDOWN)

    def cast(self, enemy_group, shielded_group=None, spell_objects=None, player=None):
        if not self.ready or spell_objects is None or player is None:
            return False
        bomb = BombObject(player.pos.x, player.pos.y)
        spell_objects.add(bomb)
        self.cooldown_timer = self.cooldown_max
        return True


# ═══════════════════════════════════════════════════
#  3. SHOCKWAVE SPELL
# ═══════════════════════════════════════════════════

class ShockwaveObject(pygame.sprite.Sprite):
    """Expanding ring centred on player; kills anything it touches."""

    # diagonal of max world size — safe upper bound
    MAX_RADIUS = int(math.hypot(WORLD_W, WORLD_H) / 2) + 200

    def __init__(self, wx: float, wy: float):
        super().__init__()
        self.world_pos = pygame.Vector2(wx, wy)
        self.radius    = 20.0   # start just outside player
        self._killed   = set()  # track already-killed enemies
        sz = 4
        self.image = pygame.Surface((sz, sz), pygame.SRCALPHA)
        self.rect  = self.image.get_rect(center=(int(wx), int(wy)))

    @property
    def _screen_radius(self):
        """Max screen diagonal — used as termination check."""
        return math.hypot(SCREEN_W, SCREEN_H)

    def update(self):
        self.radius += SHOCKWAVE_SPEED
        if self.radius > self._screen_radius + 200:
            self.kill()

    def check_kills(self, enemy_group, shielded_group, particle_group, all_sprites):
        """Kill any enemy whose centre falls inside the ring's swept area."""
        count = 0
        for group in (enemy_group, shielded_group):
            for e in list(group):
                eid = id(e)
                if eid in self._killed:
                    continue
                dist = (e.pos - self.world_pos).length()
                if dist <= self.radius:
                    self._killed.add(eid)
                    from entities import DeathParticle
                    for _ in range(8):
                        p = DeathParticle(e.pos.x, e.pos.y)
                        particle_group.add(p)
                        all_sprites.add(p)
                    e.kill()
                    count += 1
        return count

    def draw_world(self, screen, camera):
        if self.radius <= 0:
            return
        cx, cy = camera.apply_pos(self.world_pos)
        r      = int(self.radius)
        # fade out as it grows
        max_r  = self._screen_radius
        alpha  = max(20, int(220 * (1 - self.radius / max_r)))

        surf = pygame.Surface((r * 2 + 6, r * 2 + 6), pygame.SRCALPHA)
        # outer ring
        pygame.draw.circle(surf, (180, 100, 255, alpha),
                           (r + 3, r + 3), r, 4)
        # inner glow ring
        if r > 12:
            pygame.draw.circle(surf, (220, 160, 255, alpha // 3),
                               (r + 3, r + 3), r - 8, 2)
        screen.blit(surf, (cx - r - 3, cy - r - 3))


class ShockwaveSpell(_BaseSpell):
    ID    = "shockwave"
    NAME  = "SHOCKWAVE"
    DESC  = "Expanding ring kills all"
    COLOR = (200, 100, 255)
    KEY   = pygame.K_q
    ICON  = "⚡"

    def __init__(self):
        super().__init__(SHOCKWAVE_COOLDOWN)

    def cast(self, enemy_group, shielded_group=None, spell_objects=None, player=None):
        if not self.ready or spell_objects is None or player is None:
            return False
        sw = ShockwaveObject(player.pos.x, player.pos.y)
        spell_objects.add(sw)
        self.cooldown_timer = self.cooldown_max
        return True


# ═══════════════════════════════════════════════════
#  Spell registry  — order = rebirth unlock order
# ═══════════════════════════════════════════════════

ALL_SPELL_CLASSES = [FreezeSpell, BombSpell, ShockwaveSpell]


# ═══════════════════════════════════════════════════
#  Spell menu UI  (opens as a PAUSE overlay)
# ═══════════════════════════════════════════════════

CARD_W, CARD_H = 210, 175
GAP            = 20
CARD_BG        = (20, 28, 52)
CARD_HOVER     = (38, 52, 100)
CARD_SEL       = (24, 60, 110)
CARD_BORDER    = (70, 90, 160)

# Icon labels per spell id
_ICONS = {
    "freeze":    "❄",
    "bomb":      "B",
    "shockwave": "~",
}


class SpellMenu:
    def __init__(self):
        self.font_title  = pygame.font.SysFont("consolas", 24, bold=True)
        self.font_name   = pygame.font.SysFont("consolas", 17, bold=True)
        self.font_desc   = pygame.font.SysFont("consolas", 12)
        self.font_small  = pygame.font.SysFont("consolas", 13)
        self.font_ico    = pygame.font.SysFont("consolas", 20, bold=True)
        self.visible      = False
        self.rebirth_mode = False
        self.choices      = []
        self.last_picked  = None

    def set_choices(self, spell_classes: list):
        """Set which spell classes are shown in this menu."""
        self.choices       = list(spell_classes)
        self.last_picked   = None   # class of last spell picked (rebirth mode)

    # ── open / close ──────────────────────────
    def open(self, rebirth: bool = False):
        self.visible      = True
        self.rebirth_mode = rebirth
        self.last_picked  = None

    def close(self):
        self.visible      = False
        self.rebirth_mode = False

    def toggle(self):
        if self.visible:
            self.close()
        else:
            self.open(rebirth=False)

    # ── events ────────────────────────────────
    def handle_event(self, event, unlocked_spells: list, equipped: list) -> bool:
        if not self.visible:
            return False

        # ESC always closes (in rebirth mode only if a spell was already picked)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.rebirth_mode and self.last_picked is None:
                    return True   # must pick first, block ESC
                self.close()
                return True
            if event.key == pygame.K_TAB and not self.rebirth_mode:
                self.close()
                return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            cards  = self._card_rects(unlocked_spells)
            for i, rect in enumerate(cards):
                if rect.collidepoint(event.pos):
                    cls = unlocked_spells[i]
                    # Block switching if active spell is on cooldown
                    if equipped and not equipped[0].ready:
                        return True   # consume click but don't switch
                    # Single slot: replace whatever is equipped
                    equipped.clear()
                    equipped.append(cls())
                    if self.rebirth_mode:
                        self.last_picked = cls
                        self.close()
                    return True

        return False

    # ── draw ──────────────────────────────────
    def draw(self, screen, unlocked_spells: list, equipped: list):
        if not self.visible:
            return

        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 185))
        screen.blit(overlay, (0, 0))

        cx = SCREEN_W // 2

        if self.rebirth_mode:
            title_txt = "REBIRTH  -  CHOOSE YOUR SPELL"
            title_col = (255, 200, 60)
            sub_txt   = "Select a spell to equip and continue"
        else:
            title_txt = "-- SPELL BOOK --"
            title_col = (200, 230, 255)
            sub_txt   = "Click to equip  |  ESC to close"

        title = self.font_title.render(title_txt, True, title_col)
        screen.blit(title, title.get_rect(center=(cx, SCREEN_H // 2 - CARD_H // 2 - 50)))

        hint = self.font_small.render(sub_txt, True, (120, 140, 170))
        screen.blit(hint, hint.get_rect(center=(cx, SCREEN_H // 2 - CARD_H // 2 - 22)))

        equipped_ids = {s.ID for s in equipped}
        # Check if switching is blocked (active spell on cooldown)
        switch_blocked = bool(equipped) and not equipped[0].ready
        mouse_pos    = pygame.mouse.get_pos()
        cards        = self._card_rects(unlocked_spells)

        for cls, rect in zip(unlocked_spells, cards):
            sel     = cls.ID in equipped_ids
            hovered = rect.collidepoint(mouse_pos)
            bg      = CARD_SEL if sel else (CARD_HOVER if hovered else CARD_BG)
            border  = cls.COLOR if sel else ((120, 150, 220) if hovered else CARD_BORDER)

            pygame.draw.rect(screen, bg,     rect, border_radius=12)
            pygame.draw.rect(screen, border, rect, width=2, border_radius=12)

            # Icon circle
            ico_y = rect.y + 42
            pygame.draw.circle(screen, (*cls.COLOR, 60), (rect.centerx, ico_y), 24)
            pygame.draw.circle(screen, cls.COLOR,        (rect.centerx, ico_y), 18)
            ico_lbl = self.font_ico.render(_ICONS.get(cls.ID, "*"), True, (255, 255, 255))
            screen.blit(ico_lbl, ico_lbl.get_rect(center=(rect.centerx, ico_y)))

            lbl = self.font_name.render(cls.NAME, True, cls.COLOR)
            screen.blit(lbl, lbl.get_rect(centerx=rect.centerx, top=rect.y + 72))

            desc = self.font_desc.render(cls.DESC, True, (190, 200, 220))
            screen.blit(desc, desc.get_rect(centerx=rect.centerx, top=rect.y + 96))

            key_lbl = self.font_small.render(
                f"Hotkey: {pygame.key.name(cls.KEY).upper()}", True, (140, 160, 200))
            screen.blit(key_lbl, key_lbl.get_rect(centerx=rect.centerx, top=rect.y + 116))

            if sel:
                st_txt, st_col = "EQUIPPED", (100, 255, 160)
            elif switch_blocked:
                st_txt, st_col = "COOLDOWN ACTIVE", (220, 80, 80)
            elif hovered:
                st_txt, st_col = "Click to select", (220, 220, 255)
            else:
                st_txt, st_col = "Click to select", (80, 100, 140)

            st = self.font_small.render(st_txt, True, st_col)
            screen.blit(st, st.get_rect(centerx=rect.centerx, top=rect.y + CARD_H - 28))

    def _card_rects(self, unlocked_spells):
        n = len(unlocked_spells)
        if n == 0:
            return []
        # Shrink card width slightly when 3 cards to fit screen
        card_w = CARD_W if n <= 2 else 185
        gap    = GAP    if n <= 2 else 16
        total_w = card_w * n + gap * (n - 1)
        sx = (SCREEN_W - total_w) // 2
        cy = SCREEN_H // 2 - CARD_H // 2
        return [pygame.Rect(sx + i * (card_w + gap), cy, card_w, CARD_H)
                for i in range(n)]


# ═══════════════════════════════════════════════════
#  Left-side spell tab button
# ═══════════════════════════════════════════════════

class SpellTabButton:
    BTN_W = 36
    BTN_H = 90

    def __init__(self):
        self.font   = pygame.font.SysFont("consolas", 12, bold=True)
        self.rect   = pygame.Rect(0, SCREEN_H // 2 - self.BTN_H // 2,
                                  self.BTN_W, self.BTN_H)
        self._hover = False
        self._pulse = 0.0

    def handle_event(self, event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self._hover = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def draw(self, screen, unlocked_spells: list, spell_menu_visible: bool):
        if not unlocked_spells:
            return

        self._pulse = (self._pulse + 0.06) % (2 * math.pi)

        base_col   = (30, 50, 110) if spell_menu_visible else (40, 60, 130)
        border_col = (100, 160, 255) if (self._hover or spell_menu_visible) else (60, 90, 180)

        if not spell_menu_visible:
            glow_a = int(18 + 14 * math.sin(self._pulse))
            glow   = pygame.Surface((self.BTN_W + 6, self.BTN_H + 6), pygame.SRCALPHA)
            pygame.draw.rect(glow, (80, 140, 255, glow_a), glow.get_rect(), border_radius=8)
            screen.blit(glow, (self.rect.x - 3, self.rect.y - 3))

        pygame.draw.rect(screen, base_col,   self.rect, border_radius=8)
        pygame.draw.rect(screen, border_col, self.rect, width=2, border_radius=8)

        letters = "SPELLS"
        lh      = 13
        start_y = self.rect.centery - (len(letters) * lh) // 2
        for j, ch in enumerate(letters):
            s = self.font.render(ch, True, (180, 210, 255))
            screen.blit(s, s.get_rect(centerx=self.rect.centerx,
                                      top=start_y + j * lh))

        arrow = ">" if not spell_menu_visible else "<"
        a_surf = self.font.render(arrow, True, border_col)
        screen.blit(a_surf, a_surf.get_rect(centerx=self.rect.centerx,
                                             top=self.rect.bottom - 18))


# ═══════════════════════════════════════════════════
#  HUD bar  (bottom centre) — click to cast
# ═══════════════════════════════════════════════════

class SpellHUD:
    SLOT_W = 70
    SLOT_H = 66
    GAP    = 8

    def __init__(self):
        self.font       = pygame.font.SysFont("consolas", 13)
        self.font_ico   = pygame.font.SysFont("consolas", 16, bold=True)
        self._slot_rects: list[pygame.Rect] = []

    def _build_rects(self, n: int) -> list[pygame.Rect]:
        total = self.SLOT_W * n + self.GAP * (n - 1)
        sx    = (SCREEN_W - total) // 2
        sy    = SCREEN_H - self.SLOT_H - 50
        return [pygame.Rect(sx + i * (self.SLOT_W + self.GAP), sy,
                            self.SLOT_W, self.SLOT_H)
                for i in range(n)]

    def handle_event(self, event, equipped: list,
                     enemy_group, shielded_group=None,
                     spell_objects=None, player=None) -> bool:
        """Returns True if a spell was cast via click."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self._slot_rects):
                if rect.collidepoint(event.pos) and i < len(equipped):
                    equipped[i].cast(enemy_group, shielded_group,
                                     spell_objects, player)
                    return True
        return False

    def draw(self, screen, equipped: list):
        if not equipped:
            self._slot_rects = []
            return

        # Only ever show the single equipped spell
        spell = equipped[0]
        self._slot_rects = self._build_rects(1)
        rect  = self._slot_rects[0]
        mouse_pos = pygame.mouse.get_pos()
        hovered   = rect.collidepoint(mouse_pos)

        bg_col = (28, 34, 62) if hovered and spell.ready else (18, 22, 45)
        pygame.draw.rect(screen, bg_col, rect, border_radius=6)
        border_col = spell.COLOR if spell.ready else (60, 60, 80)
        if hovered and spell.ready:
            border_col = (255, 255, 255)
        pygame.draw.rect(screen, border_col, rect, width=2, border_radius=6)

        # cooldown fill (bottom-up)
        pct    = spell.cooldown_pct
        fill_h = int(rect.h * pct)
        if fill_h > 0:
            fill_surf = pygame.Surface((rect.w, fill_h), pygame.SRCALPHA)
            fill_surf.fill((*spell.COLOR, 45))
            screen.blit(fill_surf, (rect.x, rect.y + rect.h - fill_h))

        ico_cx = rect.centerx
        ico_cy = rect.y + 22
        pygame.draw.circle(screen, spell.COLOR, (ico_cx, ico_cy), 14)
        if hovered and spell.ready:
            pygame.draw.circle(screen, (255, 255, 255), (ico_cx, ico_cy), 14, 2)
        ico_txt = self.font_ico.render(_ICONS.get(spell.ID, "*"), True, (255, 255, 255))
        screen.blit(ico_txt, ico_txt.get_rect(center=(ico_cx, ico_cy)))

        lbl = self.font.render(spell.NAME, True, spell.COLOR)
        screen.blit(lbl, lbl.get_rect(centerx=ico_cx, top=rect.y + 40))

        if spell.ready:
            cd = self.font.render("READY", True, (100, 255, 160))
        else:
            cd = self.font.render(f"{spell.cd_seconds}s", True, (180, 180, 220))
        screen.blit(cd, cd.get_rect(centerx=ico_cx, top=rect.y + 53))

        # Always show Q as the hotkey
        key_lbl = self.font.render("Q", True, (80, 100, 140))
        screen.blit(key_lbl, key_lbl.get_rect(centerx=ico_cx, top=rect.y + 2))


# ═══════════════════════════════════════════════════
#  Pause menu  (ESC in-game)
# ═══════════════════════════════════════════════════

class PauseMenu:
    BTN_W = 240
    BTN_H = 52
    GAP   = 18

    def __init__(self):
        self.font_title = pygame.font.SysFont("consolas", 32, bold=True)
        self.font_btn   = pygame.font.SysFont("consolas", 18, bold=True)
        self.font_sub   = pygame.font.SysFont("consolas", 14)

        cx = SCREEN_W // 2
        cy = SCREEN_H // 2

        self.btn_menu = pygame.Rect(cx - self.BTN_W // 2, cy,
                                    self.BTN_W, self.BTN_H)
        self.btn_quit = pygame.Rect(cx - self.BTN_W // 2,
                                    cy + self.BTN_H + self.GAP,
                                    self.BTN_W, self.BTN_H)

    def handle_event(self, event) -> str | None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "resume"
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_menu.collidepoint(event.pos):
                return "menu"
            if self.btn_quit.collidepoint(event.pos):
                return "quit"
        return None

    def draw(self, screen):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

        cx = SCREEN_W // 2
        title = self.font_title.render("PAUSED", True, (200, 220, 255))
        screen.blit(title, title.get_rect(center=(cx, SCREEN_H // 2 - 80)))

        sub = self.font_sub.render("Press ESC to resume", True, (80, 100, 140))
        screen.blit(sub, sub.get_rect(center=(cx, SCREEN_H // 2 - 44)))

        mouse_pos = pygame.mouse.get_pos()

        hov_m = self.btn_menu.collidepoint(mouse_pos)
        pygame.draw.rect(screen,
                         (50, 60, 120) if hov_m else (30, 38, 80),
                         self.btn_menu, border_radius=10)
        pygame.draw.rect(screen,
                         (120, 160, 255) if hov_m else (70, 90, 160),
                         self.btn_menu, width=2, border_radius=10)
        lbl_m = self.font_btn.render("Back to Menu", True,
                                     (200, 220, 255) if hov_m else (140, 160, 220))
        screen.blit(lbl_m, lbl_m.get_rect(center=self.btn_menu.center))

        hov_q = self.btn_quit.collidepoint(mouse_pos)
        pygame.draw.rect(screen,
                         (100, 30, 30) if hov_q else (60, 20, 20),
                         self.btn_quit, border_radius=10)
        pygame.draw.rect(screen,
                         (255, 80, 80) if hov_q else (160, 60, 60),
                         self.btn_quit, width=2, border_radius=10)
        lbl_q = self.font_btn.render("Quit Game", True,
                                     (255, 120, 120) if hov_q else (200, 80, 80))
        screen.blit(lbl_q, lbl_q.get_rect(center=self.btn_quit.center))
