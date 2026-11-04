#!/bin/bash
D=/usr/lib/openfoam/openfoam2606/src/fvOptions/sources/derived/buoyancyTurbSource
grep -v "^ *$" $D/buoyancyTurbSource.C | sed -n '/^Foam::fv::buoyancyTurbSource::buoyancyTurbSource/,$p'
grep -n "g_\|meshObjects" $D/buoyancyTurbSource.H
