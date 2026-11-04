#!/usr/bin/env python3
"""Generate a 2D PCM melting case (rectangular enclosure heated from one side, optional
horizontal fins on the heated wall) for OpenFOAM v2606.

Model: buoyantPimpleFoam with constant properties (rhoConst, hConst, const transport) and
the enthalpy-porosity source solidificationMeltingSource (Voller & Prakash 1987): latent heat
as an enthalpy source, Carman-Kozeny momentum sink Cu*(1-a)^2/(a^3+q) in solid and mushy
cells, and Boussinesq buoyancy rho*g*beta*(T - Tmelt) added by the same source. Density is
constant in the solver, so buoyancy comes only from that source (no double counting).
This is the simplified "B-2D" model of Vogel & Thess (2019), validated there within 1.4 % of
a variable-property VOF model on liquid fraction.

Fins are isothermal at the wall temperature (--fin-model isothermal, holes in the mesh), or
conducting (--fin-model conduct, with --melt-range): the fin cells stay in the mesh as a
cellZone 'fin' held solid (liquid fraction 0, Darcy sink), and an extra implicit diffusion
term raises their conductivity to --k-fin. Face conductivities are harmonic means, so the
fin/PCM faces see the series resistance. Fin heat capacity is the PCM's rho*cp (Al is ~15 %
higher; the fins are a few per cent of the volume).
Uniform square cells, so fields map directly onto a regular grid for ML. Writes case.json.

Usage: make_pcm_case.py <case_dir> [--material octadecane] [--W 0.025] [--H 0.1]
                        [--tw 38] [--t0 27] [--h 0.0005] [--right sym|wall] [--top sym|wall]
                        [--nfins 0 --fin-len 0.01 --fin-t 0.001] [--tilt 0|45|90]
                        [--end 14400 --write 60]
Lengths (W, H, fin length, fin thickness, fin positions) must be multiples of h.
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

# Constant-property sets. octadecane: Vogel & Thess (2019) Table 3 (from Galione et al. 2015),
# reduced the B-2D way (their Table 5): mean of solid and liquid density and cp near Tmelt
# (correct stored energy), liquid conductivity at Tmelt, viscosity at the mean liquid
# temperature Tmelt + dT/2 (33 C for their Tw = 38 C). Formulas take T in K.
MATERIALS = {
    "octadecane": {
        "Tmelt_C": 28.0, "L_J_kg": 242454.0, "beta_1_K": 8.9e-4, "molWeight": 254.5,
        "rho_s": 863.0, "rho_l_at_Tm": 778.466, "cp_s": 1942.0,
        "cp_l": lambda T: 1394.560 + 2.7186 * T,                       # T in K
        "k_l": lambda T: 0.2067352 - 1.841779e-4 * T,
        "mu_l": lambda T: 0.02966723 - 8.533286e-5 * T,
        "source": "Vogel & Thess 2019 Appl Therm Eng 148:147, Table 3 (Galione et al. 2015)",
    },
    # lauric acid: Kamkari & Shokouhmand (2014) Table 1 (constant values; melting range
    # 43.5-48.2 C, interface taken as 43.5 C as in the paper). beta backed out from the
    # paper's Ra at 55 and 70 C (both give 8.2e-4); mu = nu * rho_liquid.
    "lauric": {
        "Tmelt_C": 43.5, "L_J_kg": 187210.0, "beta_1_K": 8.2e-4, "molWeight": 200.3,
        "rho_s": 940.0, "rho_l_at_Tm": 885.0, "cp_s": 2180.0,
        "cp_l": lambda T: 2390.0,
        "k_l": lambda T: 0.14,
        "mu_l": lambda T: 6.7e-6 * 885.0,
        "source": "Kamkari & Shokouhmand 2014 IJHMT 78:839, Table 1; beta from their Ra",
    },
}


def props(mat, tw_K, tmelt_C=None):
    """Constant B-2D property set for a wall temperature tw_K (optionally another Tmelt,
    e.g. the midpoint of a melting range)."""
    m = MATERIALS[mat]
    Tm = (m["Tmelt_C"] if tmelt_C is None else tmelt_C) + 273.15
    Tl = 0.5 * (Tm + tw_K)                                      # mean liquid temperature
    rho = 0.5 * (m["rho_s"] + m["rho_l_at_Tm"])
    cp = 0.5 * (m["cp_s"] + m["cp_l"](Tm))
    # Vogel & Thess Table 5 (checked against the published version): k = liquid value at Tm,
    # mu at the mean liquid temperature Tm + dT/2
    k, mu = m["k_l"](Tm), m["mu_l"](Tl)
    return {"rho": rho, "cp": cp, "k": k, "mu": mu, "Pr": cp * mu / k, "Tmelt_K": Tm,
            "L": m["L_J_kg"], "beta": m["beta_1_K"], "molWeight": m["molWeight"],
            "props_at_K": Tl, "source": m["source"]}


def melt_range_fvoptions(Ts, Tl, L, cp, rho, beta, Cu, q, relax, k_pcm=None, k_fin=None):
    """Enthalpy-porosity with a melting RANGE [Ts, Tl] (K) as two coded fvOptions.
    Liquid fraction alpha = (T - Ts)/(Tl - Ts) clamped to [0, 1], reached by the
    Voller-Swaminathan source update, once per time step:
        alpha += relax * cp (T - T_F(alpha)) / (L + cp (Tl - Ts)),  T_F = Ts + alpha (Tl - Ts)
    (the increment that puts T back on the alpha(T) line at fixed enthalpy; with Tl = Ts it is
    exactly OpenFOAM's solidificationMeltingSource update). Energy: h -= L ddt(rho, alpha).
    Momentum: Carman-Kozeny sink Cu (1-alpha)^2/(alpha^3+q) and Boussinesq buoyancy
    rho g beta (T - Tref) with Tref the range midpoint, signs as in solidificationMeltingSource.
    The field is called melting:alpha1, like OpenFOAM's source, so logging, auto-stop and the
    exporter work unchanged."""
    Tref = 0.5 * (Ts + Tl)
    return f"""meltRangeEnergy
{{
    type            scalarCodedSource;
    selectionMode   all;
    fields          (h);
    name            meltRangeEnergy;

    codeInclude
    #{{
        #include "fvcDdt.H"
    #}};

    codeAddSup
    #{{
        FatalErrorInFunction << "meltRangeEnergy needs a density-based solver" << abort(FatalError);
    #}};

    codeAddSupRho
    #{{
        const scalar Ts = {Ts:.8g}, Tl = {Tl:.8g}, L = {L:.8g}, cp = {cp:.8g}, relax = {relax:.8g};
        const volScalarField& T = mesh_.lookupObject<volScalarField>("T");
        volScalarField* ap = mesh_.getObjectPtr<volScalarField>("melting:alpha1");
        if (!ap)
        {{
            ap = new volScalarField
            (
                IOobject("melting:alpha1", mesh_.time().timeName(), mesh_,
                         IOobject::READ_IF_PRESENT, IOobject::AUTO_WRITE, IOobject::REGISTER),
                mesh_, dimensionedScalar(dimless, Zero), fvPatchFieldBase::zeroGradientType()
            );
            ap->store();
        }}
        volScalarField& alpha = *ap;
        static label lastIndex = -1;
        if (lastIndex != mesh_.time().timeIndex())
        {{
            alpha.oldTime();
            // conducting fin cells (cellZone fin, if any) stay solid
            boolList isFin(mesh_.nCells(), false);
            const label zi = mesh_.cellZones().findZoneID("fin");
            if (zi >= 0)
            {{
                for (const label c : mesh_.cellZones()[zi]) isFin[c] = true;
            }}
            forAll(alpha, i)
            {{
                if (isFin[i]) continue;
                const scalar TF = Ts + alpha[i]*(Tl - Ts);
                alpha[i] = clamp(alpha[i] + relax*cp*(T[i] - TF)/(L + cp*(Tl - Ts)), zero_one{{}});
            }}
            alpha.correctBoundaryConditions();
            lastIndex = mesh_.time().timeIndex();
        }}
        eqn -= dimensionedScalar(dimEnergy/dimMass, L)*fvc::ddt(rho, alpha);
    #}};

    codeCorrect
    #{{
    #}};

    codeConstrain
    #{{
    #}};
}}

meltRangeMomentum
{{
    type            vectorCodedSource;
    selectionMode   all;
    fields          (U);
    name            meltRangeMomentum;

    codeInclude
    #{{
        #include "gravityMeshObject.H"
    #}};

    codeAddSup
    #{{
        FatalErrorInFunction << "meltRangeMomentum needs a density-based solver" << abort(FatalError);
    #}};

    codeAddSupRho
    #{{
        const scalar Cu = {Cu:.8g}, q = {q:.8g}, rhoRef = {rho:.8g}, beta = {beta:.8g}, Tref = {Tref:.8g};
        const volScalarField& T = mesh_.lookupObject<volScalarField>("T");
        // before the energy source has created the field (first step) everything is solid
        const volScalarField* ap = mesh_.findObject<volScalarField>("melting:alpha1");
        const vector& g = meshObjects::gravity::New(mesh_.time()).value();
        scalarField& Sp = eqn.diag();
        vectorField& Su = eqn.source();
        const scalarField& V = mesh_.V();
        forAll(V, i)
        {{
            const scalar a = ap ? (*ap)[i] : 0.0;
            Sp[i] += V[i]*(-Cu*sqr(1.0 - a)/(pow3(a) + q));
            Su[i] += V[i]*rhoRef*beta*(T[i] - Tref)*g;
        }}
    #}};

    codeCorrect
    #{{
    #}};

    codeConstrain
    #{{
    #}};
}}
""" + ("" if k_fin is None else fin_conduction_fvoption(k_pcm, k_fin, cp))


def fin_conduction_fvoption(k_pcm, k_fin, cp):
    """Extra implicit diffusion that raises the conductivity of the cellZone 'fin' from k_pcm
    to k_fin: the energy equation gets laplacian(D, h) with face D = (k_face - k_pcm)/cp,
    k_face the harmonic mean of the two cell conductivities (exact series resistance on a
    uniform grid; 0 on PCM-PCM faces, ~k_pcm on fin-PCM faces, k_fin - k_pcm inside the fin
    and on the fin root at the heated wall)."""
    return f"""
finConduction
{{
    type            scalarCodedSource;
    selectionMode   all;
    fields          (h);
    name            finConduction;

    codeInclude
    #{{
        #include "fvmLaplacian.H"
        #include "surfaceInterpolate.H"
    #}};

    codeAddSup
    #{{
        FatalErrorInFunction << "finConduction needs a density-based solver" << abort(FatalError);
    #}};

    codeAddSupRho
    #{{
        const scalar kPcm = {k_pcm:.8g}, kFin = {k_fin:.8g}, cp = {cp:.8g};
        surfaceScalarField* Dp = mesh_.getObjectPtr<surfaceScalarField>("finConduction:D");
        if (!Dp)
        {{
            volScalarField rk
            (
                IOobject("finConduction:rk", mesh_.time().timeName(), mesh_,
                         IOobject::NO_READ, IOobject::NO_WRITE, IOobject::NO_REGISTER),
                mesh_, dimensionedScalar(dimless, 1.0/kPcm), fvPatchFieldBase::zeroGradientType()
            );
            const label zi = mesh_.cellZones().findZoneID("fin");
            if (zi < 0)
            {{
                FatalErrorInFunction << "no cellZone fin (run topoSet)" << abort(FatalError);
            }}
            for (const label c : mesh_.cellZones()[zi]) rk[c] = 1.0/kFin;
            rk.correctBoundaryConditions();
            Dp = new surfaceScalarField
            (
                IOobject("finConduction:D", mesh_.time().timeName(), mesh_,
                         IOobject::NO_READ, IOobject::NO_WRITE, IOobject::REGISTER),
                dimensionedScalar(dimMass/dimLength/dimTime, 1.0)
               *max(1.0/fvc::interpolate(rk) - kPcm, dimensionedScalar(dimless, Zero))/cp
            );
            Dp->store();
            Info<< "finConduction: " << returnReduce(mesh_.cellZones()[zi].size(), sumOp<label>())
                << " fin cells, k " << kFin << " (PCM " << kPcm << ")" << endl;
        }}
        eqn += fvm::laplacian(*Dp, eqn.psi());
    #}};

    codeCorrect
    #{{
    #}};

    codeConstrain
    #{{
    #}};
}}
"""


def write(path, cls, obj, body):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(HEADER.format(cls=cls, obj=obj) + body)


def ncells(length, h):
    n = round(length / h)
    if n < 1 or abs(n * h - length) > 1e-9:
        raise ValueError(f"length {length} not a positive multiple of cell size {h}")
    return n


def fin_spans(H, nfins, fin_t, h, centres=None):
    """(y_lo, y_hi) of each fin, snapped to the cell grid. Centres default to H*k/(nfins+1)
    (equal spacing); pass centres to place fins as in an experiment."""
    if centres is None:
        centres = [H * k / (nfins + 1) for k in range(1, nfins + 1)]
    out = []
    for yc in centres:
        lo = round((yc - fin_t / 2) / h) * h
        out.append((round(lo, 10), round(lo + fin_t, 10)))
    return out


def block_mesh(h, W, H, fins, fin_len, right, top, holes=True):
    """Multi-block 2D mesh with the fin blocks left out. Returns (dict text, xs, ys, solid)."""
    xs = sorted({0.0, W} | ({round(fin_len, 10)} if fins else set()))
    ys = sorted({0.0, H} | {y for f in fins for y in f})
    I, J = len(xs) - 1, len(ys) - 1
    finb = {(0, j) for j in range(J) if any(abs(ys[j] - lo) < EPS and abs(ys[j + 1] - hi) < EPS
                                             for lo, hi in fins)}
    solid = finb if holes else set()
    idx, verts = {}, []
    for j, y in enumerate(ys):
        for i, x in enumerate(xs):
            for k, z in enumerate((0.0, h)):
                idx[(i, j, k)] = len(verts)
                verts.append(f"    ({x:.10g} {y:.10g} {z:.10g})")
    blocks, faces = [], {"hot": [], "finroot": [], "fins": [], "right": [], "bottom": [], "top": [], "frontAndBack": []}
    q = lambda pts: "(" + " ".join(str(idx[p]) for p in pts) + ")"
    for j in range(J):
        for i in range(I):
            if (i, j) in solid:
                continue
            nx, ny = ncells(xs[i + 1] - xs[i], h), ncells(ys[j + 1] - ys[j], h)
            v = [(i, j, 0), (i + 1, j, 0), (i + 1, j + 1, 0), (i, j + 1, 0),
                 (i, j, 1), (i + 1, j, 1), (i + 1, j + 1, 1), (i, j + 1, 1)]
            blocks.append(f"    hex {q(v)} ({nx} {ny} 1) simpleGrading (1 1 1)")
            # lateral faces (outward normals) and what lies beyond each
            sides = {
                "xmin": ((i, j, 0), (i, j, 1), (i, j + 1, 1), (i, j + 1, 0)),
                "xmax": ((i + 1, j, 0), (i + 1, j + 1, 0), (i + 1, j + 1, 1), (i + 1, j, 1)),
                "ymin": ((i, j, 0), (i + 1, j, 0), (i + 1, j, 1), (i, j, 1)),
                "ymax": ((i, j + 1, 0), (i, j + 1, 1), (i + 1, j + 1, 1), (i + 1, j + 1, 0)),
            }
            nb = {"xmin": (i - 1, j), "xmax": (i + 1, j), "ymin": (i, j - 1), "ymax": (i, j + 1)}
            for s, pts in sides.items():
                ni, nj = nb[s]
                if (ni, nj) in solid:
                    faces["fins"].append(q(pts))
                elif ni < 0:
                    faces["finroot" if (i, j) in finb else "hot"].append(q(pts))
                elif ni >= I:
                    faces["right"].append(q(pts))
                elif nj < 0:
                    faces["bottom"].append(q(pts))
                elif nj >= J:
                    faces["top"].append(q(pts))
            faces["frontAndBack"] += [q((v[0], v[3], v[2], v[1])), q((v[4], v[5], v[6], v[7]))]
    kind = {"hot": "wall", "finroot": "wall", "fins": "wall", "bottom": "wall", "frontAndBack": "empty",
            "right": "symmetryPlane" if right == "sym" else "wall",
            "top": "symmetryPlane" if top == "sym" else "wall"}

    def patch(name):
        fl = "\n".join("            " + f for f in faces[name])
        return f"    {name}\n    {{\n        type {kind[name]};\n        faces\n        (\n{fl}\n        );\n    }}"

    body = "convertToMeters 1;\n\nvertices\n(\n" + "\n".join(verts) + "\n);\n\nblocks\n(\n"
    body += "\n".join(blocks) + "\n);\n\nedges\n(\n);\n\nboundary\n(\n"
    body += "\n".join(patch(n) for n in faces if faces[n]) + "\n);\n\nmergePatchPairs\n(\n);\n"
    return body, xs, ys, solid, kind, [n for n in faces if faces[n]]


def field(dim, internal, bcs):
    entries = "\n".join(f"    {p}\n    {{\n{b}\n    }}" for p, b in bcs.items())
    return f"dimensions      {dim};\n\ninternalField   {internal};\n\nboundaryField\n{{\n{entries}\n}}\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("case")
    ap.add_argument("--material", choices=list(MATERIALS), default="octadecane")
    ap.add_argument("--W", type=float, default=0.025, help="width, or half width with --right sym (m)")
    ap.add_argument("--H", type=float, default=0.1, help="height (m)")
    ap.add_argument("--tw", type=float, default=38.0, help="heated wall (and fin) temperature (C)")
    ap.add_argument("--t0", type=float, default=27.0, help="initial temperature (C), below Tmelt")
    ap.add_argument("--h", type=float, default=0.0005, help="cell size (m)")
    ap.add_argument("--right", choices=["sym", "wall"], default="sym",
                    help="sym: symmetry plane (box heated from both sides); wall: adiabatic wall")
    ap.add_argument("--top", choices=["sym", "wall"], default="sym",
                    help="sym: adiabatic slip surface (free surface); wall: adiabatic no-slip lid")
    ap.add_argument("--nfins", type=int, default=0)
    ap.add_argument("--fin-len", type=float, default=0.01, help="fin length from the hot wall (m)")
    ap.add_argument("--fin-t", type=float, default=0.001, help="fin thickness (m)")
    ap.add_argument("--fin-y", default=None,
                    help="comma-separated fin centre heights (m); default: equally spaced. "
                         "Kamkari 2014 3-fin wall: 0.029,0.060,0.091")
    ap.add_argument("--fin-model", choices=["isothermal", "conduct"], default="isothermal",
                    help="isothermal: fins at the wall temperature (holes in the mesh); conduct: "
                         "fins conduct heat with --k-fin (needs --melt-range)")
    ap.add_argument("--k-fin", type=float, default=130.0,
                    help="fin conductivity (W/m K) for --fin-model conduct; Kamkari's Al 130")
    ap.add_argument("--tilt", type=float, default=0.0,
                    help="inclination (deg): 0 heated from the side, 90 heated from below; "
                         "the box stays fixed and gravity is rotated, g = -9.81 (sin, cos)")
    ap.add_argument("--tw-tau", type=float, default=0.0,
                    help="heater warm-up time constant (s): wall (and fin) temperature "
                         "Tw - (Tw - T0) exp(-t/tau); 0 = instant step. Kamkari's heater "
                         "(inclination paper Fig. 3, 70 C in ~4 min) fits tau ~ 53 s")
    ap.add_argument("--tmelt", type=float, default=None,
                    help="override the melting temperature (C); lauric acid melts over "
                         "43.5-48.2 C, Safari/Kamkari 2022 use the midpoint 45.85")
    ap.add_argument("--melt-range", default=None,
                    help="'Ts,Tl' in C: melt over a temperature range (coded enthalpy-porosity "
                         "source) instead of OpenFOAM's isothermal source; lauric acid 43.5,48.2")
    ap.add_argument("--Cu", type=float, default=1e6, help="mushy zone constant (kg/m3/s)")
    ap.add_argument("--q", type=float, default=1e-3, help="Carman-Kozeny epsilon")
    ap.add_argument("--relax", type=float, default=0.9, help="liquid fraction update relaxation")
    ap.add_argument("--maxdt", type=float, default=0.1, help="maximum time step (s)")
    ap.add_argument("--maxco", type=float, default=1.0)
    ap.add_argument("--stop-at", type=float, default=None,
                    help="stop early when the mean liquid fraction exceeds this (e.g. 0.995); "
                         "--end is then the cap")
    ap.add_argument("--end", type=float, default=14400.0, help="end time (s)")
    ap.add_argument("--write", type=float, default=60.0, help="field write interval (s)")
    a = ap.parse_args()

    c, W, H, h = a.case, a.W, a.H, a.h
    mr = [float(v) + 273.15 for v in a.melt_range.split(",")] if a.melt_range else None
    if mr and not (len(mr) == 2 and mr[0] < mr[1]):
        ap.error("--melt-range needs Ts,Tl with Ts < Tl")
    if mr and a.tmelt is not None:
        ap.error("use --melt-range or --tmelt, not both")
    # with a range, Tmelt (Boussinesq reference, Ra, Ste, Nu) is the range midpoint
    p = props(a.material, a.tw + 273.15, 0.5 * (mr[0] + mr[1]) - 273.15 if mr else a.tmelt)
    tw, t0, Tm = a.tw + 273.15, a.t0 + 273.15, p["Tmelt_K"]
    if not (t0 <= (mr[0] if mr else Tm) and (mr[1] if mr else Tm) < tw):
        ap.error("need t0 <= Tmelt (or Ts) and Tmelt (or Tl) < tw")
    centres = [float(v) for v in a.fin_y.split(",")] if a.fin_y else None
    if centres is not None and len(centres) != a.nfins:
        ap.error("--fin-y needs one height per fin")
    fins = fin_spans(H, a.nfins, a.fin_t, h, centres) if a.nfins else []
    if any(lo <= 0 or hi >= H for lo, hi in fins) or any(
            fins[i][1] >= fins[i + 1][0] for i in range(len(fins) - 1)):
        ap.error(f"fins overlap or touch the top/bottom wall: {fins}")
    if fins and not (0 < a.fin_len < W):
        ap.error("fin length must be between 0 and W")
    conduct = bool(fins) and a.fin_model == "conduct"
    if conduct and not mr:
        ap.error("--fin-model conduct needs --melt-range (use a narrow range for a melting point)")
    bm, xs, ys, solid, kind, patches = block_mesh(h, W, H, fins, a.fin_len, a.right, a.top,
                                                  holes=not conduct)
    write(f"{c}/system/blockMeshDict", "dictionary", "blockMeshDict", bm)
    nx, ny = ncells(W, h), ncells(H, h)
    n_fin = sum(ncells(a.fin_len, h) * ncells(hi - lo, h) for lo, hi in fins)
    n_fluid = nx * ny - n_fin
    if conduct:   # cellZones fin and pcm (its complement) for the sources and the averages
        boxes = " ".join(f"(-1 {lo + h / 4:.10g} -1) ({a.fin_len - h / 4:.10g} {hi - h / 4:.10g} 1)"
                         for lo, hi in fins)
        write(f"{c}/system/topoSetDict", "dictionary", "topoSetDict", f"""actions
(
    {{ name finSet; type cellSet; action new; source boxToCell; boxes ({boxes}); }}
    {{ name fin; type cellZoneSet; action new; source setToCellZone; set finSet; }}
    {{ name pcmSet; type cellSet; action new; source cellToCell; sets (finSet); }}
    {{ name pcmSet; type cellSet; action invert; }}
    {{ name pcm; type cellZoneSet; action new; source setToCellZone; set pcmSet; }}
);
""")

    # The heated wall is x = 0. Tilting by theta rotates gravity towards it: theta = 90 puts
    # the heated wall at the bottom (gravity along -x).
    th = math.radians(a.tilt)
    gx, gy = -9.81 * math.sin(th), -9.81 * math.cos(th)
    write(f"{c}/constant/g", "uniformDimensionedVectorField", "g",
          f"dimensions      [0 1 -2 0 0 0 0];\nvalue           ({gx:.6g} {gy:.6g} 0);\n")
    write(f"{c}/constant/thermophysicalProperties", "dictionary", "thermophysicalProperties", f"""thermoType
{{
    type            heRhoThermo;
    mixture         pureMixture;
    transport       const;
    thermo          hConst;
    equationOfState rhoConst;
    specie          specie;
    energy          sensibleEnthalpy;
}}

mixture
{{
    specie
    {{
        molWeight       {p['molWeight']};
    }}
    equationOfState
    {{
        rho             {p['rho']:.6g};
    }}
    thermodynamics
    {{
        Cp              {p['cp']:.6g};
        Hf              0;
    }}
    transport
    {{
        mu              {p['mu']:.6g};
        Pr              {p['Pr']:.6g};
    }}
}}
""")
    write(f"{c}/constant/turbulenceProperties", "dictionary", "turbulenceProperties",
          "simulationType  laminar;\n")
    if mr:
        write(f"{c}/constant/fvOptions", "dictionary", "fvOptions", melt_range_fvoptions(
            mr[0], mr[1], p["L"], p["cp"], p["rho"], p["beta"], a.Cu, a.q, a.relax,
            p["k"] if conduct else None, a.k_fin if conduct else None))
    else:
        write(f"{c}/constant/fvOptions", "dictionary", "fvOptions", f"""melting
{{
    type            solidificationMeltingSource;
    selectionMode   all;
    Tmelt           {Tm:.6g};
    L               {p['L']:.6g};
    thermoMode      thermo;
    rhoRef          {p['rho']:.6g};
    beta            {p['beta']:.6g};
    Cu              {a.Cu:.6g};
    q               {a.q:.6g};
    relax           {a.relax:.6g};
}}
""")

    def bc(name, wall, sym, hot=None):
        """Boundary entry per patch type."""
        out = {}
        for n in patches:
            if n == "frontAndBack":
                out[n] = "        type            empty;"
            elif kind[n] == "symmetryPlane":
                out[n] = "        type            symmetryPlane;"
            elif n in ("hot", "finroot", "fins") and hot is not None:
                out[n] = hot
            else:
                out[n] = wall
        return out

    pval = 1e5
    write(f"{c}/0/U", "volVectorField", "U", field("[0 1 -1 0 0 0 0]", "uniform (0 0 0)",
          bc("U", "        type            noSlip;", True)))
    if a.tw_tau > 0:   # heater warm-up as a time table, linear between points, then Tw
        pts = [(t, tw - (tw - t0) * math.exp(-t / a.tw_tau)) for t in range(0, int(10 * a.tw_tau) + 1, 5)]
        table = " ".join(f"({t} {v:.4f})" for t, v in pts) + f" ({int(10 * a.tw_tau) + 5} {tw})"
        hot_bc = (f"        type            uniformFixedValue;\n        uniformValue    table ({table});\n"
                  f"        value           uniform {t0};")
    else:
        hot_bc = f"        type            fixedValue;\n        value           uniform {tw};"
    write(f"{c}/0/T", "volScalarField", "T", field("[0 0 0 1 0 0 0]", f"uniform {t0}",
          bc("T", "        type            zeroGradient;", True, hot=hot_bc)))
    write(f"{c}/0/p_rgh", "volScalarField", "p_rgh", field("[1 -1 -2 0 0 0 0]", f"uniform {pval}",
          bc("p_rgh", f"        type            fixedFluxPressure;\n        value           uniform {pval};", True)))
    write(f"{c}/0/p", "volScalarField", "p", field("[1 -1 -2 0 0 0 0]", f"uniform {pval}",
          bc("p", f"        type            calculated;\n        value           uniform {pval};", True)))
    write(f"{c}/0/alphat", "volScalarField", "alphat", field("[1 -1 -1 0 0 0 0]", "uniform 0",
          bc("alphat", "        type            calculated;\n        value           uniform 0;", True)))

    write(f"{c}/system/fvSchemes", "dictionary", "fvSchemes", """ddtSchemes
{
    default         Euler;
}
gradSchemes
{
    default         Gauss linear;
}
divSchemes
{
    default         none;
    div(phi,U)      Gauss linearUpwind grad(U);
    div(phi,h)      Gauss linearUpwind grad(h);
    div(phi,K)      Gauss linear;
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
""")
    # closed box: the pressure level is fixed at one point (top corner away from fins)
    pref = f"({W - h / 2:.10g} {H - h / 2:.10g} {h / 2:.10g})"
    write(f"{c}/system/fvSolution", "dictionary", "fvSolution", """solvers
{
    p_rgh
    {
        solver          GAMG;
        smoother        GaussSeidel;
        tolerance       1e-8;
        relTol          0.01;
    }
    p_rghFinal
    {
        $p_rgh;
        // the Darcy sink in the solid makes p_rgh stiff: a fixed absolute tolerance stalls
        // and hits 1000 GAMG iterations (1e-8 at 0.5 mm, 1e-7 at 0.25 mm). Stop at a
        // 1000-fold residual drop or 1e-7, whichever comes first: mesh-independent
        tolerance       1e-7;
        // 2026-11-04 (Saxam, option A, all PCM cases): relTol 0 + maxIter 200 instead of relTol
        // 1e-3. The residual left by relTol 1e-3 collected at the pressure reference cell once it
        // melted and heated it up to +16-19 K above T_wall (QC "T out of bounds"); with relTol 0
        // there is no overshoot and the melt curve is unchanged (P0329: liquid fraction within
        // 0.005), ~25 % more run time (pc4 ~/pcm_fixtest/V1_tight). maxIter keeps the stiff
        // Darcy-sink solve from stalling at 1000 GAMG iterations.
        relTol          0;
        maxIter         200;
    }
    "rho.*"
    {
        solver          diagonal;
    }
    "(U|h)"
    {
        solver          PBiCGStab;
        preconditioner  DILU;
        tolerance       1e-10;
        relTol          0.1;
    }
    "(U|h)Final"
    {
        $U;
        relTol          0;
    }
}
PIMPLE
{
    momentumPredictor yes;
    nOuterCorrectors 1;   // the source updates the liquid fraction once per time step
    nCorrectors     2;
    nNonOrthogonalCorrectors 0;
    pRefPoint       PREF;
    pRefValue       1e5;
}
""".replace("PREF", pref))
    # volume averages over the PCM only (conducting fin cells are in the mesh)
    lf_region = "cellZone;\n        name            pcm" if conduct else "all"
    hot_patches = "(hot finroot)" if conduct else "(hot fins)" if fins else "(hot)"
    heat_fos = "".join(f"""    heat_{pn}
    {{
        type            surfaceFieldValue;
        libs            (fieldFunctionObjects);
        writeControl    timeStep;
        writeInterval   10;
        writeFields     false;
        regionType      patch;
        name            {pn};
        operation       areaIntegrate;
        fields          (wallHeatFlux);
    }}
""" for pn in (["hot", "finroot"] if conduct else ["hot", "fins"] if fins else ["hot"]))
    # stop once fully melted: runTimeControl minMax condition on the liquidFraction result
    # (v2606 source: mode maximum is satisfied when the value exceeds 'value'; action end
    # writes the final time and exits cleanly). A condition whose value is missing counts
    # as satisfied, so it only starts after 1 s, when liquidFraction has run.
    # (On a cellZone the result is named volAverage(<zone>,<field>).)
    stop_fo = "" if a.stop_at is None else f"""    stopAtMelt
    {{
        type            runTimeControl;
        libs            (utilityFunctionObjects);
        timeStart       1;
        conditions
        {{
            melted
            {{
                type            minMax;
                functionObject  liquidFraction;
                fields          ({'volAverage(pcm,melting:alpha1)' if conduct else 'volAverage(melting:alpha1)'});
                mode            maximum;
                value           {a.stop_at};
            }}
        }}
        satisfiedAction end;
    }}
"""
    write(f"{c}/system/controlDict", "dictionary", "controlDict", f"""application     buoyantPimpleFoam;
startFrom       startTime;
startTime       0;
stopAt          endTime;
endTime         {a.end};
deltaT          0.001;
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
maxCo           {a.maxco};
maxDeltaT       {a.maxdt};

functions
{{
    liquidFraction
    {{
        type            volFieldValue;
        libs            (fieldFunctionObjects);
        executeControl  timeStep;   // every step, so stopAtMelt always has a value
        executeInterval 1;
        writeControl    timeStep;
        writeInterval   10;
        writeFields     false;
        regionType      {lf_region};
        operation       volAverage;
        fields          (melting:alpha1 T);
    }}
    // wallHeatFlux writes its field at every write step (writeFields is ignored), which
    // made a time directory every 10 steps: compute it every step, write it only with the
    // fields, and log the heat rate per heated patch with surfaceFieldValue instead
    wallHeat
    {{
        type            wallHeatFlux;
        libs            (fieldFunctionObjects);
        executeControl  timeStep;
        executeInterval 1;
        writeControl    writeTime;
        patches         {hot_patches};
    }}
{heat_fos}
    maxU
    {{
        type            fieldMinMax;
        libs            (fieldFunctionObjects);
        writeControl    timeStep;
        writeInterval   10;
        mode            magnitude;
        fields          (U);
    }}
{stop_fo}}}
""")
    dT = tw - Tm
    nu, alpha = p["mu"] / p["rho"], p["k"] / (p["rho"] * p["cp"])
    meta = {
        "case": os.path.basename(os.path.normpath(c)), "family": "pcm_melting",
        "generator": "make_pcm_case.py", "openfoam": "v2606", "solver": "buoyantPimpleFoam",
        "model": "enthalpy-porosity (solidificationMeltingSource), constant properties, Boussinesq buoyancy",
        "material": a.material, "props": {k: v for k, v in p.items() if k != "source"},
        "props_source": p["source"],
        "mesh_h_m": h, "nx": nx, "ny": ny, "cells": n_fluid, "x_breaks": xs, "y_breaks": ys,
        "W_m": W, "H_m": H, "right": a.right, "top": a.top, "tilt_deg": a.tilt, "g": [gx, gy, 0.0],
        "nfins": a.nfins, "fin_len_m": a.fin_len if fins else 0.0, "fin_t_m": a.fin_t if fins else 0.0,
        "fins_y_m": fins, "fins_model": (f"conducting, k = {a.k_fin} W/m K (cellZone fin, PCM rho cp)"
                                      if conduct else "isothermal at T_wall") if fins else None,
        "fin_cells_in_mesh": conduct, "k_fin": a.k_fin if conduct else None,
        "T_wall_K": tw, "T_init_K": t0, "Tmelt_K": Tm, "T_wall_warmup_tau_s": a.tw_tau,
        "melt_model": "range (coded Voller-Swaminathan)" if mr else "isothermal (solidificationMeltingSource)",
        "T_solidus_K": mr[0] if mr else Tm, "T_liquidus_K": mr[1] if mr else Tm,
        "Cu": a.Cu, "q": a.q, "relax": a.relax, "maxCo": a.maxco, "maxDeltaT_s": a.maxdt,
        "end_time_s": a.end, "write_interval_s": a.write, "stop_at_liquid_fraction": a.stop_at,
        "Ra_H": 9.81 * p["beta"] * dT * H ** 3 / (nu * alpha), "Ste": p["cp"] * dT / p["L"],
        "Pr": p["Pr"], "aspect_ratio_H_W": H / W, "subcooling_K": Tm - t0,
    }
    with open(f"{c}/case.json", "w") as f:
        json.dump(meta, f, indent=1)
    print(f"case={c} {nx}x{ny} h={h} cells={n_fluid}{f'+{n_fin} fin' if conduct else ''} fins={a.nfins} Tw={a.tw}C T0={a.t0}C "
          f"Ra={meta['Ra_H']:.3g} Ste={meta['Ste']:.3f} Pr={meta['Pr']:.1f} A={H / W:g}")


if __name__ == "__main__":
    main()
