# Move queued (not yet started) runs from the lab share to the laptop so both finish together.
# Uses measured speeds: lab ~LAB_F x slower per run than the cost model (laptop-fitted); laptop at 8 jobs ~LAP_F.
# Lab keeps its running driver: moved runs get a placeholder dir on the lab with DONE + MOVED_TO_LAPTOP,
# so the lab driver skips them. Writes design_v2_full_laptop2.csv and moved_to_laptop.txt.
import csv, os, sys, json, subprocess, numpy as np
R = "/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench"
c = np.array([3.129, 0.523, 1.329, 0.255])
LAB_F, LAP_F, LAB_J, LAP_J = 4.1, float(os.environ.get("LAP_F", 1.5)), 14, 8
cost = lambda d: np.exp(c @ [1, np.log(float(d["u_in"])), np.log(float(d["W"])), d["turb"] != "laminar"]) * float(d["end_s"])
lab = list(csv.DictReader(open(f"{R}/design_v2_full_lab.csv")))
lap = list(csv.DictReader(open(f"{R}/design_v2_full_laptop.csv")))
# lab state: which run dirs exist, DONE, and progress of running ones
state = subprocess.run(["ssh", "labpc", "cd ~/of_runs/full_h5mm && for d in */; do d=${d%/}; "
    "if [ -f $d/DONE ]; then echo $d done; else t=$(tail -c 20000 $d/log.solver 2>/dev/null | grep '^Time = ' | tail -1 | awk '{print $3}'); echo $d run ${t:-0}; fi; done"],
    capture_output=True, text=True, check=True).stdout.split("\n")
lab_state = {l.split()[0]: l.split()[1:] for l in state if l.strip()}
lap_dir = os.path.expanduser("~/of_runs/full_h5mm")
lab_load = 0.0; queued = []
for d in lab:
    s = lab_state.get(d["run_id"])
    if s and s[0] == "done": continue
    if s:  # running: remaining fraction
        lab_load += cost(d) * (1 - float(s[1]) / float(d["end_s"]))
    else:
        queued.append(d)
lap_load = sum(cost(d) for d in lap if not os.path.exists(f"{lap_dir}/{d['run_id']}/DONE"))
# lab driver order: longest first by end_s*W/s; move from the END of its queue
queued.sort(key=lambda r: -float(r["end_s"]) * float(r["W"]) / float(r["s"]))
lab_load += sum(cost(d) for d in queued)
hours = lambda load, f, j: load * f / j / 3600
print(f"before: laptop {hours(lap_load, LAP_F, LAP_J):.1f} h, lab {hours(lab_load, LAB_F, LAB_J):.1f} h, lab queued {len(queued)}")
moved = []
while queued and hours(lab_load, LAB_F, LAB_J) > hours(lap_load, LAP_F, LAP_J):
    d = queued.pop(); moved.append(d); lab_load -= cost(d); lap_load += cost(d)
print(f"after : laptop {hours(lap_load, LAP_F, LAP_J):.1f} h, lab {hours(lab_load, LAB_F, LAB_J):.1f} h, moved {len(moved)} runs")
if "--apply" in sys.argv:
    ids = [d["run_id"] for d in moved]
    open(f"{R}/moved_to_laptop.txt", "w").write("\n".join(ids) + "\n")
    rows = lap + moved
    with open(f"{R}/design_v2_full_laptop2.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=lab[0].keys()); w.writeheader(); w.writerows(rows)
    cmd = "cd ~/of_runs/full_h5mm && for r in " + " ".join(ids) + \
          "; do [ -e $r ] && { echo EXISTS $r; continue; }; mkdir $r && echo 'moved to laptop, not a result' > $r/MOVED_TO_LAPTOP && touch $r/DONE; done; ls */MOVED_TO_LAPTOP | wc -l"
    print("lab placeholders:", subprocess.run(["ssh", "labpc", cmd], capture_output=True, text=True).stdout.strip())
    print(f"laptop list: {len(rows)} runs")
