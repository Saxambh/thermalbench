#!/bin/bash
# Install the `tbstat` command on the laptop (shows laptop + lab PC) and on the lab PC.
unset LD_LIBRARY_PATH
S=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
mkdir -p ~/bin ~/thermbench
cp $S/tbstat.py ~/thermbench/tbstat.py
cat > ~/bin/tbstat <<'EOF'
#!/bin/bash
# ThermBench progress on both machines. Live view: tbstat -w  (Ctrl+C to leave)
unset LD_LIBRARY_PATH
if [ "$1" = "-w" ]; then exec watch -n 30 -t "$0"; fi
python3 ~/thermbench/tbstat.py
echo
ssh -o ConnectTimeout=8 -o BatchMode=yes labpc 'python3 ~/thermbench/tbstat.py' 2>/dev/null \
  || echo "=== lab PC not reachable (Ubuntu window closed, PC asleep, or offline)"
EOF
chmod +x ~/bin/tbstat
grep -q 'HOME/bin' ~/.bashrc || echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
ssh labpc 'mkdir -p ~/thermbench' && scp -q $S/tbstat.py labpc:thermbench/tbstat.py
~/bin/tbstat
