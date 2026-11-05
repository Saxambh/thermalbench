"""Predict a new PCM melting case with a trained ThermalStorageBench model (no CFD).

  python pcm_predict.py --material octadecane --tw 50 --t0 20 --W 0.04 \
                        [--nfins 2 --fin-len 0.02 --fin-t 0.002] [--tilt 0|45|90] [--out predictions_pcm]
  python pcm_predict.py --from-run P0046        # a dataset run: predict it and score against its CFD

Inputs are the design parameters of the PCM family (scripts/pcm_design.py): material
(octadecane or lauric acid), heated-wall and initial temperature (C), enclosure width W (m,
height 100 mm, closed box), number of horizontal fins on the heated wall with their length
and thickness (m; conducting aluminium fins), and the tilt (0 side heating, 45, 90 heated
from below).

How: pcm_design.case() turns the inputs into the generator's command line exactly as for the
dataset (material settings, melting range, mushy constant, write interval), and
make_pcm_case.py writes the case into a temp folder (files only, no mesh, no solver), so
grid, fin cells, properties, Ra and t_ref are those a dataset run would have. The network
predicts theta and liquid fraction at every snapshot (the dataset's write interval) from
t = 0 up to the latest tau = t / t_ref seen in training, and the output is cut shortly after
the predicted melted fraction reaches 0.995 (where the CFD runs stop).

Model: --model (default fno_hybrid, the FNO learning the correction to the Front baseline)
trained on --split (default random). Every seed found (ckpt_pcm_<model>[_s<n>]_<split>.pt) is
used: the prediction is their mean, and their spread is saved as an uncertainty estimate. The
input scaling and the Front baseline's fitted constant are rebuilt from the split's training
runs in the frozen PCM manifest (exactly as pcm_train.py did) and cached next to the
checkpoint (<ckpt>.encoder.json), so later runs need no data. A warning is printed for every
input outside the range of the training runs.

Writes <out>/<name>.npz (T_K and alpha [n, ny, nx], their seed spread, mask, times_s, tau,
melted fraction, stored-energy fraction, t50 and t90) and <out>/<name>.png.
Written 2026-11-05 (Saxam: "go ahead with both", PCM predictor + PCM training rehearsal).
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

import pcm_metrics
from models import MODELS
from pcm_baselines import Front
from pcm_data import DEFAULT_ROOTS, PARAMS, PCMRun, W_MAX, index
from pcm_splits import SPLITS, split_runs
from pcm_train import Encoder, Predictor

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(os.path.dirname(HERE), "scripts")
sys.path.insert(0, SCRIPTS)
STOP = 0.995


class VirtualPCMRun(PCMRun):
    """A PCMRun built from case.json alone: mask and snapshot times, no CFD fields."""

    def __init__(self, meta):
        super().__init__(path=meta["case"], meta=meta)
        w, end = meta["write_interval_s"], meta["end_time_s"]
        self._t = np.arange(0.0, end + 0.5 * w, w)

    def times(self):
        return self._t, self._t / self.t_ref

    def mask(self):
        from export_pcm_case import cell_index
        return cell_index(self.meta)[2]

    def field(self, *a, **k):
        raise ValueError("a predicted case has no CFD fields")

    def metrics(self):
        raise ValueError("a predicted case has no CFD metrics")

    def cut(self, n):
        self._t = self._t[:n]


def make_meta(a):
    """case.json for the requested case, through the dataset's own design mapping and generator."""
    import pcm_design as D
    s = D.SETTINGS[a.material]
    ts, tl = s["melt_range"]
    tref = 0.5 * (ts + tl)
    sh, sub = a.tw - tref, ts - a.t0
    R = D.RANGES
    u = lambda k, v: (v - R[k][0]) / (R[k][1] - R[k][0])
    n = a.nfins
    row = D.case(a.name, a.material, u("sh", sh), u("sub", sub), u("W", a.W), n,
                 u("Lf", a.fin_len / a.W) if n else 0.0, u("tf", a.fin_t) if n else 0.0, a.tilt, h=0.0005)
    with tempfile.TemporaryDirectory() as tmp:
        case = os.path.join(tmp, a.name)
        p = subprocess.run([sys.executable, os.path.join(SCRIPTS, "make_pcm_case.py"), case] + row["args"].split(),
                           capture_output=True, text=True)
        if p.returncode != 0:
            sys.exit(f"make_pcm_case.py refused the inputs:\n{p.stderr.strip()[-800:]}")
        meta = json.load(open(os.path.join(case, "case.json")))
    meta["case"] = a.name
    return meta


