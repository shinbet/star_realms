import glob
import json
import multiprocessing
import random
import re
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

def last_model(dname):
    return max(glob.glob(dname + 'model_*.pt'))

def last_model_id(dname):
    return re.match(r'.*_(\d+).pt', last_model(dname)).groups()[0]

def load_net_or_create(dname):
    fname = dname + 'model.pt'
    try:
        model = load_net(fname)
    except FileNotFoundError:
        model = Net()
        save_model(model, fname)
    return model

def load_net(fname):
    model = Net()
    model.load_state_dict(torch.load(fname))
    return model

def save_model(model, fname):
    torch.save(model.state_dict(), fname)
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
        if WORKER_MODEL_ID > 0:
            WORKER_NN = load_net(WORKER_DNAME + fname_from_id(WORKER_MODEL_ID))
        else:
            WORKER_NN = Net()
        WORKER_NN.eval()
    nn = WORKER_NN

    p1 = NNSimplePlayer('p1', nn=nn, train=True)
    p2 = NNSimplePlayer('p2', nn=nn, train=True)
    g = Game(players=[p1, p2], verbose=False)
    winner = g.run()
    extra = ''
    for _ in range(5):
        try:
            fname = '{:05}_{}_{}__{}.json'.format(WORKER_MODEL_ID, int(time.time()), extra, len(p1._states) + len(p2._states))
            with open(f'{WORKER_DNAME}{fname}', 'x') as f:
                json.dump({'p1_s': p1._states, 'p2_s': p2._states, 'w': 0 if p1 == winner else 1}, f)
                log.info('wrote %s', fname)
            break
        except FileExistsError:
            log.info('file exists')
            extra = str(random.randint(1,1000))

def gen_training(args):
    dname = 'run_{}/'.format(args.run)
    import os
    os.makedirs(dname, exist_ok=True)

    if args.net:
        model_id = args.net
    else:
        try:
            model_id = last_model_id(dname)
        except:
            log.warning('no model found')
            model_id = 0

    global WORKER_MODEL_ID, WORKER_DNAME, WORKER_ROLLOUTS
    WORKER_MODEL_ID = int(model_id)
    WORKER_DNAME = dname
    WORKER_ROLLOUTS = args.rollouts

    pool = multiprocessing.Pool(args.workers)
    pool.map(game_gen_worker, range(args.num_games))
    pool.close()
    pool.join()
    return model_id


def train(args):
    dname = 'run_{}/'.format(args.run)
    try:
        cur_model_id = int(last_model_id(dname))
        model = load_net(dname + fname_from_id(cur_model_id))
    except:
        log.warning('no prev model found, staring new run')
        cur_model_id = 0
        model = Net()

    model.train()

    loss_func = MSELoss()
    #opt = torch.optim.SGD(model.parameters(), lr=1e-4)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)

    datafiles = ['{}{:05}_'.format(dname, m_id) for m_id in range(cur_model_id, -1, -1)[:3]]
    #ds = GamesDataset(*datafiles, discount=0.01)
    ds = GamesDataset(*datafiles)

    epochs = 200

    # we want ~4 samples from each game
    #num_samples = len(ds) // (epochs * 200)
    num_samples = len(ds) // 50

    sampler = torch.utils.data.RandomSampler(ds, replacement=True, num_samples=num_samples)
    train_dl = DataLoader(ds, batch_size=1000, sampler=sampler)

    for epoch in range(epochs):
        for xb, yb in train_dl:
            opt.zero_grad()
            pred = model(xb)
            yb = yb.view(-1, 1)
            loss = loss_func(pred, yb)

            loss.backward()
            opt.step()

        if epoch % 40 == 0:
            print(epoch, loss.item())
    print(loss_func(model(xb), yb).item())

    save_model(model, dname + fname_from_id(cur_model_id+1))
    return model

def bench(args):
    dname = 'run_{}/'.format(args.run)
    p = [make_player(NNSimplePlayer, id_, nn=load_net(dname + fname_from_id(id_))) for id_ in args.ids]

    from players.random_player import RandomPlayer, WEIGHT_MAP26
    #p.append(make_player(SimplePlayer, 'simple'))
    if args.tourney:
        b = RoundRobin(p)
    else:
        b = Bench(p)
    b.run(args.games)
    b.summary()


def train_loop(args):
    parser = get_parser()
    gen_args = parser.parse_args(['gen', args.run, f'-n {args.num_games}'])
    train_args = parser.parse_args(['train', args.run])
    bench_args = parser.parse_args(['bench', args.run, '1 2'])

    for i in range(args.loops):
        log.info('starting loop %s', i)
        gid = int(gen_training(gen_args))
        model = train(train_args)
        gid += 1
        bench_args.ids = list(range(gid, 0, -1)[:3])
        bench(bench_args)


def get_parser():
    from argparse import ArgumentParser

    parser = ArgumentParser(description='NN player training')

    subparsers = parser.add_subparsers(help='sub-command help')
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

    loop = subparsers.add_parser('loop', help="generate training data and train")
    loop.add_argument('run', help='training run')
    loop.add_argument('-n', '--num-games', type=int, default=2000, help='number of games to generate')
    loop.add_argument('--net', type=int, default=None, help='net id')
    loop.add_argument('-r', '--rollouts', type=int, default=50, help='node rollouts')
    loop.add_argument('-p', '--workers', type=int, default=4, help='workers')
    loop.add_argument('-l', '--loops', type=int, default=10, help='number of loops')
    loop.set_defaults(func=train_loop)

    return parser

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    parser = get_parser()
    args = parser.parse_args()
    args.func(args)
