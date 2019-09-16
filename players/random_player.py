import random

from cards import BaseCard, OutpostCard
from engine import Game
from user_actions import UndoMove
from players.player import Player


class RandomPlayer(Player):
    def choose_action(self, b, p_other, actions):
        return random.choice(actions)

    def do_choose_from_piles(self, action, piles, min_n=0, max_n=1, ship_only=False):
        n = random.randint(min_n, max_n)
        if not n:
            return None, None
        pile = random.choice(piles)
        n = min(n, len(pile))
        cards = random.sample(pile, n)
        return pile, cards




if __name__ == '__main__':
    p1 = RandomPlayer('p1')
    p2 = RandomPlayer('p2')

    g=Game([p1,p2], seed=None)

    g.run()