def checkpoints(results, model, split):
    """{seed name: path}, final layout (<results>/ckpt/) first, then the older code-folder files."""
    found = {}
    stem = f"ckpt_pcm_{model}"
    for pattern in (os.path.join(HERE, results, "ckpt", f"{stem}*_{split}.pt"), os.path.join(HERE, f"{stem}*_{split}.pt")):
        for f in sorted(glob.glob(pattern)):
            tag = os.path.basename(f)[len(stem):-len(f"_{split}.pt")]
            if (tag == "" or (tag.startswith("_s") and tag[2:].isdigit())) and (tag or "_s0") not in found:
                found[tag or "_s0"] = f
        if found:
            break
    return found


def encoder(ckpt, split, manifest, hybrid):
    """Input scaling (and the Front constant) of the training runs; cached as <ckpt>.encoder.json.
    Returns (encoder, params lo, params hi, largest training tau)."""
    cache = ckpt + ".encoder.json"
    tag = os.path.basename(manifest) if manifest else "all finished runs (no manifest)"
    if os.path.exists(cache):
        c = json.load(open(cache))
        if c["split"] == split and c["manifest"] == tag and c["params"] == list(PARAMS):
            enc = Encoder.__new__(Encoder)
            enc.hybrid, enc.mu, enc.sd, enc.nx_max = hybrid, np.array(c["mu"]), np.array(c["sd"]), c["nx_max"]
            enc.front = Front(c["front_s"]) if hybrid else None
            return enc, np.array(c["lo"]), np.array(c["hi"]), c["tau_max"]
    if not manifest:
        print("WARNING: no frozen PCM manifest here; the input scaling is rebuilt from all finished runs, "
              "which only matches the checkpoint if it was trained on the same runs (rehearsal / dev use)")
    train = split_runs(index(DEFAULT_ROOTS, manifest=manifest), split)["train"]
    if not train:
        sys.exit("no training runs found to rebuild the input scaling (run where the PCM dataset is)")
    enc = Encoder(train, hybrid=True)        # always fit Front, so the cache serves both variants
    P = np.array([r.params() for r in train])
    tau_max = float(max(r.times()[1][-1] for r in train))
    json.dump({"split": split, "manifest": tag, "params": list(PARAMS), "n_train": len(train),
               "mu": enc.mu.tolist(), "sd": enc.sd.tolist(), "nx_max": enc.nx_max, "front_s": enc.front.s,
               "lo": P.min(0).tolist(), "hi": P.max(0).tolist(), "tau_max": tau_max}, open(cache, "w"), indent=1)
    enc.hybrid = hybrid
    if not hybrid:
        enc.front = None
    return enc, P.min(0), P.max(0), tau_max


def curves(theta, alpha, run):
    """Melted fraction and stored-energy fraction per snapshot (as pcm_metrics)."""
    m, w = run.meta, run.mask() > 0
    S = m["props"]["cp"] * (m["T_wall_K"] - m["T_init_K"]) / m["props"]["L"]
    frac = alpha[:, w].mean(1)
    energy = ((S * theta + alpha)[:, w]).mean(1) / (S + 1)
    return frac, energy


