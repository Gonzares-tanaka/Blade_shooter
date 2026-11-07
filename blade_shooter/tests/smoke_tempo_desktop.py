"""実Pyxelを60fpsで起動。通常入力だけで30秒コースを描画・音声付き確認。"""
from pathlib import Path
import json
import sys
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parent)]
import pyxel
import config as C
import main
from game import Game, Actions
from pilot import pilot_action

FOLDER=Path(__file__).resolve().parents[1]/'verification'/('v'+C.VERSION)/'desktop'
FOLDER.mkdir(parents=True,exist_ok=True)
ROUTES=(('tempo','idle'),('tempo','move'),('tempo','blade'),
        ('tempo_fast','move'),('tempo_fast','blade'))
original_run=pyxel.run
index=0
captures=set()
results=[]
frame=0


def read():
    mode=ROUTES[index][1]
    return Actions() if mode=='idle' else pilot_action(app.game,mode=='blade',mode=='blade')


def run(update,draw):
    global app
    app=update.__self__
    app.input.read=read
    app.game=Game(ROUTES[index][0])
    app.draw();pyxel.screenshot(str(FOLDER/'title.png'),scale=2)
    app.game.reset()
    original_run(tick,app.draw)


def tick():
    global index,frame
    frame+=1
    app.update()
    g=app.game
    labels=[]
    for moment in (1.1,2.7,3.4,12.5,17.8,24,29):
        if g.time>=moment:labels.append(str(moment))
    if g.slash_polys:labels.append('blade-active')
    if g.blade_kills and g.bullets:labels.append('kill-with-bullets')
    if g.cleared_bullets:labels.append('bullet-cut')
    for label in labels:
        key=f'{index}-{label}'
        if key not in captures:
            captures.add(key);app.draw()
            pyxel.screenshot(str(FOLDER/(key+'.png')),scale=2)
    if g.state in ('clear','gameover'):
        assert g.state==('gameover' if ROUTES[index][1]=='idle' else 'clear')
        r=dict(course=g.course,mode=ROUTES[index][1],state=g.state,time=g.time,
               hp=g.hp,slashes=g.slashes,blade=g.blade_kills_by_kind,
               cleared=g.cleared_bullets,shot=g.shot_kills_by_kind)
        results.append(r)
        print('DESKTOP_ROUTE',json.dumps(r),flush=True)
        if index==len(ROUTES)-1:
            (FOLDER/'result.json').write_text(json.dumps(dict(fps=C.FPS,automatic_input=True,routes=results),indent=2))
            pyxel.quit()
        else:
            index+=1;app.game=Game(ROUTES[index][0]);app.game.reset()
    if frame>140*C.FPS:raise AssertionError('desktop timeout')


pyxel.run=run
main.App()
