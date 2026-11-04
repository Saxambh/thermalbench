#!/bin/bash
# Launch the coarse 3D test detached; stops itself after 15 min wall time (timing + stability).
S=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
setsid nohup timeout 900 bash $S/lou3d_test2.sh > ~/of_runs/lou3d_timing.log 2>&1 < /dev/null &
sleep 5; echo started
