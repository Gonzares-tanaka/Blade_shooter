"""描画・入力APIに依存しない共通ゲーム。斬撃ポリゴンは描画と判定で共有。"""
from dataclasses import dataclass
import math
import json
import config as C
from boss import Battleship
from items import AreaItems
from progress import RunState,Result,ScorePopup
from stages import get_stage
from cave import CaveWalls
from stage3_config import BARRIER,FINAL,ENDING
from stage2_config import ROCK,ROCK_PATTERNS,ROCK_FLOWS,MISSILE,rock_row,rock_position,steer_missile


@dataclass
class Actions:
    x: float = 0
    y: float = 0
    drag_x: float = 0
    drag_y: float = 0
    slash: bool = False
    confirm: bool = False
    pause: bool = False
    focus_lost: bool = False
    quit: bool = False
    course: bool = False
    section: int = 0
    settings: bool = False
    weapon: int = 0
    touch_mode: int = 0
    lab: int = 0  # 1=weapons, 2=free
    title: bool = False
    retry: bool = False
    next_stage: bool = False



@dataclass
class Enemy:
    uid: int
    kind: str
    x: float
    y: float
    hp: int
    age: float = 0
    settled: float = 0
    next_fire: float = 0
    flash: float = 0
    home_x: float = 0
    group: int = 0
    phase: str = "entry"
    phase_time: float = 0
    vx: float = 0
    vy: float = 0
    aim_x: float = 0
    aim_y: float = 0
    shots_fired: int = 0
    pattern: str = "line"
    contact_grace: float = 0
    visible_time: float = 0
    rock_radius: float = 0
    home_y: float = -20
    warning_duration: float = 0
    spin: float = 25

    @property
    def damageable(self):
        return self.phase!="marker" if self.kind in ("rear","asteroid") else True

    @property
    def shielded(self):return self.kind=="barrier" and self.phase!="open"

    @property
    def contact_active(self):
        return self.phase!="marker" if self.kind=="asteroid" else self.kind != "rear" or (self.phase not in ("marker","entry") and self.contact_grace<=0)

    @property
    def radius(self):
        return {"armor": C.ARMOR_RADIUS, "small": C.SMALL_RADIUS,
                "charger": C.CHARGER_RADIUS, "rear": C.REAR_RADIUS,
                "asteroid": self.rock_radius or ROCK["radius"], "missile": MISSILE["radius"],"barrier":BARRIER["radius"]}[self.kind]

    @property
    def resting(self):
        return self.kind == "armor" and self.phase == "open"

    @property
    def on_screen(self):
        return (self.radius <= self.x <= C.WIDTH-self.radius and
                C.HUD_HEIGHT+self.radius <= self.y <= C.HEIGHT-self.radius)


@dataclass
class Bullet:
    x: float
    y: float
    vx: float
    vy: float
    source: str = ""
    homing_remaining: float = 0.0
    age: float = 0.0

    reflectable: bool = False
    friendly: bool = False

    @property
    def missile(self):return self.source=="missile"

    @property
    def radius(self):return MISSILE["radius_bullet"] if self.missile else C.BULLET_RADIUS


@dataclass
class Effect:
    x: float
    y: float
    kind: str
    radius: float = 0
    age: float = 0
    enemy_kind: str = "armor"


def point_at(x, y, radius, degrees):
    angle = math.radians(degrees)
    return x+math.cos(angle)*radius, y+math.sin(angle)*radius


def segment_distance_sq(x, y, a, b):
    dx, dy = b[0]-a[0], b[1]-a[1]
    t = max(0, min(1, ((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy or 1)))
    return (x-a[0]-t*dx)**2+(y-a[1]-t*dy)**2


def polygon_hits_circle(poly, x, y, radius):
    # 凸ポリゴン内部、または辺への距離。描画で使う頂点と完全に共通。
    signs = []
    for a, b in zip(poly, poly[1:]+poly[:1]):
        signs.append((b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0]))
        if segment_distance_sq(x, y, a, b) <= radius*radius:
            return True
    return all(v >= 0 for v in signs) or all(v <= 0 for v in signs)


def blade_outline(x, y, angle, inner=C.BLADE_INNER, reach=C.BLADE_REACH, width=C.BLADE_WIDTH):
    """刃本体の4頂点。表示と掃引判定の入力を共用する。"""
    a = math.radians(angle)
    nx, ny = -math.sin(a)*width/2, math.cos(a)*width/2
    near, far = point_at(x, y, inner, angle), point_at(x, y, reach, angle)
    return ((near[0]-nx, near[1]-ny), (far[0]-nx, far[1]-ny),
            (far[0]+nx, far[1]+ny), (near[0]+nx, near[1]+ny))


def convex_hull(points):
    points = sorted(set(points))
    def cross(a, b, c):
        return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    halves = []
    for sequence in (points, points[::-1]):
        half = []
        for p in sequence:
            while len(half) >= 2 and cross(half[-2], half[-1], p) <= 0:
                half.pop()
            half.append(p)
        halves.extend(half[:-1])
    return tuple(halves)


def sweep_polygons(x, y, start, end, previous=None):
    # 回転5度・移動4px以下に細分し、移動前後の刃本体をつなぐ。
    # 自機中心や斬撃全体の扇形をまとめて保護する判定は作らない。
    px, py = previous if previous is not None else (x, y)
    n = max(1, math.ceil(abs(end-start)/5), math.ceil(math.hypot(x-px, y-py)/4))
    poses = [blade_outline(px+(x-px)*i/n, py+(y-py)*i/n, start+(end-start)*i/n)
             for i in range(n+1)]
    return [convex_hull(poses[i]+poses[i+1]) for i in range(n)]


def weapon_pose(weapon, time):
    """実体の角度・根元距離・先端距離・幅。描画と判定で共用。"""
    w=C.WEAPONS[weapon]
    wind,active=w["windup"],w["active"]
    progress=max(0,min(1,(time-wind)/active))
    angle=w["start_angle"]+(w["end_angle"]-w["start_angle"])*progress
    if weapon=="lance":
        # 自機は動かさず、先端28pxだけを突き出して戻す。柄は無判定。
        if time<wind:extension=0
        elif time<=wind+active:extension=min(1,progress/0.65)
        else:extension=max(0,1-(time-wind-active)/w["recovery"])
        far=46+(w["reach"]-46)*extension
        return -90.0,far-(w["reach"]-w["inner"]),far,w["width"]
    if time<wind:angle=w["start_angle"]-45+45*time/wind
    elif time>wind+active:angle=w["end_angle"]+45*min(1,(time-wind-active)/w["recovery"])
    return angle,w["inner"],w["reach"],w["width"]


