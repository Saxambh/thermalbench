"""Run on each CFD machine (laptop, lab, pc3): for every tank list there, print the run_ids that are
this machine's job (not a MOVED placeholder) and whether they are DONE with thermbench.h5. Used by freeze_all.sh."""
import csv, glob, json, os, socket
R = "/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench"
H = {"Saxam": "laptop", "DESKTOP-HK82PPA": "lab", "SoRrYnAh": "pc3"}[socket.gethostname()]
L = {"laptop": [(f"{R}/design_v2_full_laptop_n2.csv", "~/of_runs/full_h5mm"), (f"{R}/design_v2_full_laptopx_n2.csv", "~/of_runs/full_h5mm_x")],
     "lab": [("~/thermbench/design_v2_full_lab_n2.csv", "~/of_runs/full_h5mm"), ("~/thermbench/design_v2_full_labx_n2.csv", "~/of_runs/full_h5mm_x"), ("~/thermbench/design_v2_full_laby_n2.csv", "~/of_runs/full_h5mm_x"), ("~/thermbench/design_v2_full_labz_n2.csv", "~/of_runs/full_h5mm_x")],
     "pc3": [("~/thermbench/design_v2_full_pc3_n2.csv", "~/of_runs/full_h5mm")]}[H]
out = []
for f, d in L:
    f, d = os.path.expanduser(f), os.path.expanduser(d)
    for r in csv.DictReader(open(f)):
        p = f"{d}/{r['run_id']}"
        if glob.glob(f"{p}/MOVED*"):
            continue
        out.append({"m": H, "list": os.path.basename(f), "run_id": r["run_id"], "done": os.path.exists(f"{p}/DONE"),
                    "h5": os.path.exists(f"{p}/thermbench.h5")})
print(json.dumps(out))
