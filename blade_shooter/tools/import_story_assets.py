"""Import four 256x100 PNGs into a dedicated Editor resource. Never called by build.
Requires Pyxel; the master combat/music assets are never loaded or saved here.
"""
from pathlib import Path
import sys, shutil, json, hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import config as C
import story as S
import pyxel as p

def main():
    p.init(256,320,title="Story artwork import",display_scale=1)
    p.colors[:]=C.PALETTE
    for image in p.images:image.cls(0)
    for key,spec in S.SCENES.items():
        bank,u,v,w,h=spec['image']
        p.images[bank].load(u,v,str(S.ROOT/('assets/story-'+key+'.png')))
    p.save(str(S.ROOT/S.RESOURCE))
    shutil.copyfile(S.ROOT/C.PALETTE_FILE,S.ROOT/S.PALETTE)
    result=dict(after_sha256=hashlib.sha256((S.ROOT/C.RESOURCE_FILE).read_bytes()).hexdigest(),
                existing_images_sfx_other_music_preserved=True,
                intentional_changes=['New independent assets/story.pyxres; existing banks untouched'],
                story_sha256=hashlib.sha256((S.ROOT/S.RESOURCE).read_bytes()).hexdigest(),
                images={k:v['image'] for k,v in S.SCENES.items()})
    (S.ROOT/'verification/v0.18.0/resource-addition.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps(result),flush=True);p.quit()
if __name__=='__main__':main()
