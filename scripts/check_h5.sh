#!/bin/bash
unset LD_LIBRARY_PATH
S=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
echo "laptop: $(python3 -c 'import numpy, h5py; print("numpy", numpy.__version__, "h5py", h5py.__version__)')"
echo "lab:    $(ssh labpc "python3 -c 'import numpy, h5py; print(\"numpy\", numpy.__version__, \"h5py\", h5py.__version__)'")"
python3 $S/export_case.py ~/of_runs/export_tests/lam
python3 - <<'EOF'
import h5py, os
f = h5py.File(os.path.expanduser("~/of_runs/export_tests/lam/thermbench.h5"))
print("  datasets:", sorted(f["fields"].keys()), f["fields/T"].shape, f["fields/T"].dtype)
print("  metrics:", sorted(f["metrics"].keys()))
print("  E at last snapshot (MJ/m):", round(float(f["metrics/E_J"][-1]) / 1e6, 4))
EOF
scp -q $S/make_tank_case.py $S/export_case.py labpc:thermbench/scripts/
