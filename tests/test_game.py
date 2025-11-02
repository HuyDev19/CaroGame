import unittest
from server.game import GameState


class TestGameState(unittest.TestCase):
    def test_horizontal_win(self):
        g = GameState(size=10, win_len=5)
        y = 4
        for x in range(5):
            g.turn = 1
            self.assertTrue(g.make_move(x, y))
            if x < 4:
                # after placing not yet win
                self.assertIsNone(g.winner)
        self.assertEqual(g.winner, 1)

    def test_blocked_move(self):
        g = GameState(size=5, win_len=5)
        self.assertTrue(g.make_move(0, 0))
        # cannot move same cell
        self.assertFalse(g.make_move(0, 0))


if __name__ == '__main__':
    unittest.main()
