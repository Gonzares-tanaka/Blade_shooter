"""通常の出現・HP・被弾・入力だけで30秒の密度と攻略を記録する。"""
from pathlib import Path
import json
import sys
sys.path[:0] = [str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parent)]
import config as C
from game import Game, Actions
from pilot import pilot_action

DT = 1/C.FPS
FOLDER = Path(__file__).resolve().parents[1]/'verification'/('v'+C.VERSION)


def route(course, mode, section=0):
    g = Game(course, section)
    g.reset()
    mixed = triple = four = near = peak = volleys = 0
    hits, attacks, known = [], [], set()
    for _ in range(round((g.duration-g.time)*C.FPS)+1):
        action = (Actions() if mode == 'idle' else
                  Actions(slash=g.cooldown<=0 and g.swing<0) if mode == 'stationary_slash' else
                  pilot_action(g, mode == 'blade', mode == 'blade'))
        hp = g.hp
        before = {e.uid:e.shots_fired for e in g.enemies}
        g.step(DT, action)
        kinds = {e.kind for e in g.enemies if e.on_screen}
        mixed += len(kinds)>=2
        triple += len(kinds)==3
        four += len(kinds)>3
        peak = max(peak, len(g.bullets))
        near += any((b.x-g.px)**2+(b.y-g.py)**2 < 28**2 for b in g.bullets)
        for e in g.enemies:
            n = e.shots_fired-before.get(e.uid,0)
            volleys += n
            if n and e.uid not in known:
                known.add(e.uid)
                attacks.append(dict(kind=e.kind,time=round(g.time,3),hp=e.hp,on_screen=e.on_screen))
        if g.hp<hp:
            hits.append(round(g.time,3))
        if g.state!='playing':
            break
    return dict(course=course,mode=mode,section=section+1,speed=g.player_speed,
                state=g.state,time=round(g.time,3),hp=g.hp,hits=hits,
                blade=g.blade_kills_by_kind,shot=g.shot_kills_by_kind,
                cleared=g.cleared_bullets,slashes=g.slashes,max_swing=g.max_swing_kills,
                mixed_seconds=round(mixed*DT,3),triple_seconds=round(triple*DT,3),
                four_kind_seconds=round(four*DT,3),near_bullet_seconds=round(near*DT,3),
                peak_bullets=peak,volleys=volleys,first_attacks=attacks)


def schedule_probe():
    # 戦闘攻略とは別に、撃破しなかった場合の出現表だけを観測する。
    g=Game('tempo');g.reset()
    counts={i:0 for i in range(5)}
    first={}
    longest=run=0
    for f in range(30*C.FPS):
        g.time=f*DT;g.schedule();g.update_enemies(DT)
        g.enemies=[e for e in g.enemies if -50<e.y<C.HEIGHT+24 and -50<e.x<C.WIDTH+50]
        n=len({e.kind for e in g.enemies if e.on_screen})
        counts[n]+=1
        run=run+1 if n==3 else 0
        longest=max(longest,run)
        for e in g.enemies:
            if e.shots_fired and e.kind not in first:
                first[e.kind]=round(e.age,3)
    return dict(kind_seconds={k:round(v*DT,3) for k,v in counts.items()},
                longest_three_kind_seconds=round(longest*DT,3),first_shot_age=first)


def check():
    routes=[route(c,m) for c in C.PLAYER_SPEED_PRESETS
            for m in ('idle','stationary_slash','move','blade')]
    checkpoints=[route(c,'blade',s) for c in C.PLAYER_SPEED_PRESETS for s in (1,2)]
    for r in routes:
        assert r['four_kind_seconds']==0,r
        assert r['near_bullet_seconds']>.5,r
        if r['mode'] in ('idle','stationary_slash'):
            assert r['state']=='gameover',r
        else:
            assert r['state']=='clear',r
            # 早期撃破で密度を減らす攻略は許す。未撃破時の密度は別途出現表で確認。
            assert r['mixed_seconds']>12,r
        if r['mode']=='blade':
            assert r['blade']['armor']>=3 and r['cleared']>0,r
    assert all(r['state']=='clear' for r in checkpoints),checkpoints
    probe=schedule_probe()
    assert probe['kind_seconds'][4]==0
    assert probe['kind_seconds'][2]+probe['kind_seconds'][3]>28
    result=dict(version=C.VERSION,routes=routes,checkpoints=checkpoints,schedule=probe)
    FOLDER.mkdir(parents=True,exist_ok=True)
    (FOLDER/'tempo.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps(dict(routes=[{k:v for k,v in r.items() if k!='first_attacks'} for r in routes],
                          checkpoints=[(r['course'],r['section'],r['state'],r['hp']) for r in checkpoints],
                          schedule=probe),indent=2))
    return result


if __name__=='__main__':check()
