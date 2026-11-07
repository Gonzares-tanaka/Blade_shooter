"""実Pyxel 60fps・描画音声付きで300秒道中から戦艦撃破まで通す。"""
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
    for moment in (4,44,84,124,164,214,264,299.9,300,302,305,308,312,320):
        if g.time>=moment:capture(str(moment))
    if g.boss:
        for p in g.boss.parts:
            if p.phase=='warning':capture('boss-warning-'+p.key)
        for key in g.boss.destroyed_order:capture('destroyed-'+key)
        if g.boss.opening and g.slash_polys:capture('boss-blade-opening')
    if g.state in ('clear','gameover'):
        capture('result')
        result=dict(version=C.VERSION,fps=C.FPS,frames=frames,wall_seconds=time.perf_counter()-started,
                    automatic_input=True,state=g.state,time=g.time,hp=g.hp,boss_spawn=g.boss_spawned_at,
                    first_boss_fire=g.boss.first_fire_time if g.boss else None,
                    order=g.boss.destroyed_order if g.boss else [],blade=g.blade_kills_by_kind,
                    cleared=g.cleared_bullets)
        (FOLDER/'result.json').write_text(json.dumps(result,indent=2))
        print('DESKTOP_STAGE',json.dumps(result),flush=True)
        assert g.state=='clear' and g.boss_spawned_at==300
        pyxel.quit()
    if frames>480*C.FPS:raise AssertionError('stage timeout')


pyxel.run=run
main.App()
