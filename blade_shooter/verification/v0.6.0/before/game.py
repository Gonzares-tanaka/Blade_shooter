"""描画・入力APIに依存しない共通ゲーム。斬撃ポリゴンは描画と判定で共有。"""
from dataclasses import dataclass
import math
import config as C


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

    @property
    def damageable(self):
        return self.kind != "rear" or self.phase != "marker"

    @property
    def contact_active(self):
        return self.kind != "rear" or (self.phase not in ("marker","entry") and self.contact_grace<=0)

    @property
    def radius(self):
        return {"armor": C.ARMOR_RADIUS, "small": C.SMALL_RADIUS,
                "charger": C.CHARGER_RADIUS, "rear": C.REAR_RADIUS}[self.kind]

    @property
    def resting(self):
        return (self.kind == "armor" and self.y >= C.ARMOR_Y and
                self.settled % (C.ARMOR_FIRE_SECONDS+C.ARMOR_REST_SECONDS) >= C.ARMOR_FIRE_SECONDS)


@dataclass
class Bullet:
    x: float
    y: float
    vx: float
    vy: float
    source: str = ""


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


def blade_outline(x, y, angle):
    """刃本体の4頂点。表示と掃引判定の入力を共用する。"""
    a = math.radians(angle)
    nx, ny = -math.sin(a)*C.BLADE_WIDTH/2, math.cos(a)*C.BLADE_WIDTH/2
    near, far = point_at(x, y, C.BLADE_INNER, angle), point_at(x, y, C.BLADE_REACH, angle)
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
    def __init__(self, course=C.DEFAULT_COURSE, section=0):
        if course not in C.COURSES:
            raise ValueError("Unknown test course: "+course)
        self.course = course
        self.checkpoint = section
        self.state = "title"
        self.reset()
        self.state = "title"

    def reset(self):
        self.state = "playing"
        self.checkpoint=max(0,min(self.checkpoint,len(self.course_config["sections"])-1))
        self.time = self.world_time = self.course_config["sections"][self.checkpoint][0]
        self.px, self.py = C.WIDTH/2, C.HEIGHT-54
        self.hp, self.invincible = C.PLAYER_HP, 0.0
        self.cooldown, self.swing, self.shot_clock = 0.0, -1.0, 0.0
        self.hitstop = self.shake = 0.0
        self.enemies, self.bullets, self.shots, self.effects = [], [], [], []
        self.slash_polys, self.slash_slices, self.slash_hits = [], [], set()
        self.events = []
        self.done = {i for i,w in enumerate(self.course_config["waves"]) if w["at"]<self.time}
        self.uid = self.slashes = self.blade_kills = self.shot_kills = self.cleared_bullets = 0
        self.swing_hitstop = False
        self.blade_angle = -70.0
        self.blade_pivot = (self.px, self.py-4)
        self.group_id = 0
        self.blade_kills_by_kind = {kind: 0 for kind in ("armor", "small", "charger", "rear")}
        self.shot_kills_by_kind = dict(self.blade_kills_by_kind)
        self.swing_kills = self.max_swing_kills = 0
        self.menu_direction = 0
        self.menu_vertical = 0
        self.rear_shots_fired = 0
        self.stage_complete = False
        self.pending_scene = None

    @property
    def course_config(self):
        return C.COURSES[self.course]

    @property
    def duration(self):
        return self.course_config["duration"]

    def finish_course(self):
        """道中の出口。将来はここからボスへ接続する。現在は仮クリアを表示。"""
        self.stage_complete = True
        self.pending_scene = self.course_config["next_scene"]
        self.state = "clear"
        self.events.extend(("route_end","clear"))

    @property
    def section(self):
        return next(s for s in reversed(self.course_config["sections"]) if self.time >= s[0])

    def spawn(self, kind, x, y=-20):
        self.uid += 1
        hp = {"armor": C.ARMOR_HP, "small": C.SMALL_HP,
              "charger": C.CHARGER_HP, "rear": C.REAR_HP}[kind]
        enemy = Enemy(self.uid, kind, x, y, hp, home_x=x)
        self.enemies.append(enemy)
        return enemy

    def spawn_rear(self, x, pattern="rise"):
        enemy = self.spawn("rear", x, C.HEIGHT+16)
        enemy.pattern, enemy.phase = pattern, "marker"
        enemy.vx=C.REAR_PATTERNS[pattern]["escape_vx"]
        self.events.append("rear_warning")
        return enemy

    def spawn_formation(self, x, y=-20, pattern="line"):
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
        self.swing, self.cooldown = 0.0, C.BLADE_COOLDOWN
        self.slash_hits.clear()
        self.swing_kills = 0
        self.swing_hitstop = False
        self.slashes += 1
        self.events.append("swing")
        return True

    def damage_enemy(self, enemy, amount, blade=False):
        enemy.hp -= amount
        enemy.flash = 0.07
        if enemy.hp <= 0:
            self.effects.append(Effect(enemy.x, enemy.y, "split" if blade else "pop", enemy.radius, enemy_kind=enemy.kind))
            self.events.append("kill")
            if blade:
                self.blade_kills += 1
                self.blade_kills_by_kind[enemy.kind] += 1
                self.swing_kills += 1
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
        if action.focus_lost and self.state == "playing":
            self.state = "paused"
            return
        if self.state in ("title", "gameover", "clear"):
            direction = int(action.x != 0)
            change_course = action.course or (direction and not self.menu_direction)
            self.menu_direction = direction
            if change_course:
                courses = tuple(C.COURSES)
                self.course = courses[(courses.index(self.course)+1)%len(courses)]
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
        self.time = min(self.duration, self.time+dt)
        if self.time >= self.duration-1e-7:
            self.time = self.duration
            self.finish_course()
            return
        if self.hitstop > 0:
            self.hitstop = max(0, self.hitstop-dt)
            return
        self.world_time += dt
        self.shake = max(0, self.shake-dt)
        self.invincible = max(0, self.invincible-dt)
        self.cooldown = max(0, self.cooldown-dt)
        previous_pivot = (self.px, self.py-4)
        length = max(1.0, math.hypot(action.x, action.y))
        self.px = max(8, min(C.WIDTH-8, self.px+action.x/length*C.PLAYER_SPEED*dt+action.drag_x))
        self.py = max(C.HUD_HEIGHT+8, min(C.HEIGHT-8, self.py+action.y/length*C.PLAYER_SPEED*dt+action.drag_y))
        if action.slash:
            self.start_slash()
        # 終了するフレームも含め、振り始めから振り終わりまでは新規発射しない。
        shot_blocked = self.swing >= 0
        self.schedule()
        previous_enemies = {e.uid: (e.x, e.y) for e in self.enemies}
        self.update_enemies(dt)
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
            for enemy in sorted(self.enemies, key=lambda e: -e.y):
                ex, ey = previous_enemies[enemy.uid]
                if enemy.hp > 0 and enemy.damageable and segment_distance_sq(0, 0,
                        (shot.x-ex, previous_y-ey), (shot.x-enemy.x, shot.y-enemy.y)) <= (enemy.radius+1)**2:
                    self.damage_enemy(enemy, C.SHOT_DAMAGE)
                    shot.y = -999
                    break
        self.shots = [b for b in self.shots if b.y > C.HUD_HEIGHT-8]
        live = []
        for b in self.bullets:
            previous = (b.x, b.y)
            b.x += b.vx*dt
            b.y += b.vy*dt
            if self.blade_hits_motion(previous, (b.x, b.y), C.BULLET_RADIUS):
                self.cleared_bullets += 1
                self.events.append("erase")
                if sum(e.kind == "spark" for e in self.effects) < 24:
                    self.effects.append(Effect(b.x, b.y, "spark"))
                continue
            if segment_distance_sq(self.px, self.py, previous, (b.x, b.y)) <= (C.PLAYER_HIT_RADIUS+C.BULLET_HIT_RADIUS)**2:
                self.hurt()
                continue
            if -10 < b.x < C.WIDTH+10 and C.HUD_HEIGHT-20 < b.y < C.HEIGHT+12:
                live.append(b)
        self.bullets = live
        # 突進の前後と自機移動を相対化して掃引。高速設定でも機体をすり抜けない。
        body = ((self.px-8, self.py-8), (self.px+8, self.py-8),
                (self.px+8, self.py+8), (self.px-8, self.py+8))
        for e in self.enemies:
            ex, ey = previous_enemies[e.uid]
            previous = (ex+self.px-previous_pivot[0], ey+self.py-4-previous_pivot[1])
            if e.hp > 0 and e.contact_active and polygon_hits_motion(body, previous, (e.x, e.y), e.radius):
                self.hurt()
        self.enemies = [e for e in self.enemies if e.hp > 0 and -50 < e.y < C.HEIGHT+24 and -50 < e.x < C.WIDTH+50]
        for effect in self.effects:
            effect.age += dt
        self.effects = [e for e in self.effects if e.age < (0.48 if e.kind == "split" else 0.22)]

    def schedule(self):
        for i,wave in enumerate(self.course_config["waves"]):
            if self.time < wave["at"] or i in self.done:continue
            self.done.add(i)
            kind,x,pattern=wave["kind"],wave["x"],wave["pattern"]
            if kind=="formation":self.spawn_formation(x,pattern=pattern)
            elif kind=="rear":self.spawn_rear(x,pattern)
            else:
                e=self.spawn(kind,x)
                e.pattern=pattern

    def update_enemies(self, dt):
        for e in self.enemies:
            e.age += dt
            e.flash = max(0, e.flash-dt)
            e.contact_grace=max(0,e.contact_grace-dt)
            if e.kind == "rear":
                self.update_rear(e,dt)
            elif e.kind == "small":
                pattern=C.FORMATION_PATTERNS[e.pattern]
                e.y += pattern["speed"]*dt
                if e.group:
                    e.x = e.home_x+pattern["drift"]*e.age+math.sin(e.age*.8)*pattern["sway"]
                if pattern["shot_after"] is not None and e.age >= pattern["shot_after"] and e.next_fire == 0:
                    self.fire(e, C.SMALL_BULLET_SPEED, (0,))
                    e.next_fire = 1
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
            elif e.age > C.ARMOR_LIFETIME:
                e.y -= C.ARMOR_ENTRY_SPEED*dt
            elif e.y < C.ARMOR_Y:
                e.y = min(C.ARMOR_Y, e.y+C.ARMOR_ENTRY_SPEED*dt)
            else:
                e.settled += dt
                phase = e.settled % (C.ARMOR_FIRE_SECONDS+C.ARMOR_REST_SECONDS)
                if phase < C.ARMOR_FIRE_SECONDS:
                    e.next_fire -= dt
                    if e.next_fire <= 1e-6:
                        spread = C.ARMOR_SPREAD_DEGREES
                        self.fire(e, C.ARMOR_BULLET_SPEED, (-spread, 0, spread))
                        e.next_fire += C.ARMOR_FIRE_INTERVAL
                else:
                    e.next_fire = 0

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

    def fire(self, e, speed, angles):
        aim = math.atan2(self.py-e.y, self.px-e.x)
        for offset in angles:
            a = aim+math.radians(offset)
            self.bullets.append(Bullet(e.x, e.y+e.radius, math.cos(a)*speed, math.sin(a)*speed))

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
        wind, active = C.BLADE_WINDUP, C.BLADE_ACTIVE
        def angle(t):
            return C.BLADE_START_ANGLE+(C.BLADE_END_ANGLE-C.BLADE_START_ANGLE)*max(0, min(1, (t-wind)/active))
        if self.swing <= wind:
            self.blade_angle = -210+45*self.swing/wind
        elif min(self.swing, wind+active)-max(before, wind) > 1e-9:
            self.blade_angle = angle(self.swing)
            t0, t1 = (max(before, wind)-before)/dt, (min(self.swing, wind+active)-before)/dt
            current = (self.px, self.py-4)
            previous = previous_pivot if previous_pivot is not None else current
            def pivot(t):
                return (previous[0]+(current[0]-previous[0])*t,
                        previous[1]+(current[1]-previous[1])*t)
            self.slash_polys = sweep_polygons(*pivot(t1), angle(before), self.blade_angle, previous=pivot(t0))
            self.blade_pivot = pivot(t1)
            n = len(self.slash_polys)
            self.slash_slices = [(poly, t0+(t1-t0)*i/n, t0+(t1-t0)*(i+1)/n)
                                 for i, poly in enumerate(self.slash_polys)]
            for e in self.enemies:
                previous = (previous_enemies or {}).get(e.uid, (e.x, e.y))
                if e.hp > 0 and e.damageable and e.uid not in self.slash_hits and self.blade_hits_motion(previous, (e.x, e.y), e.radius):
                    self.slash_hits.add(e.uid)
                    self.damage_enemy(e, C.BLADE_DAMAGE, True)
        else:
            self.blade_angle = C.BLADE_END_ANGLE+45*min(1, (self.swing-wind-active)/C.BLADE_RECOVERY)
        if self.swing >= wind+active+C.BLADE_RECOVERY:
            self.swing = -1

    def hurt(self):
        if self.invincible > 0 or self.state != "playing":
            return
        self.hp -= 1
        self.invincible = C.INVINCIBLE_SECONDS
        self.events.append("hurt")
        self.effects.append(Effect(self.px, self.py, "hurt"))
        if self.hp <= 0:
            self.state = "gameover"
            self.events.append("over")
