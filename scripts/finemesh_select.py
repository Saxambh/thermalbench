#!/usr/bin/env python3
"""PCM fine-mesh label check (10 November 2026): pre-registered case selection.
Plan: thermbench_ml/finemesh_2026-11-10/PLAN.md (committed before any run).

Selects 60 dataset cases to rerun at h = 0.25 mm (dataset: 0.5 mm), with exactly the dataset case's own
generator arguments except --h (as the 4 November spot check, spot_pcm.csv).

Eligibility:
  - solver_qc "ok" in pcm_inventory_2026-11-07.csv (the 34 reruns used a different pressure solver and
    the 39 solver-WARN cases are excluded, so fine and dataset runs share one solver set-up);
  - predicted fine-mesh cost <= CAP core-hours, from the campaign's own cost model (pcm_design.py):
    the dataset estimate scaled by 4 (cells) x the time-step ratio (Courant limit, capped at maxdt).
Strata (each case in the first that applies, by its test membership in the frozen splits):
  random (test of 'random'), drive (test of ood_drive), fins (test of ood_fins), tilt45 / tilt90 (test of
  ood_tilt by angle), other (in no test set except a material split).
Quota: random 10, drive 10, fins 10, tilt45 6, tilt90 6, other 18 = 60, each half lauric acid and half
n-octadecane, so each material-transfer test set gets 30 cases.
Order within a stratum and material: sha256(case_id + SALT); the first eligible cases are taken.
Writes scripts/fine_pcm.csv (pcm_batch.sh format) and thermbench_ml/finemesh_2026-11-10/selection.json.
"""
import csv, hashlib, json, math, os, sys
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(R, "thermbench_ml"))
from pcm_data import DEFAULT_ROOTS, index
from pcm_splits import side

CAP = 36.0                      # predicted core-hours per fine case (see PLAN.md for the margin)
SALT = "finemesh-2026-11-10"
QUOTA = {"random": 10, "drive": 10, "fins": 10, "tilt45": 6, "tilt90": 6, "other": 18}
H_FINE = 0.00025


def dt(h, maxdt, sh):
    return min(maxdt, 0.1 * (h / 0.0005) * math.sqrt(26.5 / sh))


def main():
    runs = {r.run_id: r for r in index(DEFAULT_ROOTS, manifest=os.path.join(R, "thermbench_ml", "manifest_pcm.json"))}
    inv = {r["case_id"]: r for r in csv.DictReader(open(os.path.join(R, "pcm_inventory_2026-11-07.csv")))}
    design = {r["case_id"]: r for r in csv.DictReader(open(os.path.join(R, "scripts", "pcm_full.csv")))}
    assert len(runs) == 500
    pool, n_elig = {}, 0
    for cid, d in design.items():
        if cid not in runs:
            continue
        sh, maxdt = float(d["superheat_K"]), float(d["maxdt_s"])
        fine = float(d["core_h_est"]) * 4 * dt(0.0005, maxdt, sh) / dt(H_FINE, maxdt, sh)
        r = runs[cid]
        if side(r, "random") == "test":
            st = "random"
        elif side(r, "ood_drive") == "test":
            st = "drive"
        elif side(r, "ood_fins") == "test":
            st = "fins"
        elif side(r, "ood_tilt") == "test":
            st = "tilt45" if float(d["tilt_deg"]) == 45 else "tilt90"
        else:
            st = "other"
        ok = inv[cid]["solver_qc"] == "ok" and fine <= CAP
        n_elig += ok
        pool.setdefault((st, d["material"]), []).append(
            (hashlib.sha256((cid + SALT).encode()).hexdigest(), cid, round(fine, 1), ok))
    chosen, report = [], {}
    for st, q in QUOTA.items():
        for mat in ("lauric", "octadecane"):
            cand = sorted(pool.get((st, mat), []))
            elig = [c for c in cand if c[3]]
            take = elig[: q // 2]
            if len(take) < q // 2:
                sys.exit(f"stratum {st}/{mat}: only {len(take)} eligible of {q // 2} needed")
            chosen += [(st, mat) + c[1:3] for c in take]
            report[f"{st}/{mat}"] = {"in_stratum": len(cand), "eligible": len(elig), "taken": [c[1] for c in take]}
    rows = []
    for st, mat, cid, fine in chosen:
        d = dict(design[cid])
        assert "--h 0.0005" in d["args"]
        d["args"] = d["args"].replace("--h 0.0005", f"--h {H_FINE:g}")
        d["h_m"], d["core_h_est"] = H_FINE, fine
        rows.append(d)
    with open(os.path.join(R, "scripts", "fine_pcm.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(design[next(iter(design))].keys()))
        w.writeheader(); w.writerows(rows)
    out = {"cap_core_h": CAP, "salt": SALT, "quota": QUOTA, "eligible_total": int(n_elig),
           "strata": report, "predicted_core_h_total": round(sum(r["core_h_est"] for r in rows), 1),
           "predicted_core_h_max": max(r["core_h_est"] for r in rows),
           "cases": [{"case_id": c, "stratum": s, "material": m, "pred_core_h": p} for s, m, c, p in chosen]}
    os.makedirs(os.path.join(R, "thermbench_ml", "finemesh_2026-11-10"), exist_ok=True)
    json.dump(out, open(os.path.join(R, "thermbench_ml", "finemesh_2026-11-10", "selection.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k not in ("cases",)}, indent=1))


if __name__ == "__main__":
    main()
