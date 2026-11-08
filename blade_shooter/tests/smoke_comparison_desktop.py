"""実Pyxel 60fps、3武器の54秒コースを通常入力で描画・音声付き確認。"""
from pathlib import Path
import sys,json,time
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parent)]
import pyxel
import config as C
import main
from game import Game
from check_comparison import action
FOLDER=Path(__file__).resolve().parents[1]/'verification/v0.8.0/desktop'
FOLDER.mkdir(parents=True,exist_ok=True)
weapons=tuple(C.WEAPONS);index=0;captures=set();results=[];frame=0
original_run=pyxel.run
started=time.monotonic()
def read():return action(app.game)
def run(update,draw):
    global app
    app=update.__self__;app.input.read=read
    app.game=Game('compare',weapon=weapons[index]);app.draw();pyxel.screenshot(str(FOLDER/'title.png'),scale=2)
    app.game.state='settings';app.draw();pyxel.screenshot(str(FOLDER/'settings.png'),scale=2)
    app.game.reset();original_run(tick,app.draw)
def tick():
    global index,frame
    frame+=1;app.update();g=app.game;labels=[]
    if g.slash_polys:labels.append('active')
    if g.blade_kills and g.bullets:labels.append('kill-bullets-remain')
    if g.cleared_bullets:labels.append('erased')
    if 28<g.time<29:labels.append('barrage')
    if len({e.kind for e in g.enemies})==3:labels.append('triple')
    if g.state!='playing':labels.append(g.state)
    for label in labels:
        key=weapons[index]+'-'+label
        if key not in captures:
            captures.add(key);app.draw();pyxel.screenshot(str(FOLDER/(key+'.png')),scale=2)
    if g.state!='playing':
        row=dict(weapon=g.weapon,state=g.state,time=g.time,hp=g.hp,slashes=g.slashes,kills=g.blade_kills,erased=g.cleared_bullets)
        assert g.state=='clear',row;results.append(row);print('NATIVE_COMPARISON',json.dumps(row),flush=True)
        if index==len(weapons)-1:
            (FOLDER/'result.json').write_text(json.dumps(dict(fps=C.FPS,wall_seconds=time.monotonic()-started,automatic_input=True,routes=results),indent=2),encoding='utf8');pyxel.quit()
        else:index+=1;app.game=Game('compare',weapon=weapons[index]);app.game.reset()
    if frame>170*60:raise AssertionError('native timeout')
pyxel.run=run
main.App()
