# ThermalStorageBench: paper outline (9 November 2026)

**Target:** Journal of Energy Storage, full length research article (`JES_guide_notes_2026-11-09.md`):
at most about 6,000 words, 8 to 10 figures and tables, replication detail and sensitivity analyses in
appendices.

**Authors:** Saxam Bhattarai, Bivek Baral, Henrik Davidsson. The corresponding author is decided before
submission.

**Title (Astra, 8 November):** ThermalStorageBench: A CFD benchmark for machine learning in sensible and
latent thermal energy storage.

**Contribution sentence (lead claim, agreed):** an open benchmark combining transient stratified-tank and
PCM-melting fields with fixed design-level splits, engineering metrics, and released CFD verification
cases. A "first" claim is secondary at most, and only if the final Scopus rerun supports it.

**Rules for the text:**
- Every number comes from a committed result note (source given per item below).
- Wording already agreed with the reviewer is used as agreed.
- The name is always ThermalStorageBench in full.
- No em-dashes or en-dash connectors.
- FNO and U-Net are co-equal baselines, with no "main model".

## Figure and table budget (9 items in the main text)

| # | Item | Content | Source |
|---|---|---|---|
| Fig. 1 | Benchmark overview | Both families: tank (types A/B, ports, slot, width range) and PCM cavity (heated wall, 0 to 5 fins, tilt); design parameters; the split scheme (which axis each OOD split holds out) | parameter plans, `splits.py`, `pcm_splits.py`, `figures_mesh/` |
| Table 1 | Dataset summary | Per family: physics, solver, mesh, runs, parameter ranges, outputs per run, QC outcome, size, manifest md5 | dataset cards |
| Fig. 2 | Validation | (a) Lou jet depth h_j(t), ours, PIV and their CFD; (b) Lou outlet T*(t*), ours vs the two β reconstructions; (c) Kamkari melt fraction (plain wall, 1 and 3 fins, tilt); (d) Vogel & Thess | `validation_*.md`, `verification_data/lou_outlet_2026-11-07/` |
| Table 2 | Tank benchmark | Field error (% of ΔT) for all baselines and 8 neural variants on 4 splits; multi-node 1D model; design-level intervals in Appendix E | `results_merged/tables.md`, `stats_2026-11-07/`, `multinode_2026-11-08/` |
| Fig. 3 | Tank: where models fail | (a) charge/discharge symmetry, ood_mode error with and without the canonical frame; (b) error against Ri (jet-dominated regime); (c) one hard example: CFD, prediction, error | `confirmation_discharge_2026-11-07/`, dossier §8.2 |
| Table 3 | PCM benchmark | Field RMSE (seed mean ± SD) and t90 error for FNO, U-Net, Transolver (plain, hybrid) and the baselines on 6 splits | `pcm_final_2026-11-08/RESULT_tables.md`, `extra_baselines_2026-11-08/RESULT_ts_tables.md` |
| Fig. 4 | PCM material transfer | Per-seed field RMSE in both directions against IDW; t90 crossing rates | `pcm_final_2026-11-08/RESULT.md`, `extra_baselines_2026-11-08/RESULT.md` |
| Fig. 5 | Field accuracy vs melt time | Per-model field RMSE against t90 error on held-out fins (U-Net / Transolver rank change); multi-node vs surrogates (profile vs near-outlet) as a second panel | `result_ts.json`, `multinode_2026-11-08/compare.json` |
| Fig. 6 | Example predictions | One tank and one PCM test run: CFD, prediction, error at three times | h5 data and release checkpoints |

There is room for one more item if needed (for example, uncertainty calibration); otherwise it goes to
Appendix F.

## Sections and word budget (main text about 6,000 words; abstract 250 words separately)

### 1. Introduction (about 800 words)
- **Why it matters:** thermal storage design and control need fast transient models, and ML surrogates are
  proposed for this.
- **The gap:** each ML study trains on its own few simulations, with no shared splits or baselines, so
  results cannot be compared (Shen et al. 2025, 3 simulations; the Scopus single-study groups;
  2512.01011; Ma et al. 2026).
- **Benchmark precedent in other fields:** PDEBench, The Well, AirfRANS, BubbleML, CFDBench, REALM,
  IC-ThermBench. A building-TES ML review calling for shared benchmarks can be cited once it is verified
  (browser check pending).
