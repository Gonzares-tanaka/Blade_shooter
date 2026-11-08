"""54秒固定出現を通常入力だけで比較。HP/弾/無敵/出現は改変しない。"""
from pathlib import Path
import sys,json,math
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import config as C
from game import Game,Actions
from pilot import pilot_action,steer
ROOT=Path(__file__).resolve().parents[1]

def action(g):
    a=pilot_action(g,True)
    if g.weapon=='lance':
        # 横薙ぎ用の編隊中心ではなく、穂先が通る一機へ正対する。
        armor=next((e for e in g.enemies if e.kind=='armor' and e.resting),None)
        small=next((e for e in sorted(g.enemies,key=lambda e:abs(e.x-g.px)) if e.kind=='small' and e.y<g.py-25),None)
        target=armor or small
        if target:a=steer(g,target.x,min(275,target.y+82),precision=True)
        a.slash=any(e.hp>0 and e.damageable and abs(e.x-g.px)<e.radius+1 and
                    32<g.py-e.y<96 and (e.kind!='armor' or e.resting) for e in g.enemies)
    if g.cooldown<=0:
        width=10 if g.weapon=='lance' else 28 if g.weapon=='axe' else 42
        if any(24<g.py-b.y<g.weapon_config['reach']+3 and abs(g.px-b.x)<width for b in g.bullets):a.slash=True
    return a

def run(weapon,mode,still=False):
    g=Game('compare',weapon=weapon,touch_mode=mode);g.reset()
    near=moved=coexist=0;peak=0;arrived=set();shots=0
    for frame in range(60*55):
        a=Actions() if still else action(g)
        moved+=bool(a.x or a.y)
        g.step(1/60,a)
        near+=any(math.hypot(b.x-g.px,b.y-g.py)<45 for b in g.bullets)
        kinds={e.kind for e in g.enemies};coexist+=len(kinds)>=2;peak=max(peak,len(kinds));arrived.update(kinds)
        shots+=sum(event=='enemy_fire' for event in g.events)
        if g.state!='playing':break
    return dict(weapon=weapon,touch_mode=mode,stationary=still,state=g.state,time=round(g.time,3),hp=g.hp,
                melee=g.slashes,kills=g.blade_kills,erased=g.cleared_bullets,movement_frames=moved,
                bullets_near_frames=near,two_types_seconds=round(coexist/60,2),peak_types=peak,types=sorted(arrived))

if __name__=='__main__':
    rows=[run(w,m) for w in C.WEAPONS for m in C.TOUCH_MODES]
    rows.append(run('blade','flick',True))
    for row in rows:print(json.dumps(row))
    out=ROOT/'verification/v0.9.0/comparison.json';out.write_text(json.dumps(rows,indent=2),encoding='utf8')
    assert all(r['state']=='clear' and r['time']==54 and r['kills']>0 and r['erased']>0 and r['movement_frames']>0 and r['peak_types']==3 for r in rows[:-1])
    assert rows[-1]['state']=='gameover'
