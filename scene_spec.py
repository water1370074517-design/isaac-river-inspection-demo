"""Deterministic, offline river scene. Metres, ENU, Z up; no Isaac imports."""
from dataclasses import dataclass
import math
import random

PALETTE = {
    'grass': (0.32, 0.46, 0.30), 'grass_light': (0.43, 0.55, 0.34),
    'sand': (0.69, 0.65, 0.46), 'water': (0.035, 0.36, 0.43),
    'shallows': (0.13, 0.49, 0.49), 'ripple': (0.43, 0.72, 0.71),
    'path': (0.78, 0.75, 0.65), 'white': (0.93, 0.94, 0.86),
    'bark': (0.26, 0.22, 0.16), 'leaf': (0.17, 0.34, 0.23),
    'leaf_light': (0.27, 0.44, 0.25), 'slate': (0.14, 0.23, 0.26),
    'orange': (0.98, 0.48, 0.16), 'route': (0.35, 0.92, 0.91),
    'blue': (0.12, 0.43, 0.67), 'solar': (0.12, 0.22, 0.32),
}

# ENU offsets from the launch pad. Bridge top < 4 m, survey altitude >= 8 m.
ROUTE = [(0., 0., 8.), (12., 14., 9.), (20., 32., 9.),
         (15., 50., 10.), (14., 70., 10.), (24., 92., 10.),
         (31., 90., 11.), (28., 66., 11.), (29., 36., 11.),
         (0., 0., 9.)]
SITES = [('P1', 14., 24.), ('P2', 14., 51.), ('P3', 21., 79.)]

@dataclass
class Shape:
    name: str
    kind: str
    xyz: tuple
    scale: tuple
    color: tuple
    yaw: float = 0.
    points: list | None = None
    faces: list | None = None

def river_x(y):
    return 17. + 5.2 * math.sin(y / 14.) + 2.2 * math.sin(y / 7.5)

def scene():
    objects = []
    def add(name, kind, xyz, scale, color, yaw=0., points=None, faces=None):
        objects.append(Shape(name, kind, tuple(xyz), tuple(scale),
                             PALETTE.get(color, color), yaw, points, faces))
    def box(name, xyz, scale, color, yaw=0.):
        add(name, 'cube', xyz, scale, color, yaw)
    def strip(name, width, z, color):
        pts = [(river_x(y)+side*width/2, y, z) for y in range(-18, 121, 2)
               for side in (-1, 1)]
        faces = [(i, i+1, i+3, i+2) for i in range(0, len(pts)-2, 2)]
        add(name, 'mesh', (0,0,0), (1,1,1), color, points=pts, faces=faces)
    box('Terrain', (10,50,-.25), (112,150,.5), 'grass')
    strip('Riverbank', 18., .018, 'sand')
    strip('ShallowWater', 14.3, .035, 'shallows')
    strip('RiverWater', 12.5, .05, 'water')
    # Left-bank path follows the river; line segments have actual widths.
    for j, y in enumerate(range(-10,110,2)):
        a, b = (river_x(y)-13,y,.055), (river_x(y+2)-13,y+2,.055)
        segment(objects, f'Path{j}', a, b, .95, PALETTE['path'], flat=True)
    rng = random.Random(481)
    for j in range(95):
        y = rng.uniform(-12,113)
        side = rng.choice((-1,1))
        x = river_x(y) + side*rng.uniform(17,40)
        if math.hypot(x, y) < 11 or (x < 2 and y < 15):
            continue
        h, r = rng.uniform(2.6,5.7), rng.uniform(1.2,2.0)
        add(f'Trunk{j}', 'cylinder', (x,y,h*.24), (.19,.19,h*.48), 'bark')
        for k in range(3):
            add(f'Crown{j}_{k}', 'cone', (x,y,h*(.45+k*.17)),
                (r*(1-k*.17),r*(1-k*.17),h*.48),
                'leaf' if j%3 else 'leaf_light')
    # Local material water highlights, no texture servers or water solver.
    for j in range(76):
        y=rng.uniform(-12,113); x=river_x(y)+rng.uniform(-5,5)
        box(f'Ripple{j}', (x,y,.065), (rng.uniform(.4,1.6),.045,.008), 'ripple', -12)
    # Launch apron and helipad at the world origin.
    box('Apron', (0,0,.07), (10,10,.10), 'path')
    add('Helipad', 'cylinder', (0,0,.14), (3.25,3.25,.04), 'slate')
    for i in range(48):
        a=i*math.tau/48; b=(i+.65)*math.tau/48
        segment(objects, f'PadRing{i}', (2.8*math.cos(a),2.8*math.sin(a),.17),
                (2.8*math.cos(b),2.8*math.sin(b),.17), .10, PALETTE['orange'], flat=True)
    box('H1', (-.7,0,.18), (.20,2.1,.025), 'white')
    box('H2', (.7,0,.18), (.20,2.1,.025), 'white')
    box('H3', (0,0,.18), (1.4,.20,.025), 'white')
    # Edge station: service building, deck, solar panels, mast.
    box('StationDeck', (-7,7,.15), (8,7,.3), 'path')
    box('Station', (-7,7,1.35), (5,3.8,2.4), 'white')
    box('StationRoof', (-7,7,2.7), (5.5,4.2,.28), 'slate')
    for j in range(3):
        box(f'Window{j}', (-8.6+j*1.35,5.08,1.55), (.9,.05,1.05), 'blue')
        box(f'Solar{j}', (-8.6+j*1.6,7,2.91), (1.35,2.7,.12), 'solar')
    add('Mast', 'cylinder', (-10,9,3.), (.12,.12,6.), 'white')
    for j in range(2):
        box(f'Antenna{j}', (-10+.45*j,9,5.35), (.15,.8,.65), 'orange')
    # A low pedestrian bridge, with rails and piers; outside the flight corridor height.
    bx, by = river_x(57), 57.
    box('BridgeDeck', (bx,by,2.6), (25,2.6,.42), 'path')
    # Bridge approaches meet both the deck surface and the existing flat shore.
    # Closed wedge prisms retain a continuous walking surface, with no floating ends.
    for side in (-1,1):
        inner=bx+side*12.5; outer=inner+side*9.
        points=[(x,by+dy,z) for x,top in ((inner,2.81),(outer,.08))
                for z in (-.025,top) for dy in (-1.5,1.5)]
        faces=[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)]
        add(f'BridgeRamp{side}','mesh',(0,0,0),(1,1,1),'path',points=points,faces=faces)
    for sign in (-1,1):
        box(f'BridgeRail{sign}', (bx,by+sign*1.25,3.2), (25,.10,.12), 'white')
        for j in range(11):
            box(f'BridgePost{sign}_{j}', (bx-12+j*2.4,by+sign*1.25,2.98), (.10,.10,.8), 'slate')
    for j, dx in enumerate((-8,8)):
        box(f'Pier{j}', (bx+dx,by,1.3), (.7,1.8,2.6), 'slate')
    for name,x,y in SITES:
        add(name+'Pad', 'cylinder', (x-12,y,.12), (1.6,1.6,.16), 'orange')
        add(name+'Pole', 'cylinder', (x-12,y,1.5), (.08,.08,2.8), 'slate')
        box(name+'Sensor', (x-12,y,2.9), (.6,.45,.5), 'white')
        label(objects, name, (x-14,y-2,.15), .65, PALETTE['white'])
    # Clearly marked debris proxy: a predefined task location, not a model detection.
    for j in range(7):
        box(f'Debris{j}', (river_x(80)+rng.uniform(-3,3),80+rng.uniform(-2,2),.16),
            (.5,.25,.16), 'orange', rng.uniform(0,180))
    label(objects,'BASE',(-2,-5,.14), .50, PALETTE['white'])
    label(objects,'EDGE',(-9,3,.15), .50, PALETTE['slate'])
    # Survey guide: dashed ground projection, elevated path and waypoint rings.
    for j,(a,b) in enumerate(zip(ROUTE,ROUTE[1:])):
        distance=math.dist(a,b); steps=max(1,int(distance/2.8))
        for k in range(steps):
            u=k/steps; v=min(1,(k+.53)/steps)
            p=tuple(a[i]+u*(b[i]-a[i]) for i in range(3))
            q=tuple(a[i]+v*(b[i]-a[i]) for i in range(3))
            segment(objects,f'Route{j}_{k}',p,q,.10,PALETTE['route'])
    for j,p in enumerate(ROUTE[1:-1],1):
        add(f'Waypoint{j}','sphere',p,(.32,.32,.32),'orange')
    return objects

