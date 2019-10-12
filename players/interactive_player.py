import pickle
import time
from typing import Tuple, List

from cards import BaseCard, OutpostCard
from engine import Game, Card
from players.player import Player
from user_actions import UserActionPlayAllCards, UserActionPlayCard


class InteractivePlayer(Player):

    def choose_action(self, b: Game, p_other: Player, actions):
        while 1:
            self._print_player(p_other)
            self._print_player(self)
            self._print_cards('trade:', b.trade_pile)
            self._print_cards('in play:', self.in_play)
            print(f'trade:{self.trade} damage:{self.damage} discard:{p_other.discard}')
            #self._print_cards('draw:', self.draw_pile)
            self._print_cards('hand:', self.hand)

            print()
            print('actions:')
            #actions = self.get_actions(b, p_other)
            for n, a in enumerate(actions, 1):
                print('{}: {}'.format(n, a))
            try:
                i = input(f'{self.name} action?')
                if i == 'a':
                    return UserActionPlayAllCards([a for a in actions if isinstance(a, UserActionPlayCard)])
                elif i.startswith('p'):
                    fname = i[1:]
                    fname.strip()
                    if not fname:
                        fname = time.strftime('%Y_%m_%d__%H_%M') + '.pkl'
                    with open(fname, 'xb') as f:
                        pickle.dump(b, f)
                    print(f'wrote file {fname}')
                else:
                    return actions[int(i)-1]
            except Exception as e:
                print(f'bad choice, got exception: {e}')


    def _print_player(self, p):
        print(f'{p.name} {p.health}')
        self._print_cards('bases:', p.bases)
        self._print_cards('outposts:', p.outposts)

    def _print_cards(self, caption, cards):
        print(caption)
        for c in cards:
            print(f'{c.name} {c.cost} {c.actions}')

    def do_choose_from_piles(self, action, piles, min_n, max_n):

        print(f'choose {min_n} to {max_n} cards to {action} from :')
        if len(piles) > 1:
            for pid, pile in enumerate(piles,1):
                print(f'pile {pid} {pile.name}:')
                self._print_cards('', pile)
            ids = input('choose pile and ids:')
            if ids:
                pid, *ids = [int(i)-1 for i in ids.split()]
                pile = piles[pid]
        else:
            pile = piles[0]
            self._print_cards('', pile)
            ids = input('choose ids:')
            ids = [int(i) - 1 for i in ids.split()]
        if not ids:
            return None, None

        return pile, [pile[i] for i in ids]


if __name__ == '__main__':

    p1 = InteractivePlayer('p1')
    p2 = InteractivePlayer('p2')
    players = [p1,p2]
    g = Game(players, seed=None)
    winner = g.run()
