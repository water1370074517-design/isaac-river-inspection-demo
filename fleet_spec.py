"""One shore base, five sectors and scripted inspection landmarks (ENU metres)."""
from dataclasses import dataclass
import math
from scene_spec import Shape,scene,river_x,segment,label,PALETTE

@dataclass(frozen=True)
class Aircraft:
    instance: int
    namespace: str
    spawn: tuple
    color: tuple
    route_world: tuple

    @property
    def system_id(self): return self.instance+1
    @property
    def tcp_port(self): return 4560+self.instance
    @property
    def gcs_port(self): return 18570+self.instance
    @property
    def relative_route(self):
        return tuple((p[0]-self.spawn[0],p[1]-self.spawn[1],p[2]) for p in self.route_world)
    def manifest(self):
        return {'instance':self.instance,'system_id':self.system_id,'namespace':self.namespace,
            'tcp_port':self.tcp_port,'gcs_port':self.gcs_port,'spawn_enu':list(self.spawn),
            'route_world_enu':self.route_world,'relative_route_enu':self.relative_route,'color':self.color}

COLORS=((.20,.85,.91),(.98,.59,.18),(.56,.49,.98),(.24,.78,.48),(.95,.36,.57))

HOMES=((-24.,-6.,.24),(-16.,-6.,.24),(-8.,-6.,.24),(-20.,-14.,.24),(-12.,-14.,.24))
PATROL_HEIGHTS=(9.,12.,8.,17.,11.)
TRANSIT_HEIGHTS=(6.,10.5,15.,19.5,24.)
BRIDGE_TARGET=(river_x(57)-6.,57.,3.)
FISHER_POSITION=(river_x(100)+10.5,100.,.1)
PERSON_TARGET=(FISHER_POSITION[0],100.,1.25)

def sector_loop(i,bounds=None):
    lo,hi=bounds or ((i-1)*22.,i*22.)
    h=PATROL_HEIGHTS[i-1]
    # Smooth sampled ellipse follows the river; camera footprints overlap at boundaries.
    mid=(lo+hi)/2; radius=(hi-lo)/2-1.5
    return tuple((river_x(mid+radius*math.sin(t))-4*math.cos(t),mid+radius*math.sin(t),h)
        for t in (k*math.tau/12 for k in range(13)))

def fleet():
    return tuple(Aircraft(i,f'river_uav{i+1}',HOMES[i],COLORS[i],sector_loop(i+1)) for i in range(5))

def minimum_sector_gap():
    return 3.

def fleet_scene():
    aircraft=fleet(); objects=[]
    skip=('Route','Waypoint','PadRing','LabelBASE')
    for obj in scene():
        if obj.name.startswith(skip) or obj.name in ('Apron','Helipad','H1','H2','H3'): continue
        if obj.name.startswith(('Trunk','Crown')) and (-34<obj.xyz[0]<0 and -24<obj.xyz[1]<5): continue
        if obj.name.startswith('P3') or obj.name.startswith('LabelP3'):
            from dataclasses import replace
            obj=replace(obj,xyz=(obj.xyz[0]-10,obj.xyz[1],obj.xyz[2]))
        objects.append(obj)
    objects.append(Shape('Apron','cube',(-16,-10,.07),(26,20,.10),PALETTE['path']))
    for a in aircraft:
        x,y,_=a.spawn; n=a.system_id
        objects.append(Shape('Helipad' if n==1 else f'FleetPad{n}','cylinder',(x,y,.14),(3.1,3.1,.04),PALETTE['slate']))
        if n>1: objects.append(Shape(f'FleetApron{n}','cube',(x,y,.075),(6.6,6.6,.08),PALETTE['path']))
        for k,dx in enumerate((-.7,.7)):
            objects.append(Shape(f'FleetH{n}_{k}','cube',(x+dx,y,.19),(.2,2.1,.025),PALETTE['white']))
        objects.append(Shape(f'FleetHBar{n}','cube',(x,y,.19),(1.4,.2,.025),PALETTE['white']))
        for j in range(32):
            u=j*math.tau/32; v=(j+.65)*math.tau/32
            segment(objects,f'FleetRing{n}_{j}',(x+2.8*math.cos(u),y+2.8*math.sin(u),.20),
                (x+2.8*math.cos(v),y+2.8*math.sin(v),.20),.12,a.color,flat=True)
        label(objects,f'U{n}',(x-1,y-3.6,.19),.85,a.color)
    # A visible bridge defect proxy: event truth is scripted, never model detection.
    bx,by,bz=BRIDGE_TARGET
    for j in range(4):
        objects.append(Shape(f'BridgeDefect{j}','cube',(bx+j*.25,by-.65,bz-.16),(.55,.08,.045),(.35,.12,.08),-30+j*20))
    x,y,z=FISHER_POSITION
    def add(name,kind,xyz,scale,color,yaw=0): objects.append(Shape('Fisher'+name,kind,xyz,scale,color,yaw))
    add('Mat','cube',(x,y,.10),(2.3,2.,.08),(.61,.56,.42))
    add('Stool','cube',(x,y,.37),(.55,.55,.52),(.28,.22,.16))
    add('Body','cube',(x,y,1.05),(.48,.38,.70),(.90,.47,.12))
    add('Head','sphere',(x,y,1.62),(.20,.19,.23),(.75,.57,.40))
    add('Hat','cylinder',(x,y,1.85),(.36,.36,.10),(.79,.72,.46))
    for j,dy in enumerate((-.18,.18)):
        add('Leg'+str(j),'cube',(x-.25,y+dy,.54),(.65,.14,.18),(.16,.22,.30))
        add('Arm'+str(j),'cube',(x-.33,y+dy,1.20),(.60,.13,.13),(.75,.57,.40))
    add('Bucket','cylinder',(x+.75,y-.65,.36),(.28,.28,.46),(.18,.43,.60))
    segment(objects,'FishingRod',(x-.6,y,1.2),(x-3.6,y+.4,2.7),.045,(.17,.18,.16))
    segment(objects,'FishingLine',(x-3.6,y+.4,2.7),(x-5.5,y+.5,.10),.012,(.78,.79,.72))
    return objects

