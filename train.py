import glob
import json
import multiprocessing
import os
import random
import re
import sys
import time

import torch
from torch import nn
from torch.nn import MSELoss
from torch.utils.data import DataLoader

from engine import Game
from match import Bench, make_player, RoundRobin
from players.NN.NNSimple import NNSimplePlayer
from players.NN.NNUCTPlayer import NNUCTPlayer, Net
from players.NN.utils import GamesDataset, ToTensor
import logging

log = logging.getLogger(__file__)

class LinearNet(nn.Module):
    def __init__(self, layers):
        super().__init__()
        l = nn.ModuleList()
        in_p = layers[0]
        for out_p in layers:
            l.append(nn.Linear(in_p, out_p))
            l.append(nn.ReLU())
            in_p = out_p
        l.append(nn.Linear(in_p, 1))
        l.append(nn.Tanh())
        self.layers = l
        self.layers_conf = layers

    def forward(self, x):
        if type(x) == list:
            x = torch.tensor(x).unsqueeze(0)

        for l in self.layers:
            x = l(x)
        return x

def last_model(dname):
    return max(glob.glob(os.path.join(dname, 'model_*.pt')))

def last_model_id(dname):
    return re.match(r'.*_(\d+).pt', last_model(dname)).groups()[0]

def load_net(*fname):
    if isinstance(fname[-1], int):
        fname = fname[:-1] + [fname_from_id(fname[-1])]

    data = torch.load(os.path.join(*fname))
    if not isinstance(data, dict) or 'layers_conf' not in data:
        model = Net()
        model.load_state_dict(data)
    else:
        model = LinearNet(data['layers_conf'])
        model.load_state_dict(data['model_state'])
    return model

def save_model(model, *fname):
    data = {
        'layers_conf': model.layers_conf,
        'model_state': model.state_dict(),
    }
    torch.save(data, os.path.join(*fname))
    log.info('model saved: %s', fname)

def fname_from_id(id_):
    return 'model_{:05}.pt'.format(int(id_))

def load_from_name(name):
    run, netid = name.split()
    nn = load_net('run_{}/{}'.format(run, fname_from_id(netid)))
    return nn

'''
def load_checkpoint(fname):
    model = Net()
    checkpoint = torch.load(fname)
    model.load_state_dict(checkpoint['model_state_dict'])
    optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    epoch = checkpoint['epoch']
    loss = checkpoint['loss']

    model.eval()
    # - or -
    model.train()
'''

WORKER_NN = None
WORKER_MODEL_ID = None
WORKER_DNAME = None
def game_gen_worker(*args):
    global WORKER_NN
    if not WORKER_NN:
        WORKER_NN = load_net(WORKER_DNAME, fname_from_id(WORKER_MODEL_ID))
        WORKER_NN.eval()
    nn = WORKER_NN

    p1 = NNSimplePlayer('p1', nn=nn, train=True)
    p2 = NNSimplePlayer('p2', nn=nn, train=True)
    g = Game(players=[p1, p2], verbose=False)
    winner = g.run()
    extra = str(random.randint(1,1000))
    for _ in range(5):
        try:
            fname = '{:05}_{}_{}__{}.json'.format(WORKER_MODEL_ID, int(time.time()), extra, len(p1._states) + len(p2._states))
            fname = os.path.join(WORKER_DNAME, fname)
            with open(fname, 'x') as f:
                json.dump({'p1_s': p1._states, 'p2_s': p2._states, 'w': 0 if p1 == winner else 1}, f)
                log.info('wrote %s', fname)
            break
        except FileExistsError:
            log.info('file exists')
            extra = str(random.randint(1,1000))

def gen_training(dname, model_id, conf):
    global WORKER_MODEL_ID, WORKER_DNAME, WORKER_ROLLOUTS
    WORKER_MODEL_ID = int(model_id)
    WORKER_DNAME = dname
    #WORKER_ROLLOUTS = conf['rollouts

    pool = multiprocessing.Pool(conf['workers'])
    pool.map(game_gen_worker, range(conf['num']))
    pool.close()
    pool.join()

'''
CONFIG = {
    'net': {
        'version': 1,
        'layers': [142, 142, 71],
    },
    'games': {
        'num': 2000,
        'workers': 4,
    },
    'bench': {
        'num': 2000,
        'workers': 4,
        'type': 'bench',
    },
    'train': {
        'epocs': 200,
        'batch_size': 32,
        'discount': None,
        'lr': 1e-3,
        'samples': 0.01,
    }
}
'''

