"""実PyxelでHUD固定位置・取得・リザルト・小画面用キャプチャを検証。"""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pyxel as p
import config as C
import main
from game import Actions
folder=Path(__file__).resolve().parents[1]/'verification'/('v'+C.VERSION)/'hud'
folder.mkdir(parents=True,exist_ok=True)

def run(update,draw):
    app=update.__self__;g=app.game;g.reset();g.schedule=lambda:None
    for score,cut,weapon in ((0,0,'blade'),(12500,8,'axe'),(999999,124,'lance')):
        g.score=score;g.run.current_cut=cut;g.run.max_cut=cut;g.weapon=weapon;g.cut_pulse=.18 if cut else 0
        app.draw();p.screenshot(str(folder/f'hud-{score}-{cut}.png'),scale=2)
    g.run.current_cut=8;g.score=12500;g.best_score=15000;g.hp=1;g.invincible=0;g.hurt()
    app.draw();p.screenshot(str(folder/'gameover.png'),scale=2)
    g.state='result';g.boss_defeated=True
    app.draw();p.screenshot(str(folder/'result.png'),scale=2)
    g.step(1/C.FPS,Actions(retry=True));assert g.score==0 and g.max_cut==0
    app.draw();p.screenshot(str(folder/'retry.png'),scale=2)
    # 文字が他のHUD描画で欠けていないか、同じFontの単独描画と比較。
    expected={}
    for key,x,y,text,color in (('weapon',54,15,'BLADE',6),('cut',191,4,'CUT',6),('timer',201,15,'00:00',3)):
        p.cls(0);p.text(x,y,text,color)
        expected[key]=[(a,b) for a in range(x,x+len(text)*4) for b in range(y,y+6) if p.screen.pget(a,b)==color]
    app.draw()
    missing={key:[pos for pos in points if p.screen.pget(*pos)==0] for key,points in expected.items()}
    result=dict(result='PASS' if not any(missing.values()) else 'FAIL',missing=missing,
                expected_counts={key:len(points) for key,points in expected.items()},hud_height=C.HUD_HEIGHT)
    (folder/'result.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print('HUD_CHECK',json.dumps(result),flush=True)
    assert result['result']=='PASS',missing
    p.quit()

p.run=run
main.App()
