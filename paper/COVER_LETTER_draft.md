Editor-in-Chief
Journal of Energy Storage

Dear Editor,

We are pleased to submit our manuscript, "ThermalStorageBench: A CFD Benchmark for Machine Learning in Sensible and Latent Thermal Energy Storage," for consideration as a Full Length Research Article in the Journal of Energy Storage.

Machine-learning surrogates are increasingly proposed for the design and control of thermal energy storage, but almost every study trains and tests its model on its own small set of simulations, so the published accuracies cannot be compared and it is unknown which methods hold up beyond the cases they were trained on. Our manuscript provides a shared, open test for this purpose: an open benchmark combining transient stratified-tank and PCM-melting fields with fixed design-level splits, engineering metrics, and released CFD verification cases. Energy storage is the central subject throughout: the two families cover sensible storage in stratified water tanks (1,212 runs) and latent storage in finned and tilted PCM cells (500 runs), and the metrics are those used to judge a store, including thermocline position, near-outlet temperature, stored energy and melting time.

The manuscript makes four contributions:
- the quality-controlled dataset, with pre-specified verification limits on representative designs, a measured sensitivity floor of the labels, and comparisons with four published experiments, including Lou et al. in this journal;
- fixed train and test splits for interpolation and eight out-of-distribution tests, with baselines ranging from calibrated one-dimensional storage models, scalar regressors and a POD model to three neural architectures (FNO, U-Net and, for PCM, Transolver);
- findings that matter for storage modelling: the charge/discharge symmetry of a tank lets neural networks trained on charging predict discharge; the preferred model depends on the quantity needed (for example, a calibrated multi-node model is as good as the networks at the delivered outlet temperature); and when the PCM material changes, no evaluated network beats interpolation or simple regressors on the design inputs, which identifies a clear open problem;
- an auditable release: all 204 network checkpoints reproduce their reported per-run scores when rescored from the deposited data.

The data, splits and checkpoints are deposited in Zenodo (https://doi.org/10.5281/zenodo.24087719), and the code in [code repository, to be added], in line with the journal's research data policy.

We confirm that this manuscript is original, has not been published previously, and is not under consideration for publication elsewhere. All authors have read and approved the submitted version, and there are no competing interests to declare. [Funding statement to be confirmed by the authors.] The use of generative AI tools in preparing the work is declared in the manuscript.

The corresponding author is [to be decided: Saxam Bhattarai (saxambhattarai1@gmail.com) or Henrik Davidsson].

Thank you for considering our manuscript. We look forward to your response.

Sincerely,
[Corresponding author], on behalf of the authors
