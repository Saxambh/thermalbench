"""Fig. 3: tank family. (a) Discharge (ood_mode, never seen in training): field error of every FNO and U-Net
variant, per seed and seed mean, with the baselines. (b) Per-run field error of the two hybrid + canonical
models (seed mean) against the bulk Richardson number Ri, on all test runs of the four splits.
Data: results_merged/<split>.json (per-run rmse_theta), design_v2_full.csv (Ri, turbulence model),
multinode_2026-11-08/compare.json (multi-node mean)."""
import csv, json, os
import numpy as np
from matplotlib.lines import Line2D
from style import plt, ARCH, NAME, INK, INK2, GRID, MM, ML, ROOT, save

res = json.load(open(os.path.join(ML, "results_merged", "ood_mode.json")))["results"]
mn = json.load(open(os.path.join(ML, "multinode_2026-11-08", "compare.json")))
VARS = [("", "plain"), ("_canon", "canonical frame"), ("_hybrid", "hybrid"), ("_hybrid_canon", "hybrid +\ncanonical")]

fig, (a1, a2) = plt.subplots(1, 2, figsize=(190 * MM, 70 * MM), gridspec_kw={"width_ratios": [1, 1.25]})
# (a) discharge, per variant
for j, arch in enumerate(("fno", "unet")):
    for i, (v, lab) in enumerate(VARS):
        x = i + (j - 0.5) * 0.28
        seeds = [100 * np.mean([p["rmse_theta"] for p in res[f"{arch}{v}{s}"]["per_run"]]) for s in ("", "_s1", "_s2")]
        a1.scatter([x] * 3, seeds, s=14, color=ARCH[arch], zorder=3, linewidth=0)
        a1.plot([x - 0.1, x + 0.1], [np.mean(seeds)] * 2, color=INK, lw=1.3, zorder=4)
best_i = min(("knn", "nn", "idw", "rbf"), key=lambda m: np.mean([p["rmse_theta"] for p in res[m]["per_run"]]))
for ref, lab, ls in ((100 * np.mean([p["rmse_theta"] for p in res[best_i]["per_run"]]), f"best interpolation ({best_i.upper()})", (0, (1, 1.5))),
                     (mn["ood_mode"]["metrics"]["rmse_theta"]["multinode_mean"], "multi-node 1D", (0, (4, 2))),
                     (100 * np.mean([p["rmse_theta"] for p in res["ideal_stratified"]["per_run"]]), "1D ideal stratification", (0, (6, 2, 1, 2)))):
    a1.axhline(ref, color=INK2, lw=0.9, ls=ls, zorder=1)
    a1.text(3.55, ref * 1.06, lab, ha="right", va="bottom", fontsize=6.5, color=INK2)
a1.set_yscale("log"); a1.set_ylim(3, 100)
a1.set_yticks([3, 5, 10, 20, 50, 100]); a1.set_yticklabels(["3", "5", "10", "20", "50", "100"])
a1.set_xticks(range(4)); a1.set_xticklabels([l for _, l in VARS])
a1.set_xlim(-0.5, 3.6)
a1.set_ylabel("Field RMSE, % of ΔT (log scale)")
a1.set_title("(a) Discharge, trained on charging only", loc="left")
a1.legend(handles=[Line2D([], [], marker="o", ls="", color=ARCH["fno"], markersize=4, label="FNO seed"),
                   Line2D([], [], marker="o", ls="", color=ARCH["unet"], markersize=4, label="U-Net seed"),
                   Line2D([], [], marker="_", ls="", color=INK, markersize=8, markeredgewidth=1.3, label="mean of 3 seeds")],
          loc="upper right", fontsize=6.5, bbox_to_anchor=(1.0, 0.86))

# (b) per-run error vs Ri
des = {r["run_id"]: r for r in csv.DictReader(open(os.path.join(ROOT, "design_v2_full.csv")))}
for arch, mk in (("fno", "o"), ("unet", "s")):
    xs, ys, turb = [], [], []
    for split in ("random", "ood_geom", "ood_mode", "ood_flow"):
        r = json.load(open(os.path.join(ML, "results_merged", f"{split}.json")))["results"]
        per = [{p["run_id"]: p["rmse_theta"] for p in r[f"{arch}_hybrid_canon{s}"]["per_run"]} for s in ("", "_s1", "_s2")]
        for rid in per[0]:
            xs.append(float(des[rid]["Ri"])); ys.append(100 * np.mean([d[rid] for d in per])); turb.append(des[rid]["turb"])
    xs, ys, turb = map(np.array, (xs, ys, turb))
    for t, face in (("laminar", "white"), ("kOmegaSST", ARCH[arch])):
        k = turb == t
        a2.scatter(xs[k], ys[k], s=7, marker=mk, facecolor=face if t == "kOmegaSST" else "none", edgecolor=ARCH[arch],
                   linewidth=0.6, alpha=0.8, zorder=3 if t == "kOmegaSST" else 2)
a2.set_xscale("log"); a2.set_yscale("log")
a2.set_xlabel("Bulk Richardson number Ri (log scale)"); a2.set_ylabel("Field RMSE, % of ΔT (log scale)")
a2.set_yticks([1, 2, 5, 10, 20, 50]); a2.set_yticklabels(["1", "2", "5", "10", "20", "50"])
a2.axhline(10, color=GRID, lw=0.8, zorder=0)
a2.set_title("(b) Per test run, hybrid + canonical models", loc="left")
a2.legend(handles=[Line2D([], [], marker="o", ls="", markerfacecolor=ARCH["fno"], markeredgecolor=ARCH["fno"], markersize=4, label="FNO, SST run"),
                   Line2D([], [], marker="o", ls="", markerfacecolor="none", markeredgecolor=ARCH["fno"], markersize=4, label="FNO, laminar run"),
                   Line2D([], [], marker="s", ls="", markerfacecolor=ARCH["unet"], markeredgecolor=ARCH["unet"], markersize=4, label="U-Net, SST run"),
                   Line2D([], [], marker="s", ls="", markerfacecolor="none", markeredgecolor=ARCH["unet"], markersize=4, label="U-Net, laminar run")],
           loc="lower left", fontsize=6.5, frameon=True, framealpha=0.92, edgecolor="none")
fig.tight_layout(w_pad=2.5)
save(fig, "fig3_tank")
