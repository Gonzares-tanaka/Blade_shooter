"""Group clocks, visible warning, natural residual bullets and unchanged content."""
import unittest,sys,runpy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from stealth import StealthChain
from stage2_config import STEALTH_ATTACK as A,STEALTH,STEALTH_ROUTE,ROCK_FLOWS,stage2_course
from game import Game,Bullet

class CadenceTests(unittest.TestCase):
    def test_alternating_groups_and_full_rests_even_with_missing_group(self):
        for live in (tuple(range(6)),(0,1,2),(3,4,5),(5,)):
            b=StealthChain();b.active=True
            for i,p in enumerate(b.parts):
                if i not in live:p.hp=0
            events=[];rest_frames=0
            for frame in range(28*60):
                commands=b.update(1/60,True);group,state,phase=b.attack_state()
                if state=='rest':
                    rest_frames+=1;self.assertFalse(commands)
                for p,*_ in commands:
                    self.assertEqual(b.parts.index(p)//A['group_size'],group)
                    self.assertEqual(state,'fire');events.append((b.fight_time,b.parts.index(p)))
                for p in b.parts:
                    if p.phase=='warning':
                        self.assertEqual(state,'warning')
                        self.assertEqual(b.parts.index(p)//A['group_size'],group)
            self.assertEqual(rest_frames,20*60)
            expected=len(live)*6
            self.assertEqual(len(events),expected)
            self.assertTrue(all(e[1] in live for e in events))

    def test_visible_group_warning_precedes_each_shooters_first_volley(self):
        b=StealthChain();b.active=True;warned={}
        for _ in range(14*60):
            for p,*_ in b.update(1/60,True):
                i=b.parts.index(p)
                self.assertIn(i,warned)
                self.assertGreaterEqual(b.fight_time-warned[i],A['warning']-1/60-1e-8)
            for i,p in enumerate(b.parts):
                if p.phase=='warning':warned.setdefault(i,b.fight_time)

    def test_rest_and_source_destruction_do_not_delete_bullets(self):
        g=Game('stealth');g.reset();b=g.boss;b.active=True;b.fight_time=2.01
        bullet=Bullet(20,200,0,126,'boss:stealth_1');g.bullets=[bullet]
        g.update_boss(.01);self.assertIn(bullet,g.bullets)
        g.damage_enemy(b.parts[0],999);self.assertIn(bullet,g.bullets)
        g.step(.1);self.assertIn(bullet,g.bullets);self.assertGreater(bullet.y,200)

    def test_rocks_weapons_hp_and_movement_remain_unchanged(self):
        root=Path(__file__).resolve().parents[1]
        old=runpy.run_path(str(root/'verification/v0.14.1/before/stage2_config.py'))
        self.assertEqual(ROCK_FLOWS,old['ROCK_FLOWS'])
        self.assertEqual(stage2_course(),old['stage2_course']())
        self.assertEqual(STEALTH_ROUTE,old['STEALTH_ROUTE'])
        for k in ('count','hp','radius','delay','bullet_speed','cross_speed','break_speed'):
            self.assertEqual(STEALTH[k],old['STEALTH'][k])

if __name__=='__main__':unittest.main()
