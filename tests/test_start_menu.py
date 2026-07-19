import os
import unittest

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from music_manager import get_master_volume, set_master_volume
from start_menu import CONTROLS, MENU_ITEMS, open_in_game_menu


class StartMenuTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((600, 320))

    @classmethod
    def tearDownClass(cls):
        set_master_volume(1.0)
        pygame.quit()

    def test_start_menu_has_all_requested_options(self):
        self.assertEqual(
            MENU_ITEMS,
            ("Start Game", "Controls", "Options (Sound)", "Exit"),
        )

    def test_controls_include_every_requested_key(self):
        labels = {key for key, _action in CONTROLS}
        self.assertTrue(
            {
                "A / LEFT",
                "D / RIGHT",
                "W / UP",
                "S / DOWN",
                "C",
                "M",
                "SPACE",
                "F",
                "K",
                "G",
                "H",
            }.issubset(labels)
        )

    def test_master_sound_volume_is_clamped(self):
        self.assertEqual(set_master_volume(-1), 0.0)
        self.assertEqual(set_master_volume(2), 1.0)
        self.assertEqual(set_master_volume(0.4), 0.4)
        self.assertEqual(get_master_volume(), 0.4)

    def test_in_game_menu_resumes_and_restores_map_caption(self):
        pygame.display.set_caption("Current Map")
        pygame.event.post(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        )

        self.assertTrue(open_in_game_menu(pygame.time.Clock()))
        self.assertEqual(pygame.display.get_caption()[0], "Current Map")


if __name__ == "__main__":
    unittest.main()
