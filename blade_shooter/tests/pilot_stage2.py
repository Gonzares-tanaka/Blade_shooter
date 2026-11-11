"""検証専用の入力。衝突・HP・武器・敵を変更しない。"""
import math
import config as C
from game import Actions
from stage2_config import ROCK,ROCK_PATTERNS


class Pilot:
    def __init__(self,melee=True):
        self.melee=melee;self.opened={};self.cut_rows=set();self.dodged_rows=set()
        self.row_positions={};self.plans={};self.cut_targets={};self.previous_rocks=0

    def action(self,g):
        if g.state=='title':return Actions(confirm=True)
        if g.state!='playing':return Actions()
        if g.boss:return self.boss(g)
        rocks=[e for e in g.enemies if e.kind=='asteroid' and e.hp>0]
        groups={e.group for e in rocks}
        for group in groups:
            row=[e for e in rocks if e.group==group];y=row[0].y
            self.row_positions[group]=y
            if y>g.py+25 and group not in self.cut_rows:self.dodged_rows.add(group)
        ahead=[e for e in rocks if g.py-160<e.y<g.py+24]
        row=max(ahead,key=lambda e:e.y,default=None)
        tx,ty,slash=128,274,False
        if row:
            p=ROCK_PATTERNS[row.pattern];drift=p['direction']*ROCK['drift']*math.sin(row.age*ROCK['drift_frequency'])
            tx=p['gap']+drift
            if row.group not in self.plans:
                self.plans[row.group]=self.melee and g.time<30 and row.group%3==1 and (g.py-row.y)/p['speed']>g.cooldown+.5
            if row.group in self.opened:tx=self.opened[row.group]+drift
            elif self.plans[row.group]:
                target=min((e for e in rocks if e.group==row.group),key=lambda e:abs(e.x-128))
                self.cut_targets[row.group]=target.home_x
                tx=target.x
                limit={'blade':63,'axe':48,'lance':100}[g.weapon]
                slash=g.cooldown<=0 and abs(g.px-tx)<7 and 25<g.py-target.y<limit
                if slash:self.opened[row.group]=target.home_x;self.cut_rows.add(row.group)
        else:
            target=next((e for e in g.enemies if e.kind!='asteroid' and e.hp>0 and e.y<g.py-50),None)
            if target:tx=target.x
        # 岩以外でも正面のミサイル／通常弾を実際の近接入力で消す。
        if self.melee and g.cooldown<=0 and not row:
            slash|=any(32<g.py-b.y<70 and abs(g.px-b.x)<18 for b in g.bullets)
        return self.steer(g,tx,ty,slash)

    def boss(self,g):
        b=g.boss;parts=[p for p in b.parts if p.hp>0]
        if not parts:return Actions()
        target=min(parts,key=lambda p:abs(p.x-g.px))
        approach=self.melee and b.opening
        tx=target.x;ty=target.y+{'blade':49,'axe':36,'lance':82}[g.weapon] if approach else 266
        slash=approach and abs(g.px-tx)<12 and 22<g.py-target.y<g.weapon_config['reach']+5
        slash|=self.melee and any(32<g.py-bullet.y<72 and abs(g.px-bullet.x)<18 for bullet in g.bullets)
        return self.steer(g,tx,ty,slash and g.cooldown<=0)

    def steer(self,g,tx,ty,slash):
        choices=[]
        for ax,ay in ((0,0),(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,-1),(-1,1),(1,1)):
            length=max(1,math.hypot(ax,ay));vx=ax/length*g.player_speed;vy=ay/length*g.player_speed
            nx=max(12,min(244,g.px+vx*.18));ny=max(45,min(306,g.py+vy*.18))
            cost=math.hypot(nx-tx,ny-ty)*.65
            if g.items.current:
                cost+=max(0,32-math.hypot(nx-g.items.current.x,ny-g.items.current.y))**2*8
            for t in (.025,.08,.22,.40,.65):
                px=max(8,min(248,g.px+vx*t));py=max(32,min(312,g.py+vy*t))
                for e in g.enemies:
                    if e.hp<=0:continue
                    if e.kind=='asteroid':
                        if e.group in self.opened and abs(e.home_x-self.opened[e.group])<18:continue
                        if self.plans.get(e.group) and e.home_x==self.cut_targets.get(e.group) and g.cooldown<=.05:continue
                        p=ROCK_PATTERNS[e.pattern];ex=e.home_x+p['direction']*ROCK['drift']*math.sin((e.age+t)*ROCK['drift_frequency']);ey=e.y+p['speed']*t
                    elif e.kind=='small':
                        p=C.FORMATION_PATTERNS[e.pattern]
                        ex=e.home_x+p['drift']*(e.age+t)+math.sin((e.age+t)*.8)*p['sway'];ey=e.y+p['speed']*t
                    else:ex,ey=e.x+e.vx*t,e.y+(e.vy*t if e.kind=='charger' else 25*t)
                    margin=13 if e.kind=='asteroid' else 24
                    cost+=max(0,e.radius+margin-math.hypot(px-ex,py-ey))**2*5
                for bullet in g.bullets:
                    cost+=max(0,17-math.hypot(px-bullet.x-bullet.vx*t,py-bullet.y-bullet.vy*t))**2*4
                if g.boss and g.boss.active:
                    for part in g.boss.parts:
                        if part.hp>0:cost+=max(0,part.radius+12-math.hypot(px-part.x,py-part.y))**2*4
            choices.append((cost,ax,ay))
        _,ax,ay=min(choices)
        return Actions(x=ax,y=ay,slash=bool(slash))
