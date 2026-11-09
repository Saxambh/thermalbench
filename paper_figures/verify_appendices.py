"""Traceability check for the appendices: every quoted number must appear in the source note it comes from.
Writes out/VERIFY_APPENDICES.md; exits non-zero on any miss."""
import os, sys
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ML = os.path.join(R, "thermbench_ml")
S = {"dossier": os.path.join(R, "VALIDATION_DOSSIER_2026-11-07.md"), "crit": os.path.join(R, "verification_criteria_2026-11-06.md"),
     "lou": os.path.join(R, "validation_Lou2023_case_data.md"), "loures": os.path.join(R, "verification_data", "lou_outlet_2026-11-07", "RESULT.md"),
     "altref": os.path.join(ML, "altref_2026-11-07", "RESULT.md"), "pcmres": os.path.join(ML, "pcm_final_2026-11-08", "RESULT.md"),
     "plan": os.path.join(ML, "extra_baselines_2026-11-08", "PLAN.md"), "conf": os.path.join(ML, "confirmation_discharge_2026-11-07", "RESULT.md"),
     "dci": os.path.join(ML, "stats_2026-11-07", "design_ci.md"), "mn": os.path.join(ML, "multinode_2026-11-08", "RESULT_tables.md"),
     "mnr": os.path.join(ML, "multinode_2026-11-08", "RESULT.md"), "rta": os.path.join(ML, "repro_all_2026-11-08", "RESULT.md"),
     "rpc": os.path.join(ML, "repro_pcm_2026-11-08", "RESULT.md"), "proxy": os.path.join(ML, "proxy_check_2026-11-07", "RESULT.md"),
     "pcmcard": os.path.join(R, "DATASET_CARD_pcm_draft.md"), "t99": os.path.join(R, "verification_data", "pcm_timestep_t99.md"),
     "env": os.path.join(R, "release", "README.md"), "paired": os.path.join(ML, "pcm_final_2026-11-08", "PAIRED.md")}
T = {k: open(v, encoding="utf-8").read() for k, v in S.items()}
Q = [("0.34 %", "dossier"), ("0.60 %", "dossier"), ("1.70 %", "dossier"), ("2.76 %", "dossier"), ("0.96 %", "dossier"), ("7.38", "dossier"), ("7.32", "dossier"),
     ("0.47", "dossier"), ("2.14", "dossier"), ("1.96", "dossier"), ("2.49 %", "dossier"), ("0 to 31 %", "dossier"), ("3.9 %", "dossier"),
     ("0.7 to 8.3 %", "dossier"), ("−0.62", "dossier"), ("+0.12", "dossier"), ("38.5 %", "dossier"), ("1.6 % above 30", "dossier"),
     ("1.0 to 8.7 %", "dossier"), ("median 4.9 %", "dossier"), ("0.036", "dossier"), ("4.2 to 7.6 %", "dossier"), ("13.06", "dossier"), ("7.50", "dossier"),
     ("0.741", "dossier"), ("9.5 %", "dossier"), ("6.76 %", "dossier"), ("−2.1 to +0.9 %", "dossier"), ("2.54 %", "dossier"), ("17 cases", "dossier"),
     ("≤ 1.5 %", "dossier"), ("> 25 mm", "dossier"), ("230,156", "lou"), ("−2.9 mm", "lou"), ("−0.9 mm", "lou"), ("+10.8 mm", "lou"), ("0.180", "lou"), ("0.151", "lou"),
     ("19 %", "lou"), ("0.1 mm", "lou"), ("0.81", "loures"), ("0.750", "loures"), ("0.919", "loures"), ("0.850", "loures"), ("0.985", "loures"), ("0.77", "loures"),
     ("0.768", "loures"), ("0.788", "loures"), ("18 runs, 23 run-split rows", "altref"), ("+0.54", "altref"), ("+0.20 → +0.24", "altref"), ("T0221_lam", "altref"),
     ("random 3, fins 15", "pcmres"), ("0.10 K", "pcmres"), ("0.60 K", "pcmres"), ("0.04559", "plan"), ("0.0473", "plan"), ("1.16 M", "plan"), ("0.012", "plan"),
     ("15 times", "plan"), ("+9.17", "conf"), ("[+8.33, +10.02]", "conf"), ("+9.74", "conf"), ("[+8.84, +10.64]", "conf"), ("+12.53", "conf"), ("+12.61", "conf"),
     ("259", "conf"), ("215", "conf"), ("96 %", "conf"), ("95 %", "conf"), ("0.0004", "conf"), ("+0.41 [+0.34, +0.48]", "dci"),
     ("7.07", "mn"), ("6.21", "mn"), ("0.83", "mn"), ("2.26", "mn"), ("0.67", "mn"), ("6.65", "mn"), ("3.11", "mn"), ("2.01", "mn"), ("6.63", "mn"), ("3.02", "mn"),
     ("1.29", "mn"), ("9.60", "mn"), ("5.46", "mn"), ("1.62", "mn"), ("0.17 K [0.02, 0.34]", "mnr"), ("0.31 K [0.12, 0.52]", "mnr"), ("0.05 s", "mnr"),
     ("19,704", "rta"), ("16,056", "rpc"), ("0.00016 K", "rpc"), ("0.990 to 1.009", "proxy"), ("0.62", "proxy"), ("2.3", "proxy"), ("29.7", "proxy"),
     ("2.5 % / 15 % / 51 %", "proxy"), ("0.10 %", "pcmcard"), ("Python 3.12.3", "env"), ("uses 100 of", "pcmres"),
     ("0.86 | 11 / 13", "dossier"), ("| 0.82 |", "dossier"), ("| 0.94 |", "dossier"), ("4.0 | 91 % / 96 %", "dossier"), ("3.5 | 88 % / 93 %", "dossier"),
     ("3.7 | 90 % / 94 %", "dossier"), ("71 % / 84 %", "dossier"), ("19 % / 37 %", "dossier"), ("about 0.38", "dossier")]
miss = [(q, s) for q, s in Q if q not in T[s]]
L = [f"# Appendix numbers: traceability", "", f"{len(Q)} quoted values, {len(miss)} not found in their source.", ""] + [f"- MISSING: `{q}` in {S[s]}" for q, s in miss]
os.makedirs(os.path.join(R, "paper_figures", "out"), exist_ok=True)
open(os.path.join(R, "paper_figures", "out", "VERIFY_APPENDICES.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
print(f"{len(Q)} quoted values, {len(miss)} missing"); [print("MISSING", q, "in", s) for q, s in miss]
sys.exit(1 if miss else 0)
