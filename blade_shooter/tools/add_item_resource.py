"""空き画像4枠とSE17/18だけに追加。起動・ビルドからは実行しない。"""
from pathlib import Path
import sys,zipfile,tomllib,json,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import config as C
import pyxel as p
ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'verification/v0.11.0'
target=ROOT/C.RESOURCE_FILE
backup=folder/'before'/C.RESOURCE_FILE

def read(file):
    with zipfile.ZipFile(file) as z:return tomllib.loads(z.read('pyxel_resource.toml').decode())
def pixel(bank,x,y):
    d=bank['data'];return d[y][x] if y<len(d) and x<len(d[y]) else 0
before=read(target)
assert target.read_bytes()==backup.read_bytes()
assert all(not pixel(before['images'][0],x,y) for y in range(96,112) for x in range(64))
assert all(not before['sounds'][i]['notes'] for i in (17,18))
p.init(256,256,title='Editable area item icons and pickup sounds')
p.colors[:]=C.PALETTE;p.load(str(target));im=p.images[0]
# ハート。武器は各々異なるシルエット。色以外でも判別できる。
im.circ(4,101,3,8);im.circ(10,101,3,8);im.tri(1,102,13,102,7,110,8)
im.line(3,99,5,99,3);im.pset(2,100,3)
# 剣: 斜めの直剣＋鍔。
im.tri(19,106,27,97,29,97,40);im.tri(19,106,29,97,28,100,3)
im.line(18,104,22,108,10);im.line(19,107,17,109,37)
# 斧: 短い柄＋大きい片刃。
im.rect(38,100,2,11,37);im.rect(39,99,7,6,40)
im.line(45,98,45,105,3);im.line(40,99,44,99,3)
# 槍: 長い縦の柄＋矢じり。
im.rect(55,102,2,9,37);im.tri(56,96,52,104,60,104,40)
im.line(56,97,56,103,3);im.line(53,105,59,105,10)
p.sounds[17].set('c3e3g3c4','t','6543','n',7)
p.sounds[18].set('g2c3g3','p','654','n',6)
p.save(str(target));after=read(target)
for bank,(old,new) in enumerate(zip(before['images'],after['images'])):
    for y in range(256):
        for x in range(256):
            if bank==0 and 0<=x<64 and 96<=y<112:continue
            assert pixel(old,x,y)==pixel(new,x,y),(bank,x,y)
for i,(old,new) in enumerate(zip(before['sounds'],after['sounds'])):
    if i not in (17,18):assert old==new,('sound',i)
for key in ('musics','tilemaps'):assert before[key]==after[key],key
(folder/'resource-addition.json').write_text(json.dumps(dict(
    before_sha256=hashlib.sha256(backup.read_bytes()).hexdigest(),
    after_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
    image_rects=[[x,96,16,16] for x in (0,16,32,48)],sounds_added=[17,18],
    all_prior_pixels_sounds_music_and_tilemaps_preserved=True,palette_unchanged=True),indent=2),encoding='utf8')
print('ITEM_RESOURCE_ADDED',flush=True);p.quit()
