#!/bin/bash
ssh labpc 'bash -s' <<'X'
grep MHz /proc/cpuinfo | awk '{s+=$4; n++} END {print "avg MHz seen by WSL:", s/n}'
nproc
cat /proc/meminfo | grep -E "MemTotal|MemAvailable"
top -bn1 | head -20 | tail -14
timeout 20 /mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -NoProfile -Command "(Get-CimInstance Win32_Processor).LoadPercentage; (Get-CimInstance Win32_Processor).CurrentClockSpeed; powercfg /getactivescheme; Get-Process | Sort-Object CPU -Descending | Select-Object -First 8 Name,CPU | Format-Table -AutoSize | Out-String" 2>&1 | head -30
X
