#!/bin/bash
# Copy mesh-only copies of three cases to the Windows scratchpad for ParaView (running cases untouched)
V=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/viz
rm -rf $V; mkdir -p $V
cp_case() { mkdir -p $V/$2/constant $V/$2/system
  cp -r $1/constant/polyMesh $V/$2/constant/
  cp $1/system/controlDict $1/system/fvSchemes $1/system/fvSolution $V/$2/system/
  touch $V/$2/$2.foam
  grep -E '"(inlet_type|mode|W_m|H_m|nx|ny)"' $1/case.json 2>/dev/null | tr -d ' \n'; echo " -> $2"; }
cp_case ~/of_runs/full_h5mm/T0238_lam tankA
cp_case ~/of_runs/full_h5mm/T0921_lam tankB
cp_case ~/of_runs/lou3d/sst lou3d
grep -E '^\s*[a-zA-Z]+$' -A3 ~/of_runs/lou3d/sst/constant/polyMesh/boundary | grep -E '^\s*[a-zA-Z]+$|nFaces' | paste - -
du -sh $V/*
