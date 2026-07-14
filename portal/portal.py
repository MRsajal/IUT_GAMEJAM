from pathlib import Path

import pygame


PORTAL_FRAME_COUNT = 8
PORTAL_ANIMATION_SPEED = 10
PORTAL_PATH = Path(__file__).parent


class Portal:
    def __init__(self, center_x, bottom_y):
        self.frames = self._load_frames()
        self.animation_time = 0.0

        width = max(frame.get_width() for frame in self.frames)
        height = max(frame.get_height() for frame in self.frames)
        self.rect = pygame.Rect(0, 0, width, height)
        self.rect.midbottom = (center_x, bottom_y)

    def _load_frames(self):
        frames = []

        for frame_number in range(PORTAL_FRAME_COUNT):
            path = PORTAL_PATH / f"{frame_number}.png"
            frames.append(pygame.image.load(path).convert_alpha())

        return frames

    def update(self, delta_time):
        self.animation_time += delta_time

    def draw(self, screen, camera_x):
        frame_index = int(
            self.animation_time * PORTAL_ANIMATION_SPEED
        ) % len(self.frames)
        image = self.frames[frame_index]
        draw_rect = image.get_rect(
            midbottom=(
                self.rect.centerx - round(camera_x),
                self.rect.bottom,
            )
        )
        screen.blit(image, draw_rect)
