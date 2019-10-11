import random

import numpy as np

from engine import Game
from players.player import Player
from user_actions import UserActionDone, UserActionPlayCard, UserActionBuyCard, UserActionAttackOutpost, \
    UserActionAttackFace, UserActionAttackBase, UserActionCardAction

import logging
log = logging.getLogger(__name__)

RANDOM_MAP = {}

WEIGHT_MAP = {
    UserActionPlayCard: 100,
    UserActionAttackOutpost: 60,
    UserActionAttackFace: 60,
    UserActionAttackBase: 30,
    UserActionBuyCard: 20,
    UserActionCardAction: 10,
    UserActionDone: 1,
}

ACTIONS = [UserActionPlayCard,
           UserActionAttackOutpost,
           UserActionAttackFace,
           UserActionAttackBase,
           UserActionBuyCard,
           UserActionCardAction,
           UserActionDone]


WEIGHT_MAP29 = {a:v for a,v in zip(ACTIONS, [100, 60, 60, 81, 7, 89, 1])}
WEIGHT_MAP26 = {a:v for a,v in zip(ACTIONS, [100,60,96,81,7,89,1])}

WEIGHT_MAP_t1 = {a:v for a,v in zip(ACTIONS, [100,50,50,60,20,88,1])}
WEIGHT_MAP_t2 = {a:v for a,v in zip(ACTIONS, [100,85,50,60,20,23,1])}

'''
    PLAYER      %  GAMES      W      L
      lr26  55.31   1600    885    715
      lr29  53.87   1600    862    738
        t1  48.19   1600    771    829
        t2  48.19   1600    771    829
      mine  44.44   1600    711    889
'''

#ALL_ACTIONS = set()
'''
{'play Viper', 'choose one of: (damage:5, Draw a card for each ally played)', 'play Ram', 'play TheHive',
 'play BlobFighter', 'Destroy target base', 'attack outpost: TradingPost', 'buy DefenseCenter',
 'scrap up to 2 cards from discard or hand and draw as many cards', 'play BlobWorld', 'buy Cutter',
 'attack outpost: DefenseCenter', 'trade:3', 'attack outpost: MechWorld', 'play StealthNeedle', 'play BattlePod',
 'buy Freighter', 'attack outpost: RoyalRedoubt', 'buy FleetHQ', 'buy BattleMech', 'play EmbassyYacht', 'buy BlobWheel',
 'buy BlobFighter', 'buy BlobCarrier', 'attack outpost: BattleStation', 'get free ship and put on top of draw pile',
 'play Corvette', 'play CommandShip', 'buy ImperialFrigate', 'play Explorer', 'play WarWorld',
 'attack outpost: MachineBase', 'attack base: BarterWorld', 'buy SurveyShip', 'play DefenseCenter', 'buy BarterWorld',
 'buy TradePod', 'health:1', 'scrap self, then:(Draw card,)', 'scrap from hand or discard pile',
 'scrap self, then:(trade:3,)', 'buy RecyclingStation', 'play MachineBase', 'attack base: CentralOffice', 'health:3',
 'Draw card then scrap from hand', 'buy MechWorld', 'buy PortOfCall', 'buy EmbassyYacht', 'buy ImperialFighter',
 'scrap from trade row', 'scrap self, then:(Target opponent discards a card,)', 'buy PatrolMech', 'play BarterWorld',
 'buy MissileMech', 'buy Battlecruiser', 'buy TradeBot', 'play BlobCarrier', 'play ImperialFrigate', 'buy TheHive',
 'play BlobDestroyer', 'damage:5', 'play MechWorld', 'play Flagship', 'play FederationShuttle', 'attack base: FleetHQ',
 'buy MissileBot', 'play RecyclingStation', 'attack user', 'play TradePod', 'trade:1', 'buy WarWorld',
 'choose one of: (health:1, trade:1)', 'play BlobWheel', 'attack base: TheHive', 'attack base: BlobWheel',
 'play MissileBot', 'buy TradeEscort', 'buy BlobWorld', 'buy MachineBase', 'play Freighter', 'play CentralOffice',
 'play BattleMech', 'turn done', 'buy Flagship', 'buy BattleStation', 'buy SpaceStation',
 'scrap self, then:(Draw card, Optional: Destroy target base)', 'play TradeEscort', 'Draw a card for each ally played',
 'buy Ram', 'damage:2', 'scrap self, then:(damage:4,)', 'buy CentralOffice', 'play BattleBlob', 'buy Mothership',
 'play SpaceStation', 'play BattleStation', 'attack outpost: RecyclingStation', 'play PortOfCall',
 'scrap self, then:(damage:5,)', 'buy CommandShip',
 'choose one of: (trade:1, discard up to 2 cards from hand and draw as many cards)', 'buy StealthNeedle',
 'discard up to 2 cards from hand and draw as many cards', 'scrap self, then:(damage:3,)', 'play Dreadnaught',
 'buy Dreadnaught', 'play TradeBot', 'play Junkyard', 'play TradingPost', 'buy BrainWorld', 'play RoyalRedoubt',
 'buy RoyalRedoubt', 'buy Corvette', 'play ImperialFighter', 'scrap self, then:(Draw card, Destroy target base)',
 'play Scout', 'buy SupplyBot', 'attack outpost: Junkyard', 'play MissileMech', 'buy Junkyard', 'play BrainWorld',
 'scrap self, then:(damage:2,)', 'buy FederationShuttle', 'attack outpost: BrainWorld', 'play FleetHQ', 'play Cutter',
 'trade:2', 'buy Explorer', 'scrap self, then:(trade:4,)', 'play PatrolMech', 'attack outpost: WarWorld',
 'play SupplyBot', 'buy BattleBlob', 'attack base: BlobWorld', 'choose one of: (health:3, damage:2)', 'buy BattlePod',
 'play SurveyShip', 'attack outpost: PortOfCall', 'buy BlobDestroyer', 'play Battlecruiser', 'health:2',
 'choose one of: (trade:2, health:2)', 'buy TradingPost', 'play Mothership', 'attack outpost: SpaceStation'}
'''

