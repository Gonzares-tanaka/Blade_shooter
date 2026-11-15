"""0.16: existing atlas art is preserved except the deliberately revised cave tile."""
from pathlib import Path
import sys,hashlib,json,zipfile,tomllib,math
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pyxel as p
import config as C
ROOT=Path(__file__).resolve().parents[1]
def data(file):
 with zipfile.ZipFile(file) as z:return tomllib.loads(z.read('pyxel_resource.toml').decode())
def main():
 folder=ROOT/'verification/v0.16.0';target=ROOT/C.RESOURCE_FILE;backup=folder/'before'/C.RESOURCE_FILE
 prior=folder/'resource-addition.json'
 allowed={hashlib.sha256(backup.read_bytes()).hexdigest()}
 if prior.exists():allowed.add(json.loads(prior.read_text())['after_sha256'])
 assert hashlib.sha256(target.read_bytes()).hexdigest() in allowed,'Never overwrite later Editor work'
 before=data(backup);p.init(256,320,title='Editable lunar rock faces');p.colors[:]=C.PALETTE;p.load(str(backup));im=p.images[0]
 # A separate 128x128 Image1 atlas prevents tiny repeated brick-like patterns.
 im=p.images[1]
 assert all(im.pget(x,y)==0 for y in range(128) for x in range(128))
 seeds=((4,9),(39,4),(72,17),(112,3),(17,43),(53,37),(98,45),(125,35),
        (3,79),(38,73),(77,84),(113,78),(16,118),(58,112),(91,123),(127,117))
 for y in range(128):
  for x in range(128):
   xx=x+3*math.sin(y*.09);yy=y+2*math.sin(x*.11)
   ds=sorted(((xx-a)**2+(yy-b)**2,i) for i,(a,b) in enumerate(seeds))
   col=16 if ds[0][1]%4 else 1
   if ds[1][0]-ds[0][0]<24:col=1
   # Small mineral facets, no bright projectile-colored flecks.
   if ds[0][1] in (2,9,13) and ds[0][0]<45 and x<seeds[ds[0][1]][0]:col=2
   im.pset(x,y,col)
 im=p.images[0]
 # Background texture is darker and has no bright solid rim.
 for y in range(16):
  for x in range(16):
   col=1 if 2<x<13 and 2<y<13 and x+y>8 and x-y<8 else 0
   if x==6+(y//4) and 4<y<12:col=0
   im.pset(224+x,240+y,col)
 temp=folder/'rock.pyxres';p.save(temp.as_posix());after=data(temp)
 def pixel(bank,x,y):
  a=bank['data'];return a[y][x] if y<len(a) and x<len(a[y]) else 0
 for bank,(old,new) in enumerate(zip(before['images'],after['images'])):
  for y in range(256):
   for x in range(256):
    changed=(bank==1 and x<128 and y<128) or (bank==0 and 224<=x<240 and 240<=y<256)
    if not changed:assert pixel(old,x,y)==pixel(new,x,y),(bank,x,y)
 for key in ('sounds','musics','tilemaps'):assert before[key]==after[key],key
 target.write_bytes(temp.read_bytes());temp.unlink()
 result=dict(before_sha256=hashlib.sha256(backup.read_bytes()).hexdigest(),after_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
  sprites_added=['Image1:0,0,128,128 rock mass atlas'],sprites_revised=['cave_tile'],all_sounds_music_tilemaps_preserved=True,
  existing_images_sfx_other_music_preserved=True,standard_editor_sound_count=64)
 (folder/'resource-addition.json').write_text(json.dumps(result,indent=2),encoding='utf8')
 print(json.dumps(result));p.quit()
if __name__=='__main__':main()
