from pathlib import Path

import pygame


NPC_PATH = Path(__file__).parent
NPC_FRAME_COUNT = 5
NPC_ANIMATION_SPEED = 7
NPC_INTERACTION_RANGE = 70


class QuestWindow:
    def __init__(self, player):
        self.player = player
        self.closed = False
        self.title_font = pygame.font.Font(None, 31)
        self.body_font = pygame.font.Font(None, 22)
        self.small_font = pygame.font.Font(None, 18)

        if player.map7_has_book:
            self.mode = "handover"
            self.text = (
                "You found my wife's Book of Arcana. Its final lesson "
                "masters Fire and Fly Magic forever, without crystals. "
                "Hand it to me, and I will teach you now."
            )
        elif player.map7_book_delivered:
            self.mode = "thanks"
            self.text = (
                "I will guard her book for the rest of my days. "
                "You have given an old man peace."
            )
        elif player.map7_quest_accepted:
            self.mode = "reminder"
            self.text = (
                "The haunted manor still holds my late wife's hidden book. "
                "Will you return and continue the search?"
            )
        else:
            self.mode = "request"
            self.text = (
                "My late wife hid the Book of Arcana inside an abandoned "
                "manor. Please help me find it and bring it home."
            )

    def handle_event(self, event):
        if self.closed or event.type != pygame.KEYDOWN:
            return False, None
        if event.key == pygame.K_ESCAPE:
            self.closed = True
            return True, None

        if self.mode == "request":
            if event.key in (
                pygame.K_e,
                pygame.K_y,
                pygame.K_RETURN,
                pygame.K_KP_ENTER,
            ):
                self.player.map7_quest_accepted = True
                self.closed = True
                return True, "travel_map7"
            if event.key == pygame.K_n:
                self.closed = True
                return True, None
            return True, None

        if self.mode == "reminder" and event.key in (
            pygame.K_e,
            pygame.K_RETURN,
            pygame.K_KP_ENTER,
        ):
            self.closed = True
            return True, "travel_map7"

        if self.mode == "handover" and event.key in (
            pygame.K_e,
            pygame.K_RETURN,
            pygame.K_KP_ENTER,
        ):
            self.player.map7_has_book = False
            self.player.map7_book_delivered = True
            self.player.arcana_magic_mastered = True
            self.closed = True
            return True, "book_delivered"

        if self.mode == "thanks" and event.key in (
            pygame.K_e,
            pygame.K_RETURN,
            pygame.K_KP_ENTER,
        ):
            self.closed = True
            return True, None
        return True, None

    def _wrap(self, maximum_width):
        rows = []
        current = ""
        for word in self.text.split():
            candidate = f"{current} {word}".strip()
            if current and self.body_font.size(candidate)[0] > maximum_width:
                rows.append(current)
                current = word
            else:
                current = candidate
        if current:
            rows.append(current)
        return rows

    def draw(self, screen):
        width, height = screen.get_size()
        shade = pygame.Surface((width, height), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 175))
        screen.blit(shade, (0, 0))
        panel = pygame.Rect(65, 55, width - 130, height - 110)
        pygame.draw.rect(screen, (42, 37, 42), panel, border_radius=9)
        pygame.draw.rect(screen, (210, 178, 115), panel, 3, border_radius=9)

        title = self.title_font.render(
            "The Grieving Husband", True, (245, 215, 155)
        )
        screen.blit(title, title.get_rect(midtop=(panel.centerx, panel.y + 15)))
        y = panel.y + 58
        for row in self._wrap(panel.width - 50):
            text = self.body_font.render(row, True, (235, 230, 220))
            screen.blit(text, (panel.x + 25, y))
            y += 23

        if self.mode == "request":
            hint_value = "ENTER / Y: Accept    N / ESC: Not now"
        elif self.mode == "reminder":
            hint_value = "ENTER: Return to the manor    ESC: Close"
        elif self.mode == "handover":
            hint_value = "ENTER: Hand over the Book of Arcana"
        else:
            hint_value = "ENTER / ESC: Close"
        hint = self.small_font.render(
            hint_value, True, (190, 190, 200)
        )
        screen.blit(
            hint,
            hint.get_rect(midbottom=(panel.centerx, panel.bottom - 16)),
        )


class QuestNPC:
    _frames = None

    def __init__(self, center_x, bottom_y):
        self._load_frames()
        self.rect = pygame.Rect(0, 0, 24, 42)
        self.rect.midbottom = (center_x, bottom_y)
        self.animation_time = 0.0
        self.window = None
        self.font = pygame.font.Font(None, 18)

    @classmethod
    def _load_frames(cls):
        if cls._frames is not None:
            return
        cls._frames = [
            pygame.image.load(NPC_PATH / f"{number}.png").convert_alpha()
            for number in range(NPC_FRAME_COUNT)
        ]

    @property
    def active(self):
        return self.window is not None

    def is_near(self, player):
        return self.rect.inflate(
            NPC_INTERACTION_RANGE * 2,
            NPC_INTERACTION_RANGE * 2,
        ).colliderect(player.rect)

    def open(self, player):
        self.window = QuestWindow(player)

    def handle_event(self, event):
        if self.window is None:
            return False, None
        consumed, action = self.window.handle_event(event)
        if self.window.closed:
            self.window = None
        return consumed, action

    def update(self, delta_time):
        self.animation_time += delta_time

    def draw(self, screen, camera_x, player):
        frame_index = int(
            self.animation_time * NPC_ANIMATION_SPEED
        ) % len(self._frames)
        image = self._frames[frame_index]
        screen_x = self.rect.centerx - round(camera_x)
        draw_rect = image.get_rect(midbottom=(screen_x, self.rect.bottom))
        screen.blit(image, draw_rect)

        if self.is_near(player) and self.window is None:
            prompt = self.font.render(
                "E: Talk", True, (255, 235, 165)
            )
            prompt_rect = prompt.get_rect(
                midbottom=(screen_x, draw_rect.top - 4)
            )
            pygame.draw.rect(
                screen,
                (24, 21, 29),
                prompt_rect.inflate(10, 6),
                border_radius=5,
            )
            screen.blit(prompt, prompt_rect)

    def draw_window(self, screen):
        if self.window is not None:
            self.window.draw(screen)
