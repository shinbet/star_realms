import random
from operator import attrgetter

from engine import Game
from players.interactive_player import InteractivePlayer
from players.player import Player
from user_actions import *

def _get_action_of_type(a_type, actions):
    for a in actions:
        if isinstance(a, a_type):
            yield a


class SimplePolicy:
    def simple_pile_policy(self, p, action, piles, min_n, max_n):
        if action == 'destory':
            # choose base/outpost with highest health to destroy
            return piles[0], sorted(piles[0], key=attrgetter('defence'), reverse=True)[:max_n]
        elif action == 'discard':
            # discard cheapest cards
            return piles[0], sorted(piles[0], key=attrgetter('cost'))[:min_n]
        elif action == 'discard_draw':
            # cycle cheap cards
            return piles[0], [c for c in piles[0] if c.cost == 1][:max_n]
        elif action == 'scrap':
            if piles[0].name == 'trade':
                # we don't scrap from trade row
                return None, None

            try:
                discard_p = next(p for p in piles if p.name=='discard')
                if min_n == 0:
                    # return only cheap cards
                    return discard_p, [c for c in discard_p if c.cost == 1][:max_n]
                else:
                    return discard_p, sorted(discard_p, key=attrgetter('cost'))[:min_n]
            except StopIteration:
                pass # no discard

            hand_p = piles[0]
            if min_n == 0:
                return None, None
            else:
                return hand_p, sorted(hand_p, key=attrgetter('cost'))[:min_n]
        elif action == 'buy':
            c = self.choose_buy_card(piles[0])
            if c:
                return piles[0], [c]
            else:
                return None, None
            # buy most expensive, but only if cost > 3
            c = max(piles[0], key=attrgetter('cost'))
            if c.cost > 3:
                return piles[0], [c]
            else:
                return None, None


    def simple_action_policy(self, p1: Player, game, p2, actions):
        from actions import ActionDiscardAndDraw, ActionDrawThenScrap, ActionScarpDrawCard

        # first play bases
        for base_a in _get_action_of_type(UserActionPlayCard, actions):
            if isinstance(base_a.card, (BaseCard, OutpostCard)):
                return base_a

        # optional discard/scrap actions
        for discard_a in _get_action_of_type(UserActionCardAction, actions):
            if isinstance(discard_a, (ActionDiscardAndDraw, ActionDrawThenScrap)):
                if len(c for c in p1.hand if c.cost == 1) > 0:
                    return discard_a
            if isinstance(discard_a, ActionScarpDrawCard):
                if len(c for c in p1.discard_pile if c.cost == 1) > 0:
                    return discard_a

        # play all cards
        for a in _get_action_of_type(UserActionPlayCard, actions):
            return a

        # other optional actions

        # buy good cards
        buys = list(_get_action_of_type(UserActionBuyCard, actions))
        if buys:
            b = self.choose_buy_actions(game, p1, p2, buys)
            if b:
                return b

        # do damage
        outposts =  sorted(_get_action_of_type(UserActionAttackOutpost, actions), key=lambda a: a.outpost.defence, reverse=True)
        if outposts:
            return outposts[0]

        bases =  sorted(_get_action_of_type(UserActionAttackBase, actions), key=lambda a: a.base.defence, reverse=True)
        if bases:
            return bases[0]

        for a in _get_action_of_type(UserActionAttackFace, actions):
            return a

        for a in _get_action_of_type(UserActionDone, actions):
            return a

        return random.choice(actions)

    def choose_buy_actions(self, game, p1, p2, buys):
        card_to_action = {a.card: a for a in buys}
        c = self.choose_buy_card(game, p1, p2, card_to_action.keys())
        if c:
            return card_to_action[c]

    def choose_buy_card(self, game, p1, p2, cards):
        # buy most expensive
        b = max(cards, key=attrgetter('cost'))
        return b

class SimplePlayer(Player, SimplePolicy):
    def choose_action(self, b, p_other, actions):
        return self.simple_action_policy(self, b, p_other, actions)

    choose_card_action = choose_action

    def do_choose_from_piles(self, action, piles, min_n, max_n):
        return self.simple_pile_policy(self, action, piles, min_n, max_n)

if __name__ == '__main__':
    p1 = InteractivePlayer('p1')
    p2 = SimplePlayer('p2')
    g = Game(players=[p1, p2])
    winner = g.run()