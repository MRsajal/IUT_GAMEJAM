import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from dialogue import MapSelectionBox
from map7.map7 import create_platform_rects, load_map, map7
from map7.interactions import (
    CLOCK_CORRECT_TIME,
    InteractionWindow,
    NOTE_PAGES,
    PAINTING_CORRECT_ANGLE,
    create_interactables,
    light_candle,
)
from player import Player


class Map7Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_map7_is_an_open_map1_destination(self):
        selection = MapSelectionBox()
        option = next(
            item for item in selection.options if item["map"] == "map7"
        )
        self.assertFalse(option["locked"])

    def test_map7_keeps_its_native_world_size(self):
        self.assertEqual(load_map().get_size(), (960, 320))

    def test_map7_foreground_provides_platform_collision(self):
        platforms = create_platform_rects()
        self.assertTrue(platforms)
        self.assertTrue(any(rect.top == 288 for rect in platforms))

    def test_object_array_creates_all_six_interactions(self):
        interactables = create_interactables()
        self.assertEqual(len(interactables), 6)
        self.assertEqual(
            {item.object_type for item in interactables},
            {0, 1, 2, 3, 4, 5},
        )

    def test_note_window_contains_all_lore_pages(self):
        note = next(
            item for item in create_interactables()
            if item.object_type == 0
        )
        window = InteractionWindow(note)
        self.assertEqual(window.pages, NOTE_PAGES)
        full_text = " ".join(window.pages)
        self.assertIn("Book of Arcana", full_text)
        self.assertIn("10:10", full_text)
        self.assertIn("Black candle", full_text)
        self.assertIn("rising sun", full_text)

    def test_painting_is_correct_when_face_points_east(self):
        painting = next(
            item for item in create_interactables()
            if item.object_type == 4
        )
        player = Player(0, 0)
        window = InteractionWindow(painting, player)
        right = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT)
        window.handle_event(right)
        window.handle_event(right)
        self.assertEqual(window.painting_angle, PAINTING_CORRECT_ANGLE)

        enter = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        window.handle_event(enter)
        self.assertTrue(player.map7_painting_solved)
        self.assertEqual(player.map7_painting_angle, 180)
        self.assertIn("Correct", window.result_message)

    def test_painting_reports_a_wrong_angle(self):
        painting = next(
            item for item in create_interactables()
            if item.object_type == 4
        )
        player = Player(0, 0)
        window = InteractionWindow(painting, player)
        window.painting_angle = 90
        enter = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        window.handle_event(enter)
        self.assertFalse(player.map7_painting_solved)
        self.assertEqual(window.result_message, "Wrong angle.")

    def test_clock_accepts_ten_ten(self):
        clock = next(
            item for item in create_interactables()
            if item.object_type == 3
        )
        player = Player(0, 0)
        window = InteractionWindow(clock, player)
        window.clock_hour, window.clock_minute = CLOCK_CORRECT_TIME
        enter = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        window.handle_event(enter)
        self.assertTrue(player.map7_clock_solved)
        self.assertEqual(window.result_message, "Correct time!")

    def test_wrong_candle_order_resets_all_candles(self):
        player = Player(0, 0)
        light_candle(player, 1)
        light_candle(player, 5)
        self.assertEqual(player.map7_candles_lit, [])
        self.assertFalse(player.map7_candles_solved)

    def test_complete_mission_requires_all_three_puzzles(self):
        player = Player(0, 0)
        player.map7_painting_solved = True
        player.map7_clock_solved = True
        light_candle(player, 1)
        light_candle(player, 2)
        light_candle(player, 5)
        self.assertTrue(player.map7_candles_solved)
        self.assertTrue(player.map7_mission_complete)

    def test_escape_returns_to_map1_and_preserves_player(self):
        player = Player(0, 0)
        pygame.event.post(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        )
        next_map, returned_player, arrived_from = map7(player, "map1")
        self.assertEqual(next_map, "map1")
        self.assertIs(returned_player, player)
        self.assertEqual(arrived_from, "map7")


if __name__ == "__main__":
    unittest.main()
