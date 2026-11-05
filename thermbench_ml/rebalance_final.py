"""Rebalance the remaining run_final.sh jobs over the GPUs that still work (2026-11-05).

pc5's GPU 0 failed (CUDA launch failure, the driver lost the card; no one can restart pc5) and the
laptop's Ubuntu kept stopping, so their jobs and every job not yet started are shared out again
over lab, pc3, pc4, pc5b and pc6, by the speeds measured on finished jobs (relative to the
laptop-hour estimates of run_final.sh plan; the CFD runs on the same machines slow the GPUs down).
A job running now stays first in its worker's list (skipped once its result is in, run again if
it failed). Writes jobs_<worker>.txt, which run_final.sh uses instead of its planned list.
  python3 rebalance_final.py <dir with one subfolder of result jsons per worker> [running jobs...]
  running job: worker=model/split/seed/flags, e.g. lab=unet/random/0/--hybrid
"""
import glob, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FRAC = {"random": 0.80, "ood_flow": 0.81, "ood_geom": 0.76, "ood_mode": 0.45}
EPOCH_H = {"fno": 81 / 3600 / 0.80, "unet": 107 / 3600 / 0.80}
SPEED = {"lab": 2.2, "pc3": 1.07, "pc4": 0.75, "pc5b": 1.1, "pc6": 1.0}   # measured 2026-11-05
START = {"lab": 0.0, "pc3": 0.8, "pc4": 0.2, "pc5b": 0.5, "pc6": 5.2}     # h until the GPU is free
OLD = ["laptop", "lab", "pc3", "pc4", "pc5a", "pc5b"]


def hours(job):
    model, split, seed, ep, flags = job
    return int(ep) * EPOCH_H[model] * FRAC[split] + 0.08


def name(job):
    model, split, seed, ep, flags = job
    return model + ("_hybrid" if "hybrid" in flags else "") + ("_canon" if "canon" in flags else "") + (f"_s{seed}" if seed != "0" else "")


def planned(w):
    src = open(os.path.join(HERE, "run_final.sh")).read()
    fn = re.search(r"^plan\(\) \{.*?^\}", src, re.S | re.M).group(0)
    out = subprocess.run(["bash", "-c", fn + f"\nplan {w}"], capture_output=True, text=True, cwd=HERE).stdout
    return [tuple((l.split(None, 4) + [""])[:5]) for l in out.splitlines() if l.strip()]


done = set()
for f in glob.glob(os.path.join(sys.argv[1], "*", "*.json")):
    try:
        done |= {(os.path.basename(f)[:-5], k) for k in json.load(open(f))["results"]}
    except (ValueError, KeyError):
        pass
running = {}
for a in sys.argv[2:]:
    w, j = a.split("=", 1)
    m, s, seed, flags = j.split("/")
    running[w] =(m, s, seed, "60" if m == "fno" else "100", flags)

pool = [j for w in OLD for j in planned(w) if (j[1], name(j)) not in done and j not in running.values()]
pool.sort(key=hours, reverse=True)
free = dict(START)
lists = {w: ([running[w]] if w in running else []) for w in SPEED}
for j in pool:
    w = min(SPEED, key=lambda w: free[w] + hours(j) / SPEED[w])
    free[w] += hours(j) / SPEED[w]
    lists[w].append(j)
for w in SPEED:
    with open(os.path.join(HERE, f"jobs_{w}.txt"), "w") as fh:
        fh.write("".join(" ".join(j).strip() + "\n" for j in lists[w]))
    print(f"{w:5s} {len(lists[w]):2d} jobs, done in about {free[w]:4.1f} h")
print(f"{len(pool) + len(running)} jobs left, {len(done)} results in")
