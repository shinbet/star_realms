import random
from dataclasses import dataclass
import copy

from engine import Game
from players.player import Player
from players.random_player import RandomPlayer
from user_actions import UserActionDone, UserActionPlayCard, UserActionBuyCard, UserActionAttackOutpost, \
    UserActionAttackFace, UserActionAttackBase, UserActionCardAction

import logging
log = logging.getLogger(__name__)

RANDOM_MAP = {}

WEIGHT_MAP = {
    UserActionPlayCard: 100,
    UserActionAttackOutpost: 60,
    UserActionAttackFace: 60,
    UserActionAttackBase: 30,
    UserActionBuyCard: 20,
    UserActionCardAction: 10,
    UserActionDone: 1,
}

ACTIONS = [UserActionPlayCard,
           UserActionAttackOutpost,
           UserActionAttackFace,
           UserActionAttackBase,
           UserActionBuyCard,
           UserActionCardAction,
           UserActionDone]


WEIGHT_MAP29 = {a:v for a,v in zip(ACTIONS, [100, 60, 60, 81, 7, 89, 1])}
WEIGHT_MAP26 = {a:v for a,v in zip(ACTIONS, [100,60,96,81,7,89,1])}

WEIGHT_MAP_t1 = {a:v for a,v in zip(ACTIONS, [100,50,50,60,20,88,1])}
WEIGHT_MAP_t2 = {a:v for a,v in zip(ACTIONS, [100,85,50,60,20,23,1])}

@dataclass
class Result:
    W: int = 0
    L: int = 0

class RandomPlayerWithFirstAction(RandomPlayer):
    def choose_action(self, b, p_other, actions):
        if not self.first_action in actions:
            assert self.first_action in actions
        self.choose_action = super().choose_action
        return self.first_action

class MCSimplePlayer(Player):
    def __init__(self, name, health=50, draw_pile=None, discard_pile=None, bases=None, hand=None, outposts=None):
        super().__init__(name, health, draw_pile, discard_pile, bases, hand, outposts)

    def choose_action(self, b, p_other, actions):
        results = {repr(a): Result() for a in actions}

        me, other = RandomPlayerWithFirstAction('me', w=WEIGHT_MAP26), RandomPlayer('other', w=WEIGHT_MAP26)
        new_players = [me, other]
        if b.players[0] != self:
            new_players.reverse()

        for _ in range(100):
            a = random.choice(actions)
            me.first_action = a
            game = copy.copy(b)

            # copy player state
            for o_p, p in zip(b.players, new_players):
                p.from_player(o_p)
            game.players = new_players
            game.verbose = False
            winner = game.run()
            if winner.name == 'me':
                results[repr(a)].W += 1
            else:
                results[repr(a)].L += 1

        log.info('results= %s', results)
        best = max(results.items(), key=lambda item: item[1].W/(item[1].W + item[1].L))
        for a in actions:
            if repr(a) == best[0]:
                return a

    def choose_card_action(self, b, p_other, actions):
        # right now we cannot make this part of the rollouts so we have to choose randomly
        return random.choice(actions)


    def do_choose_from_piles(self, action, piles, min_n=0, max_n=1, ship_only=False):
        n = random.randint(min_n, max_n)
        if not n:
            return None, None
        pile = random.choice(piles)
        n = min(n, len(pile))
        cards = random.sample(pile, n)
        return pile, cards

def simple_match():

    win = {'p1':0, 'p2':0}
    for i in range(1):
        p1 = RandomPlayer('p1')
        p2 = MCSimplePlayer('p2', 100)
        players = [p1,p2]
        if i%2:
            players = players[::-1]
        g = Game(players, seed=None)
        winner = g.run()
        win[winner.name] += 1
        print(win)
    print(win)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    simple_match()