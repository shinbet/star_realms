from __future__ import annotations

import copy
from typing import List
from dataclasses import dataclass, field
from enum import Enum, auto, Flag

### https://github.com/tonywok/realms/tree/master/lib

class AutoName(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name

class Faction(Flag):
    UNALIGNED = auto()
    BLOB = auto()
    TRADE_FEDERATION = auto()
    MACHINE_CULT = auto()
    STAR_ALLIANCE = auto()
    ALL = BLOB | TRADE_FEDERATION | MACHINE_CULT | STAR_ALLIANCE

class CardType(AutoName):
    REG = auto()
    BASE = auto()
    OUTPOST = auto()

@dataclass
class Card:
    name : str
    #type: CardType
    cost: int
    faction: Faction
    actions: List

    def is_ally(self, c: Card):
        return bool(self.faction & c.faction)

@dataclass
class BaseCard(Card):
    defence: int

@dataclass
class OutpostCard(Card):
    defence: int



class Action:
    def exec(self, c: Card, game, p1, p2):
        raise NotImplementedError()


class ActionBuyCard(Action):
    def __init__(self, on_top=True):
        self.on_top = on_top

    def exec(self, c: Card, game, p1, p2):
        pile, idx = p1.choose_pile('buy', game.trade_pile)
        card = pile[idx]
        if self.on_top:
            p1.on_top += 1
        game.buy(p1, p2, card, free=True)

class ActionScrap(Action):
    def exec(self, c: Card, game, p1, p2):
        pile, idx = p1.choose_pile('scrap', p1.hand, p1.discard_pile)
        if pile is not None:
            game.scrap_pile.append(pile[idx])
            del pile[idx]

class ActionTradeRowScrap(Action):
    def exec(self, c: Card, game, p1, p2):
        pile, idx = p1.choose_pile('scrap', game.trade_pile)
        if idx is not None:
            game.scrap_pile.append(pile[idx])
            game.trade_pile[idx] = self.draw_pile.pop()


class SimpleAction(Action):
    def __init__(self, n):
        self.n = n

    def exec(self, c: Card, game, p1, p2):
        v = getattr(p1, self.attr)
        setattr(p1, self.attr, v + self.n)

class ActionDamage(SimpleAction):
    attr = 'damage'
class ActionTrade(SimpleAction):
    attr = 'trade'
class ActionHealth(SimpleAction):
    attr = 'health'

class ActionAddDiscard(Action):
    def __init__(self, n=1):
        self.n = n
    def exec(self, c: Card, game, p1, p2):
        v = getattr(p1, self.attr)
        setattr(p2, self.attr, v + self.n)

class AllyAction:
    def __init__(self, action):
        self.action = action

class OptionalAction:
    def __init__(self, action):
        self.action = action

class ChooseAction(Action):
    def __init__(self, *actions):
        self.actions = actions
    def exec(self, c: Card, game, p1, p2):
        a = p1.choose_action(self.actions)
        a.exec(c, game, p1, p2)

class ActionSelfScrap(OptionalAction):
    def __init__(self, *actions):
        self.actions = actions
        self.action = self
    def exec(self, c: Card, game, p1, p2):
        p1.in_play.remove(c)
        for a in self.actions:
            a.exec(c, game, p1, p2)

class ActionDrawCard(Action):
    def __init__(self, n=1):
        self.n = n
    def exec(self, c: Card, game, p1, p2):
        p1.draw(self.n)

class ActionDrawCardXAllies(Action):
    def exec(self, c: Card, game, p1, p2):
        n = len(1 for ac in p1.in_play if c.is_ally(ac))
        p1.draw(self.n)


class ActionDestroyBase(Action):
    def exec(self, c: Card, game, p1, p2):
        pile , idx = p1.choose_pile('destroy', p2.outposts or p2.bases)
        if pile:
            c = pile.pop(idx)
            p2.discard.append(c)

class ActionScarpDrawCard(Action):
    def __init__(self, n):
        self.n = n
    def exec(self, c: Card, game, p1, p2):
        pile, *idx = p1.choose_pile('scrap', p1.hand, p1.discard_pile, max_n=self.n)
        if pile:
            for i in idx:
                del pile[i]
            p1.draw(len(idx))

class ActionOnTop:
    def exec(self, c: Card, game, p1, p2):
        p1.on_top += 1

class ActionDrawIfBases(Action):
    def __init__(self, bases, draw):
        self.bases = bases
        self.draw = draw
    def exec(self, c: Card, game, p1, p2):
        if len(p1.outposts) + len(p1.bases) >= self.bases:
            p1.draw(self.draw)

class ActionDrawThenScrap(Action):
    def exec(self, c: Card, game, p1, p2):
        p1.draw(1)
        p1.choose_pile('scrap', p1.hand, min_n=1, max_n=1)

VIPER = Card('Viper', 0, Faction.UNALIGNED, [ActionDamage(1)])
SCOUT = Card('Scout', 0, Faction.UNALIGNED, [ActionTrade(1)])
EXPLORER = Card('Explorer', 2, Faction.UNALIGNED, [ActionTrade(2),
                                                   ActionSelfScrap(ActionDamage(2))])

BarterWorld = BaseCard('BarterWorld', 4, Faction.TRADE_FEDERATION,
                       [OptionalAction(ChooseAction(ActionTrade(2), ActionHealth(2))),
                        ActionSelfScrap([ActionDamage(5)])], defence=4)
BattleBlob = Card('BattleBlob', 6, Faction.BLOB, [ActionDamage(8),
                                                  AllyAction(ActionDrawCard()),
                                                  OptionalAction(ActionSelfScrap(ActionDamage(4)))])
BattleMech = Card('BattleMech', 5, Faction.MACHINE_CULT,
                  [ActionDamage(4),
                   ActionScrap(),
                   AllyAction(ActionDrawCard(1))])
BATTLEPOD = Card('BattlePod', 2, Faction.BLOB,
                 [ActionDamage(4), ActionTradeRowScrap(),
                 AllyAction(ActionDamage(2))])
BattleStation = OutpostCard('BattleStation', 3, Faction.MACHINE_CULT,
                            [OptionalAction(ActionSelfScrap(ActionDamage(5)))],
                            defence=5)
Battlecruiser = Card('Battlecruiser', 6, Faction.STAR_ALLIANCE,
                     [ActionDamage(5), ActionDrawCard(),
                      AllyAction(ActionAddDiscard()),
                      OptionalAction(ActionSelfScrap(ActionDrawCard(), ActionDestroyBase()))])
BlobCarrier = Card('BlobCarrier', 6, Faction.BLOB,
                   [ActionDamage(7),
                    AllyAction(OptionalAction(ActionBuyCard()))])
BlobDestroyer = Card('BlobDestroyer', 4, Faction.BLOB,
                     [ActionDamage(6),
                      AllyAction(OptionalAction(ActionDestroyBase())),
                      AllyAction(OptionalAction(ActionTradeRowScrap()))])
BLOBFIGHTER = Card('BlobFighter', 1, Faction.BLOB,
                   [ActionDamage(3),
                    AllyAction(ActionDrawCard())])
BlobWheel = BaseCard('BlobWheel', 3, Faction.BLOB,
                     [ActionDamage(1),
                      OptionalAction(ActionSelfScrap(ActionTrade(3)))],
                     defence=5)
BlobWorld = BaseCard('BlobWorld', 8, Faction.BLOB,
                     [OptionalAction(ChooseAction(ActionDamage(5), ActionDrawCardXAllies()))],
                     defence=7)
BrainWorld = OutpostCard('BrainWorld', 8, Faction.MACHINE_CULT,
                         [OptionalAction(ActionScarpDrawCard(2))],
                         defence=6)
CentralOffice = BaseCard('CentralOffice', 7, Faction.TRADE_FEDERATION,
                         [ActionTrade(2), ActionOnTop(),
                          AllyAction(ActionDrawCard())],
                         defence=6)
CommandShip = Card('CommandShip', 8, Faction.TRADE_FEDERATION,
                   [ActionDamage(5), ActionHealth(4), ActionDrawCard(2),
                    AllyAction(OptionalAction(ActionDestroyBase()))])
Corvette = Card('Corvette', 2, Faction.STAR_ALLIANCE,
                [ActionDamage(1), ActionDrawCard(),
                 AllyAction(ActionDamage(2))])
Cutter = Card('Cutter', 2, Faction.TRADE_FEDERATION,
              [ActionHealth(4), ActionTrade(2),
               AllyAction(ActionDamage(4))])
DefenseCenter = OutpostCard('DefenseCenter', 5, Faction.TRADE_FEDERATION,
                     [OptionalAction(ChooseAction(ActionHealth(3), ActionDamage(2))),
                      AllyAction(ActionDamage(2))],
                     defence=5)
Dreadnaught = Card('Dreadnaught', 7, Faction.STAR_ALLIANCE,
                   [ActionDamage(7), ActionDrawCard(),
                    OptionalAction(ActionSelfScrap(ActionDamage(5)))])
EmbassyYacht = Card('EmbassyYacht', 3, Faction.TRADE_FEDERATION,
                    [ActionHealth(3), ActionTrade(2),
                     ActionDrawIfBases(2,2)])
FederationShuttle = Card('FederationShuttle', 1, Faction.TRADE_FEDERATION,
                         [ActionTrade(2),
                          AllyAction(ActionHealth(4))])
Flagship = Card('Flagship', 6, Faction.TRADE_FEDERATION,
                [ActionDamage(5), ActionDrawCard(),
                 AllyAction(ActionHealth(5))])
FleetHQ = BaseCard('FleetHQ', 8, Faction.STAR_ALLIANCE,
                   [], # TODO: all ship get combat
                   defence=8)
Freighter = Card('Freighter', 4, Faction.TRADE_FEDERATION,
                 [ActionTrade(4),
                  AllyAction(ActionOnTop())])
ImperialFighter = Card('ImperialFighter', 1, Faction.STAR_ALLIANCE,
                       [ActionDamage(2), ActionAddDiscard(1),
                        AllyAction(ActionDamage(2))])
ImperialFrigate = Card('ImperialFrigate', 3, Faction.STAR_ALLIANCE,
                       [ActionDamage(4), ActionAddDiscard(1),
                        AllyAction(ActionDamage(4)),
                        OptionalAction(ActionSelfScrap(ActionDrawCard(1)))])
Junkyard = OutpostCard('Junkyard', 6, Faction.MACHINE_CULT,
                       [OptionalAction(ActionScrap())],
                       defence=5)
MachineBase = OutpostCard('MachineBase', 7, Faction.MACHINE_CULT,
                          [OptionalAction(ActionDrawThenScrap())],
                          defence=6)

DEFAULT_PLAYER_DRAW = [VIPER]*3 + [SCOUT]*7
#DEFAULT_PLAYER_DRAW = [copy.copy(c) for c in DEFAULT_PLAYER_DRAW]
DEFAULT_TRADE_PILE = [BLOBFIGHTER]*5 + [BATTLEPOD]*3
#DEFAULT_TRADE_PILE = [copy.copy(c) for c in DEFAULT_TRADE_PILE]

'''
      # Machine Cult
      card TradeBot, 3
      card MissileBot, 3
      card SupplyBot, 3
      card PatrolMech, 2
      card StealthNeedle, 1
      card BattleMech, 1
      card MissileMech, 1
      card BattleStation, 2
      card MechWorld, 1
      card BrainWorld, 1
      card MachineBase, 1
      card Junkyard, 1

      # Star Empire
      card ImperialFighter, 3
      card ImperialFrigate, 3
      card SurveyShip, 3
      card Corvette, 2
      card Battlecruiser, 1
      card Dreadnaught, 1
      card SpaceStation, 2
      card RecyclingStation, 2
      card WarWorld, 1
      card RoyalRedoubt, 1
      card FleetHQ, 1

      # Trade Federation
      card FederationShuttle, 3
      card Cutter, 3
      card EmbassyYacht, 2
      card Freighter, 2
      card CommandShip, 1
      card TradeEscort, 1
      card Flagship, 1
      card TradingPost, 2
      card BarterWorld, 2
      card DefenseCenter, 1
      card CentralOffice, 1
      card PortOfCall, 1

      # Blob
      card BlobFighter, 3
      card TradePod, 3
      card BattlePod, 2
      card Ram, 2
      card BlobDestroyer, 2
      card BattleBlob, 1
      card BlobCarrier, 1
      card Mothership, 1
      card BlobWheel, 3
      card TheHive, 1
      card BlobWorld, 1
'''