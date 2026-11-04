#!/bin/bash
unset LD_LIBRARY_PATH
C=~/of_runs/e2e_test/P02_sst
cat ~/of_runs/e2e_test/batch_status.csv
echo "--- case dir contents (raw time dirs should be gone except 0)"; ls $C
du -sh $C
python3 - <<'EOF'
import h5py, json, os
c = os.path.expanduser("~/of_runs/e2e_test/P02_sst")
f = h5py.File(f"{c}/thermbench.h5")
print("fields:", {k: f["fields/" + k].shape for k in f["fields"]})
m = json.load(open(f"{c}/metrics.json"))
meta = m["case"]
print(f"Re {meta['Re_in']:.0f} Ri {meta['Ri_H']:.2f} end {meta['end_time_s']} s")
for r in m["snapshots"][::12]:
    print(f"  t*={r['tstar']:.2f}  MIX={r['MIX']:.3f}  Str={r['Str']:.2f}  y_mid={r['y_mid_m']:.3f}  thick={r['thick_m']:.3f}  T_out={r['T_out_K']-273.15:.2f} C")
EOF
echo "--- pilot status so far"; cat ~/of_runs/pilot_h5mm/batch_status.csv 2>/dev/null | tail -5; pgrep -fc buoyantPimpleFoam
