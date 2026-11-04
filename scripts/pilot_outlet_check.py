# For each finished pilot case: does the outlet slot see backflow (fluid entering through the outlet)?
import os, json, glob, numpy as np, h5py
B = os.path.expanduser("~/of_runs/pilot_h5mm")
print(f"{'case':10} {'type':4} {'mode':9} {'s_mm':>4} {'u_in':>6} {'Umax/u_in':>9} {'backflow snaps':>14} {'worst backflow frac':>19} {'Umax late/early':>15}")
for c in sorted(glob.glob(f"{B}/*/DONE")):
    d = os.path.dirname(c); j = json.load(open(f"{d}/case.json"))
    f = h5py.File(glob.glob(f"{d}/*.h5")[0], "r")
    ux, uy = f["fields/ux"][:], f["fields/uy"][:]
    nt, ny, nx = ux.shape; h = j["mesh_h_m"]
    side, a, b = j["outlet_port"]
    if side in ("left", "right"):
        rows = slice(int(round(a/h)), int(round(b/h)))
        col = 0 if side == "left" else nx-1
        un = ux[:, rows, col] * (-1 if side == "left" else 1)        # positive = leaving the tank
    else:
        cols = slice(int(round(a/h)), int(round(b/h)))
        un = uy[:, ny-1 if side == "top" else 0, cols] * (1 if side == "top" else -1)
    back = (un < 0).mean(axis=1)
    U = np.sqrt(np.asarray(ux)**2 + np.asarray(uy)**2).reshape(nt, -1).max(axis=1)
    u = j["u_in_m_s"]
    print(f"{j['case']:10} {j['inlet_type']:4} {j['mode']:9} {j['slot_m']*1e3:4.0f} {u:6.3f} {U.max()/u:9.1f} "
          f"{(back>0).sum():6d}/{nt:<7d} {back.max():19.2f} {U[nt//2:].max()/U[1:nt//2].max():15.2f}")
