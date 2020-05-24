import asyncio
import functools
from queue import Queue
from threading import Thread

from aiohttp import web
import logging

from cards import Card
from engine import Game, UserActionPlayCard, UserActionPlayAllCards
from pile import Pile
from players.player import Player

STOP_GAME = object()

async def handle_index(request):
    return web.FileResponse('static/index2.html')

@functools.lru_cache(maxsize=None)
def card_to_fname(card, ext):
    # file name: 'MissileBot' -> 'Missile-Bot-214x300.jpg'
    res = []
    next_c = 1
    for i, c in enumerate(card):
        if i > next_c and c.isupper():
            res.append('-')
            next_c = i+1 # skip next... HQ stays HQ, not H-Q
        res.append(c)
    return ''.join(res) + ext

async def handle_card_image(request):
    card = request.match_info['name']
    fname = card_to_fname(card, ext='-214x300.jpg')
    return web.FileResponse(f'static/cards/{fname}')

async def handle_base_image(request):
    card = request.match_info['name']
    fname = card_to_fname(card, ext='-300x214.jpg')
    return web.FileResponse(f'static/cards/{fname}')


async def wshandle(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    game = None

    log = logging.getLogger(request.remote)

    async for msg in ws:
        log.info('got: %s', msg)
        if msg.type == web.WSMsgType.text:
            event, data = msg.json()
            if event == 'start_game':
                if game:
                    p1._q.put(STOP_GAME)
                    # should really not do this...
                    t.join()

                from players.monte_carlo import MCSimplePlayer

                p1 = WebPlayer(ws, 'p1')
                # p2 = InteractivePlayer('p2')
                p2 = MCSimplePlayer('p2')

                game = Game([p1, p2], seed=666)
                p1.game = game
                p1.other = p2
                t = Thread(target=game.run)
                await ws.send_json(['status', 'game started'])
                t.start()
            elif event in ('choose_action', 'choose_piles'):
                # TODO: check game is started...
                p1._q.put([event, data])
            else:
                log.warning('unknown event: %s; data=%s', event, data)
        #elif msg.type == web.WSMsgType.binary:
        #    await ws.send_bytes(msg.data)
        elif msg.type == web.WSMsgType.close:
            break
        else:
            log.warning('unknown message type:', msg)
    return ws


def _card_to_json(c: Card):
    return {'name':c.name, 'cost': c.cost, 'actions': str(c.actions)}

def _player_to_json(p: Player):
    return {
        'name': p.name, 'health': p.health, 'discard': p.discard,
        'trade': p.trade, 'damage': p.damage,
        'hand': [_card_to_json(c) for c in p.hand],
        'bases': [_card_to_json(c) for c in p.bases],
        'outposts': [_card_to_json(c) for c in p.outposts],
        'draw_pile': [_card_to_json(c) for c in p.draw_pile],
        'discard_pile': [_card_to_json(c) for c in p.discard_pile],
        'in_play': [_card_to_json(c) for c in p.in_play]
}
class WebPlayer(Player):
    def __init__(self, ws, *args, **kwargs):
        super(WebPlayer, self).__init__(*args, **kwargs)
        self._q = Queue()
        self._ws = ws
        self._log = logging.getLogger(f'player {self.name}')

        # need to be set after
        self.game = None
        self.other = None

    def send_msg(self, event, msg):
        #app._loop.rucall_soon_threadsafe(self._ws.send_json, [event, msg])
        async def send():
            return await self._ws.send_json([event, msg])

        future = asyncio.run_coroutine_threadsafe(send(), app._loop)
        # Wait for the result:
        result = future.result()
        self._log.info('sent %s', [event, msg])

    def get_msg(self):
        d = self._q.get()
        self._log.info('got %s', d)
        if d is STOP_GAME:
            raise Exception('stop game')
        return d

    def get_state(self, b: Game, p_other: Player):
        state = {'trade_pile': [_card_to_json(c) for c in b.trade_pile]}
        state['player'] = _player_to_json(self)
        other = _player_to_json(p_other)
        # todo: need to restrict some data
        state['other_player'] = other
        return state

    def send_state(self, b: Game, p_other: Player):
        self.send_msg('game_state', self.get_state(b, p_other))

    def choose_action(self, b: Game, p_other: Player, actions):
        self.send_state(b, p_other)
        self.send_msg('choose_action', {str(n): str(a) for n, a in enumerate(actions, 1)})
        event, msg = self.get_msg()
        print(event, msg)
        i = msg['action']
        if i =='all':
            return UserActionPlayAllCards([a for a in actions if isinstance(a, UserActionPlayCard)])
        return actions[int(i)-1]

    def do_choose_from_piles(self, action, piles: [Pile], min_n, max_n):
        self.send_state(self.game, self.other)
        self.send_msg('choose_piles', {'action':action, 'piles':[p.name for p in piles], 'min':min_n, 'max':max_n})
        event, msg = self.get_msg()
        print(event, msg)
        pile_name = msg['pile']
        pile = None
        cards = []
        if pile_name:
            pile = next(p for p in piles if p.name == pile_name)
            candidates = list(pile)
            for chosen in msg['cards']:
                card = next(c for c in candidates if c.name == chosen)
                cards.append(card)
                candidates.remove(card)
        return pile, cards

    def won(self, b, other):
        s = self.get_state(b, other)
        self.send_msg('player_won', s)

    def lost(self, b, other):
        s = self.get_state(b, other)
        self.send_msg('player_lost', s)


app = web.Application()
app.add_routes([web.get('/', handle_index),
                web.static('/static', './static/', show_index=True),
                web.get('/card/{name}', handle_card_image),
                web.get('/base/{name}', handle_base_image),
                web.get('/ws', wshandle),
                ])

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    web.run_app(app)