def train(model, datafiles, conf):

    loss_func = MSELoss()
    #opt = torch.optim.SGD(model.parameters(), lr=1e-4)
    opt = torch.optim.Adam(model.parameters(), lr=conf['lr'], weight_decay=conf['weight_decay'])

    ds = GamesDataset(*datafiles, discount=conf['discount'])
    #ds = GamesDataset(*datafiles)

    epochs = conf['epochs']

    # we want ~4 samples from each game
    #num_samples = len(ds) // (epochs * 200)
    num_samples = int(len(ds) * conf['samples'])

    sampler = torch.utils.data.RandomSampler(ds, replacement=True, num_samples=num_samples)
    train_dl = DataLoader(ds, batch_size=conf['batch_size'], sampler=sampler)

    running_loss = 0.0
    n_loss = 0
    for epoch in range(epochs):
        for xb, yb in train_dl:
            opt.zero_grad()
            pred = model(xb)
            yb = yb.view(-1, 1)
            loss = loss_func(pred, yb)
            loss.backward()
            opt.step()

            running_loss += loss.item()
            n_loss += 1
        #if epoch % 40 == 0:
        print(epoch, running_loss/n_loss)
        running_loss = 0.0
        n_loss = 0

    return model

def do_bench(args):
    dname = args.dir
    with open(os.path.join(dname, 'conf.json'), 'r') as f:
        conf = json.load(f)
    conf = conf['bench']
    conf['type'] = 'rr' if args.tourney else 'bench'
    conf['num'] = args.games
    bench(dname, args.ids, conf)

def bench(dname, ids, conf):
    p = [make_player(NNSimplePlayer, id_, nn=load_net(dname, fname_from_id(id_))) for id_ in ids]

    from players.random_player import RandomPlayer, WEIGHT_MAP26
    #p.append(make_player(SimplePlayer, 'simple'))
    if conf['type'] == 'rr':
        b = RoundRobin(p)
    else:
        b = Bench(p)
    b.run(conf['num'])
    b.summary()


def train_loop(args):
    dname = args.dir
    with open(os.path.join(dname, 'conf.json'), 'r') as f:
        conf = json.load(f)

    try:
        model_id = int(last_model_id(dname))
        model = load_net(dname, fname_from_id(model_id))
    except ValueError:
        log.info('no existing model found - starting new run!')
        model_id = 0
        model = LinearNet(conf['net']['layers'])
        save_model(model, dname, fname_from_id(model_id))

    for i in range(args.loops):
        log.info('starting loop %s', i)
        model.train(False)
        gen_training(dname, model_id, conf['games'])

        datafiles = [os.path.join(dname, '{:05}_'.format(m_id)) for m_id in range(model_id, -1, -1)[:3]]
        model.train(True)
        model = train(model, datafiles, conf['train'])

        model_id += 1
        save_model(model, dname, fname_from_id(model_id))

        bench(dname, list(range(model_id, -1, -1)[:3]), conf['bench'])


def get_parser():
    from argparse import ArgumentParser

    parser = ArgumentParser(description='NN player training')
    parser.add_argument('dir', help='training run dir')

    subparsers = parser.add_subparsers(help='sub-command help')
    '''
    
    gen = subparsers.add_parser('gen', help="generate training data")
    gen.add_argument('run', help='training run')
    gen.add_argument('-n', '--num-games', type=int, default=99999, help='number of games to generate')
    gen.add_argument('--net', type=int, default=None, help='net id')
    gen.add_argument('-r', '--rollouts', type=int, default=50, help='node rollouts')
    gen.add_argument('-p', '--workers', type=int, default=4, help='workers')
    gen.set_defaults(func=gen_training)

    train_p = subparsers.add_parser('train', help="train model on data")
    train_p.add_argument('run', help='training run')
    train_p.set_defaults(func=train)

    bench_p = subparsers.add_parser('bench', help="bench")
    bench_p.add_argument('run', help='training run')
    bench_p.add_argument('ids', nargs='+', help='models')
    bench_p.add_argument('-n', '--games', type=int, default=200, help='number of games to run against each')
    bench_p.add_argument('-t', '--tourney', default=False, action='store_true', help='full round robin tournament')
    bench_p.set_defaults(func=bench)
    '''

    loop = subparsers.add_parser('loop', help="generate training data and train")
    #loop.add_argument('run', help='training run')
    loop.add_argument('-l', '--loops', type=int, default=5, help='number of loops')
    loop.set_defaults(func=train_loop)

    bench_p = subparsers.add_parser('bench', help="bench")
    #bench_p.add_argument('run', help='training run')
    bench_p.add_argument('ids', nargs='+', help='models')
    bench_p.add_argument('-n', '--games', type=int, default=200, help='number of games to run against each')
    bench_p.add_argument('-t', '--tourney', default=False, action='store_true', help='full round robin tournament')
    bench_p.set_defaults(func=do_bench)

    return parser

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    parser = get_parser()
    args = parser.parse_args()
    args.func(args)
