"""空き領域に編集可能な斧頭と槍穂を一度だけ追加。ビルド/起動では呼ばない。"""
from pathlib import Path
import sys,zipfile,tomllib,json,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pyxel as p
import config as C
ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'verification/v0.8.0'
target=ROOT/C.RESOURCE_FILE
backup=folder/'before/assets/blade.pyxres'
def read(file):
    with zipfile.ZipFile(file) as z:return tomllib.loads(z.read('pyxel_resource.toml').decode())
def pixel(bank,x,y):
    data=bank['data'];return data[y][x] if y<len(data) and x<len(data[y]) else 0
def new_area(x,y):return (192<=x<206 and 0<=y<14) or (208<=x<236 and 0<=y<5)
before=read(target)
assert target.read_bytes()==backup.read_bytes()
assert all(not pixel(before['images'][0],x,y) for y in range(256) for x in range(256) if new_area(x,y))
p.init(256,256,title='Add editable melee weapons')
p.colors[:]=C.PALETTE;p.load(str(target));im=p.images[0]
im.rect(192,0,14,14,33);im.rect(194,1,11,12,37)
im.rect(202,0,4,14,46);im.line(205,0,205,13,3)
im.rect(193,4,7,6,16);im.rect(195,5,4,4,10)
im.rect(208,0,28,5,33);im.rect(209,1,26,3,40)
im.line(208,2,235,2,3);im.line(225,1,235,1,51)
p.save(str(target))
after=read(target)
for bank,(old,new) in enumerate(zip(before['images'],after['images'])):
    for y in range(256):
        for x in range(256):
            if bank==0 and new_area(x,y):continue
            assert pixel(old,x,y)==pixel(new,x,y),(bank,x,y)
for key in ('sounds','musics','tilemaps'):assert before[key]==after[key],key
(folder/'resource-addition.json').write_text(json.dumps(dict(
    before_sha256=hashlib.sha256(backup.read_bytes()).hexdigest(),
    after_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
    image_rects=[[192,0,14,14],[208,0,28,5]],sounds_added=[],
    all_prior_pixels_sounds_music_and_tilemaps_preserved=True,palette_unchanged=True),indent=2),encoding='utf8')
print('WEAPON_RESOURCE_ADDED',flush=True);p.quit()
