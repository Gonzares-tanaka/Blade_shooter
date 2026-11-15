"""Actual native Pyxel: two complete loops per attached song, four voices + SE."""
from pathlib import Path
from types import SimpleNamespace
import sys,json,time,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pyxel as p
import config as C
from audio import Audio
from assets import load_resources
folder=Path(__file__).resolve().parents[1]/'verification'/('v'+C.VERSION)/'later-bgm-native'
folder.mkdir(parents=True,exist_ok=True)
p.init(256,320,title='BLADE / stage 2 and 3 BGM verification',fps=60)
load_resources(p);a=Audio(p);songs=iter(C.LATER_BGM);results=[];music=None;records=[];paused=False
labels={2:'STAGE 2 / ASTEROID',3:'STAGE 2 / STEALTH BOSS',4:'STAGE 3 / LUNAR CAVE',5:'STAGE 3 / FINAL BOSS'}
def next_song():
 global music,driver,started,previous,wraps,durations,samples,paused
 music=next(songs,None)
 if music is None:
  # Full resource-bank return path, including the existing ending and stage-one BGM.
  driver.state='credits';a.update(driver);assert a.music_number==6 and p.play_pos(0) is not None
  driver.state='playing';driver.stage_definition=SimpleNamespace(bgm=0,boss_bgm=1);a.update(driver)
  assert a.bank==1 and a.music_number==0
  result=dict(result='PASS',engine='actual Pyxel 2.9.9',version=C.VERSION,audio_only_fixture=True,
    real_handheld=False,channels=len(p.channels),bgm_channels=C.AUDIO_BGM_CHANNELS,sfx_channels=C.AUDIO_SE_CHANNELS,
    ending_and_stage1_return=True,tracks=results)
  (folder/'result.json').write_text(json.dumps(result,indent=2),encoding='utf8')
  print('LATER_BGM_NATIVE_PASS',json.dumps(result),flush=True);p.quit();return
 spec=C.LATER_BGM[music]
 driver=SimpleNamespace(state='playing',events=[],boss=None,stage_definition=SimpleNamespace(bgm=music,boss_bgm=music))
 a.update(driver);assert len(p.channels)==6
 durations=[sum(p.sounds[i].total_sec() for i in seq) for seq in p.musics[music].seqs[:len(spec['tracks'])]]
 expected=256*15/spec['tempo']
 assert all(abs(d-expected)<.001 for d in durations),(music,durations,expected)
 assert p.musics[music].seqs[len(spec['tracks']):]==[] or all(not s for s in p.musics[music].seqs[len(spec['tracks']):])
 started=time.perf_counter();previous=None;wraps=[0]*len(durations);samples=[];paused=False
 print('START',music,durations,flush=True)
def update():
 global previous,paused
 elapsed=time.perf_counter()-started
 driver.events=['shot','cut'] if p.frame_count%18==0 else []
 a.update(driver)
 pos=[p.play_pos(ch) for ch in range(len(durations))]
 if elapsed>.2:
  assert all(x is not None for x in pos),(music,pos)
  if previous:
   for i,(old,new) in enumerate(zip(previous,pos)):
    if old[1]>durations[i]*.6 and new[1]<old[1]-durations[i]*.5:wraps[i]+=1
  previous=pos
 if p.frame_count%120==0:samples.append(dict(seconds=round(elapsed,3),positions=pos))
 if min(wraps)>=2:
  # Stop/resume uses every BGM channel, including the fourth voice.
  driver.state='paused';a.update(driver);assert all(p.play_pos(ch) is None for ch in C.AUDIO_BGM_CHANNELS)
  driver.state='playing';a.update(driver)
  assert all(p.play_pos(ch) is not None for ch in range(len(durations)))
  p.screenshot(str(folder/('music-'+str(music)+'.png')),scale=2)
  results.append(dict(music=music,file=C.LATER_BGM[music]['file'],tempo=C.LATER_BGM[music]['tempo'],
   seconds=durations,wraps=wraps,sfx_concurrent=True,pause_resume=True,samples=samples))
  print('TWO_LOOPS_PASS',music,wraps,flush=True);next_song()
 assert elapsed<2*max(durations)+8,(music,elapsed,wraps)
def draw():
 p.cls(0);p.text(12,18,'BLADE / AUDIO VERIFICATION',6);p.text(12,44,labels.get(music,''),3)
 if music is None:return
 p.text(12,68,'ORIGINAL MML / LOOP',10)
 for i,d in enumerate(durations):
  pos=p.play_pos(i);sec=pos[1] if pos else 0
  p.text(12,100+i*32,f'CH{i}  {sec:05.2f} / {d:05.2f}  LOOP {wraps[i]}',3)
  p.rect(12,111+i*32,220,3,1);p.rect(12,111+i*32,220*sec/d,3,6)
 p.text(12,266,'SFX CH4 / CH5 / FOUR VOICES SAFE',10)
next_song();p.run(update,draw)
