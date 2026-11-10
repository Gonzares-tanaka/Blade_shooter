"""実Pyxelのボス3声・2周ループ・道中切替・SE併用を確認。"""
from pathlib import Path
from types import SimpleNamespace
import json,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pyxel as p
import config as C
import main

folder=Path(__file__).resolve().parents[1]/'verification'/('v'+C.VERSION)/'boss-bgm-native'
folder.mkdir(parents=True,exist_ok=True)
original_run=p.run
frames=0;wraps=[0,0,0];previous=[None]*3


def run(update,draw):
    global app,driver,started,durations
    app=update.__self__;app.game.reset()
    driver=SimpleNamespace(state='playing',events=[],boss=None)
    durations=[sum(p.sounds[i].total_sec() for i in seq) for seq in p.musics[1].seqs[:3]]
    assert all(abs(d-25.6)<.001 for d in durations),durations
    started=time.perf_counter();original_run(tick,app.draw)


def tick():
    global frames,previous
    frames+=1
    if frames==12:driver.boss=object()
    if frames==3160:driver.state='paused'
    if frames==3165:driver.state='playing'
    driver.events=['shot','cut','erase'] if frames%18==0 else []
    app.audio.update(driver)
    positions=[p.play_pos(ch) for ch in C.AUDIO_BGM_CHANNELS]
    if 24<=frames<3160:
        assert all(pos is not None for pos in positions),positions
        for i,(old,new) in enumerate(zip(previous,positions)):
            if old and new and new[0]<old[0]:wraps[i]+=1
        previous=positions
    if frames==3163:assert positions==[None]*3,positions
    if frames==3175:
        assert all(pos is not None and pos[1]<1 for pos in positions),positions
        assert wraps==[2,2,2],wraps
        result=dict(result='PASS',version=C.VERSION,engine='actual Pyxel 2.9.9',
                    audio_only_fixture=True,real_handheld=False,
                    wall_seconds=time.perf_counter()-started,track_seconds=durations,
                    loop_wraps=wraps,stage_to_boss_switch=True,sfx_concurrent=True,pause_resume=True)
        (folder/'result.json').write_text(json.dumps(result,indent=2),encoding='utf8')
        print('BOSS_BGM_NATIVE_PASS',json.dumps(result),flush=True);p.quit()


p.run=run
main.App()
