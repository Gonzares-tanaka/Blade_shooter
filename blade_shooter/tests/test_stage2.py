"""2面の実判定、状態引継ぎ、追尾上限、独立機体、固定配置を検証。"""
from pathlib import Path
import sys,math,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import config as C
from game import Game,Actions,Bullet,weapon_pose,point_at
from stage2_config import ROCK,ROCK_PATTERNS,MISSILE,STEALTH,steer_missile,rock_row
from stealth import StealthChain


class Stage2Tests(unittest.TestCase):
    def sandbox(self,weapon='blade'):
        g=Game('stage2',weapon=weapon);g.reset();g.schedule=lambda:None;return g

    def test_result_then_next_stage_carries_run_and_resets_local_entities(self):
        g=Game();g.reset();g.hp=2;g.weapon='axe';g.score=12345;g.add_cut(17)
        g.begin_boss()
        for part in g.boss.parts:g.damage_enemy(part,999)
        g.check_boss_defeat();self.assertEqual(g.state,'stage_clear')
        g.step(1.81);self.assertEqual(g.state,'result');self.assertTrue(g.can_advance_stage)
        previous=(g.hp,g.weapon,g.score,g.max_cut);run=g.run
        g.step(.01,Actions(confirm=True))
        self.assertIs(g.run,run);self.assertEqual(g.run.current_stage,2)
        self.assertEqual((g.hp,g.weapon,g.score,g.max_cut),previous)
        self.assertEqual((g.time,g.current_cut),(0,0));self.assertFalse(g.boss or g.enemies or g.bullets or g.items.current)

    def test_rocks_ignore_shots_and_each_weapon_breaks_without_points_cut_or_combo(self):
        for weapon in C.WEAPONS:
            g=self.sandbox(weapon);g.px,g.py=128,270
            e=g.spawn('asteroid',128,220);e.pattern='left_gap'
            g.damage_enemy(e,999);self.assertEqual(e.hp,1);self.assertIn('rock_ricochet',g.events)
            w=g.weapon_config;g.swing=w['windup']+.6*w['active'];g.swing_weapon=weapon
            angle,near,far,width=weapon_pose(weapon,g.swing)
            e.x,e.y=point_at(g.px,g.py-4,(near+far)/2,angle);e.home_x=e.x
            g.update_blade(.001)
            self.assertEqual(e.hp,0,weapon);self.assertEqual(g.rocks_destroyed,1)
            self.assertEqual((g.score,g.current_cut,g.swing_kills,g.blade_kills),(0,0,0,0))
            g.damage_enemy(e,999,True);self.assertEqual(g.rocks_destroyed,1)

    def test_missile_cut_counts_once_each_weapon_and_no_score(self):
        for weapon in C.WEAPONS:
            g=self.sandbox(weapon);g.shot_clock=999;w=g.weapon_config
            g.swing=w['windup']+.6*w['active'];g.swing_weapon=weapon
            a,n,f,width=weapon_pose(weapon,g.swing);x,y=point_at(g.px,g.py-4,(n+f)/2,a)
            g.bullets=[Bullet(x,y,0,0,'missile')]
            g.step(.001);g.step(.001)
            self.assertEqual((g.current_cut,g.max_cut,g.missiles_cut,g.score),(1,1,1,0),weapon)

    def test_missile_turn_limit_and_stops_homing(self):
        b=Bullet(128,100,0,102,'missile',MISSILE['homing_seconds'])
        before=math.atan2(b.vy,b.vx);steer_missile(b,0,20,.1)
        change=abs(math.atan2(b.vy,b.vx)-before)
        self.assertAlmostEqual(change,math.radians(65)*.1)
        for _ in range(20):steer_missile(b,0,20,.1)
        velocity=(b.vx,b.vy);steer_missile(b,256,320,.5)
        self.assertEqual((b.vx,b.vy),velocity);self.assertEqual(b.homing_remaining,0)

    def test_launched_missile_survives_carrier_death_and_pause_freezes_it(self):
        g=self.sandbox();e=g.spawn('missile',192,78)
        e.phase='warning';e.phase_time=MISSILE['warning']
        g.update_missile(e,.01);self.assertEqual(len(g.bullets),1)
        b=g.bullets[0];g.damage_enemy(e,999)
        g.step(.01);self.assertIn(b,g.bullets)
        position=(b.x,b.y,b.homing_remaining,b.age)
        g.step(.01,Actions(pause=True));g.step(5)
        self.assertEqual(position,(b.x,b.y,b.homing_remaining,b.age))

    def test_missile_warning_on_screen_and_solo_debut(self):
        g=Game('stage2');g.reset();g.time=30;g.done={i for i,w in enumerate(g.course_config['waves']) if w['at']<30}
        for _ in range(150):g.step(1/60)
        shots=[b for b in g.bullets if b.missile]
        self.assertTrue(shots);self.assertTrue(all(b.y>C.HUD_HEIGHT for b in shots))
        g=self.sandbox();e=g.spawn('missile',176);first=None;warning=None
        for frame in range(180):
            g.update_enemies(1/60)
            if e.phase=='warning' and warning is None:warning=frame/60;self.assertTrue(e.on_screen)
            if g.bullets:first=frame/60;break
        self.assertGreaterEqual(first-warning,MISSILE['warning']-1/60)

    def test_stealth_dead_slots_keep_gaps_and_head_death_continues(self):
        a,b=StealthChain(),StealthChain()
        for _ in range(240):a.update(1/60,True);b.update(1/60,True)
        b.parts[0].hp=b.parts[2].hp=0
        for _ in range(300):a.update(1/60,True);commands=b.update(1/60,True)
        self.assertEqual(len(b.parts),6)
        for pa,pb in zip(a.parts,b.parts):self.assertEqual((pa.x,pa.y),(pb.x,pb.y))
        self.assertTrue(b.parts[1].shots_fired)
        self.assertTrue(all(not p.enabled for p in (b.parts[0],b.parts[2])))
        for i,part in enumerate(b.parts):
            x,y=b.path(b.fight_time-i*STEALTH['delay'])
            self.assertAlmostEqual(part.x,x,delta=.002);self.assertAlmostEqual(part.y,y,delta=.003)

    def test_stealth_requires_all_parts_and_scores_once(self):
        g=Game('stealth');g.reset();self.assertIsInstance(g.boss,StealthChain)
        for part in g.boss.parts[:-1]:g.damage_enemy(part,999)
        g.check_boss_defeat();self.assertFalse(g.boss_defeated)
        g.damage_enemy(g.boss.parts[-1],999,True);g.check_boss_defeat()
        expected=5*2000+4000+8000
        self.assertEqual(g.score,expected);self.assertFalse(g.bullets)
        g.check_boss_defeat();self.assertEqual(g.score,expected)
        g.step(1.81);self.assertEqual(g.state,'result');self.assertFalse(g.can_advance_stage)

    def test_fixed_schedule_gaps_and_route_end_cleanup(self):
        a,b=Game('stage2',seed=1),Game('stage2',seed=999)
        self.assertEqual(a.course_config['waves'],b.course_config['waves'])
        self.assertEqual(a.duration,180);self.assertEqual(a.stage_definition.bgm,2)
        for name in ROCK_PATTERNS:
            xs=rock_row(name)
            # 生存岩を切らなくても通れる、少なくとも自機幅+余白の通路。
            gaps=[xs[0]-ROCK['radius'],256-xs[-1]-ROCK['radius']]+[r-l-2*ROCK['radius'] for l,r in zip(xs,xs[1:])]
            self.assertGreaterEqual(max(gaps),48,name)
        a.reset();a.time=a.duration-1/60
        a.spawn('asteroid',128,220).pattern='left_gap';a.bullets=[Bullet(20,120,0,0,'missile',1)]
        for _ in range(125):a.step(1/60)
        self.assertIsInstance(a.boss,StealthChain);self.assertFalse(a.bullets or a.enemies)
        self.assertLessEqual(a.boss_spawned_at,182.05)

    def test_retry_clears_stage2_state_and_preserves_weapon_selection(self):
        g=self.sandbox('lance');g.rocks_destroyed=7;g.missiles_cut=5;g.score=999;g.hp=1
        g.add_cut(4);g.hurt();g.step(.1,Actions(retry=True))
        self.assertEqual((g.score,g.max_cut,g.hp,g.rocks_destroyed,g.missiles_cut),(0,0,3,0,0))
        self.assertEqual(g.weapon,'lance');self.assertEqual(g.run.current_stage,2)

    def test_return_to_title_and_comparison_use_consistent_stage_metadata(self):
        g=Game();g.enter_stage(2,carry_run=False);g.score=123;g.hp=1;g.hurt()
        g.step(.01,Actions(title=True))
        self.assertEqual((g.state,g.run.current_stage,g.stage_definition.number,g.score),('title',1,1,0))
        g.choose_course('stage2');g.set_lab('weapons');g.reset()
        self.assertEqual((g.course,g.stage_definition.number),('compare',1))


if __name__=='__main__':unittest.main()
