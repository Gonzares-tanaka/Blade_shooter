"""通常入力だけで5分道中・戦艦・全破壊順・混成候補を通す。"""
from pathlib import Path
from itertools import permutations
import sys,json
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parent)]
import config as C
from game import Game,Actions
from pilot import pilot_action,boss_action

DT=1/C.FPS
FOLDER=Path(__file__).resolve().parents[1]/'verification'/('v'+C.VERSION)


def run(course='stage',blade=True,seed=7,order=('center','left','right'),stop=None):
    g=Game(course,5 if stop else 0,seed=seed);g.reset()
    sections={};hits=[];peak=0;frames=0
    for _ in range(480*C.FPS):
        key='boss' if g.boss else g.section[1]
        s=sections.setdefault(key,dict(near=0,erased=0,slashes=0,mixed=0,triple=0,four=0))
        near=any((b.x-g.px)**2+(b.y-g.py)**2<28**2 for b in g.bullets)
        n=len({e.kind for e in g.enemies if e.on_screen})
        s['near']+=DT*near;s['mixed']+=DT*(n>=2);s['triple']+=DT*(n==3);s['four']+=DT*(n>3)
        hp,erased,slashes=g.hp,g.cleared_bullets,g.slashes
        action=boss_action(g,blade,order) if g.boss else pilot_action(g,blade,blade)
        g.step(DT,action);frames+=1
        s['erased']+=g.cleared_bullets-erased;s['slashes']+=g.slashes-slashes
        peak=max(peak,len(g.bullets))
        if g.hp<hp:hits.append(round(g.time,3))
        if g.state!='playing' or stop and g.time>=stop-1e-6:break
    if g.state=='stage_clear':
        while g.state=='stage_clear':g.step(DT)
    result=dict(course=course,blade=blade,seed=seed,state=g.state,time=round(g.time,3),hp=g.hp,
                hits=hits,boss_spawn=g.boss_spawned_at,boss_engaged=g.boss_engaged_at,
                first_boss_fire=g.boss.first_fire_time if g.boss else None,
                order=g.boss.destroyed_order if g.boss else [],requested_order=order,blade_kills=g.blade_kills_by_kind,
                shot_kills=g.shot_kills_by_kind,cleared=g.cleared_bullets,peak_bullets=peak,
                choices=g.course_config.get('mix_choices'),sections=sections,frames=frames)
    print('STAGE_CHECK',json.dumps({k:v for k,v in result.items() if k not in ('sections','choices')}),flush=True)
    return result


def population(seed):
    g=Game('stage',seed=seed);g.reset();counts={}
    for f in range(300*C.FPS):
        g.time=f*DT;g.schedule();g.update_enemies(DT)
        g.enemies=[e for e in g.enemies if -50<e.x<C.WIDTH+50 and -50<e.y<C.HEIGHT+24]
        key=g.section[1];n=len({e.kind for e in g.enemies if e.on_screen})
        c=counts.setdefault(key,{i:0 for i in range(5)})
        c[n]+=1
    assert all(c[4]==0 for c in counts.values()),counts
    return {key:{i:round(v*DT,3) for i,v in c.items()} for key,c in counts.items()}


def check():
    full=[run(seed=s) for s in (7,42)]
    for r in full:
        assert r['state']=='result' and 300<=r['boss_spawn']<=302.1,r
        assert r['first_boss_fire']>=304.8,r
        mix=r['sections']['06 / COMBINED ASSAULT']
        assert mix['near']>1 and mix['erased']>0 and mix['slashes']>0,r
        assert all(s['four']==0 for s in r['sections'].values()),r
    bosses=[run('boss',True,order=o) for o in permutations(('left','right','center'))]
    for r in bosses:assert r['state']=='result' and tuple(r['order'])==r['requested_order'],r
    shot=run('boss',False)
    assert shot['state']=='result' and shot['time']>max(r['time'] for r in bosses)*1.5,shot
    candidates={}
    for key in C.MIX_CANDIDATES:
        seed=next(s for s in range(100) if C.mixed_waves(s)[1][0]==key)
        result=run(seed=seed,stop=225)
        assert result['state']=='playing' and result['hp']>0,result
        candidates[key]=result
    populations={str(seed):population(seed) for seed in (7,42)}
    g=Game();g.reset()
    while g.state=='playing' and g.time<40:g.step(DT,Actions())
    idle=dict(state=g.state,time=g.time,hp=g.hp)
    assert idle['state']=='gameover',idle
    result=dict(version=C.VERSION,automatic_input=True,full=full,boss_orders=bosses,
                shot_only_boss=shot,mixed_candidates=candidates,population=populations,idle=idle)
    FOLDER.mkdir(parents=True,exist_ok=True)
    (FOLDER/'stage.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    return result


if __name__=='__main__':check()
