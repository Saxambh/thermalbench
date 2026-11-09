# ThermalStorageBench data release: plan (9 November 2026)

The Journal of Energy Storage requires the data in a repository and cited with a link in the article
(Guide for Authors, "Option C"), so the deposit must exist, at least as a reserved DOI, before submission.

Sizes are in decimal GB (10⁹ bytes); the manifests record file sizes in MB of 10⁶ bytes.

## What is packed (dry run, `make_release.py`, plan in `plan/archives.tsv`)

| Archives | Contents | Size |
|---|---|---|
| tank_runs_01 to 11 | 1,212 tank run folders: h5 file, case.json, metrics.json, qc.json, system/ | 54.5 GB |
| pcm_runs_01 to 02 | 500 PCM run folders, same files | 10.3 GB |
| checkpoints | 96 tank + 108 PCM checkpoints with provenance tables (the replaced WRONG_SOURCE file is excluded) | 4.2 GB |
| manifests | frozen manifests (md5 per run), split code, label flags, dataset cards | < 0.01 GB |
| **Total** | **15 archives** | **69.0 GB** |

- Every run in both manifests was found.
- Archives are cut at about 5 GB.
- A SHA256SUMS file is written with the build.
- Not packed: solver logs and raw OpenFOAM time folders. They stay on the machines until the DOI exists,
  and the backup on G: holds the laptop copies.

## Decisions for Saxam (and co-authors)

1. **Licence.**
   - Proposal: **CC BY 4.0 for the data and checkpoints** (anyone may reuse with attribution; the usual
     choice for research data, and accepted by Zenodo and Elsevier's data policy).
   - Proposal: **MIT for the code** (short and permissive; usual for ML benchmark code).
   - Alternatives:
     - CC0 for the data (no attribution required; maximises reuse but loses the citation requirement);
     - Apache-2.0 for the code (adds an explicit patent grant).
2. **Repository.**
   - Proposal: **Zenodo** (free, gives a DOI, versioned, CERN-hosted, links to GitHub).
   - Its standard limit per record is about 50 GB (check the current limit when uploading), so 69 GB needs
     either:
     - (a) a quota increase, which Zenodo grants on request for research data; or
     - (b) three linked records: tank archives 01 to 06, tank archives 07 to 11, and PCM + checkpoints + manifests (the tank alone is 54.5 GB, above the limit).
   - A record can be created as a draft with a **reserved DOI** before upload, which is enough for the
     manuscript's data statement.
   - Alternatives with larger limits exist (e.g. institutional repositories, Hugging Face datasets), but
     Zenodo is the most common for CFD datasets.
3. **Account.** The deposit should be made from Saxam's own Zenodo account (Saxam signs in; Claude does
   not handle credentials). If Henrik becomes corresponding author, a Lund repository is also possible.

## Steps (in order)

1. Decide licence and repository (above).
2. **Rename for release:**
   - `thermbench_ml` to a ThermalStorageBench package name;
   - `thermbench.h5` to `ThermalStorageBench.h5` (or keep the file name and document it);
   - folder and README names;
   - rerun the rescoring check afterwards on a few checkpoints so the rename breaks nothing.
3. **Build:** `python3 make_release.py --build /mnt/g/ThermalStorageBench_release` (about 1 hour; G: has
   room). Verify SHA256SUMS.
4. **Code:** tag a release on GitHub (repos to be renamed by Saxam), archive it to Zenodo through the GitHub
   integration (gives the code its own DOI).
5. **Upload** the archives to the Zenodo draft (Saxam signs in), with a README:
   - what each archive holds;
   - how to verify with SHA256SUMS and the manifests' md5;
   - the licence;
   - how to cite.
6. Put the DOI(s) into the manuscript's data statement and the dataset cards. Publish the record at
   submission or at acceptance, as the authors prefer.
