"""添付ボスMMLをEditor用の音符へ変換。起動・ビルドでは実行しない。"""
from pathlib import Path
import hashlib,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from convert_stage_bgm import convert,read
import config as C
import pyxel as p

ROOT=Path(__file__).resolve().parents[1]


def main():
    folder=ROOT/'verification/v0.12.1'
    target=ROOT/C.RESOURCE_FILE
    backup=folder/'before'/C.RESOURCE_FILE
    before=read(target)
    assert target.read_bytes()==backup.read_bytes(), 'Run once against backed-up resource'
    rows=[row.strip() for row in (ROOT/C.BOSS_BGM_MML_FILE).read_text(encoding='utf-8-sig').splitlines()
          if row.strip() and not row.strip().startswith('https://')]
    assert len(rows)==4
    tracks=[convert(rows[i]) for i in (0,1,3)]
    assert list(map(len,tracks))==[256,256,256]
    # 共通フレーズを再利用し、道中40〜51と全SE0〜18を上書きしない。
    slots=iter((*range(36,40),*range(52,64)))
    for i in range(52,64):assert not before['sounds'][i]['notes']
    p.init(C.WIDTH,C.HEIGHT,title='Editor editable stage 1 boss BGM')
    p.colors[:]=C.PALETTE;p.load(str(target))
    chunks={};sequences=[]
    for track in tracks:
        sequence=[]
        for start in range(0,len(track),32):
            chunk=tuple(track[start:start+32])
            if chunk not in chunks:
                slot=next(slots);chunks[chunk]=slot;sound=p.sounds[slot]
                sound.notes[:]=[a[0] for a in chunk];sound.tones[:]=[a[1] for a in chunk]
                sound.volumes[:]=[a[2] for a in chunk];sound.effects[:]=[a[3] for a in chunk]
                sound.speed=12
            sequence.append(chunks[chunk])
        sequences.append(sequence)
    p.musics[1].set(*sequences,[])
    temporary=folder/'boss-converted.pyxres'
    p.save(temporary.as_posix());target.write_bytes(temporary.read_bytes());temporary.unlink()
    after=read(target)
    changed=sorted(chunks.values())
    for key in ('images','tilemaps'):assert before[key]==after[key]
    for i,(old,new) in enumerate(zip(before['sounds'],after['sounds'])):
        if i not in changed:assert old==new,i
    for i,(old,new) in enumerate(zip(before['musics'],after['musics'])):
        if i!=1:assert old==new,i
    result=dict(before_sha256=hashlib.sha256(backup.read_bytes()).hexdigest(),
                after_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                sounds_added=changed,music_updated=1,sequence=sequences,loop_seconds=25.6,
                source_mml_preserved=True,existing_images_sfx_other_music_preserved=True,
                approximations=['ENV/volume quantized at 16th notes to 0-7',
                                'noise lowered two octaves for Editor note range',
                                'MML-only vibrato/glide and tied sustain approximated'])
    (folder/'resource-addition.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print('BOSS_RESOURCE_READY',json.dumps(result),flush=True);p.quit()


if __name__=='__main__':main()
