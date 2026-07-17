from pathlib import Path

import pygame

from .object import objects as object_layer


TILE_SIZE = 16
INTERACTION_RANGE = 55
PAINTING_PATH = Path(__file__).parent / "painting.png"
PAINTING_CORRECT_ANGLE = 180
CLOCK_PATH = Path(__file__).parent / "clock0.png"
CLOCK_CORRECT_TIME = (10, 10)
CANDLE_SEQUENCE = (1, 2, 5)
CANDLE_COLORS = {
    1: (105, 85, 160),
    2: (255, 75, 55),
    5: (255, 240, 175),
}
OBJECT_NAMES = {
    0: "Faded Note",
    1: "Black Candle",
    2: "Red Candle",
    3: "Grandfather Clock",
    4: "Old Portrait",
    5: "White Candle",
}

NOTE_PAGES = (
    (
        "If someone is reading this, then perhaps you seek the Book of "
        "Arcana. I scattered its pages so that only those with patience "
        "and wisdom could reunite them."
    ),
    (
        "Time has become my greatest companion. Every evening, when the "
        "old grandfather clock rested at 10:10, I would sit in silence "
        "and remember the days when magic filled this house."
    ),
    (
        "Before my nightly studies, I always followed the old ritual "
        "taught by my master. First the Black candle, to leave the past "
        "behind. Then the Red candle, to ignite the will to learn. "
        "Finally, the White candle, to let wisdom reveal the path ahead. "
        "I never dared change the order."
    ),
    (
        "There hangs a portrait of my old friend. He always insisted that "
        "a true mage must never lose sight of the rising sun. I kept his "
        "portrait facing the east, just as he wished."
    ),
    (
        "If you can understand these memories, perhaps you are worthy of "
        "what lies hidden within this home."
    ),
)


class Interactable:
    def __init__(self, object_type, rect):
        self.object_type = object_type
        self.rect = rect
        self.name = OBJECT_NAMES[object_type]

    def is_near(self, player):
        return self.rect.inflate(
            INTERACTION_RANGE * 2,
            INTERACTION_RANGE * 2,
        ).colliderect(player.rect)


def create_interactables():
    """Combine adjacent cells of the same value into one object region."""
    interactables = []
    visited = set()
    row_count = len(object_layer)

    for row_number, row in enumerate(object_layer):
        for column_number, object_type in enumerate(row):
            start = (row_number, column_number)
            if object_type < 0 or start in visited:
                continue

            stack = [start]
            visited.add(start)
            cells = []
            while stack:
                current_row, current_column = stack.pop()
                cells.append((current_row, current_column))
                for next_row, next_column in (
                    (current_row - 1, current_column),
                    (current_row + 1, current_column),
                    (current_row, current_column - 1),
                    (current_row, current_column + 1),
                ):
                    if not (
                        0 <= next_row < row_count
                        and 0 <= next_column < len(object_layer[next_row])
                    ):
                        continue
                    next_cell = (next_row, next_column)
                    if (
                        next_cell not in visited
                        and object_layer[next_row][next_column] == object_type
                    ):
                        visited.add(next_cell)
                        stack.append(next_cell)

            rows = [cell[0] for cell in cells]
            columns = [cell[1] for cell in cells]
            left = min(columns) * TILE_SIZE
            top = min(rows) * TILE_SIZE
            width = (max(columns) - min(columns) + 1) * TILE_SIZE
            height = (max(rows) - min(rows) + 1) * TILE_SIZE
            interactables.append(
                Interactable(
                    object_type,
                    pygame.Rect(left, top, width, height),
                )
            )

    return interactables


def nearest_interactable(player, interactables):
    nearby = [item for item in interactables if item.is_near(player)]
    if not nearby:
        return None
    return min(
        nearby,
        key=lambda item: pygame.Vector2(player.rect.center).distance_to(
            item.rect.center
        ),
    )


