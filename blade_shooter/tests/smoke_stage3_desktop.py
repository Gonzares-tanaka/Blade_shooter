"""Native Pyxel: unchanged input/collision, all three complete third-stage runs."""
from pathlib import Path
import sys,json
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parent)]
import pyxel as p
import main,config as C
from game import Game
from pilot_stage3 import CavePilot
folder=Path(__file__).resolve().parents[1]/'verification'/('v'+C.VERSION)/'stage3-native'
folder.mkdir(parents=True,exist_ok=True)
original_run=p.run;weapons=iter(C.WEAPONS);results=[];captures=set()
def advance():
    global weapon,pilot,clear_score,seen_credits
    weapon=next(weapons,None)
    if weapon is None:
        (folder/'result.json').write_text(json.dumps(dict(result='PASS',actual_pyxel=True,automatic_input=True,
            real_devices=False,updates_per_draw=6,runs=results),indent=2),encoding='utf8')
        print('STAGE3_NATIVE_PASS',flush=True);p.quit();return
    app.game=Game('stage3',weapon=weapon);app.game.reset();pilot=CavePilot();clear_score=None;seen_credits=False
    app.input.read=lambda:pilot.action(app.game)
def capture(name):
    key=weapon+'-'+name
    if key not in captures:
        captures.add(key);app.draw();p.screenshot(str(folder/(key+'.png')),scale=2)
def run(update,draw):
    global app
    app=update.__self__;advance();original_run(tick,app.draw)
def tick():
    global clear_score,seen_credits
    for _ in range(6):
        app.update();g=app.game
        if g.cave and any(w.y>60 for w in g.cave.walls):capture('solid-wall')
        for e in g.enemies:
            if e.kind=='barrier' and e.on_screen:capture('barrier-'+e.phase)
        if g.boss and g.boss.active:
            capture('final-'+g.boss.phase)
            if any(b.friendly for b in g.bullets):capture('reflected-bullet')
        if g.state=='gameover':raise AssertionError((weapon,g.time,g.hp))
        if g.state=='ending_clear':
            capture('clear-score')
            if clear_score is None:
                clear_score=g.score
                results.append(dict(weapon=weapon,seconds=g.time,hp=g.hp,score=g.score,max_cut=g.max_cut,
                    reflections=g.reflections,hits=g.reflected_hits,wall_contacts=g.cave.contacts))
                assert g.reflected_hits>=20 and g.weapon==weapon
        if g.state=='credits':
            seen_credits=True
            if g.scene_time>6:capture('credits')
        if clear_score is not None and g.state=='title':
            assert seen_credits and g.run.current_stage==1 and g.best_score>=clear_score
            capture('returned-title');print('STAGE3_NATIVE_RUN',json.dumps(results[-1]),flush=True)
            advance();return
        assert g.time<330,'timeout'
p.run=run
main.App()
