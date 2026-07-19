from pathlib import Path

import pygame


NPC_FRAME_COUNT = 13
NPC_ANIMATION_SPEED = 8
NPC_INTERACTION_RANGE = 60
NPC_MESSAGE_DURATION = 2.5
NPC_PATH = Path(__file__).parent


class HealingNPC:
    _frames = None

    def __init__(self, center_x, bottom_y):
        self._load_frames()
        self.rect = pygame.Rect(0, 0, 34, 50)
        self.rect.midbottom = (center_x, bottom_y)
        self.animation_time = 0.0
        self.message_time_left = 0.0
        self.font = pygame.font.Font(None, 20)

    @classmethod
    def _load_frames(cls):
        if cls._frames is not None:
            return

        cls._frames = []
        for frame_number in range(NPC_FRAME_COUNT):
            path = NPC_PATH / f"{frame_number}.png"
            cls._frames.append(pygame.image.load(path).convert_alpha())

    def can_talk(self, player):
        horizontal_distance = abs(player.rect.centerx - self.rect.centerx)
        vertical_distance = abs(player.rect.centery - self.rect.centery)
        return (
            not player.is_dead
            and horizontal_distance <= NPC_INTERACTION_RANGE
            and vertical_distance <= NPC_INTERACTION_RANGE
        )

    @property
    def portrait(self):
        """Return a representative frame for dialogue interfaces."""
        return self._frames[0]

    def talk(self, player):
        if not self.can_talk(player):
            return False

        player.health = player.max_health
        self.message_time_left = NPC_MESSAGE_DURATION
        return True

    def update(self, delta_time):
        self.animation_time += delta_time
        self.message_time_left = max(
            0, self.message_time_left - delta_time
        )

    def draw(self, screen, camera_x, player):
        frame_index = int(
            self.animation_time * NPC_ANIMATION_SPEED
        ) % len(self._frames)
        image = self._frames[frame_index]
        screen_x = self.rect.centerx - round(camera_x)
        draw_rect = image.get_rect(
            midbottom=(screen_x, self.rect.bottom)
        )
        screen.blit(image, draw_rect)

        if self.message_time_left > 0:
            text_value = "Your health is fully restored!"
            text_color = (120, 255, 160)
        elif self.can_talk(player):
            text_value = "Press E to heal"
            text_color = (255, 245, 170)
        else:
            return

        text = self.font.render(text_value, True, text_color)
        text_rect = text.get_rect(
            midbottom=(screen_x, draw_rect.top - 4)
        )
        background = text_rect.inflate(10, 6)
        pygame.draw.rect(
            screen, (25, 28, 40), background, border_radius=5
        )
        screen.blit(text, text_rect)