def figure(path, run, th, al, frac, energy, sd_frac, true=None):
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
    t_min = run.times()[0] / 60
    pick = [int(round(f * (len(t_min) - 1))) for f in (0.15, 0.4, 0.7, 1.0)]
    rows = 2 if true is not None else 1
    fig = plt.figure(figsize=(9.6, 3.3 * rows + 2.4))
    gs = fig.add_gridspec(rows + 1, 4, height_ratios=[1.35] * rows + [0.95], hspace=0.45, wspace=0.12)
    ext = [0, m["W_m"] * 1000, 0, m["H_m"] * 1000]
    T0, Tw = run.T0 - 273.15, run.Tw - 273.15
    fin = np.ma.masked_where(run.mask() > 0.5, np.ones_like(run.mask()))
    for j, k in enumerate(pick):
        for r, (fth, fal, lab) in enumerate([(th, al, "predicted")] + ([(true[0], true[1], "CFD")] if true is not None else [])):
            ax = fig.add_subplot(gs[r, j])
            im = ax.imshow(T0 + fth[k] * (Tw - T0), origin="lower", extent=ext, cmap=cmap, vmin=T0, vmax=Tw, aspect="equal")
            ax.imshow(fin, origin="lower", extent=ext, cmap=matplotlib.colors.ListedColormap([GREY]), aspect="equal")
            if 0 < fal[k].max() and fal[k].min() < 1:
                ax.contour(fal[k], levels=[0.5], origin="lower", extent=ext, colors=BLUE, linewidths=1.2)
            ax.plot([0, 0], [0, m["H_m"] * 1000], color="#a8401a", lw=4, solid_capstyle="butt", clip_on=False)
            ax.set_title(f"{lab}, {t_min[k]:.0f} min", color=INK, fontsize=8.5)
            ax.set_xticks([0, round(m["W_m"] * 1000)]); ax.set_yticks([0, 100] if j == 0 else [])
            if j == 0:
                ax.set_ylabel("mm")
    cb = fig.colorbar(im, ax=fig.axes[:4 * rows], fraction=0.02, pad=0.03)
    cb.set_label("T (C)")
    ax = fig.add_subplot(gs[rows, 0:2])
    if sd_frac is not None:
        ax.fill_between(t_min, frac - sd_frac, frac + sd_frac, color=BLUE, alpha=0.18, lw=0, label="seed spread (1 sd)")
    if true is not None:
        ax.plot(t_min, true[2], color=INK2, lw=2, label="CFD")
    ax.plot(t_min, frac, color=BLUE, lw=2, label="predicted")
    ax.set_xlabel("t (min)"); ax.set_ylabel("melted fraction"); ax.set_ylim(0, 1.02); ax.grid(color=GRID, lw=0.6)
    ax.legend(frameon=False, fontsize=7.5)
    ax = fig.add_subplot(gs[rows, 2:4])
    if true is not None:
        ax.plot(t_min, true[3], color=INK2, lw=2, label="CFD")
    ax.plot(t_min, energy, color=ORANGE, lw=2, label="predicted")
    ax.set_xlabel("t (min)"); ax.set_ylabel("stored energy / full charge"); ax.set_ylim(0, 1.02); ax.grid(color=GRID, lw=0.6)
    ax.legend(frameon=False, fontsize=7.5)
    fins = f"{m['nfins']} fins {m['fin_len_m'] * 1000:g} x {m['fin_t_m'] * 1000:g} mm" if m.get("nfins") else "no fins"
    tilt = {0: "side heated", 90: "heated from below"}.get(round(m.get("tilt_deg", 0)), f"tilted {m.get('tilt_deg'):g} deg")
    fig.suptitle(f"{m['case']}: {m['material']}, W {m['W_m'] * 1000:g} mm, {fins}, {tilt}, wall {Tw:.1f} C, "
                 f"start {T0:.1f} C, Ra {m['Ra_H']:.3g}  (heated wall left, melt front blue)",
                 color=INK, fontsize=9, y=0.95 if rows == 2 else 0.99)
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_argument_group("case (design parameters)")
    g.add_argument("--material", choices=["octadecane", "lauric"], default="octadecane")
    g.add_argument("--tw", type=float, help="heated-wall temperature (C); dataset: 8 to 30 K above the melting "
                                            "point (octadecane 28 C, lauric acid range midpoint 45.85 C)")
    g.add_argument("--t0", type=float, help="initial temperature (C); dataset: 0.5 to 20 K below the solidus "
                                            "(octadecane 27.99 C, lauric acid 43.5 C)")
    g.add_argument("--W", type=float, help="enclosure width (m), dataset 0.02 to 0.06 (height 0.1 m)")
    g.add_argument("--nfins", type=int, default=0, help="fins on the heated wall, dataset 0 to 5")
    g.add_argument("--fin-len", type=float, default=0.0, help="fin length (m), dataset 0.2 to 0.8 of W")
    g.add_argument("--fin-t", type=float, default=0.0, help="fin thickness (m), dataset 0.001 to 0.004")
    g.add_argument("--tilt", type=float, default=0.0, help="0 side heating, 45, 90 heated from below")
    g.add_argument("--name", default="new_pcm_case")
    ap.add_argument("--from-run", help="a dataset run_id: predict it and score against its CFD")
    ap.add_argument("--model", default="fno_hybrid")
    ap.add_argument("--split", default="random", choices=SPLITS)
    ap.add_argument("--results", default="results_pcm", help="results folder holding ckpt/ (merged final results)")
    ap.add_argument("--manifest", default=os.path.join(HERE, "manifest_pcm.json"))
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--out", default=os.path.join(HERE, "predictions_pcm"))
    a = ap.parse_args()

    if a.from_run:
        hits = [r for r in index(DEFAULT_ROOTS) if r.run_id == a.from_run]
        if not hits:
            sys.exit(f"{a.from_run}: not found under {DEFAULT_ROOTS}")
        run, name = hits[0], a.from_run
    else:
        need = [k for k in ("tw", "t0", "W") if getattr(a, k) is None]
        if need:
            ap.error("missing " + ", ".join("--" + k for k in need) + " (or use --from-run)")
        # the networks work on a fixed 100 mm x 60 mm grid of 0.5 mm cells: a wider box does not fit
        if not 0.002 <= a.W <= W_MAX + 1e-9:
            ap.error(f"--W must be in [0.002, {W_MAX:g}] m: the networks' grid holds boxes up to {W_MAX * 1000:g} mm wide")
        if not 0 <= a.nfins <= 9 or (a.nfins and not (0 < a.fin_len < a.W and a.fin_t > 0)):
            ap.error("with --nfins > 0 give --fin-len (0 < fin-len < W) and --fin-t > 0")
        if a.tilt not in (0, 45, 90):
            print(f"WARNING: tilt {a.tilt:g} deg; the dataset has 0, 45 and 90 only")
        run, name = VirtualPCMRun(make_meta(a)), a.name
        m = run.meta
        if m["T_wall_K"] <= m["Tmelt_K"] or m["T_init_K"] >= m.get("T_solidus_K", m["Tmelt_K"]):
            ap.error("need --tw above the melting point and --t0 below the solidus (the PCM starts solid)")

    hybrid = "hybrid" in a.model
    arch = a.model.split("_")[0]
    ck = checkpoints(a.results, a.model, a.split)
    if not ck:
        sys.exit(f"no checkpoint ckpt_pcm_{a.model}*_{a.split}.pt in {a.results}/ckpt or {HERE}")
    enc, lo, hi, tau_max = encoder(next(iter(ck.values())), a.split,
                                   a.manifest if os.path.exists(a.manifest) else None, hybrid)

    p = run.params()
    for k, (v, l, h) in enumerate(zip(p, lo, hi)):
        if v < l - 1e-9 or v > h + 1e-9:
            print(f"WARNING: {list(PARAMS)[k]} = {v:.4g} is outside the training range [{l:.4g}, {h:.4g}]: "
                  f"extrapolation, expect larger errors")

    if isinstance(run, VirtualPCMRun):     # predict only over the training runs' tau window
        run.cut(int(np.sum(run.times()[1] <= tau_max + 1e-9)))
    idx = np.arange(len(run.times()[0]))
    th_all, al_all = [], []
    for tag, f in ck.items():
        kw = {"width": 32} if arch == "fno" else {"base": 32}
        net = MODELS[arch](enc.channels, cout=2, **kw)
        net.load_state_dict(torch.load(f, map_location=a.device))
        th, al = Predictor(net.to(a.device), enc, a.device).predict(run, idx)
        th[0], al[0] = 0.0, 0.0                       # t = 0: solid at T0 everywhere (fins included)
        th_all.append(th); al_all.append(al)
    th, al = np.clip(np.mean(th_all, 0), 0, 1), np.mean(al_all, 0)
    al = np.where(run.mask() > 0, al, 0.0)
    fr_all = [curves(t_, a_, run)[0] for t_, a_ in zip(th_all, al_all)]
    sd_frac = np.std(fr_all, 0) if len(ck) > 1 else None
    frac, energy = curves(th, al, run)

    if isinstance(run, VirtualPCMRun):     # stop shortly after full melt, as the CFD runs do
        done = np.nonzero(frac >= STOP)[0]
        if done.size:
            n = min(len(frac), done[0] + 3)
            run.cut(n); th, al, frac, energy = th[:n], al[:n], frac[:n], energy[:n]
            sd_frac = sd_frac[:n] if sd_frac is not None else None
            th_all = [x[:n] for x in th_all]; al_all = [x[:n] for x in al_all]
    t = run.times()[0]
    t50, t90 = pcm_metrics._t_cross(t, frac, 0.5), pcm_metrics._t_cross(t, frac, 0.9)
    m = run.meta
    fins = f"{m['nfins']} fins {m['fin_len_m'] * 1000:g} x {m['fin_t_m'] * 1000:g} mm" if m.get("nfins") else "no fins"
    print(f"{name}: {m['material']}, W {m['W_m'] * 1000:g} mm, {fins}, tilt {m.get('tilt_deg', 0):g}, wall "
          f"{run.Tw - 273.15:.2f} C, start {run.T0 - 273.15:.2f} C; Ra {m['Ra_H']:.3g}, Ste {m['Ste']:.3g}, "
          f"t_ref {run.t_ref / 60:.1f} min, {len(t)} snapshots to {t[-1] / 60:.1f} min")
    print(f"model {a.model}, split {a.split}, seeds {list(ck)}")
    fmt = lambda v: f"{v / 60:.1f} min" if np.isfinite(v) else "not reached"
    print(f"  predicted: half melted {fmt(t50)}, 90 % melted {fmt(t90)}, final melted fraction {frac[-1]:.3f}, "
          f"stored energy {energy[-1]:.3f} of a full charge"
          + (f", seed spread of the melted fraction up to {sd_frac.max():.3f}" if sd_frac is not None else ""))
    if not np.isfinite(t90) and isinstance(run, VirtualPCMRun):
        print(f"  (the prediction stops at tau = {tau_max:.2f}, the latest time in training: {t[-1] / 60:.1f} min)")

    true = None
    if a.from_run:
        tt, ta = run.field("T", theta=True), run.field("alpha")
        tf, te = curves(tt, ta, run)
        true = (tt, ta, tf, te)
        S = m["props"]["cp"] * (m["T_wall_K"] - m["T_init_K"]) / m["props"]["L"]
        s = pcm_metrics.score(th[1:], al[1:], tt[1:], ta[1:], run.mask(), run.Tw - run.T0, S, t[1:])
        t90c = pcm_metrics._t_cross(t, tf, 0.9)
        print(f"  CFD: 90 % melted {fmt(t90c)}")
        print(f"  vs CFD (all {len(t) - 1} snapshots): rmse {s['rmse_K']:.3f} K, liquid fraction rmse "
              f"{s['alpha_rmse']:.3f}, melt-region IoU {s['liquid_iou']:.3f}, melted fraction {s['melt_frac_err']:.4f}, "
              f"energy {s['energy_err']:.4f}, t90 {s['t90_err'] * 100:.1f} %")

    os.makedirs(a.out, exist_ok=True)
    sd_T = np.std(th_all, 0) * (run.Tw - run.T0) if len(ck) > 1 else np.zeros(0)
    sd_a = np.std(al_all, 0) if len(ck) > 1 else np.zeros(0)
    np.savez_compressed(os.path.join(a.out, f"{name}.npz"), T_K=(run.T0 + th * (run.Tw - run.T0)).astype(np.float32),
                        alpha=al.astype(np.float32), T_sd_K=sd_T.astype(np.float32), alpha_sd=sd_a.astype(np.float32),
                        mask=run.mask(), times_s=t, tau=run.times()[1], melted_fraction=frac, energy_fraction=energy,
                        t50_s=t50, t90_s=t90, case_json=json.dumps(m), model=a.model, split=a.split)
    figure(os.path.join(a.out, f"{name}.png"), run, th, al, frac, energy, sd_frac, true)
    print(f"wrote {os.path.join(a.out, name)}.npz and .png")


if __name__ == "__main__":
    main()
