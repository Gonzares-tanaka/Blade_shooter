"""無操作連斬と移動する攻略の比較。戦闘ルールは変更せず、調整値だけ比較する。"""
from pathlib import Path
import json
import sys
from unittest.mock import patch
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parent)]
import config as C
from game import Game, Actions, Bullet
from pilot import pilot_action


def route(mode,course='legacy',section=0):
    g=Game(course,section);g.reset()
    sections={}
    max_enemies=max_bullets=0
    for _ in range(int((g.duration-g.time)*C.FPS)+1):
        action=(Actions(slash=g.cooldown<=1e-6 and g.swing<0) if mode=='stationary' else
                pilot_action(g, mode in ('approach','rear_first'),mode=='rear_first'))
        g.step(1/C.FPS,action)
        key=g.section[1]
        if key not in sections:sections[key]=dict(start=round(g.time,3),start_hp=g.hp,blade_kills_before=g.blade_kills)
        sections[key].update(end_hp=g.hp,blade_kills=g.blade_kills-sections[key]['blade_kills_before'])
        max_enemies=max(max_enemies,sum(e.phase!='marker' for e in g.enemies))
        max_bullets=max(max_bullets,len(g.bullets))
        if g.state!='playing':break
    return dict(mode=mode,course=course,start_section=section+1,state=g.state,time=round(g.time,3),hp=g.hp,slashes=g.slashes,
                blade_kills=g.blade_kills,shot_kills=g.shot_kills,cleared=g.cleared_bullets,
                blade_by_kind=g.blade_kills_by_kind,shot_by_kind=g.shot_kills_by_kind,
                rear_shots=g.rear_shots_fired,max_swing_kills=g.max_swing_kills,
                max_enemies=max_enemies,max_bullets=max_bullets,sections=sections)


def check():
    comparisons=[]
    for name, tuning in (
        ('final',{}),):
        with patch.multiple(C,**tuning) if tuning else patch.object(C,'VERSION',C.VERSION):
            values={k:getattr(C,k) for k in ('BLADE_REACH','BLADE_INNER','BLADE_ACTIVE','BLADE_RECOVERY','BLADE_COOLDOWN')}
            comparisons.append(dict(name=name,tuning=values,result=route('stationary')))
    routes=[route(mode,course) for course in ('legacy','classic','rear')
            for mode in (('shot_only','approach','rear_first') if course=='legacy' else ('shot_only','rear_first'))]
    checkpoints=[route(mode,'legacy',i) for i in range(1,6) for mode in ('shot_only','rear_first')]
    assert comparisons[-1]['result']['hp']<C.PLAYER_HP
    assert all(r['state']=='clear' for r in routes)
    assert all(r['state']=='clear' for r in checkpoints)
    counter=next(r for r in routes if r['course']=='legacy' and r['mode']=='rear_first')['blade_by_kind']
    assert all(counter[kind]>0 for kind in ('armor','small','charger','rear'))
    g=Game();g.reset();g.schedule=lambda:None;g.shot_clock=999
    g.bullets=[Bullet(x,222,0,C.ARMOR_BULLET_SPEED) for x in range(48,209,16)]
    for frame in range(14):g.step(1/C.FPS,Actions(slash=frame==0))
    cut_y=g.py
    cleared=g.cleared_bullets
    for _ in range(36):g.step(1/C.FPS,Actions(y=-1))
    gap=dict(cleared=cleared,moved=round(cut_y-g.py,2),hp=g.hp,slashes=g.slashes)
    assert g.hp==3 and cut_y-g.py>65
    result=dict(version=C.VERSION,stage_seconds=C.STAGE_SECONDS,comparisons=comparisons,routes=routes,checkpoints=checkpoints,front_gap=gap)
    folder=Path(__file__).resolve().parents[1]/'verification'/('v'+C.VERSION)
    folder.mkdir(parents=True,exist_ok=True)
    (folder/'balance.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(dict(routes=[{k:v for k,v in r.items() if k!='sections'} for r in routes],
                          checkpoints_passed=len(checkpoints),stationary=comparisons[0]['result']),indent=2))


if __name__=='__main__':check()
