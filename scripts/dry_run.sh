#!/bin/bash
unset LD_LIBRARY_PATH
S=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
D="/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench"
cd "$D" && rm -f design_h5mm_*.csv && python3 $S/make_design.py --h 0.005 --out design_h5mm 2>&1 | grep -v Warning
for n in pilot full; do
  rm -rf ~/of_runs/dry_$n
  python3 $S/run_batch.py "$D/design_h5mm_$n.csv" ~/of_runs/dry_$n --jobs 16 --dry-run > ~/of_runs/dry_$n.log 2>&1
  echo "$n: $(grep -c dry_ok ~/of_runs/dry_$n/batch_status.csv) dry_ok, failures:"
  grep -v "dry_ok\|^run_id" ~/of_runs/dry_$n/batch_status.csv | head
done
rm -rf ~/of_runs/dry_full   # 1188 meshes, not needed
