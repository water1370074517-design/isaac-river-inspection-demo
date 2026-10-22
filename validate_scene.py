"""Validate the native USD asset with pxr (use Isaac's python.sh)."""
import argparse
from pathlib import Path

def validate_text(text):
    from pxr import Usd, UsdGeom, UsdShade, Sdf
    stage=Usd.Stage.CreateInMemory()
    if not stage.GetRootLayer().ImportFromString(text): raise RuntimeError('USD import failed')
    if stage.GetDefaultPrim().GetName()!='River': raise RuntimeError('Missing River default prim')
    count=0; meshes=0
    for prim in stage.Traverse():
        if not prim.IsA(UsdGeom.Gprim): continue
        count+=1
        binding=UsdShade.MaterialBindingAPI(prim).GetDirectBindingRel().GetTargets()
        if not binding or not stage.GetPrimAtPath(binding[0]): raise RuntimeError(f'Unresolved material: {prim.GetPath()}')
        if prim.IsA(UsdGeom.Mesh):
            meshes+=1; mesh=UsdGeom.Mesh(prim)
            points=mesh.GetPointsAttr().Get(); indices=mesh.GetFaceVertexIndicesAttr().Get()
            counts=mesh.GetFaceVertexCountsAttr().Get()
            if sum(counts)!=len(indices) or max(indices)>=len(points): raise RuntimeError('Invalid mesh topology')
    if count<500: raise RuntimeError('Scene geometry unexpectedly incomplete')
    return {'usd_parse':'PASS','native_geometry':count,'meshes':meshes,'external_assets':False}

if __name__=='__main__':
    import json
    import importlib.util
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--asset',type=Path,default=Path(__file__).parent/'assets/river.usda')
    p.add_argument('--report',type=Path,help='Write the validation result as JSON')
    args=p.parse_args(); app=None
    try:
        # Isaac 5.1 exposes USD through Kit extensions after runtime startup.
        # A standalone usd-core installation does not need this initialization.
        if importlib.util.find_spec('pxr') is None:
            from isaacsim import SimulationApp
            app=SimulationApp({'headless':True,'width':64,'height':64,
                'multi_gpu':False,'disable_viewport_updates':True})
        result=validate_text(args.asset.read_text(encoding='utf-8'))
        if args.report:
            args.report.parent.mkdir(parents=True,exist_ok=True)
            args.report.write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(json.dumps(result,indent=2),flush=True)
    finally:
        if app: app.close()
