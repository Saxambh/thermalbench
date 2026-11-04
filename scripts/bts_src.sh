#!/bin/bash
D=$(find /usr/lib/openfoam/openfoam2606/src -type d -name buoyancyTurbSource | head -1)
echo "DIR $D"; ls $D
sed -n '1,140p' $D/buoyancyTurbSource.H | grep -v "^ *$" | sed -n '/Description/,/SourceFiles/p'
echo "======== Templates"
cat $D/buoyancyTurbSourceTemplates.C | sed -n '/buoyancyTurbSource::/,$p' | grep -v "^ *$" | head -150
