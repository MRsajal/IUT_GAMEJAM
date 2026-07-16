from pathlib import Path
import random

import pygame


NPC_FRAME_COUNT = 5
NPC_ANIMATION_SPEED = 7
NPC_INTERACTION_RANGE = 65
NPC_WARNING_DURATION = 2.5
NPC_PATH = Path(__file__).parent
REQUEST_AMOUNTS = (1, 2, 3)
SPELL_PRICES = {
    "Fire Magic": 20,
    "Fly Magic": 40,
}


class MissionNPC:
    """Offers a Map 3 restart and buys level-appropriate spells."""

    _frames = None

    def __init__(self, center_x, bottom_y):
        self._load_frames()
        self.rect = pygame.Rect(0, 0, 24, 42)
        self.rect.midbottom = (center_x, bottom_y)
        self.animation_time = 0.0
        self.active = False
        self.request_magic = None
        self.request_amount = 0
        self.message = ""
        self.previous_amount = None
        self.warning = ""
        self.warning_time_left = 0.0
        self.font = pygame.font.Font(None, 20)
        self.body_font = pygame.font.Font(None, 23)
        self.title_font = pygame.font.Font(None, 31)

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

    def open(self, player):
        """Open a fresh offer; the requested amount changes each time."""
        self.active = True
        self.message = ""

        if player.level < 2:
            self.request_magic = None
            self.request_amount = 0
            return

        unlocked_magic = ["Fire Magic"]
        if player.level >= 3:
            unlocked_magic.append("Fly Magic")
        self.request_magic = random.choice(unlocked_magic)

        available_amounts = [
            amount
            for amount in REQUEST_AMOUNTS
            if amount != self.previous_amount
        ]
        self.request_amount = random.choice(available_amounts)
        self.previous_amount = self.request_amount

    @property
    def price_per_spell(self):
        return SPELL_PRICES.get(self.request_magic, 0)

    @property
    def reward(self):
        return self.request_amount * self.price_per_spell

    def handle_event(self, event, player):
        """Return (consumed, action), where action may restart the mission."""
        if not self.active or event.type != pygame.KEYDOWN:
            return False, None

        if event.key in (pygame.K_ESCAPE, pygame.K_e):
            self.active = False
            return True, None

        if event.key == pygame.K_r:
            self.active = False
            return True, "restart"

        if event.key == pygame.K_s:
            if self.request_magic is None:
                self.message = "Reach level 2 before selling magic."
                return True, None

            sold = player.sell_magic(
                self.request_magic,
                self.request_amount,
                self.price_per_spell,
            )
            if sold:
                self.active = False
                return True, "sold"

            owned = player.held_magic.count(self.request_magic)
            self.message = (
                f"You only have {owned}/{self.request_amount} requested."
            )
            return True, None

        return True, None

    def update(self, delta_time):
        self.animation_time += delta_time
        self.warning_time_left = max(
            0.0, self.warning_time_left - delta_time
        )

    def warn_about_flight(self, player):
        if player.magic_uses.get("Fly Magic", 0) > 0:
            self.warning = "Activate Fly Magic with G before leaving!"
        else:
            self.warning = "Map 4 is bottomless! Craft Fly Magic first!"
        self.warning_time_left = NPC_WARNING_DURATION

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

        if self.can_talk(player) and not self.active:
            prompt = self.font.render(
                "Press E to talk", True, (255, 245, 170)
            )
            prompt_rect = prompt.get_rect(
                midbottom=(screen_x, draw_rect.top - 4)
            )
            pygame.draw.rect(
                screen,
                (25, 28, 40),
                prompt_rect.inflate(10, 6),
                border_radius=5,
            )
            screen.blit(prompt, prompt_rect)

        if self.warning_time_left > 0 and not self.active:
            warning = self.font.render(
                self.warning, True, (255, 180, 105)
            )
            warning_rect = warning.get_rect(
                midbottom=(screen_x, draw_rect.top - 4)
            )
            pygame.draw.rect(
                screen,
                (35, 25, 35),
                warning_rect.inflate(12, 7),
                border_radius=5,
            )
            screen.blit(warning, warning_rect)

        if self.active:
            self._draw_panel(screen, player)

    def _draw_panel(self, screen, player):
        width, height = screen.get_size()
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 175))
        screen.blit(overlay, (0, 0))

        panel = pygame.Rect(70, 42, width - 140, height - 84)
        pygame.draw.rect(screen, (31, 37, 47), panel, border_radius=10)
        pygame.draw.rect(
            screen, (125, 210, 150), panel, 2, border_radius=10
        )

        title = self.title_font.render(
            "Toad Mission Keeper", True, (165, 240, 185)
        )
        screen.blit(title, (panel.x + 22, panel.y + 16))

        restart = self.body_font.render(
            "R - Restart all toad missions", True, (235, 235, 240)
        )
        screen.blit(restart, (panel.x + 22, panel.y + 57))

        if self.request_magic is None:
            offer_text = "Reach level 2 to receive a magic order."
            offer_color = (175, 180, 190)
        else:
            offer_text = (
                f"Wanted: {self.request_amount} x {self.request_magic}  "
                f"Reward: {self.reward} money"
            )
            offer_color = (255, 205, 115)
        offer = self.font.render(offer_text, True, offer_color)
        screen.blit(offer, (panel.x + 22, panel.y + 94))

        sell = self.body_font.render(
            "S - Sell requested magic", True, (235, 235, 240)
        )
        screen.blit(sell, (panel.x + 22, panel.y + 121))

        flight_tip = self.font.render(
            "Map 4 warning: craft Fly Magic, then press G here.",
            True,
            (135, 220, 255),
        )
        screen.blit(flight_tip, (panel.x + 22, panel.y + 180))

        if self.message:
            message = self.font.render(
                self.message, True, (255, 145, 120)
            )
            screen.blit(message, (panel.x + 22, panel.y + 151))

        close = self.font.render(
            "E or ESC - Close", True, (170, 180, 195)
        )
        screen.blit(close, (panel.x + 22, panel.bottom - 27))
