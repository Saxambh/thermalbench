"""Predict a new stratified-tank case with a trained ThermalStorageBench model (no CFD).

  python predict.py --uin 0.03 --tin 60 --t0 20 --W 0.6 --s 0.04 --off 0.1 --inlet-type A \
                    --mode charge [--yi 0.5] [--turb sst] [--tstar 1.0] [--out predictions]
  python predict.py --from-run T0123_lam          # a dataset run: predict it and score against its CFD

Inputs are the design parameters of the dataset (make_design.args_for): inlet velocity (m/s),
inlet and initial temperature (C), width W (m, height is 1 m), port size s and port offset (m),
port type A (side wall) or B (lid and bottom), charge or discharge, optional pre-stratified start
(interface height yi as a fraction of H), laminar or SST, and the end time as t* = t Q / V.

How: the case generator (scripts/make_tank_case.py) writes the case into a temp folder (files
only, no mesh, no solver), so ports, cell counts, Re and Ri are exactly those of a dataset run.
The initial field (uniform, or the generator's tanh profile) and the 121 snapshot times
(t* = k t*_end / 120) are built the same way, and the network predicts theta at every snapshot.

Model: --model (default fno_hybrid_canon, the main model) trained on --split (default random,
trained on ~80 % of the design). Every seed found (ckpt_<model>[_s<n>]_<split>.pt) is used: the
prediction is their mean, and their spread is saved as an uncertainty estimate. The input
scaling is refitted from the split's training runs in the frozen manifest (exactly as train.py
did) and cached next to the checkpoint (<ckpt>.encoder.json), so later runs need no data.
A warning is printed for every input outside the range of the training runs: there the
prediction is an extrapolation.

Writes <out>/<name>.npz (T_K [n, ny, nx], theta, theta_sd, times_s, tstar, per-snapshot metrics:
stored energy, MIX, thermocline height, outlet temperature) and <out>/<name>.png.
Written 2026-11-05 (Saxam: "build predict.py").
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import tempfile

import numpy as np
import torch

from data import DEFAULT_ROOTS, PARAMS, Run, index, port_maps
from models import MODELS
from splits import SPLITS, split_runs
from train import Encoder, Predictor, plug

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(os.path.dirname(HERE), "scripts")
sys.path.insert(0, SCRIPTS)
NSNAP = 120


class VirtualRun(Run):
    """A Run built from case.json alone: initial field and snapshot times, no CFD fields."""

    def __init__(self, meta, nsnap=NSNAP):
        super().__init__(path=meta["case"], meta=meta)
        Q, V = meta["u_in_m_s"] * meta["slot_m"], meta["W_m"] * meta["H_m"]
        self._tstar = np.arange(nsnap + 1) * meta["tstar_end"] / nsnap
        self._times = self._tstar * V / Q

    def times(self):
        return self._times, self._tstar

    def field(self, name="T", idx=None, theta=False):
        idx = np.atleast_1d(0 if idx is None else idx)
        if name != "T" or np.any(idx != 0):
            raise ValueError("a predicted case has only its initial field")
        m = self.meta
        ny, nx, h = m["ny"], m["nx"], m["mesh_h_m"]
        if m["init"] == "uniform":
            th = np.full((ny, nx), 1.0 if m["T_init_K"] >= m["T_in_K"] else 0.0)
        else:   # make_tank_case.py: hot over cold, 0.5 (1 + tanh((y - yi H) / delta))
            y = (np.arange(ny) + 0.5) * h
            prof = 0.5 * (1 + np.tanh((y - m["init"]["yi_frac"] * m["H_m"]) / m["init"]["delta_m"]))
            th = np.repeat(prof[:, None], nx, axis=1)
        a = th if theta else self.Tc + th * (self.Th - self.Tc)
        return np.repeat(a[None].astype(np.float32), len(idx), axis=0)


def make_meta(a):
    """case.json for the requested case, written by the dataset's own generator."""
    gen_args = ["--props", "real", "--h", "0.005", "--uin", str(a.uin), "--tin", str(a.tin), "--t0", str(a.t0),
                "--W", str(a.W), "--H", "1.0", "--s", str(a.s), "--off", str(a.off), "--inlet-type", a.inlet_type,
                "--mode", a.mode, "--tstar", str(a.tstar), "--nsnap", str(NSNAP)]
    if a.yi is not None:
        gen_args += ["--yi", str(a.yi)]
    if a.turb == "sst":
        gen_args += ["--turb", "kOmegaSST", "--buoy"]
    with tempfile.TemporaryDirectory() as tmp:
        case = os.path.join(tmp, a.name)
        p = subprocess.run([sys.executable, os.path.join(SCRIPTS, "make_tank_case.py"), case] + gen_args,
                           capture_output=True, text=True)
        if p.returncode != 0:
            sys.exit(f"make_tank_case.py refused the inputs:\n{p.stderr.strip()[-800:]}")
        return json.load(open(os.path.join(case, "case.json")))


