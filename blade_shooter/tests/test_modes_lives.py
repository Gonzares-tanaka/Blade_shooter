from pathlib import Path
from types import SimpleNamespace
import unittest,sys,zipfile,tomllib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import config as C
from game import Game,Actions,Bullet
from stage3_config import ENDING
from audio import Audio
from test_audio import Fake
from tools.convert_stage_bgm import convert
ROOT=Path(__file__).resolve().parents[1]

class ModesLivesTests(unittest.TestCase):
    def kill_boss(self,g):
        g.begin_boss()
        for part in g.boss.parts:g.damage_enemy(part,part.hp,reflected=True)
        g.check_boss_defeat()

    def last_ship(self,g):
        g.run.lives=1;g.hp=1;g.invincible=0;g.hurt()

    def test_public_menu_only_two_modes_and_stage_select(self):
        g=Game()
        self.assertEqual(g.menu_options,("START","CONTINUE"))
        g.step(.01,Actions(menu_pick=2));self.assertEqual(g.state,"title")
        g.step(.01,Actions(confirm=True))
        self.assertEqual(g.menu_options,("CAMPAIGN","STAGE SELECT","BACK"))
        g.step(.01,Actions(menu_pick=2));self.assertEqual(g.state,"stage_select")
        self.assertEqual(len(g.menu_options),4)
        for stage in (1,2,3):
            g.state="stage_select";g.step(.01,Actions(menu_pick=stage))
            self.assertEqual((g.run.current_stage,g.time,g.play_mode,g.run.lives),(stage,0,"stage_select",3))
            self.kill_boss(g);g.step(C.FLOW['clear_banner_seconds'])
            self.assertEqual(g.state,"result");self.assertFalse(g.can_advance_stage)
            self.assertEqual(g.result_options,("RETRY","TITLE"))
            g.step(.01,Actions(next_stage=True));self.assertEqual(g.state,"result")

    def test_development_direct_courses_still_start_at_requested_stage(self):
        for course,stage in (("stage2",2),("stage3",3),("stealth",2),("final",3)):
            g=Game(course);self.assertTrue(g.development)
            g.step(.01,Actions(confirm=True))
            self.assertEqual((g.state,g.run.current_stage),("playing",stage))

    def test_campaign_carries_all_state_and_final_clear_then_credits(self):
        g=Game();g.step(.01,Actions(menu_pick=1));g.step(.01,Actions(menu_pick=1))
        self.assertEqual((g.state,g.play_mode),("story","campaign"))
        g.step(.01);g.step(.01,Actions(settings=True))
        g.hp=2;g.weapon="axe";g.add_cut(7)
        for stage in (1,2):
            self.kill_boss(g);g.step(C.FLOW['clear_banner_seconds'])
            carry=(g.hp,g.weapon,g.score,g.max_cut,g.run.lives,g.run.next_extend)
            g.step(.01,Actions(next_stage=True))
            self.assertEqual(g.run.current_stage,stage+1)
            self.assertEqual((g.hp,g.weapon,g.score,g.max_cut,g.run.lives,g.run.next_extend),carry)
            self.assertEqual(g.stage_entry.score,g.score)
            self.assertEqual(g.state,"story")
            g.step(.01);g.step(.01,Actions(settings=True))
        self.kill_boss(g)
        score=g.score
        self.assertEqual((g.state,g.result.score),("ending_clear",score))
        self.assertEqual(g.score,21000+20000+20000)
        g.step(ENDING['clear_seconds']);self.assertEqual(g.state,"story")
        g.step(.01);g.step(.01,Actions(settings=True));self.assertEqual(g.state,"credits")
        g.step(200);self.assertEqual((g.state,g.score,g.can_continue),("title",0,False))

    def test_three_ships_hp_loss_respawn_and_no_scene_reset(self):
        g=Game();g.start_play(mode="stage_select");e=g.spawn("armor",60,80)
        b=Bullet(70,100,0,10);g.bullets=[b];g.time=71
        for lives in (2,1):
            for hp in (2,1):
                g.invincible=0;g.hurt();self.assertEqual(g.hp,hp)
                g.hurt();self.assertEqual(g.hp,hp)
            g.invincible=0;g.hurt()
            self.assertEqual((g.hp,g.run.lives,g.state),(3,lives,"playing"))
            self.assertEqual(g.invincible,C.LIVES['respawn_invincible'])
            self.assertEqual((g.time,g.enemies,g.bullets),(71,[e],[b]))
            g.hurt();self.assertEqual(g.hp,3)
        self.last_ship(g)
        self.assertEqual((g.state,g.hp,g.run.lives),("gameover",0,0))
        self.assertTrue(g.can_continue)

    def test_extends_cross_multiple_thresholds_once_and_resume_cursor(self):
        g=Game();g.start_play();g.add_score(29999,"test")
        self.assertEqual((g.run.lives,g.run.next_extend),(3,30000))
        self.assertNotIn("extend",g.events)
        g.add_score(1,"test");self.assertEqual((g.run.lives,g.run.next_extend),(4,60000))
        g.add_score(75000,"test");self.assertEqual((g.run.lives,g.run.next_extend),(6,120000))
        g.add_score(0,"test");self.assertEqual(g.run.lives,6)
        g.enter_stage(2);self.assertEqual(g.stage_entry.score,105000)
        g.add_score(75000,"test");self.assertEqual(g.run.next_extend,210000)
        self.last_ship(g);g.step(.01,Actions(continue_run=True))
        self.assertEqual((g.score,g.run.lives,g.run.next_extend),(105000,3,120000))
        g.add_score(14999,"test");self.assertEqual(g.run.lives,3)
        g.add_score(1,"test");self.assertEqual((g.run.lives,g.run.next_extend),(4,150000))

    def test_continue_derives_next_extend_from_restored_score_for_stage_two_three(self):
        from dataclasses import replace
        for stage in (2,3):
            for score in (0,29999,30000,60000,90001):
                with self.subTest(stage=stage,score=score):
                    g=Game();g.start_play();g.add_score(score,"entry");g.enter_stage(stage)
                    g.add_score(95000,"failed");self.last_ship(g)
                    # A stale checkpoint cursor must not grant any ship at resume.
                    g.continue_entry=replace(g.continue_entry,next_extend=1)
                    g.continue_play()
                    expected=(score//30000+1)*30000
                    self.assertEqual((g.score,g.run.lives,g.run.next_extend),(score,3,expected))
                    g.add_score(0,"resume");self.assertEqual(g.run.lives,3)
                    g.add_score(expected-score,"next threshold");self.assertEqual(g.run.lives,4)
                    g.add_score(0,"duplicate");self.assertEqual(g.run.lives,4)

    def test_credits_replace_only_names_and_keep_roles_order(self):
        import runpy
        old=runpy.run_path(str(ROOT/'verification/v0.17.1/before/stage3_config.py'))['ENDING']
        self.assertEqual(ENDING['credits'],tuple('GONZARES TANAKA' if name=='TBD' else name for name in old['credits']))
        self.assertFalse(any('TBD' in line for line in ENDING['credits']))
        self.assertEqual(ENDING['credits'].count('GONZARES TANAKA'),3)
        self.assertEqual({k:v for k,v in ENDING.items() if k!='credits'},{k:v for k,v in old.items() if k!='credits'})

    def test_stage_two_three_continue_rolls_back_score_and_clears_all_local_state(self):
        for stage in (2,3):
            with self.subTest(stage=stage):
                g=Game();g.start_play();g.add_score(12000,"entry");g.weapon="lance";g.add_cut(6)
                g.enter_stage(stage);g.add_score(17000,"failed_stage");g.add_cut(11);g.weapon="axe"
                g.time=90;g.begin_boss();g.spawn("small",40,80);g.bullets=[Bullet(40,200,0,20)]
                self.last_ship(g)
                g.step(.01,Actions(title=True));self.assertTrue(g.can_continue)
                self.assertEqual(g.state,"title")
                g.step(.01,Actions(menu_pick=2))
                self.assertEqual((g.run.current_stage,g.state,g.time,g.hp,g.run.lives,g.score,g.weapon),(stage,"playing",0,3,3,12000,"lance"))
                self.assertEqual((g.current_cut,g.max_cut),(0,11))
                self.assertFalse(g.boss or g.enemies or g.bullets or g.shots or g.items.current)
                self.assertFalse(g.items.done or g.can_continue)
                self.assertEqual(g.stage_entry.score,12000)
                g.run.lives=1;g.hp=1;g.hurt();g.step(.01,Actions(confirm=True))
                self.assertEqual((g.state,g.run.current_stage,g.score),("playing",stage,12000))

    def test_new_play_discards_continue_and_resets_extends(self):
        g=Game();g.start_play(3,"stage_select");self.last_ship(g)
        self.assertTrue(g.can_continue)
        g.return_title();g.step(.01,Actions(menu_pick=1));g.step(.01,Actions(menu_pick=1))
        self.assertFalse(g.can_continue)
        self.assertEqual((g.run.current_stage,g.score,g.run.lives,g.run.next_extend),(1,0,3,30000))

class MenuAudioTests(unittest.TestCase):
    def test_title_and_ending_mml_exact_tracks_loop_and_music_switches(self):
        p=Fake();a=Audio(p);g=Game()
        for state,music in (("title",7),("mode_select",7),("playing",0),("credits",6),("title",7)):
            g.state=state;a.update(g)
            self.assertEqual(a.music_number,music)
            if music in C.UI_BGM:
                spec=C.UI_BGM[music]
                rows=[r for r in (ROOT/spec['file']).read_text(encoding='utf-8-sig').splitlines() if r.startswith('Q')]
                self.assertEqual([p.mml[i] for i in range(22,26)],rows)
                self.assertIn(('music',(music,),{'loop':True}),p.calls)
        self.assertEqual(len(p.channels),6)

    def test_hurt_wins_sfx_priority_only_on_real_hp_loss_and_briefly_ducks(self):
        p=Fake();p.channels=[SimpleNamespace(gain=.125) for _ in range(6)]
        a=Audio(p);g=Game();g.start_play(mode="stage_select");g.hurt()
        g.events+=['kill','cut','reflected_hit','boss_defeat','over']
        a.update(g)
        self.assertIn(('se',(5,5),{}),p.calls)
        self.assertLess(p.channels[0].gain,.125);self.assertGreater(p.channels[5].gain,.125)
        p.calls.clear();g.events=[];g.hurt();a.update(g)
        self.assertFalse(any(c[0]=='se' for c in p.calls))
        for _ in range(12):a.update(g)
        self.assertEqual(p.channels[0].gain,.125)
        self.assertEqual(p.channels[5].gain,.125)

    def test_ui_bank_editable_notes_and_preservation(self):
        with zipfile.ZipFile(ROOT/C.AUDIO_BANKS[4]) as z:data=tomllib.loads(z.read('pyxel_resource.toml').decode())
        self.assertEqual(len(data['sounds']),64)
        for music,spec in C.UI_BGM.items():
            rows=[r for r in (ROOT/spec['file']).read_text(encoding='utf-8-sig').splitlines() if r.startswith('Q')]
            for seq,row in zip(data['musics'][music]['seqs'],rows):
                actual=[]
                for slot in seq:
                    sound=data['sounds'][slot];attrs=[sound[k] for k in ('notes','tones','volumes','effects')]
                    actual.extend(tuple(a[i%len(a)] for a in attrs) for i in range(len(attrs[0])))
                    self.assertLessEqual(len(attrs[0]),48)
                    self.assertEqual(sound['speed'],round(1800/spec['tempo']))
                self.assertEqual(actual,convert(row))

if __name__=='__main__':unittest.main()
