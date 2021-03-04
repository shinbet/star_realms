from cards import Card, OutpostCard, BaseCard


class UserAction:
    def __eq__(self, other):
        if isinstance(other, self.__class__) and self.__dict__ == other.__dict__:
            return True
        return False
    def __repr__(self):
        return str(self)
    def __hash__(self):
        return hash(str(self))

class UserActionPlayCard(UserAction):
    def __init__(self, c: Card):
        self.card = c
    def __str__(self):
        return 'play ' + self.card.name

class UserActionBuyCard(UserAction):
    def __init__(self, c: Card):
        self.card = c
    def __str__(self):
        return f'buy {self.card.name}' #: ${self.card.cost} {self.card}'
    def __repr__(self):
        return f'buy {self.card.name}'

class UserActionAttackFace(UserAction):
    def __str__(self):
        return 'attack user'

class UserActionAttackBase(UserAction):
    def __init__(self, base: BaseCard):
        self.base = base
    def __str__(self):
        return 'attack base: ' + self.base.name

class UserActionAttackOutpost(UserAction):
    def __init__(self, outpost: OutpostCard):
        self.outpost = outpost
    def __str__(self):
        return 'attack outpost: ' + self.outpost.name

class UserActionCardAction(UserAction):
    def __init__(self, c, a):
        self.card = c
        self.action = a
    def __str__(self):
        return f'{self.action} from: {self.card}'
    def __repr__(self):
        return repr(self.action)

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