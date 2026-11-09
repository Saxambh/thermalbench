"""Graphical abstract: the benchmark (left) and its headline result (right): field error of the best neural
operator relative to IDW interpolation on each PCM test split (best neural seed-mean RMSE / IDW RMSE, from
extra_baselines_2026-11-08/result_ts.json), log scale with the parity line. Journal: at least 1328 px wide,
readable at 13 cm."""
import json, os
import numpy as np
from matplotlib.patches import Rectangle
from style import plt, ARCH, INK, INK2, GRID, MM, ML, OUT

R = json.load(open(os.path.join(ML, "extra_baselines_2026-11-08", "result_ts.json")))["splits"]
NEU = ["fno", "fno_hybrid", "unet", "unet_hybrid", "transolver", "transolver_hybrid"]
SPL = [("random", "random"), ("ood_drive", "stronger heating"), ("ood_fins", "held-out fins"), ("ood_tilt", "unseen tilt"),
       ("ood_material", "lauric acid\n(trained on octadecane)"), ("ood_material_r", "n-octadecane\n(trained on lauric acid)")]
ratio = []
for s, _ in SPL:
    M = R[s]["models"]
    best = min(M[m]["all"]["rmse_K"] for m in NEU)
    ratio.append(best / M["idw"]["all"]["rmse_K"])

fig = plt.figure(figsize=(130 * MM, 60 * MM))
a0 = fig.add_axes([0.0, 0.0, 0.40, 1.0]); a0.set_axis_off(); a0.set_xlim(0, 1); a0.set_ylim(0, 1)
a0.text(0.03, 0.92, "ThermalStorageBench", fontsize=10, weight="bold", color=INK)
a0.text(0.03, 0.84, "open CFD benchmark for ML in storage", fontsize=6.8, color=INK2)
# tank icon
a0.add_patch(Rectangle((0.06, 0.30), 0.22, 0.42, fill=False, ec=INK2, lw=1.2))
a0.add_patch(Rectangle((0.06, 0.52), 0.22, 0.20, color="#c8423a", alpha=0.25, lw=0))
a0.add_patch(Rectangle((0.06, 0.30), 0.22, 0.22, color="#2f6db3", alpha=0.2, lw=0))
a0.text(0.17, 0.22, "1,212 tank\nruns", ha="center", va="top", fontsize=6.8, color=INK)
a0.text(0.17, 0.10, "(sensible)", ha="center", va="top", fontsize=6.3, color=INK2)
# PCM icon
a0.add_patch(Rectangle((0.42, 0.30), 0.12, 0.42, fill=False, ec=INK2, lw=1.2))
a0.plot([0.42, 0.42], [0.30, 0.72], color="#c8423a", lw=3)
for y in (0.42, 0.52, 0.62):
    a0.plot([0.42, 0.48], [y, y], color=INK2, lw=1.4)
a0.text(0.48, 0.22, "500 PCM\nruns", ha="center", va="top", fontsize=6.8, color=INK)
a0.text(0.48, 0.10, "(latent)", ha="center", va="top", fontsize=6.3, color=INK2)
a0.text(0.03, -0.06, "fixed splits · engineering metrics · verified · validated", fontsize=6.0, color=INK2)
a0.annotate("", (0.98, 0.5), (0.66, 0.5), arrowprops=dict(arrowstyle="-|>", color=INK2, lw=1.2))
a0.text(0.82, 0.55, "test FNO,\nU-Net,\nTransolver", ha="center", va="bottom", fontsize=6.3, color=INK2)

a1 = fig.add_axes([0.62, 0.20, 0.36, 0.66])
y = np.arange(len(SPL))[::-1]
for yi, r in zip(y, ratio):
    col = ARCH["fno"] if r < 1 else "#c8423a"
    a1.plot([1, r], [yi, yi], color=col, lw=1.4)
    a1.scatter([r], [yi], s=26, color=col, zorder=3)
a1.axvline(1, color=INK2, lw=0.9, ls=(0, (4, 2)))
a1.set_xscale("log"); a1.set_xlim(0.15, 3); a1.set_xticks([0.2, 0.5, 1, 2]); a1.set_xticklabels(["0.2", "0.5", "1", "2"])
a1.set_yticks(y); a1.set_yticklabels([l for _, l in SPL], fontsize=6.2)
a1.set_xlabel("best neural error / interpolation error", fontsize=6.5)
a1.set_title("PCM: neural models win within a material,\nlose when the material changes", fontsize=7, loc="right")
os.makedirs(OUT, exist_ok=True)
fig.savefig(os.path.join(OUT, "graphical_abstract.png"), dpi=400, bbox_inches="tight")
fig.savefig(os.path.join(OUT, "graphical_abstract.pdf"), bbox_inches="tight")
print("ratios", [round(r, 2) for r in ratio])
from PIL import Image
print("pixels", Image.open(os.path.join(OUT, "graphical_abstract.png")).size)
