#!/bin/bash
# One-time setup of a new ThermalStorageBench machine (pc4), same as pc3: run INSIDE its Ubuntu 24.04 (WSL)
# window as user saxam:   bash pc4_setup.sh
# Installs: OpenFOAM v2606 (pinned to 2606.0~rc2-1, the lab/pc3 build, so results are identical),
# compiler, python3 numpy + h5py, OpenSSH server, Tailscale; enables systemd; adds the laptop's
# ssh key. The Tailscale login at the end opens a link that Saxam signs in to himself.
set -e
echo "== machine: $(nproc) threads, $(free -g | awk '/Mem/{print $2}') GB in WSL, $(df -h ~ | awk 'NR==2{print $4}') free; $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2)"
grep -q "systemd=true" /etc/wsl.conf 2>/dev/null || printf '[boot]\nsystemd=true\n\n[user]\ndefault=saxam\n' | sudo tee /etc/wsl.conf > /dev/null
sudo apt-get update
sudo apt-get install -y curl build-essential openssh-server python3-numpy python3-h5py
curl -fsSL https://dl.openfoam.com/add-debian-repo.sh | sudo bash
sudo apt-get install -y openfoam2606-default=2606.0~rc2-1 openfoam2606=2606.0~rc2-1 openfoam2606-common=2606.0~rc2-1 \
  openfoam2606-dev=2606.0~rc2-1 openfoam2606-tools=2606.0~rc2-1 openfoam2606-source=2606.0~rc2-1 openfoam2606-tutorials=2606.0~rc2-1
sudo apt-mark hold openfoam2606 openfoam2606-common openfoam2606-default openfoam2606-dev openfoam2606-tools openfoam2606-source openfoam2606-tutorials
curl -fsSL https://tailscale.com/install.sh | sh
mkdir -p ~/.ssh ~/thermbench/scripts ~/of_runs && chmod 700 ~/.ssh
K="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIK/Oy2iFZKu/LQQmq8MhGGFYnV4oTVw0MZKdTMZKZYfT saxam-laptop-thermbench"
grep -qF "$K" ~/.ssh/authorized_keys 2>/dev/null || echo "$K" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
echo "== OpenFOAM: $(dpkg -l openfoam2606-default | awk '/^ii/{print $3}')"
if systemctl is-system-running > /dev/null 2>&1 || [ "$(ps -p 1 -o comm=)" = systemd ]; then
  sudo systemctl enable --now ssh tailscaled
  echo "== now sign in to Tailscale with the link below (Saxam):"
  sudo tailscale up --hostname pc4 --ssh=false
  echo "== DONE. Tailscale address: $(tailscale ip -4)"
else
  echo "== systemd was just enabled: close this window, run 'wsl --shutdown' in Windows PowerShell,"
  echo "   reopen Ubuntu and run this script again (it skips what is already done)."
fi
