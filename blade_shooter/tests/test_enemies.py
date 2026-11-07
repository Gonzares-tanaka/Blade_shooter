from pathlib import Path
import sys
import unittest
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parent)]
import config as C
from game import Game,Actions
from test_game import sandbox,DT


class EnemyTests(unittest.TestCase):
    def test_three_formation_members_in_one_swing(self):
        g=sandbox();g.px,g.py=128,180
        group=g.spawn_formation(128,126)
        for i in range(35):g.step(DT,Actions(slash=i==0))
        self.assertTrue(all(e.hp<=0 for e in group))
        self.assertEqual(g.blade_kills_by_kind['small'],3)
        self.assertEqual(g.max_swing_kills,3)
        self.assertEqual(g.hp,3)

    def test_charge_locks_at_warning_start_and_never_tracks(self):
        g=sandbox();e=g.spawn('charger',64,C.CHARGER_Y)
        g.update_enemies(DT)
        self.assertEqual(e.phase,'warning')
        aim=(e.aim_x,e.aim_y,e.vx,e.vy)
        g.px,g.py=230,170
        for _ in range(int(C.CHARGER_WARNING_SECONDS*C.FPS)+2):g.update_enemies(DT)
        self.assertEqual(e.phase,'dash')
        self.assertEqual((e.aim_x,e.aim_y,e.vx,e.vy),aim)
        x,y=e.x,e.y
        g.update_enemies(DT)
        self.assertAlmostEqual(e.x-x,e.vx*DT)
        self.assertAlmostEqual(e.y-y,e.vy*DT)

    def test_charge_can_be_intercepted_with_one_cut(self):
        g=sandbox();g.px,g.py=128,230
        e=g.spawn('charger',128,145)
        e.phase='dash';e.vy=C.CHARGER_SPEED
        for i in range(22):g.step(DT,Actions(slash=i==0))
        self.assertLessEqual(e.hp,0)
        self.assertEqual(g.blade_kills_by_kind['charger'],1)
        self.assertEqual(g.hp,3)

    def test_locked_charge_can_be_evaded_without_blade(self):
        g=sandbox();g.px,g.py=128,230
        e=g.spawn('charger',128,C.CHARGER_Y)
        g.step(DT)
        for _ in range(160):g.step(DT,Actions(x=1 if g.px<215 else 0))
        self.assertEqual(g.hp,3)
        self.assertEqual(g.slashes,0)

    def test_fast_charge_cannot_tunnel_through_player(self):
        g=sandbox();g.px,g.py=128,230
        e=g.spawn('charger',128,170);e.phase='dash';e.vy=6000
        g.step(DT)
        self.assertEqual(g.hp,2)

    def test_training_sections_have_one_kind_then_mix(self):
        for start,end,expected in ((0,16,{'armor'}),(16,36,{'small'}),(36,56,{'charger'}),(56,80,{'armor','small','charger'})):
            g=sandbox();g.schedule=Game.schedule.__get__(g)
            g.course='classic'
            seen=set()
            for i in range(int(end*C.FPS)):
                g.time=i/C.FPS
                g.schedule()
                if start<=g.time<end:
                    for e in g.enemies:seen.add(e.kind)
                g.enemies.clear()
            self.assertEqual(seen,expected)


if __name__=='__main__':unittest.main()
