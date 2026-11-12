"""機体の生死と独立した先頭航跡を、各スロットが時間差でたどる。"""
import math
from collections import deque
from boss import BossPart
from stage2_config import STEALTH as S


class StealthChain:
    score_key='stealth_group'
    contact_parts=True
    def __init__(self):
        self.age=self.fight_time=0.0;self.active=False
        self.first_fire_time=None;self.destroyed_order=[];self.warnings=[]
        self.parts=[];self.fired=set();self.history=deque()
        for i in range(S['count']):
            x,y=self.path(-i*S['delay'])
            self.parts.append(BossPart(-i-1,'stealth_'+str(i+1),x,y-180,S['hp'],S['hp'],S['radius']))
        # 入場直後から追従が途切れず、先頭撃破でも履歴を作り続ける。
        for n in range(-int(S['count']*S['delay']*60)-2,1):
            self.history.append((n/60,*self.path(n/60)))

    @staticmethod
    def path(t):
        phase=t*S['angular_speed']
        return S['center_x']+S['sweep_width']*math.sin(phase),S['center_y']+S['sweep_height']*math.sin(phase*2)

    @property
    def opening(self):return self.active and self.fight_time%S['cycle']>=S['open_from']

    @property
    def hull(self):return ()

    def sample(self,t):
        for a,b in zip(self.history,list(self.history)[1:]):
            if a[0]<=t<=b[0]:
                ratio=(t-a[0])/(b[0]-a[0] or 1)
                return a[1]+(b[1]-a[1])*ratio,a[2]+(b[2]-a[2])*ratio
        return self.path(t)

    def update(self,dt,ready):
        self.age+=dt;self.warnings=[]
        if not self.active:
            progress=min(1,self.age/S['entry_seconds'])
            for i,part in enumerate(self.parts):
                part.x,y=self.path(-i*S['delay']);part.y=y-180*(1-progress)
            if progress<1 or not ready:return []
            self.active=True
        before=self.fight_time;self.fight_time+=dt
        self.history.append((self.fight_time,*self.path(self.fight_time)))
        while len(self.history)>2 and self.history[1][0]<self.fight_time-S['count']*S['delay']-.2:
            self.history.popleft()
        commands=[]
        for i,part in enumerate(self.parts):
            part.x,part.y=self.sample(self.fight_time-i*S['delay'])
            part.flash=max(0,part.flash-dt);part.enabled=part.hp>0
            phase=self.fight_time%S['cycle'];at=.15+i*S['part_offset']
            previous=part.phase
            part.phase='destroyed' if part.hp<=0 else 'warning' if at<=phase<at+S['warning'] else 'open'
            if part.phase=='warning' and previous!='warning':self.warnings.append(part.key)
            if part.hp<=0:continue
            for cycle in range(int(before//S['cycle']),int(self.fight_time//S['cycle'])+1):
                fire_at=cycle*S['cycle']+at+S['warning'];key=(cycle,i)
                if before<fire_at<=self.fight_time and key not in self.fired:
                    self.fired.add(key);part.shots_fired+=1
                    commands.append((part,S['bullet_speed'],S['angles']))
        return commands
