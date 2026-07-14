from pathlib import Path

import pygame


DROP_PATH = Path(__file__).parent / "drop.png"
DROP_SIZE = (18, 18)


class SlimeDrop:
    _image = None

    def __init__(self, center_x, bottom_y):
        if SlimeDrop._image is None:
            original_image = pygame.image.load(DROP_PATH).convert_alpha()
            SlimeDrop._image = pygame.transform.smoothscale(
                original_image, DROP_SIZE
            )

        self.rect = SlimeDrop._image.get_rect(
            midbottom=(center_x, bottom_y)
        )

    def draw(self, screen, camera_x):
        screen.blit(
            self._image,
            (self.rect.x - round(camera_x), self.rect.y),
        )
