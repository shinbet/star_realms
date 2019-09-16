
from cards import Card

class UserAction:
    def __eq__(self, other):
        if isinstance(other, self.__class__) and self.__dict__ == other.__dict__:
            return True
        return False

class UserActionPlayCard(UserAction):
    def __init__(self, c: Card):
        self.card = c
    def __str__(self):
        return 'play ' + self.card.name

class UserActionBuyCard(UserAction):
    def __init__(self, c: Card):
        self.card = c
    def __str__(self):
        return f'buy {self.card.name}: ${self.card.cost} {self.card}'

class UserActionAttackFace(UserAction):
    def __str__(self):
        return 'attack user'

class UserActionAttackBase(UserAction):
    def __init__(self, base):
        self.base = base
    def __str__(self):
        return 'attack base'

class UserActionAttackOutpost(UserAction):
    def __init__(self, outpost):
        self.outpost = outpost
    def __str__(self):
        return 'attack outpost'

class UserActionCardAction(UserAction):
    def __init__(self, c, a):
        self.card = c
        self.action = a
    def __str__(self):
        return f'{self.action} from: {self.card}'

class UserActionPlayAllCards(UserAction):
    def __init__(self, actions):
        self.actions = actions
    def __str__(self):
        return 'play all cards'

class UserActionDone(UserAction):
    def __str__(self):
        return 'turn done'

USER_ACTION_DONE = UserActionDone()


class UndoMove(Exception):
    pass