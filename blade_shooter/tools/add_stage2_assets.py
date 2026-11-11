"""第2面のEditor原本への初回追加。既存画素・音・曲を保持する。"""
from pathlib import Path
import sys,json,hashlib,zipfile,tomllib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import config as C
import pyxel as p
from assets import SPRITES

ROOT=Path(__file__).resolve().parents[1]

def read(path):
    with zipfile.ZipFile(path) as z:return tomllib.loads(z.read('pyxel_resource.toml').decode())

def main():
    target=ROOT/C.RESOURCE_FILE;folder=ROOT/'verification/v0.13.0'
    backup=folder/'before'/C.RESOURCE_FILE
    assert target.read_bytes()==backup.read_bytes()
    before=read(target)
    p.init(C.WIDTH,C.HEIGHT,title='Stage 2 editable assets');p.colors[:]=C.PALETTE;p.load(str(target))
    image=p.images[0]
    names=('asteroid','missile_carrier','homing_missile','stealth','stealth_warning','distant_rock')
    for name in names:
        u,v,w,h=SPRITES[name]
        assert all(image.pget(u+x,v+y)==0 for y in range(h) for x in range(w)),name
    # ゲーム内で描画を生成せず、素材の画素を保存してEditorで編集できるようにする。
    u,v,_,_=SPRITES['asteroid']
    for y in range(24):
        for x in range(24):
            dx,dy=x-11.5,y-11.5
            if dx*dx+dy*dy<108 and not (x<4 and y<7):
                color=16 if x+y>24 else 2 if x+y<15 else 1
                if (x-8)**2+(y-9)**2<12:color=1 if x+y<17 else 16
                if (x-16)**2+(y-16)**2<7:color=0 if x+y>32 else 1
                image.pset(u+x,v+y,color)
    u,v,_,_=SPRITES['missile_carrier']
    for y in range(24):
        for x in range(24):
            if abs(x-11.5)<4 and 2<=y<=21:color=25 if x<11 else 6
            elif 5<=y<=18 and (2<=x<=7 or 16<=x<=21):color=1 if y>12 else 2
            else:continue
            if y in (7,13) and (x in range(3,7) or x in range(17,21)):color=10
            image.pset(u+x,v+y,color)
    u,v,_,_=SPRITES['homing_missile']
    for y in range(16):
        for x in range(8):
            if 2<=x<=5 and 2<=y<=12:image.pset(u+x,v+y,3 if y<5 else 10 if x<4 else 11)
            if y>=11 and abs(x-3.5)<(y-9)/2:image.pset(u+x,v+y,37 if y<14 else 10)
    for name,base in (('stealth',33),('stealth_warning',10)):
        u,v,_,_=SPRITES[name]
        for y in range(16):
            for x in range(32):
                dx=abs(x-15.5)
                if 2<=y<=13 and dx<(y-1)*1.25 and (y<10 or dx>y-8):
                    color=base if x<16 or y in (3,8,12) else 25
                    if dx<2 and y<8:color=40 if name=='stealth' else 3
                    image.pset(u+x,v+y,color)
    u,v,_,_=SPRITES['distant_rock']
    for y in range(16):
        for x in range(16):
            if (x-7)**2+(y-8)**2<35:image.pset(u+x,v+y,25 if x+y<12 else 1)
    for slot in (19,20,21,*range(24,32)):assert not before['sounds'][slot]['notes'],slot
    p.sounds[19].set('c3r','n','31','n',5)
    p.sounds[20].set('g3d3a2c2','n','6531','f',6)
    p.sounds[21].set('c2g2d3a3','p','2342','s',5)
    stage_lead=('c3r g3r d3r g3r a#3r g3r d3r f3r '*2,
                'd#3r a#3r f3r a#3r c4r a#3r f3r g3r '*2)
    stage_bass=('c2r c2r c2r g2r '*4,'d#2r d#2r a#2r g2r '*4)
    boss_lead=('g3r a#3r d4r a3r g3r d4r c4r a#3r '*2,
               'f#3r a3r c4r d4r c4r a3r g3r f#3r '*2)
    boss_bass=('g2r d2r g2r a#2r '*4,'d2r a2r d2r f#2r '*4)
    for first,leads,basses,music in ((24,stage_lead,stage_bass,2),(28,boss_lead,boss_bass,3)):
        for i,notes in enumerate((*leads,*basses)):
            p.sounds[first+i].set(notes,'t' if i<2 else 'p','3' if i<2 else '2','n',12)
            assert len(p.sounds[first+i].notes)==32
        p.musics[music].set([first,first+1],[first+2,first+3],[],[])
    temporary=folder/'stage2.pyxres';p.save(temporary.as_posix())
    target.write_bytes(temporary.read_bytes());temporary.unlink();after=read(target)
    for i,(old,new) in enumerate(zip(before['sounds'],after['sounds'])):
        if i not in (19,20,21,*range(24,32)):assert old==new,i
    assert before['musics'][:2]==after['musics'][:2]
    assert before['tilemaps']==after['tilemaps']
    for bank,(old,new) in enumerate(zip(before['images'],after['images'])):
        for y,row in enumerate(old['data']):
            for x,color in enumerate(row):
                if color:assert new['data'][y][x]==color,(bank,x,y)
    result=dict(before_sha256=hashlib.sha256(backup.read_bytes()).hexdigest(),
                after_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                sprites_added=list(names),sounds_added=[19,20,21,*range(24,32)],musics_added=[2,3],
                existing_images_sfx_other_music_preserved=True)
    (folder/'resource-addition.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print('STAGE2_ASSETS',json.dumps(result),flush=True);p.quit()

if __name__=='__main__':main()
