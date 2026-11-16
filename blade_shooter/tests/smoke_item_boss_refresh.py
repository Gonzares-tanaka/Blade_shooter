"""Actual Pyxel render of edited items, battleship destruction states and credits."""
from pathlib import Path
import sys,json,itertools,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pyxel as p
import main,config as C
from items import AreaItem
from assets import SPRITES
from stage3_config import ENDING
folder=Path(__file__).resolve().parents[1]/'verification'/('v'+C.VERSION)/'refresh-native'
folder.mkdir(parents=True,exist_ok=True)

def run(update,draw):
    app=update.__self__;g=app.game;captures=[]
    def capture(name):
        app.audio.update(g);app.draw();p.screenshot(str(folder/(name+'.png')),scale=2);captures.append(name)
    g.start_play();g.schedule=lambda:None
    for kind in C.AREA_ITEM['kinds']:
        g.items.current=AreaItem(0,128,176,kind);capture('item-'+kind)
        u,v,w,h=SPRITES['item_'+kind]
        assert all(p.screen.pget(120+x,168+y)==p.images[0].pget(u+x,v+y) for y in range(16) for x in range(16) if p.images[0].pget(u+x,v+y))
    g.items.current=None;g.begin_boss();g.boss.update(C.BOSS_ENTRY_SECONDS+.01,True)
    g.time=310;g.py=270
    for part in g.boss.parts:part.phase='open'
    capture('boss-intact')
    for key in ('left','right','center'):
        part=next(part for part in g.boss.parts if part.key==key)
        g.damage_enemy(part,part.hp);g.effects.clear();g.shake=0
        capture('boss-destroyed-'+key)
    g.state='credits';g.scene_time=16
    capture('credits-names')
    assert not any('TBD' in name for name in ENDING['credits'])
    assert ENDING['credits'].count('GONZARES TANAKA')==3
    g.start_play();g.add_score(29999,'verification')
    assert g.run.lives==3;capture('score-29999')
    g.add_score(1,'verification');assert g.run.lives==4;capture('score-30000')
    g.add_score(75000,'verification');assert g.run.lives==6
    g.add_score(0,'verification');assert g.run.lives==6
    result=dict(result='PASS',engine='actual Pyxel 2.9.9',real_devices=False,render_fixtures=True,
                captures=captures,master_sha256=hashlib.sha256((Path(__file__).resolve().parents[1]/C.RESOURCE_FILE).read_bytes()).hexdigest(),
                lives_at_29999=3,lives_at_30000=4,lives_at_105000=6,duplicate_extend=False,
                credits_names=ENDING['credits'].count('GONZARES TANAKA'),colors=len(p.colors))
    (folder/'result.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps(result),flush=True);p.quit()
p.run=run;main.App()
