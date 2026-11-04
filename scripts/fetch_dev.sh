#!/bin/bash
D=~/of_runs/esi_develop; rm -rf $D; mkdir -p $D; cd $D
U=https://develop.openfoam.com/Development/openfoam/-/raw/develop/src/fvOptions/sources/derived/buoyancyTurbSource
for f in buoyancyTurbSource.C buoyancyTurbSourceTemplates.C buoyancyTurbSource.H; do
  curl -s -m 60 -o $f "$U/$f"; echo "$f: $(wc -c < $f) bytes, $(head -c 60 $f | tr '\n' ' ')"
done
for f in buoyancyTurbSource.C buoyancyTurbSourceTemplates.C; do
  diff <(grep -v '^ *$' $f) <(grep -v '^ *$' /usr/lib/openfoam/openfoam2606/src/fvOptions/sources/derived/buoyancyTurbSource/$f) > /dev/null && echo "$f identical to v2606" || echo "$f DIFFERS from v2606"
done
grep -n "eqn -=\|return beta_\|GbByK(" buoyancyTurbSource.C buoyancyTurbSourceTemplates.C
curl -s -m 60 "https://develop.openfoam.com/api/v4/projects/Development%2Fopenfoam/repository/commits?ref_name=develop&path=src/fvOptions/sources/derived/buoyancyTurbSource&per_page=5" | python3 -c "import json,sys; [print(c['committed_date'][:10], c['title']) for c in json.load(sys.stdin)]" 2>&1 | head -6
curl -s -m 60 "https://develop.openfoam.com/api/v4/projects/Development%2Fopenfoam/issues?search=buoyancyTurbSource&scope=all&state=all&per_page=50" | python3 -c "import json,sys; [print(i['iid'], i['state'], i['created_at'][:10], i['title']) for i in json.load(sys.stdin)]" 2>&1 | head -20
