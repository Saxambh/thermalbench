#!/bin/bash
for p in $(ps -eo pid,args | grep "[b]uoyantPimpleFoam -parallel" | awk '{print $1}'); do kill $p; done
sleep 3
ps -eo pid,args | grep "[b]uoyantPimpleFoam -parallel" | wc -l
ps -eo pid,args | grep "[b]uoyantPimpleFoam" | wc -l
