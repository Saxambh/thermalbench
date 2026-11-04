# ParaView GUI start-up: 3D Lou tank geometry + mesh (open with paraview --script=viz_gui.py)
import os
from paraview.simple import *

V = r"C:\Users\Saxam\AppData\Local\Temp\claude\C--Users-Saxam\9b6c9561-2c28-4e96-aceb-94a1b7f26d31\scratchpad\viz"
F = os.path.join(V, "lou3d", "lou3d.foam")


def part(name, regions):
    r = OpenFOAMReader(registrationName=name, FileName=F)
    r.MeshRegions = regions
    return r


def full(src, name):
    r1 = Reflect(registrationName=name + " (half)", Input=src, Plane="X Min", CopyInput=1)
    return Reflect(registrationName=name, Input=r1, Plane="Z Min", CopyInput=1)


def show(src, color, rep="Surface", opacity=1.0, visible=True):
    d = Show(src)
    d.SetRepresentationType(rep)
    d.ColorArrayName = ["POINTS", ""]
    d.AmbientColor = d.DiffuseColor = color
    d.Opacity = opacity
    if not visible:
        Hide(src)
    return d


v = GetActiveViewOrCreate("RenderView")
shell = full(part("quarter: walls", ["patch/walls", "patch/top", "patch/bottom"]), "Tank walls")
show(shell, [0.6, 0.7, 0.8], opacity=0.15)
show(full(part("quarter: baffles", ["patch/baffle"]), "Baffles (mesh)"), [0.95, 0.65, 0.1], "Surface With Edges")
show(full(part("quarter: inlet", ["patch/inlet"]), "Inlet port"), [0.85, 0.2, 0.15])
show(full(part("quarter: outlet", ["patch/outlet"]), "Outlet port"), [0.15, 0.35, 0.85])

mesh = part("quarter: fluid mesh", ["internalMesh"])
sl = Slice(registrationName="Mid-plane slice (mesh)", Input=mesh)
sl.SliceType.Origin = [0, 0, 0.0001]
sl.SliceType.Normal = [0, 0, 1]
sl.Triangulatetheslice = 0
show(sl, [0.93, 0.93, 0.93], "Surface With Edges")

for s in ("quarter: walls", "quarter: baffles", "quarter: inlet", "quarter: outlet", "quarter: fluid mesh",
          "Tank walls (half)", "Baffles (mesh) (half)", "Inlet port (half)", "Outlet port (half)"):
    Hide(FindSource(s), v)

v.OrientationAxesVisibility = 1
v.CameraPosition = [0.55, 0.62, 0.55]
v.CameraFocalPoint = [0, 0.195, 0]
v.CameraViewUp = [0, 1, 0]
ResetCamera(v)
Render(v)
