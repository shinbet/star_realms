from typing import Tuple, List

from cards import BaseCard, OutpostCard
from engine import Game, Card
from players.player import Player
from user_actions import UserActionPlayAllCards, UserActionPlayCard


class InteractivePlayer(Player):

    def choose_action(self, b: Game, p_other: Player, actions):
        self._print_player(p_other)
        self._print_player(self)
        self._print_cards('trade:', b.trade_pile)
        self._print_cards('played:', self.in_play)
        print(f'trade:{self.trade} damage:{self.damage} discard:{p_other.discard}')
        self._print_cards('draw:', self.draw_pile)
        self._print_cards('hand:', self.hand)

        print()
        print('actions:')
        #actions = self.get_actions(b, p_other)
        for n, a in enumerate(actions, 1):
            print('{}: {}'.format(n, a))
        i = input(f'{self.name} action?')
        if i == 'a':
            action = UserActionPlayAllCards([a for a in actions if isinstance(a, UserActionPlayCard)])
        else:
            action = actions[int(i)-1]
        return action

    def _print_player(self, p):
        print(f'{p.name} {p.health}')
        self._print_cards('bases:', p.bases)

    def _print_cards(self, caption, cards):
        print(caption)
        for c in cards:
            print(f'{c.name} {c.cost} {c.actions}')

    def do_choose_from_piles(self, action, *piles, min_n=0, max_n=1, ship_only=False)  -> Tuple['Pile',List[Card]]:
        if ship_only:
            piles = [list(filter(lambda c: not isinstance(c, (BaseCard, OutpostCard)), p)) for p in piles]
            piles = [p for p in piles if p and len(p) > min_n]

        print(f'choose {min_n} to {max_n} cards to {action} from :')
        if len(piles) > 1:
            for pile in piles:
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

        return [pile] + [pile[i] for i in ids]