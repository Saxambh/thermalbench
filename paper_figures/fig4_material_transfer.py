"""Fig. 4: material transfer, per-seed field RMSE of every neural variant against IDW, with the t90 crossing
rate, in both directions. Data: extra_baselines_2026-11-08/result_ts.json (same numbers as
pcm_final_2026-11-08 for FNO, U-Net and the baselines)."""
import json, os
import numpy as np
from style import plt, ARCH, NAME, INK, INK2, GRID, MM, ML, save

R = json.load(open(os.path.join(ML, "extra_baselines_2026-11-08", "result_ts.json")))["splits"]
ROWS = [(a, h) for a in ("fno", "unet", "transolver") for h in (False, True)]
PANELS = [("ood_material", "Trained on n-octadecane,\ntested on lauric acid"),
          ("ood_material_r", "Trained on lauric acid,\ntested on n-octadecane")]

fig, axes = plt.subplots(1, 2, figsize=(190 * MM, 62 * MM), sharey=True)
for ax, (split, title) in zip(axes, PANELS):
    M = R[split]["models"]
    idw = M["idw"]["all"]["rmse_K"]
    n = R[split]["n_test"]
    ax.axvline(idw, color=INK2, lw=1.0, ls=(0, (4, 2)), zorder=1)
    ax.text(idw, len(ROWS) - 0.35, f" IDW {idw:.2f} K", color=INK2, va="bottom", ha="left", fontsize=7)
    for i, (a, h) in enumerate(ROWS):
        m = a + ("_hybrid" if h else "")
        y = len(ROWS) - 1 - i
        s = M[m]["all"]["seed_rmse_K"]
        mean = M[m]["all"]["rmse_K"]
        col = ARCH[a]
        ax.axhline(y, color=GRID, lw=0.5, zorder=0)
        ax.scatter(s, [y] * len(s), s=22, marker="o", facecolor="white" if h else col, edgecolor=col,
                   linewidth=1.2, zorder=3)
        ax.plot([mean, mean], [y - 0.28, y + 0.28], color=INK, lw=1.4, zorder=4, solid_capstyle="round")
        cr = M[m]["all"]["n_crossed"] / n
        ax.text(1.16, y, f"{100 * cr:.0f} %", transform=ax.get_yaxis_transform(), ha="right", va="center",
                fontsize=7, color=INK, clip_on=False)
    ax.set_xscale("log")
    ax.set_xlim(2.5, 60)
    ax.set_xticks([3, 5, 10, 20, 50]); ax.set_xticklabels(["3", "5", "10", "20", "50"])
    ax.set_xlabel("Field RMSE (K), log scale")
    ax.set_title(title, loc="left", color=INK)
    ax.text(1.16, len(ROWS) - 0.35, "reach t90", transform=ax.get_yaxis_transform(), ha="right", va="bottom",
            fontsize=7, color=INK2, clip_on=False)
axes[0].set_yticks(range(len(ROWS)))
axes[0].set_yticklabels([f"{NAME[a]}{' hybrid' if h else ''}" for a, h in ROWS][::-1])
axes[0].set_ylim(-0.6, len(ROWS) - 0.1)
# legend for the encodings (marker = seed, bar = seed mean)
from matplotlib.lines import Line2D
hand = [Line2D([], [], marker="o", ls="", color=INK2, markerfacecolor=INK2, markersize=4.5, label="one training seed (plain)"),
        Line2D([], [], marker="o", ls="", color=INK2, markerfacecolor="white", markersize=4.5, label="one training seed (hybrid)"),
        Line2D([], [], marker="|", ls="", color=INK, markersize=8, markeredgewidth=1.4, label="mean of 3 seeds"),
        Line2D([], [], ls=(0, (4, 2)), color=INK2, label="IDW interpolation baseline")]
fig.legend(handles=hand, loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.08), fontsize=7)
fig.tight_layout(w_pad=5)
save(fig, "fig4_material_transfer")
