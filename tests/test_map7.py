import os
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from dialogue import MapSelectionBox
from ghosts.ghost import INTRO_PAGES
from map7.map7 import (
    LADDER_LOWER_FLOOR_Y,
    LADDER_RECT,
    LADDER_UPPER_FLOOR_Y,
    PLAYER_SPAWN,
    PUZZLE_TIME_LIMIT,
    create_platform_rects,
    load_ladder,
    load_map,
    map7,
    move_player_on_ladder,
    reset_timed_puzzle,
)
from map7.interactions import (
    CLOCK_CORRECT_TIME,
    InteractionWindow,
    NOTE_PAGES,
    PAINTING_CORRECT_ANGLE,
    create_interactables,
    light_candle,
)
from map7.platform import platform
from player import Player


class Map7Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_map7_is_locked_until_map6_is_complete(self):
        locked = MapSelectionBox(map4_cleared=True)
        locked_option = next(
            item for item in locked.options if item["map"] == "map7"
        )
        self.assertTrue(locked_option["locked"])
        self.assertEqual(locked_option["name"], "Haunted Manor")
        self.assertEqual(locked_option["status"], "LOCKED: Complete Map 6")

        unlocked = MapSelectionBox(
            map4_cleared=True,
            map6_cleared=True,
        )
        unlocked_option = next(
            item for item in unlocked.options if item["map"] == "map7"
        )
        self.assertFalse(unlocked_option["locked"])
        self.assertEqual(
            unlocked_option["status"], "BOOK OF ARCANA QUEST"
        )

    def test_map6_unlocks_after_map4(self):
        locked = MapSelectionBox(map3_cleared=True)
        locked_option = next(
            item for item in locked.options if item["map"] == "map6"
        )
        self.assertTrue(locked_option["locked"])

        unlocked = MapSelectionBox(map4_cleared=True)
        unlocked_option = next(
            item for item in unlocked.options if item["map"] == "map6"
        )
        self.assertFalse(unlocked_option["locked"])
        self.assertEqual(unlocked_option["name"], "Grieving Hollow")

    def test_map7_spawn_is_next_to_the_riddle_note(self):
        note = next(
            item for item in create_interactables()
            if item.object_type == 0
        )
        spawn_rect = pygame.Rect(*PLAYER_SPAWN, 24, 40)
        self.assertTrue(note.rect.inflate(110, 110).colliderect(spawn_rect))

    def test_map7_keeps_its_native_world_size(self):
        self.assertEqual(load_map().get_size(), (960, 320))

    def test_map7_foreground_provides_platform_collision(self):
        platforms = create_platform_rects()
        self.assertTrue(platforms)
        self.assertTrue(any(rect.top == 288 for rect in platforms))
        expected_count = sum(
            tile != -1 for row in platform for tile in row
        )
        self.assertEqual(len(platforms), expected_count)

    def test_ladder_right_of_red_candle_connects_both_floors(self):
        red_candle = next(
            item for item in create_interactables()
            if item.object_type == 2
        )
        self.assertGreaterEqual(LADDER_RECT.left, red_candle.rect.right)
        self.assertLess(LADDER_RECT.left - red_candle.rect.right, 48)
        self.assertLessEqual(LADDER_RECT.top, LADDER_UPPER_FLOOR_Y)
        self.assertEqual(LADDER_RECT.bottom, LADDER_LOWER_FLOOR_Y)
        self.assertEqual(load_ladder().get_size(), LADDER_RECT.size)
        upper_platforms = [
            rect
            for rect in create_platform_rects()
            if rect.top == LADDER_UPPER_FLOOR_Y
        ]
        player_at_top = pygame.Rect(
            LADDER_RECT.centerx - 12,
            LADDER_UPPER_FLOOR_Y - 40,
            24,
            40,
        )
        self.assertTrue(
            any(
                player_at_top.right > rect.left
                and player_at_top.left < rect.right
                for rect in upper_platforms
            )
        )

    def test_player_can_climb_map7_ladder(self):
        player = Player(
            LADDER_RECT.centerx - 12,
            LADDER_LOWER_FLOOR_Y - 40,
        )
        starting_y = player.position.y

        self.assertTrue(move_player_on_ladder(player, -1, 0.25))
        self.assertLess(player.position.y, starting_y)

        for _ in range(120):
            move_player_on_ladder(player, -1, 1 / 60)
        self.assertEqual(player.rect.bottom, LADDER_UPPER_FLOOR_Y)

        for _ in range(120):
            move_player_on_ladder(player, 1, 1 / 60)
        self.assertEqual(player.rect.bottom, LADDER_LOWER_FLOOR_Y)

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

    def test_intro_ghost_gives_short_timed_challenge(self):
        full_text = " ".join(INTRO_PAGES)
        self.assertEqual(len(INTRO_PAGES), 1)
        self.assertIn("1 minute 30 seconds", full_text)
        self.assertIn("rewarded", full_text)

    def test_timed_challenge_reset_clears_every_puzzle(self):
        player = Player(0, 0)
        player.map7_painting_solved = True
        player.map7_clock_solved = True
        player.map7_candles_lit[:] = [1, 2, 5]
        player.map7_candles_solved = True
        player.map7_mission_complete = True

        reset_timed_puzzle(player)

        self.assertFalse(player.map7_painting_solved)
        self.assertFalse(player.map7_clock_solved)
        self.assertEqual(player.map7_candles_lit, [])
        self.assertFalse(player.map7_mission_complete)
        self.assertEqual(player.map7_puzzle_time_left, PUZZLE_TIME_LIMIT)

    def test_intro_ghost_appears_on_first_entry_without_quest_flag(self):
        player = Player(0, 0)
        for _ in INTRO_PAGES:
            pygame.event.post(
                pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
            )
        pygame.event.post(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        )

        with patch(
            "map7.map7.open_in_game_menu", return_value=False
        ):
            next_map, returned_player, arrived_from = map7(player, "map1")
        self.assertTrue(player.map7_ghost_intro_seen)
        self.assertIsNone(next_map)
        self.assertIs(returned_player, player)
        self.assertIsNone(arrived_from)

    def test_escape_opens_menu_and_preserves_player(self):
        player = Player(0, 0)
        player.map7_ghost_intro_seen = True
        pygame.event.post(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        )
        with patch(
            "map7.map7.open_in_game_menu", return_value=False
        ) as pause_menu:
            next_map, returned_player, arrived_from = map7(player, "map1")
        pause_menu.assert_called_once()
        self.assertIsNone(next_map)
        self.assertIs(returned_player, player)
        self.assertIsNone(arrived_from)

    def test_map7_book_exit_returns_to_map6(self):
        source = Path(__file__).parents[1] / "map7" / "map7.py"
        map7_source = source.read_text(encoding="utf-8")
        self.assertIn('next_map = "map6"', map7_source)


if __name__ == "__main__":
    unittest.main()
