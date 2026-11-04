#!/bin/bash
echo "solvers running: $(pgrep -fc buoyantPimpleFoam)"
S=~/of_runs/pilot_h5mm/batch_status.csv
echo "finished (DONE marker): $(ls ~/of_runs/pilot_h5mm/*/DONE 2>/dev/null | wc -l) of 24"
echo "status file (lags: the pilot's runner reports in list order):"
grep -v "generator_failed\|^run_id" $S
for c in ~/of_runs/pilot_h5mm/P*/; do [ -f $c/DONE ] && echo "  done: $(basename $c)"; done
for c in ~/of_runs/pilot_h5mm/P*/; do
  [ -f $c/DONE ] && continue
  [ -f $c/log.solver ] || continue
  t=$(grep "^Time =" $c/log.solver | tail -1 | awk '{print $3}')
  e=$(python3 -c "import json; print(json.load(open('$c/case.json'))['end_time_s'])" 2>/dev/null)
  printf "  %-10s t=%8.1f / %8.1f s\n" $(basename $c) ${t:-0} ${e:-0}
done
