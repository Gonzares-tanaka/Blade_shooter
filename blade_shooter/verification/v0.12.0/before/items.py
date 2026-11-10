"""エリアごとに1個。表示中の種類を確定してから時間を進める。"""
from dataclasses import dataclass
import math
import random
import config as C


@dataclass
class AreaItem:
    area: int
    x: float
    y: float
    kind: str
    age: float = 0.0
    cycle: float = 0.0

    @property
    def exiting(self):
        return self.age >= C.AREA_ITEM["stay_seconds"]

    @property
    def warning(self):
        return (not self.exiting and self.cycle >=
                C.AREA_ITEM["switch_seconds"]-C.AREA_ITEM["warning_seconds"])


class AreaItems:
    def __init__(self, game):
        self.rng = random.Random(game.seed ^ 0x4954454D)  # 敵の乱数とは独立
        self.ends = []
        elapsed = 0.0
        if game.course in C.AREA_ITEM["courses"]:
            for part in game.course_config.get("plan", ()):
                elapsed += part["length"]
                self.ends.append(elapsed)
        self.done = {i for i, end in enumerate(self.ends) if end <= game.time}
        self.current = None
        self.history = []
        self.notice, self.notice_time = "", 0.0

    def location(self, game):
        c = C.AREA_ITEM
        # 先に自機から離れた候補だけに絞る。敵・残弾の局所的な余裕で選ぶ。
        candidates = [p for p in c["positions"]
                      if math.hypot(p[0]-game.px, p[1]-game.py) >= c["player_clearance"]]
        if not candidates:
            return None, False
        def margin(p):
            distances = [math.hypot(p[0]-e.x, p[1]-e.y)-e.radius-c["enemy_clearance"]
                         for e in game.enemies if e.hp > 0 and e.damageable]
            distances += [math.hypot(p[0]-b.x, p[1]-b.y)-c["bullet_clearance"]
                          for b in game.bullets]
            return min(distances, default=999.0)
        pos = max(candidates, key=margin)
        return pos, margin(pos) >= 0

    def schedule(self, game):
        for area, end in enumerate(self.ends):
            if area in self.done or game.time < end-1e-7:
                continue
            final = area == len(self.ends)-1
            delay = game.time-end
            if not final and delay < C.AREA_ITEM["settle_seconds"]-1e-7:
                continue
            pos, safe = self.location(game)
            if pos is None or (not safe and not final and delay < C.AREA_ITEM["max_delay"]):
                continue
            # エリア間隔は滞在＋退場より長い。設定変更時も蓄積させない。
            self.current = AreaItem(area, *pos, self.rng.choice(C.AREA_ITEM["kinds"]))
            self.done.add(area)
            self.history.append(dict(event="spawn", area=area+1, time=game.time,
                                     x=pos[0], y=pos[1], kind=self.current.kind))

    def collect(self, game):
        item = self.current
        kind = item.kind  # 取得時に再抽選しない。描画されていた種類をそのまま使う。
        before = game.weapon
        if kind == "heal":
            hp = game.hp
            game.hp = min(C.PLAYER_HP, game.hp+1)
            self.notice = "HP +1" if game.hp > hp else "HP FULL"
            game.events.append("pickup_heal")
        else:
            game.weapon = kind
            self.notice = C.WEAPONS[kind]["label"]+(" / SAME" if before == kind else " EQUIPPED")
            game.events.append("pickup_weapon")
        self.notice_time = C.AREA_ITEM["notice_seconds"]
        self.history.append(dict(event="pickup", area=item.area+1, time=game.time,
                                 kind=kind, weapon=game.weapon, hp=game.hp))
        self.current = None

    def update(self, game, dt, previous):
        self.notice_time = max(0.0, self.notice_time-dt)
        item = self.current
        if item is None:
            return
        # このstepで新たに描画する種類へ切り替える前に、前の表示との接触を確定。
        from game import segment_distance_sq
        speed = -C.AREA_ITEM["exit_speed"] if item.exiting else C.AREA_ITEM["drift_speed"]
        next_y = item.y+speed*dt
        if segment_distance_sq(0, 0, (previous[0]-item.x, previous[1]-item.y),
                               (game.px-item.x, game.py-next_y)) <= (
                                   C.AREA_ITEM["pickup_radius"]+C.PLAYER_SIZE/2)**2:
            self.collect(game)
            return
        item.y = next_y
        item.age += dt
        if item.y < C.HUD_HEIGHT-16:
            self.history.append(dict(event="exit", area=item.area+1, time=game.time, kind=item.kind))
            self.current = None
            return
        if not item.exiting:
            item.cycle += dt
            while item.cycle >= C.AREA_ITEM["switch_seconds"]-1e-9:
                item.cycle = max(0, item.cycle-C.AREA_ITEM["switch_seconds"])
                item.kind = self.rng.choice([k for k in C.AREA_ITEM["kinds"] if k != item.kind])
