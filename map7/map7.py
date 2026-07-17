from pathlib import Path
import csv

import pygame

from ghosts import Ghost, GhostWindow
from player import Player
from portal import Portal
from .interactions import (
    InteractionWindow,
    create_interactables,
    CANDLE_SEQUENCE,
    draw_lit_candles,
    draw_interaction_prompt,
    light_candle,
    nearest_interactable,
)


SCREEN_WIDTH = 600
SCREEN_HEIGHT = 320
MAP_WIDTH = 960
MAP_HEIGHT = 320
TILE_SIZE = 16
PLAYER_SPAWN = (60, 80)
EXIT_PORTAL_X = MAP_WIDTH - 28
EXIT_PORTAL_BOTTOM = 288
PUZZLE_TIME_LIMIT = 90.0
MAP_PATH = Path(__file__).parent / "map7.png"
PLATFORM_PATH = Path(__file__).parent / "map7_Tile Layer 2.csv"


def load_map():
    """Load Map 7 at its native world size."""
    image = pygame.image.load(MAP_PATH).convert()
    if image.get_size() != (MAP_WIDTH, MAP_HEIGHT):
        image = pygame.transform.scale(
            image, (MAP_WIDTH, MAP_HEIGHT)
        )
    return image


def create_platform_rects():
    """Use every foreground tile as a landing surface."""
    platform_rects = []
    with PLATFORM_PATH.open(newline="", encoding="utf-8") as csv_file:
        for row_number, row in enumerate(csv.reader(csv_file)):
            for column_number, tile_value in enumerate(row):
                if int(tile_value) >= 0:
                    platform_rects.append(
                        pygame.Rect(
                            column_number * TILE_SIZE,
                            row_number * TILE_SIZE,
                            TILE_SIZE,
                            TILE_SIZE,
                        )
                    )
    return platform_rects


def reset_timed_puzzle(player):
    player.map7_painting_angle = 0
    player.map7_painting_solved = False
    player.map7_clock_hour = 12
    player.map7_clock_minute = 0
    player.map7_clock_solved = False
    player.map7_candles_lit.clear()
    player.map7_candles_solved = False
    player.map7_mission_complete = False
    player.map7_puzzle_time_left = PUZZLE_TIME_LIMIT
    player.map7_puzzle_timer_started = True
    player.combat_message = "Time expired. The puzzles have reset!"
    player.combat_message_time_left = 3.0


def draw_puzzle_timer(screen, player):
    seconds_left = max(0, int(player.map7_puzzle_time_left + 0.99))
    minutes, seconds = divmod(seconds_left, 60)
    font = pygame.font.Font(None, 24)
    text = font.render(
        f"Time: {minutes}:{seconds:02d}", True, (255, 225, 135)
    )
    rect = text.get_rect(topright=(SCREEN_WIDTH - 14, 14))
    pygame.draw.rect(
        screen, (25, 23, 38), rect.inflate(12, 7), border_radius=5
    )
    screen.blit(text, rect)


