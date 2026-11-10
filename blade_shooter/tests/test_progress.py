"""実際の撃破/弾消し/遷移を通して得点、CUT、終了と保存を検査。"""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from types import SimpleNamespace
import contextlib,io,sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import config as C
from game import Game,Actions,Bullet
from items import AreaItem
from persistence import BestStore
from stages import STAGES,PLANNED_STAGE_COUNT

class ProgressTests(unittest.TestCase):
    def sandbox(self,weapon='blade'):
        g=Game(weapon=weapon);g.reset();g.schedule=lambda:None;return g

    def test_shot_melee_points_and_death_guard(self):
        for kind,points in (('small',100),('charger',200),('rear',250),('armor',500)):
            for melee in (False,True):
                g=self.sandbox();enemy=g.spawn(kind,80,100)
                g.damage_enemy(enemy,enemy.hp,blade=melee)
                self.assertEqual(g.score,points*(2 if melee else 1))
                g.damage_enemy(enemy,999,blade=melee);self.assertEqual(g.score,points*(2 if melee else 1))

    def test_real_three_kill_swing_bonus_once_and_next_swing_reset(self):
        g=self.sandbox();g.px,g.py=128,230;g.shot_clock=999
        g.spawn_formation(128,176)
        for i in range(25):g.step(1/C.FPS,Actions(slash=i==0))
        self.assertEqual(g.blade_kills,3);self.assertEqual(g.score,1000) # 3*100*2+2*200
        self.assertEqual(g.combo_text,'TRIPLE +400')
        for _ in range(80):g.step(1/C.FPS)
        self.assertEqual(g.score,1000)
        g.start_slash();e=g.spawn('armor',128,170);g.damage_enemy(e,e.hp,True)
        self.assertEqual(g.score,2000) # 一振り目の複数撃破数を持ち越さない。

    def test_all_boss_parts_and_ship_once_with_melee_multiplier(self):
        g=Game('boss');g.reset();g.start_slash()
        for part in g.boss.parts:g.damage_enemy(part,part.hp,True)
        self.assertEqual(g.score,22000+400)
        g.bullets=[Bullet(g.px,g.py,0,0,'boss:left')]
        g.check_boss_defeat();self.assertEqual(g.score,32400)
        self.assertEqual(g.state,'stage_clear');self.assertFalse(g.bullets)
        for _ in range(5):g.check_boss_defeat();g.update_boss(.5)
        self.assertEqual(g.score,32400);self.assertFalse(g.bullets)
        g.step(1.8);self.assertEqual(g.state,'result');self.assertEqual(g.result.score,32400)
        self.assertTrue(g.result.boss_defeated)

    def test_shot_boss_points_do_not_receive_melee_bonus(self):
        g=Game('boss');g.reset()
        for part in g.boss.parts:g.damage_enemy(part,part.hp)
        g.check_boss_defeat();self.assertEqual(g.score,21000)

    def test_each_weapon_erases_each_bullet_once_and_does_not_score(self):
        for weapon in C.WEAPONS:
            g=self.sandbox(weapon);w=g.weapon_config;g.shot_clock=999
            g.swing=w['windup']+.7*w['active'];g.swing_weapon=weapon
            if weapon=='lance':x,y=g.px,g.py-84
            else:
                from game import point_at,weapon_pose
                angle,near,far,width=weapon_pose(weapon,g.swing)
                x,y=point_at(g.px,g.py-4,(near+far)/2,angle)
            g.bullets=[Bullet(x,y,0,0) for _ in range(3)]
            g.step(.001)
            self.assertEqual(g.current_cut,3,weapon);self.assertEqual(g.max_cut,3)
            self.assertEqual(g.score,0);self.assertFalse(g.bullets)
            g.step(.001);self.assertEqual(g.current_cut,3)

    def test_cut_timeout_damage_and_maximum(self):
        g=self.sandbox();g.add_cut(8);g.step(1.49)
        self.assertEqual(g.current_cut,8);g.step(.01);self.assertEqual(g.current_cut,0)
        self.assertEqual(g.max_cut,8);g.add_cut(2);g.hurt()
        self.assertEqual(g.current_cut,0);self.assertEqual(g.max_cut,8)
        g.invincible=0;g.hp=1;g.hurt()
        self.assertEqual(g.state,'gameover');self.assertEqual(g.result.max_cut,8)

    def test_no_enemy_body_cut_counts_as_bullet_cut(self):
        g=self.sandbox();g.start_slash();e=g.spawn('armor',128,180)
        g.damage_enemy(e,999,True);self.assertEqual(g.current_cut,0)

    def test_cut_grace_frozen_during_pause_intro_and_results(self):
        g=self.sandbox();g.add_cut(4);g.step(.1,Actions(pause=True));g.step(8)
        self.assertEqual(g.run.cut_remaining,1.5)
        g.step(.1,Actions(pause=True));g.begin_boss()
        g.step(.5);self.assertEqual(g.run.cut_remaining,1.5)
        for part in g.boss.parts:g.damage_enemy(part,999)
        g.check_boss_defeat();g.step(1);self.assertEqual(g.run.cut_remaining,1.5)
        g.step(1);g.step(5);self.assertEqual(g.run.cut_remaining,1.5)

    def test_result_retry_completely_resets_and_title_keeps_selection(self):
        g=self.sandbox('lance');g.add_score(1234,'test');g.add_cut(9)
        g.time=299;g.checkpoint=5;g.hp=1
        g.enemies=[g.spawn('armor',80,100)];g.bullets=[Bullet(10,10,0,0)]
        g.items.current=AreaItem(2,64,200,'axe');g.hurt()
        self.assertEqual(g.result.score,1234);self.assertEqual(g.result.max_cut,9)
        g.step(.1,Actions(retry=True))
        self.assertEqual((g.score,g.current_cut,g.max_cut,g.hp,g.time),(0,0,0,3,0))
        self.assertFalse(g.enemies or g.bullets or g.shots or g.items.current or g.boss)
        self.assertEqual(g.items.done,set());self.assertEqual(g.weapon,'lance')
        self.assertEqual(g.best_score,1234)
        g.hp=1;g.invincible=0;g.hurt();g.step(.1,Actions(y=1));g.step(.1,Actions(confirm=True))
        self.assertEqual(g.state,'title');self.assertEqual(g.selected_weapon,'lance')

    def test_cleanup_bounded_no_new_enemies_and_final_item_not_delayed(self):
        g=self.sandbox();g.time=300-1/C.FPS
        g.spawn('armor',80,100);g.bullets=[Bullet(10,100,0,0,'armor')]
        g.add_cut(4);g.step(1/C.FPS)
        self.assertTrue(g.boss_pending);self.assertIsNone(g.boss)
        self.assertEqual(g.items.current.area,5)
        for _ in range(122):g.step(1/C.FPS)
        self.assertIsNotNone(g.boss);self.assertLessEqual(g.boss_spawned_at,302.02)
        self.assertFalse(g.enemies or g.bullets);self.assertEqual(g.current_cut,4)
        self.assertEqual(g.uid,1)

    def test_stage_registry_only_one_and_common_state_can_be_carried(self):
        self.assertEqual(PLANNED_STAGE_COUNT,3);self.assertEqual(tuple(STAGES),(1,))
        g=self.sandbox();g.hp=2;g.weapon='axe';g.score=123;g.add_cut(4)
        old=g.run;g.enter_stage(1,carry_run=True)
        self.assertIs(old,g.run);self.assertEqual((g.hp,g.weapon,g.score,g.max_cut),(2,'axe',123,4))
        self.assertTrue({'stage_number','duration','waves','mixed_candidates','background','bgm','item_points','boss','boss_bgm','clear_target','next_stage'}<=g.stage_data.keys())
        with self.assertRaises(ValueError):g.enter_stage(2)

    def test_debug_log_off_by_default_and_reports_score_cut_end_when_enabled(self):
        g=self.sandbox();g.add_score(100,'test');self.assertEqual(g.debug_log,[])
        g.debug=True
        with contextlib.redirect_stdout(io.StringIO()):
            g.add_score(50,'test');g.add_cut(2);g.hp=1;g.hurt()
        self.assertTrue({'score','cut','max_cut','stage_end'}<={e['event'] for e in g.debug_log})

