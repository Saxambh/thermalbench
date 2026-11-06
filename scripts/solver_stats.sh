#!/bin/bash
# Solver behaviour per verification run (2026-11-07): time steps, mean time step, p_rgh initial residual
# (all solves), largest Courant number, execution time. usage: solver_stats.sh <case_dir> ...
for c in "$@"; do f=$c/log.solver.gz; [ -f $f ] || f=$c/log.solver; [ -f $f ] || continue
  zcat -f $f | awk -v c=$(basename $c) '
    /^Time = /{n++} /^deltaT = /{dt+=$3; k++}
    /Solving for p_rgh/{r=$0; sub(/.*Initial residual = /,"",r); sub(/,.*/,"",r); s+=r; m++; it=$NF; its+=it}
    /^Courant Number mean/{co=$NF; if(co>cmax)cmax=co}
    /^ExecutionTime/{if($3<et)tot+=et; et=$3}
    END{printf "%-18s steps %7d  mean dt %.4f s  p_rgh: mean init. residual %.4f, mean iterations %.1f  max Co %.2f  exec %.0f s\n", c, n, (k?dt/k:0), (m?s/m:0), (m?its/m:0), cmax, tot+et}'
done
