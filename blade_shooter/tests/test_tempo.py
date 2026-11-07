import unittest
from unittest.mock import patch
import config as C
from game import Game, Actions, Bullet
from test_game import sandbox, DT
from check_tempo import route, schedule_probe


class TempoTests(unittest.TestCase):
    def test_default_direct_test_and_identical_speed_comparison(self):
        self.assertEqual(Game().course,'stage')
        self.assertEqual(C.COURSES['tempo']['waves'],C.COURSES['tempo_fast']['waves'])
        for c,m in C.PLAYER_SPEED_PRESETS.items():
            g=Game(c);g.reset();x=g.px
            g.step(DT,Actions(x=1))
            self.assertAlmostEqual(g.px-x,125*m*DT)
            x=g.px;g.step(DT)
            self.assertEqual(g.px,x)  # 入力を離せば即停止。
            g.step(DT,Actions(drag_x=10))
            self.assertAlmostEqual(g.px-x,10*m)

    def test_compile_blocks_shift_together(self):
        from copy import deepcopy
        plan=deepcopy(C.TEMPO_PLAN);plan[0]['length']+=2
        course=C.compile_course('test','test',plan)
        self.assertEqual(course['duration'],32)
        self.assertEqual(course['sections'][1][0],12)
        self.assertEqual([w['at'] for w in course['waves'] if w['section']=='flank'],
                         [w['at']+2 for w in C.COURSES['tempo']['waves'] if w['section']=='flank'])

    def test_no_kill_schedule_has_two_kinds_and_short_three_kind_peaks(self):
        p=schedule_probe()
        self.assertEqual(p['kind_seconds'][4],0)
        self.assertGreater(p['kind_seconds'][2],p['kind_seconds'][3])
        self.assertLess(p['longest_three_kind_seconds'],5)

    def test_armor_fires_before_settling_under_normal_auto_shot(self):
        g=sandbox();g.shot_clock=0
        e=g.spawn('armor',128)
        for _ in range(90):
            g.step(DT)
            if e.shots_fired:break
        self.assertGreater(e.hp,0)
        self.assertGreater(e.shots_fired,0)
        self.assertLess(e.age,1.1)
        self.assertLess(e.y,C.ARMOR_Y)
        self.assertGreaterEqual(e.visible_time,C.ARMOR_WARNING_SECONDS)
        self.assertLessEqual(e.hp,C.ARMOR_HP)

    def test_no_offscreen_fire_from_front_enemies(self):
        for kind in ('armor','small'):
            g=sandbox();e=g.spawn(kind,128,0)
            e.age=5
            with patch.object(C,'ARMOR_ENTRY_SPEED',0),patch.dict(C.FORMATION_PATTERNS,line=dict(speed=0,sway=0,drift=0,shot_after=0)):
                for _ in range(120):g.update_enemies(DT)
            self.assertEqual(g.bullets,[])

    def test_kill_and_exit_preserve_fired_bullets(self):
        for blade in (False,True):
            g=sandbox();e=g.spawn('armor',128,132)
            g.fire(e,100,(0,))
            bullets=list(g.bullets)
            e.phase='fire'
            g.damage_enemy(e,40,blade)
            for _ in range(6):g.step(DT)
            self.assertNotIn(e,g.enemies)
            self.assertEqual(g.bullets,bullets)
            self.assertEqual(e.shots_fired,1)
        g=sandbox();e=g.spawn('armor',128,132);g.fire(e,100,(0,))
        e.age=C.ARMOR_LIFETIME+1;e.y=-49
        g.step(DT)
        self.assertNotIn(e,g.enemies)
        self.assertEqual(len(g.bullets),1)

    def test_rest_is_a_real_no_fire_approach_window(self):
        g=sandbox();e=g.spawn('armor',128,132)
        e.phase='open'
        g.px,g.py=128,250
        for f in range(55):
            g.step(DT,Actions(y=-1 if g.py>186 else 0,
                              slash=g.py<=186 and g.swing<0 and g.cooldown<=0))
        self.assertEqual(g.blade_kills_by_kind['armor'],1)
        self.assertEqual(g.hp,3)
        self.assertEqual(g.bullets,[])

    def test_moving_player_cannot_tunnel_through_bullet(self):
        g=sandbox();g.bullets=[Bullet(141,266,0,0)]
        g.step(DT,Actions(drag_x=20))
        self.assertEqual(g.hp,2)

    def test_auto_shot_without_move_or_slash_is_not_safe(self):
        r=route('tempo','idle')
        self.assertEqual(r['state'],'gameover')
        self.assertGreater(r['near_bullet_seconds'],1)


if __name__=='__main__':unittest.main()
