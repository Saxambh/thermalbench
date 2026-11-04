"""Non-neural reference predictors for the PCM forward task: given a run's inputs (case.json)
and snapshot times, predict theta and liquid fraction alpha at each time.

  Initial   nothing happens: solid at T0 everywhere (lower bar)
  Stefan    conduction only: the exact two-phase Neumann solution for a semi-infinite slab
            heated at x = 0 (equal diffusivity in both phases, as the constant-property CFD),
            fins and convection ignored. Shows how much natural convection matters
  Front     conduction, then convection: early melting is conduction-dominated (Stefan), later
            the convective rate takes over, f = min(1, s tau) with tau = t / t_ref
            (pcm_data.t_ref) and one scale s fitted on the training runs. At each time the
            regime further along wins: the Stefan field while it has melted more, otherwise a
            vertical melt layer of width f W at the heated wall with a linear liquid
            temperature from the wall to the melting point. Physics base of the hybrids
  KNN       average of the k training runs nearest in standardised parameter space, each
            taken at the same tau and stretched to the target width
Fin cells are given theta = 1 and alpha = 0 by Stefan and Front.
All predictors expose predict(run, idx) -> (theta [n, ny, nx], alpha [n, ny, nx]).
"""
import math

import numpy as np

from baselines import stretch_x
from pcm_data import PARAMS


def _theta_m(m):
    return (m["Tmelt_K"] - m["T_init_K"]) / (m["T_wall_K"] - m["T_init_K"])


def _x(m):
    return (np.arange(m["nx"]) + 0.5) * m["mesh_h_m"]


def _fins(run, out_th, out_a):
    fin = run.mask() < 0.5
    out_th[:, fin] = 1.0
    out_a[:, fin] = 0.0
    return out_th, out_a


class Initial:
    name = "initial"

    def fit(self, train):
        return self

    def predict(self, run, idx):
        n, (ny, nx) = len(np.atleast_1d(idx)), run.mask().shape
        return np.zeros((n, ny, nx), np.float32), np.zeros((n, ny, nx), np.float32)


def neumann_lambda(st_l, st_s):
    """Root of st_l e^-l^2 / erf(l) - st_s e^-l^2 / erfc(l) = l sqrt(pi) (bisection)."""
    g = lambda l: st_l * math.exp(-l * l) / math.erf(l) - st_s * math.exp(-l * l) / math.erfc(l) - l * math.sqrt(math.pi)
    lo, hi = 1e-6, 5.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if g(mid) > 0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


class Stefan:
    name = "stefan"

    def fit(self, train):
        return self

    def predict(self, run, idx):
        m, p = run.meta, run.meta["props"]
        a = p["k"] / (p["rho"] * p["cp"])
        st_l = p["cp"] * (m["T_wall_K"] - m["Tmelt_K"]) / p["L"]
        st_s = p["cp"] * (m["Tmelt_K"] - m["T_init_K"]) / p["L"]
        lam, thm = neumann_lambda(st_l, st_s), _theta_m(m)
        t = run.times()[0][np.atleast_1d(idx)]
        x = _x(m)
        ny = m["ny"]
        th = np.zeros((len(t), ny, len(x)), np.float32)
        al = np.zeros_like(th)
        for n, tn in enumerate(t):
            if tn <= 0:
                continue
            xi = x / (2 * math.sqrt(a * tn))
            erf = np.vectorize(math.erf)(xi)
            liq = xi < lam
            prof = np.where(liq, 1 - (1 - thm) * erf / math.erf(lam),
                            thm * (1 - erf) / math.erfc(lam))
            th[n] = prof[None, :]
            al[n] = liq[None, :]
        return _fins(run, th, al)


class Front:
    name = "front"

    def __init__(self, s=1.0):
        self.s = s

    @staticmethod
    def _cond(run, t):
        """Conduction-only melted fraction (Stefan front 2 lambda sqrt(a t) over W)."""
        m, p = run.meta, run.meta["props"]
        a = p["k"] / (p["rho"] * p["cp"])
        lam = neumann_lambda(p["cp"] * (m["T_wall_K"] - m["Tmelt_K"]) / p["L"],
                             p["cp"] * (m["Tmelt_K"] - m["T_init_K"]) / p["L"])
        return np.minimum(1.0, 2 * lam * np.sqrt(a * np.maximum(t, 0)) / m["W_m"])

    def fit(self, train):
        """Scale s minimising the mean melted-fraction error on the training runs."""
        taus, fc, fs = [], [], []
        for r in train:
            t, tau = r.times()
            taus.append(tau)
            fc.append(self._cond(r, t))
            fs.append(r.metrics()["liquid_fraction"])
        tau, fc, f = np.concatenate(taus), np.concatenate(fc), np.concatenate(fs)
        grid = np.exp(np.linspace(np.log(0.2), np.log(5), 400))
        err = [np.abs(np.maximum(fc, np.minimum(1, s * tau)) - f).mean() for s in grid]
        self.s = float(grid[int(np.argmin(err))])
        return self

    def frac(self, run, idx):
        t, tau = run.times()
        i = np.atleast_1d(idx)
        return np.maximum(self._cond(run, t[i]), np.minimum(1.0, self.s * tau[i]))

    def predict(self, run, idx):
        m = run.meta
        i = np.atleast_1d(idx)
        t, tau = run.times()
        fc, fv = self._cond(run, t[i]), np.minimum(1.0, self.s * tau[i])
        st_th, st_al = Stefan().predict(run, i)
        x, W, thm = _x(m), m["W_m"], _theta_m(m)
        th, al = st_th.copy(), st_al.copy()
        for n in np.nonzero(fv > fc)[0]:          # convective regime
            xf = max(fv[n] * W, 1e-9)
            liq = x < xf
            th[n] = np.where(liq, thm + (1 - thm) * (1 - x / xf), 0.0)[None, :]
            al[n] = liq[None, :]
        return _fins(run, th, al)


class KNN:
    name = "knn"

    def __init__(self, k=5):
        self.k = k

    def fit(self, train):
        self.train = train
        X = np.array([r.params() for r in train])
        sd = X.std(0)
        self.mu, self.sd = X.mean(0), np.where(sd < 1e-6, 1.0, sd)
        self.X = (X - self.mu) / self.sd
        self.taus = [r.times()[1] for r in train]
        return self

    def predict(self, run, idx):
        d = np.linalg.norm(self.X - (run.params() - self.mu) / self.sd, axis=1)
        near = np.argsort(d)[: self.k]
        tau = run.times()[1][np.atleast_1d(idx)]
        ny, nx = run.mask().shape
        th = np.zeros((len(tau), ny, nx), np.float32)
        al = np.zeros_like(th)
        for j in near:
            nb, nt = self.train[j], self.taus[j]
            k = np.abs(nt[None, :] - tau[:, None]).argmin(axis=1)   # nearest snapshot in tau
            u = np.unique(k)
            sel = np.searchsorted(u, k)
            th += stretch_x(nb.field("T", idx=u, theta=True)[sel], nx)
            al += stretch_x(nb.field("alpha", idx=u)[sel], nx)
        return th / len(near), al / len(near)


MAKERS = {"initial": Initial, "stefan": Stefan, "front": Front, "knn": KNN}
