import json, os, numpy as np
d = json.load(open(os.path.expanduser("~/tb_verify/ml_calib.json")))
Q = (0.5, 0.9, 0.95); summary = {}
for sp, parts in d.items():
    print(f"\n== {sp}: val {len(parts['val'])} runs, test {len(parts['test'])} runs")
    summary[sp] = {}
    for lvl in ("run", "snapshot"):
        if lvl == "run":
            ev = np.array([r["err"] for r in parts["val"]]); sv = np.array([r["sd"] for r in parts["val"]])
            et = np.array([r["err"] for r in parts["test"]]); st = np.array([r["sd"] for r in parts["test"]])
        else:
            ev = np.concatenate([r["err_snap"] for r in parts["val"]]); sv = np.concatenate([r["sd_snap"] for r in parts["val"]])
            et = np.concatenate([r["err_snap"] for r in parts["test"]]); st = np.concatenate([r["sd_snap"] for r in parts["test"]])
            ok = (sv > 0); ev, sv = ev[ok], sv[ok]; ok = st > 0; et, st = et[ok], st[ok]
        ratio = ev / sv
        print(f"  {lvl} level: error/spread on val median {np.median(ratio):.2f}")
        for q in Q:
            k = np.quantile(ratio, q); c = np.quantile(ev, q)        # spread-scaled vs constant bound
            cov_k = np.mean(et <= k * st); cov_c = np.mean(et <= c)
            w_k = np.median(k * st); w_c = c
            # sharpness at equal coverage: for runs that are actually easy (err below median), how tight is each bound
            easy = et <= np.median(et)
            print(f"    q {q:.2f}: k = {k:.2f}  test coverage {cov_k:.0%} (target {q:.0%}) median bound {w_k:.2f} %  | constant bound {c:.2f} %: coverage {cov_c:.0%}"
                  f" | bound on easy half: spread {np.median((k*st)[easy]):.2f} vs constant {c:.2f}; on hard half: {np.median((k*st)[~easy]):.2f} vs {c:.2f}")
            summary[sp][f"{lvl}_q{q}"] = {"k": float(k), "cov_test": float(cov_k), "const": float(c), "cov_const": float(cov_c)}
json.dump(summary, open(os.path.expanduser("~/tb_verify/ml_calib_summary.json"), "w"), indent=1)