class RandomPlayer(Player):
    def __init__(self, name, health=50, draw_pile=None, discard_pile=None, bases=None, hand=None, outposts=None, w={}):
        super().__init__(name, health, draw_pile, discard_pile, bases, hand, outposts)
        self.weights = w

    def choose_action(self, b, p_other, actions):
        w = self.weights
        weights = [w.get(type(a), 5) for a  in actions]

        # REMOVE ME:
        #ALL_ACTIONS.update(repr(a) for a in actions)
        #print()
        #for a,w in zip(actions, weights):
        #    print(f' {w}: {a}')
        return random.choices(actions, weights=weights)[0]

    choose_card_action = choose_action

    def do_choose_from_piles(self, action, piles, min_n, max_n):
        n = random.randint(min_n, max_n)
        if not n:
            return None, None
        pile = random.choice(piles)
        n = min(n, len(pile))
        cards = random.sample(pile, n)
        return pile, cards


def run_match(x: np.ndarray):
    w = {k:v for k,v in zip(ACTIONS, x)}
    win = {'p1': 0, 'p2': 0}
    for i in range(100):
        p1 = RandomPlayer('p1',w=WEIGHT_MAP)
        p2 = RandomPlayer('p2', w=w)
        players = [p1, p2]
        if i % 2:
            players = players[::-1]
        g = Game(players, seed=None, verbose=False)
        try:
            winner = g.run()
            win[winner.name] += 1
        except:
            log.exception('error running game')
    pct = win['p1']/(win['p1']+win['p2'])
    #log.info('match win ratio: %s', pct)
    return pct

def simple_match():

    win = {'p1':0, 'p2':0}
    for i in range(500):
        p1 = RandomPlayer('p1')
        p2 = RandomPlayer('p2', w=WEIGHT_MAP29)
        players = [p1,p2]
        if i%2:
            players = players[::-1]
        g = Game(players, seed=None)
        winner = g.run()
        win[winner.name] += 1
        print(win)
    print(win)

def callback(x, f, context):
    log.info('callback: x=%s, f=%s, context=%s', x,f,context)

def optimize():
    from scipy.optimize import dual_annealing
    bounds = [(0,100)] * len(ACTIONS)
    x0 = np.array(list(WEIGHT_MAP.values()))
    res = dual_annealing(run_match, bounds, x0=x0, callback=callback)
    print('*'*10)
    print(res)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    optimize()