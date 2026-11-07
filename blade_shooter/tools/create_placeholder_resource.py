"""初期仮素材を一度だけ作成。ゲーム・ビルドから呼ばず、既存原本には書かない。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config as C
import pyxel as p

root=Path(__file__).resolve().parents[1]
target=root/C.RESOURCE_FILE
if target.exists():
    raise SystemExit("Resource already exists. Edit in Pyxel Editor; will not overwrite it.")
p.init(256,256,title="Initial resource creation")
p.colors[:]=C.PALETTE
im=p.images[0]
im.cls(0)
im.tri(8,0,0,15,15,15,33);im.tri(8,1,4,13,11,13,6)
im.rect(7,3,3,6,40);im.line(2,12,5,10,3);im.line(13,12,11,10,3)
im.rect(16,0,8,4,33);im.line(16,1,23,1,40)
im.rect(32,0,30,4,6);im.rect(32,1,30,2,3)
im.tri(64,2,79,2,72,15,13);im.line(67,4,76,4,35);im.rect(71,7,2,3,3)
im.rect(81,0,2,8,40);im.circ(91.5,3.5,3,12);im.circ(91.5,3.5,1,3)
im.circ(97.5,1.5,1.5,40)
im.tri(104,0,111,0,108,7,10);im.tri(106,0,109,0,108,4,3)
for x,y,col in ((129,2,25),(138,12,1),(142,6,25)):im.pset(x,y,col)
im.line(147,0,147,10,25)
for ox,color in ((0,11),(32,6)):
    im.tri(ox+16,32,ox+1,39,ox+1,56,color);im.tri(ox+16,32,ox+1,56,ox+16,63,color)
    im.tri(ox+16,32,ox+30,39,ox+30,56,color);im.tri(ox+16,32,ox+30,56,ox+16,63,color)
    im.rect(ox+12,42,8,12,25);im.line(ox+16,35,ox+16,60,51 if ox else 10)
    im.line(ox+5,43,ox+10,38,40);im.line(ox+22,38,ox+27,43,40)
for ox,color in ((64,10),(88,37),(112,11)):
    im.tri(ox+12,32,ox+3,48,ox+12,55,color);im.tri(ox+12,32,ox+21,48,ox+12,55,color)
    im.tri(ox+12,35,ox+8,47,ox+16,47,3)
    im.line(ox+5,49,ox+8,45,10);im.line(ox+19,49,ox+16,45,10)
for x in range(16):
    im.pset(x,87,3);im.pset(7,80+x,3)
    if 3<=x<=12:im.pset(x,80+x,10);im.pset(15-x,80+x,10)
im.line(16,83,23,83,6);im.line(19,80,19,87,3)
im.circb(31,87,6,10);im.circb(31,87,3,37)
im.circb(47,87,7,37);im.line(42,82,52,92,3);im.line(52,82,42,92,3)
im.line(56,93,71,81,3);im.line(56,94,71,82,6)
sounds=(("c4","p","2","f",2),("g3e3c2","n","642","f",2),
        ("c2g1c1c0","n","7762","f",3),("c4g4","t","32","f",2),
        ("c2g1c1","n","653","f",4),("c1g0","n","75","f",7),
        ("c3e3g3c4","t","3454","n",7),("c3e3g3c4e4","t","44554","n",9),
        ("g2e2c2","p","654","f",9),("g2c3g3","p","344","s",3))
for i,args in enumerate(sounds):p.sounds[i].set(*args)
p.sounds[32].set("c3 r e3 g3 r e3 d3 r c3 r g2 r c3 e3 g3 r","t","2","n",14)
p.sounds[33].set("f3 r a3 g3 r e3 d3 r e3 g3 c4 r g3 e3 d3 r","t","2","n",14)
p.sounds[34].set("c2 r c2 r g1 r g1 r a1 r a1 r g1 r g1 r","p","1","n",14)
p.sounds[35].set("f1 r f1 r g1 r g1 r c2 r c2 r g1 r g1 r","p","1","n",14)
p.musics[0].set([32,33],[34,35],[],[])
p.save(str(target))
(root/C.PALETTE_FILE).write_text(''.join(f'{color:06X}\n' for color in C.PALETTE),encoding='ascii')
print("Created",target)
p.quit()
