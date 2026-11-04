# pvbatch: upper vs lower baffle from above, same scale, with cell edges
import os, sys
from paraview.simple import *
V = sys.argv[1]
r = OpenFOAMReader(FileName=os.path.join(V, "lou3d", "lou3d.foam"))
r.MeshRegions = ["patch/baffle"]
for name, keep_upper in (("upper", 0), ("lower", 1)):
    c = Clip(Input=r, ClipType="Plane")
    c.ClipType.Origin = [0, 0.2, 0]
    c.ClipType.Normal = [0, 1, 0]
    c.Invert = keep_upper
    # top face of each plate only, seen from above
    v = CreateRenderView(); v.ViewSize = [1200, 1200]; v.OrientationAxesVisibility = 0
    v.Background = [1, 1, 1]
    try: v.UseColorPaletteForBackground = 0
    except AttributeError: pass
    d = Show(c, v); d.SetRepresentationType("Surface With Edges"); d.ColorArrayName = ["POINTS", ""]
    d.DiffuseColor = d.AmbientColor = [0.95, 0.65, 0.1]; d.EdgeColor = [0.25, 0.25, 0.3]
    v.CameraPosition = [0.05, 1.5, 0.05]; v.CameraFocalPoint = [0.05, 0.2, 0.05]; v.CameraViewUp = [0, 0, -1]
    v.CameraParallelProjection = 1; v.CameraParallelScale = 0.05
    Render(v)
    SaveScreenshot(os.path.join(V, "png", f"lou3d_baffle_{name}_quarter.png"), v, ImageResolution=[1200, 1200])
    print("wrote", name, c.GetDataInformation().GetNumberOfCells(), "faces")
