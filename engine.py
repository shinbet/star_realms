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
    def __init__(self, players: List[Player], turn = 0, trade_pile=None, draw_pile=None, verbose=True, seed=None):
        self.turn = turn
        self.players : List[Player] = players
        if draw_pile is None:
            draw_pile = DEFAULT_TRADE_PILE.copy()
            random.shuffle(draw_pile)
        self.trade_pile : Pile[Card] = Pile('Trade', trade_pile or [])
        self.draw_pile : Pile[Card] = Pile('Trade Draw pile', draw_pile)
        #self.scrap_pile : Pile[Card] = Pile('scrap', [])

        if seed:
            random.seed(seed)
        self.verbose = verbose

    def __copy__(self):
        return Game(self.players, self.turn, self.trade_pile, self.draw_pile, self.verbose)

    def __hash__(self):
        v = (self.turn, self.draw_pile, self.trade_pile, self.players[0], self.players[1])
        return hash(v)

    def run(self):
        if not self.trade_pile:
            self.trade_pile[:] = [self.draw_pile.pop() for _ in range(min(5, len(self.draw_pile)))]

        p1 = self.players[self.turn % 2]
        p2 = self.players[(self.turn+1) % 2]
        try:
            while True:
                self.do_turn(p1, p2)
                self.turn += 1
                p1, p2 = p2, p1
        except GameOver as e:
            if self.verbose:
                log.info(f'winner is: {e.winner.name}')
            return e.winner

    def do_turn(self, p1: Player, p2: Player):
        if p1.need_draw:
            p1.draw(5 if self.turn > 0 else 3)
            p1.need_draw = False

            if p1.discard:
                p1.choose_discard(p1.discard)

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
        if len(available_actions) > 1:
            a = p1.choose_action(self, p2, available_actions)
        else:
            a = available_actions[0]
        if isinstance(a, UserActionPlayAllCards):
            for a_ in a.actions:
                self.do_action(p1, p2, a_)
        else:
            return self.do_action(p1, p2, a)
        return True

    def do_action(self, p1: Player, p2: Player, a: UserAction):
        if self.verbose:
            log.info('turn %s player %s: %s', self.turn, p1.name, a)

        if isinstance(a, UserActionAttackFace):
            if p2.outposts:
                raise Exception('user has outposts!' + str(p2.outposts))
            p2.health -= p1.damage
            p1.damage = 0
        elif isinstance(a, UserActionPlayCard):
            self.action_play_card(p1, p2, a.card)
        elif isinstance(a, UserActionBuyCard):
            self.action_buy(p1, a.card)
        elif isinstance(a, UserActionCardAction):
            # TODO: this is always optional... should we remove in choose_action?
            try:
                p1.remaining_actions.remove((a.card, a.action))
            except ValueError:
                p1.remaining_actions.remove((a.card, OptionalAction(a.action)))
            try:
                a.action.exec(a.card, self, p1, p2)
            except:
                p=1
        elif isinstance(a, UserActionAttackOutpost):
            p2.outposts.remove(a.outpost)
            p2.discard_pile.append(a.outpost)
            p1.damage -= a.outpost.defence
        elif isinstance(a, UserActionAttackBase):
            p2.bases.remove(a.base)
            p2.discard_pile.append(a.base)
            p1.damage -= a.base.defence
        elif a == USER_ACTION_DONE:
            return False
        else:
            raise Exception(f'unhandled action: {a}')
        return True

    def action_buy(self, p: Player, card: Card, free=False):
        # check enough trade
        if not free and p.trade < card.cost:
            raise Exception('insufficient funds')
        if card != EXPLORER:
            idx = self.trade_pile.index(card)
            try:
                self.trade_pile[idx] = self.draw_pile.pop()
            except IndexError:
                # ran out of cards
                self.trade_pile[idx:] = self.trade_pile[idx+1:]
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

        is_allied = card.faction != Faction.UNALIGNED and any(card.is_ally(c) for c in chain(p1.in_play, p1.bases, p1.outposts))

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
        enable_done = True
        actions = []
        for c in p1.hand:
            actions.append(UserActionPlayCard(c))
            enable_done = False
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
                        enable_done = False
            else:
                enable_done = False
                for b in p2.bases:
                    if b.defence <= p1.damage:
                        actions.append(UserActionAttackBase(b))
                if not p1.hand:
                    actions.append(UserActionAttackFace())
        if enable_done:
            actions.append(USER_ACTION_DONE)
        return actions


if __name__ == '__main__':
    from players.interactive_player import InteractivePlayer
    from players.monte_carlo import MCSimplePlayer

    p1 = InteractivePlayer('p1')
    #p2 = InteractivePlayer('p2')
    p2 = MCSimplePlayer('p2')

    g=Game([p1,p2], seed=666)

    print(g.run())