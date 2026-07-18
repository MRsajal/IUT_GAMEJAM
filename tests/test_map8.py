import os
import unittest

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from map8.map8 import create_platform_rects, load_map
from map8.platform import platform
from Orge.ogre import OGRE_MAX_HEALTH, OgreBoss
from player import Player


class Map8Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((600, 320))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_map8_uses_native_size_and_platform_array(self):
        self.assertEqual(load_map().get_size(), (960, 320))
        expected_count = sum(
            tile != -1 for row in platform for tile in row
        )
        self.assertEqual(len(create_platform_rects()), expected_count)

    def test_ogre_has_three_rage_stages(self):
        ogre = OgreBoss(790, 272, 250, 950)
        self.assertEqual(ogre.max_health, OGRE_MAX_HEALTH)
        self.assertEqual(ogre.rage_stage, 0)
        ogre.health = round(ogre.max_health * 0.5)
        self.assertEqual(ogre.rage_stage, 1)
        ogre.health = round(ogre.max_health * 0.2)
        self.assertEqual(ogre.rage_stage, 2)

    def test_ogre_attack_animation_deals_damage(self):
        player = Player(730, 200)
        ogre = OgreBoss(790, 272, 250, 950)
        player.rect.centerx = ogre.rect.centerx - 40
        player.rect.centery = ogre.rect.centery
        player.position.update(player.rect.topleft)

        ogre.update(0.01, player)
        ogre.update(0.40, player)
        ogre.update(0.01, player)

        self.assertLess(player.health, player.max_health)


if __name__ == "__main__":
    unittest.main()
