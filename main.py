import pygame

from map1.map1 import map1
from map2.map2 import map2
from map3.map3 import map3
from opening_video import SLIME_VIDEO_PATH, play_opening_video, play_video


def main():
    pygame.init()

    if not play_opening_video():
        pygame.quit()
        return

    maps = {
        "map1": map1,
        "map2": map2,
        "map3": map3,
    }
    current_map = "map1"
    player = None
    arrived_from = None

    while current_map in maps:
        next_map, player, arrived_from = maps[current_map](
            player, arrived_from
        )
        if (
            next_map == "map2"
            and player is not None
            and not player.slime_video_seen
        ):
            if not play_video(SLIME_VIDEO_PATH):
                break
            player.slime_video_seen = True
        current_map = next_map

    pygame.quit()


if __name__ == "__main__":
    main()
