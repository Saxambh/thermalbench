#!/usr/bin/env python3
"""Mesh spot check of the dataset runs (2026-11-04, Saxam: "set up the spot check"). A random
sample of dataset cases is rerun at half the cell size (and so about half the time step, the
time step is Courant-limited), and its exported fields and metrics are compared with the dataset
run of the same case. Shows that the cases in the dataset are mesh-converged, not just the
tuning case of the convergence study.

  spotcheck.py select            write spot_tank.csv and spot_pcm.csv (seeded, reproducible)
  spotcheck.py compare tank|pcm  compare finished refined runs with the dataset runs

Selection (seed 20261104):
  tank  10 runs, 5 laminar + 5 SST, from the 1,217-run design minus the T0765-type exclusions,
        h 5 -> 2.5 mm; only runs whose refined run is predicted to take <= 24 h on the laptop
        (8x the dataset run: 4x cells, 2x steps; dataset wall from a log-linear fit to the laptop's
        own runs, as rebalance4.py) - the share of the design that passes is printed.
  pcm   6 cases from the 500, h 0.5 -> 0.25 mm, cases whose refined run is predicted <= 20 h on
        pc4, spread over material x (no fins / fins) x tilt (0 / tilted).
Run: tank on the laptop (run_batch.py spot_tank.csv ~/of_runs/spot_tank --jobs 6) once its tank
runs end; PCM on pc4 (pcm_batch.sh spot_pcm.csv ~/of_runs/spot_pcm 6) once the validation re-runs end.
Compare: refined fields are 2 x 2 block-averaged onto the dataset grid (exact, h halves), at the
same snapshot times. Tank: field rmse (K) against the 0.65-2 K chaotic noise floor, stored energy,
outlet temperature, thermocline position. PCM: field rmse (K), liquid-fraction rmse, melt curve and
t(0.99) difference."""
import contextlib, csv, glob, importlib.util, io, json, os, random, sys
import numpy as np

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = os.path.join(R, "scripts")
SEED = 20261104


def tank_cost_fit():
    """log wall_s ~ features, from the laptop's dataset runs (as rebalance4.py)."""
    design = {r["run_id"]: r for r in csv.DictReader(open(os.path.join(R, "design_v2_full.csv")))}
    f = lambda r: [1.0, np.log(float(r["end_s"])), np.log(float(r["W"])), np.log(float(r["u_in"])),
                   np.log(float(r["s"])), float(r["turb"] != "laminar")]
    X, y = [], []
    for st in glob.glob(os.path.expanduser("~/of_runs/full_h5mm*/batch_status.csv")):
        for l in csv.DictReader(open(st)):
            if l.get("status") == "ok" and l["run_id"] in design and float(l["wall_s"]) > 60:
                X.append(f(design[l["run_id"]])); y.append(np.log(float(l["wall_s"])))
    c = np.linalg.lstsq(np.array(X), np.array(y), rcond=None)[0]
    v = (np.array(y) - np.array(X) @ c).var()
    return design, (lambda r: float(np.exp(np.array(f(r)) @ c + 0.5 * v)) / 3600), len(y)


