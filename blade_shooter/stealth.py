"""各機が同じ時刻付き航跡を追う。開口・離脱予告・射撃は機体ごとの位相。"""
import math
from boss import BossPart
from stage2_config import STEALTH as S,STEALTH_ROUTE,STEALTH_START,STEALTH_FIRE


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
        self.parts=[];self.fired=set();self.locks={};self.aim_marks=[]
        self.player_position=(128.0,270.0);self.player_previous=self.player_position
        self.player_velocity=(0.0,0.0);self.fire_history=[]
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

    def pressure_target(self,part):
        seconds=min(S['lead_seconds'],math.hypot(self.player_position[0]-part.x,self.player_position[1]-part.y)/S['break_speed'])
        dx,dy=(v*seconds for v in self.player_velocity)
        ratio=min(1,S['lead_max_px']/(math.hypot(dx,dy) or 1))
        return self.player_position[0]+dx*ratio,self.player_position[1]+dy*ratio

    def update(self,dt,ready):
        self.age+=dt;self.warnings=[];self.aim_marks=[]
        self.player_velocity=tuple(.8*v+.2*(p-old)/max(.001,dt) for v,p,old in zip(self.player_velocity,self.player_position,self.player_previous))
        self.player_previous=self.player_position
        if not self.active:
            progress=min(1,self.age/S['entry_seconds'])
            for i,part in enumerate(self.parts):
                part.x,y=self.path(-i*S['delay']);part.y=y-180*(1-progress)
            if progress<1 or not ready:return []
            self.active=True
        before=self.fight_time;self.fight_time+=dt;commands=[]
        for i,part in enumerate(self.parts):
            t=self.fight_time-i*S['delay'];phase=t%S['cycle'];cycle=math.floor(t/S['cycle'])
            (part.x,part.y),motion=path_state(t)
            part.flash=max(0,part.flash-dt);part.enabled=part.hp>0
            previous=part.phase
            if any(a<=phase<b for a,b in S['break_warning_windows']):motion='break_warning'
            if motion=='open' and not any(a<=phase<b for a,b in S['open_windows']):motion='pressure'
            part.phase='destroyed' if part.hp<=0 else 'warning' if motion.endswith('warning') else 'open' if motion=='open' else 'fire'
            # 交差射撃は予告時に固定。離脱射撃は移動先を照準表示し、発射後は直進。
            if part.hp<=0:continue
            if part.phase=='warning':
                key=(i,cycle,motion,phase>=7)
                if key not in self.locks:self.locks[key]=self.player_position
                self.aim_marks.append((part,self.pressure_target(part) if motion=='break_warning' else self.locks[key],motion))
                if previous!='warning':self.warnings.append(part.key)
            old_t=before-i*S['delay']
            for turn in range(math.floor(old_t/S['cycle'])-1,cycle+1):
                for event,(at,style) in enumerate(STEALTH_FIRE):
                    key=(i,turn,event);fire_at=turn*S['cycle']+at
                    if not old_t<fire_at<=t or key in self.fired:continue
                    self.fired.add(key)
                    if self.fight_time<S['first_fire_grace']-1e-8:continue
                    if style=='trail':
                        ax,ay=self.path(t-.02);bx,by=self.path(t+.02)
                        aim=math.degrees(math.atan2(by-ay,bx-ax));speed=S['bullet_speed'];angles=(aim,)
                    else:
                        warning='turn_warning' if style=='cross' else 'break_warning'
                        target=self.pressure_target(part) if style=='break' else self.locks.get((i,turn,warning,at>=7),self.player_position)
                        ox=part.x+(S['wing_offset']*(-1 if event%2==0 else 1) if style=='break' else 0)
                        oy=part.y+part.radius+2
                        aim=math.degrees(math.atan2(target[1]-oy,target[0]-ox))
                        speed=S['cross_speed'] if style=='cross' else S['break_speed']
                        angles=tuple(aim+a for a in S[style+'_offsets'])
                    part.shots_fired+=1
                    commands.append((part,speed,angles,ox,oy) if style=='break' else (part,speed,angles))
                    self.fire_history.append(dict(time=self.fight_time,part=i,style=style))
        self.fire_history=self.fire_history[-512:]
        oldest=math.floor(self.fight_time/S['cycle'])-2
        self.locks={k:v for k,v in self.locks.items() if k[1]>=oldest}
        return commands
