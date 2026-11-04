#!/bin/bash
D=~/of_runs/esi_develop; mkdir -p $D; cd $D
P="https://gitlab.com/api/v4/projects/openfoam%2Fcore%2Fopenfoam"
F="src%2FfvOptions%2Fsources%2Fderived%2FbuoyancyTurbSource"
curl -s -m 60 "$P" | python3 -c "import json,sys; d=json.load(sys.stdin); print('project:', d.get('path_with_namespace'), 'default:', d.get('default_branch'), 'last activity:', d.get('last_activity_at'), 'open issues:', d.get('open_issues_count'))"
curl -s -m 60 "$P/repository/branches?per_page=50" | python3 -c "import json,sys; print('branches:', [(b['name'], b['commit']['committed_date'][:10]) for b in json.load(sys.stdin)])"
for br in develop master; do
  curl -s -m 60 "$P/repository/commits?ref_name=$br&path=src/fvOptions/sources/derived/buoyancyTurbSource&per_page=10" | python3 -c "
import json,sys
for c in json.load(sys.stdin): print('   $br commit touching dir:', c['committed_date'][:10], c['title'][:90])"
  for f in buoyancyTurbSource.C buoyancyTurbSourceTemplates.C; do
    curl -s -m 60 -o gl_${br}_$f "$P/repository/files/$F%2F$f/raw?ref=$br"
    echo "   $br/$f: $(wc -c < gl_${br}_$f) bytes"
  done
  grep -n "eqn -=\|return beta_\|GbByK(" gl_${br}_buoyancyTurbSource.C gl_${br}_buoyancyTurbSourceTemplates.C | sed 's/^/      /'
done
echo "== issues mentioning buoyancyTurbSource"
curl -s -m 60 "$P/issues?search=buoyancyTurbSource&scope=all&state=all&per_page=50" | python3 -c "
import json,sys
d=json.load(sys.stdin)
print(d if isinstance(d, dict) else '')
for i in (d if isinstance(d, list) else []): print('  #', i['iid'], i['state'], i['created_at'][:10], i['title'][:100])"
