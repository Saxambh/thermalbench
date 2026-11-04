# Rough cost model: wall time per simulated second vs inflow speed, from finished runs; projects the full batch.
import csv, os, numpy as np
R = "/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench"
design = {r["run_id"]: r for r in csv.DictReader(open(f"{R}/design_v2_full.csv"))}
pil = {r["run_id"]: r for r in csv.DictReader(open(f"{R}/design_v2_pilot.csv"))}
X = []
for B, D in (("full_h5mm", design), ("pilot_v2", pil)):
    for r in csv.DictReader(open(os.path.expanduser(f"~/of_runs/{B}/batch_status.csv"))):
        if r["status"] == "ok" and r["run_id"] in D:
            d = D[r["run_id"]]
            X.append((float(d["u_in"]), float(d["end_s"]), float(d["W"]), d["turb"], float(r["wall_s"])))
st = [r["status"] for r in csv.DictReader(open(os.path.expanduser("~/of_runs/full_h5mm/batch_status.csv")))]
print("full batch statuses:", {s: st.count(s) for s in set(st)})
u, e, W, t, w = map(np.array, zip(*X))
# wall/sim-second ~ a * u^b * W  (cells ~ W, dt ~ 1/velocity scale)
A = np.c_[np.ones(len(u)), np.log(u), np.log(W)]
c, *_ = np.linalg.lstsq(A, np.log(w/e), rcond=None)
pred = lambda d: np.exp(c[0] + c[1]*np.log(float(d["u_in"])) + c[2]*np.log(float(d["W"]))) * float(d["end_s"])
err = np.exp(np.abs(A@c - np.log(w/e)))
print(f"fit on {len(u)} runs, median factor error {np.median(err):.2f}")
done = set(r["run_id"] for r in csv.DictReader(open(os.path.expanduser("~/of_runs/full_h5mm/batch_status.csv"))))
rem = [pred(d) for k, d in design.items() if k not in done]
print(f"remaining runs {len(rem)}, total {sum(rem)/3600:.0f} core-hours; at 4 jobs {sum(rem)/3600/4/24:.1f} days, at 4+14 jobs {sum(rem)/3600/18/24:.1f} days")
