# pvbatch script: geometry and mesh pictures of the ThermalStorageBench 2D tanks and the 3D Lou tank.
# Usage: pvbatch viz_mesh.py <viz_dir>
import os
import sys

from paraview.simple import *

V = sys.argv[1]
OUT = os.path.join(V, "png")
os.makedirs(OUT, exist_ok=True)
GREY, EDGE = [0.93, 0.93, 0.93], [0.25, 0.25, 0.3]
RED, BLUE, GOLD = [0.85, 0.2, 0.15], [0.15, 0.35, 0.85], [0.95, 0.65, 0.1]


def reader(case, regions):
    r = OpenFOAMReader(FileName=os.path.join(V, case, case + ".foam"))
    avail = r.GetProperty("MeshRegions").Available
    pick = [a for a in avail if any(a == g or a.endswith("/" + g) for g in regions)]
    r.MeshRegions = pick
    r.UpdatePipeline()
    return r, avail


def view(w=1600, h=1200):
    v = CreateRenderView()
    v.ViewSize = [w, h]
    v.OrientationAxesVisibility = 0
    v.Background = [1, 1, 1]
    try:
        v.UseColorPaletteForBackground = 0
    except AttributeError:
        pass
    return v


def show(src, v, color, rep="Surface", opacity=1.0, lw=1.0, edges=False):
    d = Show(src, v)
    d.SetRepresentationType(rep)
    d.ColorArrayName = ["POINTS", ""]
    d.AmbientColor = d.DiffuseColor = color
    d.Opacity = opacity
    d.LineWidth = lw
    if edges:
        d.EdgeColor = EDGE
    return d


def save(v, name):
    Render(v)
    SaveScreenshot(os.path.join(OUT, name), v, ImageResolution=v.ViewSize)
    print("wrote", name)


def camera2d(v, b, pad=0.03):
    """Parallel view from +z onto bounds b=(x0,x1,y0,y1,z0,z1)."""
    cx, cy, cz = (b[0] + b[1]) / 2, (b[2] + b[3]) / 2, (b[4] + b[5]) / 2
    v.CameraPosition = [cx, cy, cz + 10]
    v.CameraFocalPoint = [cx, cy, cz]
    v.CameraViewUp = [0, 1, 0]
    v.CameraParallelProjection = 1
    aspect = v.ViewSize[0] / v.ViewSize[1]
    v.CameraParallelScale = max((b[3] - b[2]) / 2, (b[1] - b[0]) / 2 / aspect) * (1 + pad)


# ---------- 2D tanks: whole tank + zoom on each port ----------
for case in ("tankA", "tankB"):
    mesh, avail = reader(case, ["internalMesh"])
    print(case, "regions:", list(avail))
    ports = {p: reader(case, [p])[0] for p in ("inlet", "outlet")}
    b = mesh.GetDataInformation().GetBounds()
    v = view(1200, 1300)
    show(mesh, v, GREY, "Surface With Edges", edges=True)
    show(ports["inlet"], v, RED, "Surface", lw=6).SetRepresentationType("Wireframe")
    show(ports["outlet"], v, BLUE, "Surface", lw=6).SetRepresentationType("Wireframe")
    for p in ports.values():
        GetDisplayProperties(p, v).LineWidth = 8
    camera2d(v, b)
    save(v, f"{case}_mesh_full.png")
    for p, src in ports.items():
        pb = src.GetDataInformation().GetBounds()
        cx, cy = (pb[0] + pb[1]) / 2, (pb[2] + pb[3]) / 2
        half = 0.06
        # keep the zoom window inside the tank
        cx = min(max(cx, b[0] + half), b[1] - half)
        cy = min(max(cy, b[2] + half), b[3] - half)
        camera2d(v, (cx - half, cx + half, cy - half, cy + half, b[4], b[5]), pad=0)
        save(v, f"{case}_mesh_{p}_zoom.png")
    Delete(v)

# ---------- 3D Lou tank (quarter domain, mirrored to the full tank for the geometry views) ----------
mesh3, avail3 = reader("lou3d", ["internalMesh"])
print("lou3d regions:", list(avail3))
patch = {p: reader("lou3d", [p])[0] for p in ("walls", "top", "bottom", "baffle", "inlet", "outlet")}


def full(src):
    r1 = Reflect(Input=src, Plane="X Min", CopyInput=1)
    return Reflect(Input=r1, Plane="Z Min", CopyInput=1)


# (a) geometry: translucent shell, baffles, ports
v = view(1400, 1600)
show(full(patch["walls"]), v, [0.6, 0.7, 0.8], opacity=0.12)
show(full(patch["top"]), v, [0.6, 0.7, 0.8], opacity=0.12)
show(full(patch["bottom"]), v, [0.6, 0.7, 0.8], opacity=0.12)
show(full(patch["baffle"]), v, GOLD)
show(full(patch["inlet"]), v, RED)
show(full(patch["outlet"]), v, BLUE)
show(full(patch["walls"]), v, [0.3, 0.35, 0.45], "Feature Edges")
v.CameraPosition = [0.55, 0.62, 0.55]
v.CameraFocalPoint = [0, 0.195, 0]
v.CameraViewUp = [0, 1, 0]
ResetCamera(v)
v.CameraParallelProjection = 0
GetActiveCamera().Zoom(1.15)
save(v, "lou3d_geometry.png")
Delete(v)

# (b) upper baffle seen from above, with its mesh (holes)
up = Clip(Input=patch["baffle"], ClipType="Plane")
up.ClipType.Origin = [0, 0.2, 0]
up.ClipType.Normal = [0, 1, 0]
up.Invert = 0
v = view(1400, 1400)
show(full(up), v, GOLD, "Surface With Edges", edges=True)
v.CameraPosition = [0, 1.5, 0]
v.CameraFocalPoint = [0, 0.36, 0]
v.CameraViewUp = [0, 0, -1]
v.CameraParallelProjection = 1
v.CameraParallelScale = 0.102
save(v, "lou3d_baffle_top.png")
Delete(v)

# (c) symmetry-plane slice z = 0 with the mesh: whole height and zoom on the upper manifold
sl = Slice(Input=mesh3)
sl.SliceType = "Plane"
sl.SliceType.Origin = [0, 0, 0.0001]
sl.SliceType.Normal = [0, 0, 1]
sl.Triangulatetheslice = 0
v = view(700, 1500)
show(sl, v, GREY, "Surface With Edges", edges=True)
show(patch["inlet"], v, RED)
show(patch["outlet"], v, BLUE)
b = sl.GetDataInformation().GetBounds()
camera2d(v, b)
save(v, "lou3d_slice_full.png")
v.ViewSize = [1400, 1000]
camera2d(v, (0, 0.097, 0.32, 0.39, b[4], b[5]), pad=0.02)
save(v, "lou3d_slice_top_zoom.png")
camera2d(v, (0, 0.097, 0.0, 0.05, b[4], b[5]), pad=0.02)
save(v, "lou3d_slice_bottom_zoom.png")