def segment(objects,name,a,b,width,color,flat=False):
    dx,dy,dz=[b[i]-a[i] for i in range(3)]
    # Scene paths are horizontal; cylinders for the elevated, sloped guide are
    # emitted as explicit mesh prisms to avoid rotation-order ambiguity.
    length=math.hypot(dx,dy)
    if length < 1e-9: return
    nx,ny=-dy/length*width/2,dx/length*width/2
    h=.01 if flat else width
    pts=[(p[0]+s*nx,p[1]+s*ny,p[2]+z) for z in (-h/2,h/2)
         for p in (a,b) for s in (-1,1)]
    faces=[(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)]
    objects.append(Shape(name,'mesh',(0,0,0),(1,1,1),tuple(color),points=pts,faces=faces))

FONT={'P':['1110','1001','1110','1000','1000'],
      'U':['101','101','101','101','111'],
      '4':['101','101','111','001','001'], '5':['111','100','111','001','111'],
      '1':['010','110','010','010','111'], '2':['111','001','111','100','111'],
      '3':['111','001','111','001','111'], 'B':['110','101','110','101','110'],
      'A':['010','101','111','101','101'], 'S':['111','100','111','001','111'],
      'E':['111','100','110','100','111'], 'D':['110','101','101','101','110'],
      'G':['111','100','101','101','111']}
def label(objects,text,origin,size,color):
    x,y,z=origin
    for c,char in enumerate(text):
        for row,line in enumerate(FONT[char]):
            for col,pixel in enumerate(line):
                if pixel=='1':
                    objects.append(Shape(f'Label{text}_{c}_{row}_{col}','cube',
                        (x+(c*5+col)*size*.25,y+(4-row)*size*.25,z),
                        (size*.22,size*.22,.018),color))

def route_position(fraction):
    if fraction<=0: return ROUTE[0]
    if fraction>=1: return ROUTE[-1]
    lengths=[math.dist(a,b) for a,b in zip(ROUTE,ROUTE[1:])]
    remaining=max(0,min(1,fraction))*sum(lengths)
    for a,b,d in zip(ROUTE,ROUTE[1:],lengths):
        if remaining<=d:
            return tuple(a[i]+remaining/d*(b[i]-a[i]) for i in range(3))
        remaining-=d
    return ROUTE[-1]

def enu_to_ned(point):
    x,y,z=point
    return (y,x,-z)
