import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from dialogue import MapSelectionBox
from map5.entities import CrystalSocket, FireBarrier, MovableCrystal, Shrine
from map5.map5 import CYAN, GROUND_Y, PuzzleState
from player import Player


class Map5PuzzleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_portal_is_visible_and_open_for_testing(self):
        portal = MapSelectionBox(True, True, False, False)
        map5_option = next(
            option for option in portal.options if option["map"] == "map5"
        )
        self.assertFalse(map5_option["locked"])

    def test_matching_crystal_activates_socket(self):
        crystal = MovableCrystal(100, GROUND_Y, CYAN)
        socket = CrystalSocket(crystal.rect.centerx, GROUND_Y, CYAN)
        self.assertTrue(socket.accepts(crystal))

    def test_crystal_stops_at_blocker(self):
        crystal = MovableCrystal(100, GROUND_Y, CYAN)
        crystal.blockers = [crystal.rect.move(crystal.rect.width, 0)]
        self.assertFalse(crystal.push(crystal.rect.width))

    def test_barrier_only_accepts_fire_damage(self):
        barrier = FireBarrier((100, 100, 30, 100))
        self.assertFalse(barrier.take_damage(999))
        self.assertFalse(barrier.destroyed)
        self.assertTrue(barrier.take_fire_damage(1))
        self.assertTrue(barrier.destroyed)

    def test_shrine_charges_do_not_add_sellable_spells(self):
        player = Player(0, 0)
        held_before = list(player.held_magic)
        Shrine(0, 0).recharge(player)
        self.assertGreaterEqual(player.magic_uses["Fire Magic"], 3)
        self.assertGreaterEqual(player.magic_uses["Fly Magic"], 2)
        self.assertEqual(player.held_magic, held_before)

    def test_checkpoint_reconstructs_completed_sections(self):
        state = PuzzleState(2)
        self.assertTrue(state.socket1.accepts(state.crystal1))
        self.assertTrue(state.barrier.destroyed)
        self.assertFalse(state.socket3.accepts(state.crystal3))


if __name__ == "__main__":
    unittest.main()
