"""Render every story page in the actual native Pyxel renderer."""
from pathlib import Path
import sys,json,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import config as C, story as S
from game import Game
from view import View
from assets import load_resources
import pyxel as p

def main():
    folder=S.ROOT/'verification'/('v'+C.VERSION)/'story-native';folder.mkdir(parents=True,exist_ok=True)
    p.init(256,320,title="Story layout verification",display_scale=1)
    load_resources(p);g=Game();view=View(p)
    original=hashlib.sha256(bytes(p.images[0].pget(x,y) for y in range(256) for x in range(256))).hexdigest()
    results={}
    for key,spec in S.SCENES.items():
        g.preview_story(key);results[key]=dict(pages=len(g.story.pages),widths=[])
        for i,page in enumerate(g.story.pages):
            g.story.page=i;view.draw(g)
            assert all(view.story_font.text_width(row)==S.text_width(row)<=S.LAYOUT['width'] for row in page)
            assert all(p.screen.pget(x,y)==p.images[spec['image'][0]].pget(spec['image'][1]+x,spec['image'][2]+y) for y in range(100) for x in range(256))
            results[key]['widths'].append(max(map(S.text_width,page)))
            p.screenshot(str(folder/(key+'-'+str(i+1)+'.png')),scale=3)
        assert list(p.colors)==C.PALETTE
    g.state='title';view.draw(g)
    restored=hashlib.sha256(bytes(p.images[0].pget(x,y) for y in range(256) for x in range(256))).hexdigest()
    assert restored==original
    view.profile='gkd';g.preview_story('stage1');view.draw(g)
    p.screenshot(str(folder/'gkd-page1.png'),scale=3)
    g.reset();e=g.spawn('armor',128,110);e.phase='warning';e.aim_x=128;e.aim_y=266
    C.DEBUG_ATTACK_GUIDES=False;view.draw(g)
    off=bytes(p.screen.pget(x,y) for y in range(320) for x in range(256))
    p.screenshot(str(folder/'guides-off.png'),scale=3)
    C.DEBUG_ATTACK_GUIDES=True;view.draw(g)
    on=bytes(p.screen.pget(x,y) for y in range(320) for x in range(256))
    assert off!=on
    p.screenshot(str(folder/'guides-dev-only.png'),scale=3)
    C.DEBUG_ATTACK_GUIDES=False
    report=dict(result='PASS',version=C.VERSION,scenes=results,native_font_matches_layout=True,
                palette_order_preserved=True,combat_images_restored=True,gkd_instruction_layout_rendered=True,guides_developer_only=True,real_gkd=False,real_iphone=False)
    (folder/'result.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report),flush=True);p.quit()
if __name__=='__main__':main()
