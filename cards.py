from __future__ import annotations

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

@dataclass(frozen=True)
class Card:
    name : str
    #type: CardType
    cost: int
    faction: Faction
    actions: List

    def is_ally(self, c: Card):
        return bool(self.faction & c.faction)

    def __eq__(self, other):
        return isinstance(other, Card) and self.name == other.name

    def __lt__(self, other):
        return self.name < other.name

    def __hash__(self):
        return hash(self.name)

@dataclass(frozen=True)
class BaseCard(Card):
    defence: int

    def __eq__(self, other):
        return isinstance(other, Card) and self.name == other.name

    def __hash__(self):
        return hash(self.name)

@dataclass(frozen=True)
class OutpostCard(Card):
    defence: int

    def __eq__(self, other):
        return isinstance(other, Card) and self.name == other.name

    def __hash__(self):
        return hash(self.name)

from actions import *

VIPER = Card('Viper', 0, Faction.UNALIGNED, [ActionDamage(1)])
SCOUT = Card('Scout', 0, Faction.UNALIGNED, [ActionTrade(1)])
EXPLORER = Card('Explorer', 2, Faction.UNALIGNED, [ActionTrade(2),
                                                   ActionSelfScrap(ActionDamage(2))])

BarterWorld = BaseCard('BarterWorld', 4, Faction.TRADE_FEDERATION,
                       [OptionalAction(ChooseAction(ActionTrade(2), ActionHealth(2))),
                        ActionSelfScrap(ActionDamage(5))], defence=4)
BattleBlob = Card('BattleBlob', 6, Faction.BLOB, [ActionDamage(8),
                                                  AllyAction(ActionDrawCard()),
                                                  OptionalAction(ActionSelfScrap(ActionDamage(4)))])
BattleMech = Card('BattleMech', 5, Faction.MACHINE_CULT,
                  [ActionDamage(4),
                   ActionScrap(),
                   AllyAction(ActionDrawCard(1))])
BattlePod = Card('BattlePod', 2, Faction.BLOB,
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
                    AllyAction(OptionalAction(ActionFreeShipCard()))])
BlobDestroyer = Card('BlobDestroyer', 4, Faction.BLOB,
                     [ActionDamage(6),
                      AllyAction(OptionalAction(ActionDestroyBase())),
                      AllyAction(OptionalAction(ActionTradeRowScrap()))])
