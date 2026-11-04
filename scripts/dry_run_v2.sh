#!/bin/bash
unset LD_LIBRARY_PATH
S=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
D="/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench"
cd "$D" && python3 $S/make_design.py --h 0.005 --fine-h 0.0033333333333 --out design_v2
for n in full fine128; do
  rm -rf ~/of_runs/dry_$n
  nice -n 10 python3 $S/run_batch.py "$D/design_v2_$n.csv" ~/of_runs/dry_$n --jobs 4 --dry-run > ~/of_runs/dry_$n.log 2>&1
  echo "$n: $(grep -c dry_ok ~/of_runs/dry_$n/batch_status.csv) dry_ok; failures:"
  grep -v "dry_ok\|^run_id" ~/of_runs/dry_$n/batch_status.csv | head
  rm -rf ~/of_runs/dry_$n
done
python3 - "$D" <<'EOF'
import csv, sys
d = sys.argv[1]
f = {r["run_id"]: r for r in csv.DictReader(open(f"{d}/design_v2_full.csv"))}
g = list(csv.DictReader(open(f"{d}/design_v2_fine128.csv")))
same = all(all(f[r["run_id"]][k] == r[k] for k in ("u_in","dT","s","off","W","inlet_type","mode","yi","tstar","turb")) for r in g)
print(f"fine subset: {len(g)} runs, identical physical parameters to their 5 mm twins: {same}")
EOF
