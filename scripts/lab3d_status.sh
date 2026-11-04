#!/bin/bash
unset LD_LIBRARY_PATH
S=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
scp -q $S/lou3d_status.sh labpc:thermbench/scripts/
ssh -o BatchMode=yes labpc 'bash ~/thermbench/scripts/lou3d_status.sh ~/of_runs/lou3d/sst_finelow'
