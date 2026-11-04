#!/bin/bash
B=~/of_runs/outletfix_smoke
sed -n '/outlet/,/}/p' $B/real_lam_A_dis/0/p_rgh $B/real_lam_A_dis/0/T
grep -o '"solver": "[a-zA-Z]*"' $B/bous_lam_A/case.json
