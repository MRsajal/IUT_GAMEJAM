from pathlib import Path
import random

import pygame

from music_manager import play_background_music
from player import Player
from portal import Portal
from .entities import (
    CrystalSocket,
    FallingDebris,
    FireBarrier,
    MovableCrystal,
    ResetPedestal,
    Shrine,
    DEBRIS_DAMAGE,
)


SCREEN_WIDTH = 600
SCREEN_HEIGHT = 320
MAP_WIDTH = 1800
MAP_HEIGHT = 320
GROUND_Y = 288
PLAYER_SPAWN = (80, GROUND_Y - 40)
CHECKPOINT_SPAWNS = (
    PLAYER_SPAWN,
    (640, GROUND_Y - 40),
    (1190, GROUND_Y - 40),
    (1680, GROUND_Y - 40),
)
MAP_PATH = Path(__file__).parent / "map5.png"
MUSIC_PATH = Path(__file__).parent / "music.mp3"
CYAN = (80, 230, 255)
VIOLET = (190, 105, 255)

SECTION_OBJECTIVES = (
    (
        "TRIAL 1: CRYSTAL ALIGNMENT",
        "Push the CYAN crystal into the matching CYAN floor socket.",
        "Walk against it to push. Press K to kick it farther.",
    ),
    (
        "TRIAL 2: FIRE AND DEBRIS",
        "Use the shrine (E), then burn the cracked RED growth with F.",
        "Move away from the red warning lines before debris falls.",
    ),
    (
        "TRIAL 3: WIND ASCENT",
        "Move the VIOLET crystal onto its socket, then press G to fly.",
        "Touch the glowing seal high above. Both conditions are required.",
    ),
    (
        "LABYRINTH RESTORED",
        "All three seals are active. Reach the portal on the far right.",
        "You can return here later; your completed trials are saved.",
    ),
)


def draw_text_box(screen, rect, lines, font, title_font=None):
    surface = pygame.Surface(rect.size, pygame.SRCALPHA)
    surface.fill((12, 17, 35, 225))
    screen.blit(surface, rect)
    pygame.draw.rect(screen, (105, 220, 235), rect, 2, border_radius=7)
    y = rect.y + 8
    for index, line in enumerate(lines):
        use_font = title_font if index == 0 and title_font else font
        color = (125, 240, 255) if index == 0 else (240, 240, 225)
        text = use_font.render(line, True, color)
        screen.blit(text, (rect.x + 10, y))
        y += text.get_height() + 3


def draw_world_label(screen, camera_x, world_x, y, text, font, color):
    label = font.render(text, True, color)
    rect = label.get_rect(midbottom=(world_x - round(camera_x), y))
    background = rect.inflate(8, 5)
    pygame.draw.rect(screen, (12, 17, 35), background, border_radius=4)
    pygame.draw.rect(screen, color, background, 1, border_radius=4)
    screen.blit(label, rect)


def load_map():
    image = pygame.image.load(MAP_PATH).convert()
    return pygame.transform.scale(image, (MAP_WIDTH, MAP_HEIGHT))


def base_platforms():
    platforms = [pygame.Rect(0, GROUND_Y, MAP_WIDTH, MAP_HEIGHT - GROUND_Y)]
    platforms.extend(
        [
            pygame.Rect(1210, 218, 150, 16),
            pygame.Rect(1430, 165, 145, 16),
            pygame.Rect(1610, 112, 140, 16),
        ]
    )
    return platforms


