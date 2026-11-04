#!/bin/bash
P="https://gitlab.com/api/v4/projects/openfoam%2Fcore%2Fopenfoam"
for i in 2293 3131; do
  echo "=== #$i"
  curl -s -m 60 "$P/issues/$i" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['title']); print(d['description'][:1500])"
  curl -s -m 60 "$P/issues/$i/notes?per_page=50&sort=asc" | python3 -c "
import json,sys
for n in json.load(sys.stdin):
    if not n.get('system'): print('--- note', n['created_at'][:10], ':', n['body'][:600].replace(chr(10),' '))"
done
echo "=== other searches"
for q in "buoyancy%20turbulence%20sign" "buoyancy%20source%20k%20sign" "stable%20stratification%20turbulence" "buoyantBoussinesqPimpleFoam%20kOmegaSST"; do
  curl -s -m 60 "$P/issues?search=$q&scope=all&state=all&per_page=20" | python3 -c "
import json,sys
for i in json.load(sys.stdin): print('  [$q] #', i['iid'], i['state'], i['created_at'][:10], i['title'][:100])"
done
