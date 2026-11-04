"""Benchmark figures from the merged results (<results>/<split>.json), written 2026-11-04 so the
final results become figures in one command:
  python figures.py [--results results] [--family tank|pcm] [--out <results>/figures]
  fig_main      main metric per model, one panel per split (dot = seed mean, bar = +-1 sd over seeds),
                log x axis; colour = architecture (grey baseline, blue FNO, orange U-Net), labels name
                every row; tank: the CFD noise floor (0.65-2 K) shaded
  fig_ablation  tank only: 2 x 2 physics base x canonical frame, rmse_K, one panel per arch x split
  fig_perrun    per-run error of the best neural model against the split's driving parameter
                (tank: inflow Re on ood_flow; PCM: superheat on ood_drive), test runs only
Colours: the validated categorical pair blue #2a78d6 / orange #eb6834 (dataviz validator, light
surface: all checks pass), neutral grey for baselines, a single-hue blue ramp for the heatmap.
PNG (200 dpi) and PDF.
"""
import argparse
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.ticker
import matplotlib.pyplot as plt
import numpy as np

import tables

HERE = os.path.dirname(os.path.abspath(__file__))
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
ARCH = {"fno": ("#2a78d6", "FNO"), "unet": ("#eb6834", "U-Net"), "base": ("#8a8984", "baseline")}
plt.rcParams.update({"font.size": 8.5, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF})


def arch(m):
    return "fno" if m.startswith("fno") else "unet" if m.startswith("unet") else "base"


