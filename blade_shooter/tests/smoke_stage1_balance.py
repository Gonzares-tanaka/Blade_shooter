"""Real Pyxel renderer/audio, ordinary controller actions, six simulation updates per draw."""
from pathlib import Path
import sys,json
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parent)]
import pyxel as p
import main,config as C
from game import Game,Actions
from pilot_stage1 import StagePilot
from persistence import BestStore

folder=Path(__file__).resolve().parents[1]/'verification'/('v'+C.VERSION)/'stage1-native'
folder.mkdir(parents=True,exist_ok=True)
original_run=p.run;weapons=iter(C.WEAPONS);records=[];captures=set()

def capture(name):
    if name in captures:return
    captures.add(name);app.draw();p.screenshot(str(folder/(name+'.png')),scale=3)

def advance():
    global weapon,pilot
    weapon=next(weapons,None)
    if weapon is None:
        fixtures=verify_fixtures()
        (folder/'result.json').write_text(json.dumps(dict(result='PASS',actual_pyxel=True,
            automatic_input=True,updates_per_draw=6,real_devices=False,runs=records,fixtures=fixtures),indent=2),encoding='utf8')
        print('STAGE1_NATIVE_PASS',flush=True);p.quit();return
    app.game=Game(weapon=weapon);app.game.reset();pilot=StagePilot(weapon)
    app.input.read=lambda:pilot.action(app.game)

def verify_fixtures():
    rows=[]
    for w,distance,count in [('blade',36,2),('axe',36,1),('blade',125,1),('lance',125,1)]:
        g=Game('compare',weapon=w);g.reset();g.schedule=lambda:None;g.px,g.py=128,136+distance
        enemy=g.spawn_armor(128,'bulwark',132);enemy.phase='open'
        app.game=g;swings=0;hits=[];key=f'{w}-distance-{distance}'
        def action():
            nonlocal swings
            start=g.cooldown<=0 and g.swing<0 and swings<count
            if start:swings+=1
            return Actions(slash=start)
        app.input.read=action
        for f in range(108):
            hp=enemy.hp;app.update()
            if hp-enemy.hp>1:
                hits.append(dict(time=g.time,before=hp,after=enemy.hp));capture(key+'-hit-'+str(len(hits)))
            if distance==125 and g.slash_polys:capture(key+'-attack')
            if enemy.hp<=0:break
        rows.append(dict(weapon=w,distance=distance,swings=swings,hp=enemy.hp,melee=hits))
    assert len(rows[0]['melee'])==2 and rows[0]['hp']<=0
    assert len(rows[1]['melee'])==1 and rows[1]['hp']<=0
    assert not rows[2]['melee'] and rows[3]['melee']
    g=Game('compare',weapon='lance');g.reset();g.schedule=lambda:None;g.px,g.py=104,236
    front=g.spawn_armor(104,'column_front',132);back=g.spawn_armor(104,'column_back',88)
    front.phase=back.phase='open';app.game=g
    app.input.read=lambda:Actions(slash=g.slashes==0)
    for f in range(24):
        app.update()
        if len(g.slash_hits)==2:capture('lance-column-both-hit')
    assert (front.hp,back.hp)==(32,32)
    rows.append(dict(case='column',hp=[front.hp,back.hp],swings=g.slashes))
    return rows

def run(update,draw):
    global app
    app=update.__self__;app.store=BestStore(path=folder/'best.json');advance();original_run(tick,app.draw)

def tick():
    for _ in range(6):
        app.update();g=app.game
        kinds={e.kind for e in g.enemies if e.on_screen and e.hp>0}
        if len(kinds)>=3:capture(weapon+'-three-types')
        if g.time>151 and g.time<160 and {'armor','rear'}<=kinds:capture(weapon+'-final-front-rear')
        if g.items.current:capture(weapon+'-item-'+str(g.items.current.area+1))
        if g.boss:capture(weapon+'-boss-arrival')
        if g.slash_polys and g.boss and g.boss.opening:capture(weapon+'-boss-melee')
        if g.state=='gameover':raise AssertionError((weapon,g.time,g.hp))
        if g.state=='result':
            capture(weapon+'-result');collected=[h for h in g.items.history if h['event']=='pickup']
            assert len(collected)==4 and g.weapon==weapon
            assert 165<=g.boss_spawned_at<=167.1 and len(g.boss.destroyed_order)==3
            records.append(dict(weapon=weapon,time=g.time,boss_spawn=g.boss_spawned_at,
                first_boss_fire=g.boss.first_fire_time,hp=g.hp,lives=g.run.lives,
                slashes=g.slashes,cuts=g.cleared_bullets,items=collected,
                shot_kills=g.shot_kills_by_kind,melee_kills=g.blade_kills_by_kind))
            print('STAGE1_NATIVE_RUN',json.dumps(records[-1]),flush=True);advance();return
        assert g.time<300,'timeout'

p.run=run
main.App()
