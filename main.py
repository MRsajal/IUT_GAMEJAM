from map1.map1 import map1
from map2.map2 import map2


def main():
    maps = {
        "map1": map1,
        "map2": map2,
    }
    current_map = "map1"

    while current_map in maps:
        current_map = maps[current_map]()


if __name__ == "__main__":
    main()
