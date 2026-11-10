"""Referee fixes (PLAN.md), tank CFD selections. Run in WSL on the laptop (needs the laptop's batch_status files).

1. Noise-floor pairs (fix 7): 24 tank runs that are on the test side of at least one split, rerun with the inlet
   velocity x (1 + 1e-4) (tank_verify.sh variant "rep", as T0551 in the 6 November mesh check).
   Strata: 6 bins of log Ri (equal-count bins over the eligible runs) x closure (laminar / SST), 2 runs per cell,
   taken in sha256(run_id + SALT) order. Eligible: in the frozen manifest, not a flagged run, predicted wall of
   the rerun <= 18 h (cost fit of spotcheck.tank_cost_fit, laptop runs).
2. Inlet mesh test (fix 6): the 2.5 mm rerun (variant "h25") of the test-side run with the smallest slot
   (s = 0.02 m) and the highest slot Reynolds number whose predicted 2.5 mm wall (8 x) is <= 60 h, run on 8 cores.
Writes pairs.txt and inlet.txt (lines "<run_id> <variant>") and selection_tank.json.
"""
import hashlib, json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
ML = os.path.dirname(HERE)
R = os.path.dirname(ML)
sys.path[:0] = [ML, os.path.join(R, "scripts")]
from spotcheck import tank_cost_fit
from splits import SPLITS, side
from data import DEFAULT_ROOTS, index

SALT = "referee-2026-11-10"
design, wall_h, n_fit = tank_cost_fit()
runs = index(DEFAULT_ROOTS, manifest=os.path.join(ML, "manifest_full_h5mm.json"))
flags = set(json.load(open(os.path.join(ML, "label_flags_tank.json"))).keys()) if os.path.exists(os.path.join(ML, "label_flags_tank.json")) else set()
test_side = [r for r in runs if any(side(r, s) == "test" for s in SPLITS) and r.run_id in design]
print(f"cost fit on {n_fit} runs; {len(test_side)} test-side runs")
flagged = {k for k in flags if k.startswith("T")}
pool = [r for r in test_side if r.run_id not in flagged and wall_h(design[r.run_id]) <= 18]
lri = np.array([np.log(float(design[r.run_id]["Ri"])) for r in pool])
edges = np.quantile(lri, np.linspace(0, 1, 7))
cells = {}
for r, x in zip(pool, lri):
    b = min(int(np.searchsorted(edges, x, side="right")) - 1, 5)
    cells.setdefault((b, design[r.run_id]["turb"] != "laminar"), []).append(r.run_id)
pairs = []
for b in range(6):
    for sst in (False, True):
        c = sorted(cells.get((b, sst), []), key=lambda x: hashlib.sha256((x + SALT).encode()).hexdigest())
        if len(c) < 2:
            sys.exit(f"cell {b}/{sst}: {len(c)} eligible")
        pairs += c[:2]
inl = sorted((r for r in test_side if float(design[r.run_id]["s"]) == 0.02 and r.run_id not in flagged
              and 8 * wall_h(design[r.run_id]) <= 60), key=lambda r: -float(design[r.run_id]["Re"]))
inlet = inl[0].run_id
open(os.path.join(HERE, "pairs.txt"), "w").write("".join(f"{x} rep\n" for x in pairs))
open(os.path.join(HERE, "inlet.txt"), "w").write(f"{inlet} h25\n")
out = {"salt": SALT, "cost_fit_runs": n_fit, "eligible_pairs": len(pool), "logRi_edges": edges.tolist(),
       "pairs": [{"run_id": x, "Ri": float(design[x]["Ri"]), "Re": float(design[x]["Re"]), "turb": design[x]["turb"],
                  "pred_wall_h": round(wall_h(design[x]), 2)} for x in pairs],
       "inlet": {"run_id": inlet, "s": 0.02, "Re": float(design[inlet]["Re"]), "Ri": float(design[inlet]["Ri"]),
                 "pred_wall_h_2p5mm": round(8 * wall_h(design[inlet]), 1), "candidates": len(inl)}}
json.dump(out, open(os.path.join(HERE, "selection_tank.json"), "w"), indent=1)
for p in out["pairs"]:
    print(p)
print("inlet", out["inlet"])
