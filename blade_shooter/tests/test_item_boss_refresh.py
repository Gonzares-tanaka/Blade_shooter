from pathlib import Path
import sys,unittest,zipfile,tomllib,runpy,itertools
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import config as C
from assets import SPRITES
from game import Game
ROOT=Path(__file__).resolve().parents[1];FOLDER=ROOT/'verification/v0.17.1'
def read(path):
    with zipfile.ZipFile(path) as z:return tomllib.loads(z.read('pyxel_resource.toml').decode())

class ItemBossRefreshTests(unittest.TestCase):
    def test_edited_master_and_all_audio_bank_images_match_exactly(self):
        self.assertEqual((ROOT/C.RESOURCE_FILE).read_bytes(),(FOLDER/'before/user-edited.pyxres').read_bytes())
        current=read(ROOT/C.RESOURCE_FILE);old=read(FOLDER/'before/published.pyxres')
        for key in ('sounds','musics','tilemaps'):self.assertEqual(current[key],old[key])
        for bank,path in C.AUDIO_BANKS.items():
            data=read(ROOT/path)
            self.assertEqual(data['images'],current['images'],bank)
        self.assertEqual(SPRITES,runpy.run_path(str(FOLDER/'before/assets.py'))['SPRITES'])
        for name in ('boss.py','items.py'):
            self.assertEqual((ROOT/name).read_bytes(),(FOLDER/'before'/name).read_bytes())

    def test_boss_hp_attacks_and_item_rules_preserved(self):
        old=runpy.run_path(str(FOLDER/'before/config.py'))
        for key in ('AREA_ITEM','BOSS_PARTS','BOSS_CYCLE_SECONDS','BOSS_OPEN_FROM','BOSS_HULL_RECT','WEAPONS','SCORING','PALETTE'):
            self.assertEqual(getattr(C,key),old[key],key)
        self.assertEqual(C.LIVES,{**old['LIVES'],'extend_points':30000})

    def test_all_six_boss_orders_keep_destroyed_parts_silent_and_remaining_parts_shooting(self):
        for order in itertools.permutations(('left','right','center')):
            g=Game('boss');g.reset();g.boss.update(C.BOSS_ENTRY_SECONDS+.01,True)
            for index,key in enumerate(order):
                part=next(p for p in g.boss.parts if p.key==key)
                g.damage_enemy(part,part.hp)
                self.assertEqual(g.boss.destroyed_order,list(order[:index+1]))
                commands=g.boss.update(C.BOSS_CYCLE_SECONDS+.01,True)
                self.assertFalse(any(p.hp<=0 for p,_,_ in commands))
                self.assertEqual({p.key for p,_,_ in commands},set(order[index+1:]))

    def test_current_player_facing_extend_text_is_updated(self):
        for name in ('README.md','web/index.html','web/play.html'):
            text=(ROOT/name).read_text(encoding='utf8')
            self.assertNotIn('10,000点ごと',text,name)
            self.assertIn('30,000点ごと',text,name)

if __name__=='__main__':unittest.main()
