#!/bin/bash
unset LD_LIBRARY_PATH
mkdir -p ~/.ssh && chmod 700 ~/.ssh
grep -q "^labpc " ~/.ssh/known_hosts 2>/dev/null || ssh-keyscan -T 10 -t ed25519 labpc 2>/dev/null >> ~/.ssh/known_hosts
grep -q "^Host labpc" ~/.ssh/config 2>/dev/null || cat >> ~/.ssh/config <<'EOF'
Host labpc
    HostName labpc
    User saxam
    IdentityFile ~/.ssh/id_ed25519
    ServerAliveInterval 30
    ServerAliveCountMax 6
EOF
chmod 600 ~/.ssh/config
ssh -o BatchMode=yes labpc 'echo "connected as $(whoami) on $(hostname)"; nproc; free -g | head -2; df -h ~ | tail -1; unset LD_LIBRARY_PATH; source /usr/lib/openfoam/openfoam2606/etc/bashrc && echo "OpenFOAM $WM_PROJECT_VERSION"; command -v python3; cat /proc/loadavg'
