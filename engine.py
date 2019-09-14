from __future__ import annotations

import copy
import random

from dataclasses import dataclass, field
from itertools import chain
from typing import List, Tuple

from cards import DEFAULT_PLAYER_DRAW, Card, DEFAULT_TRADE_PILE, AllyAction, \
    Faction, OptionalAction, OutpostCard, BaseCard, EXPLORER, Action


### https://github.com/tonywok/realms/tree/master/lib

def print_pile(pile):
    for n, c in enumerate(pile, 1):
        print(f'{n} {c.name}')

class UserActionPlayCard:
    def __init__(self, c: Card):
        self.card = c
    def __str__(self):
        return 'play ' + self.card.name

class UserActionBuyCard:
    def __init__(self, c: Card):
        self.card = c
    def __str__(self):
        return f'buy {self.card.name}: ${self.card.cost} {self.card}'

class UserActionAttackFace:
    def __str__(self):
        return 'attack user'

class UserActionAttackBase:
    def __init__(self, base):
        self.base = base

class UserActionAttackOutpost:
    def __init__(self, outpost):
        self.outpost = outpost

class UserActionCardAction:
    def __init__(self, c, a):
        self.card = c
        self.action = a

class UserActionPlayAllCards:
    def __init__(self, actions):
        self.actions = actions

class UserActionDone:
    pass

USER_ACTION_DONE = UserActionDone()

class Player:
    def __init__(self, name, health=50, draw_pile=None, discrad_pile=None, bases=None, hand=None, outposts=None):
        if not draw_pile and not discrad_pile:
            discrad_pile = DEFAULT_PLAYER_DRAW.copy()
            random.shuffle(discrad_pile)


        self.draw_pile : List[Card] = draw_pile or []
        self.discard_pile : List[Card] = discrad_pile or []
        self.health = health
        self.name = name
        self.bases : List[BaseCard] = bases or []
        self.outposts : List[OutpostCard] = outposts or []

        # turn data
        self.hand : List[Card] = hand or []
        self.in_play : List[Card] = []
        self.trade = 0
        self.discard = 0
        self.on_top = 0
        self.damage = 0
        self.remaining_actions : List[Tuple[Card, Action]] = []

    def end_turn(self):
        # end turn
        self.discard_pile.extend(self.hand)
        self.hand = []
        self.discard_pile.extend(self.in_play)
        self.in_play = []
        self.trade = 0
        self.discard = 0
        self.on_top = 0
        self.damage = 0
        self.remaining_actions = []

    def draw(self, n):
        for _ in range(n):
            if not self.draw_pile:
                # shuffle discard into draw
                self.draw_pile, self.discard_pile = self.discard_pile, []
                random.shuffle(self.draw_pile)
            if not self.draw_pile:
                return # insufficient cards
            self.hand.append(self.draw_pile.pop())

    def get_actions(self, game: Game, p2: Player):
        actions = []
        for c in self.hand:
            actions.append(UserActionPlayCard(c))
        for c in game.trade_pile:
            if c.cost <= self.trade:
                actions.append(UserActionBuyCard(c))
        if self.trade > 1:
            actions.append(UserActionBuyCard(copy.copy(EXPLORER)))
        for c, a in self.remaining_actions:
            if isinstance(a, OptionalAction):
                actions.append(UserActionCardAction(c, a.action))
        if self.damage:
            if p2.outposts:
                for o in p2.outposts:
                    if o.defence <= self.damage:
                        actions.append(UserActionAttackOutpost(o))
            else:
                for b in p2.bases:
                    if b.defence <= self.damage:
                        actions.append(UserActionAttackBase(b))
                actions.append(UserActionAttackFace())
        actions.append(USER_ACTION_DONE)
        return actions

class UndoMove(Exception):
    pass


