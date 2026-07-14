from pathlib import Path

import pygame

from player import Player
from portal import Portal
from .platform import platform


SCREEN_WIDTH = 600
SCREEN_HEIGHT = 320
MAP_WIDTH = 960
MAP_HEIGHT = 320
TILE_SIZE = 16
WALKABLE_TILE = 142

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


def map2():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Map 2")
    clock = pygame.time.Clock()

    map_surface = load_map()
    platform_rects = create_platform_rects()
    player = Player(x=80, y=100)

    # Place the return portal above the leftmost platform.
    left_edge_platforms = [
        rect for rect in platform_rects if rect.left == 0
    ]
    portal_bottom = min(
        (rect.top for rect in left_edge_platforms), default=MAP_HEIGHT
    )
    portal = Portal(center_x=24, bottom_y=portal_bottom)

    # Add future enemies here. Each needs a rect and take_damage(amount).
    damage_targets = []
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
            delta_time, platform_rects, MAP_WIDTH, damage_targets
        )
        portal.update(delta_time)

        if player.rect.colliderect(portal.rect):
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
        player.draw(screen, camera_x)
        player.draw_health_bar(screen)

        pygame.display.flip()

    pygame.quit()
    return next_map
