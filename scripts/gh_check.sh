#!/bin/bash
D=~/of_runs/esi_develop; rm -rf $D; mkdir -p $D; cd $D
API=https://api.github.com/repos/openfoamdotcom/openfoam
curl -s -m 60 $API | python3 -c "import json,sys; d=json.load(sys.stdin); print('repo:', d.get('full_name'), 'default branch:', d.get('default_branch'), 'pushed_at:', d.get('pushed_at'), 'desc:', d.get('description'))"
curl -s -m 60 "$API/branches?per_page=100" | python3 -c "import json,sys; print('branches:', [b['name'] for b in json.load(sys.stdin)])"
for br in develop master; do
  curl -s -m 60 "$API/commits?sha=$br&per_page=1" | python3 -c "import json,sys; c=json.load(sys.stdin)[0]; print('$br head:', c['commit']['committer']['date'], c['commit']['message'].splitlines()[0][:80])" 2>&1
  curl -s -m 60 "$API/commits?sha=$br&path=src/fvOptions/sources/derived/buoyancyTurbSource&per_page=10" | python3 -c "
import json,sys
for c in json.load(sys.stdin): print('   $br buoyancyTurbSource commit:', c['commit']['committer']['date'][:10], c['commit']['message'].splitlines()[0][:90])" 2>&1
  for f in buoyancyTurbSource.C buoyancyTurbSourceTemplates.C; do
    curl -s -m 60 -o ${br}_$f https://raw.githubusercontent.com/openfoamdotcom/openfoam/$br/src/fvOptions/sources/derived/buoyancyTurbSource/$f
    diff <(grep -v '^ *$' ${br}_$f | grep -v Copyright) <(grep -v '^ *$' /usr/lib/openfoam/openfoam2606/src/fvOptions/sources/derived/buoyancyTurbSource/$f | grep -v Copyright) > /dev/null \
      && echo "   $br/$f: identical to installed v2606" || { echo "   $br/$f: DIFFERS from v2606"; diff <(grep -v '^ *$' ${br}_$f) <(grep -v '^ *$' /usr/lib/openfoam/openfoam2606/src/fvOptions/sources/derived/buoyancyTurbSource/$f) | head -20; }
  done
  grep -n "eqn -=\|return beta_\|GbByK(" ${br}_buoyancyTurbSource.C ${br}_buoyancyTurbSourceTemplates.C | sed 's/^/   /'
done
