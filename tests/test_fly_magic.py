import os
import unittest

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from map4.map4 import NPC3_X, OUTGOING_PORTAL_X
from player import Player
from player.player import FLIGHT_DURATION


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

    def test_npc3_is_next_to_map4_outgoing_portal(self):
        self.assertLessEqual(OUTGOING_PORTAL_X - NPC3_X, 50)


if __name__ == "__main__":
    unittest.main()
