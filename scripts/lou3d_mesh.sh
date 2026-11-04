#!/bin/bash
unset LD_LIBRARY_PATH
source /usr/lib/openfoam/openfoam2606/etc/bashrc
S=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
C=~/of_runs/lou3d/sst; rm -rf $C
nice -n 5 python3 $S/make_lou3d.py $C --turb kOmegaSST 2>&1 | tail -30
grep -E "cells:|faces:|Max non-orth|Max skew|Mesh OK|Failed|\*\*\*" $C/log.checkMesh | head -20
foamDictionary $C/constant/polyMesh/boundary -keywords 2>/dev/null
grep -A3 -E "^ +(inlet|outlet|baffle|walls|top|bottom|symX|symZ)$" $C/constant/polyMesh/boundary | grep -E "^ +[a-zA-Z]+$|nFaces"; ls $C/0
