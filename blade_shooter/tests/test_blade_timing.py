"""突破口を作って移動する用途と、判定が残らないことの回帰検証。"""
from pathlib import Path
import sys
import unittest
sys.path[:0] = [str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parent)]
import config as C
from game import Actions, Bullet, Game, polygon_hits_circle, point_at, sweep_polygons
from test_game import sandbox, DT


class BladeTimingTests(unittest.TestCase):
    def test_all_swing_phases_stop_new_shots_but_old_shots_keep_moving(self):
        g = sandbox()
        old = Bullet(20, 240, 0, -C.SHOT_SPEED)
        g.shots = [old]
        g.shot_clock = 0
        g.start_slash()
        phases = set()
        while g.swing >= 0:
            phases.add('windup' if g.swing < C.BLADE_WINDUP else
                       'active' if g.swing < C.BLADE_WINDUP+C.BLADE_ACTIVE else 'recovery')
            g.step(DT)
            self.assertEqual(g.shots, [old])
        self.assertEqual(phases, {'windup', 'active', 'recovery'})
        self.assertLess(old.y, 240-50)
        g.step(DT)
        self.assertEqual(len(g.shots), 2)
        # 待った時間ぶんを溜めて連射しない。
        g.step(DT)
        self.assertEqual(len(g.shots), 2)

    def test_windup_and_recovery_have_no_collision_or_shots_and_allow_movement(self):
        for timer in (0, C.BLADE_WINDUP+C.BLADE_ACTIVE+0.02):
            with self.subTest(timer=timer):
                g = sandbox()
                g.swing = timer
                g.shot_clock = 0
                b = Bullet(g.px, g.py-40, 0, 0)
                g.bullets = [b]
                x = g.px
                g.step(DT, Actions(x=1))
                self.assertGreater(g.px, x)
                self.assertEqual(g.bullets, [b])
                self.assertEqual(g.shots, [])
                self.assertEqual(g.slash_polys, [])
                self.assertEqual(g.slash_slices, [])

    def test_previous_frame_trail_cannot_clear_new_bullet(self):
        g = sandbox()
        g.swing = C.BLADE_WINDUP+0.025
        g.step(DT)
        # 通過済みの左前方へ、次のフレームで弾が来る。
        x, y = point_at(g.px, g.py-4, 46, -125)
        self.assertTrue(any(polygon_hits_circle(p,x,y,1) for p in g.slash_polys))
        b = Bullet(x,y,0,0)
        g.bullets.append(b)
        g.step(DT)
        self.assertIn(b,g.bullets)

    def test_recovery_leaves_late_front_and_side_bullets_dangerous(self):
        for side in (False,True):
            with self.subTest(side=side):
                g = sandbox()
                g.swing = C.BLADE_WINDUP+C.BLADE_ACTIVE+0.01
                if side: b=Bullet(g.px+8,g.py,-180,0)
                else: b=Bullet(g.px,g.py-8,0,180)
                g.bullets = [b]
                for _ in range(3): g.step(DT)
                self.assertEqual(g.hp,2)
                self.assertEqual(g.cleared_bullets,0)

    def test_moving_in_recovery_evades_late_front_and_side_bullets(self):
        for side in (False,True):
            for move in (False,True):
                with self.subTest(side=side,move=move):
                    g=sandbox()
                    g.swing=C.BLADE_WINDUP+C.BLADE_ACTIVE+0.005
                    g.bullets=[Bullet(g.px+18,g.py,-90,0) if side else Bullet(g.px,g.py-18,0,90)]
                    for _ in range(14):
                        g.step(DT,Actions(x=int(move and not side),y=-int(move and side)))
                    self.assertEqual(g.hp,3 if move else 2)
                    self.assertEqual(g.cleared_bullets,0)

    def test_fast_rotation_and_player_translation_sweep_between_poses(self):
        # 終端の刃だけでは当たらない途中の点に、軌跡なら当たる。
        polys=sweep_polygons(148,200,-150,-30,previous=(108,200))
        self.assertTrue(any(polygon_hits_circle(p,128,154,1) for p in polys))
        self.assertFalse(any(polygon_hits_circle(p,128,222,1) for p in polys))

    def test_player_moving_during_cut_does_not_leave_old_position_shield(self):
        g=sandbox()
        g.swing=C.BLADE_WINDUP+0.04
        x, y=point_at(g.px,g.py-4,50,-90)
        g.bullets=[Bullet(x,y,0,0)]
        g.step(DT,Actions(drag_x=40))
        self.assertEqual(g.cleared_bullets,1,'moving blade must sweep from previous player position')
        # 次フレームの刃が届かない元の場所には保護が残らない。
        b=Bullet(x,y,0,0)
        g.bullets.append(b)
        g.step(DT)
        self.assertIn(b,g.bullets)

    def test_fast_bullet_crossing_blade_between_frame_endpoints_is_cut(self):
        g=sandbox()
        g.swing=C.BLADE_WINDUP+C.BLADE_ACTIVE*0.4
        # 始点も終点も刃の外、途中だけ刃に当たる相対移動。
        g.bullets=[Bullet(g.px,g.py-96,0,6000)]
        g.step(DT)
        self.assertEqual(g.cleared_bullets,1)
        self.assertEqual(g.hp,3)

    def test_near_body_bullet_is_not_cleared_even_during_active_cut(self):
        g=sandbox()
        g.swing=C.BLADE_WINDUP+C.BLADE_ACTIVE*0.4
        b=Bullet(g.px,g.py-16,0,0)
        g.bullets=[b]
        g.step(DT)
        self.assertIn(b,g.bullets)
        self.assertEqual(g.cleared_bullets,0)

    def test_stationary_fastest_repeat_does_not_stay_safe(self):
        g=Game();g.reset()
        for _ in range(int(C.STAGE_SECONDS*C.FPS)+1):
            g.step(DT,Actions(slash=g.cooldown<=1e-6 and g.swing<0))
            if g.state!='playing':break
        self.assertLess(g.hp,C.PLAYER_HP)
        self.assertGreater(g.slashes,3)

    def test_front_row_opens_then_move_through_gap(self):
        g=sandbox()
        row=[Bullet(x,222,0,C.ARMOR_BULLET_SPEED) for x in range(48,209,16)]
        side=Bullet(40,g.py,0,0)
        g.bullets=row+[side]
        for i in range(14): g.step(DT,Actions(slash=i==0))
        self.assertGreaterEqual(g.cleared_bullets,3)
        self.assertIn(side,g.bullets)
        initial=g.py
        for _ in range(36): g.step(DT,Actions(y=-1))
        self.assertLess(g.py,initial-65)
        self.assertEqual(g.hp,3)
        self.assertEqual(g.slashes,1)

    def test_repeated_slashing_cannot_protect_body_from_side_stream(self):
        g=sandbox()
        g.bullets=[Bullet(230,g.py,-C.SMALL_BULLET_SPEED,0)]
        for _ in range(180):
            g.step(DT,Actions(slash=g.cooldown<=1e-6 and g.swing<0))
        self.assertLess(g.hp,3)
        self.assertGreaterEqual(g.slashes,3)
        self.assertEqual(g.cleared_bullets,0)


if __name__=='__main__':unittest.main()
