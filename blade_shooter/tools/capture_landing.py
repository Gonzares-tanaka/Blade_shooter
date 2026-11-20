"""Capture the current, unmodified game renderer for the landing page. No AI images.

Uses real input actions and deterministic test pilots, never injected enemies/HP.
Run manually with Pyxel; not part of the game or the normal build.
"""
from pathlib import Path
import hashlib
import json
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'tests')]
import pyxel as p
import config as C
from assets import load_resources
from game import Game, Actions, point_at, weapon_pose
from view import View
from pilot import pilot_action
from pilot_stage2 import Pilot
from pilot_stage3 import CavePilot

OUT = ROOT/'web/assets/guide'
RECORD = ROOT/'verification'/('v'+C.VERSION)/'landing-capture'
DT = 1/C.FPS


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    RECORD.mkdir(parents=True, exist_ok=True)
    p.init(256, 320, title='Current build / introduction screenshots', display_scale=1)
    load_resources(p)
    view = View(p)
    captures = {}

    def capture(name, g):
        view.draw(g)
        p.screenshot(str(OUT/(name+'.png')), scale=3)
        pose = weapon_pose(g.attack_weapon, max(0, g.swing))
        if name.startswith('weapon-'):
            detail=p.Image(256,176)
            detail.blt(0,0,p.screen,0,144,256,176)
            detail.save(str(OUT/('detail-'+name[7:]+'.png')),3)
        captures[name] = dict(stage=g.run.current_stage, time=round(g.time, 3),
            weapon=g.weapon, player=[round(g.px, 2), round(g.py, 2)],
            tip=list(point_at(*g.blade_pivot, pose[2], pose[0])),
            melee_active=bool(g.slash_polys), enemy_kinds=sorted({e.kind for e in g.enemies}),
            enemies=len(g.enemies), bullets=len(g.bullets),
            sha256=hashlib.sha256((OUT/(name+'.png')).read_bytes()).hexdigest())

    for weapon in ('blade', 'axe', 'lance'):
        g=Game(seed=7, weapon=weapon)
        g.reset()
        for _ in range(200):g.step(DT, Actions())
        if weapon=='blade':capture('move', g)
        g.step(DT, Actions(slash=True))
        target=C.WEAPONS[weapon]['windup']+C.WEAPONS[weapon]['active']*.55
        while g.swing < target:g.step(DT, Actions())
        assert g.slash_polys and g.state=='playing'
        capture('weapon-'+weapon, g)

    for stage in (1, 2, 3):
        g=Game(seed=7)
        g.enter_stage(stage, carry_run=False)
        pilot=Pilot() if stage==2 else CavePilot() if stage==3 else None
        best=-1
        for frame in range(100*C.FPS):
            action=pilot.action(g) if pilot else pilot_action(g, True, True)
            g.step(DT, action)
            if g.state!='playing':break
            if frame%15 or g.time<12:continue
            kinds={e.kind for e in g.enemies if e.on_screen}
            if stage==1 and len(kinds)<2:continue
            if stage==2 and not {'asteroid','missile'}<=kinds:continue
            if stage==3 and (len(kinds)<2 or not g.cave.walls):continue
            score=len(kinds)*15+min(16,len(g.enemies))+min(15,len(g.bullets))
            if score>best:
                capture('stage'+str(stage),g)
                best=score
        assert 'stage'+str(stage) in captures,stage

    app=ROOT/'dist/web/blade-shooter.pyxapp'
    with zipfile.ZipFile(app) as archive:
        packaged_matches=all(archive.read('blade-shooter/'+name)==(ROOT/name).read_text(encoding='utf8').replace('\r\n','\n').encode('utf8')
                            for name in ('game.py','config.py','view.py','main.py'))
    report=dict(game_version=C.VERSION, source='Actual native Pyxel renderer, input-only simulation',
                ai_generated=False, gameplay_modified=False, captures=captures,
                game_sources={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
                    for name in ('game.py','config.py','view.py','main.py','audio.py')},
                pyxapp_sha256=hashlib.sha256(app.read_bytes()).hexdigest() if packaged_matches else None)
    (RECORD/'capture.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps(report),flush=True)
    p.quit()


if __name__=='__main__':main()
