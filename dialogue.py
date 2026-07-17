"""Reusable Pokemon-style typewriter dialogue box."""

import pygame


class DialogueBox:
    def __init__(self, lines, portraits=None, characters_per_second=42):
        self.lines = lines
        self.portraits = portraits or {}
        self.characters_per_second = characters_per_second
        self.line_index = 0
        self.visible_characters = 0.0
        self.finished = not bool(lines)
        self.body_font = pygame.font.Font(None, 23)
        self.name_font = pygame.font.Font(None, 21)

    @property
    def current_line(self):
        return self.lines[self.line_index]

    @property
    def line_is_revealed(self):
        return self.visible_characters >= len(self.current_line["text"])

    def update(self, delta_time):
        if self.finished or self.line_is_revealed:
            return
        self.visible_characters = min(
            len(self.current_line["text"]),
            self.visible_characters
            + self.characters_per_second * delta_time,
        )

    def handle_event(self, event):
        if self.finished or event.type != pygame.KEYDOWN:
            return False

        if event.key == pygame.K_ESCAPE:
            self.finished = True
            return True

        if event.key not in (
            pygame.K_e,
            pygame.K_SPACE,
            pygame.K_RETURN,
            pygame.K_KP_ENTER,
        ):
            return True

        if not self.line_is_revealed:
            self.visible_characters = len(self.current_line["text"])
        elif self.line_index < len(self.lines) - 1:
            self.line_index += 1
            self.visible_characters = 0.0
        else:
            self.finished = True
        return True

    def _wrap_text(self, text, maximum_width):
        words = text.split()
        rows = []
        current_row = ""
        for word in words:
            candidate = f"{current_row} {word}".strip()
            if current_row and self.body_font.size(candidate)[0] > maximum_width:
                rows.append(current_row)
                current_row = word
            else:
                current_row = candidate
        if current_row:
            rows.append(current_row)
        return rows

    def draw(self, screen):
        if self.finished:
            return

        width, height = screen.get_size()
        panel = pygame.Rect(18, height - 104, width - 36, 86)
        shadow = panel.move(3, 3)
        pygame.draw.rect(screen, (8, 10, 18), shadow, border_radius=7)
        pygame.draw.rect(screen, (246, 244, 226), panel, border_radius=7)
        pygame.draw.rect(screen, (35, 48, 78), panel, 4, border_radius=7)
        pygame.draw.rect(screen, (105, 135, 180), panel, 2, border_radius=7)

        speaker = self.current_line["speaker"]
        name_surface = self.name_font.render(speaker, True, (255, 244, 180))
        name_box = pygame.Rect(
            panel.x + 13,
            panel.y - 18,
            name_surface.get_width() + 20,
            25,
        )
        pygame.draw.rect(screen, (35, 48, 78), name_box, border_radius=5)
        screen.blit(name_surface, (name_box.x + 10, name_box.y + 4))

        portrait = self.portraits.get(speaker)
        text_left = panel.x + 17
        text_width = panel.width - 34
        if portrait is not None:
            portrait_area = pygame.Rect(
                panel.x + 10, panel.y + 10, 68, panel.height - 20
            )
            pygame.draw.rect(
                screen, (218, 224, 221), portrait_area, border_radius=4
            )
            pygame.draw.rect(
                screen, (105, 135, 180), portrait_area, 2, border_radius=4
            )

            scale = min(
                portrait_area.width / portrait.get_width(),
                portrait_area.height / portrait.get_height(),
            )
            portrait_size = (
                max(1, round(portrait.get_width() * scale)),
                max(1, round(portrait.get_height() * scale)),
            )
            # Standard scaling preserves the hard edges of pixel artwork.
            large_portrait = pygame.transform.scale(
                portrait, portrait_size
            )
            portrait_rect = large_portrait.get_rect(
                midbottom=(portrait_area.centerx, portrait_area.bottom - 2)
            )
            screen.blit(large_portrait, portrait_rect)
            text_left = portrait_area.right + 13
            text_width = panel.right - text_left - 17

        visible_text = self.current_line["text"][
            : int(self.visible_characters)
        ]
        rows = self._wrap_text(visible_text, text_width)
        for row_number, row in enumerate(rows[:3]):
            text_surface = self.body_font.render(row, True, (28, 32, 43))
            screen.blit(
                text_surface,
                (text_left, panel.y + 18 + row_number * 21),
            )

        if self.line_is_revealed:
            arrow_x = panel.right - 22
            arrow_y = panel.bottom - 14
            pygame.draw.polygon(
                screen,
                (35, 48, 78),
                [(arrow_x, arrow_y - 5), (arrow_x + 10, arrow_y - 5),
                 (arrow_x + 5, arrow_y + 2)],
            )


