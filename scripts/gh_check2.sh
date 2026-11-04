#!/bin/bash
for r in olesenm/openfoam LostSunset/openfoam gratienj/openfoam petebachant/openfoam acxz/openfoam ZhangYanTJU/OpenFOAM-ESI pengyear/OpenFOAM-ESI sbryngelson/spuma WDRshadow/spuma SanjeevBashyal/OpenFOAM alpha-unito/OpenFOAM HenningScheufler/FormatFoam nalt1999/openFOAMSimulations; do
  curl -s -m 30 https://api.github.com/repos/$r | python3 -c "import json,sys; d=json.load(sys.stdin); print(f\"{d.get('full_name','$r'):40} pushed {str(d.get('pushed_at'))[:10]}  default {d.get('default_branch')}  {str(d.get('description'))[:70]}\")"
done
