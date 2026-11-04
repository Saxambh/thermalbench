#!/bin/bash
tail -n 15 ~/of_runs/p14_bctest/fix/log.solver
grep -E "startFrom|startTime" ~/of_runs/p14_bctest/fix/system/controlDict
