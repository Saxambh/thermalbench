buoyancyTurbSource: incompressible (Boussinesq) k source has the opposite sign to the compressible branch and to the buoyancy production term

### Summary

In `src/fvOptions/sources/derived/buoyancyTurbSource/buoyancyTurbSource.C`, the incompressible k source appears to have the wrong sign:

```cpp
// B() (BMA: Eq. 8)
return beta_*alphat()*(fvc::grad(T) & g_)();
...
// (BMA: Eq. 5)
eqn -= fvm::Sp(B()/(k() + k0), k);
```

`g_` is the gravity vector from `meshObjects::gravity`, e.g. (0 -9.81 0), so `B` is the buoyancy production G_b = beta (nu_t/Pr_t) (grad T · g).
- G_b is negative in a stable stratification (hot fluid above cold) and positive in an unstable one.
- `eqn -= fvm::Sp(B/k, k)` puts −B on the right-hand side of the k equation.
- So the source adds turbulent kinetic energy in stable stratification and removes it in unstable stratification.

The compressible branch in `buoyancyTurbSourceTemplates.C` handles the same physics with the opposite net sign:

```cpp
GbByK((nut/Prt)*(fvc::grad(rho) & g_)/max(k, k0));
eqn -= fvm::Sp(GbByK, k);
```

This gives −(nu_t/Pr_t)(grad rho · g). With grad rho = −rho beta grad T, that is +rho B. The two branches therefore apply opposite signs to the same buoyancy production.

The lines are unchanged in current develop (checked 2026-11-01) and have been present since the option was added (v2012).

### Steps to reproduce

Attached: `buoyancyTurbSourceSign_case.tgz`. It contains a closed 2D box, 1 m x 1 m with 100 x 100 cells, run with buoyantBoussinesqPimpleFoam and kOmegaSST.
- The fluid starts at rest.
- The temperature profile is linear and stable, 20 to 60 C (40 K/m).
- Initial turbulence is uniform: k = 1e-4, omega = 1.

`./Allrun` runs it with and without the fvOption and prints the domain-mean dk/dt over the first 0.25 s.

### What is the current *bug* behaviour?

v2606 output:

```
without  mean dk/dt over 0.25 s: -1.260e-05 m2/s3
with     mean dk/dt over 0.25 s: +2.407e-06 m2/s3
```

The fvOption changes dk/dt by +1.50e-5 m2/s3. The analytic buoyancy production at t = 0 is G_b = beta nu_t/Pr_t (grad T · g) = 3.5e-4 x 1e-4/0.85 x (40 x −9.81) = −1.62e-5 m2/s3. The measured change has the same magnitude but the opposite sign.

We repeated this with the mirrored (unstable) profile, and with buoyantPimpleFoam using a polynomial rho(T) for water, which exercises the compressible branch. Each value is the measured change in dk/dt divided by the analytic G_b:

| solver / branch | stable | unstable |
|---|---|---|
| buoyantBoussinesqPimpleFoam (incompressible branch) | −0.93 | −0.91 |
| buoyantPimpleFoam (compressible branch) | +0.90 | +0.94 |

Over 20 s with the stable profile, mean k behaves as follows:

| case | mean k at 20 s |
|---|---|
| no source | 2.8e-5 |
| incompressible buoyancyTurbSource | 2.5e-4 (grows, although stable stratification should damp turbulence) |
| compressible branch | 4.9e-7 |
| incompressible with the sign reversed (our coded source) | 4.4e-7 |

### What is the expected *correct* behavior?

The k equation should receive +G_b, i.e. a sink in stable stratification and a source in unstable stratification, as the compressible branch already does.

### Relevant logs and/or images

See the tables above. Issue #2293 (buoyantBoussinesqPimpleFoam + kEpsilon + buoyancyTurbSource on hotRoom, where k and epsilon blew up) may have the same cause.

### Environment information

- OpenFOAM version: v2606 (also present in v2012 and current develop)
- Operating system: Ubuntu 24.04 (WSL2)
- Hardware info: not relevant
- Compiler: gcc 13 (packaged build)

### Possible fixes

```cpp
eqn += fvm::SuSp(-B()/(k() + k0), k);
```

Or equivalent, i.e. +B on the right-hand side: implicit where B < 0, which keeps k >= 0, and explicit where B > 0.

The omega and epsilon terms use the same `eqn -= ... B()` pattern and may need the same review. Separately, in the epsilon term BMA's C3 = tanh|v/u| uses v as the velocity component parallel to gravity, whereas the code uses `tanh(mag(u/v))` with v = gHat & U. We have not verified this against the paper, so it is mentioned only as something to check.
