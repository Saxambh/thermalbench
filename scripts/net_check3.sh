#!/bin/bash
env -u LD_LIBRARY_PATH curl -sS -o /dev/null -w "openfoam %{http_code} %{remote_ip}\n" --max-time 15 https://dl.openfoam.com/add-debian-repo.sh
env -u LD_LIBRARY_PATH curl -sS -o /dev/null -w "ubuntu %{http_code} %{remote_ip}\n" --max-time 15 http://archive.ubuntu.com/ubuntu/dists/noble/Release