class InteractionWindow:
    _painting_image = None
    _clock_image = None

    def __init__(self, interactable, player=None):
        self.interactable = interactable
        self.player = player
        self.page_index = 0
        self.closed = False
        self.result_message = ""
        self.painting_angle = (
            getattr(player, "map7_painting_angle", 0) % 360
        )
        if interactable.object_type == 4 and self._painting_image is None:
            original = pygame.image.load(PAINTING_PATH).convert_alpha()
            self.__class__._painting_image = pygame.transform.scale(
                original, (160, 160)
            )
        self.clock_hour = getattr(player, "map7_clock_hour", 12)
        self.clock_minute = getattr(player, "map7_clock_minute", 0)
        self.clock_part = 0
        if interactable.object_type == 3 and self._clock_image is None:
            original = pygame.image.load(CLOCK_PATH).convert_alpha()
            self.__class__._clock_image = pygame.transform.scale(
                original, (96, 96)
            )
        if interactable.object_type == 0:
            self.pages = NOTE_PAGES
        else:
            self.pages = (
                f"The {interactable.name} can be examined. Its puzzle "
                "interaction will be added later.",
            )
        self.title_font = pygame.font.Font(None, 31)
        self.body_font = pygame.font.Font(None, 23)
        self.small_font = pygame.font.Font(None, 18)
        self.clock_font = pygame.font.Font(None, 48)

    def handle_event(self, event):
        if self.closed or event.type != pygame.KEYDOWN:
            return False

        if self.interactable.object_type == 4:
            return self._handle_painting_event(event)
        if self.interactable.object_type == 3:
            return self._handle_clock_event(event)

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

    def _handle_painting_event(self, event):
        if event.key == pygame.K_ESCAPE:
            self.closed = True
        elif event.key in (pygame.K_a, pygame.K_LEFT):
            self.painting_angle = (self.painting_angle - 90) % 360
            self.result_message = ""
        elif event.key in (pygame.K_d, pygame.K_RIGHT):
            self.painting_angle = (self.painting_angle + 90) % 360
            self.result_message = ""
        elif event.key in (
            pygame.K_RETURN,
            pygame.K_KP_ENTER,
        ):
            correct = self.painting_angle == PAINTING_CORRECT_ANGLE
            if self.player is not None:
                self.player.map7_painting_angle = self.painting_angle
                self.player.map7_painting_solved = correct
                update_map7_mission(self.player)
            if correct:
                self.result_message = (
                    "Correct! The portrait's face is looking east."
                )
            else:
                self.result_message = "Wrong angle."
        return True

    def _handle_clock_event(self, event):
        if event.key == pygame.K_ESCAPE:
            self.closed = True
        elif event.key in (pygame.K_a, pygame.K_LEFT):
            self.clock_part = 0
            self.result_message = ""
        elif event.key in (pygame.K_d, pygame.K_RIGHT):
            self.clock_part = 1
            self.result_message = ""
        elif event.key in (pygame.K_w, pygame.K_UP):
            if self.clock_part == 0:
                self.clock_hour = self.clock_hour % 12 + 1
            else:
                self.clock_minute = (self.clock_minute + 5) % 60
            self.result_message = ""
        elif event.key in (pygame.K_s, pygame.K_DOWN):
            if self.clock_part == 0:
                self.clock_hour = (self.clock_hour - 2) % 12 + 1
            else:
                self.clock_minute = (self.clock_minute - 5) % 60
            self.result_message = ""
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            correct = (
                self.clock_hour,
                self.clock_minute,
            ) == CLOCK_CORRECT_TIME
            if self.player is not None:
                self.player.map7_clock_hour = self.clock_hour
                self.player.map7_clock_minute = self.clock_minute
                self.player.map7_clock_solved = correct
                update_map7_mission(self.player)
            self.result_message = (
                "Correct time!" if correct else "Wrong time."
            )
        return True

    def _wrap_text(self, text, maximum_width):
        rows = []
        current_row = ""
        for word in text.split():
            candidate = f"{current_row} {word}".strip()
            if (
                current_row
                and self.body_font.size(candidate)[0] > maximum_width
            ):
                rows.append(current_row)
                current_row = word
            else:
                current_row = candidate
        if current_row:
            rows.append(current_row)
        return rows

    def draw(self, screen):
        if self.interactable.object_type == 4:
            self._draw_painting_window(screen)
            return
        if self.interactable.object_type == 3:
            self._draw_clock_window(screen)
            return

        width, height = screen.get_size()
        shade = pygame.Surface((width, height), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 185))
        screen.blit(shade, (0, 0))

        panel = pygame.Rect(45, 26, width - 90, height - 52)
        pygame.draw.rect(screen, (235, 225, 192), panel, border_radius=8)
        pygame.draw.rect(screen, (77, 49, 36), panel, 4, border_radius=8)

        title = self.title_font.render(
            self.interactable.name, True, (65, 39, 29)
        )
        screen.blit(title, title.get_rect(midtop=(panel.centerx, panel.y + 16)))

        rows = self._wrap_text(self.pages[self.page_index], panel.width - 54)
        y = panel.y + 62
        for row in rows:
            text = self.body_font.render(row, True, (47, 38, 33))
            screen.blit(text, (panel.x + 27, y))
            y += 24

        page = self.small_font.render(
            f"Page {self.page_index + 1}/{len(self.pages)}",
            True,
            (90, 67, 51),
        )
        screen.blit(page, (panel.x + 20, panel.bottom - 27))
        hint = self.small_font.render(
            "E / ENTER: Next    LEFT: Previous    ESC: Close",
            True,
            (90, 67, 51),
        )
        screen.blit(
            hint,
            hint.get_rect(bottomright=(panel.right - 20, panel.bottom - 14)),
        )

    def _draw_painting_window(self, screen):
        width, height = screen.get_size()
        shade = pygame.Surface((width, height), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 200))
        screen.blit(shade, (0, 0))

        panel = pygame.Rect(75, 18, width - 150, height - 36)
        pygame.draw.rect(screen, (26, 24, 34), panel, border_radius=9)
        pygame.draw.rect(screen, (190, 155, 80), panel, 3, border_radius=9)

        title = self.title_font.render(
            "Rotate the Old Portrait", True, (245, 215, 145)
        )
        screen.blit(title, title.get_rect(midtop=(panel.centerx, panel.y + 12)))

        rotated = pygame.transform.rotate(
            self._painting_image, -self.painting_angle
        )
        painting_rect = rotated.get_rect(center=(panel.centerx, panel.centery))
        screen.blit(rotated, painting_rect)

        angle_text = self.small_font.render(
            f"Angle: {self.painting_angle} degrees",
            True,
            (225, 220, 205),
        )
        screen.blit(
            angle_text,
            angle_text.get_rect(midbottom=(panel.centerx, panel.bottom - 38)),
        )

        if self.result_message:
            correct = self.painting_angle == PAINTING_CORRECT_ANGLE
            result = self.body_font.render(
                self.result_message,
                True,
                (120, 245, 150) if correct else (255, 125, 105),
            )
            screen.blit(
                result,
                result.get_rect(midtop=(panel.centerx, panel.y + 45)),
            )

        hint = self.small_font.render(
            "LEFT / RIGHT: Rotate    ENTER: Set angle    ESC: Close",
            True,
            (190, 190, 205),
        )
        screen.blit(
            hint,
            hint.get_rect(midbottom=(panel.centerx, panel.bottom - 14)),
        )

    def _draw_clock_window(self, screen):
        width, height = screen.get_size()
        shade = pygame.Surface((width, height), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 200))
        screen.blit(shade, (0, 0))

        panel = pygame.Rect(75, 18, width - 150, height - 36)
        pygame.draw.rect(screen, (20, 27, 38), panel, border_radius=9)
        pygame.draw.rect(screen, (80, 190, 220), panel, 3, border_radius=9)

        title = self.title_font.render(
            "Set the Grandfather Clock", True, (145, 225, 245)
        )
        screen.blit(title, title.get_rect(midtop=(panel.centerx, panel.y + 12)))
        screen.blit(
            self._clock_image,
            self._clock_image.get_rect(midtop=(panel.centerx, panel.y + 45)),
        )

        hour_box = pygame.Rect(panel.centerx - 92, panel.y + 151, 72, 50)
        minute_box = pygame.Rect(panel.centerx + 20, panel.y + 151, 72, 50)
        for index, box in enumerate((hour_box, minute_box)):
            pygame.draw.rect(screen, (35, 43, 57), box, border_radius=6)
            pygame.draw.rect(
                screen,
                (255, 215, 95) if self.clock_part == index else (95, 115, 135),
                box,
                3 if self.clock_part == index else 1,
                border_radius=6,
            )
        hour = self.clock_font.render(
            f"{self.clock_hour:02d}", True, (240, 245, 245)
        )
        minute = self.clock_font.render(
            f"{self.clock_minute:02d}", True, (240, 245, 245)
        )
        colon = self.clock_font.render(":", True, (240, 245, 245))
        screen.blit(hour, hour.get_rect(center=hour_box.center))
        screen.blit(minute, minute.get_rect(center=minute_box.center))
        screen.blit(colon, colon.get_rect(center=(panel.centerx, hour_box.centery)))

        if self.result_message:
            correct = (
                self.clock_hour,
                self.clock_minute,
            ) == CLOCK_CORRECT_TIME
            result = self.body_font.render(
                self.result_message,
                True,
                (120, 245, 150) if correct else (255, 125, 105),
            )
            screen.blit(
                result,
                result.get_rect(midtop=(panel.centerx, panel.y + 207)),
            )

        hint = self.small_font.render(
            "LEFT/RIGHT: Select   UP/DOWN: Change   ENTER: Set   ESC: Close",
            True,
            (190, 205, 220),
        )
        screen.blit(
            hint,
            hint.get_rect(midbottom=(panel.centerx, panel.bottom - 13)),
        )


