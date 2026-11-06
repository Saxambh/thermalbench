#!/bin/bash
# Solver-convergence check of finished PCM cases (2026-11-06, after P0124: the GAMG p_rgh solve did not converge,
# residual ~0.85 every step, every solve at the 200-iteration cap; pcm_qc.py checks only the exported fields).
# Per finished case in <runs> (DONE, not a moved-away placeholder), from log.solver(.gz):
#   cap   share of p_rgh solves that stopped at the 200-iteration cap (p_rghFinal maxIter)
#   res   mean initial residual of the p_rgh solves
#   dt    mean time step (s)
# Healthy cases (10 checked on pc4): cap 0-0.2 %, res 0.003-0.025. Flags: FAIL cap > 20 % or res > 0.2;
# WARN cap > 2 % or res > 0.05. One line per case to stdout: case cap% res dt flag
#   pcm_solver_qc.sh <runs_dir> [jobs]      (runs at nice 15)
R=${1:?runs dir}; J=${2:-4}
cd "$R" || exit 1
one() {
  c=$1; f=$c/log.solver.gz; [ -f $f ] || f=$c/log.solver; [ -f $f ] || { echo "$c nolog"; return; }
  zcat -f $f | awk -v c=$c '
    /Solving for p_rgh/ { r=$0; sub(/.*Initial residual = /,"",r); sub(/,.*/,"",r); n++; s+=r; if ($NF+0 >= 200) m++ }
    /^deltaT = / { sd+=$3; k++ }
    END { if (!n) { print c, "nopressure"; exit }
          dt = k ? sd/k : 0
          cap = 100*m/n; res = s/n
          flag = (cap > 20 || res > 0.2) ? "FAIL" : (cap > 2 || res > 0.05) ? "WARN" : "ok"
          printf "%s %.2f %.4f %.4f %s\n", c, cap, res, dt, flag }'
}
export -f one
for c in P*/; do c=${c%/}; [ -f $c/DONE ] && ! ls $c/MOVED_TO_* > /dev/null 2>&1 && echo $c; done \
  | nice -n 15 xargs -P $J -I{} bash -c 'one {}'
