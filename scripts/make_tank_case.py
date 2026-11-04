#!/usr/bin/env python3
"""Generate a 2D stratified hot-water tank case (charging or discharging) for OpenFOAM
v2606: constant-property Boussinesq or real water properties, laminar or k-omega SST.
Uniform square cells so the fields map directly onto a regular grid for ML. Writes
case.json with all inputs and the dimensionless groups.

Usage: make_tank_case.py <case_dir> [--h 0.005] [--uin 0.02] [--tin 60] [--t0 20]
                         [--W 0.5] [--H 1.0] [--s 0.04] [--off 0.06]
                         [--inlet-type A|B] [--mode charge|discharge] [--yi 0.7]
                         [--tstar 1.2 | --end 600 --write 10] [--props real] ...
All lengths must be multiples of the cell size h (type B also needs (W - s)/2).
"""
import argparse
import json
import math
import os

HEADER = """FoamFile
{{
    version     2.0;
    format      ascii;
    class       {cls};
    object      {obj};
}}
"""

EPS = 1e-9
# Inflow direction for a port on each tank side
INFLOW = {"left": (1, 0), "right": (-1, 0), "top": (0, -1), "bottom": (0, 1)}


def ports(inlet_type, W, H, s, off):
    """Upper and lower ports as (side, lo, hi), lo/hi along that side (m).
    Type A: side-wall slots (upper on the left wall, lower on the right wall), each
    `off` from the top/bottom wall. Type B: centred slots in the lid and the bottom."""
    r = lambda v: round(v, 10)
    if inlet_type == "A":
        return ("left", r(H - off - s), r(H - off)), ("right", r(off), r(off + s))
    lo, hi = r(W / 2 - s / 2), r(W / 2 + s / 2)
    return ("top", lo, hi), ("bottom", lo, hi)


# Liquid water at 1 atm, 10 to 80 C, polynomials in T [K] fitted by fit_water.py to
# IAPWS tabulated values (max error: rho 0.004 %, Cp 0.003 %, mu 0.31 %, kappa 0.03 %).
WATER_THERMO = """thermoType
{
    type            heRhoThermo;
    mixture         pureMixture;
    transport       polynomial;
    thermo          hPolynomial;
    equationOfState icoPolynomial;
    specie          specie;
    energy          sensibleEnthalpy;
}

mixture
{
    specie
    {
        molWeight       18.0153;
    }
    equationOfState
    {
        rhoCoeffs<8>    (2.1695153532e+02 6.9673175536e+00 -1.9562261905e-02 1.6666666667e-05 0 0 0 0);
    }
    thermodynamics
    {
        Hf              0;
        Sf              0;
        CpCoeffs<8>     (8.7910736814e+03 -4.0168891060e+01 1.1524691558e-01 -1.0858585859e-04 0 0 0 0);
    }
    transport
    {
        muCoeffs<8>     (4.4886658098e-01 -5.2448355236e-03 2.3131602402e-05 -4.5541804293e-08 3.3731060606e-11 0 0 0);
        kappaCoeffs<8>  (-3.9613697489e-01 3.9678796580e-03 1.5929004329e-06 -1.2121212121e-08 0 0 0 0);
    }
}
"""
P0 = 1e5  # absolute pressure level for the real-property solver (Pa)
# The same polynomial coefficients as WATER_THERMO, for metadata and post-processing
RHO_C = (2.1695153532e+02, 6.9673175536e+00, -1.9562261905e-02, 1.6666666667e-05)
CP_C = (8.7910736814e+03, -4.0168891060e+01, 1.1524691558e-01, -1.0858585859e-04)
MU_C = (4.4886658098e-01, -5.2448355236e-03, 2.3131602402e-05, -4.5541804293e-08, 3.3731060606e-11)
KAPPA_C = (-3.9613697489e-01, 3.9678796580e-03, 1.5929004329e-06, -1.2121212121e-08)


def poly(cs, T):
    return sum(c * T ** n for n, c in enumerate(cs))


