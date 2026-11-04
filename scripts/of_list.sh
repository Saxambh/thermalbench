#!/bin/bash
echo "--- OpenFOAM lines in ~/.bashrc"; grep -n -i "openfoam\|of2012" ~/.bashrc
echo "--- available packages"; env -u LD_LIBRARY_PATH apt-cache search openfoam | grep default
