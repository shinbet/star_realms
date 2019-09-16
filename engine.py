from __future__ import annotations

import random

from itertools import chain
from typing import List

from cards import DEFAULT_TRADE_PILE, AllyAction, \
    Faction, OptionalAction, OutpostCard, BaseCard, EXPLORER
from pile import Pile
from players.player import Player
from user_actions import *
import logging
logging.basicConfig(level=logging.INFO)

log = logging.getLogger()

### https://github.com/tonywok/realms/tree/master/lib


class GameOver(Exception):
    def __init__(self, p: Player):
        self.winner = p


class Game:
    def __init__(self, players: List[Player], turn = 0, trade_pile=None, draw_pile=None, seed=None, verbose=True):
        self.turn = turn
        self.players : List[Player] = players
        self.discard = 0
        if draw_pile is None:
            draw_pile = DEFAULT_TRADE_PILE.copy()
            random.shuffle(draw_pile)
        self.trade_pile : Pile[Card] = Pile('Trade', trade_pile or [])
        self.draw_pile : Pile[Card] = Pile('Trade Draw pile', draw_pile)
        self.scrap_pile : Pile[Card] = Pile('scrap', [])

        if seed:
            random.seed(seed)
        self.verbose = verbose

    def run(self):
        done = False
        p1 = self.players[self.turn % 2]
        p2 = self.players[self.turn%2 + 1]
        if not self.trade_pile:
            self.trade_pile = [self.draw_pile.pop() for _ in range(5)]

        try:
            while True:
                self.do_turn(p1, p2)
                self.turn += 1
                p1, p2 = p2, p1
        except GameOver as e:
            return e.winner

    def do_turn(self, p1, p2):
        p1.draw(5 if self.turn > 0 else 3)
        if p1.discard:
            p1.choose_discard(self.discard)
            self.discard = 0

        for c in p1.outposts:
            self.play(p1, p2, c)
        for c in p1.bases:
            self.play(p1, p2, c)

        while self.do_one_user_action(p1, p2):
            if p2.health <= 0:
                raise GameOver(p1)

        p1.end_turn()

    def do_one_user_action(self, p1 ,p2):
        available_actions = self.available_actions(p1, p2)
        a = p1.choose_action(self, p2, available_actions)
        if self.verbose:
            log.info('player %s: %s', p1.name, a)
        if a == USER_ACTION_DONE:
            return False
        elif isinstance(a, UserActionPlayAllCards):
            for a_ in a.actions:
                self.do_action(p1, p2, a_)
        else:
            self.do_action(p1, p2, a)
        return True

    def do_action(self, p: Player, p_other: Player, a: UserAction):
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
            # TODO: this is always optional... should we remove in choose_action?
            try:
                p.remaining_actions.remove((a.card, a.action))
            except ValueError:
                p.remaining_actions.remove((a.card, OptionalAction(a.action)))
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

    def available_actions(self, p1: Player, p2: Player):
        actions = []
        for c in p1.hand:
            actions.append(UserActionPlayCard(c))
        for c in self.trade_pile:
            if c.cost <= p1.trade:
                actions.append(UserActionBuyCard(c))
        if p1.trade > 1:
            actions.append(UserActionBuyCard(EXPLORER))
        for c, a in p1.remaining_actions:
            if isinstance(a, OptionalAction):
                actions.append(UserActionCardAction(c, a.action))
        if p1.damage:
            if p2.outposts:
                for o in p2.outposts:
                    if o.defence <= p1.damage:
                        actions.append(UserActionAttackOutpost(o))
            else:
                for b in p2.bases:
                    if b.defence <= p1.damage:
                        actions.append(UserActionAttackBase(b))
                actions.append(UserActionAttackFace())
        actions.append(USER_ACTION_DONE)
        return actions


if __name__ == '__main__':
    from players.interactive_player import InteractivePlayer

    p1 = InteractivePlayer('p1')
    p2 = InteractivePlayer('p2')

    g=Game([p1,p2], seed=1)

    g.run()