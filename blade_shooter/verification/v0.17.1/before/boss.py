"""独立した3部位と固定タイムライン。破壊済み砲台の射撃だけを止める。"""
from dataclasses import dataclass
import config as C


@dataclass
class BossPart:
    uid: int
    key: str
    x: float
    y: float
    hp: int
    max_hp: int
    radius: float
    kind: str = "boss"
    flash: float = 0
    phase: str = "entry"
    enabled: bool = False
    shots_fired: int = 0

    @property
    def damageable(self):
        return self.enabled and self.hp>0


class Battleship:
    def __init__(self):
        self.y=C.BOSS_ENTRY_Y
        self.age=self.fight_time=0.0
        self.active=False
        self.parts=[BossPart(-i-1,key,p["x"],self.y+p["dy"],p["hp"],p["hp"],p["radius"])
                    for i,(key,p) in enumerate(C.BOSS_PARTS.items())]
        self.fired=set()
        self.destroyed_order=[]
        self.first_fire_time=None
        self.warnings=[]

    @property
    def opening(self):
        return self.active and self.fight_time%C.BOSS_CYCLE_SECONDS>=C.BOSS_OPEN_FROM

    @property
    def hull(self):
        x,dy,w,h=C.BOSS_HULL_RECT
        return ((x,self.y+dy),(x+w,self.y+dy),(x+w,self.y+dy+h),(x,self.y+dy+h))

    def update(self, dt, ready):
        """戻り値は発射命令。ゲーム側で通常の敵弾として生成する。"""
        self.age+=dt
        self.warnings=[]
        progress=min(1,self.age/C.BOSS_ENTRY_SECONDS)
        self.y=C.BOSS_ENTRY_Y+(C.BOSS_Y-C.BOSS_ENTRY_Y)*progress
        for part in self.parts:
            part.y=self.y+C.BOSS_PARTS[part.key]["dy"]
            part.flash=max(0,part.flash-dt)
        if not self.active:
            if progress<1 or not ready:return []
            self.active=True
        before=self.fight_time
        self.fight_time+=dt
        commands=[]
        # 区間境界でも二重発射しない。低fpsでも予告と発射順を保つ。
        cycle=int(self.fight_time//C.BOSS_CYCLE_SECONDS)
        for part in self.parts:
            p=C.BOSS_PARTS[part.key]
            old_phase=part.phase
            phase=self.fight_time%C.BOSS_CYCLE_SECONDS
            fire_at=p["warning_at"]+p["warning"]
            part.enabled=part.hp>0
            part.phase=("destroyed" if part.hp<=0 else "warning" if p["warning_at"]<=phase<fire_at
                        else "fire" if fire_at<=phase<=fire_at+max(p["volleys"])+dt else "open")
            if part.phase=="warning" and old_phase!="warning":self.warnings.append(part.key)
            if part.hp<=0:continue
            for index,offset in enumerate(p["volleys"]):
                for turn in range(max(0,int(before//C.BOSS_CYCLE_SECONDS)),cycle+1):
                    key=(turn,part.key,index)
                    at=turn*C.BOSS_CYCLE_SECONDS+fire_at+offset
                    if before<at<=self.fight_time and key not in self.fired:
                        self.fired.add(key)
                        part.shots_fired+=1
                        commands.append((part,p["speed"],p["angles"]))
        return commands
