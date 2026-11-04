#!/bin/bash
# Install a Tailscale watchdog (systemd timer, every 5 min) on a ThermBench machine (pc3, pc4).
# Run once per machine:  sudo bash ~/thermbench/scripts/ts_watchdog_install.sh
# Check: Tailscale says this machine is online AND the lab PC or the laptop answers a tailscale
# ping. After 2 failed checks in a row (~10 min) it restarts tailscaled; simulations are not touched.
# Log: /var/log/ts_watchdog.log.  Remove: sudo systemctl disable --now ts-watchdog.timer
set -e
[ "$(id -u)" = 0 ] || { echo "run with sudo"; exit 1; }
cat > /usr/local/sbin/ts_watchdog.sh <<'W'
#!/bin/bash
F=/run/ts_watchdog.fails; LOG=/var/log/ts_watchdog.log
online=$(tailscale status --json 2>/dev/null | python3 -c 'import json,sys; print(json.load(sys.stdin)["Self"].get("Online", False))' 2>/dev/null)
peer=no
for h in labpc laptop; do
  timeout 20 tailscale ping -c 1 --timeout 8s $h > /dev/null 2>&1 && { peer=yes; break; }
done
if [ "$online" = True ] && [ $peer = yes ]; then echo 0 > $F; exit 0; fi
n=$(( $(cat $F 2>/dev/null || echo 0) + 1 )); echo $n > $F
echo "$(date -u '+%F %H:%M') check failed ($n): online=$online peer=$peer" >> $LOG
if [ $n -ge 2 ]; then
  systemctl restart tailscaled; sleep 20
  echo "$(date -u '+%F %H:%M') restarted tailscaled -> online=$(tailscale status --json 2>/dev/null | python3 -c 'import json,sys; print(json.load(sys.stdin)["Self"].get("Online"))' 2>/dev/null)" >> $LOG
  echo 0 > $F
fi
W
chmod 755 /usr/local/sbin/ts_watchdog.sh
cat > /etc/systemd/system/ts-watchdog.service <<'U'
[Unit]
Description=Restart tailscaled when this machine drops off the tailnet (ThermBench)
[Service]
Type=oneshot
ExecStart=/usr/local/sbin/ts_watchdog.sh
U
cat > /etc/systemd/system/ts-watchdog.timer <<'U'
[Unit]
Description=Tailscale watchdog every 5 min
[Timer]
OnBootSec=3min
OnUnitActiveSec=5min
[Install]
WantedBy=timers.target
U
systemctl daemon-reload
systemctl enable --now ts-watchdog.timer
systemctl start ts-watchdog.service
echo "watchdog installed on $(hostname): $(systemctl is-active ts-watchdog.timer), next run $(systemctl list-timers ts-watchdog.timer --no-legend | awk '{print $1, $2, $3}')"