class PuzzleState:
    def __init__(self, checkpoint):
        self.checkpoint = max(0, min(3, checkpoint))
        self.crystal1 = MovableCrystal(245, GROUND_Y, CYAN)
        self.socket1 = CrystalSocket(500, GROUND_Y, CYAN)
        self.barrier = FireBarrier((890, 180, 42, GROUND_Y - 180))
        self.crystal3 = MovableCrystal(1260, GROUND_Y, VIOLET)
        self.socket3 = CrystalSocket(1515, GROUND_Y, VIOLET)
        self.gates = [
            pygame.Rect(570, 150, 28, GROUND_Y - 150),
            pygame.Rect(1130, 120, 28, GROUND_Y - 120),
            pygame.Rect(1650, 65, 28, GROUND_Y - 65),
        ]
        self.shrines = [
            Shrine(145, GROUND_Y),
            Shrine(735, GROUND_Y),
            Shrine(1215, GROUND_Y),
        ]
        self.pedestals = [
            ResetPedestal(190, GROUND_Y),
            ResetPedestal(690, GROUND_Y),
            ResetPedestal(1245, GROUND_Y),
        ]
        self.flight_seal = pygame.Rect(1600, 65, 38, 38)
        self.debris = []
        if self.checkpoint >= 1:
            self.crystal1.rect.centerx = self.socket1.rect.centerx
            self.crystal1.rect.bottom = GROUND_Y
        if self.checkpoint >= 2:
            self.barrier.destroyed = True
        if self.checkpoint >= 3:
            self.crystal3.rect.centerx = self.socket3.rect.centerx
            self.crystal3.rect.bottom = GROUND_Y

    def reset_current(self):
        if self.checkpoint == 0:
            self.crystal1.reset()
        elif self.checkpoint == 1:
            self.barrier.destroyed = False
        elif self.checkpoint == 2:
            self.crystal3.reset()
        self.debris.clear()

    def gate_rects(self):
        return [
            gate for index, gate in enumerate(self.gates)
            if self.checkpoint <= index
        ]

    def update_blockers(self):
        crystals = [self.crystal1, self.crystal3]
        gates = self.gate_rects()
        barrier_rects = [] if self.barrier.destroyed else [self.barrier.rect]
        for crystal in crystals:
            other = [item.rect for item in crystals if item is not crystal]
            crystal.blockers = gates + barrier_rects + other + [
                pygame.Rect(-20, 0, 20, MAP_HEIGHT),
                pygame.Rect(MAP_WIDTH, 0, 20, MAP_HEIGHT),
            ]

    def try_push(self, player, direction):
        if not direction:
            return
        for crystal in (self.crystal1, self.crystal3):
            vertically_aligned = (
                player.rect.bottom > crystal.rect.top
                and player.rect.top < crystal.rect.bottom
            )
            touching = (
                direction > 0
                and 0 <= crystal.rect.left - player.rect.right <= 3
            ) or (
                direction < 0
                and 0 <= player.rect.left - crystal.rect.right <= 3
            )
            if not vertically_aligned or not touching:
                continue
            dx = direction * 2
            if crystal.push(dx):
                player.position.x += dx
                player.rect.x = round(player.position.x)

    def spawn_debris(self, center_x):
        for offset in (-28, 0, 28):
            self.debris.append(
                FallingDebris(center_x + offset + random.randint(-5, 5))
            )

    def draw(self, screen, camera_x):
        self.socket1.draw(
            screen, camera_x, self.checkpoint >= 1
            or self.socket1.accepts(self.crystal1)
        )
        self.socket3.draw(
            screen, camera_x, self.checkpoint >= 3
            or self.socket3.accepts(self.crystal3)
        )
        self.crystal1.draw(screen, camera_x)
        self.crystal3.draw(screen, camera_x)
        self.barrier.draw(screen, camera_x)
        for gate in self.gate_rects():
            rect = gate.move(-round(camera_x), 0)
            pygame.draw.rect(screen, (55, 25, 90), rect)
            for y in range(rect.top, rect.bottom, 16):
                pygame.draw.line(
                    screen, (150, 90, 220), (rect.left, y),
                    (rect.right, y + 10), 2
                )
        for shrine in self.shrines:
            shrine.draw(screen, camera_x)
        for pedestal in self.pedestals:
            pedestal.draw(screen, camera_x)
        seal = self.flight_seal.move(-round(camera_x), 0)
        pygame.draw.rect(
            screen,
            (110, 245, 225) if self.checkpoint >= 3 else (80, 65, 115),
            seal,
            border_radius=8,
        )
        for debris in self.debris:
            debris.draw(screen, camera_x, MAP_HEIGHT)


