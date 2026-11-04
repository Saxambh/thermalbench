#!/bin/bash
ssh labpc 'bash -s' <<'R'
grep -h -A2 "outlet" ~/of_runs/fine128_h3mm/*/0/p_rgh | grep type | sort | uniq -c
grep -h -A2 "outlet" ~/of_runs/fine128_h3mm/*/0/T | grep type | sort | uniq -c
R
