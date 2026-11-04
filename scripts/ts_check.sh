#!/bin/bash
unset LD_LIBRARY_PATH
tailscale status
echo "--- lab PC host key fingerprint (expect SHA256:QsS1/MlAGv021p0KF6XNEWzf1T5zTcYF/LZFO7O6w4s)"
ssh-keyscan -T 10 -t ed25519 labpc 2>/dev/null | ssh-keygen -lf -