def checkpoints(results, model, split):
    """{seed name: path}, final layout (<results>/ckpt/) first, then the older code-folder files."""
    found = {}
    for pattern in (os.path.join(HERE, results, "ckpt", f"ckpt_{model}*_{split}.pt"),
                    os.path.join(HERE, f"ckpt_{model}*_{split}.pt")):
        for f in sorted(glob.glob(pattern)):
            tag = os.path.basename(f)[len(f"ckpt_{model}"):-len(f"_{split}.pt")]
            if (tag == "" or (tag.startswith("_s") and tag[2:].isdigit())) and (tag or "_s0") not in found:
                found[tag or "_s0"] = f
        if found:
            break
    return found


def encoder(ckpt, split, manifest, hybrid, canon):
    """Input scaling of the training runs; cached as <ckpt>.encoder.json."""
    cache = ckpt + ".encoder.json"
    if os.path.exists(cache):
        c = json.load(open(cache))
        if c["split"] == split and c["manifest"] == os.path.basename(manifest or "") and c["params"] == list(PARAMS):
            enc = Encoder.__new__(Encoder)
            enc.hybrid, enc.canon = hybrid, canon
            enc.mu, enc.sd, enc.nx_max = np.array(c["mu"]), np.array(c["sd"]), c["nx_max"]
            return enc, np.array(c["lo"]), np.array(c["hi"])
    train = split_runs(index(DEFAULT_ROOTS, manifest=manifest), split)["train"]
    if not train:
        sys.exit("no training runs found to rebuild the input scaling (run where the dataset is)")
    enc = Encoder(train, hybrid=hybrid, canon=canon)
    P = np.array([r.params() for r in train])
    json.dump({"split": split, "manifest": os.path.basename(manifest or ""), "params": list(PARAMS),
               "n_train": len(train), "mu": enc.mu.tolist(), "sd": enc.sd.tolist(), "nx_max": enc.nx_max,
               "lo": P.min(0).tolist(), "hi": P.max(0).tolist()}, open(cache, "w"), indent=1)
    return enc, P.min(0), P.max(0)


def snapshot_metrics(theta, run):
    """Per-snapshot metrics, computed exactly as export_case.py does for the dataset."""
    import export_case
    m = run.meta
    out = {}
    w = port_maps(m, m["ny"], m["nx"])[1]
    w = w / w.sum()
    for k, th in enumerate(theta):
        T = run.Tc + th * (run.Th - run.Tc)
        d = export_case.metrics(T.astype(float), m, m["mesh_h_m"] ** 2)
        d["T_out_K"] = float((T * w).sum())
        for key, v in d.items():
            out.setdefault(key, []).append(v)
    return {k: np.array(v) for k, v in out.items()}


