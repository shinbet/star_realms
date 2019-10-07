from __future__ import annotations

import copy
import math
import random
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple

from cards import Card
from engine import Game
from pile import Pile
from players.player import Player
from players.random_player import RandomPlayer
from user_actions import UserActionDone, UserActionPlayCard, UserActionBuyCard, UserActionAttackOutpost, \
    UserActionAttackFace, UserActionAttackBase, UserActionCardAction, UserAction


@dataclass
class UCTNode:
    #game: Game = None
    action: Optional[UserAction] = None
    #self.is_expanded = False
    parent: Optional[UCTNode] = None
    children: Dict[UserAction, UCTNode] = None
    player: TreePlayer = None
    visits: int = 0
    total_value: int = 0

    def add_child(self, action, prior=0):
        self.children[action] = UCTNode(parent=self, action=action) #, prior=prior)

    def Q(self):  # returns float
        return self.total_value / (1 + self.visits)

    def U(self):  # returns float
        #return (math.sqrt(self.parent.number_visits)  * self.prior / (1 + self.number_visits))
        return math.sqrt(math.log(self.parent.visits) / (1 + self.visits))

    def __str__(self):
        if self.parent:
            return f'Action: {self.action} Tot:{self.total_value} Visits:{self.visits} Q:{self.Q()} U:{self.U()}'
        else:
            return f'root node Tot:{self.total_value} Visits:{self.visits}'

def dump_children(nodelist):
    for c in nodelist:
        print(c)

def node_path(n):
    a = []
    while n.parent:
        a.append(n.action)
        n = n.parent
    return reversed(a)

def best_child(children, C):
    return max(children.items(), key=lambda action_child: action_child[1].Q() + C*action_child[1].U())

class DoneExpantion(Exception):
    def __init__(self, game, leaf):
        self.game = game
        self.leaf = leaf

class TreePlayer(RandomPlayer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.transpositions = {}

    def choose_action(self, game: Game, p_other, actions):
        current = self._path[-1]

        if current.children is None:
            trans_key = hash(game)
            # check transposition table
            n = self.transpositions.get(trans_key)
            if n:
                '''
                print('found transposition: ')
                print('cur:\n' + '\n'.join(str(p.action) for p in self._path[1:]))
                print('old:\n' + '\n'.join(str(a) for a in node_path(n)))
                '''
                self._path[-1] = n
                current.parent.children[current.action] = n
                current = n
            else:
                self.transpositions[trans_key] = current
                #current.children = {a:UCTNode(a, current, None, self) for a in actions}
                raise DoneExpantion(game, current)

        children = current.children
        masked_children = {}
        for a in actions:
            n = children.get(a)
            if not n:
                # new option
                n = UCTNode(a, current, None, player=self)
                children[a] = n
            masked_children[a] = n

        a, child = best_child(masked_children, self._C)
        #print('options are:')
        #dump_children(masked_children.values())
        #print(f'chosen: {a}')

        self._path.append(child)
        return a


def leaf_expand(node: UCTNode, actions):
    if node.children is None:
        node.children = []
    for a in actions:
        node.add_child(action=a)

def backup(node: UCTNode, value_estimate: float):
    current = node
    # Child nodes are multiplied by -1 because we want max(-opponent eval)
    turnfactor = 1 #-1
    while current.parent is not None:
        current.visits += 1
        current.total_value += (value_estimate * turnfactor)
        # we dont switch sides every move
        if current.parent.player != current.player:
            turnfactor *= -1
        current = current.parent
    current.visits += 1
    current.total_value += (value_estimate * turnfactor)

class UCTPlayer(Player):

    def __init__(self, name, *args, num_rollouts=800, C=3.4, **kwargs):
        super().__init__(name, *args, **kwargs)
        self._num_rollouts = num_rollouts
        self._C = C

    def do_choose_from_piles(self, action, piles, min_n=0, max_n=1, ship_only=False):
        n = random.randint(min_n, max_n)
        if not n:
            return None, None
        pile = random.choice(piles)
        n = min(n, len(pile))
        cards = random.sample(pile, n)
        return pile, cards

    def choose_card_action(self, b, p_other, actions):
        # fixme: need to be part of rollout, or combine it with parent action
        return random.choice(actions)

    def choose_action(self, o_game, p_other, actions):

        me, other = TreePlayer('tp1'), TreePlayer('tp2')
        me._C = other._C = self._C

        new_players = [me, other]
        if o_game.players[0] != self:
            new_players.reverse()

        root = UCTNode(None, None, {}, visits=1, player=me)

        for _ in range(self._num_rollouts):
            game = copy.copy(o_game)
            me._path = other._path = [root]  # must share same list

            # copy player state
            for o_p, p in zip(game.players, new_players):
                p.from_player(o_p)
            game.players = new_players
            game.verbose = False

            try:
                winner = game.run()
            except DoneExpantion as e:
                leaf = e.leaf

                leaf.children = {}
                # evaluate leaf
                if leaf.player == me:
                    score = self.eval_state(game, me, other)
                else:
                    score = self.eval_state(game, other, me)
            else:
                # won
                leaf = me._path[-1] # both have same path
                score = 1

            # backprop
            backup(leaf, score)

            '''
            print('rollout was:')
            for n in me._path[1:]:
                print(f'p{n.player}: {n.action}')
            print()
            '''

        a, node = max(root.children.items(), key=lambda item: (item[1].visits, item[1].Q()))
        return a

    def eval_state(self, game: Game, p1, p2):
        return p1.health / p2.health

class RandomRolloutUctPlayer(UCTPlayer):
    def eval_state(self, game: Game, p1, p2):
        from players.random_player import RandomPlayer, WEIGHT_MAP26

        p1 = RandomPlayer('rr1', w=WEIGHT_MAP26)
        p2 = RandomPlayer('rr2', w=WEIGHT_MAP26)
        players = [p1, p2]
        for o_p, p in zip(game.players, players):
            p.from_player(o_p)
        g = copy.copy(game)
        g.players = players
        winner = g.run()
        return 1 if winner is p1 else -1

if __name__ == '__main__':

    p1 = UCTPlayer('p1')
    p2 = RandomRolloutUctPlayer('p2')
    players = [p1,p2]

    #g = Game(players, seed=None)
    from players.interactive_player import InteractivePlayer
    #import sys
    #sys.modules['__main__.interactive_player'] = InteractivePlayer

    import pickle
    with open('2019_09_25__21_41.pkl', 'rb') as f:
        g = pickle.load(f)
    for p_o, p in zip(g.players, players):
        p.from_player(p_o)
    g.players = players
    winner = g.run()