class Game:
    def __init__(self, players: List[Player], turn = 0, trade_pile=None, draw_pile=None, seed=None):
        self.turn = 0
        self.players : List[Player] = players
        self.discard = 0
        self.trade_pile : List[Card] = trade_pile
        self.draw_pile : List[Card] = draw_pile
        self.scrap_pile : List[Card] = []

        if seed:
            random.seed(seed)

    def run(self):
        done = False
        if not self.trade_pile:
            self.trade_pile = [self.draw_pile.pop() for _ in range(5)]
        p = self.players[self.turn % 2]
        p_other = self.players[self.turn%2 + 1]

        while not done:
            p.draw(5 if self.turn > 0 else 3)
            if p.discard:
                p.choose_discard(self.discard)
                self.discard = 0

            for c in p.outposts:
                self.play(p1, p2, c)
            for c in p.bases:
                self.play(p1, p2, c)

            while 1:
                a = p.choose_action(self, p_other)
                if a == USER_ACTION_DONE:
                    break
                elif isinstance(a, UserActionPlayAllCards):
                    for a_ in a.actions:
                        self.do_action(p, p_other, a_)
                else:
                    self.do_action(p, p_other, a)

            p.end_turn()
            self.turn += 1
            p, p_other = p_other, p

    def do_action(self, p, p_other, a):
        if isinstance(a, UserActionAttackFace):
            if p_other.outposts:
                raise Exception('user has outposts!' + str(p_other.outposts))
            p_other.health -= p.damage
            p.damage = 0
        elif isinstance(a, UserActionPlayCard):
            self.action_play_card(p, p_other, a.card)
        elif isinstance(a, UserActionBuyCard):
            self.action_buy(p, a.card)
        elif isinstance(a, UserActionCardAction):
            a.action.exec(a.card, self, p, p_other)

    def action_buy(self, p: Player, card: Card, free=False):
        # check enough trade
        if not free and p.trade < card.cost:
            raise Exception('insufficient funds')
        if card != EXPLORER:
            idx = self.trade_pile.index(card)
            self.trade_pile[idx] = self.draw_pile.pop()

        if not free:
            p.trade -= card.cost

        if p.on_top > 0:
            p.in_play.append(card)
            p.on_top -= 1
        else:
            p.discard_pile.append(card)

    def action_play_card(self, p : Player, p2: Player, card: Card):
        p.hand.remove(card)
        self.play(p, p2 , card)
        if isinstance(card, BaseCard):
            p.bases.append(card)
        elif isinstance(card, OutpostCard):
            p.outposts.append(card)
        else:
            p.in_play.append(card)


    def play(self, p1 : Player, p2 : Player, card: Card):
        remaining_actions = [(card, action) for action in card.actions] + p1.remaining_actions

        is_allied = card.faction != Faction.UNALIGNED and any(card.is_ally(c) for c in chain(p1.hand, p1.bases, p1.outposts))

        new_remaining = []
        for c, action in remaining_actions:
            # perform actions
            if isinstance(action, AllyAction):
                if is_allied and card.is_ally(c):
                    action = action.action
                else:
                    new_remaining.append((c, action))
                    continue
            if isinstance(action, OptionalAction):
                new_remaining.append((c, action))
                continue
            action.exec(c, self, p1, p2)
        p1.remaining_actions = new_remaining


class InteractivePlayer(Player):

    def choose_action(self, b: Game, p_other: Player):
        self._print_player(p_other)
        self._print_player(self)
        self._print_cards('trade:', b.trade_pile)
        self._print_cards('played:', self.in_play)
        print(f'trade:{self.trade} damage:{self.damage} discard:{p_other.discard}')
        self._print_cards('draw:', self.draw_pile)
        self._print_cards('hand:', self.hand)

        print()
        print('actions:')
        actions = self.get_actions(b, p_other)
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

    def choose_scrap(self):
        print('a:')
        print_pile(self.discard_pile)
        print('b:')
        print_pile(self.in_play)

        choice = input('choose card')
        if not choice:
            raise UndoMove()

    def choose_pile(self, action, *piles, min_n=0, max_n=1):
        print(f'choose {min_n} to {max_n} cards from :')
        piles = [p for p in piles if p]
        ids = None
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

        return [pile] + ids

if __name__ == '__main__':
    p1 = InteractivePlayer('p1')
    p2 = InteractivePlayer('p2')

    draw = DEFAULT_TRADE_PILE.copy()
    random.shuffle(draw)
    g=Game([p1,p2], draw_pile=draw, seed=1)

    g.run()