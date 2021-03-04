import glob
import json
import re
import logging

import torch
from torch.utils.data import Dataset

log = logging.getLogger(__name__)

class ToTensor(object):
    """Convert list in sample to Tensors."""

    def __call__(self, sample):
        return torch.tensor(sample[0]), torch.tensor(sample[1])

'''
class GamesDataset(Dataset):
    def __init__(self, run):
        self.dname = 'run_{}'.format(run)
        self.idx

    def __getitem__(self, index: int):
        return super().__getitem__(index)

    def __len__(self) -> int:
        n = 0
        # every file has # of states
        for f in glob.glob(self.dname):
            n += int(re.match(r'.*__(\d+).json', f).groups()[0])
        return n
'''

def discounted_v(v, n, d):
    d_v = []
    for _ in range(n):
        d_v.append(v)
        v = v * d
    d_v.reverse()
    return d_v


class GamesDataset(Dataset):
    def __init__(self, *dnames, num_games=None, discount=None):

        fnames = []
        for dname in dnames:
            fnames.extend(list(glob.glob(dname + '*.json')))

        fnames.sort()
        if num_games:
            fnames = fnames[-num_games:]

        trainx, trainy = [], []
        for fname in fnames:
            with open(fname, 'r') as f:
                try:
                    data = json.load(f)
                except Exception:
                    log.warning('bad file data: %s; skipping', fname)
                    continue
                w = 1. if data['w'] == 0 else -1.
                trainx.extend(data['p1_s'])
                trainx.extend(data['p2_s'])

                if discount:
                    d = 1.0-discount
                    trainy.extend(discounted_v(w, len(data['p1_s']), d))
                    trainy.extend(discounted_v(-w, len(data['p2_s']), d))
                else:
                    trainy.extend([w]*len(data['p1_s']))
                    trainy.extend([-w]*len(data['p2_s']))
        self.trainx = trainx
        self.trainy = trainy


    def __getitem__(self, index: int):
        return torch.tensor(self.trainx[index]), torch.tensor(self.trainy[index])

    def __len__(self) -> int:
        return len(self.trainx)


def contruct_model(layers):
    from torch import nn
    l = []
    in_p = layers[0]
    for out_p in layers:
        l.append(nn.Linear(in_p, out_p))
        l.append(nn.ReLU())
        in_p = out_p
    l.append(nn.Linear(in_p, 1))
    l.append(nn.Tanh())
    return nn.Sequential(*l)
