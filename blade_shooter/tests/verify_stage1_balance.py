"""Whole-route ordinary-input verification plus isolated real-collision weapon comparisons."""
from pathlib import Path
import sys,json,math
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parent)]
import config as C
from game import Game,Actions
from pilot_stage1 import StagePilot

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'verification'/('v'+C.VERSION)
DT=1/C.FPS


def timing():
    rows=[]
    for stage in (1,2,3):
        g=Game();g.enter_stage(stage,carry_run=False);g.invincible=10000
        frames=0
        while not g.boss and frames<400*C.FPS:g.step(DT);frames+=1
        rows.append(dict(stage=stage,route=g.duration,boss_spawn=g.boss_spawned_at,
                         wall_simulated=frames/C.FPS,timing_fixture_invincible=True,item_points=g.items.ends))
    return rows


def full(weapon,seed=7):
    g=Game(weapon=weapon,seed=seed);g.reset();pilot=StagePilot(weapon)
    samples=[];attacks=0;near=0.;mixed=0.;triple=0.;quiet=0.;dodges=0;hits=0;previous_bullets=set()
    for _ in range(330*C.FPS):
        a=pilot.action(g);hp=g.hp;before=(g.px,g.py)
        danger=any(math.hypot(g.px-b.x,g.py-b.y)<32 for b in g.bullets)
        n=len({e.kind for e in g.enemies if e.on_screen and e.hp>0})
        if not g.boss:
            near+=DT*danger;mixed+=DT*(n>=2);triple+=DT*(n>=3)
            quiet+=DT*(not n and not g.bullets and not g.items.current)
        g.step(DT,a)
        dodges+=int(danger and (g.px,g.py)!=before and not g.frame_hurt)
        hits+=int(g.hp<hp)
        attacks+=sum(event in ('armor_fire','small_fire','rear_fire') for event in g.events)
        if len(samples)<20 and n>=3 and not g.boss and (not samples or g.time-samples[-1]['time']>3):
            samples.append(dict(time=g.time,kinds=sorted({e.kind for e in g.enemies if e.on_screen and e.hp>0}),bullets=len(g.bullets)))
        if g.state in ('gameover','result'):break
    r=dict(weapon=weapon,seed=seed,state=g.state,seconds=g.time,hp=g.hp,lives=g.run.lives,
           boss_spawn=g.boss_spawned_at,first_boss_fire=g.boss.first_fire_time if g.boss else None,
           order=g.boss.destroyed_order if g.boss else [],shots=g.shot_kills_by_kind,melee=g.blade_kills_by_kind,
           slashes=g.slashes,cuts=g.cleared_bullets,hits=hits,near_seconds=near,dodge_frames=dodges,
           mixed_seconds=mixed,triple_seconds=triple,quiet_without_item_seconds=quiet,examples=samples,
           item_history=g.items.history,final_weapon=g.weapon,score=g.score)
    print('STAGE1_RUN',json.dumps(r),flush=True)
    return r


def weapon_fixture(weapon,distance=36,pattern='bulwark',swings=2):
    # Real Game.step, auto-shots, armor movement/fire, cooldown, collisions. Only schedule is isolated.
    g=Game('compare',weapon=weapon);g.reset();g.schedule=lambda:None
    g.px,g.py=128,132+4+distance
    e=g.spawn_armor(128,pattern,132);e.phase='open'
    slashes=0;records=[]
    for frame in range(180):
        press=g.cooldown<=0 and g.swing<0 and slashes<swings
        if press:slashes+=1
        previous=e.hp;g.step(DT,Actions(slash=press))
        if previous!=e.hp:records.append(dict(time=g.time,before=previous,after=e.hp,melee=previous-e.hp>1))
        if e.hp<=0:break
    return dict(weapon=weapon,distance=distance,pattern=pattern,hp=e.hp,slashes=slashes,damage_log=records)


def main():
    FOLDER.mkdir(parents=True,exist_ok=True)
    times=timing();runs=[full(w) for w in C.WEAPONS]
    weapons=[weapon_fixture('blade'),weapon_fixture('axe',swings=1),
             weapon_fixture('blade',distance=125,swings=1),weapon_fixture('lance',distance=125,swings=1)]
    report=dict(automatic_input=True,real_devices=False,version=C.VERSION,timing=times,runs=runs,weapons=weapons)
    (FOLDER/'stage1-balance.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    assert all(r['state']=='result' and 165<=r['boss_spawn']<=167.1 for r in runs)
    assert all(r['near_seconds']>1 and r['dodge_frames']>20 and r['cuts']>0 for r in runs)
    assert weapons[0]['slashes']==2 and weapons[0]['hp']<=0
    assert weapons[1]['slashes']==1 and weapons[1]['hp']<=0
    assert not any(e['melee'] for e in weapons[2]['damage_log'])
    assert any(e['melee'] for e in weapons[3]['damage_log'])
    print('STAGE1_BALANCE_PASS',flush=True)

if __name__=='__main__':main()
