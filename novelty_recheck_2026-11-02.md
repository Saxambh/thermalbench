# ThermBench novelty recheck (2026-11-02)

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
| **ThermBench (ours)** | | tank charging/discharging + PCM melting | **1,217** tank runs (+153 fine-mesh) + **500** PCM cases, every family validated against experiments |

## Conclusion

No open, validated, multi-case simulation dataset with ML benchmark tasks exists for **thermal energy storage**, either for stratified tanks or for PCM melting.
- **PCM ML studies:** each trains on its own few simulations (3 in the closest one) with no shared splits or baselines.
- **The nearest dataset efforts:** the UFRGS dissertation (12 cases, no ML) and BubbleML (boiling, 79 runs, a different application).
- **ThermBench's scale:** at 1,717 distinct cases, larger than AirfRANS (1,000), CFDBench (739) and BubbleML (79), and of the same order as The Well's Rayleigh-Benard set.

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
