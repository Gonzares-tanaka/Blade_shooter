"""画像はpyxres。軌跡・予告線・文字など動的な部分だけ図形描画。"""
import math
from pathlib import Path
import story as S
import config as C
from game import point_at, weapon_pose
from assets import SPRITES, sprite, CAVE_TEXTURE
from stage2_config import STEALTH
from stage3_config import CAVE,BARRIER,ENDING,FINAL

NUMBERS={"K":("101","101","110","101","101"),
         "B":("110","101","110","101","110"),
         "D":("110","101","101","101","110"),
         "G":("111","100","101","101","111"),
         "I":("111","010","010","010","111"),
         "M":("101","111","111","101","101"),
         "N":("101","111","111","111","101"),
         "O":("111","101","101","101","111"),
         "P":("110","101","110","100","100"),
         "S":("111","100","111","001","111"),
         "T":("111","010","010","010","010"),
         "U":("101","101","101","101","111"),
"C":("111","100","100","100","111"),
         "L":("100","100","100","100","111"),
         "E":("111","100","110","100","111"),
         "A":("111","101","111","101","101"),
         "R":("110","101","110","101","101"),
         "0":("111","101","101","101","111"),
         "1":("010","110","010","010","111"),
         "2":("111","001","111","100","111"),
         "3":("111","001","111","001","111"),
         "4":("101","101","111","001","001"),
         "5":("111","100","111","001","111"),
         "6":("111","100","111","101","111"),
         "7":("111","001","010","010","010"),
         "8":("111","101","111","101","111"),
         "9":("111","101","111","001","111"),
         "+":("000","010","111","010","000")}


