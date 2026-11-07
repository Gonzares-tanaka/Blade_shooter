"""空き領域に戦艦画像・音を一度だけ追加。通常起動・ビルドからは呼ばない。"""
from pathlib import Path
import sys,zipfile,tomllib,json,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pyxel as p
import config as C

ROOT=Path(__file__).resolve().parents[1]
target=ROOT/C.RESOURCE_FILE
folder=ROOT/'verification/v0.7.0'
backup=folder/'before/blade.pyxres'

def read(file):
    with zipfile.ZipFile(file) as z:return tomllib.loads(z.read('pyxel_resource.toml').decode())

def pixel(bank,x,y):
    data=bank['data']
    return data[y][x] if y<len(data) and x<len(data[y]) else 0

def new_area(x,y):
    return (0<=x<224 and 112<=y<216) or (0<=x<112 and 224<=y<256)

before=read(target)
assert backup.exists(),'Archive the old original before adding resources'
assert all(not pixel(before['images'][0],x,y) for y in range(256) for x in range(256) if new_area(x,y)), 'Boss area occupied; not overwriting Editor changes'
assert all(not before['sounds'][i]['notes'] for i in (*range(12,17),*range(36,40)))
assert not any(before['musics'][1]['seqs'])
palette=(ROOT/C.PALETTE_FILE).read_bytes()
p.init(256,256,title='Add editable dreadnought resource')
p.colors[:]=C.PALETTE
p.load(str(target))
im=p.images[0]

# 全幅224pxの船体。外板・装甲リブ・艦橋・配線を既存52色で描く。
oy=112
im.rect(32,oy+12,160,76,25)
im.tri(0,oy+24,32,oy+8,32,oy+96,33)
im.tri(224-1,oy+24,192,oy+8,192,oy+96,33)
im.rect(8,oy+26,208,52,33)
im.rect(16,oy+30,192,42,25)
im.rect(36,oy+8,152,80,1)
im.rectb(36,oy+8,152,80,34)
for x in (12,40,68,148,176,204):
    im.rect(x,oy+24,8,52,16)
    im.line(x,oy+24,x,oy+70,34)
    im.rect(x+1,oy+29,4,12,25)
    im.rect(x+1,oy+54,4,10,6)
im.rect(76,oy+6,72,82,25)
im.rectb(76,oy+6,72,82,33)
im.rect(88,oy,48,48,1)
im.rectb(88,oy,48,48,34)
im.rect(96,oy+8,32,20,17)
im.rect(100,oy+12,24,8,6)
for x in range(101,125,6):im.rect(x,oy+12,2,8,51)
im.rect(106,oy+32,12,42,33)
im.line(112,oy+34,112,oy+72,39)
for x in range(28,209,24):
    im.rect(x,oy+80,16,8,16)
    im.line(x,oy+80,x+15,oy+80,34)
    im.rect(x+4,oy+83,8,3,11)
im.rect(36,oy+88,152,8,25)
for x in (48,176):im.rect(x,oy+88,16,16,33)
im.rect(100,oy+88,24,16,33)
for x in (38,182):
    for y in (14,66,84):im.rect(x,oy+y,3,3,40)

# 砲台の絵は別スロット。破壊状態もEditorで編集できる。
for x in (0,24):
    im.circ(x+12,236,11,1);im.circ(x+12,236,9,33)
    im.rect(x+5,228,14,14,25);im.rectb(x+5,228,14,14,34)
    im.rect(x+9,234,6,14,16);im.rect(x+10,236,4,11,40)
    im.rect(x+5,229,3,6,6);im.rect(x+16,229,3,6,6)
im.circ(64,240,15,1);im.circ(64,240,13,33)
im.rect(54,228,20,18,25);im.rectb(54,228,20,18,34)
for x in (57,65):
    im.rect(x,238,6,18,16);im.rect(x+1,239,4,15,40)
im.rect(58,230,12,4,10)
im.circ(96,240,14,1);im.circ(96,240,10,16)
im.line(85,232,104,249,11);im.line(85,248,105,231,1)
im.rect(90,237,12,7,0)
for x,y in ((86,233),(103,246),(92,249)):im.rect(x,y,2,2,37)

p.sounds[12].set('c1c1g1c2','p','7654','f',12)
p.sounds[13].set('c3g3c4','t','345','n',5)
p.sounds[14].set('c1g1','n','54','f',3)
p.sounds[15].set('c2g1c1','n','765','f',7)
p.sounds[16].set('c2g1c1c1','n','7653','f',16)
p.sounds[36].set('c2r c2g2 a#1r g1r','p','4','n',15)
p.sounds[37].set('g1r g1d2 f2r d2r','p','4','n',15)
p.sounds[38].set('c1c1g1g1a#0a#0g0g0','t','3','n',15)
p.sounds[39].set('g0g0d1d1f1f1d1d1','t','3','n',15)
p.musics[1].set([36,37],[38,39],[],[])
p.save(str(target))

after=read(target)
for bank,(old,new) in enumerate(zip(before['images'],after['images'])):
    for y in range(256):
        for x in range(256):
            if bank==0 and new_area(x,y):continue
            assert pixel(old,x,y)==pixel(new,x,y),(bank,x,y)
for key in ('sounds','musics','tilemaps'):
    for i,(old,new) in enumerate(zip(before[key],after[key])):
        if key=='sounds' and i in (*range(12,17),*range(36,40)):continue
        if key=='musics' and i==1:continue
        assert old==new,(key,i)
assert (ROOT/C.PALETTE_FILE).read_bytes()==palette
(folder/'resource-addition.json').write_text(json.dumps(dict(
    before_sha256=hashlib.sha256(backup.read_bytes()).hexdigest(),
    after_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
    image_rects=[[0,112,224,104],[0,224,112,32]],sounds=[12,13,14,15,16,36,37,38,39],music=1,
    all_prior_pixels_sounds_music_and_tilemaps_preserved=True,palette_unchanged=True),indent=2))
print('BOSS_RESOURCE_ADDED',flush=True)
p.quit()
