"""Real inputs for all third-stage weapons and the complete 1→2→3 campaign."""
from pathlib import Path
import sys,json,time,math
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parent)]
import config as C
from game import Game,Actions
from pilot_stage3 import CavePilot
from pilot_stage2 import Pilot
from pilot import pilot_action
from stage3_config import FINAL,ENDING

FOLDER=Path(__file__).resolve().parents[1]/'verification'/('v'+C.VERSION)
def third(weapon):
    g=Game('stage3',weapon=weapon);g.reset();pilot=CavePilot();hurts=[];started=time.perf_counter()
    mixed=triple=near=0;max_types=0;examples=[];cut_lanes=[];residual=[];misses=[];route_cuts=0
    last_cut=0;last_example=-10;last_residual=-10;killed=set()
    for _ in range(330*C.FPS):
        hp=g.hp;before_enemies=list(g.enemies);g.step(1/C.FPS,pilot.action(g))
        killed.update(e.uid for e in before_enemies if e.hp<=0)
        if hp>g.hp:hurts.append(round(g.time,3))
        if 'reflected_miss' in g.events:misses.append(round(g.time,3))
        if not g.route_complete:
            types=sorted({e.kind for e in g.enemies if e.on_screen and e.hp>0})
            mixed+=len(types)>=2;triple+=len(types)>=3;max_types=max(max_types,len(types))
            close=[b for b in g.bullets if math.hypot(b.x-g.px,b.y-g.py)<70]
            near+=bool(close)
            if len(types)>=3 and g.time-last_example>8:
                examples.append(dict(time=round(g.time,3),types=types,player=[round(g.px,1),round(g.py,1)],
                    corridor=[round(v,1) for v in g.cave.bounds(g.py)],bullets=len(g.bullets)))
                last_example=g.time
            left_over=[b for b in close if b.owner_uid in killed]
            if left_over and g.time-last_residual>12:
                residual.append(dict(time=round(g.time,3),sources=sorted({b.source for b in left_over}),killed_owner_ids=sorted({b.owner_uid for b in left_over}),
                    player=[round(g.px,1),round(g.py,1)],corridor=[round(v,1) for v in g.cave.bounds(g.py)]))
                last_residual=g.time
            if g.cleared_bullets>last_cut:
                route_cuts+=g.cleared_bullets-last_cut
                if len(cut_lanes)<12:cut_lanes.append(dict(time=round(g.time,3),count=g.cleared_bullets-last_cut,
                    player=[round(g.px,1),round(g.py,1)],types=types))
            last_cut=g.cleared_bullets
        if g.state in ('ending_clear','gameover'):break
    result=dict(weapon=weapon,final_weapon=g.weapon,state=g.state,seconds=g.time,hp=g.hp,hurts=hurts,
                score=g.score,max_cut=g.max_cut,reflections=g.reflections,hits=g.reflected_hits,
                misses=g.reflected_misses,miss_times=misses,
                route_mixed_seconds=round(mixed/C.FPS,3),route_triple_seconds=round(triple/C.FPS,3),max_enemy_types=max_types,
                route_near_bullet_seconds=round(near/C.FPS,3),route_bullets_cut=route_cuts,
                mixed_examples=examples,residual_routes=residual,cut_lanes=cut_lanes,
                wall_contacts=g.cave.contacts,route_turns=pilot.route_turns,wall_passages=len(pilot.wall_dodges),
                boss_spawn=g.boss_spawned_at,wall_seconds=time.perf_counter()-started)
    print('STAGE3',json.dumps({k:v for k,v in result.items() if k not in ('mixed_examples','residual_routes','cut_lanes')}),flush=True)
    assert g.state=='ending_clear' and g.weapon==weapon and g.reflected_hits*FINAL['reflected_damage']>=FINAL['hp'],result
    assert g.reflections>=g.reflected_hits and g.max_cut>0 and pilot.route_turns>=4,result
    assert mixed/C.FPS>40 and triple/C.FPS>5 and near/C.FPS>8 and route_cuts>5,(weapon,mixed,triple,near,route_cuts)
    assert residual and examples
    return result

def campaign():
    g=Game('stage');g.reset();p2=Pilot();p3=CavePilot();records=[];carry=[];seen_stage=1
    for frame in range(1100*C.FPS):
        if g.state=='result' and g.can_advance_stage:
            expected=(g.hp,g.weapon,g.score,g.max_cut)
            records.append(dict(stage=g.run.current_stage,score=g.score,hp=g.hp,weapon=g.weapon,max_cut=g.max_cut,seconds=g.time))
            g.step(1/C.FPS,Actions(next_stage=True))
            actual=(g.hp,g.weapon,g.score,g.max_cut);assert actual==expected,(actual,expected)
            carry.append(dict(to_stage=g.run.current_stage,values=actual));continue
        action=pilot_action(g,True) if g.run.current_stage==1 else p2.action(g) if g.run.current_stage==2 else p3.action(g)
        g.step(1/C.FPS,action)
        if g.state in ('ending_clear','gameover'):break
    assert g.state=='ending_clear',(g.run.current_stage,g.state,g.time,g.hp)
    assert len(records)==2 and [c['to_stage'] for c in carry]==[2,3]
    assert g.score==records[-1]['score']+sum(g.score_totals.values())
    assert g.score_totals['final_victory']==FINAL['points']
    assert g.result.score==g.score
    final_score=g.score;max_cut=g.max_cut
    for _ in range(int(ENDING['clear_seconds']*C.FPS)-1):g.step(1/C.FPS)
    assert g.state=='ending_clear'
    while g.state=='ending_clear':g.step(1/C.FPS)
    assert g.state=='credits' and g.result.score==final_score
    for _ in range(70*C.FPS):
        g.step(1/C.FPS)
        if g.state=='title':break
    assert g.state=='title' and g.run.current_stage==1 and g.best_score>=final_score
    result=dict(result='PASS',full_campaign=True,automatic_input=True,fixtures=False,stages=records,
                carry=carry,final_score=final_score,max_cut=max_cut,ending_then_title=True,
                new_best=g.best_score,wall_frames=frame)
    print('CAMPAIGN',json.dumps(result),flush=True)
    return result

if __name__=='__main__':
    FOLDER.mkdir(parents=True,exist_ok=True)
    runs=[third(w) for w in C.WEAPONS]
    (FOLDER/'three-weapons.json').write_text(json.dumps(dict(result='PASS',real_devices=False,automatic_input=True,runs=runs),indent=2),encoding='utf8')
    (FOLDER/'campaign.json').write_text(json.dumps(campaign(),indent=2),encoding='utf8')
