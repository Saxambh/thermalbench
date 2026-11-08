# ThermalStorageBench novelty recheck (2026-11-02)

**Purpose.** The PCM parameter plan asked for a recheck, before the paper claims it, that no comparable open, validated simulation dataset or ML benchmark exists for thermal storage, including PCM melting. This extends the general Scopus search of 2026-10-30.

**Access.** Scopus through the IIT Madras federation. Dataset sizes of ML benchmarks were checked on the web, because Scopus covers NeurIPS dataset papers poorly.

## Scopus queries (all PUBYEAR > 2014 unless stated)

| # | Query (TITLE-ABS-KEY) | Hits | What they are |
|---|---|---|---|
| S1 | (PCM / latent heat storage) AND (ML / NN / neural operator / surrogate) AND (CFD / OpenFOAM / enthalpy-porosity / numerical simulation) AND (dataset / database / benchmark) | 51 | Building envelopes, battery cooling, triplex tubes, concrete. Each trains a model on its own small set of simulations; no shared dataset. |
| S2 | (PCM / latent heat) AND melting AND (enclosure / cavity / rectangular / fins) AND (ML / NN / neural operator / physics-informed) | 97 | Mostly ANNs predicting scalar outputs (melt fraction, melting time, Nu) from a handful to a few hundred CFD runs, per paper and per geometry. |
| S3 | (PCM / latent heat storage / TES / thermocline / storage tank / heat storage) AND (neural operator / FNO / DeepONet / U-Net / CNN / GNN / PINN) AND (temperature field / spatiotemporal / full-field / field prediction / flow field / temperature distribution) | 19 | PINNs for single cases, one FNO on PCM walls, one graph CNN on synthetic 1D data. No multi-case open dataset. |
| S4 | ("benchmark dataset" / "open dataset" / "public dataset" / "ML benchmark") AND (heat transfer / phase change / boiling / natural convection / TES / thermocline) AND (simulation / CFD), PUBYEAR > 2017 | 18 | Code-validation benchmarks (nuclear, divertor), DNS databases, indoor-airflow datasets. None is for thermal storage or for ML on storage. |

## Closest works (read in detail)

**Shen, Wu & Duan (2025)**, AI Thermal Fluids 1:100001, "Machine learning for predicting the PCM melting process in a rectangular enclosure energy storage". This is the same problem class as our PCM family.
- An ANN predicts the melt front and temperature distribution in a rectangular enclosure with two fins.
- It is trained on **3 simulations** (fin lengths 12.5, 25 and 37.5 mm) and tested on 2 unseen fin lengths.
- No open dataset, benchmark splits or baselines.

**Benzaama (2026)**, J. Energy Storage 175:123309. Compares universal differential equations with a **Fourier neural operator** for PCM in cement-mortar walls.
- Conduction in a wall: no convection, no melting cavity, no dataset release.

**Chen, He & Song (2026)**, J. Energy Storage 146:120035. A PINN constrained by a total-enthalpy lattice Boltzmann model, for solid-liquid phase change with natural convection.
- One case at a time; not a dataset.

**Tacques Filho (2025)**, MSc dissertation, UFRGS (advisor M. Dorn), "Generating reliable computational data through the Lattice Boltzmann Method: a simulation of the Lauric Acid melting process". Source: event-page abstract only; the repository page returned HTTP 502.
- OpenLB enthalpy LBM; lauric acid in a rectangular cavity with **one fin**.
- **12 fin configurations** (position, length, thickness).
- Validated against a lauric-acid experiment that is not named (liquid fraction and thermocouples).
- Called a "prototype structured dataset" (VTK) for future ML. **No ML is trained**; no splits or metrics; publication of the data is not stated.
- **To cite as related work.** Retry the repository record (lume.ufrgs.br/handle/10183/303708) for the PDF and any data link before submission.

**Small single-paper PCM datasets on Mendeley Data** (2025 and 2026): mushy-constant sweep (3D Fluent), hexagonal enclosures with Y-fins, sine-shaped fins. Each comes from one paper and one geometry family, with no benchmark tasks.

## ML benchmark datasets: sizes for the comparison table (web, 2026-11-02)

