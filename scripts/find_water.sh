#!/bin/bash
unset LD_LIBRARY_PATH
T=/usr/lib/openfoam/openfoam2606/tutorials
ls -d $T 2>/dev/null || echo "no tutorials dir"
timeout 60 grep -rl --include=thermophysicalProperties* "rPolynomial" $T 2>/dev/null | head -5
python3 -c 'import numpy; print("numpy", numpy.__version__)' 2>&1
