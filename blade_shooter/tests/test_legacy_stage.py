from pathlib import Path
import sys,copy,unittest
from unittest.mock import patch
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parent)]
import config as C
from game import Game,Actions
from main import App
from test_game import sandbox,DT


class StageTests(unittest.TestCase):
    def test_six_sections_and_fixed_waves_use_all_four_kinds(self):
        data=C.COURSES['legacy']
        self.assertEqual([s[0] for s in data['sections']],[0,25,45,65,85,110])
        self.assertEqual(data['duration'],120)
        self.assertEqual({w['kind'] for w in data['waves']},{'formation','armor','charger','rear'})
        first=[next(w['at'] for w in data['waves'] if w['kind']==k) for k in ('formation','armor','charger','rear')]
        self.assertEqual(first,[2,25.8,46.5,67])
        for s,kinds in enumerate(({'formation'},{'armor'},{'charger'},{'rear'},{'armor','formation','rear'},{'formation'})):
            self.assertEqual({w['kind'] for w in data['waves'] if w['section']==data['plan'][s]['key']},kinds)

    def test_section_length_shifts_following_waves_and_course_end(self):
        plan=copy.deepcopy(C.LEGACY_PLAN);plan[0]['length']+=5
        changed=C.compile_course('test','test',plan)
        self.assertEqual(changed['duration'],125)
        self.assertEqual(changed['sections'][1][0],30)
        for a,b in zip(C.COURSES['legacy']['waves'],changed['waves']):
            self.assertAlmostEqual(b['at'],a['at']+(5 if a['section']!='formation' else 0))
        with patch.dict(C.COURSES,legacy=changed):
            g=Game('legacy',1);g.reset();self.assertEqual(g.time,30)
            g.time=125-DT;g.step(DT)
            self.assertEqual((g.state,g.time),('clear',125))

    def test_invalid_wave_offset_is_rejected(self):
        plan=copy.deepcopy(C.LEGACY_PLAN);plan[0]['length']=1
        with self.assertRaises(ValueError):C.compile_course('test','test',plan)

    def test_each_section_starts_clean_and_skips_earlier_waves(self):
        for i in range(6):
            g=Game('legacy',i);g.reset();start=g.time
            g.schedule()
            self.assertEqual(g.enemies,[])
            g.time+=3;g.schedule()
            expected=[w for w in g.course_config['waves'] if start<=w['at']<=g.time]
            expected_count=sum(3 if w['kind']=='formation' else 1 for w in expected)
            self.assertEqual(len(g.enemies),expected_count)
            g.reset();self.assertEqual(g.time,start)

    def test_course_and_section_menu_edges_and_options(self):
        g=Game('legacy');g.step(DT,Actions(y=1));self.assertEqual(g.checkpoint,1)
        g.step(DT,Actions(y=1));self.assertEqual(g.checkpoint,1)
        g.step(DT);g.step(DT,Actions(section=1));self.assertEqual(g.checkpoint,2)
        g.step(DT,Actions(confirm=True));self.assertEqual((g.state,g.time),('playing',45))
        g.step(DT,Actions(section=1,course=True));self.assertEqual((g.course,g.checkpoint),('legacy',2))
        g.state='gameover';g.step(DT,Actions(confirm=True));self.assertEqual(g.time,45)
        g.state='title';g.step(DT,Actions(course=True));self.assertEqual((g.course,g.checkpoint),('classic',0))
        self.assertEqual(App.options(['--course','legacy','--section','4']),('legacy',3))
        with self.assertRaises(ValueError):App.options(['--course','legacy','--section','7'])

    def test_route_end_has_clear_retry_and_future_scene_boundary(self):
        g=Game('legacy');g.reset();g.time=g.duration-DT;g.step(DT)
        self.assertEqual((g.state,g.stage_complete,g.pending_scene),('clear',True,'retry'))
        self.assertIn('route_end',g.events)
        g.step(DT,Actions(confirm=True))
        self.assertEqual((g.state,g.time,g.hp,g.pending_scene),('playing',0,3,None))

    def test_holding_move_across_clear_does_not_change_course_or_section(self):
        g=Game('legacy');g.reset();g.time=g.duration-DT
        g.step(DT,Actions(x=1,y=1));g.step(DT,Actions(x=1,y=1))
        self.assertEqual((g.state,g.course,g.checkpoint),('clear','legacy',0))

    def test_armor_and_rear_first_volley_are_staggered(self):
        g=Game('legacy');g.reset();checked=0
        for i in range(110*C.FPS):
            g.time=i*DT;g.schedule();n=g.rear_shots_fired;g.update_enemies(DT)
            g.enemies=[e for e in g.enemies if -50<e.y<C.HEIGHT+24]
            if g.rear_shots_fired>n and g.time>=98:
                armor=next(e for e in g.enemies if e.kind=='armor')
                self.assertTrue(armor.resting,(g.time,armor.settled))
                checked+=1
        self.assertEqual(checked,C.REAR_SHOTS)

    def test_finale_allows_breather_even_without_kills(self):
        g=Game('legacy',5);g.reset();g.shot_clock=999
        while g.time<118.5:
            g.step(DT,Actions(x=-1 if g.px>16 else 0))
        self.assertEqual(g.enemies,[])
        self.assertEqual(g.bullets,[])
        self.assertEqual(g.hp,3)
        self.assertEqual(g.state,'playing')


if __name__=='__main__':unittest.main()
