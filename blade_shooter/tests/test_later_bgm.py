"""Four attached sources, native MML playback and editable resource fallback."""
from pathlib import Path
import sys,unittest,zipfile,tomllib,hashlib,json
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import config as C
from audio import Audio
from test_audio import Fake
from tools.convert_stage_bgm import convert
ROOT=Path(__file__).resolve().parents[1]
def read(file):
 with zipfile.ZipFile(file) as z:return tomllib.loads(z.read('pyxel_resource.toml').decode())
class LaterBgmTests(unittest.TestCase):
 def test_native_playback_uses_verbatim_audible_tracks_and_loops(self):
  p=Fake();a=Audio(p)
  for music,spec in C.LATER_BGM.items():
   stage=SimpleNamespace(bgm=music,boss_bgm=music)
   a.update(SimpleNamespace(state='playing',events=['shot','cut'],stage_definition=stage))
   rows=[row.strip() for row in (ROOT/spec['file']).read_text(encoding='utf-8-sig').splitlines() if row.startswith('Q')]
   self.assertEqual([p.mml[i] for i in range(22,22+len(spec['tracks']))],[rows[i] for i in spec['tracks']])
   self.assertIn(('music',(music,),{'loop':True}),p.calls)
  self.assertEqual(len(p.channels),6)
  self.assertEqual(p.music_sequences[5],([22],[23],[24],[25]))
  self.assertEqual(C.AUDIO_SE_CHANNELS,(4,5))
  self.assertFalse(set(C.AUDIO_SE_CHANNELS)&set(C.AUDIO_BGM_CHANNELS))
 def test_pause_and_bank_switches_do_not_reload_every_frame(self):
  p=Fake();a=Audio(p);stage=SimpleNamespace(bgm=2,boss_bgm=3)
  g=SimpleNamespace(state='playing',events=[],stage_definition=stage,boss=None)
  for _ in range(10):a.update(g)
  self.assertEqual(sum(c[0]=='load' for c in p.calls),1)
  g.boss=object();a.update(g);self.assertEqual(sum(c[0]=='load' for c in p.calls),1)
  g.state='paused';a.update(g)
  self.assertEqual([c[1] for c in p.calls[-4:]],[(0,),(1,),(2,),(3,)])
  g.state='playing';a.update(g);self.assertEqual(sum(c[0]=='load' for c in p.calls),1)
  g.stage_definition=SimpleNamespace(bgm=4,boss_bgm=5);a.update(g)
  self.assertEqual(a.bank,3)
  g.boss=None;g.stage_definition=SimpleNamespace(bgm=0,boss_bgm=1);a.update(g)
  self.assertEqual(a.bank,1);self.assertEqual(sum(c[0]=='load' for c in p.calls),3)
  for c in p.calls:
   if c[0]=='load':self.assertEqual(c[2],dict(exclude_images=True,exclude_tilemaps=True))
 def test_resource_mode_keeps_editor_notes(self):
  p=Fake()
  with patch.object(C,'LATER_BGM_MODE','resource'):
   a=Audio(p);a.update(SimpleNamespace(state='playing',events=[],stage_definition=SimpleNamespace(bgm=5,boss_bgm=5)))
  self.assertFalse(p.mml)
  self.assertIn(('music',(5,),{'loop':True}),p.calls)
 def test_resource_banks_preserve_art_sfx_palette_ending_and_standard_editor_limits(self):
  base=read(ROOT/C.RESOURCE_FILE)
  for bank,path in C.AUDIO_BANKS.items():
   data=read(ROOT/path)
   self.assertEqual(len(data['sounds']),64)
   for key in ('images','tilemaps'):self.assertEqual(data[key],base[key])
   for i in (*range(22),34,35,62,63):self.assertEqual(data['sounds'][i],base['sounds'][i],i)
   self.assertEqual(data['musics'][6],base['musics'][6])
   self.assertEqual((ROOT/path).with_suffix('.pyxpal').read_bytes(),(ROOT/C.PALETTE_FILE).read_bytes())
   for seqs in (m['seqs'] for m in data['musics']):
    for seq in seqs:
     for slot in seq:
      self.assertLess(slot,64);self.assertLessEqual(len(data['sounds'][slot]['notes']),48)
 def test_editor_tracks_match_source_note_volume_conversion_and_sync(self):
  for music,spec in C.LATER_BGM.items():
   data=read(ROOT/C.AUDIO_BANKS[spec['bank']]);rows=[s for s in (ROOT/spec['file']).read_text(encoding='utf-8-sig').splitlines() if s.startswith('Q')]
   for seq,index in zip(data['musics'][music]['seqs'],spec['tracks']):
    actual=[]
    for slot in seq:
     sound=data['sounds'][slot];attrs=[sound[k] for k in ('notes','tones','volumes','effects')]
     actual.extend(tuple(a[n%len(a)] for a in attrs) for n in range(len(attrs[0])))
     self.assertEqual(sound['speed'],round(1800/spec['tempo']))
    self.assertEqual(actual,convert(rows[index]));self.assertEqual(len(actual),256)
 def test_originals_and_original_resource_are_preserved(self):
  folder=ROOT/'verification/v0.16.1';report=json.loads((folder/'resource-addition.json').read_text())
  for track in report['tracks']:
   self.assertEqual(hashlib.sha256((ROOT/track['source']).read_bytes()).hexdigest(),track['source_sha256'])
  self.assertEqual((ROOT/C.RESOURCE_FILE).read_bytes(),(folder/'before'/C.RESOURCE_FILE).read_bytes())
if __name__=='__main__':unittest.main()
