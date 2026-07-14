from pathlib import Path
import random

import pygame

from player import Player
from portal import Portal
from slime import Slime, SlimeDrop
from .platform import platform


SCREEN_WIDTH = 600
SCREEN_HEIGHT = 320
MAP_WIDTH = 960
MAP_HEIGHT = 320
TILE_SIZE = 16
WALKABLE_TILE = 142
PLAYER_SPAWN = (80, 100)
SLIME_SPAWN_INTERVAL = 10.0
SLIME_POINTS = 5
SLIME_DROP_CHANCE = 0.70
INITIAL_SLIME_POSITIONS = (220, 360, 520, 700, 860)

MAP_PATH = Path(__file__).parent / "map2.png"


def load_map():
    """Load map2.png and make sure it has the required dimensions."""
    map_surface = pygame.image.load(MAP_PATH).convert()

    if map_surface.get_size() != (MAP_WIDTH, MAP_HEIGHT):
        map_surface = pygame.transform.scale(
            map_surface, (MAP_WIDTH, MAP_HEIGHT)
        )

    return map_surface


def create_platform_rects():
    """Create collision rectangles for every walkable tile."""
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


def create_slime_drop(slime, ground_y):
    """Return a drop for a defeated slime based on its 70% drop chance."""
    if random.random() < SLIME_DROP_CHANCE:
        return SlimeDrop(center_x=slime.rect.centerx, bottom_y=ground_y)

    return None


def map2(player=None):
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Map 2")
    clock = pygame.time.Clock()

    map_surface = load_map()
    platform_rects = create_platform_rects()
    if player is None:
        player = Player(*PLAYER_SPAWN)
    else:
        player.set_position(*PLAYER_SPAWN)

    # Place the return portal above the leftmost platform.
    left_edge_platforms = [
        rect for rect in platform_rects if rect.left == 0
    ]
    portal_bottom = min(
        (rect.top for rect in left_edge_platforms), default=MAP_HEIGHT
    )
    portal = Portal(center_x=24, bottom_y=portal_bottom)

    ground_y = min(
        (rect.top for rect in platform_rects), default=MAP_HEIGHT
    )
    slimes = [
        Slime(center_x=x, bottom_y=ground_y)
        for x in INITIAL_SLIME_POSITIONS
    ]
    slime_drops = []
    slime_spawn_timer = 0.0

    camera_x = 0.0
    running = True
    next_map = None

    while running:
        delta_time = clock.tick(60) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

            player.handle_event(event)

        player.update(
            delta_time, platform_rects, MAP_WIDTH, slimes
        )
        portal.update(delta_time)

        # Reward defeated enemies and roll for their item drops.
        defeated_slimes = [slime for slime in slimes if not slime.alive]
        for slime in defeated_slimes:
            player.add_points(SLIME_POINTS)
            slime_drop = create_slime_drop(slime, ground_y)
            if slime_drop is not None:
                slime_drops.append(slime_drop)

        slimes = [slime for slime in slimes if slime.alive]

        for slime in slimes:
            slime.update(delta_time, player, MAP_WIDTH)

        slime_spawn_timer += delta_time
        while slime_spawn_timer >= SLIME_SPAWN_INTERVAL:
            slime_spawn_timer -= SLIME_SPAWN_INTERVAL
            random_x = random.randint(100, MAP_WIDTH - 30)
            slimes.append(Slime(center_x=random_x, bottom_y=ground_y))

        collected_drops = [
            slime_drop
            for slime_drop in slime_drops
            if player.rect.colliderect(slime_drop.rect)
        ]
        if collected_drops:
            player.collect_drops(len(collected_drops))
            slime_drops = [
                slime_drop
                for slime_drop in slime_drops
                if slime_drop not in collected_drops
            ]

        if player.health <= 0:
            player.respawn(*PLAYER_SPAWN)
            next_map = "map1"
            running = False
        elif player.rect.colliderect(portal.rect):
            next_map = "map1"
            running = False

        # Follow the player while keeping the camera inside the map.
        camera_x = player.rect.centerx - SCREEN_WIDTH / 2
        camera_x = max(0, min(camera_x, MAP_WIDTH - SCREEN_WIDTH))

        # Draw only the 600x320 camera section of the 960x320 map.
        camera_area = pygame.Rect(
            round(camera_x), 0, SCREEN_WIDTH, SCREEN_HEIGHT
        )
        screen.blit(map_surface, (0, 0), camera_area)
        portal.draw(screen, camera_x)
        for slime_drop in slime_drops:
            slime_drop.draw(screen, camera_x)
        for slime in slimes:
            slime.draw(screen, camera_x)
        player.draw(screen, camera_x)
        player.draw_health_bar(screen)

        pygame.display.flip()

    return next_map, player
