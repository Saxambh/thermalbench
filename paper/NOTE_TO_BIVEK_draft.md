Subject: Draft of the thermal storage benchmark paper for your review

Dear Sir,

I hope you are well. I am sharing the first full draft of the paper on the thermal storage benchmark (ThermalStorageBench), with you as second author, for your review. I have also sent it to Henrik Davidsson at Lund and asked whether he would like to join as last author.

In short, the paper releases an open set of simulations that others can use to test fast "learned" models for storage:
- 1,212 hot-water tank simulations, charging and discharging;
- 500 PCM melting simulations, with fins and tilt.

The simulations are checked against four published experiments. The paper then compares common models on this shared test. The main findings:
- within one type of store, the learned models clearly beat simpler methods;
- a symmetry of the tank makes discharging predictable from charging data;
- when the PCM material changes, simple interpolation beats every learned model, which is an open problem.

We plan to submit to the Journal of Energy Storage. The draft (MANUSCRIPT_draft_v1.docx) is attached; the numbers in it are generated from our results and checked by a separate script.

I would be grateful for:
1. your comments on the draft, especially on whether the framing and claims are suitably careful;
2. your contribution roles for the author statement (for example, "Supervision", "Writing: review and editing", "Validation");
3. any funding or project we should acknowledge (for RP2 we acknowledged the SOLARFOOD project, Research Council of Norway 352437, and Erasmus+ ICM; please tell me whether these or others apply here);
4. your agreement on two points the journal asks of all authors: a short statement that an AI assistant (Claude) helped with code, analysis and drafting, and whether to post a preprint when we submit.

I aim to submit in the coming weeks, after both co-authors have read it.

With best regards,
Saxam
