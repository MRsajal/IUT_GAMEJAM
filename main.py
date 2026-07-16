import pygame

from map1.map1 import map1
from map2.map2 import map2
from map3.map3 import map3
from map4.map4 import map4


def main():
    pygame.init()

    maps = {
        "map1": map1,
        "map2": map2,
        "map3": map3,
        "map4": map4,
    }
    current_map = "map1"
    player = None
    arrived_from = None

    while current_map in maps:
        current_map, player, arrived_from = maps[current_map](
            player, arrived_from
        )

    pygame.quit()


if __name__ == "__main__":
    main()
