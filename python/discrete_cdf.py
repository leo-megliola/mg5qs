import numpy as np
import os
from pathlib import Path
import pickle

class DiscreteCDF:
    def __init__(self, v, bins):
        self.v = v # descrete values
        self.bins = bins
        self.hist, self.edges = np.histogram(self.v, bins=self.bins)
        self._pdf = self.hist / np.sum(self.hist) # normalized by sum
        self._cdf = np.concatenate((np.zeros((1)), np.cumsum(self._pdf))) # prepend 0 using concat

    def cdf(self, x):
        width = self.edges[1]-self.edges[0]
        location = (x-self.edges[0])/width # this result could be cached for high-preformance (many calls to CDF)
        left_bin = location.astype(int)
        left_bin = np.clip(left_bin, 0, self.bins-1)
        interp = location-left_bin
        apx = self._cdf[left_bin] + (self._cdf[left_bin+1]-self._cdf[left_bin]) * interp
        return np.clip(apx, 0, 1.0)

    
def unpickle_pTs(path): # pulls the pT vlaues from a pickle file
    pTs = np.empty((0), dtype=np.float64)
    if type(path) == str:
        path = Path(path)
    for fname in os.listdir(path):
        if 'pkl' in fname:
            with open(path / fname, 'rb') as f:
                params, pT = pickle.load(f)
                pTs = np.concatenate([pTs, pT[1]])
    return params, pTs
                