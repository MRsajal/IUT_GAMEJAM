from pathlib import Path

import pygame


SLIME_FRAME_COUNT = 7
SLIME_ANIMATION_SPEED = 8
SLIME_SPEED = 55
SLIME_MAX_HEALTH = 20
SLIME_CONTACT_DAMAGE = 10
SLIME_DAMAGE_COOLDOWN = 1.0
SLIME_PATH = Path(__file__).parent


class Slime:
    _right_frames = None
    _left_frames = None

    def __init__(self, center_x, bottom_y):
        self._load_frames()

        self.rect = pygame.Rect(0, 0, 18, 18)
        self.rect.midbottom = (center_x, bottom_y)
        self.position_x = float(self.rect.x)

        self.health = SLIME_MAX_HEALTH
        self.max_health = SLIME_MAX_HEALTH
        self.facing_right = True
        self.animation_time = 0.0
        self.damage_cooldown_left = 0.0

    @classmethod
    def _load_frames(cls):
        if cls._right_frames is not None:
            return

        cls._right_frames = []
        for frame_number in range(SLIME_FRAME_COUNT):
            path = SLIME_PATH / f"{frame_number}.png"
            cls._right_frames.append(
                pygame.image.load(path).convert_alpha()
            )

        cls._left_frames = [
            pygame.transform.flip(frame, True, False)
            for frame in cls._right_frames
        ]

    @property
    def alive(self):
        return self.health > 0

    def take_damage(self, amount):
        self.health = max(0, self.health - max(0, amount))

    def update(self, delta_time, player, map_width):
        if not self.alive:
            return

        if player.rect.centerx < self.rect.centerx:
            direction = -1
            self.facing_right = False
        elif player.rect.centerx > self.rect.centerx:
            direction = 1
            self.facing_right = True
        else:
            direction = 0

        self.position_x += direction * SLIME_SPEED * delta_time
        self.position_x = max(
            0, min(self.position_x, map_width - self.rect.width)
        )
        self.rect.x = round(self.position_x)

        self.damage_cooldown_left = max(
            0, self.damage_cooldown_left - delta_time
        )
        if (
            self.rect.colliderect(player.rect)
            and self.damage_cooldown_left <= 0
        ):
            player.take_damage(SLIME_CONTACT_DAMAGE)
            self.damage_cooldown_left = SLIME_DAMAGE_COOLDOWN

        self.animation_time += delta_time

    def draw(self, screen, camera_x):
        frames = (
            self._right_frames if self.facing_right else self._left_frames
        )
        frame_index = int(
            self.animation_time * SLIME_ANIMATION_SPEED
        ) % len(frames)
        image = frames[frame_index]
        draw_rect = image.get_rect(
            midbottom=(self.rect.centerx - round(camera_x), self.rect.bottom)
        )
        screen.blit(image, draw_rect)
