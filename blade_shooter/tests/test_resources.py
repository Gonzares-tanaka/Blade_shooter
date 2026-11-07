from pathlib import Path
import sys,zipfile,tomllib,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import config as C
from assets import SPRITES

ROOT=Path(__file__).resolve().parents[1]


class ResourceTests(unittest.TestCase):
    def setUp(self):
        with zipfile.ZipFile(ROOT/C.RESOURCE_FILE) as z:
            self.data=tomllib.loads(z.read('pyxel_resource.toml').decode())

    def test_editable_image_and_sound_slots_have_content(self):
        data=self.data['images'][0]['data']
        for name,(u,v,w,h) in SPRITES.items():
            with self.subTest(sprite=name):
                self.assertTrue(any(row[x] for row in data[v:v+h] for x in range(u,u+w) if x<len(row)))
        for i in range(17):self.assertTrue(self.data['sounds'][i]['notes'])
        palette=[int(line,16) for line in (ROOT/C.PALETTE_FILE).read_text().splitlines()]
        self.assertEqual(palette,C.PALETTE)
        self.assertEqual(len(palette),52)

    def test_bgm_leaves_sfx_channels_empty(self):
        for i in (0,1):
            music=self.data['musics'][i]['seqs']
            self.assertTrue(music[0]);self.assertTrue(music[1])
            self.assertTrue(all(not seq for seq in music[2:]))
            self.assertTrue(all(sound>=32 for seq in music for sound in seq))


if __name__=='__main__':unittest.main()
