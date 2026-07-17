from pathlib import Path

import pygame


GHOST_PATH = Path(__file__).parent
BOOK_PATH = GHOST_PATH.parent / "map7" / "book.jpg"
GHOST_FRAME_COUNT = 6
GHOST_ANIMATION_SPEED = 7

INTRO_PAGES = (
    (
        "Solve the manor's puzzles within 1 minute 30 seconds. Succeed, "
        "and you will be rewarded."
    ),
)
REWARD_PAGES = (
    (
        "You understood the memories I left behind. The manor has accepted "
        "you, and the Book of Arcana is yours to carry."
    ),
    (
        "Please return it to my husband. Tell him that I never forgot the "
        "life we shared."
    ),
)


class GhostWindow:
    _book_image = None

    def __init__(self, kind):
        self.kind = kind
        self.pages = INTRO_PAGES if kind == "intro" else REWARD_PAGES
        self.page_index = 0
        self.closed = False
        self.title_font = pygame.font.Font(None, 31)
        self.body_font = pygame.font.Font(None, 22)
        self.small_font = pygame.font.Font(None, 18)
        if kind == "reward" and self._book_image is None:
            image = pygame.image.load(BOOK_PATH).convert()
            self.__class__._book_image = pygame.transform.smoothscale(
                image, (72, 96)
            )

    def handle_event(self, event):
        if self.closed or event.type != pygame.KEYDOWN:
            return False
        if event.key == pygame.K_ESCAPE:
            self.closed = True
        elif event.key in (pygame.K_a, pygame.K_LEFT):
            self.page_index = max(0, self.page_index - 1)
        elif event.key in (
            pygame.K_e,
            pygame.K_d,
            pygame.K_RIGHT,
            pygame.K_SPACE,
            pygame.K_RETURN,
            pygame.K_KP_ENTER,
        ):
            if self.page_index < len(self.pages) - 1:
                self.page_index += 1
            else:
                self.closed = True
        return True

    def _wrap(self, text, maximum_width):
        rows = []
        current = ""
        for word in text.split():
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
        shade.fill((5, 8, 20, 180))
        screen.blit(shade, (0, 0))
        panel = pygame.Rect(55, 48, width - 110, height - 96)
        pygame.draw.rect(screen, (25, 30, 47), panel, border_radius=10)
        pygame.draw.rect(screen, (145, 110, 220), panel, 3, border_radius=10)

        title = self.title_font.render(
            "Spirit of the Manor", True, (215, 190, 255)
        )
        screen.blit(title, title.get_rect(midtop=(panel.centerx, panel.y + 15)))

        text_left = panel.x + 27
        text_width = panel.width - 54
        if self.kind == "intro":
            # Reserve the left side for the animated ghost sprite.
            text_left = panel.x + 125
            text_width = panel.right - text_left - 24
        elif self.kind == "reward":
            book_rect = self._book_image.get_rect(
                midleft=(panel.x + 23, panel.centery + 8)
            )
            screen.blit(self._book_image, book_rect)
            text_left = book_rect.right + 20
            text_width = panel.right - text_left - 24

        y = panel.y + 65
        for row in self._wrap(self.pages[self.page_index], text_width):
            text = self.body_font.render(row, True, (235, 230, 245))
            screen.blit(text, (text_left, y))
            y += 23

        page = self.small_font.render(
            f"{self.page_index + 1}/{len(self.pages)}",
            True,
            (180, 170, 205),
        )
        screen.blit(page, (panel.x + 18, panel.bottom - 26))
        hint = self.small_font.render(
            "ENTER / E: Continue    LEFT: Back    ESC: Close",
            True,
            (180, 170, 205),
        )
        screen.blit(
            hint,
            hint.get_rect(bottomright=(panel.right - 18, panel.bottom - 14)),
        )


class Ghost:
    _frames = None

    def __init__(self, center_x, bottom_y):
        self._load_frames()
        self.rect = pygame.Rect(0, 0, 42, 50)
        self.rect.midbottom = (center_x, bottom_y)
        self.animation_time = 0.0

    @classmethod
    def _load_frames(cls):
        if cls._frames is not None:
            return
        cls._frames = []
        for number in range(1, GHOST_FRAME_COUNT + 1):
            image = pygame.image.load(
                GHOST_PATH / f"frame{number}.png"
            ).convert_alpha()
            cls._frames.append(image)

    def set_position(self, center_x, bottom_y):
        self.rect.midbottom = (center_x, bottom_y)

    def update(self, delta_time):
        self.animation_time += delta_time

    def draw(self, screen, camera_x):
        frame_index = int(
            self.animation_time * GHOST_ANIMATION_SPEED
        ) % len(self._frames)
        image = self._frames[frame_index]
        screen.blit(
            image,
            image.get_rect(
                midbottom=(
                    self.rect.centerx - round(camera_x),
                    self.rect.bottom,
                )
            ),
        )
