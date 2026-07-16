from pathlib import Path

import pygame


STONE_PATH = Path(__file__).parent / "stone.png"
STONE_SIZE = (18, 17)
STONE_FALL_SPEED = 170
STONE_DAMAGE = 15


class FallingStone:
    _image = None

    def __init__(self, center_x):
        if FallingStone._image is None:
            original = pygame.image.load(STONE_PATH).convert_alpha()
            FallingStone._image = pygame.transform.smoothscale(
                original, STONE_SIZE
            )

        self.rect = FallingStone._image.get_rect(
            midtop=(center_x, -STONE_SIZE[1])
        )
        self.position_y = float(self.rect.y)

    def update(self, delta_time):
        self.position_y += STONE_FALL_SPEED * delta_time
        self.rect.y = round(self.position_y)

    def has_left_map(self, map_height):
        return self.rect.top > map_height

    def draw(self, screen, camera_x):
        screen.blit(
            self._image,
            (self.rect.x - round(camera_x), self.rect.y),
        )
