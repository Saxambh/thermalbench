#!/bin/bash
echo "--- resolv.conf"; cat /etc/resolv.conf
echo "--- wsl.conf"; cat /etc/wsl.conf 2>/dev/null
echo "--- resolve archive.ubuntu.com"; getent hosts archive.ubuntu.com || echo FAIL
echo "--- resolve dl.openfoam.com"; getent hosts dl.openfoam.com || echo FAIL
echo "--- ping 8.8.8.8"; ping -c 2 -W 2 8.8.8.8 2>&1 | tail -2
echo "--- openfoam repo file"; ls /etc/apt/sources.list.d/ 2>/dev/null
