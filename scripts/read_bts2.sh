#!/bin/bash
D=/usr/lib/openfoam/openfoam2606/src/fvOptions/sources/derived/buoyancyTurbSource
echo "=== buoyancyTurbSource.C lines 40-130"
sed -n '40,130p' $D/buoyancyTurbSource.C
echo "=== constructor (g_, beta_) lines 130-180"
sed -n '130,180p' $D/buoyancyTurbSource.C
echo "=== header description"
sed -n '28,120p' $D/buoyancyTurbSource.H
echo "=== semiImplicitSource addSup (sign convention reference)"
grep -n "eqn +=\|eqn -=" /usr/lib/openfoam/openfoam2606/src/fvOptions/sources/general/semiImplicitSource/*.C | head
echo "=== kOmegaSST k equation"
grep -n -A12 "tmp<fvScalarMatrix> kEqn" /usr/lib/openfoam/openfoam2606/src/TurbulenceModels/turbulenceModels/Base/kOmegaSST/kOmegaSSTBase.C | head -20
