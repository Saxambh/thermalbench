#!/bin/bash
ps -eo pid,args | grep "[b]uoyantPimpleFoam -parallel" | wc -l
ps -eo pid,args | grep "[b]uoyantPimpleFoam" | wc -l
