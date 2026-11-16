"""One-time sync of the user-edited master images; never called by builds."""
from pathlib import Path
import sys,json,hashlib,zipfile,tomllib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pyxel as p
import config as C
from assets import SPRITES,load_resources
ROOT=Path(__file__).resolve().parents[1];FOLDER=ROOT/'verification/v0.17.1'
def read(path):
    with zipfile.ZipFile(path) as z:return tomllib.loads(z.read('pyxel_resource.toml').decode())
def pixel(bank,x,y):
    rows=bank['data'];return rows[y][x] if y<len(rows) and x<len(rows[y]) else 0

def main():
    master=ROOT/C.RESOURCE_FILE;source=FOLDER/'before/user-edited.pyxres'
    assert master.read_bytes()==source.read_bytes()
    p.init(256,320,title='Sync edited item and battleship art');load_resources(p)
    images=[p.Image(256,256) for _ in p.images]
    for saved,current in zip(images,p.images):saved.blt(0,0,current,0,0,256,256)
    comparisons=[]
    for name,file in (('item_blade','blade.png'),('item_axe','ax.png'),('item_lance','yari.png'),
                      ('boss_hull','1boss_1.png'),('boss_left','1boss_2.png'),('boss_right','1boss_2.png'),
                      ('boss_center','1boss_3.png'),('boss_destroyed','1boss_4.png')):
        u,v,w,h=SPRITES[name];image=p.Image(256,256);image.load(0,0,str(FOLDER/'sources'/file))
        different=sum(images[0].pget(u+x,v+y)!=image.pget(x,y) for y in range(h) for x in range(w))
        assert different==0,(name,different)
        comparisons.append(dict(sprite=name,source=file,atlas=[u,v,w,h],different_pixels=different))
    before=read(FOLDER/'before/published.pyxres');edited=read(master)
    changed=[]
    names=('item_heal','item_blade','item_axe','item_lance','boss_hull','boss_left','boss_right','boss_center','boss_destroyed')
    for name in names:
        u,v,w,h=SPRITES[name]
        count=sum(pixel(before['images'][0],u+x,v+y)!=pixel(edited['images'][0],u+x,v+y) for y in range(h) for x in range(w))
        changed.append(dict(sprite=name,atlas=[u,v,w,h],changed_pixels=count))
    for i,(old,new) in enumerate(zip(before['images'],edited['images'])):
        for y in range(256):
            for x in range(256):
                if i==0 and any(u<=x<u+w and v<=y<v+h for name in names for u,v,w,h in (SPRITES[name],)):continue
                assert pixel(old,x,y)==pixel(new,x,y),(i,x,y)
    for path in C.AUDIO_BANKS.values():
        target=ROOT/path;old=read(target)
        p.load(str(target))
        for current,saved in zip(p.images,images):current.blt(0,0,saved,0,0,256,256)
        p.save(str(target));new=read(target)
        assert new['images']==edited['images']
        for key in ('sounds','musics','tilemaps'):assert new[key]==old[key],(path,key)
    assert master.read_bytes()==source.read_bytes()
    for key in ('sounds','musics','tilemaps'):assert before[key]==edited[key],key
    report=dict(after_sha256=hashlib.sha256(master.read_bytes()).hexdigest(),
                existing_images_sfx_other_music_preserved=True,master_preserved_byte_for_byte=True,
                prior_non_target_pixels_preserved=True,sounds_music_tilemaps_unchanged=True,
                synchronized_banks=list(C.AUDIO_BANKS.values()),sprites=changed,png_comparisons=comparisons)
    (FOLDER/'resource-addition.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps(report),flush=True);p.quit()
if __name__=='__main__':main()
