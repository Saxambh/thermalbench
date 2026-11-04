#!/bin/bash
# Start the ThermalStorageBench dashboard on the laptop (safe to rerun): collector + local web server.
# Open http://localhost:8765 in the browser on the laptop. Read-only; stops nothing.
S="$(dirname "$(readlink -f "$0")")"
mkdir -p ~/tb_dash && cp "$S/tb_dash.html" ~/tb_dash/index.html
pgrep -f "tb_dash_collect.py" > /dev/null || (setsid nohup python3 "$S/tb_dash_collect.py" >> ~/tb_dash/collect.log 2>&1 < /dev/null &)
pgrep -f "http.server 8765" > /dev/null || (cd ~/tb_dash && setsid nohup python3 -m http.server 8765 --bind 127.0.0.1 >> ~/tb_dash/server.log 2>&1 < /dev/null &)
sleep 3
echo "dashboard: http://localhost:8765  (collector $(pgrep -f tb_dash_collect.py | head -1), server $(pgrep -f 'http.server 8765' | head -1))"
