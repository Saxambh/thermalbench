# Referee fixes: new runs (plan, 10 November 2026)

Source: external referee read of draft v1 (Fable 2, 10 November; overall 6.7/10, major revision).
Saxam, 10 November: "stop the current runs and execute this fixes in all the pcs". The fine-mesh check and the extra
seeds were stopped at 05:46 UTC (finemesh_2026-11-10/PLAN.md, amendment 3); everything below was launched
05:50 to 06:40 UTC. Selections and settings are fixed in the scripts before any result. Results go to RESULT.md.

| # | Referee point | What runs | Where | Script |
|---|---|---|---|---|
| 1 | Chaotic labels: no noise floor | 24 test-side tank runs rerun with inlet velocity x (1 + 1e-4); 6 log-Ri bins x laminar/SST x 2, hash order, predicted wall <= 18 h | lab 9, pc4 6, pc6 6, pc3 3 | select_tank.py, run_tank_cfd.sh (tank_verify.sh "rep") |
| 2 | Near-outlet claim below proxy error | all tank models rescored on the flow-weighted outlet temperature (label velocity as weight), whole run and breakthrough window, paired with multinode | laptop | outlet_flow.py |
| 3 | Discharge: no mechanism, no ceiling | (a) diagnostic split mode_ceiling: half the discharge designs held out, the other half in training; fno/unet canon and hybrid canon, 3 seeds (12 jobs); (b) input diagnosis; (c) mechanism test, see below | all 5 GPUs; laptop | run_ceiling.sh, diag_canon.py, run_canonyi.sh |
| 4 | No practitioner baselines | gradient boosting and GP scalar regressors (tank energy, outlet, midpoint; PCM melted fraction, t90) and POD (32 modes) + gradient boosting field model, both families, all splits | pc7 CPU | scalar_pod.py |
| 5 | Inlet resolution | 2.5 mm reruns of the highest-Re 20 mm-slot run (T0851_sst, Re 5,809; the 20 mm slots never exceed this) and the highest-Re run overall (T0915_sst, Re 24,008, 80 mm slot), 8 cores each | lab | inlet.txt, run_tank_cfd.sh (tank_verify.sh "h25") |
| 6 | Kamkari tilt at 1e6, not the dataset's 5e6 | kam_t45 and kam_t90 rerun with mushy constant 5e6, otherwise as pcm_validate_fix.sh | pc4 | scripts/kamkari_tilt_5e6.sh |

Comparisons fixed now:
- Fix 1: rep vs dataset with cmp_tank.py (field, profile, energy, outlet, midpoint, by window); the noise floor per
  Ri bin and closure is set next to the model errors of the same runs. No threshold is changed afterwards.
- Fix 2: if the multinode advantage on discharge and faster inflow does not hold on the flow-weighted outlet (paired
  design-level interval excluding zero), the near-outlet claim leaves the abstract and is reworded as proxy-specific.
- Fix 3a: per held-out run, ceiling model vs the released ood_mode model of the same variant, design-level paired
  bootstrap (10,000, seed 20261110).
- Fix 4: all models scored with the benchmark's own metric code; reported next to the paper's tables as they come out,
  including where the scalar regressors beat the networks.
- Fix 5: cmp_tank.py against the dataset run, with the same agreement limits as the 6 November mesh check.
- Fix 6: liquid fraction vs the digitised Kamkari tilt curves, as the 4 November comparison.

## Amendment 1 (10 November, 06:30 UTC): mechanism found, test added

`diag_canon.py` on ood_mode (stored scores only): with the canonical frame alone, uniform-start discharge runs already
reach charge-level error (FNO 4.5 %, U-Net 4.2 % of dT), while pre-stratified ones fail (FNO 31.9 %, U-Net 23.8 %).
No parameter leaves the training range (except log_Re for 0.6 % of runs, by 0.18 sd), and the nearest-neighbour
distances of test and validation runs are alike. Cause: the frame mirrors the initial field (interface at 1 - y_i)
but not the input y_init, so pre-stratified discharge runs get contradictory inputs. The hybrid base carries the
right field and hides it (4.0 to 4.6 % for both start types). Test: train.py --canon-yi (diagnostic flag, off in every
released model) mirrors y_init too; fno and unet, ood_mode, 3 seeds (run_canonyi.sh, queued behind the ceiling jobs).
Prediction, written before the result: canon-yi brings the pre-stratified runs to near the uniform-start level.
The released checkpoints stay as they are; the paper reports the finding and the test.
