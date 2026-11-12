"""検証用入力。実際の武器・移動・当たり判定だけを使い、HPや敵を変更しない。"""
import math
import config as C
from game import Actions
from stage2_config import ROCK_FLOWS,rock_position,STEALTH as S

class Pilot:
    def __init__(self,melee=True):
        self.melee=melee;self.cut_rows=set();self.dodged_rows=set()
        self.target=None;self.target_deadline=-1;self.retreat_until=-1;self.retreats=0;self.melee_hits=0
        self.counted_swing=-1;self.ignore_rock=None;self.route_moves=0

    def action(self,g):
        if g.state=='title':return Actions(confirm=True)
        if g.state!='playing':return Actions()
        if g.boss:return self.boss(g)
        self.ignore_rock=None
        rocks=[e for e in g.enemies if e.kind=='asteroid' and e.hp>0 and e.phase!='marker']
        for e in rocks:
            if e.y>g.py+e.radius+12 and e.uid not in self.cut_rows:self.dodged_rows.add(e.uid)
        tx,ty=128,278;slash=False
        # 初回の正面ゲートを斬る。直後の側方岩は通常の回避入力で処理する。
        target=min((e for e in rocks if g.time<7 and e.home_x==128 and e.pattern=='cut_cross' and e.y<g.py-20),
                   key=lambda e:g.py-e.y,default=None)
        if self.melee and target:
            tx=target.x;limit={'blade':64,'axe':49,'lance':100}[g.weapon]
            slash=g.cooldown<=0 and abs(g.px-tx)<7 and 25<g.py-target.y<limit
            if g.cooldown<=0 or g.swing>=0:self.ignore_rock=target.uid
            if target.uid in g.slash_hits:self.cut_rows.add(target.uid)
        else:
            # 到達先の流れを読み、横移動だけに固定せず少し前後にも避ける。
            choices=[]
            for x in (28,64,100,136,172,208,232):
                for y in (230,266,290):
                    cost=.10*math.hypot(x-g.px,y-g.py)+.04*abs(x-128)
                    for e in rocks:
                        for t in (.3,.8,1.4):
                            ex,ey=rock_position(e,e.age+t)
                            cost+=max(0,e.radius+25-math.hypot(x-ex,y-ey))**2
                    choices.append((cost,x,y))
            _,tx,ty=min(choices)
            if abs(tx-g.px)>20:self.route_moves+=1
        if self.melee and g.cooldown<=0:
            slash|=any(30<g.py-b.y<72 and abs(g.px-b.x)<18 for b in g.bullets)
        return self.steer(g,tx,ty,slash)

    def boss(self,g):
        b=g.boss;live=[p for p in b.parts if p.hp>0]
        if not live:return Actions()
        if not b.active:return self.steer(g,128,286,False)
        target=next((p for p in b.parts if p.uid==self.target),None)
        if target and target.uid in g.slash_hits and self.counted_swing!=g.slashes:
            self.counted_swing=g.slashes;self.melee_hits+=1;self.retreats+=1
            self.retreat_until=b.fight_time+1.15;self.target=None;target=None
        if target and (target.hp<=0 or b.fight_time>self.target_deadline):self.target=None;target=None
        if not self.melee or b.fight_time<self.retreat_until:
            tx=min(live,key=lambda p:abs(p.x-g.px)).x
            return self.steer(g,tx,286,False)
        distance={'blade':49,'axe':36,'lance':82}[g.weapon]
        if target is None:
            choices=[]
            for i,p in enumerate(b.parts):
                if p.hp<=0:continue
                for turn in range(-1,3):
                    for start,end in S['open_windows']:
                        at=(math.floor(b.fight_time/S['cycle'])+turn)*S['cycle']+i*S['delay']+start
                        until=at+(end-start)
                        if until<=b.fight_time+.15:continue
                        x,y=b.path(at-i*S['delay']+.15)
                        travel=math.hypot(x-g.px,y+distance-g.py)/g.player_speed
                        if b.fight_time+travel+.18>until:continue
                        choices.append((max(at-b.fight_time,travel),p.uid,until))
            if choices:
                _,self.target,self.target_deadline=min(choices)
                target=next(p for p in live if p.uid==self.target)
        if target:
            i=b.parts.index(target);local=b.fight_time-i*S['delay']
            upcoming=[]
            for a,z in S['open_windows']:
                for turn in (math.floor(local/S['cycle']),math.floor(local/S['cycle'])+1):
                    at=turn*S['cycle']+a
                    if at+z-a>local:upcoming.append(at)
            at=min(upcoming,default=local)
            # 予備動作の終点付近で待ち、開口中だけ踏み込む。
            x,y=b.path(max(local,at+.12))
            tx,ty=x,y+distance
            if at-local>1.1:ty=280
            slash=target.phase=='open' and abs(g.px-target.x)<15 and 22<g.py-target.y<g.weapon_config['reach']+8 and g.cooldown<=0
            return self.steer(g,tx,ty,slash)
        return self.steer(g,128,286,False)

    def steer(self,g,tx,ty,slash):
        horizons=(.04,.12,.28,.50,.78)
        enemies=[]
        for e in g.enemies:
            if e.hp<=0 or e.uid==self.ignore_rock:continue
            points=[]
            for t in horizons:
                if e.kind=='asteroid':
                    points.append(None if e.age+t<e.warning_duration else rock_position(e,e.age+t))
                elif e.kind=='small':
                    p=C.FORMATION_PATTERNS[e.pattern]
                    points.append((e.home_x+p['drift']*(e.age+t)+math.sin((e.age+t)*.8)*p['sway'],e.y+p['speed']*t))
                else:points.append((e.x+e.vx*t,e.y+e.vy*t))
            enemies.append((e.radius+14,points))
        if g.boss and g.boss.active:
            for i,p in enumerate(g.boss.parts):
                if p.hp>0:enemies.append((p.radius+13,[g.boss.path(g.boss.fight_time+t-i*S['delay']) for t in horizons]))
        choices=[]
        for ax,ay in ((0,0),(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,-1),(-1,1),(1,1)):
            length=max(1,math.hypot(ax,ay));vx=ax/length*g.player_speed;vy=ay/length*g.player_speed
            nx=max(12,min(244,g.px+vx*.18));ny=max(45,min(306,g.py+vy*.18))
            cost=math.hypot(nx-tx,ny-ty)*.6
            if g.items.current:cost+=max(0,30-math.hypot(nx-g.items.current.x,ny-g.items.current.y))**2*8
            for j,t in enumerate(horizons):
                px=max(8,min(248,g.px+vx*t));py=max(32,min(312,g.py+vy*t))
                for radius,points in enemies:
                    point=points[j]
                    if point:cost+=max(0,radius-math.hypot(px-point[0],py-point[1]))**2*6
                for b in g.bullets:
                    cost+=max(0,17-math.hypot(px-b.x-b.vx*t,py-b.y-b.vy*t))**2*5
            choices.append((cost,ax,ay))
        _,ax,ay=min(choices)
        return Actions(x=ax,y=ay,slash=bool(slash))
