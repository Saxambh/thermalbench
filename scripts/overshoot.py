import json, sys, os, h5py, numpy as np
B = os.path.expanduser("~/of_runs/pilot_v2")
for r in sys.argv[1:]:
    j = json.load(open(f"{B}/{r}/case.json")); f = h5py.File(f"{B}/{r}/thermbench.h5", "r")
    T = f["fields/T"][:]; t = f["times_s"][:]
    Th = max(j["T_in_K"], j["T_init_K"]); Tc = min(j["T_in_K"], j["T_init_K"]); h = j["mesh_h_m"]
    over = T.reshape(len(t), -1).max(1) - Th; under = Tc - T.reshape(len(t), -1).min(1)
    print(f"{r}: inlet {j['inlet_port']} s={j['slot_m']} u={j['u_in_m_s']} W={j['W_m']} Re={j['Re_in']:.0f}")
    bad = np.where((over > 0.1) | (under > 0.1))[0]
    print(f"  snapshots with >0.1 K excursion: {len(bad)}/{len(t)}")
    for n in bad[:: max(1, len(bad)//6)]:
        i = np.unravel_index(T[n].argmax() if over[n] >= under[n] else T[n].argmin(), T[n].shape)
        print(f"  t={t[n]:7.1f}  over {over[n]:+.2f} K under {under[n]:+.2f} K at x={(i[1]+.5)*h:.3f} y={(i[0]+.5)*h:.3f}  cells>0.1K: {int(((T[n]>Th+.1)|(T[n]<Tc-.1)).sum())}")
