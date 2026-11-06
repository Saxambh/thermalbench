#!/bin/bash
# Case 2 start (Saxam: "case 2 at 02:30" Nepal = 20:45 UTC): wait until then AND until pc7's tank mesh run has ended.
K="--material lauric --W 0.05 --H 0.12 --right wall --top wall --tw 70 --t0 25 --fin-len 0.025 --fin-t 0.004 --melt-range 43.5,48.2 --Cu 5e6 --end 12000 --write 300 --stop-at 0.995"
F3="--nfins 3 --fin-y 0.029,0.060,0.091 --fin-model conduct --k-fin 130"
until [ $(date -u +%s) -ge $(date -u -d "2026-11-06 20:45" +%s) ] && ! pgrep -f tank_continue.sh > /dev/null; do sleep 60; done
echo "$(date -u '+%F %H:%M') case 2 waiter: starting"
bash ~/thermbench_verify/val/val_run.sh kam_n3_h025_cu5e6 8 $K $F3 --h 0.00025
