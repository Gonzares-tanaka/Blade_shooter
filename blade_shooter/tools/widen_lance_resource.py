"""穂先の空き領域を16px幅へ拡張。既存5行と他素材は保持する一度だけの編集。"""
from pathlib import Path
import sys,zipfile,tomllib,json,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import config as C
import pyxel as p
ROOT=Path(__file__).resolve().parents[1];folder=ROOT/'verification/v0.9.0'
target=ROOT/C.RESOURCE_FILE;backup=folder/'before/assets/blade.pyxres'
def read(file):
 with zipfile.ZipFile(file) as z:return tomllib.loads(z.read('pyxel_resource.toml').decode())
def pixel(bank,x,y):
 d=bank['data'];return d[y][x] if y<len(d) and x<len(d[y]) else 0
def added(x,y):return 208<=x<236 and 5<=y<16
before=read(target);assert target.read_bytes()==backup.read_bytes()
assert all(not pixel(before['images'][0],x,y) for y in range(256) for x in range(256) if added(x,y))
p.init(256,256,title='Widen editable lance tip');p.colors[:]=C.PALETTE;p.load(str(target));im=p.images[0]
# 旧5行を残し、下に追加。全16行が不透明で判定の矩形と一致する。
im.rect(208,5,28,11,33);im.rect(209,5,26,9,40);im.line(208,8,235,8,3)
im.line(225,14,235,14,51);im.line(208,15,235,15,34)
p.save(str(target));after=read(target)
for bank,(old,new) in enumerate(zip(before['images'],after['images'])):
 for y in range(256):
  for x in range(256):
   if bank==0 and added(x,y):continue
   assert pixel(old,x,y)==pixel(new,x,y),(bank,x,y)
for key in ('sounds','musics','tilemaps'):assert before[key]==after[key]
(folder/'resource-addition.json').write_text(json.dumps(dict(before_sha256=hashlib.sha256(backup.read_bytes()).hexdigest(),after_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),image_rects=[[208,5,28,11]],all_prior_pixels_sounds_music_and_tilemaps_preserved=True,palette_unchanged=True),indent=2),encoding='utf8')
print('LANCE_WIDTH_RESOURCE_16PX',flush=True);p.quit()