class View:
    def __init__(self, pyxel, profile="pc"):
        self.p, self.profile = pyxel, profile
        self.story_images=False
        self.story_font=None

    def center(self, y, text, color=3):
        self.p.text((C.WIDTH-len(text)*4)//2, y, text, color)

    def polygon(self, points, color):
        for i in range(1, len(points)-1):
            self.p.tri(*points[0], *points[i], *points[i+1], color)

    def digits(self,x,y,text,color=3,scale=2.0,slot=8):
        # 桁の枠は固定。CUTの拡大も枠の中心を動かさない。
        for index,char in enumerate(str(text)):
            glyph=NUMBERS.get(char)
            if glyph:
                width,height=round(3*scale),round(5*scale)
                left=round(x+index*slot+(slot-width)/2)
                for row in range(height):
                    line=glyph[row*5//height];start=None
                    for col in range(width+1):
                        filled=col<width and line[col*3//width]=="1"
                        if filled and start is None:start=col
                        if not filled and start is not None:
                            self.p.rect(left+start,round(y)+row,col-start,1,color);start=None

    def textured_segment(self, name, a, b, width, dim=False, ramp=None):
        # リソースの画素を腕・刃の実寸へ投影。イメージバンクには書き込まない。
        u,v,w,h=SPRITES[name]
        dx,dy=b[0]-a[0],b[1]-a[1]
        length=math.hypot(dx,dy)
        if length<.01:return
        tx,ty=dx/length,dy/length
        margin=width/2+1
        for y in range(math.floor(min(a[1],b[1])-margin),math.ceil(max(a[1],b[1])+margin)):
            for x in range(math.floor(min(a[0],b[0])-margin),math.ceil(max(a[0],b[0])+margin)):
                along=(x+.5-a[0])*tx+(y+.5-a[1])*ty
                across=-(x+.5-a[0])*ty+(y+.5-a[1])*tx
                if 0<=along<length and -width/2<=across<width/2:
                    col=self.p.images[0].pget(u+min(w-1,int(along/length*w)),v+min(h-1,int((across/width+.5)*h)))
                    if col:
                        if ramp is not None:
                            # Tint only this weapon's opaque pixels. Keep Editor geometry,
                            # transparency, texture shading and the global palette intact.
                            rgb=C.PALETTE[col]
                            light=(((rgb>>16)&255)*3+((rgb>>8)&255)*6+(rgb&255))/10
                            col=ramp['shadow'] if light<115 else ramp['highlight'] if light>=210 and not dim else ramp['base']
                        elif dim:col=33
                        self.p.pset(x,y,col)

    def draw(self, g):
        p = self.p
        p.cls(0)
        wants_story=g.state=="story"
        if wants_story!=self.story_images:
            resource=S.RESOURCE if wants_story else C.RESOURCE_FILE
            p.load(str(S.ROOT/resource),exclude_tilemaps=True,exclude_sounds=True,exclude_musics=True)
            self.story_images=wants_story
        if wants_story:
            p.camera();self.story(g);return
        if g.state in ("title","mode_select","stage_select","settings") and not g.development:
            p.camera();self.menu(g);return
        shake = C.SHAKE_PIXELS*max(0, g.shake/C.SHAKE_SECONDS)
        sx = math.sin(g.world_time*173)*shake
        sy = math.cos(g.world_time*137)*shake
        p.camera(sx, sy)
        getattr(self,"background_"+g.stage_definition.background)(g)
        if g.boss:
            if g.run.current_stage==3:self.final_fighter(g)
            elif g.run.current_stage==2:self.stealth_chain(g)
            else:self.battleship(g)
        self.draw_battle(g)

    def story(self,g):
        p=self.p
        if self.story_font is None:self.story_font=p.Font(str(S.ROOT/S.FONT))
        font=self.story_font;layout=S.LAYOUT;scene=S.SCENES[g.story.key]
        bank,u,v,w,h=scene["image"]
        p.blt(0,0,bank,u,v,w,h)  # Opaque 256x100; scene persists on every page.
        p.rect(0,100,256,220,0);p.line(8,121,248,121,33)
        p.text(8,layout['title_y'],scene['title'],6,font)
        page=f"{g.story.page+1}/{len(g.story.pages)}"
        p.text(248-font.text_width(page),layout['title_y'],page,39,font)
        for i,row in enumerate(g.story.rows):
            p.text(layout['x'],layout['y']+i*layout['line_height'],row,3,font)
        x,y,w,h=layout['skip'];p.rectb(x,y,w,h,33)
        p.text(x+16,y+8,"SKIP",39)
        label="A: 次へ / B: SKIP" if self.profile=="gkd" else "タップ / Z / Enter: 次へ"
        p.text(8,layout['footer_y'],label,39,font)
        hint="SELECT: 終了" if self.profile=="gkd" else "X: SKIP"
        p.text(8,305,hint,2,font)

    def menu(self,g):
        p=self.p
        bank,u,v,w,h=C.TITLE_IMAGE
        p.blt(0,12,bank,u,v,w,h)  # Native 256x100; no cropping or aspect change.
        if g.state=="settings":
            self.center(125,"WEAPON SETUP",6)
            self.center(157,"< "+g.weapon_config["label"]+" >",3)
            self.center(192,"LEFT/RIGHT: CHANGE WEAPON",2)
            self.center(215,"LEFT HAND: DRAG TO MOVE",39)
            self.center(229,"RIGHT: H-FLICK / LANCE: V-FLICK",39)
            self.center(261,"A / B: BACK" if self.profile=="gkd" else "Z / ENTER / X: BACK",6)
        else:
            heading={"title":"","mode_select":"SELECT MODE","stage_select":"SELECT STAGE"}[g.state]
            self.center(124,heading,39)
            for i,label in enumerate(g.menu_options):
                disabled=g.state=="title" and i==1 and not g.can_continue
                color=16 if disabled else 6 if i==g.menu_choice else 3
                left=(C.WIDTH-len(label)*8)/2
                self.digits(left,148+i*26,label,color,2,8)
                if i==g.menu_choice:p.tri(left-12,150+i*26,left-12,156+i*26,left-7,153+i*26,color)
            self.center(261,"B: WEAPON SETUP" if self.profile=="gkd" else "X: WEAPON SETUP",39)
            self.center(276,"UP/DOWN + A" if self.profile=="gkd" else "UP/DOWN + Z / ENTER",2)
            self.center(291,f"BEST {g.best_score:06d} / "+g.weapon_config['label'],2)
        if self.profile=="gkd":self.center(307,"SELECT: EXIT TO PORTS",2)

    def background_star_lanes(self,g):
        p=self.p
        for i in range(55):
            x = (i*73+17) % C.WIDTH
            y = (i*47+g.world_time*(12+i%3*7)) % C.HEIGHT
            if y > C.HUD_HEIGHT:
                sprite(p,"stars",x,y)
        # 動くレーンで縦スクロールを明示。
        for x in (24, 232):
            for i in range(9):
                y = (i*44+g.world_time*30) % C.HEIGHT
                sprite(p,"lane",x,y)

    def background_asteroid_belt(self,g):
        p=self.p
        for i in range(40):
            x=(i*73+17)%C.WIDTH;y=(i*47+g.world_time*(10+i%3*6))%C.HEIGHT
            if y>C.HUD_HEIGHT:p.pset(x,y,25 if i%3 else 33)
        for i in range(8):
            x=(i*91+g.world_time*5)%C.WIDTH;y=(i*71+g.world_time*19)%C.HEIGHT
            if y>C.HUD_HEIGHT:sprite(p,"distant_rock",x,y)

    def background_lunar_cave(self,g):
        p=self.p
        # 奥の岩肌は暗色・接触輪郭なし。壁は明色の大きな多面体。
        for side in (0,1):
            for y in range(-16,C.HEIGHT+16,16):
                yy=(y+g.world_time*24)%(C.HEIGHT+32)-16
                sprite(p,'cave_tile',25 if side==0 else 231,yy)
        if g.route_complete:return
        # 基本壁も左右非対称の岩塊。判定と同じ基底の折れ線で描く。
        for side in (0,1):
            for y in range(C.HUD_HEIGHT,C.HEIGHT):
                edge=g.cave.base_edge(y,side)
                x=C.WIDTH-edge if side else 0
                p.rect(x,y,edge,1,16)
                p.pset(C.WIDTH-edge if side else edge,y,2)
        for wall in g.cave.walls:
            low=max(C.HUD_HEIGHT,math.floor(wall.y));high=min(C.HEIGHT,math.ceil(wall.y+wall.height))
            # 凹形でも扇状三角形で通路を塗り潰さない。判定と同じedgeを走査。
            for y in range(low,high):
                edge=wall.edge(y);x=C.WIDTH-edge if wall.side else 0
                p.rect(x,y,edge,1,16)
            for y in range(low,high,4):
                edge=int(min(wall.edge(y),wall.edge(min(y+3,high-1))))
                for x in range(0,edge,128):
                    width=min(128,edge-x);sx=C.WIDTH-x-width if wall.side else x
                    bank,u,v,w,h=CAVE_TEXTURE;sy=int(y-wall.y)%h
                    p.blt(sx,y,bank,u,v+sy,width,min(4,h-sy,high-y))
            points=wall.polygon[1:-1]
            for a,b in zip(points,points[1:]):p.line(*a,*b,40)
            # 大きな層・割れ目も輪郭の内側へ収める。
            for f in (.28,.52,.76):
                yy=wall.y+wall.height*f;edge=wall.edge(yy)
                if C.HUD_HEIGHT<yy<C.HEIGHT:
                    a=(edge*.22,yy-8);b=(edge*.67,yy+3)
                    if wall.side:a=(256-a[0],a[1]);b=(256-b[0],b[1])
                    p.line(*a,*b,25)
        if g.time<8:self.center(67,'BRIGHT WALLS = SOLID',40)

    def final_fighter(self,g):
        p,b=self.p,g.boss;part=b.parts[0]
        if part.hp<=0:return
        warning=b.phase in ('warning','move_warning')
        sprite(p,'final_warning' if warning and int(g.world_time*10)%2 else 'final_fighter',part.x,part.y)
        p.rect(70,57,116,3,1);p.rect(70,57,116*part.hp/part.max_hp,3,12)
        if b.phase=='move_warning':
            if C.DEBUG_ATTACK_GUIDES:
                p.line(part.x,part.y,*b.destination,10);p.circb(*b.destination,18,10)
            self.center(67,'MOVE SIGNAL / KEEP CLEAR',10)
        elif b.phase=='warning':
            if C.DEBUG_ATTACK_GUIDES:
                p.line(part.x,part.y+16,*b.aim,25);p.circb(*b.aim,7,10)
            self.center(67,'DRAW THE BULLETS FORWARD',10)
        elif b.phase=='reflect':self.center(67,'REFLECT AT THE HOLD / THEN MOVE',6)
        if not b.active:self.center(176,'FINAL / REFLECT BULLETS WITH MELEE',6)

    def stealth_chain(self,g):
        p,b=self.p,g.boss
        # 連結線は隣接する生存スロット同士だけ。撃破した位置を詰めない。
        for left,right in zip(b.parts,b.parts[1:]):
            if left.hp>0 and right.hp>0:p.line(left.x,left.y,right.x,right.y,25)
        for i,part in enumerate(b.parts):
            if part.hp<=0:continue
            warning=part.phase=="warning" or any(part is moving for moving,_ in b.motion_warnings)
            sprite(p,"stealth_warning" if warning and int(g.world_time*10)%2 else "stealth",part.x,part.y)
            p.text(part.x-2,part.y-17,str(i+1),10 if warning else 40)
            p.rect(part.x-13,part.y+12,26,2,1)
            p.rect(part.x-13,part.y+12,26*part.hp/part.max_hp,2,10 if warning else 6)
            if part.phase=='open':p.text(part.x-6,part.y+17,'CUT',6)
            if warning:p.circb(part.x,part.y,17,10)
        if C.DEBUG_ATTACK_GUIDES:
            for part,i in b.motion_warnings:
                tx,ty=b.path(b.fight_time-i*STEALTH['delay']+.8)
                ratio=min(1,32/(math.hypot(tx-part.x,ty-part.y) or 1))
                p.line(part.x,part.y,part.x+(tx-part.x)*ratio,part.y+(ty-part.y)*ratio,33)
            for part,target,motion in b.aim_marks:
                if motion=='break_warning':
                    p.line(part.x,part.y+13,target[0],target[1],25)
                    p.circb(*target,5,10)
            # 仮想先頭航跡は先頭撃破後も残り、旋回方向を予告する。
            x,y=b.path(b.fight_time+.75)
            hx,hy=b.path(b.fight_time)
            ratio=min(1,38/(math.hypot(x-hx,y-hy) or 1))
            x,y=hx+(x-hx)*ratio,hy+(y-hy)*ratio
            angle=math.atan2(y-hy,x-hx)
            p.line(hx,hy,x,y,33)
            p.line(x,y,x-math.cos(angle-.65)*7,y-math.sin(angle-.65)*7,6)
            p.line(x,y,x-math.cos(angle+.65)*7,y-math.sin(angle+.65)*7,6)
        if not b.active:self.center(181,"STEALTH CHAIN APPROACHING",10)
        elif b.opening:self.center(57,"CUT / THEN BREAK AWAY",6)
        else:
            group,state,_=b.attack_state()
            self.center(57,"ALL REST / READ THE BULLETS" if state=='rest' else ("FRONT 1-3" if group==0 else "REAR 4-6")+" / "+state.upper(),6 if state=='rest' else 10)

    def draw_battle(self,g):
        p=self.p
        for b in g.shots:
            sprite(p,"shot",b.x,b.y)
        for e in g.enemies:
            if e.kind=="asteroid":
                if e.phase=='marker':
                    x=max(10,min(C.WIDTH-10,e.x));y=max(54,min(C.HEIGHT-18,e.y))
                    angle=math.atan2(e.vy,e.vx)
                    color=10 if int(g.world_time*10)%2 else 39
                    p.circb(x,y,7,color)
                    if C.DEBUG_ATTACK_GUIDES:
                        p.line(x,y,x+math.cos(angle)*18,y+math.sin(angle)*18,color)
                        p.line(x+math.cos(angle)*18,y+math.sin(angle)*18,x+math.cos(angle-.6)*10,y+math.sin(angle-.6)*10,color)
                    continue
                sprite(p,"asteroid",e.x,e.y,rotate=e.age*e.spin+e.uid*37,scale=e.radius/12)
            elif e.kind=="missile":
                warning=e.phase=="warning"
                sprite(p,"missile_carrier",e.x,e.y)
                if warning:
                    p.circb(e.x,e.y,15,10 if int(g.world_time*12)%2 else 3)
                    p.text(e.x-14,e.y-24,"HOMING",10)
                if e.on_screen:
                    p.rect(e.x-10,e.y+15,20,2,1)
                    p.rect(e.x-10,e.y+15,20*max(0,e.hp)/18,2,6)
            elif e.kind=='barrier':
                sprite(p,'barrier',e.x,e.y)
                color=10 if e.phase=='fading' else 34
                if e.shielded:
                    if e.phase!='fading' or int(g.world_time*14)%2:
                        p.circb(e.x,e.y,18,color);p.circb(e.x,e.y,20,color)
                    p.text(e.x-12,e.y-28,'UNLOCK' if e.phase=='fading' else 'SHIELD',color)
                else:
                    p.text(e.x-8,e.y-26,'OPEN',6)
                    p.line(e.x-19,e.y-6,e.x-19,e.y+6,6);p.line(e.x+19,e.y-6,e.x+19,e.y+6,6)
                p.rect(e.x-12,e.y+24,24,2,1);p.rect(e.x-12,e.y+24,24*max(0,e.hp)/BARRIER['hp'],2,6)
            elif e.kind == "armor":
                color = 6 if e.resting else 11
                sprite(p,"armor_open" if e.resting else "armor",e.x,e.y)
                p.rect(e.x-12, e.y+e.radius+4, 24, 2, 1)
                p.rect(e.x-12, e.y+e.radius+4, 24*max(0,e.hp)/C.ARMOR_PATTERNS.get(e.pattern,{}).get("hp",C.ARMOR_HP), 2, color)
                if C.ARMOR_PATTERNS.get(e.pattern,{}).get("hp",C.ARMOR_HP)>C.ARMOR_HP:
                    # Reinforced plates distinguish the 64-HP variant; original sprites stay editable.
                    p.line(e.x-10,e.y-7,e.x+10,e.y-7,10)
                    p.line(e.x-10,e.y-5,e.x+10,e.y-5,10)
                if e.on_screen and e.age <= C.ARMOR_LIFETIME:
                    p.text(e.x-8 if e.resting else e.x-14, e.y-e.radius-10,
                           "OPEN" if e.resting else "AIM" if e.phase=="warning" else "FIRING", 6 if e.resting else 37)
                    if e.phase=="warning":
                        p.circb(e.x,e.y,e.radius+3,10 if int(g.world_time*10)%2 else 39)
                        self.aim_line(e)
                    if e.resting:
                        p.line(e.x-22, e.y-5, e.x-22, e.y+5, 6)
                        p.line(e.x+22, e.y-5, e.x+22, e.y+5, 6)
            elif e.kind=="charger":
                angle=math.degrees(math.atan2(e.vy,e.vx))+90 if e.phase!="entry" else 180
                name="charger_warning" if e.phase=="warning" else "charger_dash" if e.phase=="dash" else "charger"
                sprite(p,name,e.x,e.y,rotate=angle)
                if e.phase=="warning":
                    if C.DEBUG_ATTACK_GUIDES:
                        length=math.hypot(e.vx,e.vy) or 1
                        ux,uy=e.vx/length,e.vy/length
                        for distance in range(20,300,12):
                            p.line(e.x+ux*distance,e.y+uy*distance,e.x+ux*(distance+5),e.y+uy*(distance+5),10)
                        p.circb(e.aim_x,e.aim_y,6,10)
                    p.text(e.x-12,e.y-23,"LOCKED",37)
            elif e.kind=="rear":
                if e.phase=="marker":
                    col=10 if int(g.world_time*8)%2==0 else 39
                    p.rectb(e.x-18,C.HEIGHT-15,36,14,col)
                    p.tri(e.x,C.HEIGHT-18,e.x-5,C.HEIGHT-11,e.x+5,C.HEIGHT-11,col)
                    p.text(e.x-10,C.HEIGHT-25,"BELOW",col)
                    p.rect(e.x-16,C.HEIGHT-4,32*min(1,e.phase_time/C.REAR_MARKER_SECONDS),2,col)
                    continue
                warning = e.phase in ("warning","fire")
                name = "rear_warning" if warning and int(g.world_time*8)%2==0 else "rear"
                sprite(p,name,e.x,e.y)
                if e.phase=="entry" or e.contact_grace>0:
                    p.circb(e.x,e.y,15,33 if int(g.world_time*12)%2 else 39)
                if warning:
                    if C.DEBUG_ATTACK_GUIDES:
                        for y in range(C.HUD_HEIGHT+32,int(e.y-18),12):
                            p.line(e.x,y,e.x,y+4,10 if e.phase=="warning" else 39)
                    p.text(e.x-14,e.y+16,"UP SHOT",39)
                elif e.phase=="exit":
                    p.text(e.x-12,e.y+16,"ESCAPE",39)
            else:
                sprite(p,"small",e.x,e.y)
                if e.phase=="warning":
                    p.circb(e.x,e.y,e.radius+3,10)
                    self.aim_line(e)
            if e.flash:
                p.rectb(e.x-e.radius,e.y-e.radius,e.radius*2,e.radius*2,3)
        if g.items.current:
            self.area_item(g.items.current)
        for popup in g.score_popups:
            text="+"+str(popup.points);x=max(8,min(C.WIDTH-len(text)*6-8,popup.x-len(text)*3))
            if popup.melee:self.digits(x,popup.y-16-popup.age*20,text,6,1.4)
            else:p.text(x,popup.y-16-popup.age*20,text,2)
        if g.combo_time>0:self.center(54,g.combo_text,6)
        if g.items.notice_time>0:self.center(65,g.items.notice,6)
        # アイテムの枠や下地で敵弾を隠さない。
        for b in g.bullets:
            if b.friendly:
                sprite(p,'reflected',b.x,b.y);p.line(b.x,b.y,b.x-b.vx*.025,b.y-b.vy*.025,6)
            elif b.reflectable:sprite(p,'reflect_bullet',b.x,b.y)
            elif b.missile:
                sprite(p,"homing_missile",b.x,b.y,rotate=math.degrees(math.atan2(b.vy,b.vx))+90)
                if b.homing_remaining>0:p.circb(b.x,b.y,6,10)
            else:sprite(p,"bullet",b.x,b.y)
        for effect in g.effects:
            self.effect(effect)
        # 攻撃中は毎フレーム掃いた領域だけを描く。ヒットストップ中も同じ領域を保持。
        for poly in g.slash_polys:
            self.polygon(poly, C.WEAPON_COLORS[g.attack_weapon]['highlight'])
        if g.hp > 0:
            self.player(g)
        p.camera()
        p.rect(0, 0, C.WIDTH, C.HUD_HEIGHT, 0)
        p.line(0, C.HUD_HEIGHT-1, C.WIDTH, C.HUD_HEIGHT-1, 25)
        p.text(6, 4, "SCORE", 2)
        columns=C.HUD["score_columns"]
        score=f"{g.score:0{columns}d}"
        if len(score)>columns:score="9"*(columns-1)+"+"
        self.digits(30,2,score,3)
        p.text(191,4,"CUT",6)
        cut=f"{g.current_cut:02d}".rjust(C.HUD["cut_columns"])
        if len(cut)>C.HUD["cut_columns"]:cut="9"*(C.HUD["cut_columns"]-1)+"+"
        self.digits(203,1,cut,6,2.0+0.25*g.cut_pulse/C.CUT["pulse_seconds"],slot=9)
        p.text(6,15,"HP",2)
        for i in range(C.PLAYER_HP):
            p.rect(20+i*8,14,5,6,6 if i<g.hp else 1)
        p.text(54,15,g.weapon_config["label"],C.WEAPON_COLORS[g.weapon]['base'])
        if g.cooldown>0:p.text(81,15,"WAIT",2)
        p.text(112,15,"LIFE",2)
        p.text(132,15,f"{g.run.lives:02d}",6)
        p.text(156,15,"ST"+str(g.run.current_stage),39)
        seconds=max(0,int(g.time))
        p.text(201, 15, f"{seconds//60:02d}:{seconds%60:02d}" if g.course in ("stage","stage2","stage3","boss","stealth","final")
               else f"{max(0, math.ceil(g.duration-g.time)):03d} SEC", 3)
        if g.state=="playing" and g.life_notice_time:
            self.center(68,g.life_notice,10)
        if g.state=="playing":
            section=g.section
            self.center(29,section[1],40)
            self.center(40,section[2],2)
            if not g.enemies and not g.bullets and not g.boss and not g.combo_time:
                self.center(54,"READ THE EDGE / CHANGE YOUR ROUTE" if g.cave and g.cave.walls else "GET READY" if g.time<section[0]+3 else "BREATHER / REPOSITION",33)
        if g.state == "title":
            self.panel(78, 202)
            self.center(91, "B L A D E", 6)
            self.center(108, g.course_config["label"], 40)
            self.center(120,f"{int(g.duration)//60}:{int(g.duration)%60:02d} + BOSS" if g.course in ("stage","stage2","stage3") else "3 TARGETS / ANY ORDER" if g.course=="boss"
                        else f"{int(g.duration)} SEC / FIXED WAVES",39)
            self.center(140,"WEAPON: "+g.weapon_config["label"],6)
            self.center(152,"LEFT: DRAG / RIGHT: "+("V-FLICK" if g.weapon=="lance" else "H-FLICK"),39)
            self.center(164,"LAB: "+g.lab_mode.upper(),2)
            if g.course=="stage":self.center(175,"AREA END: HEART / WEAPON PICKUP",39)
            self.center(184,"B: SETUP" if self.profile=="gkd" else "X: SETUP",6)
            self.center(198,"LEFT/RIGHT: COURSE",2)
            self.center(210,"UP/DOWN: START SECTION",2)
            self.center(225,"FROM: "+g.course_config["sections"][g.checkpoint][1],39)
            hint="A / START: BEGIN" if self.profile=="gkd" else "ENTER / Z: BEGIN"
            self.center(247,hint,6)
            if g.course=="compare":self.center(262,"SAME WAVES / THREE WEAPONS",2)
            else:self.center(268,f"BEST {g.best_score:06d}",2)
        elif g.state == "settings":
            self.panel(78, 202)
            self.center(93,"PRE-FLIGHT SETUP",6)
            rows=("WEAPON: "+g.weapon_config["label"], "COMPARE: "+g.lab_mode.upper())
            for i,text in enumerate(rows):
                self.center(125+i*25,("> " if i==g.settings_row else "  ")+text,6 if i==g.settings_row else 2)
            self.center(207,"UP/DOWN: ROW  LEFT/RIGHT: VALUE",2)
            self.center(223,"LEFT HAND: DRAG TO MOVE",39)
            self.center(235,"RIGHT: H-FLICK / LANCE: V-FLICK",39)
            self.center(257,"A / START / B: BACK" if self.profile=="gkd" else "Z / ENTER / X: BACK",6)
        elif g.state=='ending_clear':
            p.rect(0,C.HUD_HEIGHT,C.WIDTH,C.HEIGHT,0)
            self.digits(83,102,'CLEAR',6,3,18)
            self.center(139,'SCORE',2)
            self.digits((C.WIDTH-len(str(g.score).zfill(6))*12)/2,159,str(g.score).zfill(6),3,3,12)
            self.center(202,'ALL THREE STAGES COMPLETE',40)
            self.center(224,'MAX CUT '+str(g.max_cut),6)
        elif g.state=='credits':
            p.rect(0,C.HUD_HEIGHT,C.WIDTH,C.HEIGHT,0)
            for i,line in enumerate(ENDING['credits']):
                y=C.HEIGHT+i*ENDING['line_spacing']-g.scene_time*ENDING['scroll_speed']
                if C.HUD_HEIGHT+8<y<C.HEIGHT-8:self.center(y,line,6 if i%3==0 else 3)
        elif g.state=="stage_clear":
            self.panel(115,92)
            self.center(139,"STAGE "+str(g.run.current_stage)+" CLEAR",6)
            self.center(161,"FINAL FIGHTER DOWN" if g.run.current_stage==3 else "STEALTH CHAIN DOWN" if g.run.current_stage==2 else "DREADNOUGHT SUNK",3)
            self.center(182,f"SCORE {g.score:06d}",39)
        elif g.state in ("result","gameover"):
            self.panel(72,213)
            self.center(87,"STAGE "+str(g.run.current_stage)+" RESULT" if g.state=="result" else "GAME OVER",6)
            for y,label,value in ((111,"SCORE",g.score),(131,"BEST",g.best_score),(151,"MAX CUT",g.max_cut)):
                p.text(37,y,label,2)
                self.digits(139,y-1,f"{value:06d}",3)
            self.center(173,"BOSS: "+("DEFEATED" if g.boss_defeated else "NOT DEFEATED"),39)
            self.center(187,"WEAPON: "+g.weapon_config["label"],6)
            self.center(201,f"TIME {seconds//60:02d}:{seconds%60:02d}",2)
            for i,option in enumerate(g.result_options):
                self.center(219+i*15,("> " if g.result_choice==i else "  ")+option,6 if g.result_choice==i else 2)
            confirm_hint="A/START" if self.profile=="gkd" else "Z/ENTER"
            self.center(269,confirm_hint if g.state=="result" else "UP/DOWN + "+confirm_hint,39)
            if getattr(g,"save_failed",False):self.center(294,"BEST: THIS SESSION ONLY",2)
        elif g.state in ("clear", "paused"):
            self.panel(116, 100)
            self.center(137, {"clear":"DREADNOUGHT SUNK" if g.boss else f"SURVIVED / {int(g.duration)} SEC", "gameover":"HULL LOST", "paused":"PAUSED"}[g.state],
                        6 if g.state == "clear" else 3)
            self.center(160, g.weapon_config["label"]+" / "+C.TOUCH_MODES[g.touch_mode], 2)
            if g.state!="paused":self.center(176,"B: SETUP" if self.profile=="gkd" else "X: SETUP",39)
            hint = "START / A: RETRY" if self.profile == "gkd" else "ENTER / Z: RETRY"
            if g.state == "paused":
                hint = "START: RESUME" if self.profile == "gkd" else "P / ENTER: RESUME"
            self.center(190, hint, 6)
        if self.profile == "gkd" and g.state != "playing":
            self.center(303, "SELECT: EXIT TO PORTS", 2)

    def panel(self, y, height):
        self.p.rect(15, y, 226, height, 0)
        self.p.rectb(15, y, 226, height, 33)

    def area_item(self,item):
        p = self.p
        blink = item.warning and int(item.cycle/C.AREA_ITEM["blink_seconds"])%2 == 0
        color = 3 if blink else 2 if item.exiting else 39
        p.rect(item.x-12,item.y-12,24,24,0)
        p.rectb(item.x-12,item.y-12,24,24,color)
        # アイコンは点滅させず、取得する絵柄を常に読めるよう枠だけ点滅。
        sprite(p,"item_"+item.kind,item.x,item.y)
        label = "HP" if item.kind=="heal" else C.WEAPONS[item.kind]["label"]
        p.text(item.x-len(label)*2,item.y-21,label,color)
        if not item.exiting:
            p.rect(item.x-11,item.y+15,22,2,1)
            p.rect(item.x-11,item.y+15,22*(1-item.cycle/C.AREA_ITEM["switch_seconds"]),2,color)
        else:p.text(item.x-8,item.y+15,"EXIT",2)

    def battleship(self,g):
        p,b=self.p,g.boss
        sprite(p,"boss_hull",128,b.y+52)
        for part in b.parts:
            destroyed=part.hp<=0
            sprite(p,"boss_destroyed" if destroyed else "boss_"+part.key,part.x,part.y)
            color=1 if destroyed else 10 if part.phase=="warning" else 37 if part.phase=="fire" else 6
            p.text(part.x-6,part.y-24,{"left":"L","right":"R","center":"MAIN"}[part.key],color)
            p.rect(part.x-16,part.y+part.radius+5,32,3,1)
            p.rect(part.x-16,part.y+part.radius+5,32*max(0,part.hp)/part.max_hp,3,color)
            if part.phase=="warning":
                p.circb(part.x,part.y,part.radius+3+(int(g.world_time*12)%2)*2,10)
                if part.key=="center" and C.DEBUG_ATTACK_GUIDES:
                    for y in range(int(part.y+22),C.HEIGHT,14):
                        p.line(part.x,y,part.x,y+5,10)
            if destroyed:p.text(part.x-8,part.y+22,"DOWN",2)
        if not b.active:
            self.center(180,"DREADNOUGHT APPROACHING",10)
            self.center(192,"CLEAR DECK / MOVE BELOW",39)
        elif b.opening:
            self.center(78,"OPEN / STEP IN",6)

    def aim_line(self, e):
        if not C.DEBUG_ATTACK_GUIDES:return
        dx,dy=e.aim_x-e.x,e.aim_y-e.y
        length=math.hypot(dx,dy) or 1
        for d in range(int(e.radius+7), min(150,int(length)), 14):
            self.p.line(e.x+dx/length*d,e.y+dy/length*d,
                        e.x+dx/length*(d+4),e.y+dy/length*(d+4),10)

    def player(self, g):
        p, x, y = self.p, g.px, g.py
        weapon,w = g.attack_weapon,g.attack_config
        visible = g.invincible <= 0 or int(g.world_time*20)%2 == 0
        if visible:
            sprite(p,"player",x,y)
            sprite(p,"engine",x,y+10,scale=.7+int(g.world_time*20)%2*.15)
        pivot = g.blade_pivot if g.slash_polys else (x, y-4)
        if g.swing < 0:
            # 待機姿勢: 右腕に折りたたんだ刃。攻撃判定なし。
            elbow, hand = (x+10, y), (x+12, y-6)
            tip = (x+16, y-25)
            color = 6 if g.cooldown <= 0 else 1
        else:
            elbow = point_at(*pivot, 8, g.blade_angle-24)
            pose_time=min(g.swing,w["windup"]+w["active"]) if g.slash_polys else g.swing
            angle,inner,reach,width=weapon_pose(weapon,pose_time)
            hand = point_at(*pivot, inner, angle)
            tip = point_at(*pivot, reach, angle)
            color = 3 if g.slash_polys else 33
        self.textured_segment("arm",(x+5,y-1),elbow,3)
        self.textured_segment("arm",elbow,hand,3)
        sprite(p,"joint",*elbow)
        if weapon!="blade":
            # 柄は装飾。アックスの刃/ランスの穂先だけが実体ポリゴンに一致。
            self.textured_segment("arm",elbow,hand,2,ramp=C.WEAPON_COLORS[weapon])
        width=w["width"] if g.swing>=0 else min(7,w["width"])
        self.textured_segment(weapon,hand,tip,width,dim=not bool(g.slash_polys),ramp=C.WEAPON_COLORS[weapon])
        sprite(p,"joint",*hand)
        p.pset(x, y, 3)

    def effect(self, e):
        p, t = self.p, e.age
        if e.kind == "split":
            name="boss_destroyed" if e.enemy_kind=="boss" else "missile_carrier" if e.enemy_kind=="missile" else e.enemy_kind
            u,v,w,h=SPRITES[name]
            for side in (-1, 1):
                x, y = e.x+side*t*68, e.y+t*24
                p.blt(x-w/2 if side<0 else x,y-h/2,0,u if side<0 else u+w//2,v,w//2,h,0)
            sprite(p,"split",e.x,e.y,scale=1+t*3)
        elif e.kind == "impact":
            sprite(p,"impact",e.x,e.y,scale=1+t*3)
            for i in range(8):
                a, b = point_at(e.x, e.y, 5+t*130, i*45+15), point_at(e.x, e.y, 12+t*180, i*45+15)
                p.line(*a, *b, 3 if t < 0.08 else 10)
        elif e.kind == "spark":
            sprite(p,"spark",e.x,e.y,scale=1+t*3)
        else:
            sprite(p,"hurt" if e.kind=="hurt" else "pop",e.x,e.y,scale=1+t*3)
