import os
import unittest

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from Dragon.dragon import DRAGON_MAX_HEALTH
from map6.map6 import (
    MAP_WIDTH as MAP6_WIDTH,
    NPC3_X,
    door_is_open,
    stop_flight,
)
from npc3.npc import QuestWindow
from player import Player
from player.player import FLIGHT_DURATION, MAX_LEVEL
from toads.toad import BOSS_ATTACK_RANGE


class FlyMagicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((600, 320))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_fly_magic_unlocks_at_level_three(self):
        player = Player(80, 100)
        player.wind_crystals = 4

        self.assertFalse(player.craft_magic("Fly Magic"))
        self.assertEqual(player.wind_crystals, 4)

        player.level = 3
        self.assertTrue(player.craft_magic("Fly Magic"))
        self.assertEqual(player.wind_crystals, 2)
        self.assertEqual(player.magic_uses["Fly Magic"], 1)

    def test_each_fly_spell_adds_thirty_seconds_and_is_consumed(self):
        player = Player(80, 100)
        player.level = 3
        player.wind_crystals = 4
        player.craft_magic("Fly Magic")
        player.craft_magic("Fly Magic")
        activate = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_g)

        self.assertTrue(
            player.handle_event(activate, allow_flight_activation=True)
        )
        self.assertEqual(player.flight_time_left, FLIGHT_DURATION)
        self.assertEqual(player.magic_uses["Fly Magic"], 1)

        self.assertTrue(
            player.handle_event(
                activate,
                allow_flight_activation=True,
                require_active_flight=True,
            )
        )
        self.assertEqual(player.flight_time_left, FLIGHT_DURATION * 2)
        self.assertEqual(player.magic_uses["Fly Magic"], 0)

        self.assertTrue(
            player.handle_event(
                activate,
                allow_flight_activation=True,
                require_active_flight=True,
            )
        )
        self.assertEqual(player.flight_time_left, FLIGHT_DURATION * 2)

    def test_map6_forces_flight_to_stop(self):
        player = Player(80, 100)
        player.flight_time_left = 30.0
        player.flight_dash_time_left = 1.0

        stop_flight(player)

        self.assertEqual(player.flight_time_left, 0.0)
        self.assertEqual(player.flight_dash_time_left, 0.0)

    def test_player_can_activate_a_new_fly_spell_after_map6_entry(self):
        player = Player(80, 100)
        player.flight_time_left = 12.0
        player.magic_uses["Fly Magic"] = 1
        stop_flight(player)
        activate = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_g)

        player.handle_event(activate, allow_flight_activation=True)

        self.assertEqual(player.flight_time_left, FLIGHT_DURATION)
        self.assertEqual(player.magic_uses["Fly Magic"], 0)

    def test_npc3_is_positioned_inside_map6(self):
        self.assertGreater(NPC3_X, MAP6_WIDTH // 2)
        self.assertLess(NPC3_X, MAP6_WIDTH)

    def test_map4_dragon_has_boss_health(self):
        self.assertGreaterEqual(DRAGON_MAX_HEALTH, 200)

    def test_toad_boss_attack_range_is_reduced(self):
        self.assertEqual(BOSS_ATTACK_RANGE, 30)

    def test_player_can_reach_level_ten_but_not_higher(self):
        player = Player(80, 100)
        player.add_points(10_000)
        self.assertEqual(MAX_LEVEL, 10)
        self.assertEqual(player.level, 10)
        self.assertEqual(player.shield_health_cap, 240)

    def test_npc3_book_handover_opens_map6_door(self):
        player = Player(80, 100)
        player.map7_has_book = True
        window = QuestWindow(player)
        hand_over = pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_RETURN
        )

        consumed, action = window.handle_event(hand_over)

        self.assertTrue(consumed)
        self.assertEqual(action, "book_delivered")
        self.assertTrue(door_is_open(player))


if __name__ == "__main__":
    unittest.main()
