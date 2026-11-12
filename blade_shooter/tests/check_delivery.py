"""最終配布物と編集原本・説明書の一致を記録する。"""
from pathlib import Path
import hashlib,json,zipfile,runpy
ROOT=Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(ROOT))
import config as C
from build import SOURCES,RESOURCES

folder=ROOT/'verification'/('v'+C.VERSION)
sha=lambda data:hashlib.sha256(data).hexdigest()
folder.mkdir(exist_ok=True)
addition=json.loads((folder/'resource-addition.json').read_text())
assert sha((ROOT/C.RESOURCE_FILE).read_bytes())==addition['after_sha256']
assert (ROOT/C.PALETTE_FILE).read_bytes()==(ROOT/'verification/v0.3.0/before-rear/blade.pyxpal').read_bytes()
with zipfile.ZipFile(ROOT/'dist/blade-shooter-gkd.zip') as gkd,zipfile.ZipFile(ROOT/'dist/web/blade-shooter.pyxapp') as web:
    for name in (*SOURCES,*RESOURCES):
        assert gkd.read('blade-shooter/'+name)==web.read('blade-shooter/'+name)==(ROOT/name).read_bytes(),name
    assert gkd.read('blade-shooter.sh')==(ROOT/'blade-shooter.sh').read_bytes()
    assert gkd.read('blade-shooter/README.txt')==(ROOT/'README.md').read_bytes()
    assert gkd.read('blade-shooter/VERIFICATION.md')==(ROOT/'VERIFICATION.md').read_bytes()
# 前版と比較。戦闘の核・武器の全性能・素材・出現表を保持。
old=runpy.run_path(str(folder/'before/config.py'))
prefixes=('SHOT_','BLADE_','HITSTOP_','BULLET_')
preserved=[key for key in old if key.startswith(prefixes)]
preserved+=['PLAYER_HP','PLAYER_HIT_RADIUS','INVINCIBLE_SECONDS','SMALL_HP','ARMOR_HP','REAR_HP']
assert all(old[key]==getattr(C,key) for key in preserved)
for course in ('classic','rear','tempo','tempo_fast'):
    assert old['COURSES'][course]['waves']==C.COURSES[course]['waves']
assert old['COURSES']['stage']['waves']==C.COURSES['stage']['waves']
assert old['COURSES']['stage']['duration']==C.COURSES['stage']['duration']
for weapon,settings in old['WEAPONS'].items():
    for key,value in settings.items():
        assert C.WEAPONS[weapon][key]==value,(weapon,key)
assert C.WEAPONS['lance']['width']==C.PLAYER_SIZE==16
assert tuple(C.TOUCH_MODES)==('flick',)
# 既存画像・音の保持はtest_resourcesと素材ハッシュで検証。
assets_preserved=addition.get('existing_images_sfx_other_music_preserved',
                              addition.get('all_prior_pixels_sounds_music_and_tilemaps_preserved',False))
assert assets_preserved
gestures=(ROOT/'web/gestures.js').read_text(encoding='utf-8-sig')
assert not any(old_mode in gestures for old_mode in ('lastTap','double_tap','tap_flick','setMode'))
changes={k:dict(before=v,after=getattr(C,k)) for k,v in old.items()
         if k.isupper() and isinstance(v,(int,float)) and hasattr(C,k) and v!=getattr(C,k)}
result=dict(version=C.VERSION,resource_sha256=addition['after_sha256'],
            core_combat_hp_and_reference_wave_tables_preserved=True,
            existing_resources_preserved=assets_preserved,
            tuning_changes=changes,
            sources_resources_and_documents_match=True,packages={})
for name in ('blade-shooter-web.zip','blade-shooter-gkd.zip'):
    file=ROOT/'dist'/name
    result['packages'][name]=dict(bytes=file.stat().st_size,sha256=sha(file.read_bytes()))
(folder/'delivery.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
