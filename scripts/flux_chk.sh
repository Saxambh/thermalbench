#!/bin/bash
cd ~/of_runs/flux_test/c
grep -A4 "FOAM FATAL\|FOAM Warning" log.solver | head -12
for f in outletFlux outletHflux; do head -5 postProcessing/$f/0/surfaceFieldValue.dat | grep "#"; tail -n 2 postProcessing/$f/0/surfaceFieldValue.dat; done
tail -n 3 log.solver
