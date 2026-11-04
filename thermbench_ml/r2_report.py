"""R2 and confidence report for a results folder (results/<split>.json written by evaluate.py
and train.py with metrics.score's pooled-statistics keys).

  python r2_report.py results_interim_2026-11-02          -> prints and writes r2_report.md there

For every split and model:
  R2 field (pooled)   1 - SSE / SS of theta over every scored cell of every test run
  R2 field (per run)  mean of each run's own field R2 (harder: within-run variance only)
  R2 energy           stored-energy fraction, pooled over test runs x snapshots
  R2 thermocline      thermocline height y_mid (snapshots where both have one)
  R2 T_out            outlet temperature in kelvin
  RMSE / MAE for the same quantities
95 % confidence intervals: bootstrap over test runs (2000 resamples; the run, not the
snapshot, is the independent unit). Seeds: models trained with several seeds (name, name_s1,
...) are also summarised as mean +- sd across seeds.
"""
import glob
import json
import os
import re
import sys

import numpy as np

RNG = np.random.default_rng(0)
B = 2000


def r2(t, p):
    t, p = np.asarray(t, float), np.asarray(p, float)
    ok = np.isfinite(t) & np.isfinite(p)
    t, p = t[ok], p[ok]
    if len(t) < 3 or np.var(t) == 0:
        return np.nan
    return 1 - np.sum((t - p) ** 2) / np.sum((t - t.mean()) ** 2)


def stats(per_run):
    """Point estimates of every quantity from a list of per-run dicts."""
    dT = [r["rmse_K"] / r["rmse_theta"] if r["rmse_theta"] > 0 else np.nan for r in per_run]
    sse = sum(r["_sse"] for r in per_run)
    n = sum(r["_n"] for r in per_run)
    s1, s2 = sum(r["_sum"] for r in per_run), sum(r["_sumsq"] for r in per_run)
    out = {"R2_field_pooled": 1 - sse / (s2 - s1 ** 2 / n)}
    out["R2_field_per_run"] = float(np.nanmean([r["r2_field"] for r in per_run]))
    cat = lambda k, scale=None: np.concatenate([np.asarray(r[k], float) * (1 if scale is None else scale[i])
                                                for i, r in enumerate(per_run)])
    pairs = {"energy": (cat("_e_true"), cat("_e_pred")),
             "thermocline_m": (cat("_ymid_true"), cat("_ymid_pred")),
             "T_out_K": (cat("_out_true", dT), cat("_out_pred", dT))}
    for name, (t, p) in pairs.items():
        ok = np.isfinite(t) & np.isfinite(p)
        out[f"R2_{name}"] = r2(t, p)
        out[f"RMSE_{name}"] = float(np.sqrt(np.mean((t[ok] - p[ok]) ** 2))) if ok.any() else np.nan
        out[f"MAE_{name}"] = float(np.mean(np.abs(t[ok] - p[ok]))) if ok.any() else np.nan
    out["RMSE_field_K"] = float(np.mean([r["rmse_K"] for r in per_run]))
    return out


def with_ci(per_run):
    point = stats(per_run)
    boots = []
    for _ in range(B):
        idx = RNG.integers(0, len(per_run), len(per_run))
        boots.append(stats([per_run[i] for i in idx]))
    ci = {k: (np.nanpercentile([b[k] for b in boots], 2.5), np.nanpercentile([b[k] for b in boots], 97.5))
          for k in point}
    return point, ci


KEYS = [("R2_field_pooled", "R2 field", 3), ("R2_energy", "R2 energy", 3), ("R2_thermocline_m", "R2 thermocline", 3),
        ("R2_T_out_K", "R2 T_out", 3), ("RMSE_field_K", "field RMSE K", 2), ("MAE_T_out_K", "T_out MAE K", 2),
        ("MAE_thermocline_m", "thermocline MAE m", 3), ("MAE_energy", "energy MAE", 4)]


def main():
    folder = sys.argv[1]
    lines = [f"# R2 and confidence report: {os.path.basename(os.path.normpath(folder))}", "",
             "Point estimate [95 % bootstrap CI over test runs]. R2 field is pooled over all test cells "
             "(theta); energy, thermocline and T_out are pooled over test runs x scored snapshots.", ""]
    for path in sorted(glob.glob(os.path.join(folder, "*.json"))):
        d = json.load(open(path))
        if "results" not in d:
            continue
        sp = d["split"]
        lines += [f"## {sp}  (runs: {d['sizes']})", "",
                  "| model | " + " | ".join(k[1] for k in KEYS) + " |", "|---" * (len(KEYS) + 1) + "|"]
        seeds = {}
        for name, res in d["results"].items():
            pr = res.get("per_run", [])
            if not pr or "_sse" not in pr[0]:
                continue
            point, ci = with_ci(pr)
            cells = [f"{point[k]:.{dg}f} [{ci[k][0]:.{dg}f}, {ci[k][1]:.{dg}f}]" for k, _, dg in KEYS]
            lines.append(f"| {name} | " + " | ".join(cells) + " |")
            seeds.setdefault(re.sub(r"_s\d+$", "", name), []).append(point)
        multi = {k: v for k, v in seeds.items() if len(v) > 1}
        if multi:
            lines += ["", "Across training seeds (mean +- sd):", ""]
            for name, pts in multi.items():
                lines.append(f"- {name} ({len(pts)} seeds): " + ", ".join(
                    f"{lab} {np.mean([p[k] for p in pts]):.{dg}f} +- {np.std([p[k] for p in pts], ddof=1):.{dg}f}"
                    for k, lab, dg in KEYS[:5]))
        lines.append("")
    text = "\n".join(lines)
    open(os.path.join(folder, "r2_report.md"), "w").write(text)
    print(text)


if __name__ == "__main__":
    main()
