"""Normal input-only full campaign. No position/HP/score/enemy modifications."""
from pathlib import Path
import sys,json,time
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parent)]
import config as C
from game import Game,Actions
from pilot import pilot_action,boss_action
from pilot_stage2 import Pilot
from pilot_stage3 import CavePilot
DT=1/C.FPS

def main():
    g=Game(seed=7);g.step(DT,Actions(confirm=True));g.step(DT,Actions(confirm=True))
    p2=Pilot();p3=CavePilot();records={};started=time.monotonic();events={}
    maxframes=1500*C.FPS
    for frame in range(maxframes):
        stage=g.run.current_stage
        record=records.setdefault(stage,dict(route_seconds=g.duration,hurt=0,life_lost=0,extend=0,cut_events=0,slashes=0,items=0))
        action=(p3.action(g) if stage==3 else p2.action(g) if stage==2 else boss_action(g,True) if g.boss else pilot_action(g,True,True))
        if g.state=="result":action=Actions(next_stage=True)
        g.step(DT,action)
        for event in g.events:
            events[event]=events.get(event,0)+1
            if event in record:record[event]+=1
            if event=="cut":record["cut_events"]+=1
            if event=="swing":record["slashes"]+=1
            if event.startswith("pickup_"):record["items"]+=1
        if g.boss_spawned_at is not None:
            record.update(boss_spawn=g.boss_spawned_at,boss_engaged=g.boss_engaged_at)
        if g.result and stage==g.result.stage:
            record.update(result=g.result.cleared,stage_seconds=g.result.seconds,score=g.score,max_cut=g.max_cut,lives=g.run.lives,hp=g.hp)
        if g.state in ("gameover","ending_clear"):break
    assert g.state=="ending_clear",(g.state,g.run.current_stage,g.hp,g.run.lives)
    score=g.score;maximum=g.max_cut
    assert len(records)==3 and all(r['result'] for r in records.values())
    assert all(r['cut_events'] and r['slashes'] for r in records.values())
    assert 300<=records[1]['boss_spawn']<=302.1
    assert 180<=records[2]['boss_spawn']<=182.1
    assert 150<=records[3]['boss_spawn']<=152.1
    assert g.result.score==score and g.result.max_cut==maximum
    g.step(5.1);assert g.state=="credits"
    g.step(200);assert g.state=="title" and not g.can_continue
    result=dict(result="PASS",version=C.VERSION,seed=7,weapon="blade",input_only=True,
                simulated_seconds=round((frame+1)*DT,3),execution_seconds=round(time.monotonic()-started,3),
                final_score=score,max_cut=maximum,stages=records,events=events,ending_sequence=True)
    folder=Path(__file__).resolve().parents[1]/'verification'/('v'+C.VERSION)
    (folder/'campaign.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps(result),flush=True)
if __name__=='__main__':main()
