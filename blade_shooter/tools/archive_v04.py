"""道中版へ変更する前の動作済み配布を保存。通常ビルドからは呼ばない。"""
from pathlib import Path
import shutil
root=Path(__file__).resolve().parents[1]
folder=root/'verification/v0.4.0/before-stage'
folder.mkdir(parents=True,exist_ok=True)
for name in ('dist/blade-shooter-web.zip','dist/blade-shooter-gkd.zip','config.py','game.py','main.py','view.py','README.md','VERIFICATION.md'):
    dest=folder/Path(name).name
    if not dest.exists():shutil.copy2(root/name,dest)
print('v0.4.0 snapshot saved')
