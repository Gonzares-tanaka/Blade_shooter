"""Verification-only inputs; never change HP, position, enemy state or bullet state."""
import math
import config as C
from game import Actions
from stage3_config import CAVE,FINAL,BARRIER

class CavePilot:
    def __init__(self):self.wall_dodges=set();self.last_direction=0;self.route_turns=0
    def action(self,g):
        if g.state!='playing':return Actions()
        if g.boss:return self.final(g)
        left,right=g.cave.bounds(g.py)
        tx=max(left+30,min(right-30,128));ty=268
        for i,w in enumerate(g.cave.walls):
            if w.y<g.py<w.y+w.height and w.depth>=116:self.wall_dodges.add((round(g.time/7),w.side))
        reach={'blade':55,'axe':44,'lance':90}[g.weapon]
        slash=g.cooldown<=0 and (any(20<g.py-e.y<reach+6 and abs(e.x-g.px)<23 and not e.shielded for e in g.enemies)
              or any(reach-10<g.py-b.y<reach+12 and abs(b.x-g.px)<22 for b in g.bullets if not b.friendly))
        return self.steer(g,tx,ty,slash)
    def final(self,g):
        if not g.boss.active:return self.steer(g,128,266)
        # Intercept the central incoming lane, at a distance appropriate to the unchanged weapon.
        delay={'blade':.12,'axe':.095,'lance':.155}[g.weapon]
        reach={'blade':45,'axe':37,'lance':78}[g.weapon]
        bullets=[b for b in g.bullets if b.reflectable and not b.friendly and b.vy>20 and b.y<g.py-(reach+b.vy*(delay-.02)-4)]
        target=min(bullets,key=lambda b:(g.py-b.y)/b.vy,default=None)
        tx,ty=128,266;slash=False
        if target:
            delay={'blade':.12,'axe':.095,'lance':.155}[g.weapon]
            reach={'blade':45,'axe':37,'lance':78}[g.weapon]
            until=max(0,(g.py-reach-target.y)/target.vy)
            tx=target.x+target.vx*until
            dy=g.py-target.y
            slash=g.cooldown<=0 and abs(tx-g.px)<10 and reach+target.vy*(delay-.015)<=dy<=reach+target.vy*(delay+.045)
        return self.steer(g,tx,ty,slash,intercept=target)
    def steer(self,g,tx,ty,slash=False,intercept=None):
        choices=[]
        for ax,ay in ((0,0),(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,-1),(-1,1),(1,1)):
            length=max(1,math.hypot(ax,ay));vx=ax/length*g.player_speed;vy=ay/length*g.player_speed
            nx=max(8,min(248,g.px+vx*.12));ny=max(32,min(312,g.py+vy*.12))
            cost=.7*math.hypot(nx-tx,ny-ty)
            if g.items.current:cost+=max(0,30-math.hypot(nx-g.items.current.x,ny-g.items.current.y))**2*8
            for t in (.08,.22,.45,.8):
                px=max(8,min(248,g.px+vx*t));py=max(32,min(312,g.py+vy*t))
                if g.cave and not g.route_complete:
                    left=right=CAVE['base_width']
                    for w in g.cave.walls:
                        edge=max(w.edge(py+offset-CAVE['scroll_speed']*t) for offset in (-10,0,10))
                        if w.side:right=max(right,edge)
                        else:left=max(left,edge)
                    cost+=max(0,left+18-px)**2*15+max(0,px-(256-right-18))**2*15
                    if t<=.22 and (px<left+11 or px>256-right-11):cost+=100000
                for b in g.bullets:
                    if b.friendly:continue
                    # The current central lane will be reflected; other lanes are still avoided.
                    if b is intercept and (g.cooldown<=0 or g.swing>=0):continue
                    d=math.hypot(px-b.x-b.vx*t,py-b.y-b.vy*t)
                    cost+=max(0,14-d)**2*5
                for e in g.enemies:
                    ex,ey=e.x,e.y
                    if e.kind=='charger' and e.phase=='dash':ex+=e.vx*t;ey+=e.vy*t
                    elif e.kind=='small':ey+=C.FORMATION_PATTERNS[e.pattern]['speed']*t
                    elif e.kind=='rear' and e.phase=='exit':ey-=C.REAR_EXIT_SPEED*t
                    cost+=max(0,e.radius+18-math.hypot(px-ex,py-ey))**2*5
                if g.boss and g.boss.active:
                    bx,by=g.boss.position(g.boss.fight_time+t)
                    cost+=max(0,30-math.hypot(px-bx,py-by))**2*6
            choices.append((cost,ax,ay))
        _,ax,ay=min(choices)
        if ax and ax!=self.last_direction:self.route_turns+=1;self.last_direction=ax
        return Actions(x=ax,y=ay,slash=bool(slash))
