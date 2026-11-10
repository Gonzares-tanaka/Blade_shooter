"""実PyxelでMMLの長さ・2周ループ・SE併用・停止再開・ボス切替を確認。"""
from pathlib import Path
from types import SimpleNamespace
import json,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pyxel as p
import config as C
import main

folder=Path(__file__).resolve().parents[1]/'verification'/('v'+C.VERSION)/'bgm-native'
folder.mkdir(parents=True,exist_ok=True)
original_run=p.run
frames=0
wraps=[0,0,0];previous=[None]*3
samples=[]

def run(update,draw):
    global app,driver,started,durations
    app=update.__self__;app.game.reset()
    driver=SimpleNamespace(state='playing',events=[],boss=None)
    durations=[sum(p.sounds[i].total_sec() for i in seq) for seq in p.musics[0].seqs[:3]]
    assert abs(durations[0]-12.8)<.001
    assert max(abs(durations[i]-durations[0]) for i in (1,2))<1e-8
    assert len(p.channels)==5
    started=time.perf_counter()
    original_run(tick,app.draw)

def tick():
    global frames,previous
    frames+=1
    if frames==1621:driver.state='paused'
    if frames==1625:driver.state='playing'
    if frames==1633:driver.boss=object()
    driver.events=['shot','cut','erase'] if frames%18==0 else []
    app.audio.update(driver)
    app.game.time=frames/C.FPS
    positions=[p.play_pos(ch) for ch in C.AUDIO_BGM_CHANNELS]
    if frames<=1620:
        if frames>12:assert all(pos is not None for pos in positions),positions
        for i,(old,new) in enumerate(zip(previous,positions)):
            if old and new and new[0]<old[0]:wraps[i]+=1
        previous=positions
        if frames%120==0:samples.append(dict(frame=frames,positions=positions))
    if frames==1623:
        assert positions==[None,None,None],positions
    if frames==1630:
        assert all(pos is not None and pos[1]<1 for pos in positions),positions
    if frames==1640:
        assert positions[0] is not None and positions[1] is not None and positions[2] is None,positions
        assert wraps==[2,2,2],wraps
        result=dict(result='PASS',version=C.VERSION,engine='actual Pyxel 2.9.9',audio_only_fixture=True,
                    real_handheld=False,wall_seconds=time.perf_counter()-started,
                    source_track_seconds=durations,loop_wraps=wraps,sfx_concurrent=True,
                    pause_stops_all_bgm=True,resume_restarts_stage=True,boss_stops_stage_drums=True,
                    channels=len(p.channels),samples=samples)
        (folder/'result.json').write_text(json.dumps(result,indent=2),encoding='utf8')
        print('STAGE_BGM_NATIVE_PASS',json.dumps(result),flush=True);p.quit()

p.run=run
main.App()
