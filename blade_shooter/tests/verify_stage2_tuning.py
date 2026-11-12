"""同じHP・武器のまま、固定連打／追従連打と回避する入力を比較する。"""
from pathlib import Path
import sys,json
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parent)]
import config as C
from game import Game,Actions
from pilot_stage2 import Pilot

def spam(weapon,course,mode,x=128,y=None):
    g=Game(course,weapon=weapon);g.reset()
    g.px,g.py=x,y if y is not None else (195 if weapon!='lance' else 220) if course=='stealth' else 278
    for _ in range(180*C.FPS):
        a=Actions(slash=True)
        if mode=='chase':
            p=min((p for p in g.boss.parts if p.hp>0),key=lambda p:abs(g.px-p.x),default=None)
            if p:
                tx,ty=p.x,p.y+{'blade':49,'axe':36,'lance':82}[weapon]
                a=Actions(x=max(-1,min(1,(tx-g.px)/5)),y=max(-1,min(1,(ty-g.py)/5)),slash=True)
        g.step(1/C.FPS,a)
        if g.state in ('result','clear','gameover'):break
    return dict(weapon=weapon,course=course,mode=mode,start=[x,y],state=g.state,seconds=g.time,hp=g.hp,
                rocks_destroyed=g.rocks_destroyed,boss_hp=[p.hp for p in g.boss.parts] if g.boss else [])

def main():
    folder=Path(__file__).resolve().parents[1]/'verification'/('v'+C.VERSION)
    rows=[];grid=[];active=[]
    for weapon in C.WEAPONS:
        for course,mode in (('stage2','spam'),('stealth','camp'),('stealth','chase')):
            row=spam(weapon,course,mode);rows.append(row);print('SPAM',json.dumps(row),flush=True)
            assert row['state']=='gameover',row
        for x in (64,128,192):
            for y in (195,220,250):grid.append(spam(weapon,'stealth','camp',x,y))
        g=Game('stealth',weapon=weapon);g.reset();pilot=Pilot()
        for _ in range(180*C.FPS):
            g.step(1/C.FPS,pilot.action(g))
            if g.state in ('result','gameover'):break
        row=dict(weapon=weapon,state=g.state,seconds=g.time,hp=g.hp,retreats=pilot.retreats,
                 melee_hits=pilot.melee_hits,bullet_cuts=g.cleared_bullets)
        active.append(row);print('APPROACH_WITHDRAW',json.dumps(row),flush=True)
        assert g.state=='result' and pilot.retreats>=2,row
    assert all(row['state']=='gameover' for row in grid),grid
    result=dict(result='PASS',automatic_input=True,real_devices=False,spam=rows,camp_grid=grid,
                adaptive_boss=active,boss_hp=C.STEALTH['hp'])
    (folder/'strategy-comparison.json').write_text(json.dumps(result,indent=2),encoding='utf8')

if __name__=='__main__':main()