def update_map7_mission(player):
    was_complete = player.map7_mission_complete
    player.map7_mission_complete = (
        player.map7_painting_solved
        and player.map7_clock_solved
        and player.map7_candles_solved
    )
    if player.map7_mission_complete and not was_complete:
        player.combat_message = "Map 7 mission complete!"
        player.combat_message_time_left = 3.0
    return player.map7_mission_complete


def light_candle(player, object_type):
    expected_index = len(player.map7_candles_lit)
    if (
        expected_index < len(CANDLE_SEQUENCE)
        and object_type == CANDLE_SEQUENCE[expected_index]
    ):
        player.map7_candles_lit.append(object_type)
        player.map7_candles_solved = (
            tuple(player.map7_candles_lit) == CANDLE_SEQUENCE
        )
        if player.map7_candles_solved:
            player.combat_message = "Correct candle order!"
        else:
            player.combat_message = (
                f"{OBJECT_NAMES[object_type]} lit "
                f"({len(player.map7_candles_lit)}/3)"
            )
    elif object_type in player.map7_candles_lit:
        player.combat_message = f"{OBJECT_NAMES[object_type]} is already lit."
    else:
        player.map7_candles_lit.clear()
        player.map7_candles_solved = False
        player.combat_message = "Wrong candle order. All candles went out."

    player.combat_message_time_left = 2.5
    update_map7_mission(player)
    return player.map7_candles_solved


def draw_lit_candles(screen, camera_x, interactables, player):
    for item in interactables:
        if item.object_type not in player.map7_candles_lit:
            continue
        glow_rect = item.rect.inflate(22, 20).move(-round(camera_x), 0)
        glow = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
        color = CANDLE_COLORS[item.object_type]
        pygame.draw.ellipse(glow, (*color, 70), glow.get_rect())
        pygame.draw.ellipse(glow, (*color, 210), glow.get_rect(), 2)
        screen.blit(glow, glow_rect)


def draw_interaction_prompt(screen, camera_x, interactable, font):
    action = (
        "Light" if interactable.object_type in CANDLE_SEQUENCE else "Examine"
    )
    label = font.render(
        f"E: {action} {interactable.name}", True, (255, 240, 175)
    )
    label_rect = label.get_rect(
        midbottom=(
            interactable.rect.centerx - round(camera_x),
            interactable.rect.top - 5,
        )
    )
    pygame.draw.rect(
        screen, (20, 18, 28), label_rect.inflate(10, 6), border_radius=5
    )
    screen.blit(label, label_rect)
