"""Third-stage collision, reflection-only damage, campaign carry and ending flow."""
import sys,unittest,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import config as C
from game import Game,Actions,Bullet
from stage3_config import BARRIER,FINAL,ENDING,CAVE,stage3_course
from cave import CaveWalls

class Stage3Tests(unittest.TestCase):
    def test_second_result_carries_every_run_field_into_stage_three(self):
        g=Game('stage2');g.reset();g.score=12345;g.hp=2;g.weapon='axe';g.add_cut(17)
        g.begin_boss()
        for p in g.boss.parts:g.damage_enemy(p,999)
        g.check_boss_defeat();g.step(1.81)
        expected=(g.score,2,'axe',17)
        self.assertTrue(g.can_advance_stage)
        g.step(.01,Actions(next_stage=True))
        self.assertEqual(g.run.current_stage,3)
        self.assertEqual((g.score,g.hp,g.weapon,g.max_cut),expected)
        self.assertEqual(g.current_cut,0);self.assertFalse(g.enemies or g.bullets or g.cave.walls)

    def test_shield_damage_and_readable_fade_and_open(self):
        g=Game('stage3');g.reset();g.schedule=lambda:None
        e=g.spawn('barrier',128);e.y=BARRIER['y'];e.phase='shield'
        for phase in ('entry','shield','fading','exit'):
            e.phase=phase;g.damage_enemy(e,999);g.damage_enemy(e,999,True)
            self.assertEqual(e.hp,BARRIER['hp'])
        e.phase='shield';e.phase_time=BARRIER['shield_seconds']-.01
        g.update_barrier(e,.02);self.assertEqual(e.phase,'fading')
        g.update_barrier(e,BARRIER['fade_seconds']);self.assertEqual(e.phase,'open')
        g.damage_enemy(e,1);self.assertEqual(e.hp,BARRIER['hp']-1)
        g.damage_enemy(e,999,True);self.assertLessEqual(e.hp,0);self.assertEqual(g.score,BARRIER["points"]*2)

    def test_final_boss_rejects_direct_shot_and_every_melee_weapon(self):
        for weapon in C.WEAPONS:
            g=Game('final',weapon=weapon);g.reset();p=g.boss.parts[0];p.enabled=True
            g.damage_enemy(p,999);g.damage_enemy(p,999,True)
            self.assertEqual(p.hp,FINAL['hp']);self.assertEqual(g.score,0)

    def test_real_weapon_sweep_reflects_once_and_only_impact_damages(self):
        for weapon,y in (('blade',210),('axe',220),('lance',172)):
            g=Game('final',weapon=weapon);g.reset();g.boss.active=True;g.boss.fight_time=4
            p=g.boss.parts[0];g.py=266
            bullet=Bullet(128,y,0,108,'boss:final',reflectable=True);g.bullets=[bullet]
            g.step(1/60,Actions(slash=True))
            for _ in range(18):
                if bullet.friendly:break
                g.step(1/60)
            self.assertTrue(bullet.friendly,weapon)
            self.assertEqual((g.reflections,g.current_cut),(1,1),weapon)
            self.assertEqual(p.hp,FINAL['hp'],weapon)
            for _ in range(90):g.step(1/60)
            self.assertEqual(g.reflected_hits,1,weapon)
            self.assertEqual(p.hp,FINAL['hp']-FINAL['reflected_damage'],weapon)
            self.assertEqual(g.reflections,1);self.assertEqual(g.hp,3)

    def test_friendly_projectile_cannot_hurt_or_be_reflected_twice(self):
        g=Game('final');g.reset();g.boss.active=True;g.boss.fight_time=4
        g.bullets=[Bullet(g.px,g.py,0,-260,'boss:final',reflectable=True,friendly=True)]
        g.step(1/60,Actions(slash=True))
        self.assertEqual(g.hp,3);self.assertEqual(g.reflections,0);self.assertEqual(g.max_cut,0)

    def test_no_wall_trap_or_repeated_damage_when_held_against_wall(self):
        g=Game('stage3');g.reset();g.schedule=lambda:None
        for _ in range(180):g.step(1/60,Actions(x=-1))
        self.assertEqual(g.hp,2);self.assertGreaterEqual(g.px,CAVE['base_width']+8)
        self.assertEqual(g.cave.contacts,1)
        for _ in range(40):g.step(1/60,Actions(x=1))
        for _ in range(120):g.step(1/60,Actions(x=-1))
        self.assertEqual(g.hp,1);self.assertEqual(g.cave.contacts,2)

    def test_all_fixed_wall_streams_leave_a_walkable_corridor(self):
        walls=CaveWalls();waves=[w for w in stage3_course()['waves'] if w['kind']=='wall'];done=set()
        for frame in range(150*20):
            t=frame/20
            for i,w in enumerate(waves):
                if i not in done and w['at']<=t:walls.spawn(w['x'],w['pattern'],*w['wall']);done.add(i)
            walls.update(.05)
            for y in range(40,313,16):
                left,right=walls.bounds(y)
                self.assertGreaterEqual(right-left,CAVE['minimum_corridor']-1e-6)

    def test_fast_drag_path_cannot_pass_through_a_wall_corner_unharmed(self):
        g=Game('stage3');g.reset();g.cave.spawn(0,'shelf',124,150);g.cave.walls[0].y=100
        g.px,g.py=100,280
        g.cave.constrain(g,(100,80))
        self.assertEqual(g.hp,2);self.assertEqual(g.cave.contacts,1)
        self.assertEqual((g.px,g.py),(100,280))

    def test_pause_stops_wall_shield_and_boss_clocks(self):
        g=Game('stage3');g.reset();g.step(2);g.step(.01,Actions(pause=True))
        y=g.cave.walls[0].y;g.step(20);self.assertEqual(g.cave.walls[0].y,y)
        g=Game('final');g.reset();g.step(.01,Actions(pause=True));g.step(20)
        self.assertEqual(g.boss.age,0)

    def test_clear_uses_cumulative_score_once_then_credits_and_title(self):
        g=Game('final');g.reset();g.score=54321;g.run.max_cut=27;g.boss.active=True
        p=g.boss.parts[0];p.enabled=True
        g.damage_enemy(p,FINAL['hp'],reflected=True);g.check_boss_defeat();g.check_boss_defeat()
        self.assertEqual(g.state,'ending_clear')
        self.assertEqual(g.score,54321+FINAL['points']);self.assertEqual(g.result.score,g.score)
        hp=g.hp;g.hurt();self.assertEqual(g.hp,hp);self.assertFalse(g.bullets or g.enemies)
        g.step(ENDING['clear_seconds']-.1,Actions(confirm=True));self.assertEqual(g.state,'ending_clear')
        g.step(.11);self.assertEqual(g.state,'credits');self.assertEqual(g.max_cut,27)
        g.step((C.HEIGHT+len(ENDING['credits'])*ENDING['line_spacing'])/ENDING['scroll_speed']+3)
        self.assertEqual((g.state,g.run.current_stage,g.score),('title',1,0))
        self.assertEqual(g.best_score,54321+FINAL['points'])

    def test_retry_clears_all_stage_three_local_state(self):
        g=Game('stage3',weapon='lance');g.reset();g.step(2)
        g.score=999;g.add_cut(8);g.hp=1;g.hurt();g.step(.01,Actions(retry=True))
        self.assertEqual((g.score,g.max_cut,g.hp,g.time),(0,0,3,0))
        self.assertFalse(g.cave.walls or g.enemies or g.bullets);self.assertEqual(g.reflections,0)

if __name__=='__main__':unittest.main()
