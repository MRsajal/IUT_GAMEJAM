from pathlib import Path

import pygame


POTION_PATH = Path(__file__).parent / "potion.png"
POTION_SIZE = (16, 20)


class HealthPotion:
    _image = None

    def __init__(self, center_x, center_y):
        if HealthPotion._image is None:
            original = pygame.image.load(POTION_PATH).convert_alpha()
            visible_area = original.get_bounding_rect()
            cropped = original.subsurface(visible_area).copy()
            HealthPotion._image = pygame.transform.smoothscale(
                cropped, POTION_SIZE
            )

        self.rect = HealthPotion._image.get_rect(
            center=(center_x, center_y)
        )

    def draw(self, screen, camera_x):
        screen.blit(
            self._image,
            (self.rect.x - round(camera_x), self.rect.y),
        )
