import sys,unittest,runpy
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parent)]
import config as C
from game import Game,Actions,weapon_pose
from verify_stage1_balance import weapon_fixture

class Stage1BalanceTests(unittest.TestCase):
    def test_target_is_middle_of_other_routes_and_rewards_have_approach_time(self):
        self.assertEqual(C.STAGE_SECONDS,(C.COURSES['stage2']['duration']+C.COURSES['stage3']['duration'])/2)
        g=Game();g.reset();self.assertEqual(g.items.ends,[30,65,105,161])
        for end in g.items.ends[:-1]:
            first=min(w['at'] for w in g.course_config['waves'] if w['at']>=end)
            self.assertGreaterEqual(first-end,5)
        self.assertEqual(g.duration-g.items.ends[-1],4)
        self.assertLess(max(w['at'] for w in g.course_config['waves']),g.items.ends[-1])

    def test_only_reach_and_inner_change_in_weapon_table_and_shots_are_unchanged(self):
        old=runpy.run_path(str(Path(__file__).resolve().parents[1]/'verification/v0.19.0/before/config.py'))
        for key in ('blade','axe'):self.assertEqual(C.WEAPONS[key],old['WEAPONS'][key])
        for key,value in old['WEAPONS']['lance'].items():
            if key not in ('reach','inner'):self.assertEqual(C.WEAPONS['lance'][key],value)
        self.assertEqual(C.WEAPONS['lance']['reach'],old['WEAPONS']['lance']['reach']*1.5)
        self.assertEqual(C.WEAPONS['lance']['reach']-C.WEAPONS['lance']['inner'],28)
        for key in ('SHOT_INTERVAL','SHOT_DAMAGE','SHOT_SPEED','BOSS_PARTS','WEB_TOUCH'):
            self.assertEqual(getattr(C,key),old[key])

    def test_actual_auto_shot_step_blade_twice_axe_once_and_long_lance_hits(self):
        blade=weapon_fixture('blade');axe=weapon_fixture('axe',swings=1)
        self.assertEqual((blade['slashes'],axe['slashes']),(2,1))
        self.assertLessEqual(blade['hp'],0);self.assertLessEqual(axe['hp'],0)
        self.assertEqual([e['after'] for e in blade['damage_log'] if e['melee']][0],24)
        short=weapon_fixture('blade',125,swings=1);long=weapon_fixture('lance',125,swings=1)
        self.assertFalse(any(e['melee'] for e in short['damage_log']))
        self.assertTrue(any(e['melee'] for e in long['damage_log']))

    def test_lance_one_thrust_pierces_both_real_column_patterns(self):
        g=Game('compare',weapon='lance');g.reset();g.schedule=lambda:None;g.px,g.py=104,236
        front=g.spawn_armor(104,'column_front',132);back=g.spawn_armor(104,'column_back',88)
        front.phase=back.phase='open'
        for f in range(24):g.step(1/C.FPS,Actions(slash=f==0))
        self.assertEqual((front.hp,back.hp),(32,32))
        self.assertEqual(g.slash_hits,{front.uid,back.uid})
        self.assertEqual(g.slashes,1)
        angle,inner,reach,width=weapon_pose('lance',C.WEAPONS['lance']['windup']+C.WEAPONS['lance']['active'])
        self.assertEqual((angle,inner,reach,width),(-90,113,141,16))

    def test_armored_variant_is_local_and_final_front_rear_overlap_is_real(self):
        self.assertEqual(C.ARMOR_HP,32)
        g=Game();g.reset();g.shot_clock=999;g.invincible=999
        live_overlap=[]
        for frame in range(160*C.FPS):
            g.step(1/C.FPS)
            if 152<g.time<160:
                front=[e for e in g.enemies if e.kind=='armor' and e.pattern=='bulwark' and e.x==128 and e.on_screen]
                rear=[e for e in g.enemies if e.kind=='rear' and e.x==80 and e.on_screen]
                if front and rear:live_overlap.append(g.time)
        self.assertGreater(len(live_overlap)/C.FPS,2)

if __name__=='__main__':unittest.main()
