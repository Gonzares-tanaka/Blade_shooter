"""v0.17.0 supplied logo, title/ending MML and hurt SE import. Never run by build."""
from pathlib import Path
import sys, shutil, hashlib, json, zipfile, tomllib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import config as C
import pyxel as p
from tools.convert_stage_bgm import convert
ROOT=Path(__file__).resolve().parents[1]
def read(path):
    with zipfile.ZipFile(path) as z:return tomllib.loads(z.read("pyxel_resource.toml").decode())
def add_common():
    p.colors[:]=C.PALETTE
    p.images[2].cls(0)
    p.images[2].load(0,0,str(ROOT/"assets/title.png"))
    sound=p.sounds[5]
    sound.notes[:]=[45,39,32,25,16,8]
    sound.tones[:]=[2,3,2,3,2,3]
    sound.volumes[:]=[7,7,7,6,5,0]
    sound.effects[:]=[0,0,2,2,2,0]
    sound.speed=2

def main():
    p.init(256,320,title="Import title and editable menu music",display_scale=1)
    for path in (C.RESOURCE_FILE,C.AUDIO_BANKS[2],C.AUDIO_BANKS[3]):
        target=ROOT/path;old=read(target)
        p.load(str(target));add_common();p.save(str(target))
        new=read(target)
        assert new['images'][:2]==old['images'][:2]
        assert new['tilemaps']==old['tilemaps'] and new['musics']==old['musics']
        for i,(a,b) in enumerate(zip(old['sounds'],new['sounds'])):
            if i!=5:assert a==b,i
    base=ROOT/C.RESOURCE_FILE
    p.load(str(base))
    for music in p.musics:music.set([],[],[],[])
    for slot in range(22,62):p.sounds[slot].set("","","","",12)
    slot=22;tracks=[]
    for number,spec in C.UI_BGM.items():
        rows=[s for s in (ROOT/spec['file']).read_text(encoding='utf-8-sig').splitlines() if s.startswith('Q')]
        sequences=[]
        for index in spec['tracks']:
            notes=convert(rows[index]);sequence=[]
            assert len(notes)==128
            for start in range(0,len(notes),32):
                chunk=notes[start:start+32];sound=p.sounds[slot]
                for prop,n in (('notes',0),('tones',1),('volumes',2),('effects',3)):
                    getattr(sound,prop)[:]=[v[n] for v in chunk]
                sound.speed=round(1800/spec['tempo'])
                sequence.append(slot);slot+=1
            sequences.append(sequence)
        p.musics[number].set(*sequences)
        tracks.append(dict(music=number,source=spec['file'],source_sha256=hashlib.sha256((ROOT/spec['file']).read_bytes()).hexdigest(),tempo=spec['tempo'],editor_speed=round(1800/spec['tempo']),sequence=sequences,loop_seconds=128*60/spec['tempo']/4))
    assert slot<=62
    target=ROOT/C.AUDIO_BANKS[4];p.save(str(target))
    shutil.copyfile(ROOT/C.PALETTE_FILE,target.with_suffix('.pyxpal'))
    report=dict(after_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),
                existing_images_sfx_other_music_preserved=True,
                intentional_changes=['Image 2 (0,0,256,100) title logo','Sound 5 hurt SE in all banks'],
                preserved=['Image 0 and 1, all tilemaps, all other SFX and existing stage music'],tracks=tracks,
                native_mml_tempo_exact=True,
                editor_approximations=['ENV/volume sampled to 16ths (0-7)','VIB/GLI approximated in Editor notes only','Ending T133 -> Editor speed14 (128.571 BPM); default native MML keeps T133'])
    (ROOT/'verification/v0.17.0/resource-addition.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps(report),flush=True);p.quit()
if __name__=='__main__':main()
