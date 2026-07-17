from pathlib import Path
import csv

import pygame

from player import Player
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
            if interaction_window is not None:
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
                next_map = "map1"
                next_arrival_from = "map7"
                running = False

        if not player.ui_open and interaction_window is None:
            player.update(
                delta_time,
                platform_rects,
                MAP_WIDTH,
                map_height=MAP_HEIGHT,
            )

        if not player.is_dead and player.rect.top > MAP_HEIGHT:
            player.take_damage(player.health)
        if player.death_animation_finished:
            player.respawn(*PLAYER_SPAWN)

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
        nearby = nearest_interactable(player, interactables)
        if nearby is not None and interaction_window is None:
            draw_interaction_prompt(
                screen, camera_x, nearby, prompt_font
            )
        player.draw(screen, camera_x)
        player.draw_health_bar(screen)
        player.draw_active_screen(screen)
        if interaction_window is not None:
            interaction_window.draw(screen)
        pygame.display.flip()

    return next_map, player, next_arrival_from
