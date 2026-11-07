"""Multi-node (1D) stratified-tank model as a physics baseline for the tank benchmark (added 8 November 2026).

Why: the 1D "ideal stratification" baseline is an idealised limit (a sharp interface moving at the inflow
rate), not a model anyone uses. System simulations use calibrated multi-node tank models (TRNSYS-style). This
baseline answers the practical question: does a field surrogate beat the 1D model an engineer would use?

Model (per run, from its inputs only; the initial row-averaged profile is the initial condition):
  - N = ny horizontal layers of the run's 5 mm rows; theta = (T - Tc)/(Th - Tc), hot on top.
  - Plug flow: the inflow Q = u_in * slot (per metre depth, 2D) enters at the inlet rows (side slot: rows
    overlapping the slot; lid/bottom port: top/bottom row) at theta_in = 1 if hot inflow else 0, and leaves
    at the outlet rows; vertical flux between layers follows from continuity; upwind, implicit.
  - Diffusion: D(y) = alpha (1 + k_b) + D_in exp(-|y - y_in| / h_in), with
        D_in = c1 * Q * Ri_H^(-c2)   (inlet-jet entrainment, stronger at low Richardson number)
        h_in = c3 * H                (depth of the inlet mixing zone)
    alpha is the run's molecular thermal diffusivity, y_in the inlet height.
  - Buoyancy: any temperature inversion is removed after each step by adiabatic mixing of adjacent
    layers (pool-adjacent-violators on equal-volume layers), as in standard multi-node models.
  - Implicit Euler, 800 steps over the run.
Free parameters, fitted separately for laminar and SST runs: log10 k_b, log10 c1, c2, log10 c3.

Protocol (fixed before any test score was computed):
  - fit on each split's training + validation designs only (as the other baselines), minimising the mean
    row-averaged profile RMSE of theta at every 10th snapshot over a fixed subsample (up to 60 runs per
    closure, chosen by hash), Nelder-Mead from a fixed start, 150 evaluations;
  - predict the test runs once with the fitted parameters; the 1D profile is broadcast across the width;
  - scored by evaluate.py with the same metrics and snapshots as every other model; reported as obtained.
"""
import hashlib
import numpy as np
from scipy.linalg import solve_banded
from scipy.optimize import minimize

N_STEPS = 800
X0 = np.array([0.0, -1.0, 0.5, -1.0])      # log10 k_b, log10 c1, c2, log10 c3


def _rows(port, ny, h):
    """Inflow weights per row and the port centre height (m) for a port [side, a, b]."""
    side, a, b = port
    w = np.zeros(ny)
    if side == "top":
        w[-1] = 1.0
        return w, ny * h
    if side == "bottom":
        w[0] = 1.0
        return w, 0.0
    y0 = np.arange(ny) * h
    w = np.clip(np.minimum(y0 + h, b) - np.maximum(y0, a), 0, None)
    return w / w.sum(), 0.5 * (a + b)


def _pava(th):
    """Remove inversions (theta must not decrease upwards) by mixing adjacent equal-volume layers."""
    if np.all(np.diff(th) >= -1e-12):
        return th
    vals, cnts = [], []
    for v in th:
        vals.append(v); cnts.append(1)
        while len(vals) > 1 and vals[-2] > vals[-1]:
            v2, c2 = vals.pop(), cnts.pop()
            vals[-1] = (vals[-1] * cnts[-1] + v2 * c2) / (cnts[-1] + c2); cnts[-1] += c2
    return np.repeat(vals, cnts)


