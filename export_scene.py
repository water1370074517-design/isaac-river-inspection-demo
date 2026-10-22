"""Export self-contained USDA; Python standard library only."""
import argparse
import json
from pathlib import Path
from scene_spec import scene, PALETTE, ROUTE, SITES

def vec(values):
    return '('+', '.join(f'{float(v):.6f}' for v in values)+')'

def canonical(value):
    if isinstance(value,float): return round(value,6)
    if isinstance(value,(tuple,list)): return [canonical(x) for x in value]
    if isinstance(value,dict): return {k:canonical(v) for k,v in value.items()}
    return value

def export(path,fleet_mode=False):
    lines=['#usda 1.0','(','defaultPrim = "River"','upAxis = "Z"','metersPerUnit = 1',')',
           'def Xform "River" {', 'def Scope "Looks" {']
    if fleet_mode:
        from fleet_spec import fleet_scene
        objects=fleet_scene()
    else: objects=scene()
    colors=list(dict.fromkeys(tuple(o.color) for o in objects))
    for i,c in enumerate(colors):
        water=c==PALETTE['water'] or c==PALETTE['shallows']
        lines += [f'def Material "M{i}" {{',
          f'token outputs:surface.connect = </River/Looks/M{i}/Shader.outputs:surface>',
          'def Shader "Shader" { uniform token info:id = "UsdPreviewSurface"',
          f'color3f inputs:diffuseColor = {vec(c)}',
          f'float inputs:roughness = {0.22 if water else 0.78}',
          'float inputs:metallic = 0', 'token outputs:surface', '}', '}']
    lines += ['}', 'def Scope "Geometry" {']
    for o in objects:
        kind={'cube':'Cube','cylinder':'Cylinder','cone':'Cone','sphere':'Sphere','mesh':'Mesh'}[o.kind]
        prim_name=o.name.replace('-','n')
        lines += [f'def {kind} "{prim_name}" (prepend apiSchemas = ["MaterialBindingAPI"]) {{',
                  f'rel material:binding = </River/Looks/M{colors.index(tuple(o.color))}>']
        if o.kind=='mesh':
            lines += ['point3f[] points = ['+', '.join(vec(p) for p in o.points)+']',
                      'int[] faceVertexCounts = ['+', '.join(str(len(f)) for f in o.faces)+']',
                      'int[] faceVertexIndices = ['+', '.join(str(i) for f in o.faces for i in f)+']',
                      'uniform token subdivisionScheme = "none"','uniform bool doubleSided = true']
        else:
            if o.kind=='cube': lines += ['double size = 1']
            elif o.kind in ('cylinder','cone'): lines += ['double radius = 1','double height = 1','uniform token axis = "Z"']
            else: lines += ['double radius = 1']
            lines += [f'double3 xformOp:translate = {vec(o.xyz)}',
                      f'float xformOp:rotateZ = {o.yaw:.6f}',
                      f'double3 xformOp:scale = {vec(o.scale)}',
                      'uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:rotateZ", "xformOp:scale"]']
        lines += ['}']
    lines += ['}', '}']
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    content='\n'.join(lines)+'\n'
    if not path.exists() or path.read_text(encoding='utf-8')!=content:
        path.write_text(content,encoding='utf-8')
    metadata={'coordinate_frame':'ENU, metres, Z up',
        'objects':len(objects),'route_enu_m':ROUTE,'inspection_sites':SITES,
        'water':'visual surface; flat ground collider, no hydrodynamics',
        'route':'visual guide only; never animates the PX4 vehicle','fleet_mode':fleet_mode}
    if fleet_mode:
        from fleet_spec import fleet,BRIDGE_TARGET,PERSON_TARGET
        metadata.update(aircraft=[a.manifest() for a in fleet()],shore_site_shift_m={'P3':[-10,0,0]},
                        landmarks={'bridge_target_m':BRIDGE_TARGET,'person_target_m':PERSON_TARGET})
    path.with_suffix('.json').write_text(json.dumps(canonical(metadata),indent=2),encoding='utf-8')
    return len(objects)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=Path(__file__).parent/'assets/river.usda')
    p.add_argument('--fleet',action='store_true')
    args=p.parse_args(); print(f'Exported {export(args.output,args.fleet)} native USD objects: {args.output}')