- **Contribution:** the agreed sentence, then the four findings in one sentence each:
  1. neural surrogates beat interpolation within a family, but material transfer reverses the ranking;
  2. the charge/discharge symmetry gives discharge prediction from charge-only training;
  3. which model is preferred depends on the predicted quantity (field vs melt time, profile vs outlet);
  4. everything is reproducible from the release, with all 204 checkpoints verified.
- **Paper structure** paragraph.

### 2. Dataset (about 1,300 words)
- **2.1 Stratified tank family** (about 450 words):
  - 2D, OpenFOAM v2606 buoyantPimpleFoam, real water properties (not Boussinesq), 5 mm mesh, laminar and
    SST twins;
  - Sobol design over width, slot, port offset, type A/B, charge/discharge, inflow, ΔT, pre-stratification;
  - 1,212 runs; outputs per run (121 snapshots, energy, exergy, MIX, stratification, thermocline, outlet T).
- **2.2 PCM family** (about 400 words):
  - enthalpy-porosity melting, n-octadecane and lauric acid (mushy constants and their provenance,
    disclosed);
  - 0 to 5 conducting fins, heating from the side, 45° and from below;
  - 500 runs; a priori time scale t_ref from the inputs only.
- **2.3 Quality control and freeze** (about 450 words):
  - QC rules applied as pre-registered;
  - tank exclusions; PCM: 34 corrected reruns and 39 solver-WARN cases kept under the pre-registered
    rule;
  - frozen manifests with md5;
  - label flags (T0211, T0052).
- **2.4 Verification** (short; detail in Appendix A):
  - pre-registered limits;
  - tank mesh 2.5 vs 5 mm: 0.34 to 2.76 % of ΔT field difference in four designs; not converged, stated;
  - outer iterations and time step;
  - PCM mesh: the finer mesh melts later by 1.0 to 8.7 % (6 designs); GCI only where the levels allow
    (G131: 13.06 / 7.50 %).
- **Sources:** dataset cards, dossier §2 to §5 and §9 to §12, with the corrections table.

### 3. Validation against experiments (about 600 words; Fig. 2)
- **3.1 Tank solver set-up, 3D, Lou et al. 2023:**
  - **Jet depth h_j:** the mean bias hides a trend (−2.9 mm early, +10.8 mm at 500 to 700 s); the
    between-test spread is not an uncertainty band.
  - **Outlet T*:** the agreed wording (10 % onset under constant β; 50 % at t* 0.932 vs about 0.97 to
    1.045; 0.08 to 0.20 warmer over t* 0.95 to 1.45; heat loss consistent in direction, not isolable).
  - **σ:** one sentence.
  - **Statement:** this validates the solver set-up, not the 2D labels directly.
- **3.2 PCM:**
  - Kamkari plain wall, 1 and 3 fins, tilt (fins about 0.1 too fast in the first hour; 3-fin full melt
    8 % early);
  - Vogel & Thess;
  - the residual-difference wording (discretisation, properties, BCs, experiment, model form not
    separable).

### 4. Benchmark tasks, splits, metrics and baselines (about 800 words)
- **4.1 Tasks:** tank: inputs plus t* to the θ field. PCM: inputs plus τ to T and liquid fraction.
- **4.2 Splits:**
  - tank: random, ood_geom (tails of one geometry family), ood_mode (discharge, approximate symmetry),
    ood_flow (SST-only Re extrapolation);
  - PCM: random, held-out fins, stronger heating, unseen tilt, material transfer in both directions;
  - assignment by design point.
- **4.3 Metrics:**
  - field RMSE; profile; thermocline midpoint (with its missing rate); energy (constant-ρcp proxy, within
    ±1 %); outlet (area-averaged, differs from flow-weighted; Appendix I);
  - PCM: liquid IoU, energy, t90 with crossing rate.
- **4.4 Baselines and models:**
  - initial, 1D ideal stratification, multi-node 1D (calibrated; protocol fixed before test), kNN/IDW/RBF,
    front model;
  - FNO and U-Net (plain, hybrid, canonical; 3 seeds);
  - 4×4-patch Transolver (PCM only; tank gate failed, stated as an implementation and resource
    decision);
  - training details in Appendix D.

