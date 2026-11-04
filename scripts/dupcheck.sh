#!/bin/bash
# Run folders in ~/of_runs/full_h5mm on laptop and lab vs the n2 designs: overlaps, extras, solver settings
unset LD_LIBRARY_PATH
S=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
R="/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench"
T=$(mktemp -d)
# one line per run folder: name status nOuter outletBC created
list='cd ~/of_runs/full_h5mm && for d in T*/; do d=${d%/}; s=other
  [ -f $d/DONE ] && s=DONE; [ "$s" = other ] && [ -f $d/log.solver ] && s=running_or_stopped
  ls $d | grep -q MOVED && s=placeholder
  n=$(grep -ho "nOuterCorrectors *[0-9]*" $d/system/fvSolution 2>/dev/null | grep -o "[0-9]*$")
  b=$(grep -c fixedMean $d/0/p_rgh 2>/dev/null)
  echo "$d $s n$n fixedMean$b $(stat -c %y $d | cut -c1-16 | tr " " T)"; done'
bash -c "$list" > $T/laptop.txt
ssh -o BatchMode=yes labpc "$list" > $T/lab.txt
running_l=$(ps -eo cmd | grep "[b]uoyantPimpleFoam" | grep -v parallel | grep -o "T[0-9]*_lam" | sort -u)
python3 - "$T" "$R" <<'EOF'
import csv, sys, collections
T, R = sys.argv[1:]
def read(m):
    return {l.split()[0]: l.split()[1:] for l in open(f"{T}/{m}.txt") if l.strip()}
have = {m: read(m) for m in ("laptop", "lab")}
plan = {m: {r["run_id"] for r in csv.DictReader(open(f"{R}/design_v2_full_{m}_n2.csv"))} for m in ("laptop", "lab")}
for m in have:
    print(f"\n=== {m}: {len(have[m])} folders; status {dict(collections.Counter(v[0] for v in have[m].values()))}")
    print("    settings:", dict(collections.Counter(tuple(v[1:3]) for v in have[m].values())))
    extra = sorted(set(have[m]) - plan[m])
    print(f"    folders NOT in its own n2 list: {len(extra)}")
    for e in extra:
        other = "lab" if m == "laptop" else "laptop"
        print(f"      {e} {' '.join(have[m][e])} | in {other} list: {e in plan[other]} | {other} has it: {' '.join(have[other].get(e, ['no']))}")
both = sorted(set(have["laptop"]) & set(have["lab"]))
print(f"\nfolders present on BOTH machines: {len(both)}")
for e in both:
    print(f"  {e}: laptop {' '.join(have['laptop'][e])} | lab {' '.join(have['lab'][e])}")
dd = [e for e in both if have['laptop'][e][0] == 'DONE' and have['lab'][e][0] == 'DONE']
print(f"DONE on both: {len(dd)} {dd}")
print(f"\nplan overlap laptop&lab lists: {len(plan['laptop'] & plan['lab'])}; union {len(plan['laptop'] | plan['lab'])}")
EOF
rm -rf $T
