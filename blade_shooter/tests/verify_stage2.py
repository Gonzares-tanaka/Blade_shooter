"""固定60Hzの自動入力で3武器の第2面を通す。実機・人のプレイとは別記録。"""
from pathlib import Path
import sys,json,time,math
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parent)]
import config as C
from game import Game
from pilot_stage2 import Pilot

def verify():
    results=[]
    for weapon in C.WEAPONS:
        g=Game('stage2',weapon=weapon);g.reset();pilot=Pilot();hurts=[];started=time.perf_counter()
        for frame in range(360*C.FPS):
            hp=g.hp;g.step(1/C.FPS,pilot.action(g))
            if g.hp<hp:hurts.append(dict(time=round(g.time,3),near=[e.kind for e in g.enemies if math.hypot(g.px-e.x,g.py-e.y)<40]))
            if g.state in ('result','gameover'):break
        result=dict(weapon=weapon,final_weapon=g.weapon,state=g.state,seconds=g.time,hp=g.hp,
                    rocks_destroyed=g.rocks_destroyed,rows_cut=len(pilot.cut_rows),rows_dodged=len(pilot.dodged_rows),
                    missiles_cut=g.missiles_cut,max_cut=g.max_cut,score=g.score,hurts=hurts,
                    boss_spawn=g.boss_spawned_at,boss_first_fire=g.boss.first_fire_time if g.boss else None,
                    boss_order=g.boss.destroyed_order if g.boss else [],wall_seconds=time.perf_counter()-started)
        results.append(result);print('STAGE2_PILOT',json.dumps(result),flush=True)
        assert g.state=='result' and g.boss_defeated,(weapon,result)
        assert g.weapon==weapon and g.rocks_destroyed>0 and pilot.dodged_rows,result
        assert 180<=g.boss_spawned_at<=182.1
    folder=Path(__file__).resolve().parents[1]/'verification'/('v'+C.VERSION)
    (folder/'three-weapons.json').write_text(json.dumps(dict(result='PASS',automatic_input=True,
        fixed_dt=1/C.FPS,real_devices=False,runs=results),indent=2),encoding='utf8')

if __name__=='__main__':verify()
