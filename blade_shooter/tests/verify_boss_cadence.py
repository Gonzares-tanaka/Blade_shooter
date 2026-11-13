"""Real collision/input verification; no HP refill, invulnerability, bullet deletion or enemy damage fixtures."""
from pathlib import Path
import sys,json,math
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parent)]
import config as C
from game import Game
from pilot_stage2 import Pilot

class Recorder:
    def __init__(self,weapon,melee):
        self.weapon=weapon;self.melee=melee;self.max_bullets=0;self.near_frames=0
        self.rest_with_bullets=0;self.withdrawals=set();self.min_distance=999;self.hurts=[]
        self.last_hp=3
    def observe(self,g,pilot):
        b=g.boss;self.max_bullets=max(self.max_bullets,len(g.bullets))
        if g.hp<self.last_hp:self.hurts.append(round(g.time,3))
        self.last_hp=g.hp
        if not b.active:return
        distances=[math.hypot(g.px-bullet.x,g.py-bullet.y) for bullet in g.bullets]
        if distances:
            distance=min(distances);self.min_distance=min(self.min_distance,distance)
            self.near_frames+=distance<50
        if b.attack_state()[1]=='rest' and g.bullets:self.rest_with_bullets+=1
        for i,event in enumerate(pilot.events):
            if .25<b.fight_time-event['time']<1.3 and g.py>=275:
                self.withdrawals.add(i)
    def result(self,g,pilot):
        result=dict(weapon=self.weapon,melee_enabled=self.melee,state=g.state,seconds=g.time,
            hp=g.hp,hurts=self.hurts,slashes=g.slashes,max_cut=g.max_cut,max_bullets=self.max_bullets,
            bullet_near_frames=self.near_frames,min_bullet_distance=round(self.min_distance,3),
            rest_with_residual_frames=self.rest_with_bullets,melee_hits=pilot.melee_hits,
            completed_withdrawals=len(self.withdrawals),events=pilot.events)
        assert self.near_frames>0 and self.rest_with_bullets>0,result
        assert g.hp==3,result
        if self.melee:
            assert g.state=='result' and g.boss_defeated and pilot.melee_hits>=3 and len(self.withdrawals)>=2,result
            assert all(e['group_state']=='rest' for e in pilot.events),result
            assert any(e['bullets']>0 for e in pilot.events),result
        else:
            assert g.state=='playing' and g.time>=59.9 and g.slashes==0 and g.max_cut==0,result
        return result

def verify():
    results=[]
    for weapon in C.WEAPONS:
        for melee in (False,True):
            g=Game('stealth',weapon=weapon);g.reset();pilot=Pilot(melee);rec=Recorder(weapon,melee)
            for frame in range((90 if melee else 60)*C.FPS):
                g.step(1/C.FPS,pilot.action(g));rec.observe(g,pilot)
                if g.state in ('result','gameover'):break
            result=rec.result(g,pilot);results.append(result)
            print('BOSS_CADENCE',json.dumps(result),flush=True)
    folder=Path(__file__).resolve().parents[1]/'verification'/('v'+C.VERSION)
    folder.mkdir(parents=True,exist_ok=True)
    (folder/'boss-cadence.json').write_text(json.dumps(dict(result='PASS',automatic_input=True,
        real_devices=False,fixed_dt=1/C.FPS,runs=results),indent=2),encoding='utf8')

if __name__=='__main__':verify()
