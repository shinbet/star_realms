import json
import logging
import random
import time
from itertools import chain

from cards import TRADE_ROW_CARDS, VIPER, SCOUT, EXPLORER, OutpostCard, BaseCard
from engine import Game
from players.player import Player
from players.uct_player import UCTPlayer

import torch
import torch.nn as nn
import torch.nn.functional as F

log = logging.getLogger(__file__)

BOARD_WIDTH = 142

class Net(nn.Module):

    def __init__(self):
        super(Net, self).__init__()
        # 1 input vector
        # kernel
        self.fc1 = nn.Linear(BOARD_WIDTH, 120)
        self.fc2 = nn.Linear(120, 71)
        self.fc3 = nn.Linear(71, 1)

    def forward(self, x):
        if type(x) == list:
            x = torch.tensor(x)

        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x).tanh()
        return x

ALL_CARDS = TRADE_ROW_CARDS[::2] + [VIPER, SCOUT, EXPLORER]
CARD_TO_POS = {c:n for n, c in enumerate(ALL_CARDS)}
BASE_OUTPOST_TO_POS = {c:n for n, c in enumerate(c for c in ALL_CARDS if isinstance(c, (BaseCard, OutpostCard)))}

def to_vec(game: Game, p1: Player, p2: Player):
    p1_v = player_to_vec(p1)
    p2_v = player_to_vec(p2)

    # add trade pile? discard?
    return p1_v + p2_v

def player_to_vec(p: Player):
    # 49 cards can be held
    # 18 in play bases and outposts
    # 1 health
    # 1 dmg
    # 1 discard
    # 1 trade
    # overall: 71


    # all cards
    a = [0.0] * 49
    for c in chain(p.draw_pile, p.discard_pile, p.outposts, p.bases, p.hand, p.in_play):
        a[CARD_TO_POS[c]] += 1

    # bases/outposts in play
    b_o = [0.0] * 18
    for c in chain(p.outposts, p.bases):
        b_o[BASE_OUTPOST_TO_POS[c]] += 1

    v = a + b_o + [p.health, p.damage, p.discard, p.trade]
    return v

class NNUCTPlayer(UCTPlayer):
    def __init__(self, name, nn, *args, train=False, eps=0.1, **kwargs):
        super().__init__(name, *args, **kwargs)
        self._nn = nn
        self._train = train
        self._eps = eps
        if train:
            self._states = []

    def choose_action(self, o_game, p_other, actions):
        if self._train and self._eps and random.random() < self._eps:
            a = random.choice(actions)
        else:
            a = super().choose_action(o_game, p_other, actions)
        if self._train:
            self._states.append(to_vec(o_game, self, p_other))
        return a

    def eval_state(self, game: Game, p1, p2):
        state = to_vec(game, p1, p2)
        v = self._nn.forward(state).item()
        return v



def play():
    p1 = NNUCTPlayer('p1', nn=Net())
    p2 = NNUCTPlayer('p2', nn=Net())
    g = Game(players=[p1, p2])
    winner = g.run()

if __name__ == '__main__':
    play()