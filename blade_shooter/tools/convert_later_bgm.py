"""添付4曲のEditor用バンクを生成。実行は一度だけ、起動・ビルドでは呼ばない。"""
from pathlib import Path
import sys,json,hashlib
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parent)]
import pyxel as p
import config as C
from convert_stage_bgm import convert,read
ROOT=Path(__file__).resolve().parents[1]
def main():
 folder=ROOT/'verification/v0.16.1';source=ROOT/C.RESOURCE_FILE;before=read(source)
 assert source.read_bytes()==(folder/'before'/C.RESOURCE_FILE).read_bytes()
 p.init(C.WIDTH,C.HEIGHT,title='Stage 2 and 3 editable music banks');p.colors[:]=C.PALETTE
 records=[]
 for bank,path in C.AUDIO_BANKS.items():
  target=ROOT/path;assert not target.exists(),'Never overwrite Editor work: '+str(target)
  p.load(str(source));free=tuple((*range(22,34),*range(36,62)))
  for slot in free:p.sounds[slot].set('','','','',12)
  for number in (0,1,2,3,4,5):p.musics[number].set([],[],[],[])
  chunks={};available=iter(free)
  for number,spec in C.LATER_BGM.items():
   if spec['bank']!=bank:continue
   rows=[row.strip() for row in (ROOT/spec['file']).read_text(encoding='utf-8-sig').splitlines() if row.strip().startswith('Q')]
   tracks=[convert(rows[i]) for i in spec['tracks']];assert all(len(t)==256 for t in tracks)
   speed=round(1800/spec['tempo']);sequences=[]
   for track in tracks:
    seq=[]
    for start in range(0,len(track),32):
     chunk=tuple(track[start:start+32]);key=(speed,chunk)
     if key not in chunks:
      slot=next(available);chunks[key]=slot;sound=p.sounds[slot]
      for attr,col in (('notes',0),('tones',1),('volumes',2),('effects',3)):getattr(sound,attr)[:]=[n[col] for n in chunk]
      sound.speed=speed
     seq.append(chunks[key])
    sequences.append(seq)
   p.musics[number].set(*sequences,*([] for _ in range(4-len(sequences))))
   records.append(dict(music=number,source=spec['file'],bank=path,source_tempo=spec['tempo'],voices=len(tracks),
      source_loop_seconds=256*15/spec['tempo'],editor_loop_seconds=256*speed/120,editor_tempo=1800/speed,sequences=sequences,
      source_sha256=hashlib.sha256((ROOT/spec['file']).read_bytes()).hexdigest()))
  p.save(target.as_posix());target.with_suffix('.pyxpal').write_bytes((ROOT/C.PALETTE_FILE).read_bytes())
  after=read(target)
  for key in ('images','tilemaps'):assert before[key]==after[key]
  for i in (*range(22),34,35,62,63):assert before['sounds'][i]==after['sounds'][i],i
  assert before['musics'][6]==after['musics'][6]
  assert len(after['sounds'])==64
  print('BANK',bank,'unique chunks',len(chunks),flush=True)
 assert source.read_bytes()==(folder/'before'/C.RESOURCE_FILE).read_bytes()
 digest=hashlib.sha256(source.read_bytes()).hexdigest()
 result=dict(before_sha256=digest,after_sha256=digest,existing_images_sfx_other_music_preserved=True,
    base_resource_unchanged=True,original_mml_verbatim=True,default_playback='native MML, exact tempo / ENV / VIB',
    editor_notes_approximations=['sixteenth-note envelope volume quantized 0–7','noise pitches lowered 2 octaves',
     'vibrato and tied sustain approximated','T171 quantized to speed11 only in optional Editor playback'],tracks=records,
    bank_sha256={path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in C.AUDIO_BANKS.values()})
 (folder/'resource-addition.json').write_text(json.dumps(result,indent=2),encoding='utf8')
 print('LATER_BGM_READY',flush=True);p.quit()
if __name__=='__main__':main()
