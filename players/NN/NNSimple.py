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
                state = to_vec(game, p1, p2)
                v = self._nn.forward(state).item()
                Q.append((c,v))
                states[c] = state
                if c is not None:
                    p1.discard_pile.pop()
            c = max(Q, key=itemgetter(1))[0]
            #log.info('buy scores: %s', Q)
            log.info('%s chose %s', self.name, c.name if c else 'nothing')
            if self._train:
                self._states.append(states[c])
        return c
