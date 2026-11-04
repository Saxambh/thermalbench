# Two-way rebalance using measured per-run slowdown factors (median wall/sim-s over cost model).
# Only runs listed in moved_to_laptop.txt can go back to the lab: delete the lab placeholder,
# create a laptop placeholder (DONE + MOVED_TO_LAB). Usage: rebalance2.py LAB_F LAP_F [--apply]
import csv, os, sys, subprocess, numpy as np
R = "/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench"
c = np.array([3.129, 0.523, 1.329, 0.255])
LAB_F, LAP_F = float(sys.argv[1]), float(sys.argv[2]); LAB_J, LAP_J = 14, 8
cost = lambda d: np.exp(c @ [1, np.log(float(d["u_in"])), np.log(float(d["W"])), d["turb"] != "laminar"]) * float(d["end_s"])
order = lambda r: -float(r["end_s"]) * float(r["W"]) / float(r["s"])
design = {r["run_id"]: r for r in csv.DictReader(open(f"{R}/design_v2_full.csv"))}
moved = [l.strip() for l in open(f"{R}/moved_to_laptop.txt") if l.strip()]
lab_list = [r["run_id"] for r in csv.DictReader(open(f"{R}/design_v2_full_lab.csv"))]
lap_list = [r["run_id"] for r in csv.DictReader(open(f"{R}/design_v2_full_laptop2.csv"))]
def state(listing):
    st = {}
    for l in listing.split("\n"):
        if l.strip():
            p = l.split(); st[p[0]] = p[1:]
    return st
cmd = ("cd ~/of_runs/full_h5mm && for d in */; do d=${d%/}; if [ -f $d/MOVED_TO_LAPTOP ] || [ -f $d/MOVED_TO_LAB ]; then echo $d moved; "
       "elif [ -f $d/DONE ]; then echo $d done; else t=$(tail -c 20000 $d/log.solver 2>/dev/null | grep '^Time = ' | tail -1 | awk '{print $3}'); echo $d run ${t:-0}; fi; done")
lab_st = state(subprocess.run(["ssh", "labpc", cmd], capture_output=True, text=True, check=True).stdout)
lap_st = state(subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, check=True).stdout)
def load(lst, st):
    tot, queued = 0.0, []
    for rid in lst:
        s = st.get(rid)
        if s and s[0] in ("done", "moved"): continue
        d = design[rid]
        if s: tot += cost(d) * (1 - float(s[1]) / float(d["end_s"]))
        else: tot += cost(d); queued.append(rid)
    return tot, queued
lab_load, _ = load(lab_list, lab_st)
lap_load, lap_q = load(lap_list, lap_st)
h = lambda L, f, j: L * f / j / 3600
print(f"now: laptop {h(lap_load, LAP_F, LAP_J):.1f} h, lab {h(lab_load, LAB_F, LAB_J):.1f} h")
back = []
cand = sorted([r for r in lap_q if r in moved], key=lambda r: order(design[r]))  # longest first
# give back from the END of the laptop queue (shortest), i.e. the lab's next-to-last work
while cand and h(lap_load, LAP_F, LAP_J) > h(lab_load, LAB_F, LAB_J):
    r = cand.pop(); back.append(r); lap_load -= cost(design[r]); lab_load += cost(design[r])
print(f"after moving {len(back)} back: laptop {h(lap_load, LAP_F, LAP_J):.1f} h, lab {h(lab_load, LAB_F, LAB_J):.1f} h")
if "--apply" in sys.argv and back:
    O = os.path.expanduser("~/of_runs/full_h5mm")
    for r in back:   # laptop placeholder first, so the laptop never starts them
        os.makedirs(f"{O}/{r}", exist_ok=False)
        open(f"{O}/{r}/MOVED_TO_LAB", "w").write("moved back to lab, not a result\n")
        open(f"{O}/{r}/DONE", "w").close()
    out = subprocess.run(["ssh", "labpc", "cd ~/of_runs/full_h5mm && for r in " + " ".join(back) +
                          "; do [ -f $r/MOVED_TO_LAPTOP ] && [ ! -f $r/log.solver ] && rm -rf $r; done; ls */MOVED_TO_LAPTOP | wc -l"],
                         capture_output=True, text=True).stdout.strip()
    open(f"{R}/moved_back_to_lab.txt", "a").write("\n".join(back) + "\n")
    print("lab placeholders left:", out)
