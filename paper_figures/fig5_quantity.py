"""Fig. 5: the preferred model depends on the quantity predicted.
(a) PCM, held-out fins: field RMSE against relative t90 error, every model whose prediction reaches t90 in
    all test runs (seed means; neural seeds as small marks). Data: extra_baselines_2026-11-08/result_ts.json.
(b) Tank: vertical-profile error against near-outlet temperature error, per split, for the calibrated
    multi-node 1D model and the two hybrid + canonical surrogates. Data: multinode_2026-11-08/compare.json.
"""
import json, os
import numpy as np
from matplotlib.lines import Line2D
from style import plt, ARCH, NAME, INK, INK2, GRID, MM, ML, save

R = json.load(open(os.path.join(ML, "extra_baselines_2026-11-08", "result_ts.json")))["splits"]["ood_fins"]["models"]
C = json.load(open(os.path.join(ML, "multinode_2026-11-08", "compare.json")))

fig, (a1, a2) = plt.subplots(1, 2, figsize=(190 * MM, 72 * MM))
# (a)
OFF = {"front": (6, 0, "left"), "knn": (0, 7, "center"), "idw": (0, -8, "center"),
       "fno": (7, 0, "left"), "fno_hybrid": (7, 0, "left"), "unet": (-7, 0, "right"), "unet_hybrid": (7, 3, "left"),
       "transolver": (7, 0, "left"), "transolver_hybrid": (-7, 2, "right")}
for m, lab in (("front", "front model"), ("knn", "kNN"), ("idw", "IDW")):
    a = R[m]["all"]
    a1.scatter(a["rmse_K"], 100 * a["t90_err"], s=22, marker="D", color=ARCH["base"], zorder=3)
    dx, dy, ha = OFF[m]
    a1.annotate(lab, (a["rmse_K"], 100 * a["t90_err"]), xytext=(dx, dy), textcoords="offset points", fontsize=6.5,
                color=INK2, va="center", ha=ha)
for arch in ("fno", "unet", "transolver"):
    for hyb in (False, True):
        m = arch + ("_hybrid" if hyb else "")
        a = R[m]["all"]
        col = ARCH[arch]
        a1.scatter(a["rmse_K"], 100 * a["t90_err"], s=34, marker="o", facecolor="white" if hyb else col,
                   edgecolor=col, linewidth=1.3, zorder=4)
        dx, dy, ha = OFF[m]
        a1.annotate(NAME[arch] + (" hybrid" if hyb else ""), (a["rmse_K"], 100 * a["t90_err"]), xytext=(dx, dy),
                    textcoords="offset points", fontsize=6.5, color=INK, va="center", ha=ha)
a1.set_xscale("log"); a1.set_yscale("log")
a1.set_xlim(1.2, 14); a1.set_ylim(4, 50)
import matplotlib.ticker as mt
a1.set_xticks([2, 3, 5, 10]); a1.set_xticklabels(["2", "3", "5", "10"])
a1.xaxis.set_minor_formatter(mt.NullFormatter()); a1.yaxis.set_minor_formatter(mt.NullFormatter())
a1.set_yticks([5, 10, 20, 50]); a1.set_yticklabels(["5", "10", "20", "50"])
a1.set_xlabel("Field RMSE (K), log scale"); a1.set_ylabel("Relative t90 error (%), log scale")
a1.set_title("(a) PCM, held-out fin counts (139 runs)", loc="left")

# (b)
SPL = [("random", "random", "o"), ("ood_geom", "unseen width", "s"), ("ood_mode", "discharge", "^"), ("ood_flow", "faster inflow", "D")]
MOD = [("multinode", "multi-node 1D", ARCH["base"]), ("fno_hybrid_canon", "FNO hybrid + canonical", ARCH["fno"]),
       ("unet_hybrid_canon", "U-Net hybrid + canonical", ARCH["unet"])]
for s, slab, mk in SPL:
    met = C[s]["metrics"]
    pts = []
    for m, lab, col in MOD:
        x = met["T_out_err_K"]["multinode_mean"] if m == "multinode" else met["T_out_err_K"][m]["mean"]
        y = met["profile_rmse"]["multinode_mean"] if m == "multinode" else met["profile_rmse"][m]["mean"]
        pts.append((x, y))
        a2.scatter(x, y, s=30, marker=mk, color=col, zorder=3, edgecolor="white", linewidth=0.5)
    xs, ys = zip(*pts)
    a2.plot([xs[0], xs[1]], [ys[0], ys[1]], color=GRID, lw=0.8, zorder=1)
    a2.plot([xs[0], xs[2]], [ys[0], ys[2]], color=GRID, lw=0.8, zorder=1)
a2.set_xlabel("Near-outlet temperature error (K)"); a2.set_ylabel("Vertical-profile error, % of ΔT")
a2.set_xlim(0.4, 2.2); a2.set_ylim(0, 15)
a2.set_title("(b) Tank, per split (seed means)", loc="left")
h = [Line2D([], [], marker="o", ls="", color=col, markersize=4.5, label=lab) for _, lab, col in MOD]
h += [Line2D([], [], marker=mk, ls="", color=INK2, markerfacecolor="white", markersize=4.5, label=slab) for _, slab, mk in SPL]
a2.legend(handles=h, loc="upper left", fontsize=6.3, ncol=2, columnspacing=1.0)
fig.tight_layout(w_pad=2.5)
save(fig, "fig5_quantity")
