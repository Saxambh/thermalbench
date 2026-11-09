"""Independent cross-check of every number in the paper's tables and figures (9 November 2026).

Recomputes from the most primary source available, by code separate from the figure/table scripts:
  - per-run scores in results_merged/, results_pcm_merged/, results_pcm_ts_merged/ (not the summary jsons);
  - the frozen manifests and design files (Table 1 facts);
  - the Markdown tables of the validation notes (Fig. 2 data, parsed, not retyped);
  - the outlet series .dat files (Lou numbers quoted in the text).
and compares with the values the tables/figures use (build_tables.py, result_ts.json, compare.json) and with
numbers already reported in the result notes. Writes out/VERIFY_REPORT.md; exits non-zero on any failure.
"""
import csv, glob, json, os, re, sys
import numpy as np
from style import ML, ROOT, OUT
import build_tables as BT

checks = []


def ok(name, cond, detail=""):
    checks.append((bool(cond), name, detail))


def close(a, b, tol):
    return abs(a - b) <= tol


SEEDS = ("", "_s1", "_s2")

# ---------------- Table 2 (tank), independent recomputation
_, t2 = BT.tank()
for s, _ in BT.TANK_SPLITS:
    res = json.load(open(os.path.join(ML, "results_merged", f"{s}.json")))["results"]
    n_test = len(res["idw"]["per_run"])
    ok(f"T2 {s}: test-run count", n_test == {"random": 131, "ood_geom": 224, "ood_mode": 363, "ood_flow": 103}[s], n_test)
    for m, _ in BT.TANK_BASE + BT.TANK_NEURAL:
        if m == "multinode":
            continue
        names = [m] if m in res and m + "_s1" not in res else [m + x for x in SEEDS]
        per_seed = []
        for nm in names:
            v = [p["rmse_theta"] for p in res[nm]["per_run"]]
            assert len(v) == n_test, (s, nm)
            per_seed.append(100 * sum(v) / len(v))
        mu = float(np.mean(per_seed))
        ok(f"T2 {s} {m} mean", close(mu, t2[(m, s)][0], 1e-9), f"{mu:.4f} vs {t2[(m, s)][0]:.4f}")
        if len(per_seed) > 1:
            ok(f"T2 {s} {m} SD", close(float(np.std(per_seed, ddof=1)), t2[(m, s)][1], 1e-9))
        # the aggregate stored by the training job itself
        stored = np.mean([res[nm]["rmse_theta"] for nm in names]) * 100
        ok(f"T2 {s} {m} vs stored aggregate", close(mu, stored, 1e-6), f"{mu:.4f} vs {stored:.4f}")
mn = json.load(open(os.path.join(ML, "multinode_2026-11-08", "compare.json")))
for s, v in (("random", 7.07), ("ood_geom", 7.56), ("ood_mode", 7.58), ("ood_flow", 13.61)):
    ok(f"T2 multinode {s} vs RESULT_tables.md", close(t2[("multinode", s)][0], v, 0.005))
for (m, s, v) in (("fno_hybrid_canon", "ood_mode", 4.48), ("unet_hybrid_canon", "ood_mode", 4.37), ("unet_hybrid_canon", "ood_flow", 9.21),
                  ("fno", "ood_mode", 64.8), ("unet", "ood_mode", 67.0), ("fno_hybrid_canon", "ood_geom", 4.44),
                  ("unet_hybrid_canon", "ood_geom", 6.23), ("rbf", "random", 8.7)):
    ok(f"T2 {m} {s} vs dossier/notes ({v})", close(t2[(m, s)][0], v, 0.051))

# ---------------- Table 3 (PCM), independent recomputation from per-run records
_, t3 = BT.pcm()
for s, _ in BT.PCM_SPLITS:
    a = json.load(open(os.path.join(ML, "results_pcm_merged", f"{s}.json")))["results"]
    a |= {k: v for k, v in json.load(open(os.path.join(ML, "results_pcm_ts_merged", f"{s}.json")))["results"].items() if k.startswith("transolver")}
    for m, _ in BT.PCM_BASE + BT.PCM_NEURAL:
        names = [m] if m + "_s1" not in a else [m + x for x in SEEDS]
        rm, t9, nc = [], [], []
        for nm in names:
            pr = a[nm]["per_run"]
            rm.append(np.mean([p["rmse_K"] for p in pr]))
            cr = [p for p in pr if p["t90_reached"] > 0.5]
            nc.append(len(cr))
            t9.append(np.mean([p["t90_err"] for p in cr]) if cr else np.nan)
        mu = float(np.mean(rm))
        ok(f"T3 {s} {m} field", close(mu, t3[(m, s)][0], 1e-9), f"{mu:.4f} vs {t3[(m, s)][0]:.4f}")
        if len(rm) > 1:
            ok(f"T3 {s} {m} SD", close(float(np.std(rm, ddof=1)), t3[(m, s)][1], 1e-9))
        ok(f"T3 {s} {m} crossed", close(float(np.mean(nc)), t3[(m, s)][3], 1e-9))
        if np.any(np.isfinite(t9)):
            ok(f"T3 {s} {m} t90", close(100 * float(np.nanmean(t9)), t3[(m, s)][2], 1e-7))