def map5(player=None, arrived_from=None):
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Map 5 - Crystal Labyrinth")
    clock = pygame.time.Clock()
    play_background_music(MUSIC_PATH)
    background = load_map()
    platforms = base_platforms()

    if player is None:
        player = Player(*PLAYER_SPAWN)
    checkpoint = 3 if player.map5_cleared else player.map5_checkpoint
    state = PuzzleState(checkpoint)
    player.set_position(*CHECKPOINT_SPAWNS[checkpoint])

    saved_magic = dict(player.magic_uses)
    saved_held_magic = list(player.held_magic)
    saved_flight_time = player.flight_time_left

    return_portal = Portal(28, GROUND_Y)
    exit_portal = Portal(MAP_WIDTH - 35, GROUND_Y)
    font = pygame.font.Font(None, 20)
    title_font = pygame.font.Font(None, 24)
    label_font = pygame.font.Font(None, 17)
    camera_x = 0.0
    running = True
    next_map = None
    next_arrival_from = None
    barrier_was_destroyed = state.barrier.destroyed
    map_elapsed = 0.0
    help_open = not player.map5_cleared and player.map5_checkpoint == 0

    while running:
        delta_time = clock.tick(60) / 1000
        map_elapsed += delta_time
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue

            consumed = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                help_open = not help_open
                consumed = True
            elif help_open and event.type == pygame.KEYDOWN:
                if event.key in (
                    pygame.K_RETURN,
                    pygame.K_KP_ENTER,
                    pygame.K_SPACE,
                    pygame.K_e,
                    pygame.K_ESCAPE,
                ):
                    help_open = False
                consumed = True
            if (
                not help_open
                and not consumed
                and event.type == pygame.KEYDOWN
                and event.key == pygame.K_e
                and not player.ui_open
            ):
                for shrine in state.shrines:
                    if shrine.nearby(player):
                        shrine.recharge(player)
                        consumed = True
                        break
                if not consumed:
                    for index, pedestal in enumerate(state.pedestals):
                        if index == state.checkpoint and pedestal.nearby(player):
                            state.reset_current()
                            consumed = True
                            break
            if not consumed:
                consumed = player.handle_event(
                    event, allow_flight_activation=True
                )
            if (
                not consumed and event.type == pygame.KEYDOWN
                and event.key == pygame.K_ESCAPE
            ):
                running = False

        if not player.ui_open and not help_open:
            keys = pygame.key.get_pressed()
            direction = int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(
                keys[pygame.K_a] or keys[pygame.K_LEFT]
            )
            state.update_blockers()
            solid_rects = (
                state.gate_rects()
                + [state.crystal1.rect, state.crystal3.rect]
                + ([] if state.barrier.destroyed else [state.barrier.rect])
            )
            damage_targets = [state.crystal1, state.crystal3, state.barrier]
            player.update(
                delta_time,
                platforms,
                MAP_WIDTH,
                damage_targets,
                solid_rects,
                MAP_HEIGHT,
            )
            if direction:
                state.try_push(player, direction)

        if not barrier_was_destroyed and state.barrier.destroyed:
            state.spawn_debris(state.barrier.rect.centerx)
        barrier_was_destroyed = state.barrier.destroyed

        for debris in state.debris:
            debris.update(delta_time)
            if (
                debris.warning_time <= 0
                and not debris.hit
                and debris.rect.colliderect(player.rect)
            ):
                debris.hit = True
                player.take_damage(DEBRIS_DAMAGE)
        state.debris = [
            debris for debris in state.debris if debris.rect.top <= MAP_HEIGHT
        ]

        if state.checkpoint == 0 and state.socket1.accepts(state.crystal1):
            state.checkpoint = 1
            player.map5_checkpoint = 1
            player.combat_message = "First crystal seal restored!"
            player.combat_message_time_left = 2.0
        elif state.checkpoint == 1 and state.barrier.destroyed:
            state.checkpoint = 2
            player.map5_checkpoint = 2
            player.combat_message = "Fire seal restored!"
            player.combat_message_time_left = 2.0
        elif (
            state.checkpoint == 2
            and state.socket3.accepts(state.crystal3)
            and player.rect.colliderect(state.flight_seal.inflate(30, 30))
        ):
            state.checkpoint = 3
            player.map5_checkpoint = 3
            player.map5_cleared = True
            player.combat_message = "Crystal Labyrinth restored!"
            player.combat_message_time_left = 2.5

        return_portal.update(delta_time)
        if state.checkpoint >= 3:
            exit_portal.update(delta_time)

        if player.death_animation_finished:
            state = PuzzleState(player.map5_checkpoint)
            player.health = player.max_health
            player.set_position(*CHECKPOINT_SPAWNS[player.map5_checkpoint])
            barrier_was_destroyed = state.barrier.destroyed
        elif (
            not player.is_dead and not player.ui_open
            and player.rect.colliderect(return_portal.rect)
        ):
            next_map = "map1"
            next_arrival_from = "map5"
            running = False
        elif (
            state.checkpoint >= 3 and not player.is_dead
            and not player.ui_open
            and player.rect.colliderect(exit_portal.rect)
        ):
            next_map = "map1"
            next_arrival_from = "map5"
            running = False

        camera_x = max(
            0,
            min(
                player.rect.centerx - SCREEN_WIDTH / 2,
                MAP_WIDTH - SCREEN_WIDTH,
            ),
        )
        screen.blit(
            background,
            (0, 0),
            pygame.Rect(round(camera_x), 0, SCREEN_WIDTH, SCREEN_HEIGHT),
        )
        for platform in platforms[1:]:
            pygame.draw.rect(
                screen, (48, 55, 90), platform.move(-round(camera_x), 0)
            )
        return_portal.draw(screen, camera_x)
        if state.checkpoint >= 3:
            exit_portal.draw(screen, camera_x)
        state.draw(screen, camera_x)
        if state.checkpoint == 0:
            draw_world_label(
                screen, camera_x, state.crystal1.rect.centerx,
                state.crystal1.rect.top - 5, "MOVABLE CYAN CRYSTAL",
                label_font, CYAN
            )
            draw_world_label(
                screen, camera_x, state.socket1.rect.centerx,
                state.socket1.rect.top - 4, "MATCHING SOCKET",
                label_font, CYAN
            )
        elif state.checkpoint == 1:
            draw_world_label(
                screen, camera_x, state.shrines[1].rect.centerx,
                state.shrines[1].rect.top - 5, "E: FIRE SHRINE",
                label_font, (255, 165, 90)
            )
            if not state.barrier.destroyed:
                draw_world_label(
                    screen, camera_x, state.barrier.rect.centerx,
                    state.barrier.rect.top - 5, "F: BURN CRACKED GROWTH",
                    label_font, (255, 115, 90)
                )
        elif state.checkpoint == 2:
            draw_world_label(
                screen, camera_x, state.crystal3.rect.centerx,
                state.crystal3.rect.top - 5, "MOVABLE VIOLET CRYSTAL",
                label_font, VIOLET
            )
            draw_world_label(
                screen, camera_x, state.flight_seal.centerx,
                state.flight_seal.top - 5, "FINAL WIND SEAL",
                label_font, (125, 240, 255)
            )
        player.draw(screen, camera_x)
        player.draw_health_bar(screen)
        objective_lines = SECTION_OBJECTIVES[state.checkpoint]
        draw_text_box(
            screen,
            pygame.Rect(82, 53, 436, 68),
            (
                f"{objective_lines[0]}  |  Seals {state.checkpoint}/3",
                objective_lines[1],
                objective_lines[2],
            ),
            label_font,
            font,
        )
        tab_hint = label_font.render(
            "TAB: Full instructions   E: Use shrine/reset pedestal",
            True,
            (210, 225, 240),
        )
        screen.blit(
            tab_hint,
            tab_hint.get_rect(midbottom=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 5)),
        )
        if help_open:
            draw_text_box(
                screen,
                pygame.Rect(42, 35, SCREEN_WIDTH - 84, SCREEN_HEIGHT - 70),
                (
                    "CRYSTAL LABYRINTH — HOW TO WIN",
                    "Restore 3 seals. Each completed trial opens the next gate.",
                    "1. CYAN: push or kick the crystal onto its same-color socket.",
                    "2. FIRE: press E at the shrine, press F at red cracked growth.",
                    "   Red floor warnings mean debris is about to fall—move away.",
                    "3. VIOLET + WIND: socket the violet crystal, press G to fly,",
                    "   then touch the high final seal. Doing only one is not enough.",
                    "Stuck? Press E at the small RESET pedestal for the current trial.",
                    "Controls: A/D move, W jump/up, K kick, F fire, G wind/fly.",
                    "Press ENTER, SPACE, E, ESC, or TAB to close this guide.",
                ),
                font,
                title_font,
            )
        player.draw_active_screen(screen)
        pygame.display.flip()

    player.magic_uses.clear()
    player.magic_uses.update(saved_magic)
    player.held_magic[:] = saved_held_magic
    player.flight_time_left = max(0.0, saved_flight_time - map_elapsed)
    return next_map, player, next_arrival_from
