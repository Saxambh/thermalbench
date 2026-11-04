#!/bin/bash
ls -l /etc/resolv.conf
systemctl is-active systemd-resolved
resolvectl status 2>&1 | head -30
echo "--- direct query to 8.8.8.8"
getent hosts archive.ubuntu.com
command -v nslookup && nslookup archive.ubuntu.com 8.8.8.8 | tail -4
command -v dig && dig +short @8.8.8.8 archive.ubuntu.com
