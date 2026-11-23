"""実Pyxel 60fps・描画音声付きで設定尺の道中から戦艦撃破まで通す。"""
from pathlib import Path
import sys,json,time
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parent)]
import pyxel
import config as C
import main
from pilot import pilot_action

FOLDER=Path(__file__).resolve().parents[1]/'verification'/('v'+C.VERSION)/'desktop'
FOLDER.mkdir(parents=True,exist_ok=True)
original_run=pyxel.run
captures=set()
frames=0
started=0


def run(update,draw):
    global app,started
    app=update.__self__
    app.input.read=lambda:pilot_action(app.game,True,True)
    app.draw();pyxel.screenshot(str(FOLDER/'title.png'),scale=2)
    app.game.reset();started=time.perf_counter()
    original_run(tick,app.draw)


def capture(key):
    if key in captures:return
    captures.add(key);app.draw();pyxel.screenshot(str(FOLDER/(key+'.png')),scale=2)


def tick():
    global frames
    frames+=1;app.update();g=app.game
    for moment in (4,30.6,35.6,65.6,70.6,105.6,110.6,152.6,154.6,161.1,164.9,165,167,171,174,180,190):
        if g.time>=moment:capture(str(moment))
    if g.boss:
        for p in g.boss.parts:
            if p.phase=='warning':capture('boss-warning-'+p.key)
        for key in g.boss.destroyed_order:capture('destroyed-'+key)
        if g.boss.opening and g.slash_polys:capture('boss-blade-opening')
    if g.state=='stage_clear':capture('stage-clear')
    if g.state in ('result','gameover'):
        capture('result')
        result=dict(version=C.VERSION,fps=C.FPS,frames=frames,wall_seconds=time.perf_counter()-started,
                    automatic_input=True,state=g.state,time=g.time,hp=g.hp,boss_spawn=g.boss_spawned_at,
                    first_boss_fire=g.boss.first_fire_time if g.boss else None,
                    order=g.boss.destroyed_order if g.boss else [],blade=g.blade_kills_by_kind,
                    cleared=g.cleared_bullets,items=g.items.history,weapon=g.weapon,
                    score=g.score,best=g.best_score,max_cut=g.max_cut,score_totals=g.score_totals,
                    result_max_cut=g.result.max_cut,boss_defeated=g.boss_defeated,save_failed=app.store.failed)
        assert g.state=='result' and C.STAGE_SECONDS<=g.boss_spawned_at<=C.STAGE_SECONDS+2.1
        assert g.score>0 and g.max_cut>0 and g.result.max_cut==g.max_cut
        assert g.score==sum(g.score_totals.values())
        assert g.score_totals['battleship']==10000
        assert [h['area'] for h in g.items.history if h['event']=='spawn']==[1,2,3,4]
        from game import Actions
        carry=(g.score,g.max_cut,g.hp,g.weapon,g.run.lives)
        g.step(1/C.FPS,Actions(confirm=True))
        assert g.run.current_stage==2 and g.state=='story'
        assert (g.score,g.max_cut,g.hp,g.weapon,g.run.lives)==carry
        assert g.current_cut==0 and g.time==0
        assert not (g.enemies or g.bullets or g.shots or g.boss or g.items.current)
        capture('next-stage')
        result['next_stage_clean']=True
        (FOLDER/'result.json').write_text(json.dumps(result,indent=2))
        print('DESKTOP_STAGE',json.dumps(result),flush=True)
        pyxel.quit()
    if frames>480*C.FPS:raise AssertionError('stage timeout')


pyxel.run=run
main.App()
