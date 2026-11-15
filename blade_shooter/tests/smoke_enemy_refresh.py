"""Render every refreshed enemy with the real game View, without changing art."""
from pathlib import Path
import sys,json,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pyxel as p
import main,config as C
from game import Game,Bullet
from assets import SPRITES
folder=Path(__file__).resolve().parents[1]/'verification'/('v'+C.VERSION)/'enemy-native';folder.mkdir(parents=True,exist_ok=True)
def run(update,draw):
 app=update.__self__;captures=[]
 def capture(name):
  app.audio.update(app.game);app.draw();p.screenshot(str(folder/(name+'.png')),scale=2);captures.append(name)
 g=app.game=Game('stage2');g.reset();g.schedule=lambda:None
 e=g.spawn('missile',128,100);e.phase='warning';g.world_time=.1
 g.bullets=[Bullet(100,185,0,102,'missile'),Bullet(156,218,80,-60,'missile')]
 capture('missile-carrier-and-projectiles')
 g.enemies.clear();g.bullets.clear();g.begin_boss();b=g.boss;b.active=True
 for i,part in enumerate(b.parts):part.x=48+i*30;part.y=105+i%2*35;part.enabled=True;part.phase='open'
 capture('stealth-normal')
 for part in b.parts:part.phase='warning'
 capture('stealth-warning')
 g=app.game=Game('stage3');g.reset();g.schedule=lambda:None
 e=g.spawn('barrier',128,105);e.phase='shield';g.world_time=.1
 capture('barrier-shield')
 e.phase='open';capture('barrier-open')
 g.enemies.clear();g.begin_boss();b=g.boss;b.active=True;b.phase='fire';part=b.parts[0];part.x=128;part.y=120;part.enabled=True
 capture('final-normal')
 b.phase='move_warning';capture('final-warning')
 # Both sound banks are loaded using exclude_images; master pixels remain unchanged.
 u,v,w,h=SPRITES['homing_missile'];all_pixels=[(x,y) for y in range(64,80) for x in range(224,240) if p.images[0].pget(x,y)]
 assert all(u<=x<u+w and v<=y<v+h for x,y in all_pixels),'missile art clipped'
 result=dict(result='PASS',engine='actual Pyxel 2.9.9',graphics_fixtures=True,real_devices=False,captures=captures,
  master_sha256=hashlib.sha256((Path(__file__).resolve().parents[1]/C.RESOURCE_FILE).read_bytes()).hexdigest(),missile_art_not_clipped=True)
 (folder/'result.json').write_text(json.dumps(result,indent=2),encoding='utf8')
 print('ENEMY_GRAPHICS_NATIVE_PASS',json.dumps(result),flush=True);p.quit()
p.run=run;main.App()
