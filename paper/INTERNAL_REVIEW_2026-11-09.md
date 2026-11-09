# Internal referee read of draft v1 and the changes made (9 November 2026)

**The read.** An independent reviewer agent, without our reasoning, checked the draft against the committed
source notes.
- It found **19 claims that went beyond or misstated the sources**, 11 internal inconsistencies, 11 points a
  Journal of Energy Storage referee would raise, and writing problems.
- Each point was checked at source before any change.
- All fixes keep the automated checks passing (479 table/figure checks, 109 appendix values traced).

## Fixed (claims and consistency)

| Point | Was | Now |
|---|---|---|
| Discharge needs the frame | "required for discharge", "every model without the frame fails" | limited to the neural networks; the multi-node model transfers to discharge without special treatment (7.6 %), the hybrid networks reach 13 % |
| Hardest split | "faster inflow hardest for every model" | for the hybrid canonical networks and the 1D models only |
| Finding 1 | "within a storage family, neural operators beat..." | within one material, on field and profile metrics |
| Finding 4 | "everything is reproducible" | the release is auditable: checkpoints reproduce their stored per-run scores (tank: field score) |
| T0211 regime | "identified the low-Ri SST regime as sensitive" | one run affected; 0 of 10 in the pre-registered regime test; not systematic |
| Lou validation | "validated the solver set-up" | tests the SST set-up; laminar closure and discharge not validated; buoyancy source confirmed identical (the Lou case uses the same buoyancyTurbSource) |
| Outlet wording | "outlet temperature" | "near-outlet temperature", with the up-to-30 % mixing-cup caveat in Section 4.3 |
| "2 to 4 times" | "within a material" | random, fin-count and heating tests |
| QC history | "rules written before they were applied"; "no energy can leave"; "34 failed cases" | automated checks; the solver check was added after the first failure; almost no energy leaves; 34 reruns = 13 failed + 21 under the warning rule |
| PIV wording | "within the scatter of the two tests" | within 9 mm of the PIV mean up to 450 s |
| Kamkari plain wall | "within ±0.05, melts at 195 min" | ±0.06, 194.7 min; agreement partly by construction (the same experiment set the mushy constant) and possibly cancellation with mesh error |
| Kamkari tilt | "within ±0.08" | states that those runs used Cu 10⁶ |
| PCM melting | "networks often fail to melt at all" | rarely predict near-complete melting (2 % and 33 % reach 90 %; hybrid U-Net 100 %) |
| Best variant | hybrid + canonical implied best | clearly best only on discharge; canonical-only better on random and faster inflow; U-Net on unseen widths better with either alone |
| FNO and U-Net on discharge | "equal" | U-Net ahead by 0.13 pp [0.01, 0.24] |
| Confirmation | "no exposure", "confirmed" | "no identified exposure", "supported"; a pre-registered subset analysis, not prospective |
| Conclusions | "1,712 verified simulations" | quality-controlled, with verification on representative designs |
| Neural operator | used for U-Net | "neural models"; table headers changed |
| Fig. 3a | line labelled "best interpolation (RBF)" | the line is now the split's actual best (IDW on discharge) |
| Fig. 3b, "80 runs" | ambiguous | 821 run-split pairs pooled; 80 test cases |
| Fig. 6 θ | undefined for PCM | defined in Section 4.1 and the caption |
| Appendix E | cited Fig. 3 | cites Table 2 |
| Seed spread | "± 8.7 K" | standard deviation over three training seeds |
| Uncertainty | "holds at its stated rate" | close to its rate (88 to 91 % at 90 %), for the FNO ensemble |
| Energy proxy | "within ±1 % of the real value" | a model's real-property error equals its proxy error within ±1 % |
| Abstract | "charging temperature difference"; "each study" | inlet-to-tank temperature difference; almost always; trimmed to 247 words |

## Added

- **Table 3:** tank engineering metrics (stored energy, near-outlet temperature, thermocline midpoint) in the
  main text. Tables are renumbered in order of appearance; the PCM table is now Table 4.
- **Definitions:** Re, Ri (with their ranges), t* (with run lengths), Ra_H, Ste, MIX, Ri_bulk, the PCM θ, the
  front model, interpolation settings.
- **Section 6:**
  - label fidelity against model error (tank mesh 2.76 % against best errors of 3.5 to 4.5 %; PCM mesh 4.2 to
    7.6 % of ΔT, about 1 to 2 K, against best within-material errors of 0.59 to 1.76 K);
  - no solidification or cycling; constant properties; one cell height;
  - fins above three outside the validation;
  - laminar heating from below;
  - 2D slot ports and fixed height;
  - direct query, not rollout.
- **Methods disclosures:**
  - learning rates not tuned for FNO and U-Net;
  - epoch counts fixed from trial runs on earlier data subsets that also recorded test scores of
    preliminary models;
  - the multi-node fit is a limited search.
- **Cost:** about 3,200 core-hours for the tank CFD; PCM about 3,100 [TO CHECK: planned estimate]; 146.6
  GPU-hours of tank training.
- **References:** Benzaama et al. 2026 (FNO for PCM walls, J. Energy Storage), Siddani et al. 2021, Lino et
  al. 2022. All 26 are renumbered by first citation; the figure captions are updated to match.
- **Cover letter, highlights and graphical abstract** aligned with the corrected wording.

## Not done (candidates for the authors or for revision)

1. **A recognised 1D tank model** (for example TRNSYS Type 60 or 534) or a fully optimised multi-node fit;
   **a correlation-based PCM model**. The present 1D model is stated as reasonable, not optimal.
2. **A resolution argument** for laminar heating from below at Ra_H up to 9 × 10⁸, and for the laminar tank
   band. Stated only as a limitation.
3. **PCM parameter counts** for FNO and U-Net, and **the measured PCM CFD core-hours** (the plan estimate is
   used).
4. **Glossing ML and CFD jargon** in the main text (PIMPLE, Courant, AdamW, one-cycle, bfloat16, physics
   attention). Partly moved to Appendix D; a pass for storage readers is still useful.
5. **A short "Data records" subsection** (file format, loader, licence, version). Depends on the licence and
   repository decisions.
6. **Related work:** the Tacques Filho thesis (UFRGS) and the single-study Mendeley PCM datasets. Not cited,
   because the thesis record could not be read; check it in a browser.
