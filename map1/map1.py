from pathlib import Path

import pygame

from npc1 import HealingNPC
from player import Player
from portal import Portal
from .platform import platform


SCREEN_WIDTH = 600
SCREEN_HEIGHT = 320
MAP_WIDTH = 960
MAP_HEIGHT = 320
TILE_SIZE = 16
WALKABLE_TILE = 142
PLAYER_SPAWN = (80, 180)
MAP2_RETURN_SPAWN = (MAP_WIDTH - 80, 180)
NPC_CENTER_X = 480

MAP_PATH = Path(__file__).parent / "map.png"


def load_map():
    """Load map.png and make sure it has the required dimensions."""
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


def map1(player=None, arrived_from=None):
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Map 1")
    clock = pygame.time.Clock()

    map_surface = load_map()
    platform_rects = create_platform_rects()
    entry_spawn = (
        MAP2_RETURN_SPAWN if arrived_from == "map2" else PLAYER_SPAWN
    )
    if player is None:
        player = Player(*entry_spawn)
    else:
        player.set_position(*entry_spawn)

    # Decorative portal showing where the player enters Map 1.
    spawn_ground = min(
        (
            rect.top
            for rect in platform_rects
            if rect.left <= PLAYER_SPAWN[0] + 12 < rect.right
        ),
        default=MAP_HEIGHT,
    )
    spawn_portal = Portal(
        center_x=PLAYER_SPAWN[0] + 12,
        bottom_y=spawn_ground,
    )

    # Place the Map 2 portal at the end of Map 1.
    right_edge_platforms = [
        rect for rect in platform_rects if rect.right == MAP_WIDTH
    ]
    portal_bottom = min(
        (rect.top for rect in right_edge_platforms), default=MAP_HEIGHT
    )
    exit_portal = Portal(center_x=MAP_WIDTH - 24, bottom_y=portal_bottom)

    npc_ground = min(
        (
            rect.top
            for rect in platform_rects
            if rect.left <= NPC_CENTER_X < rect.right
        ),
        default=MAP_HEIGHT,
    )
    healing_npc = HealingNPC(NPC_CENTER_X, npc_ground)

    # Add future enemies here. Each needs a rect and take_damage(amount).
    damage_targets = []
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
                event_consumed = False
                if (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_e
                    and not player.ui_open
                ):
                    event_consumed = healing_npc.talk(player)

                if not event_consumed:
                    event_consumed = player.handle_event(event)
                if (
                    not event_consumed
                    and event.type == pygame.KEYDOWN
                    and event.key == pygame.K_ESCAPE
                ):
                    running = False

        if not player.ui_open:
            player.update(
                delta_time, platform_rects, MAP_WIDTH, damage_targets
            )
        spawn_portal.update(delta_time)
        exit_portal.update(delta_time)
        healing_npc.update(delta_time)

        if player.death_animation_finished:
            player.respawn(*PLAYER_SPAWN)
            next_map = "map1"
            next_arrival_from = None
            running = False
        elif (
            not player.is_dead
            and not player.ui_open
            and player.rect.colliderect(exit_portal.rect)
        ):
            next_map = "map2"
            next_arrival_from = "map1"
            running = False

        # Follow the player while keeping the camera inside the map.
        camera_x = player.rect.centerx - SCREEN_WIDTH / 2
        camera_x = max(0, min(camera_x, MAP_WIDTH - SCREEN_WIDTH))

        # Draw only the 600x320 camera section of the 960x320 map.
        camera_area = pygame.Rect(
            round(camera_x), 0, SCREEN_WIDTH, SCREEN_HEIGHT
        )
        screen.blit(map_surface, (0, 0), camera_area)
        spawn_portal.draw(screen, camera_x)
        exit_portal.draw(screen, camera_x)
        healing_npc.draw(screen, camera_x, player)
        player.draw(screen, camera_x)
        player.draw_health_bar(screen)
        player.draw_active_screen(screen)

        pygame.display.flip()

    return next_map, player, next_arrival_from