def simulate(meta, th0, t_out, p):
    """theta profiles [len(t_out), ny] for one run; th0 = initial row-averaged profile; p = 4 parameters."""
    kb, c1, c2, c3 = 10 ** p[0], 10 ** p[1], p[2], 10 ** p[3]
    ny, h, H, W = meta["ny"], meta["mesh_h_m"], meta["H_m"], meta["W_m"]
    Q = meta["u_in_m_s"] * meta["slot_m"]
    th_in = 1.0 if meta["T_in_K"] > meta["T_init_K"] else 0.0
    w_in, y_in = _rows(meta["inlet_port"], ny, h)
    w_out, _ = _rows(meta["outlet_port"], ny, h)
    V = W * h
    # face fluxes (positive upwards) at the ny-1 interior faces, from continuity
    F = Q * (np.cumsum(w_in)[:-1] - np.cumsum(w_out)[:-1])
    yc = (np.arange(ny) + 0.5) * h
    yf = (np.arange(1, ny)) * h
    D = meta["alpha_m2_s"] * (1 + kb) + c1 * Q * max(meta["Ri_H"], 1e-3) ** (-c2) * np.exp(-np.abs(yf - y_in) / (c3 * H))
    dt = max(t_out[-1], 1e-9) / N_STEPS
    # linear operator dth/dt = A th + b, tridiagonal
    lo, di, up = np.zeros(ny), np.zeros(ny), np.zeros(ny)
    kd = D * W / h / V                      # diffusive conductance per face, divided by layer volume
    di[:-1] -= kd; up[1:] += kd             # cell j, face j+1/2 (to j+1)
    di[1:] -= kd; lo[:-1] += kd             # cell j+1, face j+1/2 (to j)
    Fu, Fd = np.clip(F, 0, None) / V, np.clip(-F, 0, None) / V
    di[1:] -= Fu; lo[:-1] += Fu             # upward flux brings cell j into cell j+1
    di[:-1] -= Fd; up[1:] += Fd             # downward flux brings cell j+1 into cell j
    src = Q * w_in / V
    di -= src
    b = src * th_in
    ab = np.zeros((3, ny))
    ab[0, 1:] = -dt * up[1:]
    ab[1] = 1 - dt * di
    ab[2, :-1] = -dt * lo[:-1]
    th = np.asarray(th0, float).copy()
    t, k, out = 0.0, 0, np.zeros((len(t_out), ny))
    while k < len(t_out) and t_out[k] <= 0:
        out[k] = th; k += 1
    for _ in range(N_STEPS):
        th_new = _pava(solve_banded((1, 1), ab, th + dt * b))
        t_new = t + dt
        while k < len(t_out) and t_out[k] <= t_new + 1e-9:
            w = (t_out[k] - t) / dt
            out[k] = (1 - w) * th + w * th_new; k += 1
        th, t = th_new, t_new
    out[k:] = th
    return out


def _u(rid):
    return int(hashlib.md5(("mn" + rid).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


class MultiNode:
    name = "multinode"

    def __init__(self, n_fit=60, maxfev=150, stride=10):
        self.n_fit, self.maxfev, self.stride = n_fit, maxfev, stride
        self.params = {}

    def fit(self, train):
        for turb in ("laminar", "kOmegaSST"):
            runs = sorted([r for r in train if r.meta["turbulence"] == turb], key=lambda r: _u(r.run_id))[: self.n_fit]
            if not runs:
                self.params[turb] = X0.copy(); continue
            data = []
            for r in runs:
                t = r.times()[0]
                idx = np.arange(self.stride, len(t), self.stride)
                prof = r.field("T", theta=True).mean(axis=2)          # [n, ny]
                data.append((r.meta, prof[0], t[idx], prof[idx]))

            def loss(p):
                e = [np.sqrt(((simulate(m, p0, tt, p) - pt) ** 2).mean()) for m, p0, tt, pt in data]
                return float(np.mean(e))
            res = minimize(loss, X0, method="Nelder-Mead", options={"maxfev": self.maxfev, "xatol": 1e-3, "fatol": 1e-5})
            self.params[turb] = res.x
            self.fit_info = getattr(self, "fit_info", {}) | {turb: {"loss": float(res.fun), "n_runs": len(runs), "params": res.x.tolist(),
                                                                    "start_loss": float(loss(X0))}}
        return self

    def predict(self, run, idx):
        m = run.meta
        t = run.times()[0][np.atleast_1d(idx)]
        th0 = run.field("T", idx=[0], theta=True)[0].mean(axis=1)
        prof = simulate(m, th0, t, self.params[m["turbulence"]]).astype(np.float32)
        return np.repeat(prof[:, :, None], m["nx"], axis=2)
