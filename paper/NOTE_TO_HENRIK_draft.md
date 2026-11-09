Subject: Draft paper on a shared test set for fast storage models: would value your view

Hi Henrik,

I hope you are well. I have a first full draft of a paper I would like you to be part of, together with Bivek, and I would really value your view before it goes further.

**What it is about, in short.** Many groups now train fast "learned" models to predict how storage tanks and PCM stores behave, so they can stand in for slow CFD runs. But every group tests its model on its own few simulations, so nobody can tell which approach is actually better. I built an open set of simulations that everyone can use for the same test:
- 1,212 simulations of stratified hot-water tanks charging and discharging;
- 500 simulations of PCM melting in cells with and without fins, at different tilts.

They come with fixed rules for which cases are used for training and which for testing. The simulations are checked against four published experiments, including the Lou et al. tank and the Kamkari PCM tests.

**What came out when we tested common models on it.**
- Within one type of store, the learned models are much better than simple interpolation and than a calibrated 1D multi-node tank model.
- A tank discharging is like a tank charging turned upside down, with hot and cold swapped. Using that symmetry is what lets a model trained only on charging predict discharging.
- When the PCM material changes (trained on one wax, tested on the other), simple interpolation beats every learned model. That seems to me the clearest open problem.
- The best model depends on what you need. For example, the simple 1D model predicts the tank outlet temperature better in some cases, even though it gets the full temperature field wrong.

**The draft** is attached (`MANUSCRIPT_draft_v1.docx`). The target is the Journal of Energy Storage, and the main text is short. The appendices with the detailed checks are not written yet.

**Where your view would help most:**
1. From the building and storage side, does the paper answer a question that people in your field actually care about? Is the way I frame it (a shared test set first, findings second) the right way round for those readers?
2. Is there anything about how tanks or PCM stores are used in practice that I have missed or got wrong, especially in the tank set-up or in which quantities matter most (for example outlet temperature, stored energy, melting time)?
3. Would you be comfortable being on the paper as the last author? And would you consider being the corresponding author? I ask because the journal decides open access by the corresponding author's university, and Lund's agreement may make it free to read for everyone. I completely understand if that is more than you want to take on; I can handle all the correspondence either way.

There is no rush. Even a short reaction to the first question would help me a lot.

Best regards,
Saxam
