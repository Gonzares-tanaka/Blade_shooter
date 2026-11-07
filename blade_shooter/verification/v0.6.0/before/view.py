"""画像はpyxres。軌跡・予告線・文字など動的な部分だけ図形描画。"""
import math
import config as C
from game import point_at, blade_outline
from assets import SPRITES, sprite


class View:
    def __init__(self, pyxel, profile="pc"):
        self.p, self.profile = pyxel, profile

    def center(self, y, text, color=3):
        self.p.text((C.WIDTH-len(text)*4)//2, y, text, color)

    def polygon(self, points, color):
        for i in range(1, len(points)-1):
            self.p.tri(*points[0], *points[i], *points[i+1], color)

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
        for b in g.shots:
            sprite(p,"shot",b.x,b.y)
        for e in g.enemies:
            if e.kind == "armor":
                color = 6 if e.resting else 11
                sprite(p,"armor_open" if e.resting else "armor",e.x,e.y)
                p.rect(e.x-12, e.y+e.radius+4, 24, 2, 1)
                p.rect(e.x-12, e.y+e.radius+4, 24*max(0,e.hp)/C.ARMOR_HP, 2, color)
                if C.ARMOR_Y <= e.y and e.age <= C.ARMOR_LIFETIME:
                    p.text(e.x-8 if e.resting else e.x-14, e.y-e.radius-10,
                           "OPEN" if e.resting else "FIRING", 6 if e.resting else 37)
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
            if e.flash:
                p.rectb(e.x-e.radius,e.y-e.radius,e.radius*2,e.radius*2,3)
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
        p.text(8, 4, "HULL", 2)
        for i in range(C.PLAYER_HP):
            p.rect(30+i*9, 4, 6, 7, 6 if i < g.hp else 1)
        p.text(83, 5, "BLADE" if g.cooldown <= 0 else "WAIT", 6 if g.cooldown <= 0 else 2)
        p.text(177, 5, f"{max(0, math.ceil(g.duration-g.time)):03d} SEC", 3)
        if g.state=="playing":
            section=g.section
            self.center(29,section[1],40)
            self.center(40,section[2],2)
            if not g.enemies and not g.bullets:
                self.center(54,"GET READY" if g.time<section[0]+3 else "BREATHER / REPOSITION",33)
        if g.state == "title":
            self.panel(85, 161)
            self.center(101, "B L A D E", 6)
            self.center(119, g.course_config["label"]+f" / {int(g.duration)} SEC", 40)
            self.center(141, "READ THE OPENING.", 3)
            self.center(153, "MOVE CLOSE. CUT ONCE.", 3)
            self.center(173, "LEFT/RIGHT: COURSE", 2)
            self.center(185, "UP/DOWN: START SECTION", 2)
            self.center(199, "FROM: "+g.course_config["sections"][g.checkpoint][1], 39)
            hint = "A / START: BEGIN" if self.profile == "gkd" else "ENTER / Z: BEGIN"
            self.center(222, hint, 6)
        elif g.state in ("gameover", "clear", "paused"):
            self.panel(116, 100)
            self.center(137, {"clear":"STAGE 1 / ROUTE CLEAR" if g.course=="stage" else f"SURVIVED / {int(g.duration)} SEC", "gameover":"HULL LOST", "paused":"PAUSED"}[g.state],
                        6 if g.state == "clear" else 3)
            self.center(160, "READ. APPROACH. CUT.", 2)
            hint = "START / A: RETRY" if self.profile == "gkd" else "ENTER / Z: RETRY"
            if g.state == "paused":
                hint = "START: RESUME" if self.profile == "gkd" else "P / ENTER: RESUME"
            self.center(190, hint, 6)
        if self.profile == "gkd" and g.state != "playing":
            self.center(303, "SELECT: EXIT TO PORTS", 2)

    def panel(self, y, height):
        self.p.rect(15, y, 226, height, 0)
        self.p.rectb(15, y, 226, height, 33)

    def player(self, g):
        p, x, y = self.p, g.px, g.py
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
            hand = point_at(*pivot, C.BLADE_INNER, g.blade_angle)
            tip = point_at(*pivot, C.BLADE_REACH, g.blade_angle)
            color = 3 if g.slash_polys else 33
        self.textured_segment("arm",(x+5,y-1),elbow,3)
        self.textured_segment("arm",elbow,hand,3)
        sprite(p,"joint",*elbow)
        self.textured_segment("blade",hand,tip,C.BLADE_WIDTH,dim=not bool(g.slash_polys))
        sprite(p,"joint",*hand)
        p.pset(x, y, 3)

    def effect(self, e):
        p, t = self.p, e.age
        if e.kind == "split":
            name=e.enemy_kind if e.enemy_kind in ("armor","small","charger","rear") else "armor"
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
