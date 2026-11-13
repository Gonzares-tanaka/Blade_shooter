"""各機は独立した航跡を追い、射撃と全休止は編隊共通の時計で進める。"""
import math
from boss import BossPart
from stage2_config import STEALTH as S,STEALTH_ROUTE,STEALTH_START,STEALTH_ATTACK as A


def path_state(t):
    phase=t%S['cycle'];start=STEALTH_START
    for duration,end,kind in STEALTH_ROUTE:
        if phase<duration-1e-9:
            f=phase/duration
            return (start[0]+(end[0]-start[0])*f,start[1]+(end[1]-start[1])*f),kind
        phase-=duration;start=end
    return STEALTH_START,'cruise'


class StealthChain:
    score_key='stealth_group'
    contact_parts=True
    def __init__(self):
        self.age=self.fight_time=0.0;self.active=False
        self.first_fire_time=None;self.destroyed_order=[];self.warnings=[]
        self.parts=[];self.fired=set();self.locks={};self.aim_marks=[];self.motion_warnings=[]
        self.player_position=(128.0,270.0);self.fire_history=[]
        for i in range(S['count']):
            x,y=self.path(-i*S['delay'])
            self.parts.append(BossPart(-i-1,'stealth_'+str(i+1),x,y-180,S['hp'],S['hp'],S['radius']))

    @staticmethod
    def path(t):return path_state(t)[0]

    def sample(self,t):return self.path(t)

    @property
    def opening(self):return self.active and any(p.hp>0 and p.phase=='open' for p in self.parts)

    @property
    def hull(self):return ()

    def attack_state(self,t=None):
        """生存数で周期を詰めず、予告中も新規弾を出さない。"""
        t=self.fight_time if t is None else t
        half=math.floor((t+1e-9)/A['half_cycle']);phase=t-half*A['half_cycle']
        state='warning' if phase<A['warning']-1e-9 else 'fire' if phase<A['warning']+A['fire_seconds']-1e-9 else 'rest'
        return half%2,state,phase

    def can_approach(self,t):
        _,state,phase=self.attack_state(t)
        return state=='rest' and phase>=A['warning']+A['fire_seconds']+A['residual_seconds']

    def update(self,dt,ready):
        self.age+=dt;self.warnings=[];self.aim_marks=[];self.motion_warnings=[]
        if not self.active:
            progress=min(1,self.age/S['entry_seconds'])
            for i,part in enumerate(self.parts):
                part.x,y=self.path(-i*S['delay']);part.y=y-180*(1-progress)
            if progress<1 or not ready:return []
            self.active=True
        before=self.fight_time;self.fight_time+=dt;commands=[]
        group,state,phase=self.attack_state()
        half=math.floor((self.fight_time+1e-9)/A['half_cycle'])
        for i,part in enumerate(self.parts):
            t=self.fight_time-i*S['delay'];local=t%S['cycle']
            (part.x,part.y),motion=path_state(t)
            part.flash=max(0,part.flash-dt);part.enabled=part.hp>0
            previous=part.phase
            selected=i//A['group_size']==group
            is_open=motion=='open' and any(a<=local<b for a,b in S['open_windows']) and self.can_approach(self.fight_time)
            part.phase='destroyed' if part.hp<=0 else 'warning' if selected and state=='warning' else 'open' if is_open else 'fire' if selected and state=='fire' else 'rest'
            if part.hp<=0:continue
            if motion.endswith('warning'):self.motion_warnings.append((part,i))
            if part.phase=='warning':
                key=(i,half)
                if key not in self.locks:self.locks[key]=self.player_position
                self.aim_marks.append((part,self.locks[key],'break_warning'))
                if previous!='warning':self.warnings.append(part.key)
            for turn in range(max(0,math.floor(before/A['half_cycle'])),half+1):
                if i//A['group_size']!=turn%2:continue
                for event,(at,style) in enumerate(A['bursts']):
                    key=(i,turn,event)
                    fire_at=turn*A['half_cycle']+A['warning']+(i%A['group_size'])*A['stagger']+at
                    if not before<fire_at<=self.fight_time+1e-9 or key in self.fired:continue
                    self.fired.add(key)
                    # 予告時の位置を狙い、発射後は直進。残弾は休止・撃破でも残す。
                    target=self.locks.get((i,turn),self.player_position)
                    ox=part.x+(S['wing_offset']*(-1 if event%2==0 else 1) if style=='break' else 0)
                    oy=part.y+part.radius+2
                    if style=='trail':
                        ax,ay=self.path(t-.02);bx,by=self.path(t+.02)
                        aim=math.degrees(math.atan2(by-ay,bx-ax));speed=S['bullet_speed']
                    else:
                        aim=math.degrees(math.atan2(target[1]-oy,target[0]-ox))
                        speed=S['cross_speed'] if style=='cross' else S['break_speed']
                    angles=tuple(aim+a for a in A[style+'_offsets'])
                    part.shots_fired+=1;commands.append((part,speed,angles,ox,oy))
                    self.fire_history.append(dict(time=self.fight_time,part=i,group=turn%2,style=style))
        self.fire_history=self.fire_history[-512:]
        self.locks={k:v for k,v in self.locks.items() if k[1]>=half-1}
        self.fired={k for k in self.fired if k[1]>=half-1}
        return commands