def figure(path, run, theta, sd, mets, plug_th, true=None, true_mets=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
    BLUE, ORANGE, GREY = "#2a78d6", "#eb6834", "#8a8984"
    plt.rcParams.update({"font.size": 8.5, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                         "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                         "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF})
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("heat", ["#fdf0e6", "#f6b48a", "#eb6834", "#a8401a", "#4a1a08"])
    m = run.meta
    ts = run.times()[1]
    pick = [int(round(f * (len(ts) - 1))) for f in (0.25, 0.5, 0.75, 1.0)]
    rows = 2 if true is not None else 1
    fig = plt.figure(figsize=(9.6, 2.6 * rows + 2.4))
    gs = fig.add_gridspec(rows + 1, 4, height_ratios=[1] * rows + [0.95], hspace=0.45, wspace=0.25)
    ext = [0, m["W_m"], 0, m["H_m"]]
    Tc, Th = run.Tc - 273.15, run.Th - 273.15
    for j, k in enumerate(pick):
        for r, (fld, lab) in enumerate([(theta, "predicted")] + ([(true, "CFD")] if true is not None else [])):
            ax = fig.add_subplot(gs[r, j])
            im = ax.imshow(Tc + fld[k] * (Th - Tc), origin="lower", extent=ext, cmap=cmap, vmin=Tc, vmax=Th,
                           aspect="equal")
            ax.set_title(f"{lab}, t* = {ts[k]:.2f}", color=INK, fontsize=8.5)
            ax.set_xticks([0, m["W_m"]]); ax.set_yticks([0, m["H_m"]] if j == 0 else [])
            for side, lo, hi in (m["inlet_port"], m["outlet_port"]):
                c = (ORANGE if (side, lo, hi) == tuple(m["inlet_port"]) else BLUE)
                if side in ("left", "right"):
                    x = 0 if side == "left" else m["W_m"]
                    ax.plot([x, x], [lo, hi], color=c, lw=3, solid_capstyle="butt", clip_on=False)
                else:
                    yv = m["H_m"] if side == "top" else 0
                    ax.plot([lo, hi], [yv, yv], color=c, lw=3, solid_capstyle="butt", clip_on=False)
    cb = fig.colorbar(im, ax=fig.axes[:4 * rows], fraction=0.015, pad=0.01)
    cb.set_label("T (C)")
    E_full = None
    import export_case
    full = export_case.metrics(np.full((m["ny"], m["nx"]), run.Th), m, m["mesh_h_m"] ** 2)["E_J"]
    ax = fig.add_subplot(gs[rows, 0:2])
    e = mets["E_J"] / full
    ax.plot(ts, plug_th.mean(axis=(1, 2)), color=GREY, lw=1.5, ls="--", label="ideal plug flow")
    if true_mets is not None:
        ax.plot(ts, true_mets["E_J"] / full, color=INK2, lw=2, label="CFD")
    ax.plot(ts, e, color=BLUE, lw=2, label="predicted")
    ax.set_xlabel("t* = t Q / V"); ax.set_ylabel("stored energy / full charge"); ax.grid(color=GRID, lw=0.6)
    ax.legend(frameon=False, fontsize=7.5)
    ax = fig.add_subplot(gs[rows, 2:4])
    out = mets["T_out_K"] - 273.15
    if sd is not None:
        w = port_maps(m, m["ny"], m["nx"])[1]; w = w / w.sum()
        s_out = (sd * w).sum(axis=(1, 2)) * (Th - Tc)
        ax.fill_between(ts, out - s_out, out + s_out, color=BLUE, alpha=0.18, lw=0, label="seed spread (1 sd)")
    if true_mets is not None:
        ax.plot(ts, true_mets["T_out_K"] - 273.15, color=INK2, lw=2, label="CFD")
    ax.plot(ts, out, color=BLUE, lw=2, label="predicted")
    ax.set_xlabel("t* = t Q / V"); ax.set_ylabel("outlet temperature (C)"); ax.grid(color=GRID, lw=0.6)
    ax.legend(frameon=False, fontsize=7.5)
    fig.suptitle(f"{m['case']}: {m['mode']}, type {m['inlet_type']}, W {m['W_m']:g} m, u_in {m['u_in_m_s']:g} m/s, "
                 f"{Tc:.1f} to {Th:.1f} C, {m['turbulence']}, Re {m['Re_in']:.0f}, Ri {m['Ri_H']:.3g}",
                 color=INK, fontsize=9, y=0.995)
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_argument_group("case (design parameters)")
    g.add_argument("--uin", type=float, help="inlet velocity (m/s), dataset 0.005 to 0.2")
    g.add_argument("--tin", type=float, help="inlet temperature (C)")
    g.add_argument("--t0", type=float, help="initial tank temperature (C); |tin - t0| 5 to 50 K in the dataset")
    g.add_argument("--W", type=float, help="tank width (m), dataset 0.25 to 1 (height is 1 m)")
    g.add_argument("--s", type=float, help="port size (m), dataset 0.02 to 0.08")
    g.add_argument("--off", type=float, default=0.1, help="port offset from top/bottom wall (m), dataset 0 to 0.2")
    g.add_argument("--inlet-type", choices=["A", "B"], default="A", help="A side-wall slots, B lid and bottom")
    g.add_argument("--mode", choices=["charge", "discharge"], default="charge")
    g.add_argument("--yi", type=float, default=None, help="pre-stratified start: interface height / H (0.3 to 0.9)")
    g.add_argument("--turb", choices=["laminar", "sst"], default="laminar")
    g.add_argument("--tstar", type=float, default=1.0, help="end time as t* = t Q / V")
    g.add_argument("--name", default="new_case")
    ap.add_argument("--from-run", help="a dataset run_id: predict it and score against its CFD")
    ap.add_argument("--model", default="fno_hybrid_canon")
    ap.add_argument("--split", default="random", choices=SPLITS)
    ap.add_argument("--results", default="results", help="results folder holding ckpt/ (merged final results)")
    ap.add_argument("--manifest", default=os.path.join(HERE, "manifest_full_h5mm.json"))
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--out", default=os.path.join(HERE, "predictions"))
    a = ap.parse_args()

    true = true_mets = None
    if a.from_run:
        hits = [r for r in index(DEFAULT_ROOTS, qc_ok=None) if r.run_id == a.from_run]
        if not hits:
            sys.exit(f"{a.from_run}: not found under {DEFAULT_ROOTS}")
        run, name = hits[0], a.from_run
    else:
        need = [k for k in ("uin", "tin", "t0", "W", "s") if getattr(a, k) is None]
        if need:
            ap.error("missing " + ", ".join("--" + k for k in need) + " (or use --from-run)")
        run, name = VirtualRun(make_meta(a)), a.name

    hybrid, canon = "hybrid" in a.model, "canon" in a.model
    arch = a.model.split("_")[0]
    ck = checkpoints(a.results, a.model, a.split)
    if not ck:
        sys.exit(f"no checkpoint ckpt_{a.model}*_{a.split}.pt in {a.results}/ckpt or {HERE}")
    enc, lo, hi = encoder(next(iter(ck.values())), a.split, a.manifest if os.path.exists(a.manifest) else None,
                          hybrid, canon)

    p = run.params()
    for k, (v, l, h) in enumerate(zip(p, lo, hi)):
        if v < l - 1e-9 or v > h + 1e-9:
            print(f"WARNING: {list(PARAMS)[k]} = {v:.4g} is outside the training range [{l:.4g}, {h:.4g}]: "
                  f"extrapolation, expect larger errors")

    idx = np.arange(len(run.times()[1]))
    preds = []
    for tag, f in ck.items():
        kw = {"width": 32} if arch == "fno" else {"base": 32}
        net = MODELS[arch](enc.channels, **kw)
        net.load_state_dict(torch.load(f, map_location=a.device))
        preds.append(Predictor(net.to(a.device), enc, a.device).predict(run, idx))
    preds[0][0] = run.field("T", idx=[0], theta=True)[0]   # t = 0 is the given initial field
    for pr in preds[1:]:
        pr[0] = preds[0][0]
    theta = np.clip(np.mean(preds, axis=0), 0, 1)
    sd = np.std(preds, axis=0) if len(preds) > 1 else None
    mets = snapshot_metrics(theta, run)
    m = run.meta
    print(f"{name}: {m['mode']} type {m['inlet_type']} W {m['W_m']:g} m u_in {m['u_in_m_s']:g} m/s "
          f"T_in {m['T_in_K'] - 273.15:.1f} C T_0 {m['T_init_K'] - 273.15:.1f} C {m['turbulence']}; "
          f"Re {m['Re_in']:.0f}, Ri {m['Ri_H']:.3g}, {m['nx']} x {m['ny']} cells, t*_end {run.times()[1][-1]:.3g} "
          f"({run.times()[0][-1] / 60:.1f} min)")
    print(f"model {a.model}, split {a.split}, seeds {list(ck)}")
    for f in (0.25, 0.5, 0.75, 1.0):
        k = int(round(f * (len(idx) - 1)))
        print(f"  t* {run.times()[1][k]:5.2f}: outlet {mets['T_out_K'][k] - 273.15:6.2f} C, thermocline "
              f"{mets['y_mid_m'][k]:.3f} m, MIX {mets['MIX'][k]:.3f}"
              + (f", seed spread {sd[k].mean() * (run.Th - run.Tc):.2f} K" if sd is not None else ""))

    if a.from_run:
        import metrics as M
        true = run.field("T", theta=True)
        true_mets = run.metrics()
        true_mets = {"E_J": true_mets["E_J"], "T_out_K": true_mets["T_out_K"]}
        s = M.score(theta[1:], true[1:], run.Th - run.Tc, m["mesh_h_m"], port_maps(m, m["ny"], m["nx"])[1])
        print(f"  vs CFD (all {len(idx) - 1} snapshots): rmse {s['rmse_K']:.3f} K, max {s['max_abs_K']:.2f} K, "
              f"outlet {s['T_out_err_K']:.3f} K, thermocline {s['y_mid_err_m'] * 1000:.1f} mm, "
              f"energy {s['energy_err']:.4f}")

    os.makedirs(a.out, exist_ok=True)
    np.savez_compressed(os.path.join(a.out, f"{name}.npz"), T_K=(run.Tc + theta * (run.Th - run.Tc)).astype(np.float32),
                        theta=theta.astype(np.float32), theta_sd=(sd if sd is not None else np.zeros(0)).astype(np.float32),
                        times_s=run.times()[0], tstar=run.times()[1], case_json=json.dumps(m),
                        model=a.model, split=a.split, **{f"metric_{k}": v for k, v in mets.items()})
    figure(os.path.join(a.out, f"{name}.png"), run, theta, sd, mets,
           plug(run, idx, enc.nx_max)[:, :, : m["nx"]], true, true_mets)
    print(f"wrote {os.path.join(a.out, name)}.npz and .png")


if __name__ == "__main__":
    main()
