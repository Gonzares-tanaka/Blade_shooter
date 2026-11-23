"""Verification-only input planner. Never changes HP, weapons, entities or combat clocks."""
import math
import config as C
from game import Actions
from pilot import boss_action


class StagePilot:
    def __init__(self,weapon):
        self.weapon=weapon

    def action(self,g):
        if g.state!='playing':return Actions()
        if g.boss:return boss_action(g,True)
        w=g.weapon_config
        armor=next((e for e in g.enemies if e.kind=='armor' and e.on_screen and e.hp>0 and e.phase!='exit'),None)
        small=next((e for e in g.enemies if e.kind=='small' and e.hp>0 and 40<e.y<g.py-24),None)
        target=armor or small
        tx,ty=128,266
        if armor:
            if armor.resting:tx,ty=armor.x,min(280,armor.y+w['reach']-8)
            else:tx,ty=armor.x+(65 if armor.x<128 else -65),265
        elif small:tx,ty=small.x,min(275,small.y+w['reach']-8)
        slash=bool(target and (target.kind!='armor' or target.resting) and
                   abs(g.px-target.x)<(10 if g.weapon=='lance' else 19) and
                   25<g.py-target.y<w['reach']+10)
        # Read bottom warnings and leave that lane. Do not let the front target pin the ship there.
        for e in g.enemies:
            if e.kind=='rear' and e.phase in ('marker','entry','warning','fire') and abs(tx-e.x)<36:
                tx=e.x+(48 if e.x<128 else -48)
        item=g.items.current
        wanted=item and item.kind in ('heal',self.weapon)
        if item:
            if wanted:tx,ty=item.x,item.y
            else:
                # Wait outside contact range, on the current side of the reward.
                dx,dy=g.px-item.x,g.py-item.y
                d=math.hypot(dx,dy) or 1
                tx,ty=item.x+dx/d*40,item.y+dy/d*40
        # The forward slice can open a path, but sideways movement still handles its blind spots.
        cut=any(26<g.py-b.y<w['reach']+4 and abs(g.px-b.x)<(7 if g.weapon=='lance' else 28) for b in g.bullets)
        return self.steer(g,tx,ty,(slash or cut) and g.cooldown<=0,item if item and not wanted else None)

    def steer(self,g,tx,ty,slash,avoid_item=None):
        choices=[]
        for ax,ay in ((0,0),(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,-1),(-1,1),(1,1)):
            length=max(1,math.hypot(ax,ay));vx=ax/length*g.player_speed;vy=ay/length*g.player_speed
            px=max(8,min(248,g.px+vx*.14));py=max(32,min(312,g.py+vy*.14))
            cost=math.hypot(px-tx,py-ty)*.65
            for t in (.06,.14,.26,.42):
                px=max(8,min(248,g.px+vx*t));py=max(32,min(312,g.py+vy*t))
                if avoid_item:cost+=max(0,29-math.hypot(px-avoid_item.x,py-avoid_item.y))**2*10
                for b in g.bullets:
                    cost+=max(0,18-math.hypot(px-b.x-b.vx*t,py-b.y-b.vy*t))**2*5
                for e in g.enemies:
                    if e.hp<=0 or not e.damageable:continue
                    ex,ey=e.x,e.y
                    if e.kind=='small':
                        p=C.FORMATION_PATTERNS[e.pattern];ey+=p['speed']*t;ex+=p['drift']*t
                    elif e.kind=='charger' and e.phase in ('warning','dash'):
                        wait=max(0,C.CHARGER_WARNING_SECONDS-e.phase_time) if e.phase=='warning' else 0
                        ex+=e.vx*max(0,t-wait);ey+=e.vy*max(0,t-wait)
                    elif e.kind=='rear' and e.phase=='exit':ey-=C.REAR_EXIT_SPEED*t
                    cost+=max(0,e.radius+15-math.hypot(px-ex,py-ey))**2*5
            choices.append((cost,ax,ay))
        _,ax,ay=min(choices)
        return Actions(x=ax,y=ay,slash=bool(slash))
