import asyncio
from queue import Queue
from threading import Thread

from aiohttp import web
import logging

from cards import Card
from engine import Game
from pile import Pile
from players.player import Player

STOP_GAME = object()

async def handle_index(request):
    return web.FileResponse('static/index.html')

#routes = web.RouteTableDef()

#@routes.get('/card/{name}')
async def handle_card_image(request):
    card = request.match_info['name']
    fname = CARD_TO_FILENAME[card]
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
                t = Thread(target=game.run)
                await ws.send_json(['status', 'game started'])
                t.start()
            elif event == 'choose_action':
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

    def send_state(self, b: Game, p_other: Player):
        state = {'trade_pile': [_card_to_json(c) for c in b.trade_pile]}
        state['player'] = _player_to_json(self)
        other = _player_to_json(p_other)
        # todo: need to restrict some data
        state['other_player'] = other

        self.send_msg('game_state', state)

    def choose_action(self, b: Game, p_other: Player, actions):
        self.send_state(b, p_other)
        self.send_msg('choose_action', {str(n): str(a) for n, a in enumerate(actions, 1)})
        event, msg = self.get_msg()
        print(event, msg)
        i = msg['action']
        return actions[int(i)-1]

    def do_choose_from_piles(self, action, piles: [Pile], min_n, max_n):
        self.send_msg('choose_piles', {'action':action, 'piles':[p.name for p in piles], 'min':min_n, 'max':max_n})
        event, msg = self.get_msg()
        print(event, msg)
        pile = (p for p in piles if p.name == msg['pile']).next()
        candidates = list(Pile)
        cards = []
        for chosen in msg['cards']:
            card = (c for c in candidates if c.name == chosen).next()
            cards.append(card)
            candidates.remove(card)
        return pile, cards


app = web.Application()
app.add_routes([web.get('/', handle_index),
                web.static('/static', './static/', show_index=True),
                web.get('/card/{name}', handle_card_image),
                web.get('/ws', wshandle),
                ])

CARD_TO_FILENAME = {
    'TradeBot': 'Trade-Bot-214x300.jpg',
    'MissileBot': 'Missile-Bot-214x300.jpg',
    'SupplyBot': 'Supply-Bot-214x300.jpg',
    'PatrolMech': 'Patrol-Mech-214x300.jpg',
    'StealthNeedle': 'Stealth-Needle-214x300.jpg',
    'BattleMech': 'Battle-Mech-214x300.jpg',
    'MissileMech': 'Missile-Mech-214x300.jpg',
    'BattleStation': 'Battle-Station-300x214.jpg',
    'MechWorld': 'Mech-World-300x214.jpg',
    'BrainWorld': 'Brain-World-300x214.jpg',
    'MachineBase': 'Machine-Base-300x214.jpg',
    'Junkyard': 'Junkyard-300x214.jpg',
    'ImperialFighter': 'Imperial-Fighter-214x300.jpg',
    'ImperialFrigate': 'Imperial-Frigate-214x300.jpg',
    'SurveyShip': 'Survey-Ship-214x300.jpg',
    'Corvette': 'Corvette-214x300.jpg',
    'Battlecruiser': 'Battlecruiser-214x300.jpg',
    'Dreadnaught': 'Dreadnaught-214x300.jpg',
    'SpaceStation': 'Space-Station-300x214.jpg',
    'RecyclingStation': 'Recycling-Station-300x214.jpg',
    'WarWorld': 'War-World-300x214.jpg',
    'RoyalRedoubt': 'Royal-Redoubt-300x214.jpg',
    'FleetHQ': 'Fleet-HQ-300x214.jpg',
    'FederationShuttle': 'Federation-Shuttle-214x300.jpg',
    'Cutter': 'Cutter-214x300.jpg',
    'EmbassyYacht': 'Embassy-Yacht-214x300.jpg',
    'Freighter': 'Freighter-214x300.jpg',
    'CommandShip': 'Command-Ship-214x300.jpg',
    'TradeEscort': 'Trade-Escort-214x300.jpg',
    'Flagship': 'Flagship-214x300.jpg',
    'TradingPost': 'Trading-Post-300x214.jpg',
    'BarterWorld': 'Barter-World-300x214.jpg',
    'DefenseCenter': 'Defense-Center-300x214.jpg',
    'CentralOffice': 'Central-Office-300x214.jpg',
    'PortOfCall': 'Port-Of-Call-300x214.jpg',
    'BlobFighter': 'Blob-Fighter-214x300.jpg',
    'TradePod': 'Trade-Pod-214x300.jpg',
    'BattlePod': 'Battle-Pod-214x300.jpg',
    'Ram': 'Ram-214x300.jpg',
    'BlobDestroyer': 'Blob-Destroyer-214x300.jpg',
    'BattleBlob': 'Battle-Blob-214x300.jpg',
    'BlobCarrier': 'Blob-Carrier-214x300.jpg',
    'Mothership': 'Mothership-214x300.jpg',
    'BlobWheel': 'Blob-Wheel-300x214.jpg',
    'TheHive': 'The-Hive-300x214.jpg',
    'BlobWorld': 'Blob-World-300x214.jpg',
    'Viper': 'Viper-214x300.jpg',
    'Scout': 'Scout-214x300.jpg',
    'Explorer': 'Explorer-214x300.jpg',
}

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    web.run_app(app)