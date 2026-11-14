"""予備動作→横切り→予告→射撃→反射待ち。直接攻撃はゲーム側でも拒否。"""
import math
from boss import BossPart
from stage3_config import FINAL as S

class ReflectorFighter:
    score_key='final_victory'
    contact_parts=True
    reflect_only=True
    def __init__(self):
        self.age=self.fight_time=0.0;self.active=False
        self.first_fire_time=None;self.destroyed_order=[];self.warnings=[]
        self.player_position=(128.,270.);self.aim=(128.,270.)
        self.parts=[BossPart(-1,'final',128.,-30.,S['hp'],S['hp'],S['radius'])]
        self.fired=set();self.phase='entry';self.destination=S['positions'][0]
    @property
    def hull(self):return ()
    @property
    def opening(self):return self.active and self.phase=='reflect'
    def position(self,t):
        turn=math.floor(max(0,t)/S['cycle']);phase=t-turn*S['cycle']
        start=S['positions'][(turn-1)%len(S['positions'])] if turn else (128.,96.)
        end=S['positions'][turn%len(S['positions'])]
        f=max(0,min(1,(phase-S['move_warning'])/S['dash_seconds']))
        return tuple(a+(b-a)*f for a,b in zip(start,end))
    def update(self,dt,ready):
        self.age+=dt;self.warnings=[];p=self.parts[0];p.flash=max(0,p.flash-dt)
        if not self.active:
            p.y=-30+126*min(1,self.age/S['entry_seconds'])
            if self.age<S['entry_seconds'] or not ready:return []
            self.active=True
        before=self.fight_time;self.fight_time+=dt
        turn=math.floor((self.fight_time+1e-9)/S['cycle']);phase=self.fight_time-turn*S['cycle']
        previous=self.phase;fire=S['move_warning']+S['dash_seconds']+S['aim_warning']
        self.phase=('move_warning' if phase<S['move_warning'] else 'dash' if phase<S['move_warning']+S['dash_seconds']
                    else 'warning' if phase<fire else 'fire' if phase<fire+max(S['volleys'])+.1 else 'reflect')
        p.x,p.y=self.position(self.fight_time);p.enabled=p.hp>0;p.phase=self.phase
        self.destination=S['positions'][turn%len(S['positions'])]
        if self.phase=='warning' and previous!='warning':self.aim=self.player_position;self.warnings=['final']
        commands=[]
        if p.hp<=0:return commands
        for cycle in range(max(0,math.floor(before/S['cycle'])),turn+1):
            for i,offset in enumerate(S['volleys']):
                at=cycle*S['cycle']+fire+offset;key=(cycle,i)
                if before<at<=self.fight_time+1e-9 and key not in self.fired:
                    self.fired.add(key)
                    aim=math.degrees(math.atan2(self.aim[1]-p.y-16,self.aim[0]-p.x))
                    commands.append((p,S['bullet_speed'],tuple(aim+a for a in S['angles'])))
                    p.shots_fired+=1
        self.fired={k for k in self.fired if k[0]>=turn-1}
        return commands
