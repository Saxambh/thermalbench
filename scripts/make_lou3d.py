#!/usr/bin/env python3
"""3D validation case: Lou et al. (2023) J. Energy Storage 71:108017, uniform orifice baffles,
Qin = 1 L/min, Th = 60 C into Tc = 20 C. Same physics as the ThermalStorageBench production runs
(real water properties, buoyantPimpleFoam, GAMG, 2 outer correctors, fixedMean outlet).

Quarter domain (symmetry planes x = 0 and z = 0, tank axis on the y axis, y up, bottom y = 0):
  tank 194 x 194 x 390 mm; bottom manifold 0-33, bottom baffle 33-39, storage 39-351,
  upper baffle 351-357, upper manifold 357-390 mm; 10 mm ports centred in lid and bottom.
  Baffles: 37 orifices of radius 8.05 mm (porosity 0.20), layout from Lou Fig. 6a.
Mesh: hex blockMesh (2.4 mm), refined x2 around the upper manifold/baffle and the central
jet, x4 at the inlet port; baffle cells removed (staircase holes, radius tuned so the
open area equals the true 20 %); inlet/outlet discs cut from the lid/bottom faces.
Baffles are adiabatic walls (Lou modelled 0.2 W/m/K polycarbonate conduction).

Usage (OpenFOAM environment loaded): make_lou3d.py <case> [--turb kOmegaSST|laminar]
       [--end 750] [--maxCo 1] ; then run buoyantPimpleFoam (in parallel: decomposePar).
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_tank_case as gen  # noqa: E402  (water polynomials, header writer)

W2, H = 0.097, 0.390                     # half width, height (m)
YB = [0.0, 0.033, 0.039, 0.351, 0.357, 0.390]
NY = [10, 2, 96, 2, 10]                  # cells per y segment (plates are exactly 2 cells)
NXZ = 30                                 # base cells across the half width (3.23 mm);
                                         # 40 (2.4 mm) gave 549k cells and ~26 days to 750 s
R_HOLE, D_PORT, Q = 8.05e-3, 10e-3, 1.0e-3 / 60
TH, TC = 333.15, 293.15
# hole centres in one eighth (Lou Fig. 6a), mm
EIGHTH = [(0, 0), (34.3, 0), (72.8, 0), (24.25, 24.25), (48.5, 48.5), (72.76, 72.76),
          (58.55, 24.25), (82.8, 48.5)]


def all_holes():
    """37 hole centres (m) by the square's 8-fold symmetry."""
    pts = set()
    for x, z in EIGHTH:
        for a, b in ((x, z), (z, x)):
            for sa in (1, -1):
                for sb in (1, -1):
                    pts.add((round(sa * a, 3), round(sb * b, 3)))
    assert len(pts) == 37, len(pts)
    return [(x / 1000, z / 1000) for x, z in sorted(pts)]


def sh(cmd, case, log):
    with open(os.path.join(case, log), "w") as f:
        r = subprocess.run(cmd, cwd=case, shell=True, stdout=f, stderr=subprocess.STDOUT)
    if r.returncode:
        sys.exit(f"{cmd} failed, see {case}/{log}")


def wr(case, rel, cls, obj, body):
    gen.write(os.path.join(case, rel), cls, obj, body)


def staircase_radius(h):
    """Hole radius whose cell-centre staircase on spacing h gives the true open area."""
    holes = all_holes()
    xs = (np.arange(int(round(W2 / h))) + 0.5) * h
    X, Z = np.meshgrid(xs, xs)
    target = 0.25 * len(holes) * math.pi * R_HOLE ** 2       # quarter of the full open area

    def area(r):
        inside = np.zeros_like(X, bool)
        for hx, hz in holes:
            inside |= (X - hx) ** 2 + (Z - hz) ** 2 < r ** 2
        return inside.sum() * h * h

    lo, hi = 0.8 * R_HOLE, 1.2 * R_HOLE
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if area(mid) < target else (lo, mid)
    return 0.5 * (lo + hi), area(0.5 * (lo + hi)) / target