# against the committed final notes
for (m, s, v) in (("unet", "random", 0.59), ("unet", "ood_fins", 1.76), ("unet", "ood_drive", 1.05), ("fno", "ood_tilt", 6.17),
                  ("unet_hybrid", "ood_material", 5.61), ("unet_hybrid", "ood_material_r", 7.48), ("idw", "ood_material", 5.35),
                  ("idw", "ood_material_r", 3.55), ("fno", "ood_material_r", 34.45), ("transolver", "ood_fins", 2.31),
                  ("transolver", "ood_material_r", 16.66), ("transolver_hybrid", "ood_material_r", 15.77)):
    ok(f"T3 {m} {s} vs result notes ({v})", close(t3[(m, s)][0], v, 0.0051))
ok("T3 Transolver fins t90 5.6 %", close(t3[("transolver", "ood_fins")][2], 5.6, 0.051))
ok("T3 U-Net fins t90 10.2 %", close(t3[("unet", "ood_fins")][2], 10.2, 0.051))
ok("T3 Transolver material_r reach 2.0 %", close(100 * t3[("transolver", "ood_material_r")][3] / 250, 2.0, 0.01))
ok("T3 Transolver hybrid material_r reach 6.7 %", close(100 * t3[("transolver_hybrid", "ood_material_r")][3] / 250, 6.7, 0.05))

# ---------------- Fig. 4 seeds (per seed, from per-run records)
R = json.load(open(os.path.join(ML, "extra_baselines_2026-11-08", "result_ts.json")))["splits"]
for s in ("ood_material", "ood_material_r"):
    a = json.load(open(os.path.join(ML, "results_pcm_merged", f"{s}.json")))["results"]
    a |= json.load(open(os.path.join(ML, "results_pcm_ts_merged", f"{s}.json")))["results"]
    for m in ("fno", "fno_hybrid", "unet", "unet_hybrid", "transolver", "transolver_hybrid"):
        seeds = [float(np.mean([p["rmse_K"] for p in a[m + x]["per_run"]])) for x in SEEDS]
        ok(f"F4 {s} {m} seeds", np.allclose(seeds, R[s]["models"][m]["all"]["seed_rmse_K"], atol=1e-9))
ok("F4 U-Net hybrid lauric seeds 7.20/4.68/4.96", np.allclose(np.round(R["ood_material"]["models"]["unet_hybrid"]["all"]["seed_rmse_K"], 2), [7.20, 4.68, 4.96]))
ok("F4 U-Net hybrid octadecane seeds 7.07/9.07/6.32", np.allclose(np.round(R["ood_material_r"]["models"]["unet_hybrid"]["all"]["seed_rmse_K"], 2), [7.07, 9.07, 6.32]))

# ---------------- Fig. 3 (a) uses the Table 2 values; (b) point count and the regime statement
des = {r["run_id"]: r for r in csv.DictReader(open(os.path.join(ROOT, "design_v2_full.csv")))}
npts, hi = 0, []
for s in ("random", "ood_geom", "ood_mode", "ood_flow"):
    r = json.load(open(os.path.join(ML, "results_merged", f"{s}.json")))["results"]
    per = [{p["run_id"]: p["rmse_theta"] for p in r[f"fno_hybrid_canon{x}"]["per_run"]} for x in SEEDS]
    for rid in per[0]:
        npts += 1
        e = 100 * np.mean([d[rid] for d in per])
        if e > 10:
            hi.append((des[rid]["turb"], float(des[rid]["Ri"])))
ok("F3b one point per test run (821)", npts == 821, npts)
ok("F3b FNO h+c: every run above 10 % is SST", all(t == "kOmegaSST" for t, _ in hi), f"{len(hi)} runs above 10 %")
ok("F3b FNO h+c: runs above 10 % have Ri below about 9", all(ri < 9.5 for _, ri in hi), f"max Ri {max(ri for _, ri in hi):.2f}")

