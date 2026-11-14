"""第3面の画像・曲・SEを空き領域へ一度だけ追加。既存素材は検証して保持。"""
from pathlib import Path
import sys,hashlib,json,zipfile,tomllib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pyxel as p
import config as C
from assets import SPRITES

ROOT=Path(__file__).resolve().parents[1]
def read(path):
    with zipfile.ZipFile(path) as z:return tomllib.loads(z.read('pyxel_resource.toml').decode())
def main():
    folder=ROOT/'verification'/('v'+C.VERSION);target=ROOT/C.RESOURCE_FILE
    backup=ROOT/'verification/v0.15.0/before'/C.RESOURCE_FILE
    assert backup.read_bytes()==target.read_bytes(),'Already edited; never overwrite Editor work'
    before=read(target)
    p.init(C.WIDTH,C.HEIGHT,title='Stage 3 editable resources');p.colors[:]=C.PALETTE;p.load(str(target))
    image=p.images[0];names=('barrier','final_fighter','final_warning','reflected','reflect_bullet','cave_tile')
    for name in names:
        u,v,w,h=SPRITES[name]
        assert all(image.pget(u+x,v+y)==0 for y in range(h) for x in range(w)),name
    u,v,_,_=SPRITES['barrier']
    for y in range(24):
        for x in range(24):
            if abs(x-11.5)<4 and 2<y<22:image.pset(u+x,v+y,40 if x<12 else 34)
            elif 7<=y<=17 and 3<=x<=20:image.pset(u+x,v+y,5 if y<12 else 25)
            if (x-11.5)**2+(y-10)**2<9:image.pset(u+x,v+y,39)
    for name in ('final_fighter','final_warning'):
        u,v,_,_=SPRITES[name];body=10 if name=='final_warning' else 41
        for y in range(32):
            for x in range(40):
                dx=abs(x-19.5)
                if dx<4 and 3<=y<=29:color=body if x<20 else 34
                elif 11<=y<=19 and dx<13:color=body
                elif 8<=dx<=11 and 15<=y<=27:color=25
                elif 14<=dx<=18 and 20<=y<=28:color=body
                else:continue
                if dx<2 and 8<=y<=13:color=12
                image.pset(u+x,v+y,color)
    for name,color in (('reflected',6),('reflect_bullet',12)):
        u,v,_,_=SPRITES[name]
        for y in range(8):
            for x in range(8):
                d=abs(x-3.5)+abs(y-3.5)
                if d<=4:image.pset(u+x,v+y,3 if d<2 else color)
    u,v,_,_=SPRITES['cave_tile']
    for y in range(16):
        for x in range(16):image.pset(u+x,v+y,1 if (x+y*3)%17<3 else 25 if (x*2+y)%19<4 else 0)
    for slot in (22,23,62,63):assert not before['sounds'][slot]['notes'],slot
    # Sound32〜35はMusic0〜3が参照しない旧仮曲。原本はbeforeへ保存済み。
    assert not any(n in (32,33,34,35) for m in before['musics'][:4] for seq in m['seqs'] for n in seq)
    p.sounds[62].set('c3g3c4g4','p','4653','s',4)
    p.sounds[63].set('c4g3e3','t','643','f',5)
    songs=(
      (22,4,('b2r f#3r d3r e3r b2r a3r f#3r e3r '*2,'e3r b3r g3r f#3r e3r d3r f#3r b2r '*2),
             ('b1r b1r f#2r b1r '*4,'e2r e2r b1r f#2r '*4)),
      (32,5,('c3r c#3r g3r d#3r c4r g3r f#3r g3r '*2,'d3r d#3r a3r f3r d4r a3r g#3r a3r '*2),
             ('c2r g2r c2r d#2r '*4,'d2r a2r d2r f2r '*4)),
      (34,6,('c3r e3r g3r c4r b3r g3r e3r d3r '*2,'f3r a3r c4r e4r d4r c4r g3r e3r '*2),
             ('c2r g2r c3r g2r '*4,'f2r c3r g2r c3r '*4)))
    for first,music,leads,basses in songs:
        lead=' '.join(leads[0].split()[:8]+leads[1].split()[:8])
        bass=' '.join(basses[0].split()[:8]+basses[1].split()[:8])
        for i,notes in enumerate((lead,bass)):
            p.sounds[first+i].set(notes,'t' if i==0 else 'p','3' if i==0 else '2','n',14 if music==6 else 12)
            assert len(p.sounds[first+i].notes)<=48
        p.musics[music].set([first],[first+1],[],[])
    assert len(p.sounds)==p.NUM_SOUNDS==64
    temp=folder/'stage3.pyxres';p.save(temp.as_posix())
    target.write_bytes(temp.read_bytes());temp.unlink();after=read(target)
    for bank,(old,new) in enumerate(zip(before['images'],after['images'])):
        for y,row in enumerate(old['data']):
            for x,color in enumerate(row):
                if color:assert new['data'][y][x]==color,(bank,x,y)
    for i,(old,new) in enumerate(zip(before['sounds'],after['sounds'])):
        if i not in (22,23,32,33,34,35,62,63):assert old==new,i
    assert before['musics'][:4]==after['musics'][:4]
    assert before['tilemaps']==after['tilemaps']
    result=dict(before_sha256=hashlib.sha256(backup.read_bytes()).hexdigest(),
      after_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),sprites_added=names,
      sounds_added=[22,23,62,63],legacy_unused_slots_reused=[32,33,34,35],standard_editor_sound_count=64,musics_added=[4,5,6],
      existing_images_sfx_other_music_preserved=True)
    (folder/'resource-addition.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print('STAGE3_ASSETS',json.dumps(result),flush=True);p.quit()
if __name__=='__main__':main()