def weapon_sweep(weapon, previous, current, before, after):
    a,b=weapon_pose(weapon,before),weapon_pose(weapon,after)
    n=max(1,math.ceil(abs(b[0]-a[0])/5),
          math.ceil((math.hypot(current[0]-previous[0],current[1]-previous[1])+abs(b[2]-a[2]))/4))
    poses=[]
    for i in range(n+1):
        t=i/n
        angle,inner,reach,width=weapon_pose(weapon,before+(after-before)*t)
        poses.append(blade_outline(previous[0]+(current[0]-previous[0])*t,
                                   previous[1]+(current[1]-previous[1])*t,angle,inner,reach,width))
    return [convex_hull(poses[i]+poses[i+1]) for i in range(n)]


def polygon_hits_motion(poly, start, end, radius):
    """同じ短い時間区間の弾移動も掃引し、高速な相対移動を取りこぼさない。"""
    if polygon_hits_circle(poly, *start, radius) or polygon_hits_circle(poly, *end, radius):
        return True
    def cross(a, b, c):
        return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    for a, b in zip(poly, poly[1:]+poly[:1]):
        if segment_distance_sq(*a, start, end) <= radius*radius:
            return True
        if (max(start[0], end[0]) >= min(a[0], b[0]) and
                max(a[0], b[0]) >= min(start[0], end[0]) and
                max(start[1], end[1]) >= min(a[1], b[1]) and
                max(a[1], b[1]) >= min(start[1], end[1]) and
                cross(start, end, a)*cross(start, end, b) <= 0 and
                cross(a, b, start)*cross(a, b, end) <= 0):
            return True
    return False


