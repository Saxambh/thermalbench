Subject: Would you like to join a paper on a shared test set for thermal storage models?

Dear Henrik,

I hope you are well. I am writing to ask whether you would like to be a co-author on a paper I have been working on, together with Bivek. I have attached a first full draft, and I would really value your view on it.

**What the paper is about**

Many groups now train fast "learned" models that predict how hot-water tanks and PCM stores behave, so they can replace slow CFD runs in design and control. The problem is that every group tests its model on its own small set of simulations, so nobody can say which approach actually works better.

I have built an open set of simulations that everyone can use as the same test:
- 1,212 simulations of stratified hot-water tanks, charging and discharging;
- 500 simulations of PCM melting, with and without fins and at different tilts.

They come with fixed rules for which cases are used for training and which for testing. The simulations are checked against four published experiments: the Lou et al. tank, the Kamkari PCM tests with fins and tilt, and the Vogel and Thess PCM cell.

**What we found when we tested common models on it**

- Within one type of store, the learned models are clearly better than simple interpolation and than a calibrated 1D multi-node tank model.
- A tank discharging is like a tank charging turned upside down, with hot and cold swapped. Using that symmetry is what allows a model trained only on charging to predict discharging.
- When the PCM material changes (trained on one wax, tested on the other), simple interpolation beats every learned model. This seems to me the clearest open problem.
- Which model is best depends on what you need. For example, the simple 1D model predicts the tank outlet temperature better in some cases, even though it gets the full temperature field wrong.

**What I would like to ask you**

1. **Co-authorship.** Would you be willing to be a co-author? The order I had in mind is Saxam Bhattarai, Bivek Baral, and you as the last author. Please tell me if you would prefer something different.

2. **Your view as a storage and building-energy researcher.** This is where your input would matter most:
   - Does the paper answer a question that people in your field care about?
   - Is anything about how tanks or PCM stores are used in practice missing or wrong?
   - Are we measuring the quantities that matter, such as outlet temperature, stored energy and melting time?

3. **Corresponding author.** We plan to submit to the Journal of Energy Storage. The journal decides free open access by the corresponding author's university, and Lund's agreement may make the paper free to read for everyone. Would you consider being the corresponding author? I would still prepare all the files and draft all the replies, so it would mainly mean submitting under your name and forwarding the editor's messages. I fully understand if you would rather not; in that case I will be the corresponding author and we publish without the open-access option.

4. **A few details for the paper:**
   - the exact affiliation and e-mail address you would like us to use;
   - your contribution roles for the author statement (the journal uses CRediT, for example "Writing: review and editing", "Validation", "Supervision");
   - any funding or project you would like acknowledged, or confirmation that there is none to add.

5. **Two points the journal asks all authors to agree on:**
   - We used an AI assistant (Claude) to help with code, data analysis and drafting, and the journal requires a short statement saying so. All the numbers come from our own simulations and are checked by a separate script. Are you comfortable with that statement?
   - Would you be happy for us to post a preprint (on arXiv or SSRN) when we submit, or would you prefer to wait?

**Timeline**

There is no rush. I am now writing the appendices and checking every reference, and I would like to submit within the next few weeks, after you and Bivek have read it. Even a short reaction to questions 1 and 2 would help me a lot.

The draft is attached (MANUSCRIPT_draft_v1.docx, 20 pages; the appendices with the detailed checks are not written yet).

Thank you very much for considering this.

Best regards,
Saxam
