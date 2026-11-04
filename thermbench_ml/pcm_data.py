"""ThermBench PCM family: data access (runs written by make_pcm_case.py + export_pcm_case.py).

A run is one directory with DONE and thermbench.h5:
  fields/T, fields/alpha, fields/ux, fields/uy  [time, ny, nx] on the uniform grid
                                                 (row 0 = bottom, column 0 = heated wall)
  mask [ny, nx]  1 = PCM, 0 = fin;  times_s;  metrics/*;  series/*;  attrs case_json
Normalised temperature theta = (T - T0) / (Tw - T0): 0 = initial solid, 1 = heated wall.

Canonical grid: H = 100 mm and W <= W_MAX = 60 mm on a 0.5 mm mesh, so every field is
[ny, nx] with ny = H/h and nx = W/h, left-aligned (heated wall at column 0) and zero-padded
to nx_max = W_MAX/h. Nothing is interpolated.

Time input. The models are told tau = t / t_ref, where t_ref is an a priori melting-time
scale computed from the inputs alone (energy needed / laminar natural-convection heat rate,
Nu ~ Ra^0.25, calibrated on the Vogel and Kamkari validation runs; fins and tilt by the
Kamkari factors). The true melting time is an output, so it is never used as an input.
"""
import glob
import json
import os
from dataclasses import dataclass, field

import h5py
import numpy as np

from data import _uncache

W_MAX = 0.06
C_NU = 0.236          # calibration of t_ref (pcm_budget.py: Vogel 0.237, Kamkari 0.236)


def t_ref(m):
    """A priori melting-time scale (s) from case.json alone."""
    p = m["props"]
    sh, sub = m["T_wall_K"] - m["Tmelt_K"], m["Tmelt_K"] - m["T_init_K"]
    E = p["rho"] * m["W_m"] * (p["L"] + p["cp"] * (sub + sh / 2))
    q = C_NU * p["k"] * sh / m["H_m"] * m["Ra_H"] ** 0.25
    tilt = float(m.get("tilt_deg", 0.0))
    f_tilt = np.interp(tilt, [0, 45, 90], [1.0, 0.62, 0.46])
    return E / q * (1 + m.get("nfins", 0)) ** -0.5 * f_tilt


def ste_drive(m):
    """Driving Stefan number cp (Tw - Tm) / L."""
    return m["props"]["cp"] * (m["T_wall_K"] - m["Tmelt_K"]) / m["props"]["L"]


# scalar inputs offered to models (all known before the run)
PARAMS = {
    "lauric": lambda m: float(m["material"] == "lauric"),
    "superheat": lambda m: m["T_wall_K"] - m["Tmelt_K"],
    "subcooling": lambda m: m["Tmelt_K"] - m["T_init_K"],
    "W": lambda m: m["W_m"],
    "nfins": lambda m: float(m.get("nfins", 0)),
    "fin_reach": lambda m: m.get("fin_len_m", 0.0) / m["W_m"],
    "fin_t": lambda m: m.get("fin_t_m", 0.0),
    "sin_tilt": lambda m: np.sin(np.radians(m.get("tilt_deg", 0.0))),
    "cos_tilt": lambda m: np.cos(np.radians(m.get("tilt_deg", 0.0))),
    "log_Ra": lambda m: np.log(m["Ra_H"]),
    "Ste": lambda m: ste_drive(m),
    "Pr": lambda m: m["Pr"],
    "log_t_ref": lambda m: np.log(t_ref(m)),
}


@dataclass
class PCMRun:
    path: str
    meta: dict
    _cache: dict = field(default_factory=dict, repr=False)

    @property
    def run_id(self):
        return os.path.basename(self.path)

    case_id = run_id        # one run per design point

    @property
    def Tw(self):
        return self.meta["T_wall_K"]

    @property
    def T0(self):
        return self.meta["T_init_K"]

    @property
    def t_ref(self):
        return t_ref(self.meta)

    def params(self):
        return np.array([f(self.meta) for f in PARAMS.values()], float)

    def h5(self):
        return h5py.File(os.path.join(self.path, "thermbench.h5"), "r")

    def times(self):
        """(t in s, tau = t / t_ref)."""
        if "t" not in self._cache:
            with self.h5() as f:
                self._cache["t"] = f["times_s"][:]
        t = self._cache["t"]
        return t, t / self.t_ref

    def mask(self):
        """[ny, nx]: 1 = PCM, 0 = fin."""
        if "mask" not in self._cache:
            with self.h5() as f:
                self._cache["mask"] = f["mask"][:].astype(np.float32)
        return self._cache["mask"]

    def field(self, name="T", idx=None, theta=False):
        """[n, ny, nx] float32 (all snapshots, or the indices in idx)."""
        with self.h5() as f:
            d = f[f"fields/{name}"]
            a = d[:] if idx is None else d[np.sort(np.atleast_1d(idx))]
        _uncache(os.path.join(self.path, "thermbench.h5"))
        if theta and name == "T":
            a = (a - self.T0) / (self.Tw - self.T0)
        return a.astype(np.float32)

    def metrics(self):
        with self.h5() as f:
            return {k: f[f"metrics/{k}"][:] for k in f["metrics"]}


def index(roots, manifest=None):
    """All finished PCM runs under one or more batch directories (DONE + thermbench.h5). A
    run_id found under several roots is used once (the first root wins). With a manifest
    only the runs it lists are used, and a listed run that is missing is an error."""
    keep = None
    if manifest:
        keep = {e["run_id"] for e in json.load(open(manifest))["runs"]}
    runs, seen = [], set()
    for root in np.atleast_1d(roots):
        for done in sorted(glob.glob(os.path.join(os.path.expanduser(root), "*", "DONE"))):
            p = os.path.dirname(done)
            rid = os.path.basename(p)
            if not os.path.exists(f"{p}/thermbench.h5") or rid in seen or (keep is not None and rid not in keep):
                continue
            seen.add(rid)
            runs.append(PCMRun(p, json.load(open(f"{p}/case.json"))))
    if keep is not None and keep - seen:
        raise ValueError(f"{len(keep - seen)} manifest runs not found, e.g. {sorted(keep - seen)[:5]}")
    return runs


DEFAULT_ROOTS = ["~/of_runs/pcm_full/runs", "~/tb_data/laptop/pcm_full", "~/tb_data/lab/pcm_full",
                 "~/tb_data/pc3/pcm_full", "~/tb_data/pc4/pcm_full", "~/tb_data/pc5/pcm_full"]


def nx_max(h):
    return int(round(W_MAX / h))


def pad(a, nx_max_):
    """Left-align [..., ny, nx] into [..., ny, nx_max]; returns (padded, domain mask [ny, nx_max])."""
    ny, nx = a.shape[-2:]
    out = np.zeros(a.shape[:-1] + (nx_max_,), a.dtype)
    out[..., :nx] = a
    dom = np.zeros((ny, nx_max_), np.float32)
    dom[:, :nx] = 1
    return out, dom