def map7(player=None, arrived_from=None):
    """Display native Map 7 with player movement and a scrolling camera."""
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Map 7 - Image Test")
    clock = pygame.time.Clock()
    background = load_map()
    platform_rects = create_platform_rects()
    interactables = create_interactables()
    prompt_font = pygame.font.Font(None, 18)

    if player is None:
        player = Player(*PLAYER_SPAWN)
    else:
        player.set_position(*PLAYER_SPAWN)

    exit_portal = Portal(EXIT_PORTAL_X, EXIT_PORTAL_BOTTOM)
    ghost = Ghost(center_x=110, bottom_y=144)
    ghost_window = None
    if not player.map7_ghost_intro_seen:
        ghost_window = GhostWindow("intro")

    running = True
    next_map = None
    next_arrival_from = None
    camera_x = 0.0
    interaction_window = None

    while running:
        delta_time = clock.tick(60) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue

            event_consumed = False
            if ghost_window is not None:
                ghost_kind = ghost_window.kind
                event_consumed = ghost_window.handle_event(event)
                if ghost_window.closed:
                    ghost_window = None
                    if ghost_kind == "intro":
                        player.map7_ghost_intro_seen = True
                    else:
                        player.map7_ghost_reward_seen = True
                        player.map7_has_book = True
                        player.combat_message = "Book of Arcana received!"
                        player.combat_message_time_left = 3.0
            elif interaction_window is not None:
                event_consumed = interaction_window.handle_event(event)
                if interaction_window.closed:
                    interaction_window = None
            elif (
                event.type == pygame.KEYDOWN
                and event.key == pygame.K_e
                and not player.ui_open
            ):
                nearby = nearest_interactable(player, interactables)
                if nearby is not None:
                    if nearby.object_type in CANDLE_SEQUENCE:
                        light_candle(player, nearby.object_type)
                    else:
                        interaction_window = InteractionWindow(nearby, player)
                    event_consumed = True

            if not event_consumed:
                event_consumed = player.handle_event(event)
            if (
                not event_consumed
                and event.type == pygame.KEYDOWN
                and event.key == pygame.K_ESCAPE
            ):
                next_map = "map6" if arrived_from == "map6" else "map1"
                next_arrival_from = "map7"
                running = False

        modal_open = interaction_window is not None or ghost_window is not None
        if not player.ui_open and not modal_open:
            player.update(
                delta_time,
                platform_rects,
                MAP_WIDTH,
                map_height=MAP_HEIGHT,
            )

        timed_challenge_active = (
            player.map7_quest_accepted
            and player.map7_ghost_intro_seen
            and not player.map7_mission_complete
            and not player.map7_has_book
        )
        if timed_challenge_active:
            if not player.map7_puzzle_timer_started:
                player.map7_puzzle_timer_started = True
                player.map7_puzzle_time_left = PUZZLE_TIME_LIMIT
            else:
                player.map7_puzzle_time_left = max(
                    0.0, player.map7_puzzle_time_left - delta_time
                )
                if player.map7_puzzle_time_left <= 0:
                    reset_timed_puzzle(player)
        elif player.map7_mission_complete:
            player.map7_puzzle_timer_started = False

        if not player.is_dead and player.rect.top > MAP_HEIGHT:
            player.take_damage(player.health)
        if player.death_animation_finished:
            player.respawn(*PLAYER_SPAWN)

        if (
            player.map7_quest_accepted
            and player.map7_mission_complete
            and not player.map7_ghost_reward_seen
            and not player.map7_has_book
            and interaction_window is None
            and ghost_window is None
        ):
            ghost.set_position(
                max(35, min(MAP_WIDTH - 35, player.rect.centerx + 45)),
                min(MAP_HEIGHT - 16, player.rect.bottom),
            )
            ghost_window = GhostWindow("reward")

        ghost_visible = ghost_window is not None
        if ghost_visible:
            ghost.update(delta_time)
        if player.map7_has_book:
            exit_portal.update(delta_time)

        if (
            player.map7_has_book
            and not player.is_dead
            and not player.ui_open
            and interaction_window is None
            and ghost_window is None
            and player.rect.colliderect(exit_portal.rect)
        ):
            next_map = "map6"
            next_arrival_from = "map7"
            running = False

        camera_x = max(
            0,
            min(
                player.rect.centerx - SCREEN_WIDTH / 2,
                MAP_WIDTH - SCREEN_WIDTH,
            ),
        )
        camera_area = pygame.Rect(
            round(camera_x), 0, SCREEN_WIDTH, SCREEN_HEIGHT
        )
        screen.blit(background, (0, 0), camera_area)
        draw_lit_candles(screen, camera_x, interactables, player)
        if player.map7_has_book:
            exit_portal.draw(screen, camera_x)
        if ghost_visible:
            ghost.draw(screen, camera_x)
        nearby = nearest_interactable(player, interactables)
        if nearby is not None and interaction_window is None:
            draw_interaction_prompt(
                screen, camera_x, nearby, prompt_font
            )
        player.draw(screen, camera_x)
        player.draw_health_bar(screen)
        if timed_challenge_active:
            draw_puzzle_timer(screen, player)
        player.draw_active_screen(screen)
        if interaction_window is not None:
            interaction_window.draw(screen)
        if ghost_window is not None:
            ghost_window.draw(screen)
            if ghost_window.kind == "intro":
                ghost.draw(screen, camera_x)
        pygame.display.flip()

    return next_map, player, next_arrival_from
