"""Real Pyxel View/audio fixtures and native-size HUD legibility checks."""
from pathlib import Path
import sys,json,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pyxel as p
import main,config as C
from game import Actions
folder=Path(__file__).resolve().parents[1]/'verification'/('v'+C.VERSION)/'modes-native'
folder.mkdir(parents=True,exist_ok=True)

def run(update,draw):
    app=update.__self__;g=app.game;captures=[]
    def capture(name):
        app.audio.update(g);app.view.profile='gkd';app.draw()
        p.screenshot(str(folder/(name+'.png')),scale=2)
        p.screenshot(str(folder/(name+'-native.png')),scale=1)
        captures.append(name)
    capture('title')
    # The complete logo exactly equals the imported palette-index image; no crop.
    assert all(p.screen.pget(x,y+12)==p.images[2].pget(x,y) for y in range(100) for x in range(256))
    assert app.audio.music_number==7 and len(p.channels)==6
    assert any(p.screen.pget(x,y)==16 for y in range(174,185) for x in range(90,165))
    durations={}
    for state,number in (('title',7),('credits',6)):
        g.state=state;app.audio.update(g)
        times=[sum(p.sounds[i].total_sec() for i in seq) for seq in p.musics[number].seqs[:4]]
        assert max(times)-min(times)<.003
        expected=128*15/C.UI_BGM[number]['tempo']
        assert all(abs(t-expected)<.003 for t in times)
        durations[number]=times
    g.return_title();g.step(.01,Actions(confirm=True));capture('mode-select')
    g.step(.01,Actions(menu_pick=2));capture('stage-select')
    g.step(.01,Actions(menu_pick=2));g.schedule=lambda:None
    g.add_score(10000,'fixture');capture('extend-hud')
    g.hp=1;g.invincible=0;g.hurt();capture('respawn-hud')
    assert g.hp==3 and g.run.lives==3
    g.score=12500;g.run.current_cut=8;g.weapon='lance';g.cooldown=0
    g.life_notice_time=0
    g.invincible=0;capture('hud-gkd')
    labels=[('HP',6,15,2),('LIFE',112,15,2),('03',132,15,6),('LANCE',54,15,6),('ST2',156,15,39),('00:00',201,15,3)]
    expected={}
    for text,x,y,color in labels:
        p.cls(0);p.text(x,y,text,color)
        expected[text]=[(xx,yy) for xx in range(x,x+len(text)*4) for yy in range(y,y+6) if p.screen.pget(xx,yy)==color]
    app.draw()
    missing={text:[pos for pos in points if p.screen.pget(*pos)==0] for text,points in expected.items()}
    assert not any(missing.values()),missing
    g.run.lives=1;g.hp=1;g.hurt();capture('gameover')
    g.step(.01,Actions(title=True));capture('title-continue')
    g.step(.01,Actions(menu_pick=2));assert g.run.current_stage==2 and g.time==0
    capture('continued-stage-two')
    result=dict(result='PASS',engine='actual Pyxel 2.9.9',real_devices=False,graphics_audio_fixtures=True,
                logo_pixels_uncropped=True,colors=len(p.colors),music_seconds=durations,hud_missing_pixels=missing,
                hurt_sound=list(p.sounds[5].notes),captures=captures)
    (folder/'result.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print('MODES_NATIVE_PASS',json.dumps(result),flush=True);p.quit()
p.run=run;main.App()
