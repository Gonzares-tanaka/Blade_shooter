"""Editor保存後の値と、実ゲームのロード・描画結果を照合する。"""
from pathlib import Path
import sys,json,zipfile,tomllib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pyxel as p
import config as C
import main
from game import Actions,Game

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'verification'/('v'+C.VERSION)/'resources'
FOLDER.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(ROOT/C.RESOURCE_FILE) as z:
    expected=tomllib.loads(z.read('pyxel_resource.toml').decode())


def run(update,draw):
    app=update.__self__
    g=app.game
    g.course="legacy"
    assert list(p.colors)==C.PALETTE
    assert p.images[0].pget(8,4)==expected['images'][0]['data'][4][8]
    assert p.sounds[0].speed==expected['sounds'][0]['speed']
    assert list(p.musics[0].seqs[0])==[C.STAGE_BGM_SOUNDS[0]]
    g.reset();g.schedule=lambda:None
    g.px,g.py=128,230
    app.audio.update(g)
    app.draw()
    assert p.screen.pget(128,226)==p.images[0].pget(8,4)
    p.screenshot(str(FOLDER/'edited-player.png'),scale=2)
    result=dict(pixel=p.images[0].pget(8,4),screen_pixel=p.screen.pget(128,226),
                shot_speed=p.sounds[0].speed,music=list(p.musics[0].seqs[0]),colors=len(p.colors))
    # 編隊と突進の予告・迎撃を、配布ゲームの同じ描画で確認。
    g.time=22
    members=g.spawn_formation(128,176)
    app.draw();p.screenshot(str(FOLDER/'formation.png'),scale=2)
    for i in range(25):
        g.step(1/C.FPS,Actions(slash=i==0));app.audio.update(g)
    assert g.max_swing_kills==3
    app.draw();p.screenshot(str(FOLDER/'formation-cut.png'),scale=2)
    result['formation_swing_kills']=g.max_swing_kills
    g.reset();g.schedule=lambda:None;g.shot_clock=999
    g.time=67;g.px,g.py=88,266
    e=g.spawn_rear(128)
    app.audio.update(g)
    app.draw();p.screenshot(str(FOLDER/'rear-marker.png'),scale=2)
    while e.phase=='marker':g.update_enemies(1/C.FPS)
    for _ in range(10):g.update_enemies(1/C.FPS)
    app.draw();p.screenshot(str(FOLDER/'rear-entry.png'),scale=2)
    while e.phase=='entry':g.update_enemies(1/C.FPS)
    app.audio.update(g)
    app.draw();p.screenshot(str(FOLDER/'rear-warning.png'),scale=2)
    while e.shots_fired==0:g.update_enemies(1/C.FPS)
    app.audio.update(g)
    assert g.rear_shots_fired>0
    g.px=88
    app.draw();p.screenshot(str(FOLDER/'rear-fire.png'),scale=2)
    result['rear_stop']=[e.x,e.y]
    result['rear_sound_notes']={str(i):list(p.sounds[i].notes) for i in (10,11)}
    assert all(result['rear_sound_notes'].values())
    while e.phase!='exit':g.update_enemies(1/C.FPS)
    while e.y>210:g.update_enemies(1/C.FPS)
    g.bullets=[];g.px,g.py=128,266
    app.draw();p.screenshot(str(FOLDER/'rear-counter-opening.png'),scale=2)
    for i in range(20):
        g.step(1/C.FPS,Actions(slash=i==0));app.audio.update(g)
    assert g.blade_kills_by_kind['rear']==1
    app.draw();p.screenshot(str(FOLDER/'rear-counter-cut.png'),scale=2)
    result['rear_counter_blade_kills']=g.blade_kills_by_kind['rear']
    g.reset();g.schedule=lambda:None;g.time=102;g.px,g.py=112,166
    e=g.spawn('armor',128,112);e.phase="open"
    r=g.spawn_rear(176);r.y=C.REAR_STOP_Y;r.phase='warning'
    app.draw();p.screenshot(str(FOLDER/'armor-rear-choice.png'),scale=2)
    g.reset();g.schedule=lambda:None;g.time=60;g.px,g.py=104,230
    g.spawn_formation(104,176)
    r=g.spawn_rear(128);r.y=C.REAR_STOP_Y;r.phase='warning'
    app.draw();p.screenshot(str(FOLDER/'formation-rear-choice.png'),scale=2)
    g.reset();g.schedule=lambda:None;g.time=40;g.px,g.py=128,230
    e=g.spawn('charger',64,C.CHARGER_Y);g.update_enemies(1/C.FPS)
    app.draw();p.screenshot(str(FOLDER/'charger-warning.png'),scale=2)
    g.reset();g.schedule=lambda:None;g.time=42;g.px,g.py=128,230
    e=g.spawn('charger',128,145);e.phase='dash';e.vy=C.CHARGER_SPEED
    for i in range(17):
        g.step(1/C.FPS,Actions(slash=i==0));app.audio.update(g)
    assert g.blade_kills_by_kind['charger']==1 and g.hp==3
    app.draw();p.screenshot(str(FOLDER/'charger-cut.png'),scale=2)
    # 新しい戦艦もEditor原本から描画する。
    app.game=Game('boss');g=app.game;g.reset()
    for _ in range(2*C.FPS):g.update_boss(1/C.FPS)
    app.draw();p.screenshot(str(FOLDER/'boss-entry.png'),scale=2)
    for _ in range(3*C.FPS):g.update_boss(1/C.FPS)
    app.audio.update(g);app.draw();p.screenshot(str(FOLDER/'boss-three-targets.png'),scale=2)
    result['boss_sounds']={str(i):list(p.sounds[i].notes) for i in range(12,17)}
    result['boss_music']=[list(seq) for seq in p.musics[1].seqs]
    assert all(result['boss_sounds'].values()) and all(result['boss_music'][:2])
    g.damage_enemy(g.boss.parts[0],999)
    app.draw();p.screenshot(str(FOLDER/'boss-left-destroyed.png'),scale=2)
    (FOLDER/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('RESOURCE_RUNTIME_OK',json.dumps(result),flush=True)
    p.quit()


p.run=run
main.App()
