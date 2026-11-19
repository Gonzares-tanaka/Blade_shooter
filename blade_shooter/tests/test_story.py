from pathlib import Path
import json,sys,unittest,zipfile,tomllib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import config as C
import story as S
from game import Game,Actions,Bullet
from audio import Audio
from test_audio import Fake
from stage3_config import ENDING

class StoryTests(unittest.TestCase):
    def release_press(self,g,action=None):
        g.step(.01,Actions());g.step(.01,action or Actions(confirm=True))

    def test_layout_long_japanese_blank_and_manual_break_without_loss(self):
        original='星歴0149年。'+('「救出へ向かう」――。'*50)+'\n\n次の段落。'
        pages=S.paginate(original,72,3)
        self.assertGreater(len(pages),10)
        self.assertEqual(''.join(row for page in pages for row in page),original.replace('\n',''))
        self.assertTrue(any('' in page for page in pages))
        for page in pages:
            self.assertLessEqual(len(page),3)
            for row in page:self.assertLessEqual(S.text_width(row),72)
        self.assertEqual(S.paginate('第一段落\n\n第二段落\n---\n第三段落'),(('第一段落','','第二段落'),('第三段落',)))
        self.assertEqual(S.paginate(''),(('',),))
        self.assertEqual(S.paginate('一行\r\n\r\n二行'),(('一行','','二行'),))

    def test_all_initial_text_has_glyphs_and_fits_body(self):
        for key,spec in S.SCENES.items():
            text=(S.ROOT/spec['file']).read_text(encoding='utf8')
            missing=set(text+spec['title'])-set(S.glyph_widths())-set('\n-')
            self.assertFalse(missing,(key,missing))
            story=S.Story.load(key)
            for page in story.pages:
                self.assertLessEqual(len(page),S.LAYOUT['lines'])
                self.assertTrue(all(S.text_width(row)<=S.LAYOUT['width'] for row in page))
        self.assertLess(S.LAYOUT['y']+S.LAYOUT['lines']*S.LAYOUT['line_height'],S.LAYOUT['footer_y'])

    def test_campaign_intros_skip_continue_select_and_state_carry(self):
        g=Game();g.start_play();self.assertEqual((g.state,g.story.key),('story','stage1'))
        self.release_press(g,Actions(settings=True));self.assertEqual(g.state,'playing')
        g.hp=2;g.weapon='axe';g.add_score(1234,'fixture');g.add_cut(8)
        carry=(g.hp,g.weapon,g.score,g.max_cut,g.run.lives)
        for stage in (2,3):
            g.enter_stage(stage,show_intro=True)
            self.assertEqual((g.state,g.story.key),('story','stage'+str(stage)))
            self.assertEqual((g.hp,g.weapon,g.score,g.max_cut,g.run.lives),carry)
            self.release_press(g,Actions(settings=True))
            g.enter_stage(stage,show_intro=True);self.assertEqual(g.state,'playing')
            g.run.lives=1;g.hp=1;g.invincible=0;g.hurt();g.continue_play()
            self.assertEqual((g.state,g.time,g.run.current_stage),('playing',0,stage))
            g.hp=carry[0];g.weapon=carry[1];g.score=carry[2];g.run.max_cut=carry[3];g.run.lives=carry[4]
        for stage in (1,2,3):
            g.start_play(stage,'stage_select');self.assertEqual((g.state,g.time),('playing',0))

    def test_story_freezes_combat_cut_and_no_held_attack_leaks(self):
        g=Game();g.reset();g.add_cut(4);g.bullets=[Bullet(80,100,0,90)]
        before=(g.time,g.world_time,g.run.cut_remaining,g.hp,g.bullets[0].y)
        g.begin_story('stage1')
        for _ in range(120):g.step(1,Actions(confirm=True,slash=True))
        self.assertEqual(g.story.page,0)
        self.assertEqual((g.time,g.world_time,g.run.cut_remaining,g.hp,g.bullets[0].y),before)
        self.release_press(g);self.assertEqual(g.story.page,1)
        for _ in range(60):g.step(.01,Actions(confirm=True))
        self.assertEqual(g.story.page,1)
        self.release_press(g);self.release_press(g)
        self.assertEqual(g.state,'playing')
        g.schedule=lambda:None
        g.step(.01,Actions(slash=True));self.assertEqual(g.swing,-1)
        g.step(.01);g.step(.01,Actions(slash=True));self.assertGreaterEqual(g.swing,0)

    def test_ending_music_continues_through_story_credits_and_preview(self):
        g=Game();g.enter_stage(3);g.begin_boss()
        for part in g.boss.parts:g.damage_enemy(part,part.hp,reflected=True)
        g.check_boss_defeat();score=g.score
        p=Fake();audio=Audio(p);audio.update(g)
        self.assertEqual(g.state,'ending_clear')
        g.step(ENDING['clear_seconds']);audio.update(g)
        self.assertEqual((g.state,g.story.key,g.score),('story','ending',score))
        self.release_press(g,Actions(settings=True));audio.update(g)
        self.assertEqual((g.state,g.score),('credits',score))
        self.assertEqual([call[1] for call in p.calls if call[0]=='music'],[(6,)])
        g.step(200);audio.update(g);self.assertEqual(g.state,'title')
        self.assertEqual([call[1] for call in p.calls if call[0]=='music'],[(6,),(7,)])
        g.preview_story('all')
        for key in S.SCENES:
            self.assertEqual(g.story.key,key);self.release_press(g,Actions(settings=True))
        self.assertEqual(g.state,'title')

    def test_image_bank_slots_palette_and_existing_master_preserved(self):
        self.assertFalse(C.DEBUG_ATTACK_GUIDES)
        with zipfile.ZipFile(S.ROOT/S.RESOURCE) as z:d=tomllib.loads(z.read('pyxel_resource.toml').decode())
        for spec in S.SCENES.values():
            bank,u,v,w,h=spec['image'];rows=d['images'][bank]['data']
            self.assertEqual((w,h),(256,100));self.assertLessEqual(v+h,256)
            pixels=[c for row in rows[v:v+h] for c in row[u:u+w]]
            self.assertGreater(len(set(pixels)),6);self.assertLess(max(pixels),52)
        self.assertEqual((S.ROOT/S.PALETTE).read_bytes(),(S.ROOT/C.PALETTE_FILE).read_bytes())
        import hashlib
        self.assertEqual(hashlib.sha256((S.ROOT/C.RESOURCE_FILE).read_bytes()).hexdigest(),'2bf6fdaf695ddfe2e7d03d6b79a058473d8f68840b841bf1f2966fe1d6dde3d8')

if __name__=='__main__':unittest.main()
