from __future__ import annotations

import random
from abc import ABCMeta, abstractmethod
from typing import List, Tuple

from actions import Action
from cards import DEFAULT_PLAYER_DRAW, Card, BaseCard, OutpostCard
from user_actions import UndoMove
from pile import Pile


class Player(metaclass=ABCMeta):
    def __init__(self, name, health=50, draw_pile=None, discard_pile=None, bases=None, hand=None, outposts=None):
        from engine import Pile

        if not draw_pile and not discard_pile:
            discard_pile = DEFAULT_PLAYER_DRAW.copy()
            random.shuffle(discard_pile)

        self.draw_pile : Pile[Card] = Pile('draw', draw_pile or [])
        self.discard_pile : Pile[Card] = Pile('discard', discard_pile or [])
        self.health = health
        self.name = name
        self.bases : Pile[BaseCard] = Pile('bases', bases or [])
        self.outposts : Pile[OutpostCard] = Pile('outposts', outposts or [])

        # turn data
        self.hand : Pile[Card] = Pile('hand', hand or [])
        self.in_play : Pile[Card] = Pile('in_play', [])
        self.trade = 0
        self.discard = 0
        self.on_top = 0
        self.damage = 0
        self.remaining_actions : List[Tuple[Card, Action]] = []

    def end_turn(self):
        # end turn
        self.discard_pile.extend(self.hand)
        self.hand.clear()
        self.discard_pile.extend(self.in_play)
        self.in_play.clear()
        self.trade = 0
        self.discard = 0
        self.on_top = 0
        self.damage = 0
        self.remaining_actions = []

    def draw(self, n):
        for _ in range(n):
            if not self.draw_pile:
                # shuffle discard into draw
                self.draw_pile[:], self.discard_pile[:] = self.discard_pile, []
                random.shuffle(self.draw_pile)
            if not self.draw_pile:
                return # insufficient cards
            # this will be an issue when we try to play ahead
            # we need every run to be different, except for cards 'on top'
            self.hand.append(self.draw_pile.pop())

    @abstractmethod
    def choose_action(self, b, p_other, actions):
        pass

    @abstractmethod
    def do_choose_from_piles(action, filtered_piles: List[Pile], min_n:int, max_n:int) -> Tuple[Pile, List[Card]]:
        pass

    def choose_from_piles(self, action: str, *piles: List[Pile], min_n=0, max_n=1, ship_only=False, remove_from_pile=True) -> Tuple[Pile, List[Card]]:
        if ship_only:
            filtered_piles = [Pile(p.name, filter(lambda c: not isinstance(c, (BaseCard, OutpostCard)), p)) for p in piles]
            filtered_piles = [p for p in piles if p and len(p) > min_n]
        else:
            filtered_piles = piles

        if not filtered_piles and min_n > 0:
            raise UndoMove()

        pile, cards = self.do_choose_from_piles(action, filtered_piles, min_n, max_n)
        actual_pile = None
        if pile and remove_from_pile:
            actual_pile = [p for p in piles if p.name == pile.name]
            assert len(actual_pile) == 1
            actual_pile = actual_pile[0]
            for c in cards:
                actual_pile.remove(c)

        return actual_pile, cards

    def choose_discard(self, n: int):
        _, cards = self.choose_from_piles('discard', self.hand, min_n=n, max_n=n)
        if cards:
            self.discard_pile.extend(cards)
        return cards

    def choose_card_action(self, b, p_other, actions):
        return self.choose_action(b, p_other, actions)