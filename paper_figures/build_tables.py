"""Tables 1 to 3 of the paper, written as Markdown to out/tables.md (also used by the manuscript build).
Table 1: dataset facts, each taken from the dataset cards / manifests (checked by verify_paper.py).
Table 2: tank field error (% of dT) per model and split, from results_merged/<split>.json per-run scores
         (neural: per-seed mean over test runs, then mean +- SD over 3 seeds) and multinode_2026-11-08.
Table 3: PCM field RMSE (K) and t90 error, from extra_baselines_2026-11-08/result_ts.json.
"""
import json, os
import numpy as np
from style import ML, OUT

TANK_SPLITS = [("random", "Random"), ("ood_geom", "Unseen width"), ("ood_mode", "Discharge"), ("ood_flow", "Faster inflow")]
PCM_SPLITS = [("random", "Random"), ("ood_fins", "Held-out fins"), ("ood_drive", "Stronger heating"),
              ("ood_tilt", "Unseen tilt"), ("ood_material", "Held-out lauric acid"), ("ood_material_r", "Held-out n-octadecane")]
TANK_BASE = [("initial", "Initial field (no change)"), ("ideal_stratified", "1D ideal stratification"),
             ("multinode", "Multi-node 1D (calibrated)"), ("knn", "k-nearest neighbours"), ("idw", "Inverse-distance weighting"),
             ("rbf", "Radial basis functions")]
TANK_NEURAL = [(f"{a}{v}", f"{n}{l}") for a, n in (("fno", "FNO"), ("unet", "U-Net"))
               for v, l in (("", ""), ("_canon", ", canonical"), ("_hybrid", ", hybrid"), ("_hybrid_canon", ", hybrid + canonical"))]
PCM_BASE = [("initial", "Initial field (no change)"), ("stefan", "Stefan (conduction)"), ("front", "Front model"),
            ("knn", "k-nearest neighbours"), ("idw", "Inverse-distance weighting"), ("rbf", "Radial basis functions")]
PCM_NEURAL = [(f"{a}{v}", f"{n}{l}") for a, n in (("fno", "FNO"), ("unet", "U-Net"), ("transolver", "Transolver"))
              for v, l in (("", ""), ("_hybrid", ", hybrid"))]


def seed_stats(res, m, key, scale):
    names = [m + s for s in ("", "_s1", "_s2") if m + s in res]
    v = [scale * np.mean([p[key] for p in res[n]["per_run"]]) for n in names]
    return float(np.mean(v)), (float(np.std(v, ddof=1)) if len(v) > 1 else None), len(v)


def tank():
    mn = json.load(open(os.path.join(ML, "multinode_2026-11-08", "compare.json")))
    vals = {}
    for s, _ in TANK_SPLITS:
        res = json.load(open(os.path.join(ML, "results_merged", f"{s}.json")))["results"]
        for m, _ in TANK_BASE + TANK_NEURAL:
            if m == "multinode":
                vals[(m, s)] = (mn[s]["metrics"]["rmse_theta"]["multinode_mean"], None, 1)
            else:
                vals[(m, s)] = seed_stats(res, m, "rmse_theta", 100)
    best = {s: min(vals[(m, s)][0] for m, _ in TANK_BASE + TANK_NEURAL) for s, _ in TANK_SPLITS}
    L = ["**Table 2.** Tank family: temperature-field RMSE on the test runs, in % of the run's temperature "
         "difference ΔT. Neural models: mean ± SD over three training seeds. Lowest value per split in bold. "
         "Test runs: random 131, unseen width 224, discharge 363, faster inflow 103.", "",
         "| Model | " + " | ".join(l for _, l in TANK_SPLITS) + " |", "|---|" + "---|" * len(TANK_SPLITS)]
    for grp, rows in (("Baselines", TANK_BASE), ("Neural operators", TANK_NEURAL)):
        L.append(f"| *{grp}* |" + " |" * len(TANK_SPLITS))
        for m, lab in rows:
            cells = []
            for s, _ in TANK_SPLITS:
                mu, sd, n = vals[(m, s)]
                c = f"{mu:.2f}" + (f" ± {sd:.2f}" if sd is not None else "")
                cells.append(f"**{c}**" if abs(mu - best[s]) < 1e-12 else c)
            L.append(f"| {lab} | " + " | ".join(cells) + " |")
    return L, vals


