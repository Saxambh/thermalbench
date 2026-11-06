# PCM accepted-output inventory (2026-11-07, about 01:30 Nepal)

File: `pcm_inventory_2026-11-07.csv`, one row per physical case (500). Built by
`scripts/pcm_inventory_collect.sh` (run on every machine) and `scripts/pcm_inventory.py`.

## Counting terms (the 514 "QC checks" of 7 Nov were case folders, not cases)

- **Physical cases:** 500 (design `scripts/pcm_full.csv`).
- **Case folders found:** 703, across six machines plus the pc5 archive on the laptop's D: drive.
  They comprise:
  - identical copies of moved runs;
  - superseded originals;
  - half-fix reruns;
  - corrected reruns;
  - runs still in progress.

  At most 4 folders per case.
- **Accepted outputs:** exactly one per case. It is the authoritative output; all other folders are
  provenance (`superseded` column).

## Acceptance rules

1. **Usable:** DONE, not a moved-away placeholder, `pcm_qc.py` status OK or WARN, final solver set-up
   (p_rghFinal relTol 0).
2. **Corrected reruns** (PCG + DIC for both pressure solves, or a fresh rerun) replace the dataset run.
3. **A dataset run whose pressure solves failed** (solver QC FAIL) is never accepted; the case waits for
   its corrected rerun.
4. **Identical copies:** one is chosen by machine order. No accepted case has a copy that differs in size.

## Status

| Status | Cases |
|---|---|
| Accepted | **489** |
| Corrected rerun running | 6: P0044, P0143, P0224, P0294, P0362, P0495 |
| Dataset run still running (long cases) | 3: P0095 (laptop), P0280, P0316 (pc3) |
| Needs a corrected rerun (solver QC FAIL, found 7 Nov) | 2: P0419 (28 % capped), P0442 (19 % capped) |

**Accepted cases in detail**
- **pcm_qc:** 479 OK, 10 WARN.
- **Solver QC:** 425 ok, 59 WARN, and 5 corrected reruns (P0124, P0181, P0228, P0273, P0371).
- **Repairs:** 38 accepted cases carry the 7 Nov series repair.
- **Energy-balance error:** median 0.15 %, largest 1.6 %.

## Before the freeze

1. **Outstanding cases.** The 6 running reruns, the 3 running dataset runs, and corrected reruns of
   P0419 and P0442 must finish and pass QC.
2. **WARN sensitivity.** The check fixed in `verification_criteria_2026-11-06.md` (6 WARN cases, rule set
   in advance) decides whether any WARN group is rerun.
3. **Rebuild.** The inventory is regenerated. The freeze manifest is written from its accepted outputs
   only, with md5 sums.