| Dataset | Venue | Physics | Size |
|---|---|---|---|
| AirfRANS | NeurIPS 2022 D&B | RANS airfoils | **1,000** simulations (800 train / 200 test; scarce regime 200 train; OOD Re and angle splits) |
| PDEBench | NeurIPS 2022 D&B | generic PDEs | e.g. 2D compressible NS: **1,000** samples per file (512 × 512, 21 steps); larger totals across files |
| BubbleML | NeurIPS 2023 D&B | boiling (phase change) | **79** simulations (Flash-X), validated against experimental trends |
| CFDBench | arXiv 2023 | 4 canonical flows | **739** cases in total (302k frames) |
| The Well, `rayleigh_benard` | NeurIPS 2024 D&B | Rayleigh-Benard convection | **1,750** trajectories (512 × 128, 200 steps) |
| **ThermalStorageBench (ours)** | | tank charging/discharging + PCM melting | **1,217** tank runs (+153 fine-mesh) + **500** PCM cases, every family validated against experiments |

## Conclusion

No open, validated, multi-case simulation dataset with ML benchmark tasks exists for **thermal energy storage**, either for stratified tanks or for PCM melting.
- **PCM ML studies:** each trains on its own few simulations (3 in the closest one) with no shared splits or baselines.
- **The nearest dataset efforts:** the UFRGS dissertation (12 cases, no ML) and BubbleML (boiling, 79 runs, a different application).
- **ThermalStorageBench's scale:** at 1,717 distinct cases, larger than AirfRANS (1,000), CFDBench (739) and BubbleML (79), and of the same order as The Well's Rayleigh-Benard set.

**Safe wording for the paper:** "to our knowledge, the first open benchmark for ML in thermal energy storage". Cite BubbleML as the closest phase-change ML benchmark, and the UFRGS dissertation and Shen et al. 2025 as the closest PCM efforts.

**Before submission:**
- rerun S1 to S4, since new papers are appearing quickly (several 2026 hits);
- retry the UFRGS repository;
- check arXiv directly for "thermal storage" plus "benchmark", because Scopus does not index arXiv.

## Addendum (2026-11-02, evening): charge/discharge symmetry in ML for storage tanks

**Why.** The interim benchmark found that the hybrid FNO, trained on charging runs only, fails on discharging runs (2.9 K vs 0.8 K). Rotating discharge runs by 180 degrees and swapping hot and cold (the "canonical frame") brings it to 0.68 K. The question: has anyone used this symmetry, or any symmetry, in ML for thermal storage?

| # | Query (TITLE-ABS-KEY) | Hits | Relevant |
|---|---|---|---|
| S5 | (TES / storage tank / thermocline / hot water tank / stratified tank) AND (NN / ML / DL / surrogate) AND (symmetr* / equivarian* / invarian* / canonicali*) | 13 | 0 (proceedings volumes, laser scanning of tanks, cyber-attacks, PCM slurry optimisation) |
| S6 | (TES / storage tank / thermocline / stratif*) AND (NN / ML / DL / surrogate / neural operator) AND charg* AND discharg* AND (generaliz* / extrapolat* / transfer learning / unseen / out-of-distribution) | 7 | 0 (PCM state-of-charge estimation, CatBoost fin design, building-to-grid RL). Closest: Marotta et al. 2026, Energy and AI 26:100919, domain-adapted DL for PCM state of charge from images; not CFD, not charge-to-discharge transfer |
| S7 | (NN / DL / neural operator / ML) AND (equivariant / symmetry-aware / symmetry-preserving / canonicalization / physical symmetr*) AND (natural convection / Rayleigh-Benard / heat transfer / buoyan* / thermal convection / stratified flow) | 1 | Wang, Walters & Yu, ICLR 2021 (the method precedent) |
| S8 | (NN / DL / neural operator / surrogate) AND (equivariant / symmetry-aware / symmetry-preserving / canonicalization / symmetry constraint* / embedded symmetr*) AND (fluid dynamics / fluid flow / turbulen* / CFD / Navier-Stokes) | 32 | Method precedents only: rotation/reflection-equivariant networks for fluids, none for thermal storage |

**Method precedents to cite** (symmetry in ML for fluids):
- Wang, Walters & Yu 2021, ICLR, "Incorporating symmetry into deep dynamics models for improved generalization".
- Wang, Walters & Yu 2022, PMLR 162, "Approximately equivariant networks for imperfectly symmetric dynamics". Relevant, because our symmetry is only approximate (real, temperature-dependent water properties).
- Siddani, Balachandar & Fang 2021, Phys. Fluids 33:103323, rotational and reflectional equivariant CNN for data-limited flow problems.
- Lino et al. 2022, Phys. Fluids 34:087110, rotation-equivariant graph networks for unsteady fluid dynamics.