### 5. Results (about 1,700 words)
- **5.1 Tank** (about 750 words; Table 2, Fig. 3):
  - surrogates vs interpolation and 1D models, using the agreed multi-node wording (profile error 3.6 to
    4.1 pp lower; the 1D model is better at the near-outlet on discharge and high flow);
  - canonical frame: without it 13 to 67 % on ood_mode, with it about 4.4 %; confirmed on 215 designs
    (+9.2 / +9.7 pp, Holm p 0.0004);
  - regime: error grows as Ri falls, SST about 2× laminar, worst runs SST with Ri below about 9;
  - the alternative-reference check (at most 0.43 pp, ordering kept).
- **5.2 PCM** (about 700 words; Table 3, Fig. 4, Fig. 5):
  - lead with the ranking change across generalisation tasks (agreed paragraph);
  - material transfer by direction with seeds;
  - Transolver: no new winner, best melt-time error within a material, material-transfer failure shared
    by all three architectures;
  - the field vs t90 sentence (held-out fins);
  - WARN robustness in one sentence.
- **5.3 Reproducibility and cost** (about 250 words):
  - all 204 checkpoints rescored (agreed wording: exact on the training workers; 1.6×10⁻⁴ K in the
    cross-GPU spot check);
  - speed as a latency ratio (about 6,500, hardware stated, no equal-cost claim).

### 6. Discussion: what the benchmark does and does not test (about 550 words)
- 2D vs 3D; adiabatic walls; one mesh with known PCM early melting; two materials only.
- ood_flow mixes Re and closure; ood_mode relies on an approximate symmetry.
- **Uncertainty:** the seed spread ranks error and the calibrated bound holds except on ood_mode
  (Appendix F).
- **How to use the benchmark:** report seeds, the crossing rate next to t90, and the flagged runs.
- **What we do not claim:** see dossier §14 as corrected.

### 7. Conclusions (about 250 words)

### Back matter
- **Data availability:** repository DOI (licence and hosting to decide before submission); code
  repository; manifests with md5.
- **CRediT;** funding; competing interests; **declaration of generative AI use** (wording to agree with all
  authors); acknowledgements.
- **References:** numbered, DOIs, every one verified.

## Appendices (no word limit stated; keep focused)

| Appendix | Content | Source |
|---|---|---|
| A | Verification detail: pre-registered limits; tank mesh and settings (T0221, T0243, T0408, T0551); T0211 regime tests; PCM mesh, time step, GCI | `verification_criteria_2026-11-06.md`, `verification_data/`, `figures_verification/` |
| B | Lou details: digitisation, the β reconstructions, σ definition and the 0.81 slope, the mesh check of the lower baffle | Lou folder, `validation_Lou2023_case_data.md` |
| C | Label flags, the alternative-reference study, PCM WARN sensitivity | `altref_2026-11-07/`, `label_flags_tank.json`, PCM result |
| D | Model and training details: architectures, epochs, learning rates, batch sizes; Transolver amendment and gate; hybrid and canonical definitions | `models.py`, `PLAN.md` files |
| E | Statistics: design-level intervals (tank), run-level paired intervals (PCM), seed tables | `stats_2026-11-07/`, `PAIRED.md`, `RESULT_ts_tables.md` |
| F | Uncertainty: spread vs error and calibrated bounds | `capacity_2026-11-07/` |
| G | Multi-node 1D model: formulation, calibration, results | `multinode_2026-11-08/` |
| H | Reproducibility audit: checkpoint provenance, rescoring, cross-GPU note | `repro_all_2026-11-08/`, `repro_pcm_2026-11-08/` |
| I | Metric definitions and proxies (energy proxy, outlet area vs flux weighting, y_mid missing rate, t90 reference sampling) | `proxy_check_2026-11-07/`, `pcm_t90_ref_check.json` |

## Before submission (not writing)

1. Author list final, including whether Martin is on it; corresponding author and OA route.
2. Licence, hosting and the data DOI.
3. Scopus rerun (S1 to S8); verify every reference and DOI; the two browser checks (Energy Reports
   review, UFRGS thesis).
4. Agreement of all authors on the AI-use declaration and a preprint (arXiv / SSRN or none).
5. Highlights (3 to 5, at most 85 characters each), keywords (at most 7), graphical abstract.

## Proposed writing order

1. Figures and tables first (they fix the numbers).
2. Sections 4 and 5.
3. Sections 2 and 3.
4. Appendices.
5. Introduction, discussion, conclusions.
6. Abstract and highlights last.