BlobFighter = Card('BlobFighter', 1, Faction.BLOB,
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
                   [], # every ship played dmg+1 - taken care as special case in engine
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
# ally to all as action...
MechWorld = OutpostCard('MechWorld', 5, Faction.ALL,[],defence=6)
MissileBot = Card('MissileBot', 2, Faction.MACHINE_CULT,
                  [ActionDamage(2), ActionScrap(),
                   AllyAction(ActionDamage(2))])
MissileMech = Card('MissileMech', 6, Faction.MACHINE_CULT,
                   [ActionDamage(6), OptionalAction(ActionDestroyBase()),
                    AllyAction(ActionDrawCard())])
Mothership = Card('Mothership', 7, Faction.BLOB,
                  [ActionDamage(6), ActionDrawCard(),
                   AllyAction(ActionDrawCard())])
PatrolMech = Card('PatrolMech', 4, Faction.MACHINE_CULT,
                  [ChooseAction(ActionTrade(3), ActionDamage(5)),
                   AllyAction(OptionalAction(ActionScrap()))])
PortOfCall = OutpostCard('PortOfCall', 6, Faction.TRADE_FEDERATION,
                         [ActionTrade(3),
                          ActionSelfScrap(ActionDrawCard(), OptionalAction(ActionDestroyBase()))],
                         defence=6)
Ram = Card('Ram', 3, Faction.BLOB,
           [ActionDamage(5),
            AllyAction(ActionDamage(2)),
            ActionSelfScrap(ActionTrade(3))])
RecyclingStation = OutpostCard('RecyclingStation', 4, Faction.STAR_ALLIANCE,
                               [OptionalAction(ChooseAction(ActionTrade(1), ActionDiscardAndDraw(2)))],
                               defence=4)
RoyalRedoubt = OutpostCard('RoyalRedoubt', 6, Faction.STAR_ALLIANCE,
                           [ActionDamage(3),
                            AllyAction(ActionAddDiscard())],
                           defence=6)
SpaceStation = OutpostCard('SpaceStation', 4, Faction.STAR_ALLIANCE,
                           [ActionDamage(2),
                            AllyAction(ActionDamage(2)),
                            ActionSelfScrap(ActionTrade(4))],
                           defence=4)
# TODO: copy ship ability
#StealthNeedle = Card('StealthNeedle', 4, Faction.MACHINE_CULT,
#                     [])
SupplyBot = Card('SupplyBot', 3, Faction.MACHINE_CULT,
                 [ActionTrade(2), ActionScrap(),
                  AllyAction(ActionDamage(2))])
SurveyShip = Card('SurveyShip', 3, Faction.STAR_ALLIANCE,
                  [ActionTrade(1), ActionDrawCard(1),
                   ActionSelfScrap(ActionAddDiscard())])
TheHive = BaseCard('TheHive', 5, Faction.BLOB,
                   [ActionDamage(3),
                    AllyAction(ActionDrawCard(1))],
                   defence=5)
TradeBot = Card('TradeBot', 1, Faction.MACHINE_CULT,
                [ActionTrade(1), ActionScrap(),
                 AllyAction(ActionDamage(2))])
TradeEscort = Card('TradeEscort', 5, Faction.TRADE_FEDERATION,
                   [ActionHealth(4), ActionDamage(4),
                    AllyAction(ActionDrawCard())])
TradePod = Card('TradePod', 2, Faction.BLOB,
                [ActionTrade(3),
                 AllyAction(ActionDamage(2))])
TradingPost = OutpostCard('TradingPost', 3, Faction.TRADE_FEDERATION,
                          [OptionalAction(ChooseAction(ActionHealth(1), ActionTrade(1))),
                           ActionSelfScrap(ActionDamage(3))],
                          defence=4)
WarWorld = OutpostCard('WarWorld', 5, Faction.STAR_ALLIANCE,
                       [ActionDamage(3),
                        AllyAction(ActionDamage(4))],
                       defence=4)

DEFAULT_PLAYER_DRAW = [VIPER]*2 + [SCOUT]*8
TRADE_ROW_CARDS = [
       # Machine Cult
       TradeBot,3,
       MissileBot, 3,
       SupplyBot, 3,
       PatrolMech, 2,
       #StealthNeedle, 1,
       BattleMech, 1,
       MissileMech, 1,
       BattleStation, 2,
       MechWorld, 1,
       BrainWorld, 1,
       MachineBase, 1,
       Junkyard, 1,

       # Star Empire
       ImperialFighter, 3,
       ImperialFrigate, 3,
       SurveyShip, 3,
       Corvette, 2,
       Battlecruiser, 1,
       Dreadnaught, 1,
       SpaceStation, 2,
       RecyclingStation, 2,
       WarWorld, 1,
       RoyalRedoubt, 1,
       FleetHQ, 1,

       # Trade Federation
       FederationShuttle, 3,
       Cutter, 3,
       EmbassyYacht, 2,
       Freighter, 2,
       CommandShip, 1,
       TradeEscort, 1,
       Flagship, 1,
       TradingPost, 2,
       BarterWorld, 2,
       DefenseCenter, 1,
       CentralOffice, 1,
       PortOfCall, 1,

       # Blob
       BlobFighter, 3,
       TradePod, 3,
       BattlePod, 2,
       Ram, 2,
       BlobDestroyer, 2,
       BattleBlob, 1,
       BlobCarrier, 1,
       Mothership, 1,
       BlobWheel, 3,
       TheHive, 1,
       BlobWorld, 1,
]

DEFAULT_TRADE_PILE = []
for card, n in zip(TRADE_ROW_CARDS[::2], TRADE_ROW_CARDS[1::2]):
    DEFAULT_TRADE_PILE.extend([card] * n)

