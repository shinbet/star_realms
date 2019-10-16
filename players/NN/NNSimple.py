import random
import logging
from itertools import chain
from operator import itemgetter

from players.NN.NNUCTPlayer import to_vec
from players.simple import SimplePlayer

log = logging.getLogger(__name__)

NO_BUY_RATE = 0.05
class NNSimplePlayer(SimplePlayer):
    def __init__(self, name, nn, *args, train=False, eps=0.1, **kwargs):
        super().__init__(name, *args, **kwargs)
        if isinstance(nn, str):
            from train import load_from_name
            nn = load_from_name(nn)
            nn.eval()
        self._nn = nn
        self._train = train
        self._eps = eps
        if train:
            self._states = []

    def choose_buy_card(self, game, p1, p2, cards):
        if self._train and self._eps and random.random() < self._eps:
            # some chance of no buy
            if random.random() < NO_BUY_RATE:
                return None
            c = random.choice(list(cards))
            return c
        else:
            states = {}
            Q = []
            # also score no buy
            for c in chain([None], cards):
                if c is not None:
                    # for now assume to discard... we can handle on top later
                    p1.discard_pile.append(c)
                    p1.trade -= c.cost
                state = to_vec(game, p1, p2)
                v = self._nn.forward(state).item()
                Q.append((c,v))
                states[c] = state
                if c is not None:
                    p1.discard_pile.pop()
                    p1.trade += c.cost
            c = max(Q, key=itemgetter(1))[0]
            #log.info('buy scores: %s', [(c.name if c else 'nothing', v) for c,v in Q])
            #log.info('%s chose %s', self.name, c.name if c else 'nothing')
            if self._train:
                self._states.append(states[c])
        return c

if __name__ == '__main__':
    from players.interactive_player import InteractivePlayer
    from engine import Game
    from train2 import load_net, fname_from_id, load_from_name
    import train2
    import sys
    import os
    os.chdir(os.path.dirname(train2.__file__))
    p1 = InteractivePlayer('p1')
    p2 = NNSimplePlayer('p2', '3 6')
    g = Game(players=[p1, p2])
    winner = g.run()