#!/bin/bash
# Stop the 5 mm batch on both machines and keep the nOuterCorrectors=1 results as full_h5mm_n1.
pkill -f run_batch.py; pkill -f buoyantPimpleFoam; pkill -f ml_early.sh; pkill -f train.py; sleep 5
echo "laptop left: $(pgrep -fc 'buoyantPimpleFoam|run_batch.py')"
mv ~/of_runs/full_h5mm ~/of_runs/full_h5mm_n1 && echo "laptop DONE kept: $(ls ~/of_runs/full_h5mm_n1/*/thermbench.h5 | wc -l)"
ssh labpc 'bash -s' <<'X'
pkill -u saxam -f run_batch.py; pkill -u saxam -f buoyantPimpleFoam; sleep 5
echo "lab left: $(pgrep -u saxam -fc 'buoyantPimpleFoam|run_batch.py')"
mv ~/of_runs/full_h5mm ~/of_runs/full_h5mm_n1 && echo "lab DONE kept: $(ls ~/of_runs/full_h5mm_n1/*/thermbench.h5 | wc -l)"
X
