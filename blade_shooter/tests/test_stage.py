from pathlib import Path
import sys,unittest,copy
from itertools import permutations
from unittest.mock import patch
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parent)]
import config as C
from game import Game,Actions,Bullet
from main import App

DT=1/C.FPS


class StageTests(unittest.TestCase):
    def test_exact_route_length_sections_and_cutoff(self):
        c=C.COURSES['stage']
        self.assertEqual(c['duration'],300)
        self.assertEqual([s[0] for s in c['sections']],[0,40,80,120,160,210,300])
        self.assertTrue(all(0<=w['at']<300 for w in c['waves']))
        g=Game();g.reset();self.assertEqual(g.course,'stage')
        for i in range(7):
            g=Game('stage',i);g.reset();g.schedule()
            self.assertEqual(g.time,c['sections'][i][0])
            self.assertEqual(g.hp,C.PLAYER_HP)
            self.assertEqual(bool(g.boss),i==6)

    def test_seed_reproducible_and_no_consecutive_family_or_late_third(self):
        for seed in (0,1,7,42,2026):
            a=C.stage_course(seed);b=C.stage_course(seed)
            self.assertEqual(a,b)
            families=[C.MIX_CANDIDATES[k]['family'] for k in a['mix_choices']]
            self.assertTrue(all(x!=y for x,y in zip(families,families[1:])))
            for w in a['waves']:
                if w['section']=='mix' and w['kind'] in ('rear','charger'):
                    self.assertLess((w['at']-210)%C.MIX_SLOT_SECONDS,3)
        self.assertNotEqual(C.stage_course(1)['mix_choices'],C.stage_course(42)['mix_choices'])
        self.assertEqual(App.seed_option(['--seed','42']),42)
        with self.assertRaises(ValueError):App.seed_option(['--seed'])

    def test_transition_keeps_hp_enemies_bullets_and_disables_new_waves(self):
        g=Game();g.reset();g.time=300-DT;g.hp=2
        e=g.spawn('armor',64,132);e.phase='fire'
        b=Bullet(10,250,0,12,'armor');g.bullets=[b]
        g.step(DT)
        self.assertEqual((g.state,g.time,g.hp),('playing',300,2))
        self.assertEqual(g.boss_spawned_at,300)
        self.assertIn(e,g.enemies);self.assertIn(b,g.bullets)
        n=g.uid
        for _ in range(5*C.FPS):
            g.step(DT,Actions(x=1 if g.px<230 else 0))
        self.assertEqual(g.uid,n)
        self.assertFalse(g.boss.active)  # 残弾がまだ画面内なら初撃を待つ。
        self.assertIsNone(g.boss.first_fire_time)
        self.assertTrue(all(p.shots_fired==0 for p in g.boss.parts))

    def test_real_residuals_leave_before_first_boss_attack(self):
        g=Game('stage',6);g.reset()
        b=Bullet(10,288,0,-92,'rear');g.bullets=[b]
        for _ in range(5*C.FPS):g.step(DT)
        self.assertNotIn(b,g.bullets)
        self.assertTrue(g.boss.active)
        self.assertGreaterEqual(g.boss.first_fire_time,304+C.BOSS_PARTS['left']['warning_at']+C.BOSS_PARTS['left']['warning']-DT)
        self.assertFalse(g.stage_complete)

    def test_all_three_arbitrary_order_and_bullets_survive_destruction(self):
        for order in permutations(C.BOSS_PARTS):
            g=Game('boss');g.reset()
            for _ in range(8*C.FPS):
                g.time+=DT;g.update_boss(DT)
            self.assertEqual(len(g.boss.parts),3)
            self.assertEqual({b.source for b in g.bullets},{'boss:left','boss:right','boss:center'})
            saved=list(g.bullets)
            for key in order:
                p=next(p for p in g.boss.parts if p.key==key)
                g.damage_enemy(p,p.hp,blade=True)
                counts={x.key:x.shots_fired for x in g.boss.parts}
                for _ in range(round(C.BOSS_CYCLE_SECONDS*C.FPS)):
                    g.time+=DT;g.update_boss(DT)
                self.assertEqual(p.shots_fired,counts[key])
                self.assertTrue(all(b in g.bullets for b in saved))
                for other in g.boss.parts:
                    if other.hp>0:self.assertGreater(other.shots_fired,counts[other.key])
                g.check_boss_defeat()
                self.assertEqual(g.state,'clear' if key==order[-1] else 'playing')
            self.assertEqual(tuple(g.boss.destroyed_order),order)

    def test_blade_reaches_parts_from_outside_contact_hull(self):
        for key in C.BOSS_PARTS:
            g=Game('boss');g.reset()
            for _ in range(round(C.BOSS_ENTRY_SECONDS*C.FPS)+1):g.update_boss(DT)
            p=next(p for p in g.boss.parts if p.key==key)
            g.px,g.py=p.x,p.y+52
            hp=p.hp
            for f in range(16):g.step(DT,Actions(slash=f==0))
            self.assertEqual(p.hp,hp-C.BLADE_DAMAGE)
            self.assertEqual(g.hp,C.PLAYER_HP)
            self.assertGreater(g.py-8,max(v[1] for v in g.boss.hull))

    def test_warning_peaks_and_real_global_opening(self):
        firsts=[]
        for key,p in C.BOSS_PARTS.items():firsts.append(p['warning_at']+p['warning'])
        self.assertGreater(min(b-a for a,b in zip(sorted(firsts),sorted(firsts)[1:])),1)
        self.assertGreater(C.BOSS_CYCLE_SECONDS-C.BOSS_OPEN_FROM,3)
        g=Game('boss');g.reset()
        for _ in range(round((C.BOSS_ENTRY_SECONDS+C.BOSS_OPEN_FROM+.1)*C.FPS)):g.update_boss(DT)
        counts=[p.shots_fired for p in g.boss.parts]
        for _ in range(2*C.FPS):
            g.update_boss(DT)
            self.assertTrue(g.boss.opening)
        self.assertEqual(counts,[p.shots_fired for p in g.boss.parts])

    def test_pause_freezes_boss_and_retry_recreates_parts_and_same_seed(self):
        g=Game('stage',6,seed=42);g.reset();g.step(DT)
        age=g.boss.age;g.step(DT,Actions(pause=True));g.step(1)
        self.assertEqual(g.boss.age,age)
        self.assertEqual(g.state,'paused')
        g.state='gameover';g.step(DT,Actions(confirm=True))
        self.assertEqual(g.seed,42)
        self.assertEqual(g.time,300)
        self.assertTrue(all(p.hp==p.max_hp for p in g.boss.parts))


if __name__=='__main__':unittest.main()
