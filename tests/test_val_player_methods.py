import unittest

from val_player_methods import METHODS, is_player_method, player_pick

HISTORY = [dict(numbers=[5, 7, 2]), dict(numbers=[3, 1, 8]), dict(numbers=[9, 0, 4])]


class PlayerMethodTests(unittest.TestCase):
    def pick(self, method, history=HISTORY, width=3):
        return player_pick(method, history, width)["numbers"]

    def test_tic_tac_toe_adding(self):
        # 5 7 2 / 3 1 8 / 9 0 4
        self.assertEqual(self.pick("player_ttt_columns"), [7, 8, 4])     # 17, 8, 14
        self.assertEqual(self.pick("player_ttt_rows"), [4, 2, 3])        # 14, 12, 13
        self.assertEqual(self.pick("player_ttt_diagonals"), [0, 4, 5])   # 5+1+4, 7+8+9, 2+3+0

    def test_last_result_methods(self):
        self.assertEqual(self.pick("player_add_last_two"), [2, 1, 2])
        self.assertEqual(self.pick("player_mirror"), [4, 5, 9])

    def test_uses_only_most_recent_results_and_any_width(self):
        older = [dict(numbers=[1, 1, 1, 1])] * 5
        recent = [dict(numbers=[d] * 4) for d in (1, 2, 3, 4)]
        self.assertEqual(self.pick("player_ttt_columns", older + recent, 4), [0, 0, 0, 0])
        self.assertEqual(self.pick("player_ttt_rows", older + recent, 4), [4, 8, 2, 6])

    def test_needs_enough_history(self):
        with self.assertRaises(ValueError):
            self.pick("player_ttt_columns", HISTORY[:2])

    def test_every_method_runs_and_is_labeled(self):
        for method in METHODS:
            self.assertEqual(len(self.pick(method)), 3)
            self.assertTrue(is_player_method(dict(method=method)))
        self.assertFalse(is_player_method(dict(method="digit_box_v4")))


if __name__ == "__main__":
    unittest.main()
