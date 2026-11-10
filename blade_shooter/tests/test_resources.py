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
        for i in range(19):self.assertTrue(self.data['sounds'][i]['notes'])
        palette=[int(line,16) for line in (ROOT/C.PALETTE_FILE).read_text().splitlines()]
        self.assertEqual(palette,C.PALETTE)
        self.assertEqual(len(palette),52)

    def test_bgm_leaves_sfx_channels_empty(self):
        for i in (0,1):
            music=self.data['musics'][i]['seqs']
            self.assertTrue(music[0]);self.assertTrue(music[1])
            self.assertTrue(all(not music[ch] for ch in C.AUDIO_SE_CHANNELS if ch<len(music)))
            self.assertTrue(all(sound>=32 for seq in music for sound in seq))

    def test_item_additions_preserve_every_existing_pixel_sound_and_music(self):
        with zipfile.ZipFile(ROOT/'verification/v0.12.0/before'/C.RESOURCE_FILE) as z:
            before=tomllib.loads(z.read('pyxel_resource.toml').decode())
        def pixel(bank,x,y):
            rows=bank['data'];return rows[y][x] if y<len(rows) and x<len(rows[y]) else 0
        for bank,(old,new) in enumerate(zip(before['images'],self.data['images'])):
            for y in range(256):
                for x in range(256):
                    self.assertEqual(pixel(old,x,y),pixel(new,x,y),(bank,x,y))
        for i,(old,new) in enumerate(zip(before['sounds'],self.data['sounds'])):
            if i not in range(40,52):self.assertEqual(old,new,i)
        self.assertEqual(before['tilemaps'],self.data['tilemaps'])
        self.assertEqual(before['musics'][1:],self.data['musics'][1:])
        self.assertEqual(self.data['musics'][0]['seqs'],[[40,41,42,43],[44,45,46,47],[48,49,50,51]])
        for i in range(40,52):
            sound=self.data['sounds'][i]
            self.assertEqual(len(sound['notes']),32)
            self.assertTrue(all(-1<=n<=59 for n in sound['notes']))
            self.assertEqual(sound['speed'],12)
        self.assertEqual((ROOT/C.STAGE_BGM_MML_FILE).read_bytes(),
                         (ROOT/'verification/v0.12.0/before'/C.STAGE_BGM_MML_FILE).read_bytes())


if __name__=='__main__':unittest.main()