def save(fig, out, name):
    os.makedirs(out, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(out, f"{name}.{ext}"), dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("wrote", os.path.join(out, name + ".png"))


def fig_main(vals, models, splits, family, out, c="rmse_K"):
    fig, axs = plt.subplots(1, len(splits), figsize=(1.9 * len(splits) + 1.2, 0.24 * len(models) + 1.0),
                            sharey=True, squeeze=False)
    y = np.arange(len(models))[::-1]
    for ax, s in zip(axs[0], splits):
        if family == "tank":
            ax.axvspan(0.65, 2.0, color=GRID, lw=0, zorder=0)
        for yi, m in zip(y, models):
            v = tables.stat(vals, m, s, c)
            if not v.size:
                continue
            col = ARCH[arch(m)][0]
            if v.size > 1:
                ax.plot([v.mean() - v.std(), v.mean() + v.std()], [yi, yi], color=col, lw=2, solid_capstyle="round", zorder=2)
            ax.plot(v.mean(), yi, "o", ms=5, color=col, mec=SURF, mew=1.2, zorder=3)
        ax.set_xscale("log")
        ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
        ax.set_title(s, color=INK, fontsize=9)
        ax.grid(axis="x", color=GRID, lw=0.6, zorder=0)
        ax.set_xlabel(f"{c} (K)" if c.endswith("_K") else c)
    axs[0][0].set_yticks(y, models)
    handles = [plt.Line2D([], [], marker="o", ls="", color=col, label=lab) for col, lab in ARCH.values()]
    if family == "tank":
        handles.append(plt.Rectangle((0, 0), 1, 1, color=GRID, label="CFD noise floor"))
    fig.legend(handles=handles, loc="lower center", ncol=len(handles), frameon=False, bbox_to_anchor=(0.5, -0.02 - 0.1 / max(1, len(models) / 6)))
    save(fig, out, f"fig_main_{family}")


def fig_ablation(vals, splits, out):
    cfg = [("plain", ""), ("canonical", "_canon"), ("physics", "_hybrid"), ("both", "_hybrid_canon")]
    have = [s for s in splits if any(tables.stat(vals, f"{a}{k}", s, "rmse_K").size for a in ("fno", "unet") for _, k in cfg)]
    if not have:
        print("fig_ablation: no ablation results yet"); return
    fig, axs = plt.subplots(2, len(have), figsize=(1.7 * len(have) + 0.6, 3.6), squeeze=False)
    allv = [tables.stat(vals, f"{a}{k}", s, "rmse_K").mean() for a in ("fno", "unet") for _, k in cfg for s in have
            if tables.stat(vals, f"{a}{k}", s, "rmse_K").size]
    lo, hi = np.log10(min(allv)), np.log10(max(allv))
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("blue", ["#cde2fb", "#2a78d6", "#0d366b"])
    for i, a in enumerate(("fno", "unet")):
        for j, s in enumerate(have):
            ax = axs[i][j]
            g = np.full((2, 2), np.nan)
            for (lab, k), (r, cc) in zip(cfg, [(0, 0), (0, 1), (1, 0), (1, 1)]):
                v = tables.stat(vals, f"{a}{k}", s, "rmse_K")
                if v.size:
                    g[r, cc] = v.mean()
            ax.imshow(np.log10(g), cmap=cmap, vmin=lo, vmax=hi)
            for r in range(2):
                for cc in range(2):
                    if np.isfinite(g[r, cc]):
                        dark = (np.log10(g[r, cc]) - lo) / max(hi - lo, 1e-9) > 0.55
                        ax.text(cc, r, f"{g[r, cc]:.2f}", ha="center", va="center", fontsize=8,
                                color=SURF if dark else INK)
            ax.set_xticks([0, 1], ["image", "canonical"] if i == 1 else ["", ""])
            ax.set_yticks([0, 1], ["no base", "physics base"] if j == 0 else ["", ""])
            ax.tick_params(length=0)
            for sp in ax.spines.values():
                sp.set_visible(False)
            if i == 0:
                ax.set_title(s, color=INK, fontsize=9)
        axs[i][0].set_ylabel(ARCH[a][1], color=INK, fontsize=9)
    fig.suptitle("rmse_K (K), mean over seeds", color=INK2, fontsize=8.5, y=0.99)
    save(fig, out, "fig_ablation_tank")


def fig_perrun(vals, models, family, out):
    split, key = ("ood_flow", "Re") if family == "tank" else ("ood_drive", "superheat_K")
    neural = [m for m in models if arch(m) != "base" and tables.stat(vals, m, split, "rmse_K").size]
    if not neural:
        print("fig_perrun: no neural results on", split); return
    best = min(neural, key=lambda m: tables.stat(vals, m, split, "rmse_K").mean())
    design = os.path.join(HERE, "..", "design_v2_full.csv" if family == "tank" else "scripts/pcm_full.csv")
    col = "run_id" if family == "tank" else "case_id"
    par = {r[col]: float(r[key]) for r in csv.DictReader(open(design))}
    fig, ax = plt.subplots(figsize=(4.2, 2.8))
    pts = []
    for m in (best, "knn" if family == "tank" else "front"):
        runs = [r for d in vals.get((m, split), [])[:1] for r in d.get("per_run", [])]
        x = [par.get(r.get("run_id"), np.nan) for r in runs]
        yv = [r["rmse_K"] for r in runs]
        colr = ARCH[arch(m)][0]
        ax.plot(x, yv, "o", ms=4.5, color=colr, mec=SURF, mew=0.8, label=m, alpha=0.9)
        pts += yv
    ax.set_xlabel(key); ax.set_ylabel("rmse_K per test run (K)")
    ax.set_yscale("log"); ax.grid(color=GRID, lw=0.6)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
    if family == "tank":
        ax.set_xscale("log")
    ax.set_title(f"{split}: per test run (seed 0)", color=INK, fontsize=9)
    ax.legend(frameon=False)
    save(fig, out, f"fig_perrun_{family}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results")
    ap.add_argument("--family", default="tank", choices=tables.FAMILY)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = a.out or os.path.join(HERE, a.results, "figures")
    vals, sizes = tables.collect(a.results)
    splits = [s for s in tables.splits_of(a.family) if s in sizes]
    known = tables.FAMILY[a.family]["order"] + sorted({m for m, _ in vals} - set(tables.FAMILY[a.family]["order"]))
    models = [m for m in known if any((m, s) in vals for s in splits)]
    if not splits:
        print(f"figures: no results in {a.results} yet"); return
    fig_main(vals, models, splits, a.family, out)
    if a.family == "tank":
        fig_ablation(vals, splits, out)
    fig_perrun(vals, models, a.family, out)


if __name__ == "__main__":
    main()
