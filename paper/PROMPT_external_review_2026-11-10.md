You are reviewing a full manuscript draft before submission to the Journal of Energy Storage (Elsevier). Read it as a demanding but fair reviewer for that journal.

**Paper:** "ThermalStorageBench: A CFD benchmark for machine learning in sensible and latent thermal energy storage"

**Authors:** Saxam Bhattarai, Bivek Baral (Kathmandu University), Henrik Davidsson (Lund University).

**What it is:** an open benchmark of transient 2D OpenFOAM simulations. It has:
- 1,212 stratified-tank runs and 500 PCM melting runs (n-octadecane and lauric acid);
- fixed design-level splits, with eight out-of-distribution tests;
- baselines, plus FNO, U-Net and Transolver networks (plain and hybrid, 3 seeds);
- verification and validation against four published experiments;
- 204 released checkpoints, all rescored exactly from the frozen release.

Attached:
- the manuscript (.docx, with appendices A to I);
- highlights, graphical abstract, cover letter;
- the internal review log, which lists issues already found and fixed.

## Your task

1. **Score each aspect out of 10, with a short justification for each.** Aspects:
   - novelty and contribution;
   - fit to the Journal of Energy Storage;
   - title and abstract;
   - introduction and literature positioning;
   - dataset design (sampling, splits, OOD tests);
   - CFD set-up, verification and validation;
   - ML baselines and evaluation protocol;
   - statistical rigour (seeds, uncertainty, claims vs evidence);
   - results and interpretation;
   - figures;
   - tables;
   - limitations and honesty of claims;
   - reproducibility and data/code release;
   - writing clarity and structure;
   - references;
   - highlights, graphical abstract and cover letter.

   Then give an overall score and your likely editorial outcome: desk reject, major revision, minor revision or accept.

2. **List concrete problems, ranked by severity** (major / minor / cosmetic). Give each a location (section, figure, table or line) and a specific fix. For example: overclaims, numbers that do not agree across text, tables and figures, missing comparisons a reviewer would ask for, unclear methods, weak motivation, and anything a JES reviewer would attack first.

3. **List what is strongest**, so we do not weaken it while revising.

## Already known and pending: do NOT score these down as missing

These items are planned or in progress. Comment only if the plan for one of them is itself wrong or insufficient.

**A. Results still running (expected by 14 November 2026)**
- **PCM fine-mesh label check.**
  - The study: 60 pre-registered test cases are being rerun at 0.25 mm (the dataset uses 0.5 mm), and every PCM model will be rescored against the finer labels. Each ranking statement will be classed by pre-set rules as "holds", "not resolved by the labels" or "flips"; statements in the last two groups will be reworded.
  - Text it will update: the mesh appendix and the label-uncertainty limitation paragraph, which now rest on 6 spot-check cases and will rest on the 60.
  - Known caveat: a cost cap selects the cheaper half of the cases; this will be stated.
- **Extra seeds on the PCM material-transfer splits.** Seeds 3 and 4 for all six networks. Those rows will report 5 seeds, the rest stay at 3, and the table will say so.

**B. Waiting on the senior co-author's review (Henrik Davidsson, about one week)**
- Corresponding author and open-access route.
- Whether a further colleague (Martin) joins as author or is acknowledged.
- Funding statement.
- CRediT roles.
- AI-use declaration wording.
- Whether to post a preprint.

**C. Placeholders marked TO CHECK, to be settled before submission**
- **Total PCM CFD core-hours.** The text uses the planned estimate; measured solver times are partly collected.
- **The OpenFOAM buoyancy turbulence-source sign issue.** It is already reported to ESI as issue #3645, and will be rechecked against the current source.

**D. Release and metadata, done at submission**
- **Zenodo record.**
  - Status: the draft exists, and the DOI 10.5281/zenodo.24087719 is reserved and already in the data statement.
  - Files: about 69 GB in 15 archives plus SHA256SUMS and a README, uploaded and published on submission day.
- **Licence.** Proposed CC BY 4.0 for data and checkpoints, MIT for code; not final.
- **Code.** The public repository URL and the code DOI (via GitHub to Zenodo) will be added at release.
- **Final renaming.** Code, file and folder names will be renamed to the final project name at release.
- **Name.** "ThermalStorageBench" is final; do not suggest renaming it.

**E. Final checks before submission**
- Scopus novelty search, rerun just before submission.
- One related thesis (UFRGS MSc 2025, OpenLB lauric acid PCM, no ML) to be checked by hand for any ML content.
- Formatting against the JES Guide for Authors, done last.

## Output format

1. Score table: aspect, score /10, one-line justification.
2. Overall score and likely outcome.
3. Ranked problem list, with location and fix.
4. Strengths to keep.
5. Up to five additions or analyses that would most raise the paper's chance of acceptance, excluding everything listed under "Already known and pending".

Be specific and critical. Do not praise generally, and do not rewrite the paper.
