"""武器の時間/実体、開始前選択の契約を検証。"""
import sys, unittest, math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import config as C
from game import Game,Actions,Bullet,weapon_pose
from main import Input
from test_input import FakePyxel

class WeaponTests(unittest.TestCase):
    def sandbox(self,weapon):
        g=Game('compare',weapon=weapon);g.reset();g.schedule=lambda:None;return g

    def test_blade_values_preserved(self):
        w=C.WEAPONS['blade']
        self.assertEqual([w[k] for k in ('damage','reach','inner','width','windup','active','recovery','cooldown')],
                         [40,60,30,4,.07,.10,.24,1])

    def test_each_attack_hits_enemy_once_and_does_not_grant_invulnerability(self):
        for weapon in C.WEAPONS:
            with self.subTest(weapon=weapon):
                g=self.sandbox(weapon);w=g.weapon_config
                e=g.spawn('armor',g.px,g.py-4-(38 if weapon=='axe' else 50));e.hp=1000
                g.start_slash()
                for i in range(80):g.update_blade(.01)
                self.assertEqual(e.hp,1000-w['damage'])
                self.assertEqual(g.invincible,0)
                self.assertEqual(g.slash_hits,{e.uid})

    def test_all_phases_move_shots_resume_during_remaining_cooldown(self):
        for weapon in C.WEAPONS:
            g=self.sandbox(weapon);w=g.weapon_config;start=g.px
            g.step(.001,Actions(slash=True,x=1))
            self.assertGreater(g.px,start)
            while g.swing>=0:
                old=g.px;g.step(.001,Actions(x=-1 if g.px>100 else 1))
                self.assertNotEqual(g.px,old);self.assertNotIn('shot',g.events)
            self.assertGreater(g.cooldown,0)
            self.assertFalse(g.start_slash())
            g.step(.001);self.assertIn('shot',g.events)
            self.assertLessEqual(abs((w['cooldown']-g.cooldown)-w['shot_stop']),.003)
            while g.cooldown>0:g.step(.001)
            self.assertTrue(g.start_slash())

    def test_lance_long_narrow_and_no_dash_axe_short(self):
        def hit(weapon,dx,distance):
            g=self.sandbox(weapon);e=g.spawn('armor',g.px+dx,g.py-4-distance);e.hp=1000
            g.start_slash()
            for i in range(80):g.update_blade(.01)
            return e.hp<1000
        self.assertTrue(hit('lance',0,92));self.assertFalse(hit('blade',0,92));self.assertFalse(hit('axe',0,92))
        self.assertTrue(hit('blade',44,30));self.assertFalse(hit('lance',44,30))
        for weapon in C.WEAPONS:
            g=self.sandbox(weapon);xy=g.px,g.py
            for i in range(100):g.step(.01,Actions(slash=i==0))
            self.assertEqual((g.px,g.py),xy)
        near=weapon_pose('lance',C.WEAPONS['lance']['windup'])
        self.assertEqual(near[2],46) # full reach is not active at the start of the thrust

    def test_windup_recovery_and_previous_frame_are_not_shields(self):
        for weapon in C.WEAPONS:
            g=self.sandbox(weapon);w=g.weapon_config;g.start_slash()
            g.update_blade(w['windup']/2);self.assertFalse(g.slash_polys)
            g.update_blade(w['active']);self.assertTrue(g.slash_polys)
            g.update_blade(w['windup']+w['active']);g.update_blade(.001);self.assertFalse(g.slash_polys)
            g.bullets=[Bullet(g.px,g.py,0,0)]
            g.step(.001);self.assertEqual(g.hp,C.PLAYER_HP-1)

    def test_lance_width_hits_and_erases_visible_sixteen_pixel_tip(self):
        g=self.sandbox('lance');w=g.weapon_config
        self.assertEqual(w['width'],C.PLAYER_SIZE)
        g.swing=w['windup']+.7*w['active'];g.cooldown=.5;g.shot_clock=999
        e=g.spawn('small',g.px+15,g.py-4-80);e.hp=500
        g.bullets=[Bullet(g.px+10,g.py-4-80,0,0),Bullet(g.px+12,g.py-4-80,0,0)]
        g.step(.001)
        self.assertEqual(e.hp,500-w['damage'])
        self.assertEqual(g.cleared_bullets,1);self.assertEqual(len(g.bullets),1)
        self.assertEqual(g.bullets[0].x,g.px+12)
        from assets import SPRITES
        self.assertEqual(SPRITES['lance'],(208,0,28,16))

    def test_other_weapon_performance_unchanged(self):
        import runpy
        old=runpy.run_path(str(Path(__file__).resolve().parents[1]/'verification/v0.9.0/before/config.py'))
        for weapon,w in old['WEAPONS'].items():
            for key,value in w.items():
                if weapon=='lance' and key=='width':continue
                self.assertEqual(C.WEAPONS[weapon][key],value,(weapon,key))

    def test_settings_physical_rows_locks_and_retry(self):
        g=Game('compare');g.step(.01,Actions(settings=True));self.assertEqual(g.state,'settings')
        g.step(.01,Actions(x=1));self.assertEqual(g.weapon,'axe')
        g.step(.01);g.step(.01,Actions(y=1));g.step(.01);g.step(.01,Actions(x=1))
        self.assertEqual(g.touch_mode,'flick');self.assertEqual(g.lab_mode,'weapons')
        g.step(.01,Actions(weapon=1));self.assertEqual(g.weapon,'lance')
        g.step(.01,Actions(confirm=True));self.assertEqual(g.state,'title')
        g.step(.01,Actions(confirm=True));self.assertEqual(g.state,'playing')
        g.step(.01,Actions(weapon=1,settings=True,lab=2))
        self.assertEqual((g.weapon,g.touch_mode),('lance','flick'))
        g.state='gameover';g.step(.01,Actions(confirm=True))
        self.assertEqual((g.weapon,g.touch_mode,g.lab_mode),('lance','flick','weapons'))

    def test_gkd_b_settings_and_select_exit_mapping(self):
        p=FakePyxel();i=Input(p,'gkd');g=Game()
        p.held={p.GAMEPAD1_BUTTON_B};p.edges=set(p.held)
        g.step(.01,i.read());self.assertEqual(g.state,'settings')
        p.held={p.GAMEPAD1_BUTTON_DPAD_RIGHT};p.edges=set(p.held)
        g.step(.01,i.read());self.assertEqual(g.weapon,'axe')
        p.held={p.GAMEPAD1_BUTTON_BACK};p.edges=set(p.held);self.assertTrue(i.read().quit)

    def test_comparison_schedule_identical_for_every_setting(self):
        schedules=[]
        for weapon in C.WEAPONS:
            for touch in C.TOUCH_MODES:
                g=Game('compare',seed=999,weapon=weapon,touch_mode=touch)
                schedules.append(g.course_config['waves'])
                self.assertEqual(g.duration,54)
        self.assertTrue(all(s==schedules[0] for s in schedules))
        self.assertTrue({'formation','armor','charger'}<={w['kind'] for w in schedules[0]})
        self.assertTrue(any(w['pattern']=='barrage' for w in schedules[0]))

if __name__=='__main__':unittest.main()
