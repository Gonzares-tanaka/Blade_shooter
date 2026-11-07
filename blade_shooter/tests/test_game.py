import math
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import zipfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config as C
from game import Actions, Bullet, Game, sweep_polygons, polygon_hits_circle
from pilot import pilot_action

DT = 1/C.FPS


def sandbox():
    g = Game()
    g.reset()
    g.schedule = lambda: None
    g.shot_clock = 999
    return g


class CombatTests(unittest.TestCase):
    def test_blade_one_shots_armor_at_safe_distance(self):
        g = sandbox()
        g.px, g.py = 128, 180
        e = g.spawn("armor", 128, 126)
        for i in range(28):
            g.step(DT, Actions(slash=i==0))
        self.assertLessEqual(e.hp, 0)
        self.assertEqual(g.blade_kills, 1)
        self.assertEqual(g.hp, 3)
        self.assertEqual((g.px,g.py), (128,180))
        self.assertTrue(any(e.kind == "split" for e in g.effects))

    def test_damage_once_per_swing_even_when_target_survives(self):
        g = sandbox()
        g.px, g.py = 128, 180
        e = g.spawn("armor",128,145)
        e.hp = 200
        for i in range(28):
            g.step(DT, Actions(slash=i==0))
        self.assertEqual(e.hp,200-C.BLADE_DAMAGE)

    def test_swept_geometry_front_and_rear(self):
        polys = sweep_polygons(128,176,-165,-15)
        self.assertTrue(any(polygon_hits_circle(p,128,120,2) for p in polys))
        self.assertFalse(any(polygon_hits_circle(p,128,225,2) for p in polys))
        self.assertFalse(any(polygon_hits_circle(p,128,100,2) for p in polys))

    def test_only_blade_contact_clears_bullets(self):
        g = sandbox()
        g.px, g.py = 128,180
        g.bullets=[Bullet(128,125,0,0),Bullet(128,220,0,0),Bullet(230,120,0,0)]
        for i in range(24):
            g.step(DT,Actions(slash=i==0))
        self.assertEqual(g.cleared_bullets,1)
        self.assertEqual(len(g.bullets),2)

    def test_swing_does_not_grant_invulnerability(self):
        g=sandbox()
        g.bullets=[Bullet(g.px,g.py,0,0)]
        g.step(DT,Actions(slash=True))
        self.assertEqual(g.hp,2)

    def test_body_contact_during_swing(self):
        g=sandbox()
        g.spawn("armor",g.px+19,g.py)
        g.step(DT,Actions(slash=True))
        self.assertEqual(g.hp,2)

    def test_damage_grace_and_fast_retry(self):
        g=sandbox()
        g.hurt(); g.hurt()
        self.assertEqual(g.hp,2)
        g.invincible=0; g.hurt()
        g.invincible=0; g.hurt()
        self.assertEqual(g.state,"gameover")
        g.step(DT,Actions(slash=True))
        self.assertEqual((g.state,g.hp,g.time),("playing",3,0))

    def test_cooldown_and_no_dash(self):
        g=sandbox()
        self.assertTrue(g.start_slash())
        self.assertFalse(g.start_slash())
        for _ in range(math.ceil(C.BLADE_COOLDOWN*C.FPS)+1): g.step(DT)
        self.assertTrue(g.start_slash())
        self.assertEqual((g.px,g.py),(128,266))

    def test_hitstop_keeps_visual_and_world_but_not_stage_time(self):
        g=sandbox()
        g.start_slash()
        g.update_blade(0.1)
        polys=list(g.slash_polys)
        g.hitstop=.05
        g.step(DT,Actions(y=-1))
        self.assertEqual(g.slash_polys,polys)
        self.assertEqual(g.py,266)
        self.assertAlmostEqual(g.time,DT)

    def test_armor_opening_fires_no_bullets(self):
        g=sandbox()
        e=g.spawn("armor",128,C.ARMOR_Y)
        e.phase="open";e.phase_time=.1
        for _ in range(90):
            g.update_enemies(DT)
            self.assertTrue(e.resting)
        self.assertEqual(len(g.bullets),0)

    def test_shots_kill_armor_in_several_seconds(self):
        g=sandbox()
        g.shot_clock=0
        g.px,g.py=128,275
        e=g.spawn("armor",128,C.ARMOR_Y)
        # 敵弾は残し、HPを無限化しない。自機への被弾は許すが撃破時刻を確認。
        for i in range(360):
            g.step(DT)
            if e.hp<=0: break
        self.assertLessEqual(e.hp,0)
        self.assertGreater(i*DT,3)
        self.assertLess(i*DT,5.7)

    def test_pause_and_focus_loss_freeze_clock(self):
        g=sandbox()
        g.step(DT,Actions(focus_lost=True))
        g.step(2,Actions(x=1))
        self.assertEqual((g.state,g.time,g.px),("paused",0,128))
        g.step(DT,Actions(confirm=True))
        self.assertEqual(g.state,"playing")

    def test_drag_consumed_and_clamped(self):
        g=sandbox()
        g.step(DT,Actions(drag_x=10000,drag_y=-10000))
        self.assertEqual((g.px,g.py),(248,32))
        g.step(DT)
        self.assertEqual((g.px,g.py),(248,32))

    def test_legacy_route_both_approaches(self):
        for use_blade in (False,True):
            with self.subTest(blade=use_blade):
                g=Game("legacy"); g.reset()
                for _ in range(math.ceil(C.COURSES["legacy"]["duration"]*C.FPS)+1):
                    g.step(DT,pilot_action(g,use_blade))
                    if g.state!="playing": break
                print("PILOT",use_blade,g.state,round(g.time,3),g.hp,g.slashes,g.blade_kills,g.shot_kills)
                self.assertEqual(g.state,"clear")
                self.assertEqual(g.time,C.COURSES["legacy"]["duration"])
                self.assertGreater(g.hp,0)
                if use_blade: self.assertGreater(g.blade_kills,0)
                else: self.assertEqual(g.slashes,0)


class PackageTests(unittest.TestCase):
    def test_zip_sources_and_launcher(self):
        root=Path(__file__).resolve().parents[1]
        with zipfile.ZipFile(root/'dist/blade-shooter-gkd.zip') as z:
            for name in ('main.py','config.py','game.py','view.py'):
                self.assertEqual(z.read('blade-shooter/'+name),(root/name).read_bytes())
            script=z.read('blade-shooter.sh')
            self.assertIn(b'/storage/pyxel_Python/bin/python3',script)
            self.assertIn(b'exec "$game_python" -u main.py --gkd',script)
            self.assertNotIn(b'\r',script)
            self.assertTrue((z.getinfo('blade-shooter.sh').external_attr>>16)&0o111)


if __name__=='__main__': unittest.main()
