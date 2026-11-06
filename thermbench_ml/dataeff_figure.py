"""Data-efficiency figure for the tank benchmark (2026-11-06): test error on the random split against the
share of training runs used (dataeff.sh: 5, 10, 25, 50 %, 3 seeds; 100 % = the main benchmark runs of
run_final.sh, added automatically once they are in). Two models: the main model (FNO, physics base, canonical
frame) and plain FNO. Each seed is a dot, the line joins the seed means.
  python3 dataeff_figure.py results_dataeff/random.json [results dirs or random.json files with the 100 % runs...]
Writes figures/dataeff_random.png and .pdf, and prints the table.
"""
import glob
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

MODELS = [("fno_hybrid_canon", "FNO + physics base + canonical frame (main)", "#1f5fa8"),
          ("fno", "FNO (plain)", "#c4661f")]


def load(dataeff, full):
    pts = {m: {} for m, _, _ in MODELS}
    for k, v in json.load(open(dataeff))["results"].items():
        for m, _, _ in MODELS:
            if k.startswith(m + "_f") and k[len(m) + 2:].split("_")[0].isdigit():
                pts[m].setdefault(int(k[len(m) + 2:].split("_")[0]), []).append(v["rmse_K"])
    files = []
    for p in full:
        files += glob.glob(os.path.join(p, "**", "random.json"), recursive=True) if os.path.isdir(p) else [p]
    seen = set()
    for f in files:
        try:
            res = json.load(open(f))["results"]
        except (OSError, ValueError, KeyError):
            continue
        for m, _, _ in MODELS:
            for s in ("", "_s1", "_s2"):
                if m + s in res and (m, s) not in seen:
                    seen.add((m, s)); pts[m].setdefault(100, []).append(res[m + s]["rmse_K"])
    return pts


def main():
    pts = load(sys.argv[1], sys.argv[2:])
    os.makedirs("figures", exist_ok=True)
    fig, ax = plt.subplots(figsize=(5.2, 3.6), dpi=200)
    print(f"{'share %':>8} " + "  ".join(f"{m:>28}" for m, _, _ in MODELS))
    for m, label, c in MODELS:
        xs = sorted(pts[m])
        mean = [np.mean(pts[m][x]) for x in xs]
        for x in xs:
            ax.scatter([x] * len(pts[m][x]), pts[m][x], s=14, color=c, alpha=0.45, linewidths=0, zorder=3)
        ax.plot(xs, mean, color=c, lw=2, marker="o", ms=5, label=label, zorder=4)
    for x in sorted({x for m, _, _ in MODELS for x in pts[m]}):
        row = []
        for m, _, _ in MODELS:
            v = pts[m].get(x, [])
            row.append(f"{np.mean(v):6.2f} ± {np.std(v):4.2f} K (n={len(v)})" if v else f"{'-':>28}")
        print(f"{x:>8} " + "  ".join(f"{r:>28}" for r in row))
    ax.set_xscale("log")
    ax.set_xticks([5, 10, 25, 50, 100]); ax.set_xticklabels(["5", "10", "25", "50", "100"])
    ax.set_xlabel("training runs used (% of the random split's training set)")
    ax.set_ylabel("test RMSE (K)")
    ax.set_ylim(bottom=0)
    ax.grid(True, color="#e3e3e3", lw=0.6); ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    ax.set_title("Data efficiency, tank benchmark (random split, 3 seeds)", fontsize=9)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(f"figures/dataeff_random.{ext}")
    print("wrote figures/dataeff_random.png and .pdf")


if __name__ == "__main__":
    main()