u_hi, u_lam, u_wide = 0, 0, 0
for s in ("random", "ood_geom", "ood_mode", "ood_flow"):
    r = json.load(open(os.path.join(ML, "results_merged", f"{s}.json")))["results"]
    per = [{p["run_id"]: p["rmse_theta"] for p in r[f"unet_hybrid_canon{x}"]["per_run"]} for x in SEEDS]
    for rid in per[0]:
        if 100 * np.mean([d[rid] for d in per]) > 10:
            u_hi += 1
            if des[rid]["turb"] == "laminar":
                u_lam += 1
                u_wide += s == "ood_geom" and float(des[rid]["W"]) > 0.93
ok("Text: U-Net h+c 18 laminar runs above 10 %, 17 of them unseen widths W > 0.93 m", (u_lam, u_wide) == (18, 17), (u_hi, u_lam, u_wide))
from scipy.stats import spearmanr
xs, ys = [], []
for s in ("random", "ood_geom", "ood_mode", "ood_flow"):
    r = json.load(open(os.path.join(ML, "results_merged", f"{s}.json")))["results"]
    per = [{p["run_id"]: p["rmse_theta"] for p in r[f"fno_hybrid_canon{x}"]["per_run"]} for x in SEEDS]
    for rid in per[0]:
        xs.append(float(des[rid]["Ri"])); ys.append(np.mean([d[rid] for d in per]))
ok("Text: Spearman(Ri, error) FNO h+c -0.84", close(spearmanr(xs, ys)[0], -0.84, 0.005))
ok("Text: FNO h+c 80 runs above 10 %", len(hi) == 80, len(hi))

# ---------------- Fig. 5 values against the result notes
f = R["ood_fins"]["models"]
ok("F5a U-Net fins 1.76 K / 10.2 %", close(f["unet"]["all"]["rmse_K"], 1.76, 0.005) and close(100 * f["unet"]["all"]["t90_err"], 10.2, 0.05))
ok("F5a Transolver fins 2.31 K / 5.6 %", close(f["transolver"]["all"]["rmse_K"], 2.31, 0.005) and close(100 * f["transolver"]["all"]["t90_err"], 5.6, 0.05))
ok("F5a only models reaching t90 in all 139 runs are plotted",
   all(f[m]["all"]["n_crossed"] == 139 for m in ("front", "knn", "idw", "fno", "fno_hybrid", "unet", "unet_hybrid", "transolver", "transolver_hybrid")))
mt = open(os.path.join(ML, "multinode_2026-11-08", "RESULT_tables.md"), encoding="utf-8").read()
for s, mnp, fp, mno, fo in (("random", 6.21, 2.53, 0.83, 0.85), ("ood_mode", 6.63, 2.90, 0.98, 1.17), ("ood_flow", 9.60, 5.51, 1.46, 1.80)):
    m = mn[s]["metrics"]
    ok(f"F5b {s} profile/outlet vs RESULT_tables.md",
       close(m["profile_rmse"]["multinode_mean"], mnp, 0.005) and close(m["profile_rmse"]["fno_hybrid_canon"]["mean"], fp, 0.005)
       and close(m["T_out_err_K"]["multinode_mean"], mno, 0.005) and close(m["T_out_err_K"]["fno_hybrid_canon"]["mean"], fo, 0.005))

# ---------------- Fig. 2: hard-coded series against the tables in the validation notes (parsed)
import fig2_validation as F2  # noqa: E402  (renders the figure again; harmless)
lou = open(os.path.join(ROOT, "validation_Lou2023_case_data.md"), encoding="utf-8").read()
rows = re.findall(r"^\| (\d+) \| ([\d(none)]+) \| (\d+) \| (\d+) \|$", lou, re.M)
p1 = [float(r[1]) if r[1] != "(none)" else np.nan for r in rows]
ok("F2a PIV/CFD table parsed (14 rows)", len(rows) == 14, len(rows))
ok("F2a PIV test 1", np.allclose(p1, F2.piv1, equal_nan=True))
ok("F2a PIV test 2", np.allclose([float(r[2]) for r in rows], F2.piv2))
ok("F2a Lou CFD", np.allclose([float(r[3]) for r in rows], F2.lou_cfd))
ours = re.search(r"\*\*ours \(3D SST\)\*\* \| (.*) \|", lou).group(1).split(" | ")
ok("F2a our h_j", np.allclose([float(x) for x in ours], F2.ours_hj))
kam = open(os.path.join(ROOT, "validation_Kamkari2014_fins.md"), encoding="utf-8").read()
sec = kam[kam.index("### Liquid fraction at 70 °C: final model vs experiment"):]
def kam_row(label):
    line = re.search(r"^\| " + re.escape(label) + r" \|(.*)$", sec, re.M).group(1)
    vals = [c.strip().strip("*") for c in line.split("|")[:11]]
    return [float(v) if v not in ("",) else np.nan for v in vals]
