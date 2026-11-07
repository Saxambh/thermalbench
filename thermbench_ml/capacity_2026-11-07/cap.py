import json, glob, csv, os, numpy as np
from scipy.stats import spearmanr
R = "/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench"
des = {r["run_id"]: r for r in csv.DictReader(open(f"{R}/design_v2_full.csv"))}
J = os.path.expanduser("~/tb_verify/mljson"); out = {}
for sp in ["random", "ood_flow", "ood_geom", "ood_mode"]:
    seeds = {}
    for f in glob.glob(f"{J}/*_{sp}.json"):
        for k, v in json.load(open(f))["results"].items():
            if k == "fno_hybrid_canon" or k.startswith("fno_hybrid_canon_s"): seeds[k] = v
    per = {}
    for k, v in seeds.items():
        for r in v["per_run"]: per.setdefault(r["run_id"], []).append(r)
    ids = sorted(per); M = lambda key: np.array([np.mean([x[key] for x in per[i]]) for i in ids])
    rm = M("rmse_theta") * 100; e = M("energy_err") * 100; pr = M("profile_rmse") * 100; tk = M("T_out_err_K"); ym = M("y_mid_err_m") * 1000; r2 = M("r2_field")
    sd = np.array([np.std([x["rmse_theta"] for x in per[i]]) * 100 for i in ids])
    print(f"\n=== {sp}: seeds {sorted(seeds)} test runs {len(ids)}")
    q = lambda a: f"median {np.median(a):.2f}  p90 {np.percentile(a,90):.2f}  max {a.max():.2f}"
    print(f" field RMSE % dT  mean {rm.mean():.2f}  {q(rm)}   share < 2.8 % (tank mesh unc.) {np.mean(rm<2.8):.0%}  share > 10 % {np.mean(rm>10):.0%}")
    print(f" energy %  {q(e)} | profile % dT {q(pr)} | outlet K {q(tk)} | ymid mm {q(ym)} | R2 median {np.median(r2):.3f} min {r2.min():.3f}")
    print(f" seed spread of field RMSE: median {np.median(sd):.2f}")
    feats = {"Re": "Re", "Ri": "Ri", "W": "W", "u_in": "u_in", "dT": "dT", "tstar": "tstar", "s": "s", "off": "off"}
    cor = {k: spearmanr([float(des[i][c]) for i in ids], rm)[0] for k, c in feats.items()}
    print(" Spearman with field RMSE: " + "  ".join(f"{k} {v:+.2f}" for k, v in cor.items()))
    for g, fn in [("turb", lambda i: des[i]["turb"]), ("mode", lambda i: des[i]["mode"]), ("inlet", lambda i: des[i]["inlet_type"]), ("prestrat", lambda i: "yes" if des[i]["yi"] else "no")]:
        grp = {}
        for i, v in zip(ids, rm): grp.setdefault(fn(i), []).append(v)
        print(f"  by {g}: " + "  ".join(f"{k} n={len(v)} median {np.median(v):.2f}" for k, v in sorted(grp.items())))
    o = np.argsort(rm); pick = {"best": o[0], "median": o[len(o)//2], "p90": o[int(0.9*len(o))], "worst": o[-1]}
    out[sp] = {k: ids[j] for k, j in pick.items()}
    for k, j in pick.items():
        d = des[ids[j]]
        print(f"  {k:6s} {ids[j]}  field {rm[j]:.2f} %  energy {e[j]:.2f} %  outlet {tk[j]:.2f} K  ymid {ym[j]:.1f} mm | {d['mode']} {d['inlet_type']} Re {float(d['Re']):.0f} Ri {float(d['Ri']):.1f} W {d['W']} tstar {d['tstar']} yi {d['yi'] or '-'}")
    worst5 = o[-5:][::-1]
    print("  worst 5: " + ", ".join(f"{ids[j]} {rm[j]:.1f}" for j in worst5))
json.dump(out, open(os.path.expanduser("~/tb_verify/ml_picks.json"), "w"), indent=1)