**Conclusion.**
- Building symmetries into neural networks for fluids is established, so the paper must not claim the method.
- No Scopus-indexed work applies the charge/discharge symmetry of a stratified tank, or any symmetry, to ML for thermal storage, or tests charge-to-discharge transfer.
- **Safe wording:** "We show that the charge/discharge symmetry of a stratified tank, applied as a simple change of frame, lets a surrogate trained only on charging predict discharging at the CFD noise level". Cite Wang et al. 2021 and 2022 for the general principle.
- **Before submission:** check arXiv directly (Scopus covers ML conferences poorly).

**Sources (web):**
- AirfRANS: [NeurIPS 2022](https://proceedings.neurips.cc/paper_files/paper/2022/hash/94ab7b23a345f93333eac8748a66c763-Abstract.html), [PyPI](https://pypi.org/project/airfrans)
- BubbleML: [NeurIPS 2023](https://proceedings.neurips.cc/paper_files/paper/2023/hash/01726ae05d72ddba3ac784a5944fa1ef-Abstract.html)
- CFDBench: [arXiv 2310.05963](https://arxiv.org/pdf/2310.05963)
- The Well: [arXiv 2412.00568](https://arxiv.org/pdf/2412.00568)
- PDEBench: [arXiv 2210.07182](https://arxiv.org/pdf/2210.07182)
- UFRGS: [dissertation event page](https://www.inf.ufrgs.br/ppgc/eventos/evento/dissertacao-de-mestrado-de-alexandre-de-quadro-tacques-filho)
- Mendeley Data: [mushy-constant dataset](https://data.mendeley.com/datasets/5kvbfptt39/2)

## Addendum 2026-11-06: Ma et al. 2026 (missing from this file; found by the audit)

**Paper.** Ma, Liu, Zhang, ..., Zhao, Tian (2026), *Journal of Energy Storage* 180:124366, "Multi-objective
optimization of fin-embedded concrete thermal energy storage systems using CFD and machine learning".
Found in the Scopus check of 2026-10-30 (sand-battery screening), solid-media + embedded pipes + ML,
13 hits.

**What it does.** 3D CFD of a concrete store with finned embedded pipes, a hybrid deep-learning
surrogate trained on those runs, then a multi-objective genetic algorithm over fin number, height and
thickness.

**Overlap with ThermalStorageBench.** CFD plus ML surrogate for thermal storage, including a finned
geometry parameterisation (as in our PCM family).

**Difference.**
- It is a single-study surrogate for one optimisation, with its own data and no released dataset or
  benchmark.
- It covers sensible solid storage, not stratified water tanks or PCM melting.
- There are no out-of-distribution splits, no comparison of operator architectures and no
  verification protocol.

**Consequence.** The paper must cite it in the related work, alongside the S1 papers that "each train a
model on its own small set of simulations". It does not change the novelty claim (an open, verified
CFD dataset with fixed splits for ML on thermal storage).

**Wording to revise.** "At the CFD noise level" in the safe wording above should be replaced. The
collaborator note of 2026-11-06 asks not to call the perturbation sensitivity a noise floor. Use "within
the measured sensitivity of the CFD solution to small perturbations" once stage 1A gives that number for
the discharge cases.

## Addendum 2026-11-08: arXiv check and web recheck (before the outline)

**Why.** This was listed as "before submission: check arXiv directly", because Scopus does not index arXiv. It
was run once the PCM and Transolver results were in, so that the paper's positioning is checked before writing.

**arXiv API queries** (abstract field, newest first, read back to 2024):

| # | Query (abstract) | Hits | Relevant |
|---|---|---|---|
| A | "thermal energy storage" AND (benchmark OR dataset) AND (neural OR "machine learning") | 1 | 2512.01011 (below) |
| B | "phase change" AND melting AND (neural operator / Transolver / Fourier / DeepONet / surrogate) | 8 | none for storage (laser melt pools, plasma reactor) |
| C | (thermocline / "stratified tank" / "storage tank") AND (neural / surrogate / ML) | 7 | none (cryogenic tank data assimilation, climate) |
| D | Transolver AND (heat / thermal / melting) | 4 | none for storage; 2610.40731 uses a canonical coordinate frame (below) |
| E | ("latent heat" / PCM) AND (dataset / benchmark) AND (neural / learning) | 42 | none ("PCM" mostly phase-change memory) |
| F | (natural convection / Rayleigh-Benard / buoyancy) AND (neural operator / Transolver) AND (dataset / benchmark) | 1 | 2510.21804 (below) |
| G | (solid-liquid / enthalpy-porosity / melting front) AND (neural / learning) | 60 | none (atomistic ML potentials) |
| H | (heat transfer / thermal) AND "neural operator" AND (out-of-distribution / generalization) AND material | 6 | 2607.25668 (below) |
| I | (stratification / stratified) AND (neural operator / FNO) AND (tank / storage / thermal) | 0 | |
| J | "thermal storage" AND (CFD / OpenFOAM / simulation) AND (neural / surrogate / learning) | 1 | none since 2024 |

**Web search** (three searches) for journal papers and datasets since 2 November: nothing new for stratified
tanks; for PCM only the single-study Mendeley datasets already listed (plus a March 2026 hexagonal Y-fin set,
DOI 10.17632/dk9tktnk78.1, DNN training data for one paper).

**New works to cite (none changes the novelty claim):**
- **IC-ThermBench** (arXiv 2608.23977, August 2026): open benchmark for chip (2.5D/3D-IC) thermal learning,
  50,000 samples, eight baselines, generalisation scopes including material variation and cross-package
  out-of-distribution transfer, where error rises sharply (best RMSE 1.2 to 16.0 K). The closest benchmark
  *design* to ours, in a different application. Its sharp out-of-distribution degradation parallels our
  material-transfer result; cite as supporting context, not as precedent for storage.
  **Name clash:** "ThermBench" is used by this benchmark. Our release name is still open; avoid "ThermBench"
  alone (the working name ThermalStorageBench is distinct but close).
  **Decision (8 November, after review by Astra): keep ThermalStorageBench** (chosen 5 November). A
  tentative rename to HeatStoreBench was reverted: readers of thermal-energy journals search for "thermal
  storage", and the name covers sensible (tank) and latent (PCM) storage. The collision risk with
  IC-ThermBench is low for the full name; the risk is shortening ours to "ThermBench". **Rule:** the full
  name ThermalStorageBench is used everywhere (paper, captions, repository, dataset deposit, citation
  metadata), never "ThermBench". Suggested paper title: "ThermalStorageBench: A CFD benchmark for machine
  learning in sensible and latent thermal energy storage".
- **REALM** (arXiv 2512.18595): benchmark of neural surrogates on 11 realistic reactive-flow datasets,
  including spectral operators and Transformers; argues simplified proxies hide fragility. Cite with PDEBench
  and The Well as benchmark precedent.
- **Two-phase heat transfer open-data review** (arXiv 2605.23037, NED3): boiling, condensation, immersion
  cooling; calls for benchmark splits and baselines. Not storage.
- **2512.01011** (November 2025): physics-driven deep learning for a 2D finned PCM store (Stefan problem,
  forced air cooling), one system, three networks. Add to the PCM single-study group (Shen et al. 2025).
- **2601.22086** (January 2026): geometry-aware generative world model for 2D transient buoyant convection
  coupled to a solid, tested on unseen geometries. Related method, no storage, no open benchmark.
- **2510.21804 XRePIT** (October 2025): OpenFOAM plus neural-surrogate hybrid for 3D buoyancy-driven flow.
  Related tooling, not a dataset.
- **2610.40731** (October 2026): DeepONet with a Transolver trunk in a canonical (body-fitted) coordinate
  frame for hypersonic shapes. A further example of canonicalisation as a method; does not touch the
  charge/discharge symmetry claim.
- **2607.25668** (July 2026): PINO (FNO backbone) on 1,500 1D wall-conduction solutions for ranking wall
  materials. Conduction only; no material-transfer test in our sense.
- **Building TES ML review** (Energy Reports 2026, PII S2352484726007006; seen in a search snippet only,
  the page refused automated access): reportedly identifies the lack of shared benchmark problems and open
  datasets as a gap. **Verify authors, DOI and wording in a browser before citing**; if confirmed, it is the
  strongest motivation citation.

**UFRGS dissertation:** retried; the repository page timed out (HTTP 504). A search snippet now describes
it as aiming to demonstrate the data's suitability for training ML models, with public code. **Check in a
browser** whether any model was trained; it remains 12 single-fin lauric-acid cases without benchmark splits
or baselines.

**Conclusion (unchanged):** no open, verified, multi-case CFD dataset with fixed out-of-distribution splits
and ML baselines for thermal energy storage (stratified tanks or PCM melting) was found on arXiv or the web
as of 8 November 2026. Rerun Scopus S1 to S8 just before submission.

**Wording (revised after review, 8 November).** The search conclusion is narrower than a "first open
benchmark" claim, so the paper leads with the verifiable contribution instead: "an open benchmark combining
transient stratified-tank and PCM-melting fields with fixed design-level splits, engineering metrics, and
released CFD verification cases". A priority claim ("to our knowledge, the first ...") is at most secondary
and only if the final Scopus rerun supports it. This supersedes the "safe wording" above and in the
2 November conclusion.