class PersistenceTests(unittest.TestCase):
    def test_native_roundtrip_atomic_update_and_corrupt_load(self):
        with TemporaryDirectory() as folder:
            path=Path(folder)/'save/best.json';a=BestStore(path=path)
            self.assertTrue(a.save(321));self.assertEqual(BestStore(path=path).best,321)
            self.assertTrue(a.save(123));self.assertEqual(BestStore(path=path).best,321)
            path.write_text('not json');b=BestStore(path=path)
            self.assertEqual(b.best,0);self.assertTrue(b.failed)

    def test_native_write_failure_is_memory_only_without_throwing(self):
        with TemporaryDirectory() as folder:
            a=BestStore(path=Path(folder)/'save/best.json')
            with patch('pathlib.Path.mkdir',side_effect=PermissionError('readonly')):
                self.assertFalse(a.save(999));self.assertEqual(a.best,999)
                self.assertFalse(a.save(999))

    def test_web_blocked_load_and_failed_save_do_not_stop_run(self):
        def blocked():raise OSError('storage denied')
        store=BestStore(SimpleNamespace(loadBestScore=blocked,saveBestScore=lambda score:False))
        g=Game();g.reset();g.score=200;g.hp=1;g.hurt()
        self.assertFalse(store.save(g.best_score));self.assertEqual(store.best,200)
        g.step(.1,Actions(retry=True));self.assertEqual(g.state,'playing')

if __name__=='__main__':unittest.main()