def nu_beta_alpha(T):
    """Kinematic viscosity, expansion coefficient and thermal diffusivity at T [K]."""
    rho = poly(RHO_C, T)
    drho = sum(n * c * T ** (n - 1) for n, c in enumerate(RHO_C) if n)
    return poly(MU_C, T) / rho, -drho / rho, poly(KAPPA_C, T) / (rho * poly(CP_C, T))


def write(path, cls, obj, body):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(HEADER.format(cls=cls, obj=obj) + body)


def ncells(length, h):
    n = round(length / h)
    if abs(n * h - length) > 1e-9:
        raise ValueError(f"length {length} not a multiple of cell size {h}")
    return n


def breaks(W, H, port_list):
    """Block edges: tank corners plus the ends of every port."""
    xs, ys = {0.0, W}, {0.0, H}
    for side, lo, hi in port_list:
        (ys if side in ("left", "right") else xs).update((lo, hi))
    return sorted(xs), sorted(ys)


def cell_centres(h, xs, ys):
    """Cell centres in blockMesh order (blocks j-outer/i-inner, cells x-fastest)."""
    out = []
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            nx, ny = ncells(xs[i + 1] - xs[i], h), ncells(ys[j + 1] - ys[j], h)
            for b in range(ny):
                for a in range(nx):
                    out.append((xs[i] + (a + 0.5) * h, ys[j] + (b + 0.5) * h))
    return out


def block_mesh(h, xs, ys, inlet, outlet):
    I, J = len(xs) - 1, len(ys) - 1
    verts, idx = [], {}
    for j, y in enumerate(ys):
        for i, x in enumerate(xs):
            for k, z in enumerate((0.0, 0.01)):
                idx[(i, j, k)] = len(verts)
                verts.append(f"    ({x:.10g} {y:.10g} {z})")
    blocks = []
    for j in range(J):
        for i in range(I):
            nx, ny = ncells(xs[i + 1] - xs[i], h), ncells(ys[j + 1] - ys[j], h)
            v = [idx[(i, j, 0)], idx[(i + 1, j, 0)], idx[(i + 1, j + 1, 0)], idx[(i, j + 1, 0)],
                 idx[(i, j, 1)], idx[(i + 1, j, 1)], idx[(i + 1, j + 1, 1)], idx[(i, j + 1, 1)]]
            blocks.append(f"    hex ({' '.join(map(str, v))}) ({nx} {ny} 1) simpleGrading (1 1 1)")

    def face(side, n):  # boundary face of segment n on a side, outward normal
        if side == "left":
            q = [(0, n, 0), (0, n + 1, 0), (0, n + 1, 1), (0, n, 1)]
        elif side == "right":
            q = [(I, n, 0), (I, n, 1), (I, n + 1, 1), (I, n + 1, 0)]
        elif side == "bottom":
            q = [(n, 0, 0), (n, 0, 1), (n + 1, 0, 1), (n + 1, 0, 0)]
        else:
            q = [(n, J, 0), (n + 1, J, 0), (n + 1, J, 1), (n, J, 1)]
        return "(" + " ".join(str(idx[p]) for p in q) + ")"

    def matches(port, side, lo, hi):
        return port[0] == side and abs(port[1] - lo) < EPS and abs(port[2] - hi) < EPS

    faces = {"inlet": [], "outlet": [], "walls": []}
    for side in ("left", "right", "bottom", "top"):
        edges = ys if side in ("left", "right") else xs
        for n in range(len(edges) - 1):
            lo, hi = edges[n], edges[n + 1]
            name = ("inlet" if matches(inlet, side, lo, hi) else
                    "outlet" if matches(outlet, side, lo, hi) else "walls")
            faces[name].append(face(side, n))
    if len(faces["inlet"]) != 1 or len(faces["outlet"]) != 1:
        raise ValueError("port does not align with block edges")
    front = [f"({idx[(i,j,0)]} {idx[(i,j+1,0)]} {idx[(i+1,j+1,0)]} {idx[(i+1,j,0)]})"
             for j in range(J) for i in range(I)]
    back = [f"({idx[(i,j,1)]} {idx[(i+1,j,1)]} {idx[(i+1,j+1,1)]} {idx[(i,j+1,1)]})"
            for j in range(J) for i in range(I)]

    def patch(name, typ, fl):
        fl = "\n".join("            " + f for f in fl)
        return f"    {name}\n    {{\n        type {typ};\n        faces\n        (\n{fl}\n        );\n    }}"

    body = "convertToMeters 1;\n\nvertices\n(\n" + "\n".join(verts) + "\n);\n\nblocks\n(\n"
    body += "\n".join(blocks) + "\n);\n\nedges\n(\n);\n\nboundary\n(\n"
    body += "\n".join([
        patch("inlet", "patch", faces["inlet"]),
        patch("outlet", "patch", faces["outlet"]),
        patch("walls", "wall", faces["walls"]),
        patch("frontAndBack", "empty", front + back),
    ])
    body += "\n);\n\nmergePatchPairs\n(\n);\n"
    return body, ncells(xs[-1], h), ncells(ys[-1], h)


