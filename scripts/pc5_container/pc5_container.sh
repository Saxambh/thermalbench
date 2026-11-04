#!/bin/bash
# pc5: build the OpenFOAM container (once) and keep it running as "ofbox" with the home folder
# mounted at the same path, so ~/of_runs and ~/thermalbench work as on the other machines.
#   bash pc5_container.sh            build (if needed) + start; log ~/pc5_container.log
#   podman exec ofbox bash -lc '...' run a command inside
set -e
D="$(dirname "$(readlink -f "$0")")"
podman image exists localhost/thermbench-of || podman build -t localhost/thermbench-of "$D"
podman container exists ofbox || podman run -d --name ofbox --userns=keep-id --network host \
  -v "$HOME:$HOME" -e HOME="$HOME" -w "$HOME" localhost/thermbench-of sleep infinity
podman start ofbox > /dev/null
podman exec ofbox bash -c 'dpkg -l | awk "/openfoam2606/{print \$2, \$3}"; python3 -c "import numpy, h5py; print(\"numpy\", numpy.__version__, \"h5py\", h5py.__version__)"; id; nproc'
