import unittest
from unittest.mock import patch

from cards import EXPLORER
from engine import Game, UserActionPlayCard, UserActionCardAction
from players.player import Player


class TestPlayer(Player):

    def choose_action(self, b, p_other):
        pass

    def choose_from_piles(self, action, piles, min_n=0, max_n=1, ship_only=False):
        pass


class TestActions(unittest.TestCase):

    def test_self_discard(self):
        p1 = TestPlayer('p1', hand=[EXPLORER])
        p2 = TestPlayer('p2')
        g = Game([p1, p2])

        with patch.object(TestPlayer, 'choose_action') as choose_action:
            choose_action.return_value = UserActionPlayCard(EXPLORER)

            g.do_one_user_action(p1, p2)
            choose_action.assert_called_once()
            self.assertEqual(2, p1.trade)
            self.assertEqual(1, len(p1.remaining_actions))
            self.assertSequenceEqual([(EXPLORER, EXPLORER.actions[1])], p1.remaining_actions)

        action = UserActionCardAction(EXPLORER, EXPLORER.actions[1])
        actions = p1.get_actions(g, p2)
        self.assertIn(action, actions)

        with patch.object(TestPlayer, 'choose_action') as choose_action:
            choose_action.return_value = action

            g.do_one_user_action(p1, p2)
            choose_action.assert_called_once()
            self.assertEqual(2, p1.trade)
            self.assertEqual(2, p1.damage)
            self.assertEqual(0, len(p1.remaining_actions))

if __name__ == '__main__':
    unittest.main()