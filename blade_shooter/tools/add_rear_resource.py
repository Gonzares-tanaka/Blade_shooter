"""空き領域にv0.4素材を一度だけ追加。通常ビルド・起動からは呼ばない。"""
from pathlib import Path
import sys, shutil, zipfile, tomllib, json, hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import config as C
import pyxel as p

ROOT=Path(__file__).resolve().parents[1]
target=ROOT/C.RESOURCE_FILE
def read(path):
    with zipfile.ZipFile(path) as z:
        return tomllib.loads(z.read('pyxel_resource.toml').decode())
before=read(target)
for row in before['images'][0]['data'][32:56]:
    if any(row[144:192]): raise SystemExit('New sprite area already occupied; will not overwrite.')
if any(before['sounds'][i]['notes'] for i in (10,11)):
    raise SystemExit('Sound 10/11 already occupied; will not overwrite.')
backup=ROOT/'verification'/'v0.3.0'/'before-rear'
backup.mkdir(parents=True,exist_ok=True)
for name in (C.RESOURCE_FILE,C.PALETTE_FILE,'README.md','VERIFICATION.md',
             'dist/blade-shooter-web.zip','dist/blade-shooter-gkd.zip'):
    dst=backup/Path(name).name
    if (ROOT/name).exists() and not dst.exists(): shutil.copy2(ROOT/name,dst)
palette=(ROOT/C.PALETTE_FILE).read_bytes()
p.init(256,256,title='Add rear enemy resource')
p.colors[:]=C.PALETTE
p.load(str(target))
im=p.images[0]
for ox,bright in ((144,False),(168,True)):
    # U字の側面フックと、上向きの砲身。下向き三角の既存敵と区別する。
    col=10 if bright else 39
    im.rect(ox+3,38,4,14,33);im.rect(ox+17,38,4,14,33)
    im.rect(ox+4,49,16,5,col)
    im.tri(ox+3,37,ox+7,37,ox+5,33,col)
    im.tri(ox+17,37,ox+21,37,ox+19,33,col)
    im.rect(ox+9,41,6,10,7);im.rect(ox+10,37,4,12,col)
    im.tri(ox+8,39,ox+16,39,ox+12,33,3 if bright else 6)
    im.line(ox+5,41,ox+5,48,51);im.line(ox+19,41,ox+19,48,51)
    im.rect(ox+10,51,4,2,3)
p.sounds[10].set('c3e3g3','t','343','n',4)
p.sounds[11].set('g2c3','p','43','f',3)
p.save(str(target))
after=read(target)
# Pyxelの再保存で、以前のEditor編集を消していないことを全バンクで照合。
for bank,(old,new) in enumerate(zip(before['images'],after['images'])):
    for y in range(256):
        for x in range(256):
            if bank==0 and 144<=x<192 and 32<=y<56: continue
            def pixel(image):
                data=image['data']
                return data[y][x] if y<len(data) and x<len(data[y]) else 0
            assert pixel(old)==pixel(new),(bank,x,y)
for key in ('sounds','musics','tilemaps'):
    for i,(old,new) in enumerate(zip(before[key],after[key])):
        if key=='sounds' and i in (10,11):continue
        assert old==new,(key,i)
assert (ROOT/C.PALETTE_FILE).read_bytes()==palette
folder=ROOT/'verification'/'v0.4.0'
folder.mkdir(exist_ok=True)
(folder/'resource-addition.json').write_text(json.dumps(dict(
    before_sha256=hashlib.sha256((backup/'blade.pyxres').read_bytes()).hexdigest(),
    after_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
    added_image_0_rect=[144,32,48,24],added_sounds=[10,11],
    old_pixels_sounds_music_tilemaps_unchanged=True,palette_unchanged=True),indent=2),encoding='utf-8')
print('Added rear sprites and sounds; all previous resource content preserved.',flush=True)
p.quit()
