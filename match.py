from __future__ import annotations

import multiprocessing
from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations
from operator import itemgetter
from typing import List

from engine import Game
from players.NN.NNSimple import NNSimplePlayer
from players.NN.NNUCTPlayer import Net
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

    def w_l(self):
        return f'{self.W}/{self.L}'

PLAYERS_MAP = {}

class BaseRunner:
    def __init__(self, players):
        self.results = defaultdict(lambda : defaultdict(Result))

        PLAYERS_MAP.clear()
        self.players = []
        for name, p in players:
            PLAYERS_MAP[name] = p
            self.players.append(name)

    def summary(self, crosstable=True):
        res = [(name, sum(opp.values(), Result())) for name, opp in self.results.items()]
        res = [(name, r.W/(r.L+r.W), r.W, r.L) for name, r in res]
        res.sort(key=itemgetter(1), reverse=True)

        print('Summary:')
        fmt = '{:>10} {:>6} {:>6} {:>6} {:>6}'
        print(fmt.format('PLAYER', '%', 'GAMES', 'W', 'L'))
        for n,r,w,l in res:
            tot = w+l
            print(fmt.format(n, '{:.2f}'.format(r*100), tot, w , l))

        if crosstable:
            print()
            print('Crosstable:')
            players = [r[0] for r in res]
            fmt = '{:>10} ' + '{:>10}' * len(players)
            print(fmt.format('', *players))
            for p1 in players:
                scores = [self.results[p1][p2].w_l() if p2!=p1 else ' --- ' for p2 in players]
                print(fmt.format(p1, *scores))

    def run(self, rounds=400, workers=4):
        with multiprocessing.Pool(workers) as pool:
            for w,l in pool.imap_unordered(worker, self.scheduler(rounds)):
                self.results[w][l].W += 1
                self.results[l][w].L += 1
                print(f'{w}-{l}: {self.results[w][l]}')

    def scheduler(self, rounds):
        raise NotImplemented()

class RoundRobin(BaseRunner):
    def scheduler(self, rounds):
        for p1, p2 in combinations(self.players, 2):
            for r in range(rounds):
                if r % 2 == 1:
                    yield p1, p2
                else:
                    yield p2, p1



class Bench(BaseRunner):
    def scheduler(self, rounds):
        p1 = self.players[0]
        for p2 in self.players[1:]:
            for r in range(rounds):
                if r % 2 == 1:
                    yield p1, p2
                else:
                    yield p2, p1

'''
c=1s+0.1s, Hert 500 book, round robins
   # PLAYER           :  RATING  ERROR  POINTS  PLAYED   (%)  CFS(%)    W     D    L
   1 lc0.net.42850    :       3     12  1105.0    2000  55.2      69  558  1094  348
   2 lc0.net.LS10     :       0   ----  1092.0    2000  54.6     100  544  1096  360
   3 lc0.net.32930    :     -69     12   803.0    2000  40.1     ---  262  1082  656

White advantage = 35.15 +/- 4.43
Draw rate (equal opponents) = 56.83 % +/- 0.94
'''

def worker(p1_p2):
    p1, p2 = p1_p2
    p1 = PLAYERS_MAP[p1]
    p2 = PLAYERS_MAP[p2]

    players = [p1(), p2()]
    game = Game(players, verbose=False)
    winner = game.run()
    loser = players[0] if winner == players[1] else players[1]
    return winner.name, loser.name

def make_player(cls, *args, **kwargs):
    return (args[0], lambda: cls(*args, **kwargs))

if __name__ == '__main__':
    from players.random_player import RandomPlayer, WEIGHT_MAP29, WEIGHT_MAP26, WEIGHT_MAP, WEIGHT_MAP_t1, WEIGHT_MAP_t2
    from players.simple import SimplePlayer

    t = RoundRobin([
        #make_player(RandomPlayer, 'mine', w=WEIGHT_MAP),
        make_player(RandomPlayer, 'lr29', w=WEIGHT_MAP29),
        #make_player(RandomPlayer, 'lr26', w=WEIGHT_MAP26),
        #make_player(RandomPlayer, 't1', w=WEIGHT_MAP_t1),
        #make_player(RandomPlayer, 't2', w=WEIGHT_MAP_t2),
        make_player(SimplePlayer, 's1'),
        make_player(NNSimplePlayer, '3_6', "3 8"),
        make_player(NNSimplePlayer, '6_8', "6 8"),
        make_player(NNSimplePlayer, '7_5', "7 5"),
        make_player(NNSimplePlayer, '8_5', "8 5"),
    ])

    t.run()
    t.summary()