import pygame

from settings import (
    SCREEN_W, SCREEN_H, WORLD_W, WORLD_H, FPS, TITLE,
    ENEMY_COL,
    ORBIT_RADIUS, KILL_PER_LEVEL,
    ORBIT_W, ORBIT_H,
    SPEED_BONUS_PER_UPGRADE, SIZE_BONUS_PER_UPGRADE,
    SHIELDED_COL,
)
from entities  import Orbiter, DeathParticle, ShieldedEnemy
from utils     import redistribute_orbiters, make_fresh_scene
from ui        import UpgradeMenu, MainMenu
from highscore import load_highscore, save_highscore
from camera    import Camera
from wave_manager import WaveManager
from spells    import (FreezeSpell, BombSpell, ShockwaveSpell,
                       BombObject, ExplosionRing, ShockwaveObject,
                       SpellMenu, SpellHUD, SpellTabButton, PauseMenu,
                       ALL_SPELL_CLASSES)

# State
STATE_MENU      = "menu"
STATE_PLAYING   = "playing"
STATE_LEVEL_UP  = "level_up"
STATE_GAMEOVER  = "gameover"
STATE_SPELL_SEL = "spell_select"
STATE_PAUSED    = "paused"


def apply_upgrade(choice, upgrades, player, orbiter_group, all_sprites):
    upgrades[choice] = upgrades.get(choice, 0) + 1

    if choice == "speed":
        player.speed += SPEED_BONUS_PER_UPGRADE

    elif choice == "orbit":
        new_orb = Orbiter(
            player,
            w=ORBIT_W + SIZE_BONUS_PER_UPGRADE * upgrades.get("size", 0),
            h=ORBIT_H,
        )
        orbiter_group.add(new_orb)
        all_sprites.add(new_orb)
        redistribute_orbiters(list(orbiter_group))

    elif choice == "size":
        new_w = ORBIT_W + SIZE_BONUS_PER_UPGRADE * upgrades["size"]
        for orb in orbiter_group:
            orb.resize(new_w, ORBIT_H)


def draw_world_background(surface: pygame.Surface, camera: Camera):
    surface.fill((10, 10, 20))
    grid_step = 80
    off_x = int(camera.offset.x) % grid_step
    off_y = int(camera.offset.y) % grid_step

    for x in range(off_x, SCREEN_W + grid_step, grid_step):
        pygame.draw.line(surface, (18, 18, 32), (x, 0), (x, SCREEN_H))
    for y in range(off_y, SCREEN_H + grid_step, grid_step):
        pygame.draw.line(surface, (18, 18, 32), (0, y), (SCREEN_W, y))

    # Margins
    world_rect = pygame.Rect(
        camera.offset.x, camera.offset.y, WORLD_W, WORLD_H
    )
    pygame.draw.rect(surface, (40, 40, 80), world_rect, 3)


def draw_minimap(surface, player, enemy_group, camera):

    mm_w, mm_h = 160, 107
    mm_x = SCREEN_W - mm_w - 10
    mm_y = SCREEN_H - mm_h - 10
    scale_x = mm_w / WORLD_W
    scale_y = mm_h / WORLD_H

    mm_surf = pygame.Surface((mm_w, mm_h), pygame.SRCALPHA)
    mm_surf.fill((10, 10, 25, 180))
    pygame.draw.rect(mm_surf, (40, 60, 100), (0, 0, mm_w, mm_h), 1)

    # Enemy (colour-coded: shielded vs normal)
    for e in enemy_group:
        ex = int(e.pos.x * scale_x)
        ey = int(e.pos.y * scale_y)
        col = SHIELDED_COL if hasattr(e, 'shielded') else ENEMY_COL
        pygame.draw.circle(mm_surf, col, (ex, ey), 2)

    # Player
    px = int(player.pos.x * scale_x)
    py = int(player.pos.y * scale_y)
    pygame.draw.circle(mm_surf, (100, 180, 255), (px, py), 4)

    surface.blit(mm_surf, (mm_x, mm_y))


