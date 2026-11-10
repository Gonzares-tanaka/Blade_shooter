"""画像はpyxres。軌跡・予告線・文字など動的な部分だけ図形描画。"""
import math
import config as C
from game import point_at, weapon_pose
from assets import SPRITES, sprite

NUMBERS={"0":("111","101","101","101","111"),
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

    def textured_segment(self, name, a, b, width, dim=False):
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
                    if col:self.p.pset(x,y,33 if dim else col)

    def draw(self, g):
        p = self.p
        p.cls(0)
        shake = C.SHAKE_PIXELS*max(0, g.shake/C.SHAKE_SECONDS)
        sx = math.sin(g.world_time*173)*shake
        sy = math.cos(g.world_time*137)*shake
        p.camera(sx, sy)
        getattr(self,"background_"+g.stage_definition.background)(g)
        if g.boss:self.battleship(g)
        self.draw_battle(g)

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

    def draw_battle(self,g):
        p=self.p
        for b in g.shots:
            sprite(p,"shot",b.x,b.y)
        for e in g.enemies:
            if e.kind == "armor":
                color = 6 if e.resting else 11
                sprite(p,"armor_open" if e.resting else "armor",e.x,e.y)
                p.rect(e.x-12, e.y+e.radius+4, 24, 2, 1)
                p.rect(e.x-12, e.y+e.radius+4, 24*max(0,e.hp)/C.ARMOR_HP, 2, color)
                if e.on_screen and e.age <= C.ARMOR_LIFETIME:
                    p.text(e.x-8 if e.resting else e.x-14, e.y-e.radius-10,
                           "OPEN" if e.resting else "AIM" if e.phase=="warning" else "FIRING", 6 if e.resting else 37)
                    if e.phase=="warning":
                        self.aim_line(e)
                    if e.resting:
                        p.line(e.x-22, e.y-5, e.x-22, e.y+5, 6)
                        p.line(e.x+22, e.y-5, e.x+22, e.y+5, 6)
            elif e.kind=="charger":
                angle=math.degrees(math.atan2(e.vy,e.vx))+90 if e.phase!="entry" else 180
                name="charger_warning" if e.phase=="warning" else "charger_dash" if e.phase=="dash" else "charger"
                sprite(p,name,e.x,e.y,rotate=angle)
                if e.phase=="warning":
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
            sprite(p,"bullet",b.x,b.y)
        for effect in g.effects:
            self.effect(effect)
        # 攻撃中は毎フレーム掃いた領域だけを描く。ヒットストップ中も同じ領域を保持。
        for poly in g.slash_polys:
            self.polygon(poly, 51)
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
        p.text(54,15,g.weapon_config["label"],6)
        if g.cooldown>0:p.text(81,15,"WAIT",2)
        p.text(117,15,"ST"+str(g.run.current_stage),39)
        seconds=max(0,int(g.time))
        p.text(201, 15, f"{seconds//60:02d}:{seconds%60:02d}" if g.course in ("stage","boss")
               else f"{max(0, math.ceil(g.duration-g.time)):03d} SEC", 3)
        if g.state=="playing":
            section=g.section
            self.center(29,section[1],40)
            self.center(40,section[2],2)
            if not g.enemies and not g.bullets and not g.boss and not g.combo_time:
                self.center(54,"GET READY" if g.time<section[0]+3 else "BREATHER / REPOSITION",33)
        if g.state == "title":
            self.panel(78, 202)
            self.center(91, "B L A D E", 6)
            self.center(108, g.course_config["label"], 40)
            self.center(120,"5 MIN + BOSS" if g.course=="stage" else "3 TARGETS / ANY ORDER" if g.course=="boss"
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
        elif g.state=="stage_clear":
            self.panel(115,92)
            self.center(139,"STAGE 1 CLEAR",6)
            self.center(161,"DREADNOUGHT SUNK",3)
            self.center(182,f"SCORE {g.score:06d}",39)
        elif g.state in ("result","gameover"):
            self.panel(72,213)
            self.center(87,"STAGE 1 RESULT" if g.state=="result" else "GAME OVER",6)
            for y,label,value in ((111,"SCORE",g.score),(131,"BEST",g.best_score),(151,"MAX CUT",g.max_cut)):
                p.text(37,y,label,2)
                self.digits(139,y-1,f"{value:06d}",3)
            self.center(173,"BOSS: "+("DEFEATED" if g.boss_defeated else "NOT DEFEATED"),39)
            self.center(187,"WEAPON: "+g.weapon_config["label"],6)
            self.center(201,f"TIME {seconds//60:02d}:{seconds%60:02d}",2)
            self.center(226,("> " if g.result_choice==0 else "  ")+"RETRY",6 if g.result_choice==0 else 2)
            self.center(244,("> " if g.result_choice==1 else "  ")+"TITLE",6 if g.result_choice==1 else 2)
            self.center(269,"UP/DOWN + A/START" if self.profile=="gkd" else "UP/DOWN + Z/ENTER",39)
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
                if part.key=="center":
                    for y in range(int(part.y+22),C.HEIGHT,14):
                        p.line(part.x,y,part.x,y+5,10)
            if destroyed:p.text(part.x-8,part.y+22,"DOWN",2)
        if not b.active:
            self.center(180,"DREADNOUGHT APPROACHING",10)
            self.center(192,"CLEAR DECK / MOVE BELOW",39)
        elif b.opening:
            self.center(78,"OPEN / STEP IN",6)

    def aim_line(self, e):
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
            self.textured_segment("arm",elbow,hand,2)
        width=w["width"] if g.swing>=0 else min(7,w["width"])
        self.textured_segment(weapon,hand,tip,width,dim=not bool(g.slash_polys))
        sprite(p,"joint",*hand)
        p.pset(x, y, 3)

    def effect(self, e):
        p, t = self.p, e.age
        if e.kind == "split":
            name="boss_destroyed" if e.enemy_kind=="boss" else e.enemy_kind
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
