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
        self.active = False
        self.font = pygame.font.Font(None, 20)
        self.body_font = pygame.font.Font(None, 22)
        self.title_font = pygame.font.Font(None, 30)

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
        player.craft_message = "Welcome! Your health has been restored."
        self.active = True
        self.message_time_left = NPC_MESSAGE_DURATION
        return True

    def handle_event(self, event, player):
        if not self.active or event.type != pygame.KEYDOWN:
            return False

        if event.key in (pygame.K_ESCAPE, pygame.K_e):
            self.active = False
        elif event.key == pygame.K_1:
            player.craft_magic("Fire Magic")
        elif event.key == pygame.K_2:
            player.craft_message = (
                "Wind Magic is unlimited after clearing the Toad Realm."
            )
        elif event.key == pygame.K_3:
            player.craft_shield_upgrade()
        elif event.key == pygame.K_h:
            player.health = player.max_health
            player.craft_message = "Your health is fully restored!"
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

        if self.active:
            return
        if self.message_time_left > 0:
            text_value = "Your health is fully restored!"
            text_color = (120, 255, 160)
        elif self.can_talk(player):
            text_value = "Press E to talk"
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

    def draw_store(self, screen, player):
        if not self.active:
            return
        width, height = screen.get_size()
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

        panel = pygame.Rect(60, 25, width - 120, height - 50)
        pygame.draw.rect(screen, (246, 244, 226), panel, border_radius=9)
        pygame.draw.rect(screen, (35, 48, 78), panel, 4, border_radius=9)

        title = self.title_font.render(
            "Keeper's Healing & Crafting Store", True, (35, 48, 78)
        )
        screen.blit(title, (panel.x + 22, panel.y + 17))

        lines = [
            "H - Restore health (free)",
            "1 - Craft Fire Magic (Level 2, 2 Emberstones)",
            "2 - Wind Magic info (unlimited after Toad Realm)",
            (
                "3 - Improve Shield (+10 health, 1 Emberstone)  "
                f"Cap: {player.shield_health_cap}"
            ),
            (
                f"Level {player.level}/4    HP {player.health}/"
                f"{player.max_health}    Emberstones {player.emberstones}"
            ),
        ]
        y = panel.y + 58
        for line in lines:
            surface = self.body_font.render(line, True, (35, 39, 51))
            screen.blit(surface, (panel.x + 22, y))
            y += 31

        if player.craft_message:
            message = self.font.render(
                player.craft_message, True, (145, 75, 35)
            )
            screen.blit(message, (panel.x + 22, panel.bottom - 48))

        close = self.font.render(
            "E or ESC - Close store", True, (85, 91, 105)
        )
        screen.blit(close, (panel.x + 22, panel.bottom - 25))
