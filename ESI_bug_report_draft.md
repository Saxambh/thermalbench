# Draft issue for develop.openfoam.com (Saxam to post under his name)

**Where to post.** ESI's repository has moved to **https://gitlab.com/openfoam/core/openfoam** (develop.openfoam.com no longer responds). New issue: https://gitlab.com/openfoam/core/openfoam/-/issues/new. A gitlab.com account is needed.

**Checks done (1 Nov 2026):**
1. **develop branch:** head commit 2026-10-28. The relevant lines in buoyancyTurbSource.C and buoyancyTurbSourceTemplates.C are identical to v2606. The last commit touching the directory was 2024-01-11 (gcc-13 warnings), so the sign has never been changed since the option was added (2020-12-08).
2. **Issue tracker:** only two issues mention buoyancyTurbSource.
   - #3131 is about interFoam selecting the wrong addSup. It does not concern the sign.
   - #2293 (2021) is probably this bug. buoyantBoussinesqPimpleFoam + kEpsilon + buoyancyTurbSource on the hotRoom tutorial: k and epsilon blew up and the run crashed. The developer found "no programmatic error" and suggested a smaller time step. That issue was closed without a cause.
   - Searches for sign-related terms found nothing.
3. **Attachment ready:** `buoyancyTurbSourceSign_case.tgz` (3 KB, in this folder). It is a standalone case whose `./Allrun` runs with and without the fvOption.
   - Tested on v2606: without the fvOption, dk/dt = −1.26e-5; with it, +2.41e-6. The difference, +1.50e-5, is the opposite sign of Gb = −1.62e-5.

---

**Title:** buoyancyTurbSource: incompressible (Boussinesq) k source has the opposite sign to the compressible branch and to the buoyancy production term

**Version:** OpenFOAM v2606 and current develop (checked 2026-11-01); present since the option was added in v2012.

**Possibly related:** #2293. A buoyantBoussinesqPimpleFoam hotRoom case with this fvOption blew up through runaway k/epsilon; it was closed with the cause unknown. A k source with reversed sign in stable stratification would produce exactly that runaway.

**Summary**

In `src/fvOptions/sources/derived/buoyancyTurbSource/buoyancyTurbSource.C` the incompressible k source is

```cpp
// B() (BMA: Eq. 8)
return beta_*alphat()*(fvc::grad(T) & g_)();
...
// (BMA: Eq. 5)
eqn -= fvm::Sp(B()/(k() + k0), k);
```

with `g_` the gravity vector from `meshObjects::gravity` (e.g. (0 -9.81 0)). `B` is the buoyancy production G_b = beta (nu_t/Pr_t) (grad T · g). It is negative in a stable stratification (hot fluid above cold) and positive in an unstable one. Since `eqn -= fvm::Sp(B/k, k)` puts **−B** on the right-hand side of the k equation, the source **adds** turbulent kinetic energy in stable stratification and **removes** it in unstable stratification. This is the reverse of the physical effect.

The compressible branch in `buoyancyTurbSourceTemplates.C` handles the same physics with the opposite net sign:

```cpp
GbByK((nut/Prt)*(fvc::grad(rho) & g_)/max(k, k0));
eqn -= fvm::Sp(GbByK, k);
```

This gives −(nu_t/Pr_t)(grad rho · g). With grad rho = −rho beta grad T (Boussinesq), that is +rho B. The two branches therefore apply opposite signs to the same buoyancy production.

**Test**

Closed 2D box (1 m x 1 m, 100 x 100 cells), fluid at rest, linear temperature profile with 40 K/m (stable: hot on top; unstable: hot at the bottom), uniform k = 1e-4 m2/s2, omega = 1 1/s, kOmegaSST. We measured the initial domain-mean dk/dt over 0.25 s with and without `buoyancyTurbSource`, and compared the difference with the analytic G_b at t = 0 (nu_t = k/omega, Pr_t = 0.85):

| solver | stratification | measured change in dk/dt (m2/s3) | analytic G_b (m2/s3) | ratio |
|---|---|---|---|---|
| buoyantBoussinesqPimpleFoam (beta 3.5e-4) | stable | +1.50e-05 | −1.62e-05 | −0.93 |
| buoyantBoussinesqPimpleFoam | unstable | −1.47e-05 | +1.62e-05 | −0.91 |
| buoyantPimpleFoam (water, polynomial rho(T)) | stable | −1.57e-05 | −1.75e-05 | +0.90 |
| buoyantPimpleFoam | unstable | +1.64e-05 | +1.75e-05 | +0.94 |

The compressible branch reproduces +G_b. The incompressible branch reproduces −G_b.

In a longer run (20 s, stable profile), mean k went from 1e-4 to:

| case | mean k at 20 s |
|---|---|
| no buoyancy source | 2.8e-5 |
| buoyantBoussinesqPimpleFoam + buoyancyTurbSource | 2.5e-4 (grows, although stable stratification should damp turbulence) |
| Boussinesq, same term with corrected sign (scalarCodedSource) | 4.4e-7 |
| buoyantPimpleFoam + buoyancyTurbSource | 4.9e-7 |

**Suggested fix**

`eqn += fvm::SuSp(-B()/(k() + k0), k);` or equivalent, i.e. the k equation gets +B. That is implicit where B < 0 (stable, keeps k >= 0) and explicit where B > 0.

The omega and epsilon terms use the same `eqn -= ... B()` pattern and may need the same review. (In the epsilon term, BMA's C3 = tanh|v/u| with v the velocity component parallel to gravity, whereas the code uses `tanh(mag(u/v))` with v = gHat & U. We have not checked this against the paper, so it is mentioned only as something to check.)

## Posted

Posted 2026-11-01 by Saxam (GitLab user saxambhattarai1) as issue #3645: https://gitlab.com/openfoam/core/openfoam/-/work_items/3645 (case .tgz attached in the Steps section).