def mesh(case, fine_lower=False):
    v = [f"({x} {y} {z})" for y in YB for z in (0, W2) for x in (0, W2)]
    # vertex index: 4*j + 2*kz + ix
    vi = lambda j, ix, kz: 4 * j + 2 * kz + ix
    blocks, sides = [], {"symX": [], "symZ": [], "walls": [], "bottom": [], "top": []}
    for j, n in enumerate(NY):
        b = [vi(j, 0, 0), vi(j, 1, 0), vi(j + 1, 1, 0), vi(j + 1, 0, 0),
             vi(j, 0, 1), vi(j, 1, 1), vi(j + 1, 1, 1), vi(j + 1, 0, 1)]
        blocks.append(f"    hex ({' '.join(map(str, b))}) ({NXZ} {n} {NXZ}) simpleGrading (1 1 1)")
        q = lambda *p: "(" + " ".join(str(vi(*t)) for t in p) + ")"
        sides["symX"].append(q((j, 0, 0), (j, 0, 1), (j + 1, 0, 1), (j + 1, 0, 0)))
        sides["symZ"].append(q((j, 0, 0), (j + 1, 0, 0), (j + 1, 1, 0), (j, 1, 0)))
        sides["walls"].append(q((j, 1, 0), (j + 1, 1, 0), (j + 1, 1, 1), (j, 1, 1)))
        sides["walls"].append(q((j, 0, 1), (j, 1, 1), (j + 1, 1, 1), (j + 1, 0, 1)))
    sides["bottom"].append(q((0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1)))
    J = len(NY)
    sides["top"].append(q((J, 0, 0), (J, 0, 1), (J, 1, 1), (J, 1, 0)))
    types = {"symX": "symmetryPlane", "symZ": "symmetryPlane", "walls": "wall",
             "bottom": "wall", "top": "wall"}
    pats = "\n".join(f"    {n}\n    {{\n        type {types[n]};\n        faces\n        (\n"
                     + "\n".join(f"            {f}" for f in fs) + "\n        );\n    }"
                     for n, fs in sides.items())
    pats += "\n    baffle\n    {\n        type wall;\n        faces ();\n    }"
    wr(case, "system/blockMeshDict", "dictionary", "blockMeshDict",
       "convertToMeters 1;\n\nvertices\n(\n" + "\n".join(f"    {p}" for p in v) + "\n);\n\nblocks\n(\n"
       + "\n".join(blocks) + "\n);\n\nedges ();\n\nboundary\n(\n" + pats + "\n);\n")
    sh("blockMesh", case, "log.blockMesh")

    wr(case, "system/refineMeshDict", "dictionary", "refineMeshDict",
       "set r;\ncoordinateSystem global;\nglobalCoeffs\n{\n    tan1 (1 0 0);\n    tan2 (0 0 1);\n}\n"
       "directions (tan1 tan2 normal);\nuseHexTopology true;\ngeometricCut false;\nwriteMesh false;\n")
    # level 1: upper manifold + baffle + 16 mm below it, and the central jet column
    # level 2: around the inlet port
    # level 1 + 2 also around the outlet port (3 coarse faces made the outlet unstable)
    # --fine-lower: level 1 also over the lower manifold + baffle + 16 mm above it (mirror of the top)
    lower = [((0, -1, 0), (1, 0.055, 1))] if fine_lower else []
    for lvl, boxes in ((1, [((0, 0.335, 0), (1, 1, 1)), ((0, 0.15, 0), (0.025, 0.335, 0.025)),
                            ((0, -1, 0), (0.012, 0.008, 0.012))] + lower),
                       (2, [((0, 0.378, 0), (0.009, 1, 0.009)), ((0, -1, 0), (0.009, 0.004, 0.009))])):
        acts = "\n".join(f"    {{ name r; type cellSet; action {'new' if i == 0 else 'add'}; source boxToCell;"
                         f" box ({a[0]} {a[1]} {a[2]}) ({b[0]} {b[1]} {b[2]}); }}" for i, (a, b) in enumerate(boxes))
        wr(case, "system/topoSetDict.r", "dictionary", "topoSetDict", f"actions\n(\n{acts}\n);\n")
        sh("topoSet -dict system/topoSetDict.r", case, f"log.topoSet.r{lvl}")
        sh("refineMesh -dict system/refineMeshDict -overwrite", case, f"log.refineMesh{lvl}")

    # remove baffle solid: plates minus holes; staircase radius per plate resolution
    h_up = W2 / NXZ / 2
    h_lo = h_up if fine_lower else W2 / NXZ
    r_up, a_up = staircase_radius(h_up)
    r_lo, a_lo = staircase_radius(h_lo)
    acts = []
    for name, (y0, y1), r in (("up", (0.351, 0.357), r_up), ("lo", (0.033, 0.039), r_lo)):
        acts.append(f"    {{ name solid_{name}; type cellSet; action new; source boxToCell; box (0 {y0} 0) (1 {y1} 1); }}")
        for hx, hz in all_holes():
            if hx > -r and hz > -r:
                acts.append(f"    {{ name solid_{name}; type cellSet; action subtract; source cylinderToCell;"
                            f" p1 ({hx} {y0 - 0.001} {hz}); p2 ({hx} {y1 + 0.001} {hz}); radius {r:.6g}; }}")
    acts.append("    { name fluid; type cellSet; action new; source cellToCell; sets (solid_up solid_lo); }")
    acts.append("    { name fluid; type cellSet; action invert; }")
    wr(case, "system/topoSetDict.solid", "dictionary", "topoSetDict", "actions\n(\n" + "\n".join(acts) + "\n);\n")
    sh("topoSet -dict system/topoSetDict.solid", case, "log.topoSet.solid")
    sh("subsetMesh fluid -patch baffle -overwrite", case, "log.subsetMesh")
    subprocess.run(["rm", "-rf", os.path.join(case, "0", "polyMesh")])   # subsetMesh cellMap only

    # ports: discs of diameter 10 mm on the lid (inlet) and the bottom (outlet)
    acts = []
    for name, patch, y in (("inletF", "top", H), ("outletF", "bottom", 0.0)):
        acts.append(f"    {{ name {name}; type faceSet; action new; source patchToFace; patch {patch}; }}")
        acts.append(f"    {{ name {name}; type faceSet; action subset; source cylinderToFace;"
                    f" p1 (0 {y - 0.001} 0); p2 (0 {y + 0.001} 0); radius {D_PORT / 2}; }}")
    wr(case, "system/topoSetDict.ports", "dictionary", "topoSetDict", "actions\n(\n" + "\n".join(acts) + "\n);\n")
    sh("topoSet -dict system/topoSetDict.ports", case, "log.topoSet.ports")
    wr(case, "system/createPatchDict", "dictionary", "createPatchDict",
       "pointSync false;\n\npatches\n(\n"
       "    { name inlet; patchInfo { type patch; } constructFrom set; set inletF; }\n"
       "    { name outlet; patchInfo { type patch; } constructFrom set; set outletF; }\n);\n")
    sh("createPatch -overwrite", case, "log.createPatch")
    sh("checkMesh", case, "log.checkMesh")
    return {"hole_radius_upper_m": r_up, "open_area_ratio_upper": a_up,
            "hole_radius_lower_m": r_lo, "open_area_ratio_lower": a_lo}


