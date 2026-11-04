#!/bin/bash
F=/usr/lib/openfoam/openfoam2606/src/fvOptions/sources/derived/buoyancyTurbSource/buoyancyTurbSource.C
sed -n '208,290p' $F
echo "--- depthCharge water thermo"
cat /usr/lib/openfoam/openfoam2606/tutorials/multiphase/compressibleInterFoam/laminar/depthCharge3D/constant/thermophysicalProperties.water | sed -n '15,60p'
