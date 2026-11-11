"""実Pyxel描画・音声で第2面3武器を通す。固定60Hz、描画1回につき6更新。"""
from pathlib import Path
import sys,json,time
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parent)]
import pyxel as p
import config as C
import main
from game import Game
from pilot_stage2 import Pilot

folder=Path(__file__).resolve().parents[1]/'verification'/('v'+C.VERSION)/'stage2-native'
folder.mkdir(parents=True,exist_ok=True)
original_run=p.run;weapons=iter(C.WEAPONS);results=[];captures=set()

def next_weapon():
    global pilot,started,weapon
    weapon=next(weapons,None)
    if weapon is None:
        (folder/'result.json').write_text(json.dumps(dict(result='PASS',actual_pyxel=True,
            real_devices=False,automatic_input=True,updates_per_draw=6,runs=results),indent=2),encoding='utf8')
        print('STAGE2_NATIVE_PASS',json.dumps(results),flush=True);p.quit();return
    app.game=Game('stage2',weapon=weapon);app.game.reset();pilot=Pilot()
    app.input.read=lambda:pilot.action(app.game);started=time.perf_counter()

def capture(name):
    key=weapon+'-'+name
    if key not in captures:
        captures.add(key);app.draw();p.screenshot(str(folder/(key+'.png')),scale=2)

def run(update,draw):
    global app
    app=update.__self__;next_weapon();original_run(tick,app.draw)

def tick():
    for _ in range(6):
        app.update();g=app.game
        if g.slash_polys and any(e.kind=='asteroid' and abs(e.y-g.py)<100 for e in g.enemies):capture('rock-cut')
        if g.time>=12:capture('rock-gaps')
        if any(b.missile for b in g.bullets):capture('missile')
        if g.time>=96:capture('cross-current')
        if g.boss and g.boss.active:
            capture('boss')
            if g.boss.destroyed_order:capture('boss-gap')
            if g.boss.opening and g.slash_polys:capture('boss-melee')
        if g.state in ('result','gameover'):
            capture('result')
            result=dict(weapon=weapon,final_weapon=g.weapon,state=g.state,seconds=g.time,hp=g.hp,
                        rocks_destroyed=g.rocks_destroyed,rows_dodged=len(pilot.dodged_rows),
                        missiles_cut=g.missiles_cut,max_cut=g.max_cut,score=g.score,
                        boss_spawn=g.boss_spawned_at,order=g.boss.destroyed_order if g.boss else [],
                        wall_seconds=time.perf_counter()-started)
            print('STAGE2_NATIVE_RUN',json.dumps(result),flush=True)
            assert g.state=='result' and g.weapon==weapon and g.rocks_destroyed>0 and pilot.dodged_rows,result
            results.append(result);next_weapon();return
        assert g.time<360,'timeout'

p.run=run
main.App()
