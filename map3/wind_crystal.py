from pathlib import Path

import pygame


WIND_CRYSTAL_PATH = Path(__file__).parent / "mat_windcrystal.png"
WIND_CRYSTAL_SIZE = (18, 18)


class WindCrystal:
    _image = None

    def __init__(self, center_x, bottom_y):
        if WindCrystal._image is None:
            original = pygame.image.load(WIND_CRYSTAL_PATH).convert_alpha()
            WindCrystal._image = pygame.transform.smoothscale(
                original, WIND_CRYSTAL_SIZE
            )

        self.rect = WindCrystal._image.get_rect(
            midbottom=(center_x, bottom_y)
        )

    def draw(self, screen, camera_x):
        screen.blit(
            self._image,
            (self.rect.x - round(camera_x), self.rect.y),
        )