def pcm():
    R = json.load(open(os.path.join(ML, "extra_baselines_2026-11-08", "result_ts.json")))["splits"]
    vals = {}
    for s, _ in PCM_SPLITS:
        for m, _ in PCM_BASE + PCM_NEURAL:
            a = R[s]["models"][m]["all"]
            vals[(m, s)] = (a["rmse_K"], a["seed_sd_rmse_K"], 100 * a["t90_err"], a["n_crossed"], a["n"])
    best = {s: min(vals[(m, s)][0] for m, _ in PCM_BASE + PCM_NEURAL) for s, _ in PCM_SPLITS}
    best_t = {s: min(vals[(m, s)][2] for m, _ in PCM_BASE + PCM_NEURAL
                     if vals[(m, s)][3] >= 0.9 * vals[(m, s)][4]) for s, _ in PCM_SPLITS}
    L = ["**Table 3.** PCM family. (a) Temperature-field RMSE (K) on the test runs. (b) Relative melt-time (t90) "
         "error in %, over the runs whose prediction reaches a liquid fraction of 0.9 within the input-only "
         "horizon (3 t_ref); the share of runs that reach it is given when it is below 100 %, and the error is "
         "not reported when fewer than 10 % of runs reach it. Neural models: mean ± SD over three training "
         "seeds (field RMSE). Bold: lowest field RMSE, and lowest t90 error among models reaching t90 in at least "
         "90 % of runs. Test runs: " + ", ".join(f"{l.lower()} {R[s]['n_test']}" for s, l in PCM_SPLITS) + ".", "",
         "| Model | " + " | ".join(l for _, l in PCM_SPLITS) + " |", "|---|" + "---|" * len(PCM_SPLITS)]
    for block in ("field", "t90"):
        L.append(f"| **({'a' if block == 'field' else 'b'}) {'Field RMSE, K' if block == 'field' else 't90 error, %'}** |"
                 + " |" * len(PCM_SPLITS))
        for grp, rows in (("Baselines", PCM_BASE), ("Neural operators", PCM_NEURAL)):
            L.append(f"| *{grp}* |" + " |" * len(PCM_SPLITS))
            for m, lab in rows:
                cells = []
                for s, _ in PCM_SPLITS:
                    mu, sd, t9, nc, n = vals[(m, s)]
                    if block == "field":
                        c = f"{mu:.2f}" + (f" ± {sd:.2f}" if sd is not None else "")
                        c = f"**{c}**" if abs(mu - best[s]) < 1e-12 else c
                    else:
                        share = nc / n
                        if share < 0.10:
                            c = "none" if nc < 0.5 else f"({100 * share:.1f} % reach)"
                        else:
                            c = f"{t9:.1f}"
                            if abs(t9 - best_t[s]) < 1e-9 and share >= 0.9:
                                c = f"**{c}**"
                            if share < 1 - 1e-9:
                                c += f" ({100 * share:.0f} % reach)"
                    cells.append(c)
                L.append(f"| {lab} | " + " | ".join(cells) + " |")
    return L, vals


TABLE1 = ["**Table 1.** The two families of ThermalStorageBench.", "",
          "| | Stratified water tank (sensible) | PCM melting cell (latent) |", "|---|---|---|",
          "| Geometry | 2D rectangular tank, height 1 m, width 0.25 to 1.0 m; side-wall slots (A) or lid and bottom slots (B), slot height 20 to 80 mm, port offset 0 to 0.2 H | 2D enclosure, height 100 mm, width 20 to 60 mm, heated wall with 0 to 5 conducting aluminium fins (length 0.2 to 0.8 W, thickness 1 to 4 mm) |",
          "| Operation | Charging (849 runs) or discharging (363); uniform (853) or pre-stratified (359) start; inlet velocity 0.005 to 0.2 m/s, ΔT 5 to 50 K | Melting from a heated wall; side heating (350), tilted 45° (75), heated from below (75); wall superheat 8 to 30 K, subcooling 0.5 to 22.3 K |",
          "| Material | Water, temperature-dependent (real) properties | n-octadecane (250) and lauric acid (250), constant properties, enthalpy-porosity melting |",
          "| Flow regime | Laminar (Re < 1,500), k-ω SST (Re > 3,000), both between: 432 laminar-only, 396 SST-only, 192 with both | Laminar natural convection, Ra_H 1.5 × 10⁸ to 9.0 × 10⁸, Ste 0.07 to 0.37 |",
          "| Solver and mesh | OpenFOAM v2606 buoyantPimpleFoam, uniform 5 mm mesh | OpenFOAM v2606 buoyantPimpleFoam with enthalpy-porosity source, uniform 0.5 mm mesh |",
          "| Runs (design points) | 1,212 (1,020) | 500 (500) |",
          "| Output per run | 121 snapshots of T, p_rgh, u (and k, ω, ν_t for SST); stored energy, exergy, MIX, thermocline midpoint and thickness, outlet temperature | 88 to 204 snapshots of T, liquid fraction and velocity; stored energy, Nusselt number, heat input, liquid fraction |",
          "| Quality control | 1,211 OK, 1 WARN; 5 planned runs excluded by pre-set rules | 498 OK, 2 WARN (field QC); 39 solver-WARN cases kept under a pre-registered rule; 34 reruns |",
          "| Size, frozen manifest | 54.4 GB, md5 0e8b6d8d… | 10.3 GB, md5 19397b78… |"]

if __name__ == "__main__":
    L2, _ = tank(); L3, _ = pcm()
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, "tables.md"), "w", encoding="utf-8", newline="\n").write("\n".join(TABLE1 + [""] + L2 + [""] + L3) + "\n")
    print("\n".join(L2)); print(); print("\n".join(L3))