def port_area(case, patch, h):
    """Area of a port patch: its faces are all squares of side h (one refinement level)."""
    b = open(os.path.join(case, "constant/polyMesh/boundary")).read()
    n = int(re.search(r"\b" + patch + r"\s*\{[^}]*?nFaces\s+(\d+);", b).group(1))
    return n * h * h, n


def fields(case, a, u_in):
    real_p = gen.P0
    turb = a.turb != "laminar"
    bc = lambda d: "\n".join(f"    {p}\n    {{\n{b}\n    }}" for p, b in d.items())

    def fld(cls, obj, dim, internal, d):
        d = dict(d)
        d['"sym.*"'] = "        type            symmetryPlane;"
        gen.write(os.path.join(case, "0", obj), cls, obj,
                  f"dimensions      {dim};\n\ninternalField   {internal};\n\nboundaryField\n{{\n{bc(d)}\n}}\n")

    walls = '"(walls|top|bottom|baffle)"'
    ffp = f"        type            fixedFluxPressure;\n        value           uniform {real_p};"
    fld("volVectorField", "U", "[0 1 -1 0 0 0 0]", "uniform (0 0 0)", {
        "inlet": f"        type            fixedValue;\n        value           uniform (0 {-u_in:.6g} 0);",
        "outlet": "        type            pressureInletOutletVelocity;\n        value           uniform (0 0 0);",
        walls: "        type            noSlip;"})
    fld("volScalarField", "T", "[0 0 0 1 0 0 0]", f"uniform {TC}", {
        "inlet": f"        type            fixedValue;\n        value           uniform {TH};",
        "outlet": "        type            zeroGradient;", walls: "        type            zeroGradient;"})
    fld("volScalarField", "p_rgh", "[1 -1 -2 0 0 0 0]", f"uniform {real_p}", {
        "inlet": ffp, walls: ffp,
        # horizontal outlet: all faces at one height, so a uniform p_rgh is exact here
        # (fixedMean, needed for the 2D side-wall slots, let the 3 coarse faces of an
        # earlier mesh drive an in/out flow that grew to 31 m/s within 4 steps)
        "outlet": f"        type            fixedValue;\n        value           uniform {real_p};"})
    calcp = f"        type            calculated;\n        value           uniform {real_p};"
    fld("volScalarField", "p", "[1 -1 -2 0 0 0 0]", f"uniform {real_p}",
        {"inlet": calcp, "outlet": calcp, walls: calcp})
    calc0 = "        type            calculated;\n        value           uniform 0;"
    aw = ("        type            compressible::alphatJayatillekeWallFunction;\n        Prt             0.85;\n"
          "        value           uniform 0;") if turb else calc0
    fld("volScalarField", "alphat", "[1 -1 -1 0 0 0 0]", "uniform 0", {"inlet": calc0, "outlet": calc0, walls: aw})
    if turb:
        k_in = 1.5 * (0.05 * u_in) ** 2
        om_in = k_in ** 0.5 / (0.09 ** 0.25 * 0.07 * D_PORT)
        k0, om0 = 1e-8, 1e-2                     # quiescent tank
        io = lambda v: f"        type            inletOutlet;\n        inletValue      uniform {v:.4g};\n        value           uniform {v:.4g};"
        fld("volScalarField", "k", "[0 2 -2 0 0 0 0]", f"uniform {k0}", {
            "inlet": f"        type            fixedValue;\n        value           uniform {k_in:.4g};",
            "outlet": io(k0), walls: f"        type            kqRWallFunction;\n        value           uniform {k0};"})
        fld("volScalarField", "omega", "[0 0 -1 0 0 0 0]", f"uniform {om0}", {
            "inlet": f"        type            fixedValue;\n        value           uniform {om_in:.4g};",
            "outlet": io(om0), walls: f"        type            omegaWallFunction;\n        value           uniform {om0};"})
        fld("volScalarField", "nut", "[0 2 -1 0 0 0 0]", "uniform 0", {
            "inlet": calc0, "outlet": calc0, walls: "        type            nutkWallFunction;\n        value           uniform 0;"})


