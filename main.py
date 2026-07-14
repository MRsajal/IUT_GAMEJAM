import pygame

from map1.map1 import map1
from map2.map2 import map2


def main():
    pygame.init()

    maps = {
        "map1": map1,
        "map2": map2,
    }
    current_map = "map1"
    player = None

    while current_map in maps:
        current_map, player = maps[current_map](player)

    pygame.quit()


if __name__ == "__main__":
    main()
