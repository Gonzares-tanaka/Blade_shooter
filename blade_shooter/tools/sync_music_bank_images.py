"""音符バンク内の画像だけを、ユーザー編集済み原本へ同期する。"""
from pathlib import Path
import sys,json,hashlib
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parent)]
import pyxel as p
import config as C
from convert_stage_bgm import read
ROOT=Path(__file__).resolve().parents[1]
def main():
 folder=ROOT/'verification/v0.16.2';master=ROOT/C.RESOURCE_FILE;user=folder/'before/user-edited.pyxres';published=folder/'before/published.pyxres'
 assert master.read_bytes()==user.read_bytes(),'Keep the user edited original unchanged'
 p.init(256,320,title='Synchronizing refreshed enemy atlas');p.colors[:]=C.PALETTE;p.load(str(master))
 images=[]
 for src in p.images:
  copy=p.Image(256,256);copy.blt(0,0,src,0,0,256,256);images.append(copy)
 master_data=read(master);records={}
 for bank,path in C.AUDIO_BANKS.items():
  target=ROOT/path;backup=folder/'before'/target.name
  assert target.read_bytes()==backup.read_bytes(),'Never overwrite a changed music bank'
  before=read(target);p.load(str(target))
  for i,src in enumerate(images):p.images[i].blt(0,0,src,0,0,256,256)
  temp=folder/('synced-'+str(bank)+'.pyxres');p.save(temp.as_posix());after=read(temp)
  assert after['images']==master_data['images']
  for key in ('sounds','musics','tilemaps'):assert before[key]==after[key],(path,key)
  target.write_bytes(temp.read_bytes());temp.unlink()
  records[path]=hashlib.sha256(target.read_bytes()).hexdigest()
 old=read(published)
 for key in ('sounds','musics','tilemaps'):assert old[key]==master_data[key],key
 assert master.read_bytes()==user.read_bytes()
 result=dict(before_sha256=hashlib.sha256(published.read_bytes()).hexdigest(),after_sha256=hashlib.sha256(master.read_bytes()).hexdigest(),
  base_resource_is_user_edited_original=True,existing_images_sfx_other_music_preserved=True,
  all_sounds_music_tilemaps_preserved=True,updated_sprites=['missile_carrier','homing_missile','stealth','stealth_warning','barrier','final_fighter','final_warning'],
  missile_crop_before=[224,64,8,16],missile_crop_after=[225,64,8,16],bank_sha256=records)
 (folder/'resource-addition.json').write_text(json.dumps(result,indent=2),encoding='utf8')
 print('ENEMY_ATLAS_SYNC_PASS',json.dumps(result),flush=True);p.quit()
if __name__=='__main__':main()
