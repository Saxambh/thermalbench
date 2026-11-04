#!/bin/bash
setsid nohup bash /mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench/lou3d_run.sh > /dev/null 2>&1 < /dev/null &
sleep 120
ps -eo pid,args | grep "[b]uoyantPimpleFoam -parallel" | wc -l
grep -E "cells|u_in" ~/of_runs/lou3d/sst/case.json; grep "^Time = " ~/of_runs/lou3d/sst/log.solver | tail -1
