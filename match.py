from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations
from operator import itemgetter
from typing import List

from engine import Game
from players.player import Player

def expected(A, B):
    """
    Calculate expected score of A in a match against B
    :param A: Elo rating for player A
    :param B: Elo rating for player B
    """
    return 1 / (1 + 10 ** ((B - A) / 400))


def elo(old, exp, score, k=32):
    """
    Calculate the new Elo rating for a player
    :param old: The previous Elo rating
    :param exp: The expected score for this match
    :param score: The actual score for this match
    :param k: The k-factor for Elo (default: 32)
    """
    return old + k * (score - exp)

@dataclass
class Result:
    W: int = 0
    L: int = 0

    def __add__(self, other: Result):
        return Result(self.W + other.W, self.L+other.L)

class Tourny:
    def __init__(self, players):
        self.players = players
        self.results = defaultdict(lambda : defaultdict(Result))

    def run(self, rounds=400):
        for p1, p2 in combinations(self.players, 2):
            for r in range(rounds):
                players = [p1(), p2()]
                if r % 2 == 1:
                    players.reverse()
                game = Game(players, verbose=False)
                winner = game.run()
                loser = players[1] if winner is players[0] else players[0]
                self.results[winner.name][loser.name].W += 1
                self.results[loser.name][winner.name].L += 1
                print(f'{winner.name}-{loser.name}: {self.results[winner.name][loser.name]}')
    def summary(self):
        res = [(name, sum(opp.values(), Result())) for name, opp in self.results.items()]
        res = [(name, r.W/(r.L+r.W), r.W, r.L) for name, r in res]
        res.sort(key=itemgetter(1), reverse=True)

        fmt = '{:>10} {:>6} {:>6} {:>6} {:>6}'
        print(fmt.format('PLAYER', '%', 'GAMES', 'W', 'L'))
        for n,r,w,l in res:
            tot = w+l
            print(fmt.format(n, '{:.2f}'.format(r*100), tot, w , l))

class Bench:
    def __init__(self, p1, players):
        self.p1 = p1
        self.players = players
        self.results = defaultdict(lambda : defaultdict(Result))

    def run(self, rounds=400):
        for p2 in self.players:
            for r in range(rounds):
                players = [self.p1(), p2()]
                if r % 2 == 1:
                    players.reverse()
                game = Game(players, verbose=False)
                winner = game.run()
                loser = players[1] if winner is players[0] else players[0]
                self.results[winner.name][loser.name].W += 1
                self.results[loser.name][winner.name].L += 1
                print(f'{winner.name}-{loser.name}: {self.results[winner.name][loser.name]}')

    def summary(self):
        res = [(name, sum(opp.values(), Result())) for name, opp in self.results.items()]
        res = [(name, r.W/(r.L+r.W), r.W, r.L) for name, r in res]
        res.sort(key=itemgetter(1), reverse=True)

        fmt = '{:>10} {:>6} {:>6} {:>6} {:>6}'
        print(fmt.format('PLAYER', '%', 'GAMES', 'W', 'L'))
        for n,r,w,l in res:
            tot = w+l
            print(fmt.format(n, '{:.2f}'.format(r*100), tot, w , l))


'''
c=1s+0.1s, Hert 500 book, round robins
   # PLAYER           :  RATING  ERROR  POINTS  PLAYED   (%)  CFS(%)    W     D    L
   1 lc0.net.42850    :       3     12  1105.0    2000  55.2      69  558  1094  348
   2 lc0.net.LS10     :       0   ----  1092.0    2000  54.6     100  544  1096  360
   3 lc0.net.32930    :     -69     12   803.0    2000  40.1     ---  262  1082  656

White advantage = 35.15 +/- 4.43
Draw rate (equal opponents) = 56.83 % +/- 0.94
'''

def make_player(cls, *args, **kwargs):
    return lambda: cls(*args, **kwargs)

if __name__ == '__main__':
    from players.random_player import RandomPlayer, WEIGHT_MAP29, WEIGHT_MAP26, WEIGHT_MAP, WEIGHT_MAP_t1, WEIGHT_MAP_t2

    t = Tourny([
        make_player(RandomPlayer, 'mine', w=WEIGHT_MAP),
        make_player(RandomPlayer, 'lr29', w=WEIGHT_MAP29),
        make_player(RandomPlayer, 'lr26', w=WEIGHT_MAP26),
        #make_player(RandomPlayer, 't1', w=WEIGHT_MAP_t1),
        #make_player(RandomPlayer, 't2', w=WEIGHT_MAP_t2),
    ])

    t.run()
    t.summary()

    from players.random_player import ALL_ACTIONS
    print(ALL_ACTIONS)