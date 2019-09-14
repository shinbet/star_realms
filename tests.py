import unittest

from cards import VIPER, EXPLORER
from engine import Player, Game


class TestActions(unittest.TestCase):

    def test_self_discard(self):
        p1 = Player('p1', hand=[EXPLORER])
        p2 = Player('p2')
        g = Game([p1,p2])
        g.do_action(p1,p2,UserActionCardAction(EXPLORER))

if __name__ == '__main__':
    unittest.main()