def main():
    pygame.init()
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption(TITLE)
    clock  = pygame.time.Clock()

    font_s = pygame.font.SysFont("consolas", 16)
    font_b = pygame.font.SysFont("consolas", 22, bold=True)
    font_m = pygame.font.SysFont("consolas", 18)
    font_wave = pygame.font.SysFont("consolas", 28, bold=True)

    # UI
    main_menu    = MainMenu()
    upgrade_menu = UpgradeMenu()
    highscore    = load_highscore()

    # Starting new game
    def new_game():
        p, a, og, eg, pg = make_fresh_scene()
        sg  = pygame.sprite.Group()   # shielded enemy group
        wm  = WaveManager(p)
        cam = Camera()
        return (p, a, og, eg, pg, sg,
                0, 0, 0, KILL_PER_LEVEL,
                {"speed": 0, "orbit": 0, "size": 0},
                wm, cam)

    (player, all_sprites, orbiter_group, enemy_group, particle_group, shielded_group,
     kills, mastery_pts, kills_since_mastery, kill_threshold,
     upgrades, wave_mgr, camera) = new_game()

    # Spell / rebirth state (persists across new_game resets during a run)
    rebirth_count    = 0
    unlocked_spells  = []
    equipped_spells  = []
    spell_objects    = pygame.sprite.Group()   # live bombs, shockwaves
    explosion_rings  = []                      # visual-only ExplosionRing list
    spell_menu       = SpellMenu()
    spell_hud        = SpellHUD()
    spell_tab_btn    = SpellTabButton()
    pause_menu       = PauseMenu()

    state          = STATE_MENU
    is_new_record  = False
    gameover_timer = 0
    wave_flash     = 0
    pending_rebirth = False   # waiting for player to pick spell

    running = True
    while running:
        clock.tick(FPS)

        # Stare joc
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # ── PAUSE menu ──────────────────────────────────────────────
            if state == STATE_PAUSED:
                result = pause_menu.handle_event(event)
                if result == "resume":
                    state = STATE_PLAYING
                elif result == "menu":
                    state = STATE_MENU
                elif result == "quit":
                    running = False
                continue   # skip all other handling while paused

            # ── MAIN MENU ───────────────────────────────────────────────
            if state == STATE_MENU:
                if main_menu.handle_event(event):
                    (player, all_sprites, orbiter_group, enemy_group, particle_group, shielded_group,
                     kills, mastery_pts, kills_since_mastery, kill_threshold,
                     upgrades, wave_mgr, camera) = new_game()
                    rebirth_count   = 0
                    unlocked_spells = []
                    equipped_spells = []
                    spell_objects.empty()
                    explosion_rings.clear()
                    state = STATE_PLAYING

            # ── LEVEL UP ────────────────────────────────────────────────
            elif state == STATE_LEVEL_UP:
                # can rebirth if there are still spells not yet unlocked
                available_spells = [cls for cls in ALL_SPELL_CLASSES
                                    if cls not in unlocked_spells]
                can_rebirth = len(available_spells) > 0
                choice = upgrade_menu.handle_event(event, upgrades, can_rebirth)
                if choice == "rebirth":
                    rebirth_count += 1
                    upgrades = {"speed": 0, "orbit": 0, "size": 0}
                    import settings as _s
                    player.speed = _s.PLAYER_SPEED
                    for orb in list(orbiter_group):
                        orb.kill()
                    orbiter_group.empty()
                    new_orb = Orbiter(player, angle_offset=0)
                    orbiter_group.add(new_orb)
                    all_sprites.add(new_orb)
                    # Open spell select showing only spells not yet unlocked
                    spell_menu.open(rebirth=True)
                    spell_menu.set_choices(available_spells)
                    state = STATE_SPELL_SEL
                elif choice == "dismiss_max":
                    mastery_pts = 0
                    state = STATE_PLAYING
                elif choice:
                    apply_upgrade(choice, upgrades, player, orbiter_group, all_sprites)
                    mastery_pts -= 1
                    if mastery_pts == 0:
                        state = STATE_PLAYING

            # ── SPELL SELECT (paused) ────────────────────────────────────
            elif state == STATE_SPELL_SEL:
                consumed = spell_menu.handle_event(event, spell_menu.choices, equipped_spells)
                if consumed and not spell_menu.visible:
                    # Unlock the spell class that was just picked (rebirth mode)
                    if spell_menu.last_picked and spell_menu.last_picked not in unlocked_spells:
                        unlocked_spells.append(spell_menu.last_picked)
                    state = STATE_PLAYING
                continue   # ESC/click in spell menu never reaches PLAYING handlers

            # ── GAME OVER ───────────────────────────────────────────────
            elif state == STATE_GAMEOVER:
                if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    state = STATE_MENU

            # ── SPELL BOOK (non-rebirth, overlays playing) ───────────────
            if state == STATE_PLAYING:
                # Spell menu toggle via TAB or left button
                if not spell_menu.visible:
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                        if unlocked_spells:
                            spell_menu.open(rebirth=False)
                            spell_menu.set_choices(unlocked_spells)
                            state = STATE_SPELL_SEL
                    if unlocked_spells:
                        if spell_tab_btn.handle_event(event):
                            spell_menu.open(rebirth=False)
                            spell_menu.set_choices(unlocked_spells)
                            state = STATE_SPELL_SEL

                # Click-to-cast on HUD spell icons
                spell_hud.handle_event(event, equipped_spells,
                                       enemy_group, shielded_group,
                                       spell_objects, player)

                # Q always casts the equipped spell
                if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                    if equipped_spells:
                        equipped_spells[0].cast(enemy_group, shielded_group,
                                                spell_objects, player)

                # ESC → pause (only when spell menu is NOT open)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    state = STATE_PAUSED


        if state == STATE_PLAYING:

            camera.update(player)

            if wave_mgr.update(enemy_group, all_sprites, shielded_group):
                wave_flash = 120

            if wave_flash > 0:
                wave_flash -= 1

            keys = pygame.key.get_pressed()
            player.update(keys)
            player.set_danger(enemy_group)

            orbiter_group.update()
            enemy_group.update()
            particle_group.update()

            for spell in equipped_spells:
                spell.update()

            # ── Spell objects (bombs, shockwaves) ──
            spell_objects.update()

            for obj in list(spell_objects):
                if isinstance(obj, BombObject) and not obj.exploded:
                    if obj.fuse_timer <= 0:
                        spell_kills = obj.explode(enemy_group, shielded_group,
                                                   particle_group, all_sprites)
                        explosion_rings.append(ExplosionRing(
                            obj.world_pos.x, obj.world_pos.y))
                        kills += spell_kills
                        kills_since_mastery += spell_kills

                elif isinstance(obj, ShockwaveObject):
                    spell_kills = obj.check_kills(enemy_group, shielded_group,
                                                  particle_group, all_sprites)
                    kills += spell_kills
                    kills_since_mastery += spell_kills

            # Check mastery threshold after spell kills
            if kills_since_mastery >= kill_threshold:
                kills_since_mastery -= kill_threshold
                kill_threshold += 2
                mastery_pts += 1
                truly_maxed = (upgrade_menu.all_maxed(upgrades) and
                               len([c for c in ALL_SPELL_CLASSES
                                    if c not in unlocked_spells]) == 0)
                if not truly_maxed:
                    state = STATE_LEVEL_UP

            # Update explosion rings
            for ring in explosion_rings[:]:
                ring.update()
                if ring.life <= 0:
                    explosion_rings.remove(ring)

            hits = pygame.sprite.groupcollide(
                enemy_group, orbiter_group, False, False
            )
            for enemy, orbiters in hits.items():
                dmg = sum(o.damage for o in orbiters)
                died = enemy.take_damage(dmg)
                if died:
                    kills += 1
                    kills_since_mastery += 1
                    if kills_since_mastery >= kill_threshold:
                        kills_since_mastery = 0
                        kill_threshold += 2
                        mastery_pts += 1
                        truly_maxed = (upgrade_menu.all_maxed(upgrades) and
                                       len([c for c in ALL_SPELL_CLASSES
                                            if c not in unlocked_spells]) == 0)
                        if not truly_maxed:
                            state = STATE_LEVEL_UP
                    for _ in range(6):
                        p = DeathParticle(enemy.pos.x, enemy.pos.y)
                        particle_group.add(p)
                        all_sprites.add(p)

            if pygame.sprite.spritecollide(player, enemy_group, False,
                                           pygame.sprite.collide_circle):
                is_new_record = save_highscore(kills)
                highscore     = load_highscore()
                state         = STATE_GAMEOVER
                gameover_timer = 0

        elif state == STATE_GAMEOVER:
            gameover_timer += 1
            particle_group.update()

        # STATE_SPELL_SEL and STATE_PAUSED — no game updates, world frozen

        if state == STATE_MENU:
            main_menu.draw(screen, highscore)

        elif state in (STATE_PLAYING, STATE_LEVEL_UP, STATE_SPELL_SEL, STATE_PAUSED):
            draw_world_background(screen, camera)

            orbit_screen = camera.apply_pos(player.pos)
            pygame.draw.circle(screen, (40, 60, 100), orbit_screen, ORBIT_RADIUS, 1)

            for e in enemy_group:
                screen.blit(e.image, camera.apply(e))

            screen.blit(player.image, camera.apply(player))

            for o in orbiter_group:
                screen.blit(o.image, camera.apply(o))

            for p in particle_group:
                screen.blit(p.image, camera.apply(p))

            # ── Spell object world-space visuals ──
            for obj in spell_objects:
                if isinstance(obj, BombObject):
                    screen.blit(obj.image, camera.apply(obj))
                elif isinstance(obj, ShockwaveObject):
                    obj.draw_world(screen, camera)
            for ring in explosion_rings:
                ring.draw_world(screen, camera)

            draw_minimap(screen, player, enemy_group, camera)

            wave_surf = font_wave.render(f"WAVE  {wave_mgr.wave}", True, (180, 200, 255))
            screen.blit(wave_surf, wave_surf.get_rect(centerx=SCREEN_W // 2, top=10))

            # UI stanga
            next_lvl = kill_threshold - kills_since_mastery
            truly_maxed = (upgrade_menu.all_maxed(upgrades) and
                           len([c for c in ALL_SPELL_CLASSES
                                if c not in unlocked_spells]) == 0)
            if truly_maxed:
                next_upg_text = "Next UPG: MAX"
                next_upg_col  = (255, 215, 60)
            else:
                next_upg_text = f"Next UPG: {next_lvl} kills"
                next_upg_col  = (120, 200, 120)

            hud = [
                (f"Kills   : {kills}",            (255, 255, 255)),
                (f"Best    : {highscore}",         (255, 215, 60)),
                (next_upg_text,                    next_upg_col),
                (f"Enemies : {len(enemy_group)}",  ENEMY_COL),
            ]
            for i, (text, col) in enumerate(hud):
                screen.blit(font_s.render(text, True, col), (12, 12 + i * 22))

            # UI jos
            sp = upgrades.get("speed", 0)
            si = upgrades.get("size",  0)
            stat = font_s.render(f"SPD+{sp}  SZ+{si}  ORB {len(orbiter_group)}", True, (160, 200, 255))
            screen.blit(stat, (12, SCREEN_H - 26))

            # UI dreapta
            for i, text in enumerate(["WASD - Movement", "ESC  - Pause"]):
                screen.blit(font_s.render(text, True, (80, 100, 130)),
                            (SCREEN_W - 180, 12 + i * 20))

            # next wave countdown
            if wave_mgr.is_break and state == STATE_PLAYING:
                bar_w = 300
                bar_h = 14
                bx = (SCREEN_W - bar_w) // 2
                by = SCREEN_H - 36
                prog = wave_mgr.break_progress
                pygame.draw.rect(screen, (30, 30, 60), (bx, by, bar_w, bar_h), border_radius=6)
                pygame.draw.rect(screen, (80, 120, 255),
                                 (bx, by, int(bar_w * prog), bar_h), border_radius=6)
                lbl = font_s.render(f"Wave {wave_mgr.wave + 1} in...", True, (140, 160, 220))
                screen.blit(lbl, lbl.get_rect(centerx=SCREEN_W // 2, bottom=by - 4))

            if wave_flash > 0 and state == STATE_PLAYING:
                alpha = min(255, wave_flash * 4)
                wsurf = font_wave.render(f"-- WAVE {wave_mgr.wave} --", True, (180, 200, 255))
                wsurf.set_alpha(alpha)
                screen.blit(wsurf, wsurf.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 60)))

            # Spell HUD + tab button (always drawn over game world)
            spell_hud.draw(screen, equipped_spells)
            spell_tab_btn.draw(screen, unlocked_spells, state == STATE_SPELL_SEL)

            # Overlays per state
            if state == STATE_LEVEL_UP:
                available_spells = [cls for cls in ALL_SPELL_CLASSES
                                    if cls not in unlocked_spells]
                can_rebirth = len(available_spells) > 0
                upgrade_menu.draw(screen, mastery_pts, upgrades, rebirth_count, can_rebirth)

            elif state == STATE_SPELL_SEL:
                spell_menu.draw(screen, spell_menu.choices, equipped_spells)

            elif state == STATE_PAUSED:
                pause_menu.draw(screen)

        elif state == STATE_GAMEOVER:
            draw_world_background(screen, camera)
            for p in particle_group:
                screen.blit(p.image, camera.apply(p))

            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 170))
            screen.blit(overlay, (0, 0))

            lines = [
                (font_b.render("GAME  OVER", True, (255, 80, 80)),         0),
                (font_m.render(f"Wave: {wave_mgr.wave}   Kills: {kills}", True, (255, 255, 255)), 50),
            ]
            if is_new_record:
                lines.append((font_m.render("NOU RECORD!", True, (255, 215, 60)), 90))
            else:
                lines.append((font_m.render(f"Best: {highscore}", True, (255, 215, 60)), 90))

            if (gameover_timer // 30) % 2 == 0:
                lines.append((font_s.render("Apasă orice tastă pentru meniu", True, (160, 160, 180)), 140))

            base_y = SCREEN_H // 2 - 80
            for surf, dy in lines:
                screen.blit(surf, surf.get_rect(center=(SCREEN_W // 2, base_y + dy)))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
