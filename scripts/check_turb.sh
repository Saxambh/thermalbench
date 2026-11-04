#!/bin/bash
source /opt/OpenFOAM/OpenFOAM-v2012/etc/bashrc WM_COMPILER=Gcc63
cd $FOAM_SRC
echo "--- buoyancyTurbSource fvOption present?"
grep -rl "buoyancyTurbSource" . 2>/dev/null | head -5
echo "--- buoyantKEpsilon model:"
find . -iname "*buoyantKEpsilon*" | head -5
echo "--- RAS models compiled for incompressible:"
ls TurbulenceModels/turbulenceModels/RAS/ | tr '\n' ' '
echo; echo "--- liquid equations of state (rPolynomial/icoPolynomial):"
find thermophysicalModels/specie/equationOfState -maxdepth 1 -type d | xargs -n1 basename | tr '\n' ' '
echo; echo "--- buoyantPimpleFoam water tutorials:"
grep -rl "rPolynomial\|icoPolynomial" $FOAM_TUTORIALS/heatTransfer 2>/dev/null | head -5
