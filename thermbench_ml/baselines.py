"""Non-neural reference predictors for the ThermBench forward task:
given a run's inputs (case.json) and snapshot times, predict the theta field at each time.

  Initial         no change: the initial field at every time (lower bar)
  IdealStratified perfect plug flow from the energy balance: a sharp interface that moves
                  at the inflow rate, hot above, cold below (MIX = 0; the 1D design ideal)
  KNN             average of the k training runs nearest in standardised parameter space,
                  each taken at the same t* and stretched to the target width
All predictors expose predict(run, idx) -> theta [len(idx), ny, nx].
"""
import numpy as np

from data import PARAMS


def _tstar(run, idx):
    return run.times()[1][np.atleast_1d(idx)]


def _theta0(run):
    return run.field("T", idx=[0], theta=True)[0]


class Initial:
    name = "initial"

    def fit(self, train):
        return self

    def predict(self, run, idx):
        return np.repeat(_theta0(run)[None], len(np.atleast_1d(idx)), axis=0)


class IdealStratified:
    name = "ideal_stratified"

    def fit(self, train):
        return self

    def predict(self, run, idx):
        m = run.meta
        ny, nx = m["ny"], m["nx"]
        th0 = float(_theta0(run).mean())               # initial hot fraction
        ts = _tstar(run, idx)
        hot_in = m["T_in_K"] > m["T_init_K"]
        frac = np.clip(th0 + ts if hot_in else th0 - ts, 0, 1)
        y = (np.arange(ny) + 0.5) / ny                 # cell centre heights / H
        out = (y[None, :] >= (1 - frac)[:, None]).astype(np.float32)   # hot layer on top
        return np.repeat(out[:, :, None], nx, axis=2)


def stretch_x(a, nx_new):
    """Linear resampling of [..., ny, nx] to [..., ny, nx_new] in normalised x = x/W."""
    nx = a.shape[-1]
    if nx == nx_new:
        return a
    xo = (np.arange(nx) + 0.5) / nx
    xn = (np.arange(nx_new) + 0.5) / nx_new
    i = np.clip(np.searchsorted(xo, xn) - 1, 0, nx - 2)
    w = np.clip((xn - xo[i]) / (xo[i + 1] - xo[i]), 0, 1)
    return a[..., i] * (1 - w) + a[..., i + 1] * w


class KNN:
    name = "knn"

    def __init__(self, k=5, params=None):
        self.k = k
        self.params = params or list(PARAMS)

    def _x(self, run):
        allp = dict(zip(PARAMS, run.params()))
        return np.array([allp[p] for p in self.params])

    def fit(self, train):
        self.train = train
        X = np.array([self._x(r) for r in train])
        # unit scale for parameters constant in training (e.g. 'discharge' in ood_mode): a ~0 spread
        # would make that one coordinate swamp all distances and the neighbours become arbitrary
        sd = X.std(0)
        self.mu, self.sd = X.mean(0), np.where(sd < 1e-6, 1.0, sd)
        self.X = (X - self.mu) / self.sd
        self.tstars = [r.times()[1] for r in train]
        return self

    def predict(self, run, idx):
        d = np.linalg.norm(self.X - (self._x(run) - self.mu) / self.sd, axis=1)
        near = np.argsort(d)[: self.k]
        ts = _tstar(run, idx)
        out = np.zeros((len(ts), run.meta["ny"], run.meta["nx"]), np.float32)
        for j in near:
            nb, nt = self.train[j], self.tstars[j]
            # nearest neighbour snapshot in t* (snapshots past its end time: use the last)
            k = np.abs(nt[None, :] - ts[:, None]).argmin(axis=1)
            out += stretch_x(nb.field("T", idx=np.unique(k), theta=True)[
                np.searchsorted(np.unique(k), k)], run.meta["nx"])
        return out / len(near)
