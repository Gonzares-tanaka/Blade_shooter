"""添付MMLをEditorの32音単位へ変換する一度だけのツール。原文は保持。"""
from pathlib import Path
import re,sys,json,hashlib,zipfile,tomllib,math
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import config as C
import pyxel as p
ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'verification/v0.12.0'
target=ROOT/C.RESOURCE_FILE
backup=folder/'before'/C.RESOURCE_FILE

def read(file):
    with zipfile.ZipFile(file) as z:return tomllib.loads(z.read('pyxel_resource.toml').decode())

def convert(row):
    tokens=re.findall(r'@[A-Z]*\d+(?:\{[^}]*\})?|[QTLOV]\d+|[A-GR][+#-]?\d*|&\d+',row)
    octave,length,tone,volume,tempo=4,16,0,100,150
    env=None;result=[];i=0
    while i<len(tokens):
        token=tokens[i];i+=1
        if token.startswith('@ENV'):
            if '{' in token:env=[int(n) for n in re.findall(r'\d+',token.split('{')[1])]
            elif token=='@ENV0':env=None
        elif token.startswith(('@VIB','@GLI')):pass
        elif token.startswith('@'):tone=int(token[1:])
        elif token[0] in 'QTLOV':
            value=int(token[1:])
            if token[0]=='T':tempo=value
            elif token[0]=='O':octave=value
            elif token[0]=='L':length=value
            elif token[0]=='V':volume=value
        else:
            note=re.fullmatch(r'([A-GR])([+#-]?)(\d*)',token)
            if note is None:raise ValueError(token)
            name,accidental,duration=note.groups()
            units=16/int(duration or length)
            while i<len(tokens) and tokens[i].startswith('&'):
                units+=16/int(tokens[i][1:]);i+=1
            assert abs(units-round(units))<1e-8
            pitch=-1 if name=='R' else (octave-2)*12+{'C':0,'D':2,'E':4,'F':5,'G':7,'A':9,'B':11}[name]+(1 if accidental in ('+','#') else -1 if accidental=='-' else 0)
            if tone==3 and pitch>=60:pitch-=24  # Editorの0〜59内でノイズ2音の差を維持。
            assert -1<=pitch<=59,pitch
            for step in range(round(units)):
                gain=127
                if env:
                    elapsed=(step+.25)*(60/tempo/4)/(60/tempo/48)
                    gain=env[0];start=0
                    for duration_ticks,end_volume in zip(env[1::2],env[2::2]):
                        if elapsed<=start+duration_ticks:
                            gain=gain+(end_volume-gain)*max(0,(elapsed-start)/duration_ticks);break
                        start+=duration_ticks;gain=end_volume
                vol=0 if pitch<0 else max(0,min(7,round(volume/127*gain/127*7)))
                result.append((pitch,tone,vol,0))
    return result

before=read(target)
assert target.read_bytes()==backup.read_bytes()
assert all(not before['sounds'][i]['notes'] for i in range(40,52))
rows=[r.strip() for r in (ROOT/C.STAGE_BGM_MML_FILE).read_text(encoding='utf-8-sig').splitlines() if r.strip() and not r.startswith('https://')]
tracks=[convert(rows[i]) for i in C.STAGE_BGM_AUDIBLE_TRACKS]
assert [len(t) for t in tracks]==[128,128,128]
p.init(C.WIDTH,C.HEIGHT,title='Editor editable stage 1 BGM')
p.colors[:]=C.PALETTE;p.load(str(target))
sequences=[];slot=40
for track in tracks:
    sequence=[]
    for start in range(0,len(track),32):
        chunk=track[start:start+32];sound=p.sounds[slot]
        sound.notes[:]=[a[0] for a in chunk];sound.tones[:]=[a[1] for a in chunk]
        sound.volumes[:]=[a[2] for a in chunk];sound.effects[:]=[a[3] for a in chunk];sound.speed=12
        sequence.append(slot);slot+=1
    sequences.append(sequence)
p.musics[0].set(*sequences,[]);p.save(str(target));after=read(target)
for key in ('images','tilemaps'):assert before[key]==after[key]
for i,(old,new) in enumerate(zip(before['sounds'],after['sounds'])):
    if i not in range(40,52):assert old==new,i
for i,(old,new) in enumerate(zip(before['musics'],after['musics'])):
    if i!=0:assert old==new,i
result=dict(before_sha256=hashlib.sha256(backup.read_bytes()).hexdigest(),
            after_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
            sounds_added=list(range(40,52)),music_updated=0,sequence=sequences,
            loop_seconds=12.8,source_mml_preserved=True,
            existing_images_sfx_other_music_preserved=True,
            approximations=['ENV/volume quantized at 16th notes to 0-7','noise lowered two octaves for Editor note range','MML-only effects approximated'])
(folder/'resource-addition.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print('RESOURCE_BGM_READY',json.dumps(result),flush=True);p.quit()
