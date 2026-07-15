from pathlib import Path
import random

import pygame

from player import Player
from portal import Portal
from toads import Toad
from .object import object as object_layer
from .platform import platform
from .wind_crystal import WindCrystal


SCREEN_WIDTH = 600
SCREEN_HEIGHT = 320
MAP_WIDTH = 1120
MAP_HEIGHT = 320
TILE_SIZE = 16
WALKABLE_TILE = 142
TOAD_ZONE_MARKER = 113
PLAYER_SPAWN = (80, 100)
WIND_CRYSTAL_DROP_CHANCE = 0.70
BOSS_ZONE_WIDTH = 288

MAP_PATH = Path(__file__).parent / "map3.png"


def load_map():
    """Load map3.png and make sure it has the required dimensions."""
    map_surface = pygame.image.load(MAP_PATH).convert()

    if map_surface.get_size() != (MAP_WIDTH, MAP_HEIGHT):
        map_surface = pygame.transform.scale(
            map_surface, (MAP_WIDTH, MAP_HEIGHT)
        )

    return map_surface


def create_platform_rects():
    platform_rects = []

    for row_number, row in enumerate(platform):
        for column_number, tile_value in enumerate(row):
            if tile_value == WALKABLE_TILE:
                platform_rects.append(
                    pygame.Rect(
                        column_number * TILE_SIZE,
                        row_number * TILE_SIZE,
                        TILE_SIZE,
                        TILE_SIZE,
                    )
                )

    return platform_rects


def create_object_rects():
    """Create solid collision rectangles for every 113 object tile."""
    object_rects = []

    for row_number, row in enumerate(object_layer):
        for column_number, tile_value in enumerate(row):
            if tile_value == TOAD_ZONE_MARKER:
                object_rects.append(
                    pygame.Rect(
                        column_number * TILE_SIZE,
                        row_number * TILE_SIZE,
                        TILE_SIZE,
                        TILE_SIZE,
                    )
                )

    return object_rects


def create_toad_zones(platform_rects):
    """Create a zone between every two adjacent 113 markers."""
    zones = []

    for row_number, row in enumerate(object_layer):
        marker_columns = [
            column_number
            for column_number, value in enumerate(row)
            if value == TOAD_ZONE_MARKER
        ]

        for marker_index in range(len(marker_columns) - 1):
            first_column = marker_columns[marker_index]
            second_column = marker_columns[marker_index + 1]
            zone_left = first_column * TILE_SIZE
            zone_right = (second_column + 1) * TILE_SIZE
            zone_center = (zone_left + zone_right) // 2
            marker_y = row_number * TILE_SIZE

            ground_candidates = [
                rect.top
                for rect in platform_rects
                if rect.left <= zone_center < rect.right
                and rect.top >= marker_y
            ]
            ground_y = min(ground_candidates, default=MAP_HEIGHT)
            zones.append((zone_left, zone_right, ground_y))

    return zones


def create_boss_toad(platform_rects):
    marker_columns = [
        column_number
        for row in object_layer
        for column_number, value in enumerate(row)
        if value == TOAD_ZONE_MARKER
    ]
    last_marker_right = (max(marker_columns) + 1) * TILE_SIZE
    zone_right = min(MAP_WIDTH, last_marker_right + BOSS_ZONE_WIDTH)
    zone_center = (last_marker_right + zone_right) // 2
    ground_y = min(
        (
            rect.top
            for rect in platform_rects
            if rect.left <= zone_center < rect.right
        ),
        default=MAP_HEIGHT,
    )
    return Toad(last_marker_right, zone_right, ground_y, is_boss=True)


def create_wind_crystal(toad):
    if random.random() < WIND_CRYSTAL_DROP_CHANCE:
        return WindCrystal(toad.rect.centerx, toad.rect.bottom)

    return None


def map3(player=None, arrived_from=None):
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Map 3")
    clock = pygame.time.Clock()

    map_surface = load_map()
    platform_rects = create_platform_rects()
    object_rects = create_object_rects()
    if player is None:
        player = Player(*PLAYER_SPAWN)
    else:
        player.set_position(*PLAYER_SPAWN)

    left_edge_platforms = [
        rect for rect in platform_rects if rect.left == 0
    ]
    portal_bottom = min(
        (rect.top for rect in left_edge_platforms), default=MAP_HEIGHT
    )
    return_portal = Portal(center_x=24, bottom_y=portal_bottom)

    toads = [
        Toad(zone_left, zone_right, ground_y)
        for zone_left, zone_right, ground_y in create_toad_zones(
            platform_rects
        )
    ]
    toads.append(create_boss_toad(platform_rects))
    wind_crystals_on_ground = []

    camera_x = 0.0
    running = True
    next_map = None
    next_arrival_from = None

    while running:
        delta_time = clock.tick(60) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                event_consumed = player.handle_event(event)
                if (
                    not event_consumed
                    and event.type == pygame.KEYDOWN
                    and event.key == pygame.K_ESCAPE
                ):
                    running = False

        if not player.ui_open:
            player.update(
                delta_time,
                platform_rects,
                MAP_WIDTH,
                toads,
                object_rects,
            )
        return_portal.update(delta_time)

        defeated_toads = [toad for toad in toads if not toad.alive]
        for toad in defeated_toads:
            wind_crystal = create_wind_crystal(toad)
            if wind_crystal is not None:
                wind_crystals_on_ground.append(wind_crystal)
        toads = [toad for toad in toads if toad.alive]
        if not player.ui_open and not player.is_dead:
            for toad in toads:
                toad.update(delta_time, player)

        collected_crystals = [
            crystal
            for crystal in wind_crystals_on_ground
            if player.rect.colliderect(crystal.rect)
        ]
        if collected_crystals:
            player.collect_wind_crystals(len(collected_crystals))
            wind_crystals_on_ground = [
                crystal
                for crystal in wind_crystals_on_ground
                if crystal not in collected_crystals
            ]

        if player.death_animation_finished:
            player.respawn(*PLAYER_SPAWN)
            next_map = "map1"
            next_arrival_from = None
            running = False
        elif (
            not player.is_dead
            and not player.ui_open
            and player.rect.colliderect(return_portal.rect)
        ):
            next_map = "map2"
            next_arrival_from = "map3"
            running = False

        camera_x = player.rect.centerx - SCREEN_WIDTH / 2
        camera_x = max(0, min(camera_x, MAP_WIDTH - SCREEN_WIDTH))

        camera_area = pygame.Rect(
            round(camera_x), 0, SCREEN_WIDTH, SCREEN_HEIGHT
        )
        screen.blit(map_surface, (0, 0), camera_area)
        return_portal.draw(screen, camera_x)
        for crystal in wind_crystals_on_ground:
            crystal.draw(screen, camera_x)
        for toad in toads:
            toad.draw(screen, camera_x)
        player.draw(screen, camera_x)
        player.draw_health_bar(screen)
        player.draw_active_screen(screen)

        pygame.display.flip()

    return next_map, player, next_arrival_from