for lab, key in (("experiment, plain wall", ("plain wall", 0)), ("**model, plain wall**", ("plain wall", 1)),
                 ("experiment, 1 fin", ("1 fin", 0)), ("**model, 1 fin (conducting)**", ("1 fin", 1)),
                 ("experiment, 3 fins", ("3 fins", 0)), ("**model, 3 fins (conducting)**", ("3 fins", 1))):
    ok(f"F2c Kamkari {lab}", np.allclose(kam_row(lab), F2.KAM[key[0]][key[1]], equal_nan=True))
vog = open(os.path.join(ROOT, "validation_Vogel2019_pcm.md"), encoding="utf-8").read()
ve = re.search(r"^\| f_l, experiment \|(.*)$", vog, re.M).group(1).split("|")
ok("F2d Vogel experiment", np.allclose([float(x) for x in ve if x.strip()], F2.fv_exp))
vr = re.search(r"^\| \*\*re-run\*\* \|(.*)$", vog, re.M).group(1).split("|")
ok("F2d Vogel this work", np.allclose([float(x) for x in vr if x.strip()], F2.fv_ours))
vb = re.search(r"^\| B-2D \(Fig. 7\) \|(.*)$", vog, re.M).group(1).split("|")
ok("F2d Vogel B-2D", np.allclose([float(x) for x in vb if x.strip()], F2.fv_b2d))

# Lou outlet numbers quoted in the text, from the .dat series
cmp_ = json.load(open(os.path.join(ROOT, "verification_data", "lou_outlet_2026-11-07", "compare.json")))["summary"]
k = np.where(F2.o_T >= 0.1)[0][0]; k5 = np.where(F2.o_T >= 0.5)[0][0]
ok("Lou: our 10 % crossing t* 0.806", close(F2.o_t[k], 0.806, 0.0005) and close(cmp_["t_star_at_0.1_ours"], F2.o_t[k], 1e-9))
ok("Lou: our 50 % crossing t* 0.932", close(F2.o_t[k5], 0.932, 0.0005))
ok("Lou: experiment 10 % (constant beta) t* 0.796", close(cmp_["t_star_at_0.1_lou"], 0.796, 0.0005))
ok("Lou: experiment 50 % (constant beta) t* 1.045", close(cmp_["t_star_at_0.5_lou"], 1.045, 0.0005))
ok("Lou: run reaches t* 1.507", close(F2.o_t.max(), 1.507, 0.001))
kb = np.where(F2.lou_bmean >= 0.1)[0][0]
# the digitised curve has a gap between t* 0.768 and 0.788; interpolate linearly across it
tc = F2.lou_t[kb - 1] + (0.1 - F2.lou_bmean[kb - 1]) * (F2.lou_t[kb] - F2.lou_t[kb - 1]) / (F2.lou_bmean[kb] - F2.lou_bmean[kb - 1])
ok("Lou: beta-at-mean 10 % crossing about t* 0.77 (interpolated over the digitising gap)", close(tc, 0.77, 0.005),
   f"interpolated {tc:.3f}; first digitised point above 0.1 at {F2.lou_t[kb]:.3f}")

