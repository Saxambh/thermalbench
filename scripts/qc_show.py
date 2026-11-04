import json, sys, os
B = os.path.expanduser(sys.argv[1])
for r in sys.argv[2:]:
    d = json.load(open(f"{B}/{r}/qc.json"))
    print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in d.items() if k not in ("type",)})
