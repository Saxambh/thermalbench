"""ThermalStorageBench data access: run index, field loading, canonical padded grid.

A run is one directory with DONE and thermbench.h5 (written by export_case.py).
Temperatures are also given in normalised form theta = (T - Tc) / (Th - Tc) in [0, 1],
where Th and Tc are the hotter and colder of the inlet and initial temperatures.

Canonical grid: every tank has H = 1 m and width W in [0.25, 1] m on a uniform mesh of
spacing h, so its field is [ny, nx] with ny = H/h and nx = W/h. Fields are left-aligned and
zero-padded to [ny, nx_max] with a mask (1 inside the tank). Nothing is interpolated.
"""
import glob
import json
import os
from dataclasses import dataclass, field

import h5py
import numpy as np

# scalar inputs offered to models (all known before the run): name -> function of case.json
PARAMS = {
    "log_u_in": lambda m: np.log(m["u_in_m_s"]),
    "dT": lambda m: abs(m["T_in_K"] - m["T_init_K"]),
    "T_c": lambda m: min(m["T_in_K"], m["T_init_K"]),
    "slot": lambda m: m["slot_m"],
    "port_offset": lambda m: m["port_offset_m"],
    "W": lambda m: m["W_m"],
    "type_B": lambda m: float(m["inlet_type"] == "B"),
    "discharge": lambda m: float(m["mode"] == "discharge"),
    "prestrat": lambda m: float(m["init"] != "uniform"),
    "y_init": lambda m: m["init"]["yi_frac"] if m["init"] != "uniform" else 0.0,
    "log_Re": lambda m: np.log(m["Re_in"]),
    "log_Ri": lambda m: np.log(m["Ri_H"]),
    "turbulent": lambda m: float(m["turbulence"] != "laminar"),
}


def _uncache(path):
    """Drop a file we have finished reading from the Linux page cache. Training reads every
    run's h5 once; without this the cache grows to several GB, which WSL holds on to and
    Windows cannot get back. Data already loaded is unaffected."""
    try:
        fd = os.open(path, os.O_RDONLY)
        os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
        os.close(fd)
    except (OSError, AttributeError):
        pass


@dataclass
class Run:
    path: str
    meta: dict
    qc: dict = field(default_factory=dict)

    @property
    def run_id(self):
        return os.path.basename(self.path)

    @property
    def case_id(self):  # laminar and SST twins of one design point share a case_id
        return self.run_id.rsplit("_", 1)[0]

    @property
    def Th(self):
        return max(self.meta["T_in_K"], self.meta["T_init_K"])

    @property
    def Tc(self):
        return min(self.meta["T_in_K"], self.meta["T_init_K"])

    def params(self):
        return np.array([f(self.meta) for f in PARAMS.values()], float)

    def h5(self):
        return h5py.File(os.path.join(self.path, "thermbench.h5"), "r")

    def times(self):
        with self.h5() as f:
            return f["times_s"][:], f["tstar"][:]

    def field(self, name="T", idx=None, theta=False):
        """[n, ny, nx] float32 (all snapshots, or the indices in idx)."""
        with self.h5() as f:
            d = f[f"fields/{name}"]
            a = d[:] if idx is None else d[np.sort(np.atleast_1d(idx))]
        _uncache(os.path.join(self.path, "thermbench.h5"))
        if theta and name == "T":
            a = (a - self.Tc) / (self.Th - self.Tc)
        return a.astype(np.float32)

    def metrics(self):
        with self.h5() as f:
            return {k: f[f"metrics/{k}"][:] for k in f["metrics"]}


def index(roots, qc_ok=("OK", "WARN"), manifest=None):
    """All finished runs under one or more batch directories, filtered by QC verdict.
    Placeholders left by rebalancing (MOVED_TO_*) are skipped, and a run_id found under
    several roots is used once (the first root wins). With a manifest (freeze_manifest.py)
    only the runs it lists are used, and a listed run that is missing is an error."""
    keep = None
    if manifest:
        keep = {e["run_id"] for e in json.load(open(manifest))["runs"]}
    runs, seen = [], set()
    for root in np.atleast_1d(roots):
        for done in sorted(glob.glob(os.path.join(os.path.expanduser(root), "*", "DONE"))):
            p = os.path.dirname(done)
            if glob.glob(f"{p}/MOVED_TO_*") or not os.path.exists(f"{p}/thermbench.h5"):
                continue
            if os.path.basename(p) in seen or (keep is not None and os.path.basename(p) not in keep):
                continue
            qc = json.load(open(f"{p}/qc.json")) if os.path.exists(f"{p}/qc.json") else {}
            if qc_ok is not None and qc and qc.get("verdict") not in qc_ok:
                continue
            seen.add(os.path.basename(p))
            runs.append(Run(p, json.load(open(f"{p}/case.json")), qc))
    if keep is not None and keep - seen:
        raise ValueError(f"{len(keep - seen)} manifest runs not found, e.g. {sorted(keep - seen)[:5]}")
    return runs


# every machine's copy of the full 5 mm batch, as laid out by gather.sh (on the laptop) or by
# the pre-training copy to pc3 (laptop runs in ~/tb_data/laptop). Missing roots are skipped.
# full_h5mm_x holds lab runs redistributed on 2026-11-03 (rebalance3.py) to a second lab
# batch and to the laptop; their lab folders keep MOVED_TO_* placeholders, which index() skips.
DEFAULT_ROOTS = ["~/of_runs/full_h5mm", "~/of_runs/full_h5mm_x",
                 "~/tb_data/laptop/full_h5mm", "~/tb_data/laptop/full_h5mm_x",
                 "~/tb_data/lab/full_h5mm", "~/tb_data/lab/full_h5mm_x",
                 "~/tb_data/pc3/full_h5mm"]


def pad(a, nx_max):
    """Left-align [..., ny, nx] into [..., ny, nx_max]; returns (padded, mask[ny, nx_max])."""
    ny, nx = a.shape[-2:]
    out = np.zeros(a.shape[:-1] + (nx_max,), a.dtype)
    out[..., :nx] = a
    mask = np.zeros((ny, nx_max), np.float32)
    mask[:, :nx] = 1
    return out, mask


def port_maps(meta, ny, nx_max):
    """Two [ny, nx_max] maps marking the boundary cells next to the inlet and the outlet."""
    h = meta["mesh_h_m"]
    nx = meta["nx"]
    maps = []
    for port in (meta["inlet_port"], meta["outlet_port"]):
        m = np.zeros((ny, nx_max), np.float32)
        side, a, b = port
        lo, hi = int(round(a / h)), int(round(b / h))
        if side == "left":
            m[lo:hi, 0] = 1
        elif side == "right":
            m[lo:hi, nx - 1] = 1
        elif side == "top":
            m[ny - 1, lo:hi] = 1
        else:
            m[0, lo:hi] = 1
        maps.append(m)
    return maps
