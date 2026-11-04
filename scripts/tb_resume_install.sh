#!/bin/bash
# Install the boot-time resume service on a ThermBench machine (run as root, once per machine):
#   inside Ubuntu:       sudo bash ~/thermbench/scripts/tb_resume_install.sh <laptop|lab|pc3|pc4>
#   from PowerShell:     wsl -d <distro> -u root bash /home/saxam/thermbench/scripts/tb_resume_install.sh <machine>
# 60 s after Ubuntu starts, runs tb_resume.sh <machine> as saxam (log ~saxam/tb_resume.log).
# Also makes sure the SSH server starts at boot. Remove: systemctl disable tb-resume.service
set -e
M=${1:?machine: laptop, lab, pc3 or pc4}
[ "$(id -u)" = 0 ] || { echo "run as root (sudo)"; exit 1; }
cat > /etc/systemd/system/tb-resume.service <<U
[Unit]
Description=Resume unfinished ThermBench simulations after a reboot ($M)
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=saxam
ExecStartPre=/bin/sleep 60
ExecStart=/bin/bash /home/saxam/thermbench/scripts/tb_resume.sh $M
RemainAfterExit=yes
KillMode=process

[Install]
WantedBy=multi-user.target
U
systemctl daemon-reload
systemctl enable tb-resume.service
if systemctl list-unit-files ssh.service > /dev/null 2>&1; then
  systemctl is-enabled ssh.service > /dev/null 2>&1 || systemctl is-enabled ssh.socket > /dev/null 2>&1 || systemctl enable ssh.service
fi
echo "tb-resume installed on $(hostname) for '$M': $(systemctl is-enabled tb-resume.service); ssh at boot: service $(systemctl is-enabled ssh.service 2>&1), socket $(systemctl is-enabled ssh.socket 2>&1); tailscaled $(systemctl is-enabled tailscaled 2>&1)"
