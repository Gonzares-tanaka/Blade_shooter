"""Compare supplied PNGs with the already edited master atlas; never modify art."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pyxel as p
import config as C
from assets import SPRITES,load_resources
ROOT=Path(__file__).resolve().parents[1];folder=ROOT/'verification/v0.16.2'
rows=(('missile_carrier','misaile.png',24,24),('homing_missile','missaile1.png',16,16),
 ('stealth','2boss_1.png',32,16),('stealth_warning','2boss_2.png',32,16),('barrier','shield.png',24,24),
 ('final_fighter','3boss_1.png',40,32),('final_warning','3boss_2.png',40,32))
p.init(512,640,title='Supplied enemy graphics / atlas comparison');load_resources(p);p.cls(0);records=[]
p.text(8,8,'CURRENT GAME CROP                 SUPPLIED PNG',6)
for i,(name,file,w,h) in enumerate(rows):
 u,v,cw,ch=SPRITES[name];y=32+i*84;p.text(8,y,name,3)
 p.blt(36,y+24,0,u,v,cw,ch,0,scale=2)
 p.images[2].cls(0);p.images[2].load(0,0,str(folder/'sources'/file))
 p.blt(292,y+24,2,0,0,w,h,0,scale=2)
 mismatch=[(x,yy) for yy in range(h) for x in range(w) if p.images[0].pget(u+x,v+yy)!=p.images[2].pget(x,yy)]
 # White border in supplied PNGs is intentionally transparent in the user's edited atlas.
 from collections import deque
 outside=set();queue=deque((x,yy) for yy in range(h) for x in range(w) if (x in (0,w-1) or yy in (0,h-1)) and p.images[2].pget(x,yy)==3)
 while queue:
  x,yy=queue.popleft()
  if (x,yy) in outside:continue
  outside.add((x,yy))
  for xx,yyy in ((x-1,yy),(x+1,yy),(x,yy-1),(x,yy+1)):
   if 0<=xx<w and 0<=yyy<h and (xx,yyy) not in outside and p.images[2].pget(xx,yyy)==3:queue.append((xx,yyy))
 if name=='homing_missile':
  # The user placed this 16px PNG two pixels left within its atlas reservation.
  normalized=sum(p.images[0].pget(224+x,64+yy)!=(p.images[2].pget(x+2,yy) if x+2<w else 0) for yy in range(h) for x in range(w))
 else:normalized=sum(p.images[0].pget(u+x,v+yy)!=(0 if (x,yy) in outside else p.images[2].pget(x,yy)) for yy in range(h) for x in range(w))
 assert normalized==0,(name,normalized)
 record=dict(sprite=name,source=file,source_size=[w,h],game_size=[cw,ch],mismatched_pixels=len(mismatch),difference_after_white_border=normalized)
 if name=='homing_missile':
  record['atlas_rows']=[''.join(format(p.images[0].pget(u+x,v+yy),'x') if p.images[0].pget(u+x,v+yy) else '.' for x in range(16)) for yy in range(16)]
  record['source_rows']=[''.join(format(p.images[2].pget(x,yy),'x') if (x,yy) not in outside and p.images[2].pget(x,yy) else '.' for x in range(16)) for yy in range(16)]
 records.append(record)
p.screenshot(str(folder/'atlas-comparison.png'))
(folder/'png-comparison.json').write_text(json.dumps(records,indent=2),encoding='utf8')
print(json.dumps(records),flush=True);p.quit()
