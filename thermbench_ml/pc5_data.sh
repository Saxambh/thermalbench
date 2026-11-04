#!/bin/bash
# Bring pc5's training data up to date through GitHub (pc5 reaches our machines only through a slow
# Tailscale relay, ~0.3 MB/s; GitHub runs at ~4 MB/s both ways). Run in WSL on the laptop.
#   bash pc5_data.sh <manifest>          (tank manifest or PCM manifest_pcm.json)
# 1 make_slim.py: temperature-only copies of the manifest's runs into ~/tb_slim (new ones only)
# 2 commit + push ~/tb_slim to the private repo Saxambh/thermalbench-data (one commit < 2 GB)
# 3 pc5: git pull with the laptop's forwarded GitHub key (no key stored on pc5), hard-link into
#   ~/tb_data, check_data.py against the manifest
set -e
MAN=$(readlink -f "${1:?manifest}")
ML="$(dirname "$(readlink -f "$0")")"
unset LD_LIBRARY_PATH
nice -n 10 ~/venvs/tbml-gpu/bin/python "$ML/make_slim.py" "$MAN"
cd ~/tb_slim
git config core.bigFileThreshold 1m; git config pack.window 0; git config pack.compression 0
git add -A
git diff --cached --quiet || git commit -q -m "data: $(basename "$MAN") $(date -u '+%F %H:%M') UTC"
nice -n 10 git push -q origin main
echo "pushed $(git log --oneline -1)"
scp -q "$MAN" pc5:/tmp/pc5_data_manifest.json
eval $(ssh-agent -s) > /dev/null; ssh-add -q ~/.ssh/id_ed25519_github
ssh -A -o BatchMode=yes pc5 'set -e; export GIT_SSH_COMMAND="ssh -o IdentitiesOnly=no -o IdentityFile=/dev/null"
  cd ~/thermalbench-data && git pull -q --ff-only && git log --oneline -1
  for o in */; do o=${o%/}; rsync -a --link-dest=$HOME/thermalbench-data/ ~/thermalbench-data/$o ~/tb_data/; done   # every origin (tank: lab laptop pc3; PCM also pc4 pc5)
  cd ~/thermalbench/thermbench_ml && python3 check_data.py /tmp/pc5_data_manifest.json' < /dev/null
ssh-agent -k > /dev/null
