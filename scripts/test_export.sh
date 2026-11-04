#!/bin/bash
# Exporter tests: (1) synthetic MIX/Str limits, (2) real laminar charge, energy balance
# against the inflow, (3) turbulent type-B case (k, omega, nut export path).
unset LD_LIBRARY_PATH
source /usr/lib/openfoam/openfoam2606/etc/bashrc
SRC=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
B=~/of_runs/export_tests; rm -rf $B; mkdir -p $B
echo "== 1 synthetic tanks (expect MIX 0 for sharp layering, 1 for fully mixed)"
python3 - $SRC <<'EOF'
import sys; sys.path.insert(0, sys.argv[1])
import numpy as np, export_case as ex
meta = {"props": "real", "T_in_K": 333.15, "T_init_K": 293.15, "H_m": 1.0, "W_m": 0.5, "mesh_h_m": 0.005}
ny, nx = 200, 100
sharp = np.full((ny, nx), 293.15); sharp[120:, :] = 333.15          # hot top 40 %
m1 = ex.metrics(sharp, meta, 0.005**2)
E = m1["E_J"]
# fully mixed tank with the same energy: solve for uniform T by bisection
lo, hi = 293.15, 333.15
for _ in range(60):
    mid = 0.5 * (lo + hi)
    if ex.metrics(np.full((ny, nx), mid), meta, 0.005**2)["E_J"] < E: lo = mid
    else: hi = mid
m2 = ex.metrics(np.full((ny, nx), mid), meta, 0.005**2)
print(f"  sharp:  MIX={m1['MIX']:.4f}  y_mid={m1['y_mid_m']:.3f} m (expect 0.600)  Str={m1['Str']:.3f}")
print(f"  mixed:  MIX={m2['MIX']:.4f}  T={mid-273.15:.2f} C  Str={m2['Str']:.3f}  E equal: {abs(m2['E_J']-E)/E:.1e}")
EOF
run() {
  local n=$1; shift
  python3 $SRC/make_tank_case.py $B/$n "$@" > /dev/null
  cd $B/$n; blockMesh > log.blockMesh 2>&1
  local app=$(foamDictionary -entry application -value system/controlDict)
  $app > log.solver 2>&1 || { echo "$n solver FAILED"; return 1; }
  python3 $SRC/export_case.py $B/$n
}
echo "== 2 real laminar charge, 100 s: stored energy vs inflow (no hot water leaves yet)"
run lam --props real --uin 0.02 --end 100 --write 20 && python3 - $B/lam $SRC <<'EOF'
import sys, json; sys.path.insert(0, sys.argv[2])
import make_tank_case as g, export_case as ex
c = sys.argv[1]; s = json.load(open(f"{c}/metrics.json")); m = s["case"]
Tin, Tc = m["T_in_K"], m["T_init_K"]
flux = g.poly(g.RHO_C, Tin) * m["u_in_m_s"] * m["slot_m"] * (ex.h_int(Tin) - ex.h_int(Tc))  # W per m depth
for r in s["snapshots"]:
    exp = flux * r["t_s"]
    err = (r["E_J"] - exp) / exp * 100 if exp else 0.0
    print(f"  t={r['t_s']:6.1f} s  E={r['E_J']/1e6:8.4f} MJ/m  inflow={exp/1e6:8.4f} MJ/m  diff={err:+.3f} %  "
          f"MIX={r['MIX']:.3f}  y_mid={r['y_mid_m']:.3f}  thick={r['thick_m']:.3f}  T_out={r['T_out_K']-273.15:.2f} C")
EOF
echo "== 3 turbulent type B, 5 s (k, omega, nut path)"
run tb --props real --inlet-type B --W 0.3 --s 0.02 --uin 0.1 --turb kOmegaSST --buoy --end 5 --write 2.5
python3 - $B/tb <<'EOF'
import sys, numpy as np
c = sys.argv[1]
try:
    import h5py; f = h5py.File(f"{c}/thermbench.h5"); keys = list(f["fields"].keys()); T = f["fields/T"][:]; k = f["fields/k"][:]
except ImportError:
    f = np.load(f"{c}/thermbench.npz"); keys = [x for x in f.files if x.startswith("fields_")]; T = f["fields_T"]; k = f["fields_k"]
print("  arrays:", keys, "shape", T.shape, " T range", T.min().round(2), T.max().round(2), " k max", float(k.max()))
EOF
du -sh $B/lam/thermbench.* $B/lam/[0-9]* 2>/dev/null | tail -3
