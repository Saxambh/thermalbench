#!/bin/bash
unset LD_LIBRARY_PATH
R=/usr/lib/openfoam/openfoam2606
ls -d $R || exit 1
source $R/etc/bashrc
echo "WM_PROJECT_VERSION=$WM_PROJECT_VERSION compiler=$WM_COMPILER  $(gcc --version | head -1)"
command -v buoyantBoussinesqPimpleFoam buoyantPimpleFoam foamRun 2>/dev/null
echo "--- buoyancyTurbSource source files"
find $R/src -ipath "*buoyancyTurbSource*" 2>/dev/null | head
echo "--- RAS models"
ls $R/src/TurbulenceModels/turbulenceModels/RAS/ 2>/dev/null | tr '\n' ' '
echo
echo "--- tutorials using buoyancyTurbSource"
grep -rl buoyancyTurbSource $FOAM_TUTORIALS 2>/dev/null | head
