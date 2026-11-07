from pathlib import Path
import os
import subprocess
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]


class DistributionTests(unittest.TestCase):
    def test_web_app_matches_gkd_sources(self):
        with zipfile.ZipFile(ROOT/'dist/web/blade-shooter.pyxapp') as app:
            self.assertEqual(app.read('blade-shooter/.pyxapp_startup_script'),b'main.py')
            for name in ('main.py','config.py','game.py','view.py','assets.py','audio.py','assets/blade.pyxres','assets/blade.pyxpal'):
                self.assertEqual(app.read('blade-shooter/'+name),(ROOT/name).read_bytes())
        with zipfile.ZipFile(ROOT/'dist/blade-shooter-web.zip') as web:
            for path in (ROOT/'dist/web').iterdir():
                self.assertEqual(web.read(path.name),path.read_bytes())
        with zipfile.ZipFile(ROOT/'dist/blade-shooter-gkd.zip') as gkd:
            for name in ('assets.py','audio.py','assets/blade.pyxres','assets/blade.pyxpal'):
                self.assertEqual(gkd.read('blade-shooter/'+name),(ROOT/name).read_bytes())

    @unittest.skipUnless(Path('C:/Program Files/Git/bin/bash.exe').exists(),'Windows Git Bash launcher probe')
    def test_extracted_launcher_from_other_directory_with_spaces(self):
        folder=ROOT/'verification'/'launcher probe'
        folder.mkdir(exist_ok=True)
        with zipfile.ZipFile(ROOT/'dist/blade-shooter-gkd.zip') as z:
            z.extractall(folder)
        stub=folder/'python probe.sh'
        stub.write_text('#!/bin/sh\nprintf "%s\\n" "$PWD" "$@" > "$BLADE_TEST_OUTPUT"\n',encoding='utf-8',newline='\n')
        output=folder/'args.txt'
        env=dict(os.environ,BLADE_SHOOTER_PYTHON=stub.as_posix(),BLADE_TEST_OUTPUT=output.as_posix())
        result=subprocess.run(['C:/Program Files/Git/bin/bash.exe',(folder/'blade-shooter.sh').as_posix(),
                               '--probe','value with spaces'],cwd=ROOT,env=env,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        lines=output.read_text().splitlines()
        self.assertTrue(lines[0].endswith('/launcher probe/blade-shooter'))
        self.assertEqual(lines[1:],['-u','main.py','--gkd','--probe','value with spaces'])
        text=(folder/'blade-shooter.sh').read_text()
        self.assertIn('${BLADE_SHOOTER_PYTHON:-/storage/pyxel_Python/bin/python3}',text)


if __name__=='__main__': unittest.main()
