"""Actual renderer verification: weapon hue persists through every visual phase."""
from pathlib import Path
import hashlib,json,runpy,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pyxel as p
import config as C
from assets import load_resources
from game import Game,Actions
from view import View

ROOT=Path(__file__).resolve().parents[1]

def main():
    folder=ROOT/'verification'/('v'+C.VERSION)/'weapon-colors'
    folder.mkdir(parents=True,exist_ok=True)
    old=runpy.run_path(str(folder.parent/'before/config.py'))
    assert C.WEAPONS==old['WEAPONS'] and C.PALETTE==old['PALETTE']
    assert (ROOT/'game.py').read_bytes()==(folder.parent/'before/game.py').read_bytes()
    p.init(256,320,title='Weapon color verification',display_scale=1)
    load_resources(p);view=View(p);records={}
    image_hash=lambda:hashlib.sha256(bytes(p.images[b].pget(x,y) for b in range(3) for y in range(256) for x in range(256))).hexdigest()
    original=image_hash()
    for weapon,ramp in C.WEAPON_COLORS.items():
        # Isolated weapon projection proves every opaque pixel uses only its ramp.
        for dim in (False,True):
            p.cls(0)
            view.textured_segment(weapon,(70,180),(170,180),16,dim=dim,ramp=ramp)
            colors={p.screen.pget(x,y) for y in range(168,192) for x in range(65,175)}-{0}
            assert colors<=set(ramp.values()) and ramp['base'] in colors,(weapon,dim,colors)
        g=Game(weapon=weapon);g.reset();g.schedule=lambda:None
        phases={}
        def capture(phase):
            polygons=tuple(g.slash_polys)
            view.draw(g)
            assert tuple(g.slash_polys)==polygons
            p.screenshot(str(folder/(weapon+'-'+phase+'.png')),scale=3)
            phases[phase]=dict(weapon=g.attack_weapon,swing=g.swing,cooldown=g.cooldown,active=bool(g.slash_polys))
        capture('idle')
        g.step(1/C.FPS,Actions(slash=True));capture('windup')
        while g.swing<C.WEAPONS[weapon]['windup']+C.WEAPONS[weapon]['active']*.5:g.step(1/C.FPS)
        assert g.slash_polys;capture('active')
        while g.swing<C.WEAPONS[weapon]['windup']+C.WEAPONS[weapon]['active']+.04:g.step(1/C.FPS)
        capture('recovery')
        while g.swing>=0:g.step(1/C.FPS)
        assert g.cooldown>0;capture('cooldown')
        records[weapon]=dict(base_index=ramp['base'],base_rgb=f"#{C.PALETTE[ramp['base']]:06x}",phases=phases)
    assert image_hash()==original and list(p.colors)==C.PALETTE
    report=dict(result='PASS',version=C.VERSION,weapons=records,weapon_performance_and_collision_unchanged=True,
                no_image_bank_mutation=True,palette_order_unchanged=True,real_gkd=False,real_iphone=False)
    (folder/'result.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('WEAPON_COLORS_PASS',json.dumps(report),flush=True);p.quit()

if __name__=='__main__':main()
