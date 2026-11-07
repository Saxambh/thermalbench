import json, os, numpy as np
R = json.load(open(os.path.expanduser("~/tb_verify/alt_ref.json")))
print("rows", len(R))
for q in ("field_pct", "outlet_event_pct", "energy_proxy_pct", "ymid_mm"):
    print(f"\n== {q}")
    for alt in ("h25", "n4", "co25", "rep"):
        rows = [r for r in R if alt in r["ref_vs_production"]]
        d = {a: [r["scores"][f"{a}_ens"][alt][q] - r["scores"][f"{a}_ens"]["production"][q] for r in rows] for a in ("fno", "unet")}
        gp = np.array([r["scores"]["fno_ens"]["production"][q] - r["scores"]["unet_ens"]["production"][q] for r in rows])
        ga = np.array([r["scores"]["fno_ens"][alt][q] - r["scores"]["unet_ens"][alt][q] for r in rows])
        ok = np.isfinite(gp) & np.isfinite(ga)
        flips = [r["run_id"] + "/" + r["split"] for r, a, b in zip(rows, gp, ga) if np.isfinite(a) and np.isfinite(b) and np.sign(a) != np.sign(b)]
        refd = [r["ref_vs_production"][alt][q] for r in rows]
        print(f"{alt:5s} n {len(rows):2d} | ref vs prod median {np.nanmedian(refd):.2f} max {np.nanmax(refd):.2f} | change fno median {np.nanmedian(d['fno']):+.2f} [{np.nanmin(d['fno']):+.2f},{np.nanmax(d['fno']):+.2f}] unet {np.nanmedian(d['unet']):+.2f} [{np.nanmin(d['unet']):+.2f},{np.nanmax(d['unet']):+.2f}] | gap fno-unet mean prod {np.mean(gp[ok]):+.2f} alt {np.mean(ga[ok]):+.2f} | flips {len(flips)} {flips}")
# per-seed ranking flips (field), any seed pair fno_s vs unet_s
print("\n== seed-level field ranking flips (any fno seed vs any unet seed)")
for alt in ("h25", "n4", "co25", "rep"):
    n = tot = 0
    for r in [r for r in R if alt in r["ref_vs_production"]]:
        S = r["scores"]; fs = [k for k in S if k.startswith("fno") and k != "fno_ens"]; us = [k for k in S if k.startswith("unet") and k != "unet_ens"]
        for f in fs:
            for u in us:
                tot += 1; n += np.sign(S[f]["production"]["field_pct"] - S[u]["production"]["field_pct"]) != np.sign(S[f][alt]["field_pct"] - S[u][alt]["field_pct"])
    print(alt, f"{n} of {tot} seed pairs flip")
print("\n== flagged", [(r["run_id"], r["split"], {a: (round(r["scores"]["fno_ens"][a]["field_pct"], 2), round(r["scores"]["unet_ens"][a]["field_pct"], 2)) for a in r["scores"]["fno_ens"]}) for r in R if r["flagged"]])
print("seeds used", {r["split"]: r["seeds"] for r in R})
