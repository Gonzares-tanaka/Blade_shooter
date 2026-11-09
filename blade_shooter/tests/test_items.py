"""取得の表示確定・攻撃スナップショット・エリア境界と時間停止を検証。"""
import math
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import config as C
from game import Game,Actions,Bullet
from items import AreaItem


class ItemTests(unittest.TestCase):
    def sandbox(self, weapon="blade"):
        g=Game(weapon=weapon);g.reset();g.schedule=lambda:None
        return g

    def put(self,g,kind,cycle=0):
        g.items.current=AreaItem(0,g.px,g.py,kind,cycle=cycle)

    def test_six_area_ends_and_bounded_final_boss_spawn(self):
        g=self.sandbox()
        self.assertEqual(g.items.ends,[40,80,120,160,210,300])
        for i,end in enumerate(g.items.ends):
            g.time=end-.01;g.items.current=None
            g.step(.01)
            if end<300:
                self.assertIsNone(g.items.current)
                for _ in range(31):g.step(1/C.FPS)
            else:
                self.assertEqual(g.boss_spawned_at,300)
            self.assertEqual(g.items.current.area,i)
            self.assertGreaterEqual(math.hypot(g.px-g.items.current.x,g.py-g.items.current.y),64)
            self.assertEqual(len([h for h in g.items.history if h['event']=='spawn']),i+1)
            g.items.schedule(g);g.items.schedule(g)
            self.assertEqual(len([h for h in g.items.history if h['event']=='spawn']),i+1)
        # 取得しなくても、ボス初撃はアイテムの寿命に依存しない。
        g.bullets=[];g.enemies=[]
        for _ in range(6*C.FPS):g.step(1/C.FPS)
        self.assertIsNotNone(g.boss.first_fire_time)
        self.assertLess(g.boss.first_fire_time,306)
        self.assertIsNotNone(g.items.current)

    def test_collision_uses_last_displayed_kind_even_on_switch_frame(self):
        g=self.sandbox();g.hp=1
        self.put(g,"heal",.799)
        class NoDraw:
            def choice(self,pool):raise AssertionError('pickup must not draw another type')
        g.items.rng=NoDraw()
        g.step(.02)
        self.assertEqual(g.hp,2);self.assertEqual(g.weapon,"blade")
        self.assertIsNone(g.items.current)
        self.assertEqual(g.items.history[-1]['kind'],'heal')

    def test_full_hp_and_same_weapon_are_consumed_without_upgrade(self):
        g=self.sandbox("axe");g.time=10;g.cooldown=.8
        self.put(g,"heal");g.step(.01)
        self.assertEqual(g.hp,C.PLAYER_HP);self.assertEqual(g.items.notice,'HP FULL')
        self.assertIsNone(g.items.current)
        self.put(g,"axe");g.step(.01)
        self.assertEqual(g.weapon,'axe');self.assertIsNone(g.items.current)
        self.assertAlmostEqual(g.cooldown,.78);self.assertAlmostEqual(g.time,10.02)

    def test_switch_excludes_current_with_equal_choice_pool(self):
        g=self.sandbox();g.items.current=AreaItem(0,48,190,'heal')
        class Choice:
            def choice(self,pool):
                self.pool=pool;return pool[-1]
        rng=Choice();g.items.rng=rng
        for _ in range(5):
            old=g.items.current.kind
            g.items.update(g,.8,(g.px,g.py))
            self.assertEqual(set(rng.pool),set(C.AREA_ITEM['kinds'])-{old})
            self.assertEqual(len(rng.pool),3)
            self.assertNotEqual(old,g.items.current.kind)

    def test_pause_background_and_hitstop_freeze_item_timers(self):
        g=self.sandbox();g.items.current=AreaItem(0,48,190,'lance',age=1,cycle=.7)
        item=g.items.current;g.items.notice_time=1
        expected=(item.age,item.cycle,item.y,item.kind,g.items.notice_time)
        g.step(.1,Actions(pause=True));g.step(10)
        self.assertEqual(expected,(item.age,item.cycle,item.y,item.kind,g.items.notice_time))
        g.step(.1,Actions(pause=True));g.step(.1,Actions(focus_lost=True));g.step(10)
        self.assertEqual(expected,(item.age,item.cycle,item.y,item.kind,g.items.notice_time))
        g.step(.1,Actions(confirm=True));g.hitstop=.2;g.step(.1)
        self.assertEqual(expected,(item.age,item.cycle,item.y,item.kind,g.items.notice_time))

    def test_wait_then_exit_finite_and_collectible_during_exit(self):
        g=self.sandbox();g.items.current=AreaItem(0,48,190,'lance')
        for _ in range(7*C.FPS):g.items.update(g,1/C.FPS,(g.px,g.py))
        self.assertIsNotNone(g.items.current);self.assertFalse(g.items.current.exiting)
        for _ in range(5*C.FPS):g.items.update(g,1/C.FPS,(g.px,g.py))
        self.assertIsNone(g.items.current);self.assertEqual(g.items.history[-1]['event'],'exit')
        self.put(g,'lance');g.items.current.age=9;g.step(.01)
        self.assertEqual(g.weapon,'lance');self.assertIsNone(g.items.current)

    def test_active_weapon_is_held_through_windup_swing_and_recovery(self):
        for original in C.WEAPONS:
            for new in C.WEAPONS:
                for phase in (0.0,.10,.22):
                    with self.subTest(original=original,new=new,phase=phase):
                        g=self.sandbox(original);w=C.WEAPONS[original]
                        g.update_enemies=lambda dt:None;g.shot_clock=999
                        e=g.spawn('armor',g.px,g.py-4-(38 if original=='axe' else 50));e.hp=1000
                        g.start_slash()
                        if phase:g.update_blade(phase)
                        g.hitstop=0;before=g.cooldown
                        self.put(g,new);g.step(.001)
                        self.assertEqual(g.weapon,new);self.assertEqual(g.attack_weapon,original)
                        self.assertAlmostEqual(g.cooldown,before-.001)
                        while g.swing>=0:
                            g.hitstop=0;g.step(.001);self.assertNotIn('shot',g.events)
                        self.assertEqual(e.hp,1000-w['damage'])
                        self.assertEqual(g.invincible,0)
                        g.cooldown=0;g.start_slash();self.assertEqual(g.swing_weapon,new)

    def test_idle_pickup_and_attack_same_frame_uses_new_weapon(self):
        g=self.sandbox();self.put(g,'axe');g.step(.001,Actions(slash=True))
        self.assertEqual(g.swing_weapon,'axe')
        self.assertAlmostEqual(g.cooldown,C.WEAPONS['axe']['cooldown'])

    def test_weapon_pickup_preserves_hp_progress_and_existing_combat_objects(self):
        g=self.sandbox();g.hp=1;g.time=12;g.cooldown=.7
        enemy=g.spawn('armor',48,80)
        bullet=Bullet(220,160,0,10);g.bullets=[bullet]
        self.put(g,'lance');g.step(.001)
        self.assertEqual(g.hp,1);self.assertEqual(g.weapon,'lance')
        self.assertAlmostEqual(g.time,12.001);self.assertAlmostEqual(g.cooldown,.699)
        self.assertIn(enemy,g.enemies);self.assertIn(bullet,g.bullets)

    def test_spawn_avoids_local_threat_and_never_auto_collects(self):
        g=self.sandbox();g.time=40.5
        g.spawn('armor',64,200)
        g.bullets=[Bullet(192,200,0,0)]
        pos,safe=g.items.location(g)
        self.assertTrue(safe);self.assertNotIn(pos,((64,200),(192,200)))
        g.items.schedule(g);self.assertIsNotNone(g.items.current)
        g.items.update(g,.001,(g.px,g.py));self.assertIsNotNone(g.items.current)
        # 全候補が危険なら最大2秒まで待つ。ボスは待たせない。
        g=self.sandbox();g.time=40.5
        g.items.location=lambda game:((48,200),False)
        g.items.schedule(g);self.assertIsNone(g.items.current)
        g.time=42;g.items.schedule(g);self.assertIsNotNone(g.items.current)

    def test_retry_and_checkpoint_reset_without_backfilling(self):
        g=self.sandbox();g.time=40.5;g.items.schedule(g)
        first=g.items.current.kind
        g.reset();self.assertEqual(g.items.done,set());self.assertEqual(g.items.history,[])
        self.assertIsNone(g.items.current)
        g.time=40.5;g.items.schedule(g);self.assertEqual(first,g.items.current.kind)
        g.checkpoint=3;g.reset();self.assertEqual(g.items.done,{0,1,2})
        self.assertIsNone(g.items.current)
        for course in ('compare','boss','tempo','legacy'):
            h=Game(course);h.reset();self.assertEqual(h.items.ends,[])

    def test_pickup_sweeps_relative_movement_without_missing_crossing(self):
        g=self.sandbox();g.px,g.py=64,240
        g.items.current=AreaItem(0,120,240,'axe')
        g.step(.01,Actions(drag_x=90))
        self.assertEqual(g.weapon,'axe');self.assertIsNone(g.items.current)

if __name__=='__main__':unittest.main()
