"""実Pyxel原本ロード・4絵柄/予告/取得表示・SE再生・攻撃中交換を確認。"""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pyxel as p
import config as C
import main
from items import AreaItem
from game import Actions,Bullet

folder=Path(__file__).resolve().parents[1]/'verification'/('v'+C.VERSION)/'items-runtime'
folder.mkdir(parents=True,exist_ok=True)

def run(update,draw):
    app=update.__self__;g=app.game;g.reset();g.schedule=lambda:None
    g.px,g.py=128,266
    for kind in C.AREA_ITEM['kinds']:
        g.items.current=AreaItem(0,64,200,kind,cycle=.7)
        app.draw();p.screenshot(str(folder/(kind+'.png')),scale=2)
    assert len(p.colors)==52
    result=dict(version=C.VERSION,engine='actual Pyxel 2.9.9',fixture=True,
                screenshots=list(C.AREA_ITEM['kinds']),sounds={})
    g.bullets=[Bullet(64,200,0,0)];app.draw()
    from assets import SPRITES
    u,v,w,h=SPRITES['bullet']
    for dy in range(h):
        for dx in range(w):
            color=p.images[0].pget(u+dx,v+dy)
            if color:assert p.screen.pget(64-w//2+dx,200-h//2+dy)==color
    p.screenshot(str(folder/'bullet-over-item.png'),scale=2);g.bullets=[]
    result['bulletsVisibleOverItem']=True
    for kind,event,sound in (('heal','pickup_heal',17),('axe','pickup_weapon',18)):
        g.hp=2;g.items.current=AreaItem(0,g.px,g.py,kind,cycle=.799)
        g.step(1/C.FPS);assert event in g.events
        app.audio.update(g);app.draw();p.screenshot(str(folder/('pickup-'+kind+'.png')),scale=2)
        assert p.play_pos(3) is not None
        result['sounds'][str(sound)]=dict(notes=list(p.sounds[sound].notes),playing=list(p.play_pos(3)))
    assert g.weapon=='axe';g.cooldown=0;g.start_slash()
    g.items.current=AreaItem(0,g.px,g.py,'lance');g.step(1/C.FPS)
    assert g.weapon=='lance' and g.swing_weapon=='axe'
    assert abs(g.cooldown-(C.WEAPONS['axe']['cooldown']-1/C.FPS))<1e-8
    app.audio.update(g);app.draw();p.screenshot(str(folder/'axe-swing-lance-equipped.png'),scale=2)
    while g.swing>=0:g.step(1/C.FPS)
    while g.cooldown>0:g.step(1/C.FPS)
    assert g.start_slash();assert g.swing_weapon=='lance'
    for _ in range(7):g.step(1/C.FPS)
    app.draw();p.screenshot(str(folder/'next-lance.png'),scale=2)
    result.update(result='PASS',displayedKindPickup=True,oldAttackCompletes=True,
                  nextAttackNewWeapon=True,oldCooldownPreserved=True,paletteColors=len(p.colors))
    (folder/'result.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print('ITEMS_RUNTIME_PASS',json.dumps(result),flush=True);p.quit()

p.run=run
main.App()