class Game:
    def __init__(self, course=C.DEFAULT_COURSE, section=0, seed=None, weapon=C.DEFAULT_WEAPON, touch_mode=C.DEFAULT_TOUCH_MODE, debug=C.DEBUG_ENABLED):
        if course not in C.COURSES:
            raise ValueError("Unknown test course: "+course)
        if weapon not in C.WEAPONS or touch_mode not in C.TOUCH_MODES:
            raise ValueError("Unknown weapon or touch mode")
        self.run=RunState(weapon=weapon)
        self.selected_weapon=weapon
        self.weapon, self.touch_mode = weapon, touch_mode
        self.best_score=0
        self.debug=debug
        self.debug_log=[]
        self.stage_definition=get_stage(C.COURSES[course].get("stage_number",1))
        self.lab_mode = "free"
        self.settings_row = 0
        self.course = course
        self.seed=C.STAGE_SEED if seed is None else seed
        self.stage_data=self.stage_definition.build(self.seed)
        self.checkpoint = section
        self.state = "title"
        self.reset()
        self.state = "title"
        self.events=[]

    def reset(self,carry_run=False):
        if not carry_run:self.run=RunState(current_stage=self.stage_definition.number,weapon=self.selected_weapon)
        self.state = "playing"
        self.checkpoint=max(0,min(self.checkpoint,len(self.course_config["sections"])-1))
        self.time = self.world_time = self.course_config["sections"][self.checkpoint][0]
        self.px, self.py = C.WIDTH/2, C.HEIGHT-54
        self.invincible = 0.0
        self.cooldown, self.swing, self.shot_clock = 0.0, -1.0, 0.0
        self.swing_weapon = self.weapon
        self.items = AreaItems(self)
        self.hitstop = self.shake = 0.0
        self.enemies, self.bullets, self.shots, self.effects = [], [], [], []
        self.slash_polys, self.slash_slices, self.slash_hits = [], [], set()
        self.events = []
        self.done = {i for i,w in enumerate(self.course_config["waves"]) if w["at"]<self.time}
        self.uid = self.slashes = self.blade_kills = self.shot_kills = self.cleared_bullets = 0
        self.rocks_destroyed=self.rocks_passed=self.rock_shot_hits=self.missiles_cut=0
        self.cave=CaveWalls() if self.run.current_stage==3 else None
        self.reflections=self.reflected_hits=0
        self.swing_hitstop = False
        self.blade_angle = -70.0
        self.blade_pivot = (self.px, self.py-4)
        self.group_id = 0
        self.blade_kills_by_kind = {kind: 0 for kind in ("armor", "small", "charger", "rear", "boss", "missile", "barrier")}
        self.shot_kills_by_kind = dict(self.blade_kills_by_kind)
        self.swing_kills = self.max_swing_kills = 0
        self.menu_direction = 0
        self.menu_vertical = 0
        self.rear_shots_fired = 0
        self.stage_complete = False
        self.pending_scene = None
        self.boss=None
        self.boss_spawned_at=None
        self.boss_engaged_at=None
        self.route_complete=False
        self.boss_pending=False
        self.cleanup_time=0.0
        self.scene_time=0.0
        self.result=None
        self.result_choice=0
        self.frame_hurt=False
        self.cut_pulse=0.0
        self.score_popups=[]
        self.score_totals={}
        self.combo_text=""
        self.combo_time=0.0
        self.boss_defeated=False
        self.debug_log=[]
        if self.course_config["next_scene"]=="boss" and self.time>=self.duration:
            self.begin_boss()

    @property
    def weapon(self):return self.run.weapon
    @weapon.setter
    def weapon(self,value):self.run.weapon=value
    @property
    def hp(self):return self.run.hp
    @hp.setter
    def hp(self,value):self.run.hp=value
    @property
    def score(self):return self.run.score
    @score.setter
    def score(self,value):self.run.score=value
    @property
    def current_cut(self):return self.run.current_cut
    @property
    def max_cut(self):return self.run.max_cut

    def enter_stage(self,number,carry_run=True):
        self.stage_definition=get_stage(number)
        self.stage_data=self.stage_definition.build(self.seed)
        self.run.current_stage=number
        self.course="stage";self.checkpoint=0
        self.reset(carry_run=carry_run)
        if carry_run:self.reset_cut("stage_change")

    @property
    def can_advance_stage(self):
        return bool(self.result and self.result.cleared and self.course in ("stage","stage2","stage3")
                    and self.stage_definition.next_stage is not None)

    @property
    def result_options(self):
        return ("NEXT STAGE", "RETRY", "TITLE") if self.can_advance_stage else ("RETRY", "TITLE")

    def choose_course(self,course):
        self.course=course
        self.stage_definition=get_stage(C.COURSES[course].get("stage_number",1))
        self.stage_data=self.stage_definition.build(self.seed)

    def log(self,event,**data):
        if not self.debug:return
        item=dict(time=round(self.time,3),event=event,**data)
        self.debug_log.append(item);self.debug_log=self.debug_log[-256:]
        print("BLADE_DEBUG "+json.dumps(item),flush=True)

    def add_score(self,amount,reason,x=None,y=None,melee=False):
        self.score+=amount
        self.score_totals[reason]=self.score_totals.get(reason,0)+amount
        if x is not None:
            self.score_popups.append(ScorePopup(x,y,amount,melee))
            self.score_popups=self.score_popups[-6:]
        self.log("score",amount=amount,total=self.score,reason=reason)

    def reset_cut(self,reason):
        if self.current_cut:self.log("cut_reset",reason=reason,previous=self.current_cut)
        self.run.current_cut=0;self.run.cut_remaining=0
        self.cut_pulse=0

    def add_cut(self,count):
        if not count:return
        self.run.current_cut+=count
        self.run.cut_remaining=C.CUT["grace_seconds"]
        self.cut_pulse=C.CUT["pulse_seconds"]
        self.log("cut",added=count,total=self.current_cut)
        if self.current_cut>self.max_cut:
            self.run.max_cut=self.current_cut
            self.log("max_cut",value=self.max_cut)

    def finish_result(self,cleared):
        if self.result is not None:return
        self.best_score=max(self.best_score,self.score)
        self.result=Result(self.run.current_stage,cleared,self.score,self.best_score,
                           self.max_cut,self.boss_defeated,self.weapon,self.time)
        self.result_choice=0;self.menu_vertical=0
        self.log("stage_end",cleared=cleared,score=self.score,max_cut=self.max_cut)

    @property
    def weapon_config(self):
        return C.WEAPONS[self.weapon]

    @property
    def attack_weapon(self):
        return self.swing_weapon if self.swing >= 0 else self.weapon

    @property
    def attack_config(self):
        return C.WEAPONS[self.attack_weapon]

    def set_lab(self, mode):
        self.lab_mode=mode
        if mode!="free":
            self.choose_course("compare")
            self.checkpoint=0

    def configure(self, action):
        if action.lab:self.set_lab(("weapons","free")[action.lab-1])
        if action.weapon:
            choices=tuple(C.WEAPONS)
            self.weapon=choices[(choices.index(self.weapon)+action.weapon)%len(choices)]
            self.selected_weapon=self.weapon
        if action.touch_mode and self.lab_mode!="weapons":
            choices=tuple(C.TOUCH_MODES)
            self.touch_mode=choices[(choices.index(self.touch_mode)+action.touch_mode)%len(choices)]

    @property
    def course_config(self):
        return self.stage_data if self.course in ("stage","stage2","stage3") else C.COURSES[self.course]

    @property
    def duration(self):
        return self.course_config["duration"]

    @property
    def player_speed(self):
        return C.PLAYER_SPEED*C.PLAYER_SPEED_PRESETS.get(self.course, C.PLAYER_SPEED_PRESETS["tempo"])

    def finish_course(self):
        """道中の出口。300秒で出現を止め、クリアにせず戦艦へ接続する。"""
        if self.course_config["next_scene"]=="boss":
            self.route_complete=True
            self.boss_pending=True
            self.events.append("route_end")
            self.log("route_end")
            return
        self.stage_complete = True
        self.pending_scene = self.course_config["next_scene"]
        self.state = "clear"
        self.events.extend(("route_end","clear"))

    def begin_boss(self):
        if self.boss is not None:return
        self.route_complete=True
        self.boss_pending=False
        self.pending_scene="boss"
        self.boss=self.stage_definition.boss_factory()
        self.boss_spawned_at=self.time
        self.events.extend(("route_end","boss_arrival"))
        self.log("boss_arrival")

    def update_transition(self,dt):
        if not self.boss_pending:return
        self.cleanup_time+=dt
        if self.cleanup_time>=C.FLOW["cleanup_max_seconds"]:
            self.enemies.clear();self.bullets.clear();self.shots.clear()
        if not self.enemies and not self.bullets:self.begin_boss()

    @property
    def targets(self):
        return self.enemies+(self.boss.parts if self.boss else [])

    def update_boss(self,dt):
        if self.boss is None or self.boss_defeated:return
        # 撤退中の道中敵・発射済み弾はそのまま更新し、なくなるまで初撃を待つ。
        ready=not self.enemies and not any(not b.source.startswith("boss:") for b in self.bullets)
        active=self.boss.active
        if hasattr(self.boss,"player_position"):self.boss.player_position=(self.px,self.py)
        for command in self.boss.update(dt,ready):
            part,speed,angles=command[:3]
            ox,oy=command[3:] if len(command)>3 else (part.x,part.y+part.radius+2)
            if self.boss.first_fire_time is None:self.boss.first_fire_time=self.time
            for degrees in angles:
                a=math.radians(degrees)
                self.bullets.append(Bullet(ox,oy,
                                           math.cos(a)*speed,math.sin(a)*speed,"boss:"+part.key,reflectable=getattr(self.boss,"reflect_only",False)))
            self.events.append("boss_fire")
        if not active and self.boss.active:
            self.boss_engaged_at=self.time
        if self.boss.warnings:self.events.append("boss_warning")

    def check_boss_defeat(self):
        if self.boss and all(p.hp<=0 for p in self.boss.parts) and not self.boss_defeated and self.state=="playing":
            self.boss_defeated=True
            score_key=getattr(self.boss,"score_key","battleship")
            self.add_score(C.SCORING["points"][score_key],score_key)
            self.stage_complete=True
            self.pending_scene=self.stage_definition.clear_target
            self.state="ending_clear" if self.stage_definition.clear_target=="ending" else "stage_clear"
            self.scene_time=0.0
            self.bullets.clear();self.shots.clear();self.enemies.clear()
            self.items.current=None
            if self.cave:self.cave.walls.clear()
            self.slash_polys=[];self.slash_slices=[]
            self.finish_result(True)
            self.events.extend(("boss_defeat","clear"))

    @property
    def section(self):
        if self.run.current_stage==3 and self.boss:
            return (self.duration,"06 / FINAL REFLECTOR","REFLECT BULLETS WITH MELEE" if self.boss.fight_time<9 else "DODGE / REFLECT / MOVE AGAIN")
        if self.boss and self.run.current_stage==2:
            return (self.duration,"07 / STEALTH CHAIN","CUT / THEN DISENGAGE" if self.boss.opening else "ALL REST / READ THE BULLETS" if self.boss.attack_state()[1]=="rest" else "DODGE / WATCH THE GLOW")
        if self.boss_pending:return (self.duration,"CORE / APPROACHING" if self.run.current_stage==3 else "07 / CLEARING THE DECK","MOVE / FINAL FIGHTER INCOMING" if self.run.current_stage==3 else "MOVE / DREADNOUGHT INCOMING")
        if self.boss:
            return (self.duration,"07 / DREADNOUGHT","OPEN / STEP IN / CUT" if self.boss.opening
                    else "CLEAR DECK / MOVE BELOW" if not self.boss.active else "DODGE / CUT A CORRIDOR")
        return next(s for s in reversed(self.course_config["sections"]) if self.time >= s[0])

    def spawn(self, kind, x, y=-20):
        self.uid += 1
        hp = {"armor": C.ARMOR_HP, "small": C.SMALL_HP,
              "charger": C.CHARGER_HP, "rear": C.REAR_HP,
              "asteroid": ROCK["hp"], "missile": MISSILE["hp"],"barrier":BARRIER["hp"]}[kind]
        enemy = Enemy(self.uid, kind, x, y, hp, home_x=x,home_y=y)
        self.enemies.append(enemy)
        return enemy

    def spawn_rear(self, x, pattern="rise"):
        enemy = self.spawn("rear", x, C.HEIGHT+16)
        enemy.pattern, enemy.phase = pattern, "marker"
        enemy.vx=C.REAR_PATTERNS[pattern]["escape_vx"]
        self.events.append("rear_warning")
        return enemy

    def spawn_formation(self, x, y=-20, pattern="line"):
        if y==-20:y=C.FORMATION_PATTERNS[pattern].get("spawn_y",y)
        self.group_id += 1
        members = []
        for dx, dy in C.FORMATION_OFFSETS:
            e = self.spawn("small", x+dx, y+dy)
            e.group = self.group_id
            e.pattern = pattern
            members.append(e)
        return members

    def start_slash(self):
        if self.cooldown > 1e-6 or self.swing >= 0:
            return False
        self.swing, self.cooldown = 0.0, self.weapon_config["cooldown"]
        self.swing_weapon = self.weapon
        self.slash_hits.clear()
        self.swing_kills = 0
        self.swing_hitstop = False
        self.slashes += 1
        self.events.append("swing")
        return True

    def damage_enemy(self, enemy, amount, blade=False, reflected=False):
        if enemy.hp<=0:return
        if (enemy.kind=="boss" and getattr(self.boss,"reflect_only",False) and not reflected) or (enemy.kind=="barrier" and enemy.shielded):
            if enemy.flash<=0:
                self.effects.append(Effect(enemy.x,enemy.y,"spark"));self.events.append("shield_block")
                enemy.flash=.10
            return
        if enemy.kind=="asteroid":
            if not blade:
                self.rock_shot_hits+=1
                if enemy.age>=enemy.next_fire:
                    enemy.next_fire=enemy.age+ROCK['shot_spark_seconds']
                    self.effects.append(Effect(enemy.x,enemy.y+enemy.radius,"spark"))
                    self.events.append("rock_ricochet")
                return
            enemy.hp=0;self.rocks_destroyed+=1
            self.effects.append(Effect(enemy.x,enemy.y,"split",enemy.radius,enemy_kind="asteroid"))
            self.events.extend(("rock_break","cut"))
            self.shake=C.SHAKE_SECONDS
            if not self.swing_hitstop:self.hitstop=C.HITSTOP_SECONDS;self.swing_hitstop=True
            self.log("rock_break",count=self.rocks_destroyed)
            return
        enemy.hp -= amount
        enemy.flash = 0.07
        if enemy.hp <= 0:
            key=("boss_stealth" if enemy.key.startswith("stealth_") else "boss_"+enemy.key) if enemy.kind=="boss" else enemy.kind
            points=C.SCORING["points"][key]*(C.SCORING["melee_multiplier"] if blade else 1)
            if points:self.add_score(points,key,enemy.x,enemy.y,blade)
            if enemy.kind=="boss":
                enemy.hp=0
                enemy.enabled=False
                enemy.phase="destroyed"
                self.boss.destroyed_order.append(enemy.key)
                self.events.append("boss_part_break")
            self.effects.append(Effect(enemy.x, enemy.y, "split" if blade else "pop", enemy.radius, enemy_kind=enemy.kind))
            self.events.append("kill")
            if blade:
                self.blade_kills += 1
                self.blade_kills_by_kind[enemy.kind] += 1
                self.swing_kills += 1
                if self.swing_kills>=2:
                    self.add_score(C.SCORING["multi_extra"],"multi_kill")
                    self.combo_text=({2:"DOUBLE",3:"TRIPLE"}.get(self.swing_kills,str(self.swing_kills)+" KILLS")+
                                     " +"+str((self.swing_kills-1)*C.SCORING["multi_extra"]))
                    self.combo_time=C.SCORING["combo_seconds"]
                self.max_swing_kills = max(self.max_swing_kills, self.swing_kills)
            else:
                self.shot_kills += 1
                self.shot_kills_by_kind[enemy.kind] += 1
        if blade:
            self.effects.append(Effect(enemy.x, enemy.y, "impact", enemy.radius))
            self.shake = C.SHAKE_SECONDS
            self.events.append("cut")
            if not self.swing_hitstop:
                self.hitstop = C.HITSTOP_SECONDS
                self.swing_hitstop = True

    def step(self, dt, action=None):
        action = action or Actions()
        self.events = []
        if self.state in ("ending_clear","credits"):
            self.scene_time+=dt
            if self.state=="ending_clear" and self.scene_time>=ENDING['clear_seconds']:
                self.state='credits';self.scene_time=0.0
            elif self.state=='credits' and self.scene_time>=(C.HEIGHT+len(ENDING['credits'])*ENDING['line_spacing'])/ENDING['scroll_speed']+ENDING['tail_seconds']:
                self.choose_course('stage');self.checkpoint=0;self.reset();self.state='title'
            return
        if self.state=="stage_clear":
            self.scene_time+=dt
            if self.scene_time>=C.FLOW["clear_banner_seconds"]:
                if self.stage_definition.clear_target=="next_stage" and self.stage_definition.next_stage is not None:
                    self.enter_stage(self.stage_definition.next_stage,carry_run=True)
                else:self.state="result"
            return
        if self.state in ("result","gameover"):
            if action.next_stage and self.can_advance_stage:
                self.enter_stage(self.stage_definition.next_stage,carry_run=True)
                self.events.append("start");return
            if action.retry:
                if self.course in ("stage","stage2","stage3"):self.checkpoint=0
                self.reset();self.events.append("start");return
            vertical=int(action.y!=0)
            if vertical and not self.menu_vertical:
                self.result_choice=(self.result_choice+(1 if action.y>0 else -1))%len(self.result_options)
            self.menu_vertical=vertical
            choice=self.result_options[self.result_choice]
            if action.title or action.settings or ((action.confirm or action.slash) and choice=="TITLE"):
                if self.course=="stage":self.choose_course("stage")
                self.reset()
                self.state="title";self.menu_direction=self.menu_vertical=0
                self.weapon=self.selected_weapon
            elif action.confirm or action.slash:
                if choice=="NEXT STAGE":self.enter_stage(self.stage_definition.next_stage,carry_run=True)
                else:
                    if self.course in ("stage","stage2","stage3"):self.checkpoint=0
                    self.reset()
                self.events.append("start")
            return
        if action.focus_lost and self.state == "playing":
            self.state = "paused"
            return
        if self.state == "settings":
            if action.focus_lost:
                self.menu_direction=self.menu_vertical=0
                return
            vertical=int(action.y!=0)
            horizontal=int(action.x!=0)
            if vertical and not self.menu_vertical:
                self.settings_row=(self.settings_row+(1 if action.y>0 else -1))%2
            delta=(1 if action.x>0 else -1) if horizontal and not self.menu_direction else 0
            self.menu_vertical,self.menu_direction=vertical,horizontal
            if delta:
                if self.settings_row==0:action.weapon=delta
                else:
                    self.set_lab("weapons" if self.lab_mode=="free" else "free")
            self.configure(action)
            if action.settings or action.confirm or action.slash:
                self.state="title"
                self.menu_direction=self.menu_vertical=0
            return
        if self.state in ("title", "clear"):
            self.configure(action)
            if action.settings:
                self.state="settings"
                self.menu_direction=self.menu_vertical=0
                return
            direction = int(action.x != 0)
            change_course = action.course or (direction and not self.menu_direction)
            self.menu_direction = direction
            if change_course:
                courses = tuple(C.COURSES)
                self.choose_course(courses[(courses.index(self.course)+1)%len(courses)])
                if self.course!="compare":self.lab_mode="free"
                self.checkpoint = 0
                self.reset()
                self.state = "title"
                self.menu_direction = direction
                return
            vertical = int(action.y != 0)
            delta=action.section or ((1 if action.y>0 else -1) if vertical and not self.menu_vertical else 0)
            self.menu_vertical=vertical
            if delta:
                self.checkpoint=(self.checkpoint+delta)%len(self.course_config["sections"])
                self.reset()
                self.state="title"
                self.menu_vertical=vertical
                return
            if action.confirm or action.slash:
                self.reset()
                self.events.append("start")
            return
        if action.pause or (action.confirm and self.state == "paused"):
            self.state = "playing" if self.state == "paused" else "paused"
            return
        if self.state == "paused":
            return
        # 結果画面へ押しっぱなしの方向を持ち越して、コースを変えない。
        self.menu_direction=int(action.x!=0)
        self.menu_vertical=int(action.y!=0)
        self.time += dt
        if self.boss is None and not self.route_complete and self.time >= self.duration-1e-7:
            self.time = self.duration
            self.finish_course()
            if self.state!="playing":return
        if self.hitstop > 0:
            self.hitstop = max(0, self.hitstop-dt)
            return
        self.world_time += dt
        self.shake = max(0, self.shake-dt)
        self.invincible = max(0, self.invincible-dt)
        self.cooldown = max(0, self.cooldown-dt)
        self.frame_hurt=False
        self.cut_pulse=max(0,self.cut_pulse-dt)
        self.combo_time=max(0,self.combo_time-dt)
        for popup in self.score_popups:popup.age+=dt
        self.score_popups=[p for p in self.score_popups if p.age<C.SCORING["popup_seconds"]]
        if not self.boss_pending and not (self.boss and not self.boss.active) and self.current_cut:
            self.run.cut_remaining=max(0,self.run.cut_remaining-dt)
            if self.run.cut_remaining<=1e-7:self.reset_cut("timeout")
        previous_pivot = (self.px, self.py-4)
        length = max(1.0, math.hypot(action.x, action.y))
        gain = self.player_speed/C.PLAYER_SPEED
        self.px = max(8, min(C.WIDTH-8, self.px+action.x/length*self.player_speed*dt+action.drag_x*gain))
        self.py = max(C.HUD_HEIGHT+8, min(C.HEIGHT-8, self.py+action.y/length*self.player_speed*dt+action.drag_y*gain))
        if self.cave and not self.route_complete:
            self.cave.update(dt);self.cave.constrain(self,(previous_pivot[0],previous_pivot[1]+4))
        self.items.update(self, dt, (previous_pivot[0], previous_pivot[1]+4))
        self.items.schedule(self)
        if action.slash:
            self.start_slash()
        # 終了するフレームも含め、振り始めから振り終わりまでは新規発射しない。
        shot_blocked = self.swing >= 0
        self.schedule()
        previous_enemies = {e.uid: (e.x, e.y) for e in self.targets}
        self.update_enemies(dt)
        self.update_transition(dt)
        # 登場で追加した部位も、このフレームの相対移動の開始点を持つ。
        for e in self.targets:previous_enemies.setdefault(e.uid,(e.x,e.y))
        self.update_boss(dt)
        self.update_blade(dt, previous_pivot, previous_enemies)
        # 停止分を溜めて連射しない。発射済みの弾はこの下で通常どおり更新する。
        self.shot_clock -= dt
        if shot_blocked:
            self.shot_clock = max(0, self.shot_clock)
        elif self.shot_clock <= 0:
            self.shot_clock += C.SHOT_INTERVAL
            self.shots.append(Bullet(self.px, self.py-10, 0, -C.SHOT_SPEED))
            self.events.append("shot")
        for shot in self.shots:
            previous_y = shot.y
            shot.y += shot.vy*dt
            # 最初に当たる敵へ一回。高速度でも線分判定で抜けない。
            for enemy in sorted(self.targets, key=lambda e: -e.y):
                ex, ey = previous_enemies[enemy.uid]
                if enemy.hp > 0 and enemy.damageable and segment_distance_sq(0, 0,
                        (shot.x-ex, previous_y-ey), (shot.x-enemy.x, shot.y-enemy.y)) <= (enemy.radius+1)**2:
                    self.damage_enemy(enemy, C.SHOT_DAMAGE)
                    shot.y = -999
                    break
        self.shots = [b for b in self.shots if b.y > C.HUD_HEIGHT-8]
        self.check_boss_defeat()
        if self.state!="playing":return
        live = []
        erased=0
        for b in self.bullets:
            previous = (b.x, b.y)
            if b.friendly:
                b.age+=dt
                if b.age>=FINAL['reflected_lifetime']:continue
                if self.boss and self.boss.parts[0].hp>0:
                    target=self.boss.parts[0]
                    angle=math.atan2(target.y-b.y,target.x-b.x)
                    b.vx,b.vy=math.cos(angle)*FINAL['reflected_speed'],math.sin(angle)*FINAL['reflected_speed']
                    b.x+=b.vx*dt;b.y+=b.vy*dt
                    ex,ey=previous_enemies.get(target.uid,(target.x,target.y))
                    if segment_distance_sq(0,0,(previous[0]-ex,previous[1]-ey),(b.x-target.x,b.y-target.y))<=(target.radius+b.radius)**2:
                        self.damage_enemy(target,FINAL['reflected_damage'],reflected=True)
                        self.reflected_hits+=1;self.events.append('reflected_hit');continue
                    live.append(b)
                continue
            if b.missile:
                steer_missile(b,self.px,self.py,dt)
                if b.age>=MISSILE["life_seconds"]:continue
            b.x += b.vx*dt
            b.y += b.vy*dt
            if self.blade_hits_motion(previous, (b.x, b.y), b.radius):
                if b.reflectable:
                    b.friendly=True;b.age=0;self.reflections+=1
                    target=self.boss.parts[0];angle=math.atan2(target.y-b.y,target.x-b.x)
                    b.vx,b.vy=math.cos(angle)*FINAL['reflected_speed'],math.sin(angle)*FINAL['reflected_speed']
                    live.append(b);erased+=1;self.events.append('reflect')
                    self.log('reflection',count=self.reflections);continue
                self.cleared_bullets += 1
                erased+=1
                if b.missile:self.missiles_cut+=1
                self.events.append("erase")
                if sum(e.kind == "spark" for e in self.effects) < 24:
                    self.effects.append(Effect(b.x, b.y, "spark"))
                continue
            # 弾と自機の両方が動く。終点だけで判定すると速い横移動で抜ける。
            if segment_distance_sq(0, 0,
                    (previous[0]-previous_pivot[0], previous[1]-previous_pivot[1]-4),
                    (b.x-self.px,b.y-self.py)) <= (C.PLAYER_HIT_RADIUS+(MISSILE["hit_radius"] if b.missile else C.BULLET_HIT_RADIUS))**2:
                self.hurt()
                continue
            if -10 < b.x < C.WIDTH+10 and C.HUD_HEIGHT-20 < b.y < C.HEIGHT+12:
                live.append(b)
        self.bullets = live
        if not self.frame_hurt:self.add_cut(erased)
        self.check_boss_defeat()
        # 突進の前後と自機移動を相対化して掃引。高速設定でも機体をすり抜けない。
        body = ((self.px-8, self.py-8), (self.px+8, self.py-8),
                (self.px+8, self.py+8), (self.px-8, self.py+8))
        for e in self.enemies:
            ex, ey = previous_enemies[e.uid]
            previous = (ex+self.px-previous_pivot[0], ey+self.py-4-previous_pivot[1])
            if e.hp > 0 and e.contact_active and polygon_hits_motion(body, previous, (e.x, e.y), e.radius):
                self.hurt()
        if self.boss and self.boss.active and not self.stage_complete:
            if getattr(self.boss,"contact_parts",False):
                for part in self.boss.parts:
                    ex,ey=previous_enemies.get(part.uid,(part.x,part.y))
                    relative=(ex+self.px-previous_pivot[0],ey+self.py-4-previous_pivot[1])
                    if part.hp>0 and polygon_hits_motion(body,relative,(part.x,part.y),part.radius):self.hurt()
            elif polygon_hits_motion(self.boss.hull,(previous_pivot[0],previous_pivot[1]+4),
                                     (self.px,self.py),8):self.hurt()
        self.rocks_passed+=sum(e.kind=="asteroid" and e.hp>0 and e.y>=C.HEIGHT+24 for e in self.enemies)
        self.enemies = [e for e in self.enemies if e.hp > 0 and -50 < e.y < C.HEIGHT+24 and -50 < e.x < C.WIDTH+50]
        for effect in self.effects:
            effect.age += dt
        self.effects = [e for e in self.effects if e.age < (0.48 if e.kind == "split" else 0.22)]

    def schedule(self):
        if self.route_complete or self.boss is not None or self.time>=self.duration:return
        for i,wave in enumerate(self.course_config["waves"]):
            if self.time < wave["at"] or i in self.done:continue
            self.done.add(i)
            kind,x,pattern=wave["kind"],wave["x"],wave["pattern"]
            if kind=="wall":self.cave.spawn(x,pattern,*wave['wall'])
            elif kind=="rock":
                rx,ry,vx,vy,radius,spin=wave['rock']
                e=self.spawn('asteroid',rx,ry);e.pattern=pattern
                e.vx,e.vy,e.rock_radius,e.spin=vx,vy,radius,spin
                e.warning_duration=ROCK['edge_warning'] if rx<0 or rx>C.WIDTH or (ry<C.HUD_HEIGHT and math.hypot(vx,vy)>=100) else 0
                e.phase='marker' if e.warning_duration else 'coast'
                e.group=i+1
            elif kind=="rock_row":
                self.group_id+=1
                for rx in rock_row(pattern):
                    e=self.spawn("asteroid",rx);e.pattern=pattern;e.group=self.group_id
            elif kind=="formation":self.spawn_formation(x,pattern=pattern)
            elif kind=="rear":self.spawn_rear(x,pattern)
            else:
                e=self.spawn(kind,x)
                e.pattern=pattern

    def update_enemies(self, dt):
        for e in self.enemies:
            if e.hp <= 0:
                continue
            e.age += dt
            e.flash = max(0, e.flash-dt)
            e.contact_grace=max(0,e.contact_grace-dt)
            if self.route_complete:
                e.phase="retreat"
                e.y-=C.BOSS_RETREAT_SPEED*dt
            elif e.kind=="asteroid":
                e.phase='marker' if e.age<e.warning_duration else 'coast'
                e.x,e.y=rock_position(e)
            elif e.kind=="missile":
                self.update_missile(e,dt)
            elif e.kind=="barrier":
                self.update_barrier(e,dt)
            elif e.kind == "rear":
                self.update_rear(e,dt)
            elif e.kind == "small":
                pattern=C.FORMATION_PATTERNS[e.pattern]
                e.y += pattern["speed"]*dt
                if e.group:
                    e.x = e.home_x+pattern["drift"]*e.age+math.sin(e.age*.8)*pattern["sway"]
                if e.on_screen:
                    e.visible_time += dt
                if pattern["shot_after"] is not None and e.next_fire == 0:
                    if (e.age >= pattern["shot_after"]-C.SMALL_WARNING_SECONDS and
                            e.phase == "entry" and e.on_screen):
                        e.phase, e.phase_time = "warning", 0
                        e.aim_x, e.aim_y = self.px, self.py
                    elif e.phase == "warning":
                        e.phase_time += dt
                        if e.phase_time >= C.SMALL_WARNING_SECONDS and e.on_screen:
                            self.fire(e, C.SMALL_BULLET_SPEED, (0,), (e.aim_x,e.aim_y))
                            e.next_fire, e.phase = 1, "coast"
            elif e.kind == "charger":
                if e.phase == "entry":
                    e.y = min(C.CHARGER_Y, e.y+C.CHARGER_ENTRY_SPEED*dt)
                    if e.y >= C.CHARGER_Y:
                        e.phase, e.phase_time = "warning", 0
                        e.aim_x, e.aim_y = self.px, self.py
                        dx,dy=e.aim_x-e.x,e.aim_y-e.y
                        if math.hypot(dx,dy)<1:dx,dy=0,1
                        length = math.hypot(dx,dy)
                        e.vx = dx/length*C.CHARGER_SPEED
                        e.vy = dy/length*C.CHARGER_SPEED
                elif e.phase == "warning":
                    e.phase_time += dt
                    if e.phase_time >= C.CHARGER_WARNING_SECONDS:
                        e.phase = "dash"
                        self.events.append("charge")
                else:
                    e.x += e.vx*dt
                    e.y += e.vy*dt
            else:
                self.update_armor(e, dt)

    def update_barrier(self,e,dt):
        if e.age>=BARRIER['lifetime']:
            e.phase='exit';e.y-=BARRIER['exit_speed']*dt;return
        if e.phase=='entry':
            e.y=min(BARRIER['y'],e.y+BARRIER['entry_speed']*dt)
            if e.y>=BARRIER['y']:e.phase='shield';e.phase_time=0
            return
        before=e.phase_time;e.phase_time+=dt
        shield=BARRIER['shield_seconds'];fade=BARRIER['fade_seconds']
        cycle=shield+fade+BARRIER['open_seconds']
        phase=e.phase_time%cycle
        old=e.phase;e.phase='shield' if phase<shield else 'fading' if phase<shield+fade else 'open'
        if old!='fading' and e.phase=='fading':
            e.aim_x,e.aim_y=self.px,self.py;self.events.append('barrier_warning')
        for turn in range(int(before//cycle),int(e.phase_time//cycle)+1):
            for at in BARRIER['fire_at']:
                if before<turn*cycle+shield+fade+at<=e.phase_time:
                    self.fire(e,BARRIER['bullet_speed'],BARRIER['angles'],(e.aim_x,e.aim_y))

    def update_missile(self,e,dt):
        if e.phase=="exit":
            e.y-=MISSILE['exit_speed']*dt;return
        e.y=min(MISSILE['stop_y'],e.y+MISSILE['entry_speed']*dt)
        if not e.on_screen:return
        e.phase_time+=dt
        if e.phase=="entry":
            e.phase="warning";e.phase_time=0;self.events.append("missile_warning")
        elif e.phase=="warning" and e.phase_time>=MISSILE['warning']:
            angle=math.atan2(self.py-e.y,self.px-e.x)
            self.bullets.append(Bullet(e.x,e.y+e.radius+4,math.cos(angle)*MISSILE['speed'],
                                       math.sin(angle)*MISSILE['speed'],"missile",MISSILE['homing_seconds']))
            e.shots_fired+=1;e.phase_time=0;e.phase="coast"
            self.events.append("missile_launch")
        elif e.phase=="coast" and e.phase_time>=MISSILE['interval']-MISSILE['warning']:
            e.phase_time=0
            if e.shots_fired>=MISSILE['volleys']:e.phase="exit"
            else:e.phase="warning";self.events.append("missile_warning")

    def update_armor(self, e, dt):
        if e.age > C.ARMOR_LIFETIME:
            e.phase = "exit"
            e.y -= C.ARMOR_EXIT_SPEED*dt
            return
        e.y = min(C.ARMOR_Y, e.y+C.ARMOR_ENTRY_SPEED*dt)
        if not e.on_screen:
            return
        e.visible_time += dt
        if e.phase == "entry":
            e.phase, e.phase_time = "warning", 0
            e.aim_x, e.aim_y = self.px, self.py
        elif e.phase == "warning":
            e.phase_time += dt
            if e.phase_time >= C.ARMOR_WARNING_SECONDS:
                e.phase, e.phase_time, e.next_fire = "fire", 0, 0
        elif e.phase == "fire":
            e.phase_time += dt
            e.next_fire -= dt
            if e.next_fire <= 1e-6:
                pattern=C.ARMOR_PATTERNS.get(e.pattern,C.ARMOR_PATTERNS["hold"])
                self.fire(e, pattern["speed"], pattern["angles"], (e.aim_x,e.aim_y))
                e.next_fire += pattern["interval"]
            if e.phase_time >= C.ARMOR_FIRE_SECONDS:
                e.phase, e.phase_time = "open", 0
        else:
            e.phase_time += dt
            if e.phase_time >= C.ARMOR_REST_SECONDS:
                e.phase, e.phase_time = "warning", 0
                e.aim_x, e.aim_y = self.px, self.py

    def update_rear(self, e, dt):
        if e.phase=="marker":
            e.phase_time+=dt
            if e.phase_time>=C.REAR_MARKER_SECONDS:
                e.phase,e.phase_time="entry",0
        elif e.phase=="entry":
            stop_y=C.REAR_PATTERNS[e.pattern]["stop_y"]
            e.y=max(stop_y,e.y-C.REAR_ENTRY_SPEED*dt)
            if e.y<=stop_y:
                e.phase,e.phase_time="warning",0
                e.contact_grace=C.REAR_CONTACT_GRACE
                self.events.append("rear_warning")
        elif e.phase == "warning":
            e.phase_time += dt
            if e.phase_time >= C.REAR_WARNING_SECONDS:
                e.phase = "fire" if C.REAR_SHOTS>0 else "exit"
                e.next_fire = 0
        elif e.phase == "fire":
            e.next_fire -= dt
            if e.next_fire <= 1e-8:
                # 画面内で停止している間だけ発射。上へ離脱中は撃たない。
                if (e.radius <= e.x <= C.WIDTH-e.radius and
                        C.HUD_HEIGHT+e.radius <= e.y <= C.HEIGHT-e.radius):
                    self.bullets.append(Bullet(e.x,e.y-e.radius-4,0,-C.REAR_BULLET_SPEED,"rear"))
                    self.rear_shots_fired += 1
                    self.events.append("rear_fire")
                e.shots_fired += 1
                e.next_fire += max(1/C.FPS,C.REAR_SHOT_INTERVAL)
                if e.shots_fired >= C.REAR_SHOTS:
                    e.phase = "exit"
        else:
            e.x += e.vx*dt
            e.y -= C.REAR_EXIT_SPEED*dt

    def fire(self, e, speed, angles, target=None):
        # 本体全体が画面内に入り、敵別の予告を終えた場合だけ呼び出す。
        if not e.on_screen:
            return
        tx,ty = target if target is not None else (self.px,self.py)
        aim = math.atan2(ty-e.y, tx-e.x)
        e.shots_fired += 1
        for offset in angles:
            a = aim+math.radians(offset)
            self.bullets.append(Bullet(e.x, e.y+e.radius, math.cos(a)*speed, math.sin(a)*speed, e.kind))

    def blade_hits_motion(self, previous, current, radius):
        for poly, t0, t1 in self.slash_slices:
            def position(t):
                return (previous[0]+(current[0]-previous[0])*t,
                        previous[1]+(current[1]-previous[1])*t)
            if polygon_hits_motion(poly, position(t0), position(t1), radius):
                return True
        return False

    def update_blade(self, dt, previous_pivot=None, previous_enemies=None):
        # 毎フレーム破棄。振り始め・振り終わり・前フレームの残像には判定なし。
        self.slash_polys, self.slash_slices = [], []
        self.blade_pivot = (self.px, self.py-4)
        if self.swing < 0:
            self.blade_angle = -70
            return
        before = self.swing
        self.swing += dt
        weapon=self.swing_weapon
        w=C.WEAPONS[weapon]
        wind, active = w["windup"], w["active"]
        def angle(t):
            return w["start_angle"]+(w["end_angle"]-w["start_angle"])*max(0, min(1, (t-wind)/active))
        if self.swing <= wind:
            self.blade_angle = weapon_pose(weapon,self.swing)[0]
        elif min(self.swing, wind+active)-max(before, wind) > 1e-9:
            self.blade_angle = angle(self.swing)
            t0, t1 = (max(before, wind)-before)/dt, (min(self.swing, wind+active)-before)/dt
            current = (self.px, self.py-4)
            previous = previous_pivot if previous_pivot is not None else current
            def pivot(t):
                return (previous[0]+(current[0]-previous[0])*t,
                        previous[1]+(current[1]-previous[1])*t)
            if weapon=="blade":
                self.slash_polys = sweep_polygons(*pivot(t1), angle(before), self.blade_angle, previous=pivot(t0))
            else:
                self.slash_polys = weapon_sweep(weapon,pivot(t0),pivot(t1),max(before,wind),min(self.swing,wind+active))
            self.blade_pivot = pivot(t1)
            n = len(self.slash_polys)
            self.slash_slices = [(poly, t0+(t1-t0)*i/n, t0+(t1-t0)*(i+1)/n)
                                 for i, poly in enumerate(self.slash_polys)]
            for e in self.targets:
                previous = (previous_enemies or {}).get(e.uid, (e.x, e.y))
                if e.hp > 0 and e.damageable and e.uid not in self.slash_hits and self.blade_hits_motion(previous, (e.x, e.y), e.radius):
                    self.slash_hits.add(e.uid)
                    self.damage_enemy(e, w["damage"], True)
        else:
            self.blade_angle = weapon_pose(weapon,self.swing)[0]
        if self.swing >= w["shot_stop"]:
            self.swing = -1

    def hurt(self):
        if self.invincible > 0 or self.state != "playing":
            return
        self.hp -= 1
        self.frame_hurt=True
        self.reset_cut("damage")
        self.invincible = C.INVINCIBLE_SECONDS
        self.events.append("hurt")
        self.effects.append(Effect(self.px, self.py, "hurt"))
        if self.hp <= 0:
            self.state = "gameover"
            self.finish_result(False)
            self.events.append("over")
