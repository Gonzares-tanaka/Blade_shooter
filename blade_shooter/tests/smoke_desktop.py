"""実Pyxelで道中2攻略・従来コース・後方テストを通して確認する。"""
from pathlib import Path
import json
import sys
sys.path[:0] = [str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parent)]
import pyxel
import config as C
import main
from game import Actions
from pilot import pilot_action

ROOT = Path(__file__).resolve().parents[1]
original_init, original_run = pyxel.init, pyxel.run
frame = 0
app = None
route = 0
captures = set()
results = []
ROUTES=(('stage',False),('stage',True),('classic',True),('rear',True))
FOLDER = ROOT/'verification'/('v'+C.VERSION)/'desktop'
FOLDER.mkdir(parents=True,exist_ok=True)


def init(*args, **kwargs):
    kwargs['fps'] = 600
    original_init(*args, **kwargs)


def run(update, draw):
    global app
    app = update.__self__
    app.input.read = read
    original_run(tick, paint)


def read():
    if frame < 55:
        return Actions(slash=frame==8)
    return pilot_action(app.game, ROUTES[route][1], ROUTES[route][1])


def tick():
    global frame, route
    frame += 1
    if frame == 2:
        app.game.reset()
        app.game.schedule = lambda: None
        app.game.time = 10.2
        app.game.px, app.game.py = 128,166
        app.game.shot_clock = 999
        e=app.game.spawn('armor',128,112)
        e.settled=1.8
    if frame == 55:
        # 新しいGameに戻し、通常の出現表をそのまま通す。
        from game import Game
        app.game=Game('stage');app.game.reset()
    app.update()
    if frame>55 and route<2:
        for moment in (5,30,50,67.5,71,75,91,102,114,119):
            key=f'route{route}-{moment}'
            if app.game.time>=moment and key not in captures:
                captures.add(key);app.draw()
                pyxel.screenshot(str(FOLDER/(key+'.png')),scale=2)
    # 高速実行でも各段階を保存するため、該当フレームを明示的に描画する。
    if frame < 55:
        g = app.game
        label = ('title' if g.state=='title' else 'impact' if g.hitstop>0 else
                 'active' if g.slash_polys else 'windup' if 0<=g.swing<C.BLADE_WINDUP else
                 'recovery' if g.swing>=0 else 'split' if g.blade_kills else 'opening')
        if label not in captures:
            captures.add(label)
            app.draw()
            pyxel.screenshot(str(FOLDER/(label+'.png')),scale=2)
    if frame > 55 and app.game.state in ('clear','gameover'):
        g=app.game
        print('DESKTOP_ROUTE',route,g.state,g.time,g.hp,g.slashes,g.blade_kills,flush=True)
        assert g.state == 'clear'
        results.append(dict(route=route,course=g.course,state=g.state,time=g.time,hp=g.hp,slashes=g.slashes,blade_kills=g.blade_kills,
                            blade_by_kind=g.blade_kills_by_kind,rear_shots=g.rear_shots_fired))
        if route==len(ROUTES)-1:
            (FOLDER/'result.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
            pyxel.quit()
        else:
            route+=1
            g.course=ROUTES[route][0];g.checkpoint=0
            g.reset()
    if frame > int(sum(C.COURSES[c]['duration'] for c,_ in ROUTES)*C.FPS)+300:
        raise AssertionError('desktop timeout')


def paint():
    app.draw()


pyxel.init, pyxel.run = init,run
main.App()
