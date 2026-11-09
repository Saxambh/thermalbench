# Zenodo: reserve the DOI now, request the quota increase, upload at submission (9 November 2026)

Saxam does every step that needs his account (sign-in, saving, sending). Nothing is uploaded now. The draft
stays private and editable until "Publish", which happens on the day the paper is submitted.

Sources:
- Zenodo help, "Quota increase" (https://help.zenodo.org/docs/deposit/manage-files/quota-increase): a
  one-time increase up to 200 GB per dataset, requested through the support form under "File upload quota
  increase", with the draft URL and the total size, and fewer than 100 files.
- "What are the size limitations of Zenodo?": the default is 50 GB and 100 files per record, and splitting
  one dataset across records is discouraged.

## Step 1. Account (Saxam)

1. Go to https://zenodo.org and sign up or log in.
2. Logging in with ORCID is best: it links the record to your ORCID profile. GitHub or e-mail also work.

## Step 2. Create the draft and reserve the DOI (Saxam, about 10 minutes)

1. Click **New upload**. Do not add files now.
2. **"Do you already have a DOI?"** Choose **No**, then click **"Get a DOI now!"**. This reserves the DOI.
   Copy it and send it to Claude: it goes into the manuscript's data statement, the cover letter and
   CITATION.cff.
3. Fill the fields with the texts below. All of them can be edited later.
4. Click **Save draft**. Do **not** click Publish.
5. Copy the draft's URL from the browser address bar; it is needed for Step 3.

**Resource type:** Dataset

**Title:** ThermalStorageBench: A CFD benchmark for machine learning in sensible and latent thermal energy
storage

**Creators** (in order):
- Bhattarai, Saxam (Kathmandu University)
- Baral, Bivek (Kathmandu University)
- Davidsson, Henrik (Lund University)

The list is to be confirmed with the co-authors before publishing.

**Description:**

> ThermalStorageBench is an open benchmark of transient two-dimensional OpenFOAM simulations for machine
> learning in thermal energy storage. It contains 1,212 charging and discharging runs of stratified water
> tanks (sensible storage) and 500 melting runs of finned and tilted phase change material cells with
> n-octadecane and lauric acid (latent storage). It also includes:
> - frozen manifests with checksums for every run;
> - fixed design-level train/test splits;
> - engineering metrics and baselines;
> - 204 trained network checkpoints (FNO, U-Net, Transolver) that reproduce the reported scores.
>
> The simulations are verified against pre-registered limits and validated against four published
> experiments. See the accompanying article and the README for the file layout and how to verify a
> download.

**Licence:** Creative Commons Attribution 4.0 International (CC BY 4.0). This is the proposal; it can be
changed before publishing if the co-authors prefer otherwise.

**Keywords:** thermal energy storage; benchmark dataset; phase change material; stratified tank; neural
operator; computational fluid dynamics; OpenFOAM

**Version:** 1.0.0

**Related works:** add the article's DOI once it exists ("is supplement to").

## Step 3. Request the quota increase (Saxam sends)

1. Go to https://zenodo.org/support and choose the category **"File upload quota increase"**.
2. Paste this message:

> Subject: Quota increase request for a research dataset (69 GB, 15 files)
>
> Dear Zenodo team,
>
> I would like to request a one-time quota increase for the following draft record:
>
> [paste the draft URL]
>
> The dataset is ThermalStorageBench, an open benchmark of computational fluid dynamics simulations for
> machine learning in thermal energy storage. It accompanies a research article that we will submit to the
> Journal of Energy Storage, which requires the data to be deposited in a public repository.
>
> - Total size: about 69 GB (decimal), in 15 files: 13 tar archives of simulation runs, one archive of
>   trained model checkpoints and one archive of manifests, plus a SHA256SUMS file and a README.
> - The largest single file is about 5.4 GB.
> - We would prefer to keep the dataset as one record, as it is one coherent dataset with one citation.
>
> We plan to upload the files and publish the record when the article is submitted. Thank you for your
> help.
>
> Kind regards,
> Saxam Bhattarai
> Kathmandu University

## Step 4. At submission (later)

1. Rename the code and data files for release, build the archives (`make_release.py --build`) and verify
   them with SHA256SUMS.
2. Upload the 15 archives, SHA256SUMS and the README (`DATA_README_deposit.md`) to the draft.
3. Publish the record on the day the paper is submitted. The code gets its own DOI through Zenodo's GitHub
   link.
