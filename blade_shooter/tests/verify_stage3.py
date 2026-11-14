"""Real inputs for all third-stage weapons and the complete 1→2→3 campaign."""
from pathlib import Path
import sys,json,time
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
    for _ in range(330*C.FPS):
        hp=g.hp;g.step(1/C.FPS,pilot.action(g))
        if hp>g.hp:hurts.append(round(g.time,3))
        if g.state in ('ending_clear','gameover'):break
    result=dict(weapon=weapon,final_weapon=g.weapon,state=g.state,seconds=g.time,hp=g.hp,hurts=hurts,
                score=g.score,max_cut=g.max_cut,reflections=g.reflections,hits=g.reflected_hits,
                wall_contacts=g.cave.contacts,route_turns=pilot.route_turns,wall_passages=len(pilot.wall_dodges),
                boss_spawn=g.boss_spawned_at,wall_seconds=time.perf_counter()-started)
    print('STAGE3',json.dumps(result),flush=True)
    assert g.state=='ending_clear' and g.weapon==weapon and g.reflected_hits*FINAL['reflected_damage']>=FINAL['hp'],result
    assert g.reflections>=g.reflected_hits and g.max_cut>0 and pilot.route_turns>=4,result
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