def setup(case, a, u_in):
    wr(case, "constant/g", "uniformDimensionedVectorField", "g",
       "dimensions      [0 1 -2 0 0 0 0];\nvalue           (0 -9.81 0);\n")
    # dpdt off: with rho = rho(T) the start-up pressure jump over tiny time steps acts as a
    # spurious heat source near the outlet and blew the 3D case up within 5 steps (lou3d_variants.sh);
    # physically negligible for liquid water (1 kPa -> 2e-4 K), and identical results in 2D (dpdt_test.sh)
    wr(case, "constant/thermophysicalProperties", "dictionary", "thermophysicalProperties",
       "dpdt            no;\n\n" + gen.WATER_THERMO)
    if a.turb == "laminar":
        wr(case, "constant/turbulenceProperties", "dictionary", "turbulenceProperties", "simulationType  laminar;\n")
    else:
        wr(case, "constant/turbulenceProperties", "dictionary", "turbulenceProperties",
           f"simulationType  RAS;\n\nRAS\n{{\n    RASModel        {a.turb};\n    turbulence      on;\n    printCoeffs     on;\n}}\n")
        # compressible branch: correct sign (see ESI_bug_report_draft.md)
        wr(case, "constant/fvOptions", "dictionary", "fvOptions",
           "buoyancyTurbSource1\n{\n    type            buoyancyTurbSource;\n    selectionMode   all;\n}\n")
    # numerics identical to the production 2D runs
    tmp = os.path.join(case, "_gen")
    subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "make_tank_case.py"),
                    tmp, "--props", "real", "--end", "1", "--write", "1"], check=True, capture_output=True)
    for f in ("fvSchemes", "fvSolution"):
        os.replace(os.path.join(tmp, "system", f), os.path.join(case, "system", f))
    subprocess.run(["rm", "-rf", tmp])
    # centreline probes: vertical velocity and T along the tank axis (laser-sheet centre)
    # h_j = 39 mm + depth below the baffle face where U_y changes sign (Lou Fig. 3, 5)
    wr(case, "system/controlDict", "dictionary", "controlDict", f"""application     buoyantPimpleFoam;
startFrom       latestTime;
startTime       0;
stopAt          endTime;
endTime         {a.end};
deltaT          1e-4;
writeControl    adjustableRunTime;
writeInterval   50;
purgeWrite      0;
writeFormat     binary;
writePrecision  8;
writeCompression off;
timeFormat      general;
timePrecision   8;
runTimeModifiable true;
adjustTimeStep  yes;
maxCo           {a.maxCo};
maxDeltaT       0.05;

functions
{{
    axis
    {{
        type            sets;
        libs            (sampling);
        writeControl    adjustableRunTime;
        writeInterval   2.5;
        interpolationScheme cell;
        setFormat       raw;
        fields          (U T);
        sets
        (
            centreline
            {{
                type    uniform;
                axis    y;
                start   (0.0003 0.0005 0.0003);
                end     (0.0003 0.3505 0.0003);
                nPoints 701;
            }}
        );
    }}
    outletT
    {{
        type            surfaceFieldValue;
        libs            (fieldFunctionObjects);
        writeControl    timeStep;
        writeInterval   10;
        writeFields     false;
        regionType      patch;
        name            outlet;
        operation       areaAverage;
        fields          (T);
    }}
    meanT
    {{
        type            volFieldValue;
        libs            (fieldFunctionObjects);
        writeControl    timeStep;
        writeInterval   10;
        writeFields     false;
        regionType      all;
        operation       volAverage;
        fields          (T);
    }}
}}
""")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("case")
    ap.add_argument("--turb", default="kOmegaSST", choices=["kOmegaSST", "laminar"])
    ap.add_argument("--end", type=float, default=750)
    ap.add_argument("--maxCo", type=float, default=2.0)
    ap.add_argument("--fine-lower", action="store_true", help="refine the lower baffle like the upper one")
    a = ap.parse_args()
    case = os.path.abspath(a.case)
    os.makedirs(os.path.join(case, "system"), exist_ok=True)
    wr(case, "system/controlDict", "dictionary", "controlDict",
       "application blockMesh;\nstartFrom startTime;\nstartTime 0;\nstopAt endTime;\nendTime 1;\n"
       "deltaT 1;\nwriteControl timeStep;\nwriteInterval 1;\n")
    # placeholders for the mesh utilities (replaced in setup)
    wr(case, "system/fvSchemes", "dictionary", "fvSchemes",
       "ddtSchemes {}\ngradSchemes {}\ndivSchemes {}\nlaplacianSchemes {}\n"
       "interpolationSchemes {}\nsnGradSchemes {}\n")
    wr(case, "system/fvSolution", "dictionary", "fvSolution", "solvers {}\n")
    info = mesh(case, a.fine_lower)
    info["fine_lower"] = a.fine_lower
    a_in, n_in = port_area(case, "inlet", W2 / NXZ / 4)
    a_out, n_out = port_area(case, "outlet", W2 / NXZ / 4)
    u_in = (Q / 4) / a_in                    # exact quarter mass flow through the staircase disc
    setup(case, a, u_in)
    fields(case, a, u_in)
    cm = open(os.path.join(case, "log.checkMesh")).read()
    cells = int(re.search(r"cells:\s+(\d+)", cm).group(1))
    info.update({"case": "Lou2023_uniformOBD", "source": "doi:10.1016/j.est.2023.108017", "turbulence": a.turb,
                 "Q_m3_s": Q, "T_in_K": TH, "T_init_K": TC, "end_time_s": a.end, "maxCo": a.maxCo,
                 "inlet_faces": n_in, "inlet_area_quarter_m2": a_in,
                 "inlet_area_ratio": a_in / (math.pi * D_PORT ** 2 / 16), "u_in_m_s": u_in,
                 "outlet_area_ratio": a_out / (math.pi * D_PORT ** 2 / 16), "cells": cells,
                 "mesh_ok": "Mesh OK" in cm})
    json.dump(info, open(os.path.join(case, "case.json"), "w"), indent=1)
    print(json.dumps(info, indent=1))


if __name__ == "__main__":
    main()