class MapSelectionBox:
    """Pokemon-style portal destination selection panel."""

    def __init__(
        self,
        map2_cleared=False,
        map3_cleared=False,
        map4_cleared=False,
        map5_cleared=False,
    ):
        self.options = [
            {
                "name": "Ember Forest",
                "map": "map2",
                "locked": False,
                "status": "CLEARED" if map2_cleared else "SLIME MISSION",
            },
            {
                "name": "Toad Realm",
                "map": "map3",
                "locked": not map2_cleared,
                "status": (
                    "CLEARED" if map3_cleared
                    else "BOSS MISSION" if map2_cleared
                    else "LOCKED: Clear Ember Forest"
                ),
            },
            {
                "name": "Skyfall Expanse",
                "map": "map4",
                "locked": not map3_cleared,
                "status": (
                    "CLEARED" if map4_cleared
                    else "DRAGON MISSION" if map3_cleared
                    else "LOCKED: Clear Toad Realm"
                ),
            },
            {
                "name": "Crystal Labyrinth",
                "map": "map5",
                "locked": False,
                "status": (
                    "CLEARED" if map5_cleared
                    else "CRYSTAL PUZZLE (TEST OPEN)"
                ),
            },
            {
                "name": "Map 7",
                "map": "map7",
                "locked": False,
                "status": "IMAGE TEST OPEN",
            },
        ]
        self.selected = 0
        self.closed = False
        self.choice = None
        self.title_font = pygame.font.Font(None, 31)
        self.option_font = pygame.font.Font(None, 25)
        self.small_font = pygame.font.Font(None, 18)
        self.visible_rows = 3
        self.scroll_offset = 0

    def _keep_selected_visible(self):
        if self.selected < self.scroll_offset:
            self.scroll_offset = self.selected
        elif self.selected >= self.scroll_offset + self.visible_rows:
            self.scroll_offset = self.selected - self.visible_rows + 1

    def handle_event(self, event):
        if self.closed or event.type != pygame.KEYDOWN:
            return False
        if event.key == pygame.K_ESCAPE:
            self.closed = True
        elif event.key in (pygame.K_w, pygame.K_UP):
            self.selected = (self.selected - 1) % len(self.options)
            self._keep_selected_visible()
        elif event.key in (pygame.K_s, pygame.K_DOWN):
            self.selected = (self.selected + 1) % len(self.options)
            self._keep_selected_visible()
        elif event.key in (
            pygame.K_e,
            pygame.K_SPACE,
            pygame.K_RETURN,
            pygame.K_KP_ENTER,
        ):
            option = self.options[self.selected]
            if not option["locked"]:
                self.choice = option["map"]
                self.closed = True
        return True

    def draw(self, screen):
        if self.closed:
            return
        width, height = screen.get_size()
        shade = pygame.Surface((width, height), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 145))
        screen.blit(shade, (0, 0))

        panel = pygame.Rect(92, 42, width - 184, height - 84)
        pygame.draw.rect(screen, (246, 244, 226), panel, border_radius=9)
        pygame.draw.rect(screen, (35, 48, 78), panel, 4, border_radius=9)
        title = self.title_font.render(
            "Choose a Portal Destination", True, (35, 48, 78)
        )
        screen.blit(title, title.get_rect(midtop=(panel.centerx, panel.y + 17)))

        list_area = pygame.Rect(
            panel.x + 20, panel.y + 54, panel.width - 40, 142
        )
        old_clip = screen.get_clip()
        screen.set_clip(list_area)
        visible_options = self.options[
            self.scroll_offset:self.scroll_offset + self.visible_rows
        ]
        for visible_index, option in enumerate(visible_options):
            index = self.scroll_offset + visible_index
            row = pygame.Rect(
                panel.x + 24,
                panel.y + 57 + visible_index * 46,
                panel.width - 48,
                40,
            )
            selected = index == self.selected
            pygame.draw.rect(
                screen,
                (210, 225, 226) if selected else (231, 231, 217),
                row,
                border_radius=6,
            )
            if selected:
                pygame.draw.rect(
                    screen, (73, 111, 151), row, 3, border_radius=6
                )
            color = (125, 125, 125) if option["locked"] else (28, 32, 43)
            prefix = "> " if selected else "  "
            name = self.option_font.render(prefix + option["name"], True, color)
            status = self.small_font.render(option["status"], True, color)
            screen.blit(name, (row.x + 10, row.y + 2))
            screen.blit(status, (row.x + 29, row.y + 22))
        screen.set_clip(old_clip)

        if self.scroll_offset > 0:
            up = self.small_font.render("▲ more", True, (55, 62, 78))
            screen.blit(up, up.get_rect(topright=(panel.right - 18, panel.y + 42)))
        if self.scroll_offset + self.visible_rows < len(self.options):
            down = self.small_font.render("▼ more", True, (55, 62, 78))
            screen.blit(
                down,
                down.get_rect(bottomright=(panel.right - 18, panel.bottom - 31)),
            )

        hint = self.small_font.render(
            "UP/DOWN: Choose   ENTER: Travel   ESC: Cancel",
            True,
            (55, 62, 78),
        )
        screen.blit(
            hint,
            hint.get_rect(midbottom=(panel.centerx, panel.bottom - 12)),
        )
