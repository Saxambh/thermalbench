"""Time histories of one or more comparisons from cmp_tank.py json -> PNG (field, profile, stored energy,
thermocline midpoint, outlet T). usage: plot_tank.py in.json out_prefix"""
import json, sys
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
rows = json.load(open(sys.argv[1]))
cases = sorted({r["pair"].split("|")[0] for r in rows})
for c in cases:
    rs = [r for r in rows if r["pair"].startswith(c + "|")]
    fig, ax = plt.subplots(3, 3, figsize=(15, 11)); ax = ax.ravel()
    for r in rs:
        s, lab = r["series"], r["pair"].split("|")[1]
        ax[0].plot(s["t"], s["field_pct"], label=lab); ax[1].plot(s["t"], s["profile_pct"], label=lab)
        ax[2].plot(s["t"], s["dE_pct"], label=lab); ax[3].plot(s["t"], s["dymid_mm"], label=lab)
        ax[4].plot(s["tout_t"], [x - y for x, y in zip(s["tout_test"], s["tout_ref"])], label=lab)
        if "dthick_mm" in s:
            ax[6].plot(s["t"], s["dthick_mm"], label=lab); ax[7].plot(s["t"], s["dMIX"], label=lab)
            ax[8].plot(s["t"], s["backflow_test"], label=lab)
    s = rs[0]["series"]; ax[5].plot(s["tout_t"], s["tout_ref"], "k", label="reference outlet T")
    if "backflow_ref" in s: ax[8].plot(s["t"], s["backflow_ref"], "k", lw=2, label="reference")
    for a_, t in zip(ax, ["field RMSE (% dT)", "horizontal-profile RMSE (% dT)", "stored-energy difference (%)",
                          "thermocline midpoint difference (mm)", "outlet T difference (K)", "outlet T, reference (K)",
                          "thermocline thickness difference (mm)", "MIX difference (-)", "outlet backflow share (cells into tank)"]):
        a_.set_title(t, fontsize=10); a_.set_xlabel("t (s)"); a_.grid(alpha=0.3)
        ev = rs[0]["t_event_s"]
        if ev == ev: a_.axvline(ev, color="grey", ls="--", lw=0.8)
    ax[0].legend(fontsize=8); fig.suptitle(f"{c}: test minus reference at matched times (dashed: outlet event)")
    fig.tight_layout(); fig.savefig(f"{sys.argv[2]}_{c}.png", dpi=110); plt.close(fig); print("wrote", f"{sys.argv[2]}_{c}.png")
