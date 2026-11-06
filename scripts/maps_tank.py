"""Error-field maps for one comparison: reference T, test T (finer grid block-averaged onto the coarser) and
their difference, at three moments: mid-way to the outlet event, the outlet event, and late (2026-11-07).
usage: maps_tank.py label test.h5 ref.h5 out.png"""
import json, sys
import numpy as np, h5py
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
lab, ft, fr, png = sys.argv[1:5]
def coarsen(a, k):
    ny, nx = a.shape; return a.reshape(ny // k, k, nx // k, k).mean((1, 3))
with h5py.File(ft) as a, h5py.File(fr) as b:
    cj = json.loads(b.attrs["case_json"]); dT = abs(cj["T_in_K"] - cj["T_init_K"])
    ta, tb = a["times_s"][:], b["times_s"][:]
    To = b["series/T_out_K"][:]; so = b["series/T_out_t_s"][:]; ch = np.abs(To - To[0])
    t_ev = float(so[np.argmax(ch > 0.1 * ch.max())]) if ch.max() > 0 else tb[-1] / 2
    moments = [("before outlet event", t_ev / 2), ("outlet event", t_ev), ("late", min(t_ev + 0.6 * (tb[-1] - t_ev), tb[-1]))]
    fig, ax = plt.subplots(3, 3, figsize=(12, 3.6 * 3 * cj["H_m"] / max(cj["W_m"], 0.35) / 2.2 + 2))
    for r, (name, tt) in enumerate(moments):
        kb = int(np.argmin(np.abs(tb - tt))); ka = int(np.argmin(np.abs(ta - tb[kb])))
        B = b["fields/T"][kb] - 273.15; A = a["fields/T"][ka] - 273.15
        if A.shape[0] > B.shape[0]: A = coarsen(A, A.shape[0] // B.shape[0])
        elif B.shape[0] > A.shape[0]: B = coarsen(B, B.shape[0] // A.shape[0])
        lo, hi = min(A.min(), B.min()), max(A.max(), B.max()); D = A - B; m = max(abs(D).max(), 1e-6)
        for c, (F, title, cmap, vl) in enumerate([(B, "reference", "inferno", (lo, hi)), (A, "test", "inferno", (lo, hi)),
                                                  (D, f"test - reference (RMS {100*np.sqrt((D**2).mean())/dT:.2f} % dT)", "RdBu_r", (-m, m))]):
            im = ax[r, c].imshow(F, origin="lower", cmap=cmap, vmin=vl[0], vmax=vl[1], extent=[0, cj["W_m"], 0, cj["H_m"]])
            ax[r, c].set_title(f"{name}, t = {tb[kb]:.0f} s: {title}", fontsize=8); fig.colorbar(im, ax=ax[r, c], fraction=0.046)
    fig.suptitle(f"{lab}  (T in C)"); fig.tight_layout(); fig.savefig(png, dpi=100); print("wrote", png)