def select():
    rng = random.Random(SEED)
    design, wall_h, n = tank_cost_fit()
    rows = [r for r in design.values()
            if not (r["mode"] == "discharge" and r["yi"] and float(r["yi"]) > float(r["H"]) - float(r["off"]))]
    ok = [r for r in rows if 8 * wall_h(r) <= 24]
    print(f"tank: cost fit on {n} laptop runs; {len(ok)}/{len(rows)} runs ({100 * len(ok) / len(rows):.0f} %) "
          f"have a refined run <= 24 h")
    pick = []
    for turb in ("laminar", "kOmegaSST"):
        pool = sorted((r for r in ok if r["turb"] == turb), key=lambda r: r["run_id"])
        pick += rng.sample(pool, 5)
    with open(os.path.join(S, "spot_tank.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(pick[0])); w.writeheader()
        for r in pick:
            w.writerow(r | {"h": "0.0025"})
            print(f"  {r['run_id']:10s} Re {float(r['Re']):7.0f} {r['mode']:9s} refined ~{8 * wall_h(r):4.1f} h")
    # PCM
    spec = importlib.util.spec_from_file_location("cost", os.path.join(S, "pcm_cost_pilot.py"))
    cost = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):
        sys.argv = ["x", os.path.join(S, "pcm_full.csv")]; spec.loader.exec_module(cost)
    pcm = list(csv.DictReader(open(os.path.join(S, "pcm_full.csv"))))
    h4 = lambda r: cost.wall_h(r) / 3.3 * 1.45 * 1.25 * 8          # refined, hours on a pc4 slot
    okp = [r for r in pcm if h4(r) <= 20]
    print(f"pcm: {len(okp)}/{len(pcm)} cases have a refined run <= 20 h on pc4")
    cells = {}
    for r in sorted(okp, key=lambda r: r["case_id"]):
        cells.setdefault((r["material"], int(r["nfins"]) > 0, float(r["tilt_deg"]) != 0), []).append(r)
    keys = sorted(cells); rng.shuffle(keys)
    pickp = [rng.choice(cells[k]) for k in keys[:6]]
    fields = list(pcm[0])
    with open(os.path.join(S, "spot_pcm.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields); w.writeheader()
        for r in pickp:
            args = r["args"].replace("--h 0.0005", "--h 0.00025")
            assert "--h 0.00025" in args, r["case_id"]
            w.writerow(r | {"args": args, "h_m": "0.00025", "core_h_est": round(h4(r), 1)})
            print(f"  {r['case_id']} {r['material']:10s} fins {r['nfins']} tilt {r['tilt_deg']:>4s} refined ~{h4(r):4.1f} h")


def block(a):   # [t, 2ny, 2nx] -> [t, ny, nx]
    t, ny, nx = a.shape
    return a[:, :ny // 2 * 2, :nx // 2 * 2].reshape(t, ny // 2, 2, nx // 2, 2).mean((2, 4))


def compare(fam):
    import h5py
    if fam == "tank":
        fine = sorted(glob.glob(os.path.expanduser("~/of_runs/spot_tank/*/thermbench.h5")))
        roots = ["~/of_runs/full_h5mm", "~/of_runs/full_h5mm_x", "~/tb_data/lab/full_h5mm", "~/tb_data/lab/full_h5mm_x",
                 "~/tb_data/pc3/full_h5mm"]
    else:
        fine = sorted(glob.glob(os.path.expanduser("~/tb_data/pc4/spot_pcm/*/thermbench.h5")))
        roots = ["~/of_runs/pcm_full/runs"] + [f"~/tb_data/{m}/pcm_full" for m in ("laptop", "lab", "pc3", "pc4", "pc5")]
    out = []
    for f in fine:
        rid = os.path.basename(os.path.dirname(f))
        coarse = next((os.path.expanduser(f"{r}/{rid}/thermbench.h5") for r in roots
                       if os.path.exists(os.path.expanduser(f"{r}/{rid}/thermbench.h5"))), None)
        if coarse is None:
            print(f"{rid}: dataset run not here yet"); continue
        with h5py.File(f) as a, h5py.File(coarse) as b:
            n = min(len(a["times_s"]), len(b["times_s"]))
            Tf, Tc = block(a["fields/T"][:n]), b["fields/T"][:n]
            row = {"run": rid, "snapshots": n, "rmse_K": float(np.sqrt(np.mean((Tf - Tc) ** 2)))}
            if fam == "tank":
                for k in ("E_J", "T_out_K", "y_mid_m"):
                    x, y = a[f"metrics/{k}"][:n], b[f"metrics/{k}"][:n]
                    row[k] = float(np.nanmax(np.abs(x - y)) / (np.nanmax(np.abs(y)) if k == "E_J" else 1))
            else:
                Af, Ac = block(a["fields/alpha"][:n]), b["fields/alpha"][:n]
                row["alpha_rmse"] = float(np.sqrt(np.mean((Af - Ac) ** 2)))
                lf_f, lf_c = a["metrics/liquid_fraction"][:n], b["metrics/liquid_fraction"][:n]
                row["melt_curve_maxdiff"] = float(np.max(np.abs(lf_f - lf_c)))
                t = b["metrics/t_s"][:]
                def t99(lf, t): i = np.nonzero(lf >= 0.99)[0]; return float(t[i[0]]) if i.size else np.nan
                row["t99_rel_diff"] = (t99(a["metrics/liquid_fraction"][:], a["metrics/t_s"][:]) - t99(b["metrics/liquid_fraction"][:], t)) / t99(b["metrics/liquid_fraction"][:], t)
        out.append(row); print(json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in row.items()}))
    if out:
        json.dump(out, open(os.path.join(R, f"spotcheck_{fam}.json"), "w"), indent=1)
        print(f"{len(out)} pairs -> spotcheck_{fam}.json; median field rmse {np.median([r['rmse_K'] for r in out]):.2f} K")


if __name__ == "__main__":
    {"select": select, "compare": lambda: compare(sys.argv[2])}[sys.argv[1]]()