# ---------------- Table 1 facts from manifests and design files
mt_ = json.load(open(os.path.join(ML, "manifest_full_h5mm.json")))["runs"]
mp_ = json.load(open(os.path.join(ML, "manifest_pcm.json")))["runs"]
ok("T1 tank runs 1,212", len(mt_) == 1212)
ok("T1 tank design points 1,020", len({r["case_id"] for r in mt_}) == 1020)
ok("T1 PCM runs 500", len(mp_) == 500)
ok("T1 tank size 54.4 GB (h5_MB is 10^6 bytes, checked on P0000 below)", close(sum(r["h5_MB"] for r in mt_) / 1000, 54.4, 0.05))
ok("T1 PCM size 10.3 GB", close(sum(r["h5_MB"] for r in mp_) / 1000, 10.3, 0.05))
p0 = [r for r in mp_ if r["run_id"] == "P0000"][0]
ok("T1 h5_MB unit is 10^6 bytes (P0000)", close(os.path.getsize(os.path.join("D:/ThermBench_data/tb_data/pcm_frozen", "P0000", "thermbench.h5")) / 1e6, p0["h5_MB"], 0.01))
import hashlib
ok("T1 tank manifest md5 0e8b6d8d", hashlib.md5(open(os.path.join(ML, "manifest_full_h5mm.json"), "rb").read()).hexdigest().startswith("0e8b6d8d"))
ok("T1 PCM manifest md5 19397b78", hashlib.md5(open(os.path.join(ML, "manifest_pcm.json"), "rb").read()).hexdigest().startswith("19397b78"))
ids = {r["run_id"] for r in mt_}
d = [r for r in csv.DictReader(open(os.path.join(ROOT, "design_v2_full.csv"))) if r["run_id"] in ids]
ok("T1 tank: all manifest runs in design_v2_full.csv", len(d) == 1212)
ok("T1 charging 849 / discharging 363", sum(r["mode"] == "charge" for r in d) == 849 and sum(r["mode"] == "discharge" for r in d) == 363)
ok("T1 type A 844 / type B 368", sum(r["inlet_type"] == "A" for r in d) == 844 and sum(r["inlet_type"] == "B" for r in d) == 368)
pre = sum(r["yi"].strip() not in ("", "0", "0.0") for r in d)
ok("T1 pre-stratified 359 / uniform 853", pre == 359, f"pre-stratified (yi > 0): {pre}")
byc = {}
for r in d:
    byc.setdefault(r["case_id"], set()).add(r["turb"])
lam = sum(v == {"laminar"} for v in byc.values()); sst = sum(v == {"kOmegaSST"} for v in byc.values()); both = sum(len(v) == 2 for v in byc.values())
ok("T1 432 laminar-only / 396 SST-only / 192 both", (lam, sst, both) == (432, 396, 192), (lam, sst, both))
ok("T1 width 0.25 to 1.0 m", min(float(r["W"]) for r in d) >= 0.25 - 1e-9 and max(float(r["W"]) for r in d) <= 1.0 + 1e-9,
   f"{min(float(r['W']) for r in d)} to {max(float(r['W']) for r in d)}")
ok("T1 inlet velocity 0.005 to 0.2 m/s", min(float(r["u_in"]) for r in d) >= 0.005 - 1e-9 and max(float(r["u_in"]) for r in d) <= 0.2 + 1e-9)
ok("T1 dT 5 to 50 K", min(float(r["dT"]) for r in d) >= 5 - 1e-9 and max(float(r["dT"]) for r in d) <= 50 + 1e-9)
ok("T1 tank QC 1,211 OK / 1 WARN", sum(r["qc"] == "OK" for r in mt_) == 1211 and sum(r["qc"] == "WARN" for r in mt_) == 1)
pf = os.path.join(ROOT, "scripts", "pcm_full.csv")
if os.path.exists(pf):
    pc = {r.get("case_id", r.get("id", "")): r for r in csv.DictReader(open(pf))}
    keys = list(next(iter(pc.values())).keys())
    ok("T1 PCM design file readable", True, ", ".join(keys[:12]))
inv = list(csv.DictReader(open(os.path.join(ROOT, "pcm_inventory_2026-11-07.csv"))))
ok("T1 PCM solver-WARN cases 39", sum(r["solver_qc"] == "WARN" for r in inv) == 39)
ok("T1 PCM field QC 498 OK / 2 WARN", sum(r["qc"] == "OK" for r in mp_) == 498 and sum(r["qc"] == "WARN" for r in mp_) == 2)

# ---------------- Fig. 6 recomputed errors are typical for the run shown
f6 = json.load(open(os.path.join(OUT, "fig6_examples.json")))
ok("F6 tank shown snapshots near the run's stored error", 0.3 < np.mean(f6["tank"]["rmse_theta_shown"]) / f6["tank"]["stored_seed_mean_rmse_theta"] < 3)
ok("F6 PCM shown snapshots near the run's stored error", 0.3 < np.mean(f6["pcm"]["rmse_K_shown"]) / f6["pcm"]["stored_seed_mean_rmse_K"] < 3)

# ---------------- report
fails = [c for c in checks if not c[0]]
L = ["# Paper numbers: independent cross-check", "", f"{len(checks)} checks, {len(fails)} failed.", "",
     "| | Check | Detail |", "|---|---|---|"] + [f"| {'PASS' if c[0] else '**FAIL**'} | {c[1]} | {c[2]} |" for c in checks]
open(os.path.join(OUT, "VERIFY_REPORT.md"), "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print(f"{len(checks)} checks, {len(fails)} failed")
for c in fails:
    print("FAIL", c[1], c[2])
sys.exit(1 if fails else 0)
