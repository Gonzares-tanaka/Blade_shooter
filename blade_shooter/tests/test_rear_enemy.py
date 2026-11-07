"""下端予告・攻撃と離脱の分離・回避から反撃する流れを確認。"""
import unittest
import math
from game import Game,Actions,Bullet
import config as C
from test_game import sandbox,DT


class RearEnemyTests(unittest.TestCase):
    def test_marker_precedes_entry_without_body_or_offscreen_fire(self):
        g=sandbox();e=g.spawn_rear(128);g.px,g.py=128,312
        for _ in range(int(C.REAR_MARKER_SECONDS*C.FPS)-1):
            g.step(DT)
            self.assertEqual(e.phase,'marker')
            self.assertFalse(e.contact_active)
            self.assertEqual(g.bullets,[])
        while e.phase in ('marker','entry'):
            g.step(DT)
            self.assertEqual(g.hp,3)
            self.assertEqual(g.bullets,[])
        self.assertEqual(e.phase,'warning')
        self.assertEqual((e.x,e.y),(128,C.REAR_STOP_Y))
        self.assertLess(e.y+e.radius,g.py-8)

    def test_path_is_fixed_and_never_tracks_player(self):
        a,b=sandbox(),sandbox();ea,eb=a.spawn_rear(80),b.spawn_rear(80)
        for i in range(550):
            a.px,a.py=128,312;b.px,b.py=40+i%170,40+i%220
            a.update_enemies(DT);b.update_enemies(DT)
            self.assertEqual((ea.x,ea.y,ea.phase),(eb.x,eb.y,eb.phase))

    def test_warning_then_stationary_upward_volley_then_slow_escape(self):
        g=sandbox();e=g.spawn_rear(128)
        while e.phase in ('marker','entry'):g.update_enemies(DT)
        for _ in range(math.floor(C.REAR_WARNING_SECONDS*C.FPS)-1):
            g.update_enemies(DT);self.assertEqual(g.bullets,[])
        fire_times=[]
        for i in range(500):
            n=len(g.bullets);y=e.y;phase=e.phase
            g.update_enemies(DT)
            if len(g.bullets)>n:
                fire_times.append(i*DT)
                self.assertEqual(e.y,C.REAR_STOP_Y)
                self.assertTrue(C.HUD_HEIGHT+12<e.y<C.HEIGHT-12)
            if phase=='exit':
                self.assertEqual(len(g.bullets),n)
                self.assertAlmostEqual(y-e.y,C.REAR_EXIT_SPEED*DT)
        self.assertEqual(len(g.bullets),C.REAR_SHOTS)
        self.assertLess(C.REAR_EXIT_SPEED,C.PLAYER_SPEED)
        for a,b in zip(fire_times,fire_times[1:]):self.assertAlmostEqual(b-a,C.REAR_SHOT_INTERVAL,delta=DT+1e-7)
        for bullet in g.bullets:
            self.assertEqual((bullet.vx,bullet.vy,bullet.source),(0,-C.REAR_BULLET_SPEED,'rear'))
        self.assertLess(e.y,C.REAR_STOP_Y-100)

    def test_offscreen_position_cannot_fire(self):
        g=sandbox();e=g.spawn_rear(128);e.phase='fire';e.y=350
        for _ in range(200):g.update_enemies(DT)
        self.assertEqual(g.bullets,[])

    def test_entry_grace_is_local_and_does_not_make_player_invincible(self):
        g=sandbox();e=g.spawn_rear(128);e.phase='entry';e.y=g.py
        g.bullets=[Bullet(g.px,g.py,0,0)]
        g.step(DT,Actions(slash=True))
        self.assertEqual(g.hp,2)
        self.assertFalse(e.contact_active)

    def test_evade_then_counter_with_blade_or_shots_after_pass(self):
        for blade in (False,True):
            with self.subTest(blade=blade):
                g=sandbox();g.px,g.py=128,266;e=g.spawn_rear(128)
                # 実際に下端から入場させ、横へ避けてから追い越すのを待つ。
                for _ in range(750):
                    if e.phase=='exit' and e.y<230:
                        a=Actions(x=1 if g.px<126 else 0,slash=blade and abs(g.px-e.x)<16 and 30<g.py-e.y<76)
                        if not blade:g.shot_clock=min(0,g.shot_clock)
                    else:a=Actions(x=-1 if g.px>80 else 0)
                    g.step(DT,a)
                    if e.hp<=0:break
                self.assertLessEqual(e.hp,0)
                self.assertEqual(e.shots_fired,C.REAR_SHOTS)
                self.assertEqual(g.hp,3)
                self.assertEqual(g.blade_kills_by_kind['rear'],int(blade))
                self.assertEqual(g.shot_kills_by_kind['rear'],int(not blade))

    def test_upward_bullet_behind_player_still_requires_movement(self):
        for move in (False,True):
            g=sandbox();g.px,g.py=128,230
            g.bullets=[Bullet(128,250,0,-C.REAR_BULLET_SPEED,'rear')]
            for _ in range(90):g.step(DT,Actions(x=int(move and g.px<170),slash=g.cooldown<=0 and g.swing<0))
            self.assertEqual(g.hp,3 if move else 2)


if __name__=='__main__':unittest.main()
