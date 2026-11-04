#!/bin/bash
for v in n1 n2 n3; do echo "$v $(grep ExecutionTime ~/of_runs/nouter_test/$v/log.solver | tail -1) steps $(grep -c '^Time = ' ~/of_runs/nouter_test/$v/log.solver)"; done
