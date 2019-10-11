
from cards import Card, BaseCard, OutpostCard
import logging
log = logging.getLogger(__name__)

class Action:
    def exec(self, c: Card, game, p1, p2):
        raise NotImplementedError()
    def __eq__(self, other):
        return other.__class__ == self.__class__ and self.__dict__ == other.__dict__

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return id(self)


class ActionFreeShipCard(Action):
    def __init__(self, on_top=True):
        self.on_top = on_top

    def exec(self, c: Card, game: 'Game', p1, p2):
        pile, cards = p1.choose_from_piles('buy', game.trade_pile, min_n=0, max_n=1, ship_only=True, remove_from_pile=False)
        if pile:
            if self.on_top:
                p1.on_top += 1
            game.action_buy(p1, cards[0], free=True)
    def __str__(self):
        if self.on_top:
            return 'get free ship and put on top of draw pile'
        else:
            return 'get free ship'

class ActionScrap(Action):
    def exec(self, c: Card, game, p1, p2):
        pile, cards = p1.choose_from_piles('scrap', p1.hand, p1.discard_pile)
        #if pile is not None:
        #    game.scrap_pile.extend(cards)
    def __str__(self):
        return 'scrap from hand or discard pile'

class ActionTradeRowScrap(Action):
    def exec(self, c: Card, game, p1, p2):
        pile, cards = p1.choose_from_piles('scrap', game.trade_pile, remove_from_pile=False)
        if cards:
            #game.scrap_pile.extend(cards)
            for card in cards:
                idx = game.trade_pile.index(card)
                try:
                    game.trade_pile[idx] = game.draw_pile.pop()
                except IndexError:
                    # ran out of cards
                    game.trade_pile[idx:] = game.trade_pile[idx + 1:]
    def __str__(self):
        return 'scrap from trade row'

class SimpleAction(Action):
    def __init__(self, n):
        self.n = n
    def exec(self, c: Card, game, p1, p2):
        v = getattr(p1, self.attr)
        setattr(p1, self.attr, v + self.n)
    def __str__(self):
        return f'{self.attr}:{self.n}'

class ActionDamage(SimpleAction):
    attr = 'damage'
class ActionTrade(SimpleAction):
    attr = 'trade'
class ActionHealth(SimpleAction):
    attr = 'health'

class ActionAddDiscard(Action):
    def __init__(self, n=1):
        self.n = n
    def exec(self, c: Card, game, p1: 'Player', p2: 'Player'):
        p2.discard += self.n
    def __str__(self):
        return 'Target opponent discards a card'

class AllyAction(Action):
    def __init__(self, action):
        self.action = action
    def __str__(self):
        return 'Ally Action: ' + str(self.action)

class OptionalAction(Action):
    def __init__(self, action):
        self.action = action
    def exec(self, c: Card, game, p1, p2):
        self.action.exec(c, game, p1, p2)
    def __str__(self):
        return 'Optional: ' + str(self.action)

class ChooseAction(Action):
    def __init__(self, *actions):
        self.actions = actions
    def exec(self, c: Card, game, p1, p2):
        a = p1.choose_card_action(game, p2, self.actions)
        a.exec(c, game, p1, p2)
    def __str__(self):
        return 'choose one of: ' + str(self.actions)

class ActionSelfScrap(OptionalAction):
    def __init__(self, *actions):
        self.actions = actions
        self.action = self
    def exec(self, c: Card, game, p1, p2):
        # FIXME: actuall card is important... we might have multiple with remaining actions
        if isinstance(c, BaseCard):
            p1.bases.remove(c)
        elif isinstance(c, OutpostCard):
            p1.outposts.remove(c)
        else:
            p1.in_play.remove(c)

        for a in self.actions:
            try:
                a.exec(c, game, p1, p2)
            except AttributeError:
                log.exception('ActionSelfScrap got exception')
    def __str__(self):
        return 'scrap self, then:' + str(self.actions)
    def __eq__(self, other):
        return other.__class__ == self.__class__ and self.actions == other.actions

class ActionDrawCard(Action):
    def __init__(self, n=1):
        self.n = n
    def exec(self, c: Card, game, p1, p2):
        p1.draw(self.n)
    def __str__(self):
        return 'Draw card'

class ActionDrawCardXAllies(Action):
    def exec(self, c: Card, game, p1, p2):
        n = sum(1 for ac in p1.in_play if c.is_ally(ac))
        p1.draw(n)
    def __str__(self):
        return 'Draw a card for each ally played'

class ActionDestroyBase(Action):
    def exec(self, c: Card, game, p1, p2):
        pile, cards = p1.choose_from_piles('destroy', p2.outposts or p2.bases)
        if pile:
            p2.discard_pile.extend(cards)
    def __str__(self):
        return 'Destroy target base'

class ActionScarpDrawCard(Action):
    def __init__(self, n):
        self.n = n
    def exec(self, c: Card, game, p1, p2):
        pile, cards = p1.choose_from_piles('scrap', p1.hand, p1.discard_pile, max_n=self.n)
        if pile:
            #game.scrap_pile.extend(cards)
            p1.draw(len(cards))
    def __str__(self):
        return f'scrap up to {self.n} cards from discard or hand and draw as many cards'

class ActionOnTop(Action):
    def exec(self, c: Card, game, p1, p2):
        p1.on_top += 1
    def __str__(self):
        return 'put next ship on top of draw pile'

class ActionDrawIfBases(Action):
    def __init__(self, bases, draw):
        self.bases = bases
        self.draw = draw
    def exec(self, c: Card, game, p1, p2):
        if len(p1.outposts) + len(p1.bases) >= self.bases:
            p1.draw(self.draw)
    def __str__(self):
        return f'draw {self.draw} cards when you have {self.bases} bases'

class ActionDrawThenScrap(Action):
    def exec(self, c: Card, game, p1, p2):
        p1.draw(1)
        pile, cards = p1.choose_from_piles('scrap', p1.hand, min_n=1, max_n=1)
        if pile:
            p1.discard_pile.extend(cards)
    def __str__(self):
        return 'Draw card then scrap from hand'

class ActionDiscardAndDraw(Action):
    def __init__(self, n):
        self.n = n
    def exec(self, c: Card, game, p1, p2):
        pile, cards = p1.choose_from_piles('discard_draw', p1.hand, max_n=self.n)
        if pile:
            p1.discard_pile.extend(cards)
            p1.draw(len(cards))
    def __str__(self):
        return f'discard up to {self.n} cards from hand and draw as many cards'
