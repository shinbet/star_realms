import glob
import json
import re

import torch
from torch.utils.data import Dataset

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

class GamesDataset(Dataset):
    def __init__(self, dname):
        self.dname = dname

        trainx, trainy = [], []
        for fname in glob.glob(self.dname + '*.json'):
            with open(fname, 'r') as f:
                d = json.load(f)
                w = 1. if d['w'] == 0 else -1.
                trainx.extend(d['p1_s'])
                trainx.extend(d['p2_s'])

                trainy.extend([w]*len(d['p1_s']))
                trainy.extend([-w]*len(d['p2_s']))
        self.trainx = trainx
        self.trainy = trainy


    def __getitem__(self, index: int):
        return torch.tensor(self.trainx[index]), torch.tensor(self.trainy[index])

    def __len__(self) -> int:
        return len(self.trainx)