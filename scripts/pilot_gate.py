# Gate for starting the full batch: every pilot run DONE, no FATAL, no late velocity growth,
# energy metrics finite. Prints a report; exit 0 = pass.
import os, sys, json, glob, numpy as np, h5py
B = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else "~/of_runs/pilot_v2")
runs = sorted(d for d in glob.glob(f"{B}/*/") if os.path.exists(f"{d}case.json"))
ok = True
print(f"{'case':10} {'mode':9} {'u_in':>6} {'Umax/u_in':>9} {'late/early':>10} {'backflow max':>12}  verdict")
for d in runs:
    j = json.load(open(f"{d}case.json")); name = j["case"]
    if not os.path.exists(f"{d}DONE"):
        print(f"{name:10} NOT DONE"); ok = False; continue
    f = h5py.File(glob.glob(f"{d}*.h5")[0], "r")
    ux, uy = f["fields/ux"][:], f["fields/uy"][:]
    nt, ny, nx = ux.shape; h = j["mesh_h_m"]
    side, a, b = j["outlet_port"]
    if side in ("left", "right"):
        un = ux[:, int(round(a/h)):int(round(b/h)), 0 if side == "left" else nx-1] * (-1 if side == "left" else 1)
    else:
        un = uy[:, ny-1 if side == "top" else 0, int(round(a/h)):int(round(b/h))] * (1 if side == "top" else -1)
    U = np.sqrt(ux**2 + uy**2).reshape(nt, -1).max(axis=1)
    late = U[nt//2:].max() / U[1:nt//2].max()
    u = j["u_in_m_s"]
    bad = late > 3 or U.max() / u > 40
    fin = all(np.isfinite(np.asarray(f[f"metrics/{k}"])).all() for k in ("E_J", "T_mean_K"))
    if bad or not fin: ok = False
    print(f"{name:10} {j['mode']:9} {u:6.3f} {U.max()/u:9.1f} {late:10.2f} {(un<0).mean(axis=1).max():12.2f}  "
          f"{'OK' if not bad and fin else 'FAIL'}")
fatal = [d for d in runs if os.path.exists(f"{d}log.solver") and "FOAM FATAL" in open(f"{d}log.solver").read()]
if fatal: ok = False; print("FATAL in:", fatal)
print(f"runs {len(runs)}  GATE {'PASS' if ok and len(runs) == 24 else 'FAIL'}")
sys.exit(0 if ok and len(runs) == 24 else 1)
