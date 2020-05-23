import unittest
from typing import List, Tuple
from unittest.mock import patch

from cards import EXPLORER, Junkyard, Card, BattleStation, PatrolMech, BlobCarrier, BlobWheel, OptionalAction, \
    ActionFreeShipCard
from engine import Game
from pile import Pile
from players.player import Player
from user_actions import UserActionAttackOutpost, UserActionPlayCard, UserActionCardAction


class TestPlayer(Player):

    def do_choose_from_piles(action, filtered_piles: List[Pile], min_n: int, max_n: int) -> Tuple[Pile, List[Card]]:
        pass

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
        actions = g.available_actions(p1, p2)
        self.assertIn(action, actions)

        with patch.object(TestPlayer, 'choose_action') as choose_action:
            choose_action.return_value = action

            g.do_one_user_action(p1, p2)
            choose_action.assert_called_once()
            self.assertEqual(2, p1.trade)
            self.assertEqual(2, p1.damage)
            self.assertEqual(0, len(p1.remaining_actions))

    def test_attack_outpost(self):
        p1 = TestPlayer('p1')
        p2 = TestPlayer('p2')
        g = Game([p1, p2])

        p1.damage = 10
        p1.trade = 100
        p2.outposts.append(Junkyard)

        action = UserActionAttackOutpost(Junkyard)
        actions = g.available_actions(p1, p2)
        self.assertIn(action, actions)

        with patch.object(TestPlayer, 'choose_action') as choose_action:
            choose_action.return_value = action

            g.do_one_user_action(p1, p2)
            choose_action.assert_called_once()
            self.assertEqual(0, len(p2.outposts))
            self.assertEqual(10-Junkyard.defence, p1.damage)

        actions = g.available_actions(p1, p2)
        self.assertNotIn(action, actions)

    def test_card_optional_ally_action(self):
        p1 = TestPlayer('p1')
        p2 = TestPlayer('p2')
        g = Game([p1, p2])
        p1.trade = 100
        p1.bases.append(BlobWheel)
        p1.hand.append(BlobCarrier)

        action = UserActionCardAction(BlobCarrier, ActionFreeShipCard())

        actions = g.available_actions(p1, p2)
        self.assertNotIn(action, actions)

        with patch.object(TestPlayer, 'choose_action') as choose_action:
            choose_action.return_value = UserActionPlayCard(BlobCarrier)
            g.do_one_user_action(p1, p2)

            choose_action.assert_called_once()
            self.assertEqual(1, len(p1.in_play))

        actions = g.available_actions(p1, p2)
        self.assertIn(action, actions)

if __name__ == '__main__':
    unittest.main()