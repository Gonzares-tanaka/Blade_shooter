"""Native Pyxel render/audio; six real-input runs, accelerated six updates per draw."""
from pathlib import Path
import sys,json,itertools
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parent)]
import pyxel as p
import main,config as C
from game import Game
from pilot_stage2 import Pilot
from verify_boss_cadence import Recorder
folder=Path(__file__).resolve().parents[1]/'verification'/('v'+C.VERSION)/'boss-native'
folder.mkdir(parents=True,exist_ok=True)
original_run=p.run;runs=iter(itertools.product(C.WEAPONS,(False,True)));results=[];captures=set()
def advance():
    global weapon,melee,pilot,rec
    run=next(runs,None)
    if run is None:
        (folder/'result.json').write_text(json.dumps(dict(result='PASS',actual_pyxel=True,
            automatic_input=True,real_devices=False,updates_per_draw=6,runs=results),indent=2),encoding='utf8')
        print('BOSS_NATIVE_PASS',flush=True);p.quit();return
    weapon,melee=run;app.game=Game('stealth',weapon=weapon);app.game.reset()
    pilot=Pilot(melee);rec=Recorder(weapon,melee);app.input.read=lambda:pilot.action(app.game)
def capture(name):
    key=weapon+('-melee-' if melee else '-dodge-')+name
    if key not in captures:
        captures.add(key);app.draw();p.screenshot(str(folder/(key+'.png')),scale=2)
def run(update,draw):
    global app
    app=update.__self__;advance();original_run(tick,app.draw)
def tick():
    for _ in range(6):
        app.update();g=app.game;rec.observe(g,pilot);b=g.boss
        if b.active:
            group,state,_=b.attack_state()
            if state=='fire' and len(g.bullets)>10:capture(('front' if group==0 else 'rear')+'-fire')
            if state=='warning':capture(('front' if group==0 else 'rear')+'-warning')
            if state=='rest' and g.bullets:capture('rest-residual')
            if b.opening and g.slash_polys:capture('approach-cut')
            if rec.withdrawals:capture('withdrawal')
        if g.state in ('result','gameover') or (not melee and g.time>=60-1e-8):
            if melee:capture('result')
            result=rec.result(g,pilot);results.append(result)
            print('BOSS_NATIVE_RUN',json.dumps({k:v for k,v in result.items() if k!='events'}),flush=True)
            advance();return
        assert g.time<90,'timeout'
p.run=run
main.App()