def field(cls, obj, dim, internal, bcs):
    entries = "\n".join(f"    {p}\n    {{\n{b}\n    }}" for p, b in bcs.items())
    return (f"dimensions      {dim};\n\ninternalField   {internal};\n\n"
            f"boundaryField\n{{\n{entries}\n    frontAndBack\n    {{\n        type empty;\n    }}\n}}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("case")
    ap.add_argument("--h", type=float, default=0.005, help="cell size (m)")
    ap.add_argument("--uin", type=float, default=0.02, help="inlet velocity (m/s)")
    ap.add_argument("--tin", type=float, default=60.0, help="inlet temperature (C)")
    ap.add_argument("--t0", type=float, default=20.0, help="initial tank temperature (C)")
    ap.add_argument("--end", type=float, default=600.0, help="end time (s)")
    ap.add_argument("--write", type=float, default=10.0, help="field write interval (s)")
    ap.add_argument("--turb", choices=["laminar", "kOmegaSST"], default="laminar")
    ap.add_argument("--buoy", action="store_true",
                    help="add OpenFOAM's buoyancyTurbSource (k and omega); its Boussinesq "
                         "k term has the wrong sign, kept only to reproduce that finding")
    ap.add_argument("--buoyk", action="store_true",
                    help="add our buoyancy term Gb = beta*alphat*(grad(T) & g) to the k "
                         "equation only (sink in stable layers, source in unstable)")
    ap.add_argument("--ti", type=float, default=0.05, help="inlet turbulence intensity")
    ap.add_argument("--props", choices=["boussinesq", "real"], default="boussinesq",
                    help="boussinesq: constant properties (buoyantBoussinesqPimpleFoam); "
                         "real: temperature-dependent water (buoyantPimpleFoam)")
    # Geometry and operation (defaults reproduce the original reference case)
    ap.add_argument("--W", type=float, default=0.5, help="tank width (m)")
    ap.add_argument("--H", type=float, default=1.0, help="tank height (m)")
    ap.add_argument("--s", type=float, default=0.04, help="port (slot) size (m)")
    ap.add_argument("--off", type=float, default=0.06,
                    help="type A: gap between each port and the top/bottom wall (m)")
    ap.add_argument("--inlet-type", choices=["A", "B"], default="A",
                    help="A: side-wall slots; B: slots in the lid and the bottom")
    ap.add_argument("--mode", choices=["charge", "discharge"], default="charge",
                    help="charge: inflow at the upper port; discharge: inflow at the lower port")
    ap.add_argument("--yi", type=float, default=None,
                    help="pre-stratified start: interface height as a fraction of H "
                         "(hot above, cold below); omit for a uniform tank at --t0")
    ap.add_argument("--delta", type=float, default=0.02,
                    help="pre-stratified start: interface half-thickness (m), tanh profile")
    ap.add_argument("--tstar", type=float, default=None,
                    help="end at dimensionless time t* = t*Q/V (overrides --end)")
    ap.add_argument("--nsnap", type=int, default=120, help="snapshots when --tstar is used")
    a = ap.parse_args()
    real = a.props == "real"
    if (a.buoy or a.buoyk) and a.turb == "laminar":
        ap.error("--buoy/--buoyk need a turbulence model")
    if a.buoy and a.buoyk:
        ap.error("choose one of --buoy and --buoyk")
    if real and a.buoyk:
        ap.error("with --props real use --buoy (OpenFOAM's density-based k term is correct)")

    c = a.case
    W, H, s = a.W, a.H, a.s
    tin, t0 = a.tin + 273.15, a.t0 + 273.15
    tref = 0.5 * (tin + t0)
    upper, lower = ports(a.inlet_type, W, H, s, a.off)
    inlet, outlet = (upper, lower) if a.mode == "charge" else (lower, upper)
    d = INFLOW[inlet[0]]
    uvec = f"({d[0] * a.uin:g} {d[1] * a.uin:g} 0)"
    if a.tstar is not None:
        a.end = a.tstar * W * H / (a.uin * s)
        a.write = a.end / a.nsnap

    xs, ys = breaks(W, H, (inlet, outlet))
    bm, nx, ny = block_mesh(a.h, xs, ys, inlet, outlet)
    write(f"{c}/system/blockMeshDict", "dictionary", "blockMeshDict", bm)

    # Initial temperature: uniform, or hot-over-cold tanh profile around y = yi*H
    if a.yi is None:
        t_init = f"uniform {t0}"
    else:
        th, tc = max(tin, t0), min(tin, t0)
        vals = [tc + (th - tc) * 0.5 * (1 + math.tanh((y - a.yi * H) / a.delta))
                for _, y in cell_centres(a.h, xs, ys)]
        t_init = (f"nonuniform List<scalar>\n{len(vals)}\n(\n"
                  + "\n".join(f"{v:.6f}" for v in vals) + "\n)\n")

    write(f"{c}/constant/g", "uniformDimensionedVectorField", "g",
          "dimensions      [0 1 -2 0 0 0 0];\nvalue           (0 -9.81 0);\n")
    if real:
        write(f"{c}/constant/thermophysicalProperties", "dictionary",
              "thermophysicalProperties", WATER_THERMO)
    else:
        # Water near 40 C; Boussinesq expansion coefficient is a stated approximation.
        write(f"{c}/constant/transportProperties", "dictionary", "transportProperties",
              f"transportModel  Newtonian;\nnu              6.6e-07;\nbeta            3.5e-04;\n"
              f"TRef            {tref:.2f};\nPr              4.3;\nPrt             0.85;\n")
    turb = a.turb != "laminar"
    if turb:
        write(f"{c}/constant/turbulenceProperties", "dictionary", "turbulenceProperties",
              f"simulationType  RAS;\n\nRAS\n{{\n    RASModel        {a.turb};\n"
              "    turbulence      on;\n    printCoeffs     on;\n}\n")
    else:
        write(f"{c}/constant/turbulenceProperties", "dictionary", "turbulenceProperties",
              "simulationType  laminar;\n")
    if a.buoy:
        write(f"{c}/constant/fvOptions", "dictionary", "fvOptions",
              "buoyancyTurbSource1\n{\n    type            buoyancyTurbSource;\n"
              "    selectionMode   all;\n    beta            3.5e-04;\n}\n")
    if a.buoyk:
        # k equation RHS gets +Gb. Stable layers (Gb < 0): implicit sink, keeps k >= 0.
        # Unstable layers (Gb > 0): explicit source.
        write(f"{c}/constant/fvOptions", "dictionary", "fvOptions", """kBuoyancy
{
    type            scalarCodedSource;
    selectionMode   all;
    fields          (k);
    name            kBuoyancy;

    codeInclude
    #{
        #include "fvcGrad.H"
        #include "fvmSup.H"
    #};

    codeAddSup
    #{
        const volScalarField& k = eqn.psi();
        const volScalarField& T = mesh_.lookupObject<volScalarField>("T");
        const volScalarField& alphat = mesh_.lookupObject<volScalarField>("alphat");
        // Same value as constant/g (the solver does not register g)
        const dimensionedVector g(dimAcceleration, vector(0, -9.81, 0));
        const dimensionedScalar beta(dimless/dimTemperature, 3.5e-04);
        const dimensionedScalar k0(k.dimensions(), SMALL);
        const dimensionedScalar G0(k.dimensions()/dimTime, 0);

        const volScalarField Gb("Gb", beta*alphat*(fvc::grad(T) & g));
        eqn += fvm::Sp(min(Gb, G0)/max(k, k0), k);
        eqn += max(Gb, G0);
    #};

    codeCorrect
    #{
    #};

    codeConstrain
    #{
    #};
}
""")

    # Kinematic pressure (Boussinesq) or absolute pressure in Pa (real properties).
    pdim, pval = ("[1 -1 -2 0 0 0 0]", P0) if real else ("[0 2 -2 0 0 0 0]", 0)
    rho_kw = "" if real else "        rho             rhok;\n"
    wall_ffp = f"        type            fixedFluxPressure;\n{rho_kw}        value           uniform {pval};"
    write(f"{c}/0/U", "volVectorField", "U", field("volVectorField", "U", "[0 1 -1 0 0 0 0]", "uniform (0 0 0)", {
        "inlet": f"        type            fixedValue;\n        value           uniform {uvec};",
        "outlet": "        type            pressureInletOutletVelocity;\n        value           uniform (0 0 0);",
        "walls": "        type            noSlip;",
    }))
    write(f"{c}/0/T", "volScalarField", "T", field("volScalarField", "T", "[0 0 0 1 0 0 0]", t_init, {
        "inlet": f"        type            fixedValue;\n        value           uniform {tin};",
        # zeroGradient: any backflow carries the adjacent tank temperature, not T0
        "outlet": f"        type            zeroGradient;",
        "walls": "        type            zeroGradient;",
    }))
    # fixedMean: p_rgh follows the stratification across the slot. A uniform fixedValue
    # drives an exchange flow once the thermocline reaches the outlet (P14 blow-up).
    write(f"{c}/0/p_rgh", "volScalarField", "p_rgh", field("volScalarField", "p_rgh", pdim, f"uniform {pval}", {
        "inlet": wall_ffp,
        "outlet": f"        type            fixedMean;\n        meanValue       {pval};\n        value           uniform {pval};",
        "walls": wall_ffp,
    }))
    calc0 = "        type            calculated;\n        value           uniform 0;"
    calcp = f"        type            calculated;\n        value           uniform {pval};"
    write(f"{c}/0/p", "volScalarField", "p", field("volScalarField", "p", pdim, f"uniform {pval}",
          {"inlet": calcp, "outlet": calcp, "walls": calcp}))
    # alphat: kinematic (m2/s) for Boussinesq, dynamic (kg/m/s) for real properties
    adim = "[1 -1 -1 0 0 0 0]" if real else "[0 2 -1 0 0 0 0]"
    wf = "compressible::alphatJayatillekeWallFunction" if real else "alphatJayatillekeWallFunction"
    alphat_wall = (f"        type            {wf};\n        Prt             0.85;\n"
                   "        value           uniform 0;") if turb else calc0
    write(f"{c}/0/alphat", "volScalarField", "alphat", field("volScalarField", "alphat", adim, "uniform 0",
          {"inlet": calc0, "outlet": calc0, "walls": alphat_wall}))
    if turb:
        slot = s
        k_in = 1.5 * (a.ti * a.uin) ** 2
        L = 0.07 * slot                         # mixing length of the inlet slot
        om_in = k_in ** 0.5 / (0.09 ** 0.25 * L)
        out_zg = lambda v: f"        type            inletOutlet;\n        inletValue      uniform {v};\n        value           uniform {v};"
        write(f"{c}/0/k", "volScalarField", "k", field("volScalarField", "k", "[0 2 -2 0 0 0 0]", f"uniform {k_in:.3e}", {
            "inlet": f"        type            fixedValue;\n        value           uniform {k_in:.3e};",
            "outlet": out_zg(f"{k_in:.3e}"),
            "walls": f"        type            kqRWallFunction;\n        value           uniform {k_in:.3e};",
        }))
        write(f"{c}/0/omega", "volScalarField", "omega", field("volScalarField", "omega", "[0 0 -1 0 0 0 0]", f"uniform {om_in:.3e}", {
            "inlet": f"        type            fixedValue;\n        value           uniform {om_in:.3e};",
            "outlet": out_zg(f"{om_in:.3e}"),
            "walls": f"        type            omegaWallFunction;\n        value           uniform {om_in:.3e};",
        }))
        write(f"{c}/0/nut", "volScalarField", "nut", field("volScalarField", "nut", "[0 2 -1 0 0 0 0]", "uniform 0", {
            "inlet": calc0, "outlet": calc0,
            "walls": "        type            nutkWallFunction;\n        value           uniform 0;",
        }))

    write(f"{c}/system/fvSchemes", "dictionary", "fvSchemes", """ddtSchemes
{
    default         backward;
}
gradSchemes
{
    default         Gauss linear;
}
divSchemes
{
    default         none;
    div(phi,U)      Gauss limitedLinearV 1;
    div(phi,T)      Gauss limitedLinear 1;
    div(phi,k)      Gauss limitedLinear 1;
    div(phi,omega)  Gauss limitedLinear 1;
    div(phi,h)      Gauss limitedLinear 1;
    div(phi,K)      Gauss linear;
    div((nuEff*dev2(T(grad(U))))) Gauss linear;
    div(((rho*nuEff)*dev2(T(grad(U))))) Gauss linear;
}
laplacianSchemes
{
    default         Gauss linear corrected;
}
interpolationSchemes
{
    default         linear;
}
snGradSchemes
{
    default         corrected;
}
wallDist
{
    method          meshWave;
}
""")
    write(f"{c}/system/fvSolution", "dictionary", "fvSolution", """solvers
{
    p_rgh
    {
        // GAMG: 2.6x faster than PCG/DIC here (7 vs 200 iterations), same mean T
        solver          GAMG;
        smoother        GaussSeidel;
        tolerance       1e-8;
        relTol          0.01;
    }
    p_rghFinal
    {
        $p_rgh;
        relTol          0;
    }
    "rho.*"
    {
        solver          diagonal;
    }
    "(U|T|h|k|omega)"
    {
        solver          PBiCGStab;
        preconditioner  DILU;
        tolerance       1e-8;
        relTol          0.1;
    }
    "(U|T|h|k|omega)Final"
    {
        $U;
        relTol          0;
    }
}
PIMPLE
{
    momentumPredictor yes;
    nOuterCorrectors 2;   // 1 overshoots ~4 K at jet start-up (P10 test); 2: 0.13 K
    nCorrectors     2;
    nNonOrthogonalCorrectors 0;
}
""")
    solver = "buoyantPimpleFoam" if real else "buoyantBoussinesqPimpleFoam"
    # Exact mass and enthalpy flow through the outlet (sum of phi, sum of phi*h) for the
    # energy balance; the area-averaged outlet T is biased when the outlet has backflow.
    flux_fo = "" if not real else """    outletFlux
    {
        type            surfaceFieldValue;
        libs            (fieldFunctionObjects);
        writeControl    timeStep;
        writeInterval   1;
        writeFields     false;
        regionType      patch;
        name            outlet;
        operation       sum;
        fields          (phi);
    }
    outletHflux
    {
        type            surfaceFieldValue;
        libs            (fieldFunctionObjects);
        writeControl    timeStep;
        writeInterval   1;
        writeFields     false;
        regionType      patch;
        name            outlet;
        operation       weightedSum;
        weightField     phi;
        fields          (h);
    }
"""
    write(f"{c}/system/controlDict", "dictionary", "controlDict", f"""application     {solver};
startFrom       startTime;
startTime       0;
stopAt          endTime;
endTime         {a.end};
deltaT          0.01;
writeControl    adjustableRunTime;
writeInterval   {a.write};
purgeWrite      0;
writeFormat     ascii;
writePrecision  8;
writeCompression off;
timeFormat      general;
timePrecision   8;
runTimeModifiable false;
adjustTimeStep  yes;
maxCo           0.5;
maxDeltaT       0.5;

functions
{{
    meanT
    {{
        type            volFieldValue;
        libs            (fieldFunctionObjects);
        writeControl    timeStep;
        writeInterval   1;
        writeFields     false;
        regionType      all;
        operation       volAverage;
        fields          (T);
    }}
    profile
    {{
        type            sets;
        libs            (sampling);
        writeControl    adjustableRunTime;
        writeInterval   {a.write};
        interpolationScheme cellPoint;
        setFormat       raw;
        fields          (T);
        sets
        (
            centreline
            {{
                type    uniform;
                axis    y;
                start   ({W/2} 0.0005 0.005);
                end     ({W/2} {H-0.0005} 0.005);
                nPoints 200;
            }}
        );
    }}
    outletT
    {{
        type            surfaceFieldValue;
        libs            (fieldFunctionObjects);
        writeControl    timeStep;
        writeInterval   1;
        writeFields     false;
        regionType      patch;
        name            outlet;
        operation       areaAverage;
        fields          (T);
    }}
{flux_fo}}}
""")
    # Dimensionless groups with properties at the mean of inlet and initial temperature
    if real:
        nu, beta, alpha = nu_beta_alpha(tref)
    else:
        nu, beta, alpha = 6.6e-07, 3.5e-04, 6.6e-07 / 4.3
    dT = abs(tin - t0)
    meta = {
        "case": os.path.basename(os.path.normpath(c)),
        "generator": "make_tank_case.py", "openfoam": "v2606", "solver": solver,
        "props": a.props, "turbulence": a.turb,
        "buoyancy_term": "buoyancyTurbSource" if a.buoy else "kBuoyancy(ours)" if a.buoyk else "none",
        "mesh_h_m": a.h, "nx": nx, "ny": ny, "x_breaks": xs, "y_breaks": ys,
        "W_m": W, "H_m": H, "slot_m": s, "port_offset_m": a.off,
        "inlet_type": a.inlet_type, "mode": a.mode, "inlet_port": inlet, "outlet_port": outlet,
        "u_in_m_s": a.uin, "T_in_K": tin, "T_init_K": t0,
        "init": "uniform" if a.yi is None else {"profile": "tanh", "yi_frac": a.yi, "delta_m": a.delta},
        "end_time_s": a.end, "write_interval_s": a.write, "tstar_end": a.tstar,
        "inlet_turbulence_intensity": a.ti if turb else None,
        "Re_in": a.uin * s / nu, "Ri_H": 9.81 * beta * dT * H / max(a.uin, 1e-12) ** 2,
        "Pe_in": a.uin * s / alpha, "aspect_ratio_H_W": H / W,
        "props_at_K": tref, "nu_m2_s": nu, "beta_1_K": beta, "alpha_m2_s": alpha,
    }
    with open(f"{c}/case.json", "w") as f:
        json.dump(meta, f, indent=1)
    print(f"case={c} h={a.h} cells={nx}x{ny}={nx*ny} uin={a.uin} Re_in={meta['Re_in']:.0f} "
          f"Ri={meta['Ri_H']:.3g} Tin={a.tin}C T0={a.t0}C end={a.end:.6g}s turb={a.turb} buoy={a.buoy} "
          f"buoyk={a.buoyk} props={a.props} type={a.inlet_type} mode={a.mode} solver={solver}")


if __name__ == "__main__":
    main()
