"""調整箇所。時間=秒、距離=ゲーム内px、速度=px/秒。変更後build.pyで配布版更新。"""
from stage2_config import MISSILE,STEALTH

TITLE, VERSION = "BLADE / CLOSE QUARTERS", "0.15.0"
WIDTH, HEIGHT, HUD_HEIGHT, FPS = 256, 320, 24, 60
PLAYER_SIZE, PLAYER_HIT_RADIUS = 16, 2.0
PLAYER_SPEED, PLAYER_HP, INVINCIBLE_SECONDS = 125.0, 3, 1.2
PLAYER_SPEED_PRESETS = {"tempo": 1.3, "tempo_fast": 1.5}
SHOT_INTERVAL, SHOT_SPEED, SHOT_DAMAGE = 0.14, 300.0, 1
SCORING = dict(points=dict(small=100, charger=200, rear=250, armor=500,
                          boss_left=3000, boss_right=3000, boss_center=5000, battleship=10000, missile=MISSILE["points"],
                          boss_stealth=STEALTH["part_points"], stealth_group=STEALTH["defeat_points"]),
               melee_multiplier=2, multi_extra=200, popup_seconds=0.65, combo_seconds=0.7)
CUT = dict(grace_seconds=1.5, pulse_seconds=0.18)
FLOW = dict(cleanup_max_seconds=2.0, clear_banner_seconds=1.8)
HUD = dict(score_columns=6, cut_columns=4)
BEST_SCORE_KEY = "blade-shooter.best.v1"
DEBUG_ENABLED = False
# 武器の唯一の調整表。距離=ゲームpx、角度=右0/上-90、時間=秒。
# cooldownは攻撃入力が受理された時点から。shot_stopは3フェーズの合計で自動算出。
# 攻撃/弾消しはactiveのみ。near〜reachの実体だけを掃引し、柄と残像は無判定。
WEAPONS = {
    "blade": dict(label="BLADE", damage=40, reach=60.0, inner=30.0, width=4.0,
                  windup=0.07, active=0.10, recovery=0.24, cooldown=1.0,
                  start_angle=-165.0, end_angle=-15.0),
    "axe": dict(label="AXE", damage=80, reach=44.0, inner=30.0, width=14.0,
                windup=0.035, active=0.12, recovery=0.50, cooldown=1.20,
                start_angle=-145.0, end_angle=-35.0),
    "lance": dict(label="LANCE", damage=32, reach=94.0, inner=66.0, width=16.0,
                  windup=0.055, active=0.16, recovery=0.20, cooldown=0.82,
                  start_angle=-90.0, end_angle=-90.0),
}
for _weapon in WEAPONS.values():
    _weapon["shot_stop"] = _weapon["windup"]+_weapon["active"]+_weapon["recovery"]
# 従来のブレイド参照APIを維持。値は上の表から導出する。
BLADE_REACH, BLADE_INNER, BLADE_WIDTH = (WEAPONS["blade"][k] for k in ("reach","inner","width"))
BLADE_DAMAGE, BLADE_COOLDOWN = (WEAPONS["blade"][k] for k in ("damage","cooldown"))
BLADE_WINDUP, BLADE_ACTIVE, BLADE_RECOVERY = (WEAPONS["blade"][k] for k in ("windup","active","recovery"))
BLADE_START_ANGLE, BLADE_END_ANGLE = (WEAPONS["blade"][k] for k in ("start_angle","end_angle"))
TOUCH_MODES = {"flick": "FLICK"}
DEFAULT_WEAPON, DEFAULT_TOUCH_MODE = "blade", "flick"
# エリア報酬の唯一の調整表。時間=秒、位置/距離=ゲームpx、速度=px/秒。
# stageのplanの各lengthの累積時刻に1個。比較コースの固定条件は変えない。
AREA_ITEM = dict(
    courses=("stage","stage2"), kinds=("heal", "blade", "axe", "lance"),
    positions=((64.0, 200.0), (192.0, 200.0), (128.0, 176.0),
               (48.0, 248.0), (208.0, 248.0)),
    player_clearance=64.0, enemy_clearance=30.0, bullet_clearance=24.0,
    settle_seconds=0.5, max_delay=2.0,
    switch_seconds=0.8, warning_seconds=0.16, blink_seconds=0.05,
    stay_seconds=8.0, drift_speed=4.0, exit_speed=96.0,
    pickup_radius=10.0, notice_seconds=1.25,
)
HITSTOP_SECONDS, SHAKE_SECONDS, SHAKE_PIXELS = 0.05, 0.16, 1.5
SMALL_HP, SMALL_RADIUS, SMALL_SPEED = 2, 8.0, 72.0
ARMOR_HP, ARMOR_RADIUS = 32, 15.0
ARMOR_ENTRY_SPEED, ARMOR_Y, ARMOR_LIFETIME = 150.0, 132.0, 6.4
ARMOR_EXIT_SPEED, ARMOR_WARNING_SECONDS = 180.0, 0.55
ARMOR_FIRE_SECONDS, ARMOR_REST_SECONDS = 0.65, 1.9
ARMOR_FIRE_INTERVAL, ARMOR_SPREAD_DEGREES = 0.45, 22.0
ARMOR_BULLET_SPEED, SMALL_BULLET_SPEED = 100.0, 110.0
BULLET_RADIUS, BULLET_HIT_RADIUS = 3.0, 2.0
FULLSCREEN, SOUND_ENABLED = False, True
# 1面MMLの3声（主旋律・伴奏・ドラム）とSEを独立。音声のみ5chへ拡張。
AUDIO_BGM_CHANNELS, AUDIO_SE_CHANNELS = (0, 1, 2), (3, 4)
STAGE_BGM_MML_FILE = "assets/stage1_MML.txt"
BOSS_BGM_MML_FILE = "assets/stage1_boss.txt"
STAGE_BGM_MODE = "resource"  # Editor音符を優先。元のMML完全再生は"mml"で選べる。
STAGE_BGM_SOUNDS = (40, 41, 42, 43)
STAGE_BGM_AUDIBLE_TRACKS = (0, 1, 3)  # 3行目は休符のみ。原文は全4行保持。
# 小型編隊の中心と、中心からの相対配置。個々の機体HP・速度はSMALL_*。
FORMATION_OFFSETS = ((-22, 0), (0, -6), (22, 0))
FORMATION_SWAY = 5.0
SMALL_FIRST_SHOT, SMALL_WARNING_SECONDS = 1.75, 0.35
# 予告開始時点で進路を固定。突進中も追尾しない。
CHARGER_HP, CHARGER_RADIUS = 18, 11.0
CHARGER_ENTRY_SPEED, CHARGER_Y = 170.0, 100.0
CHARGER_WARNING_SECONDS, CHARGER_SPEED = 0.75, 225.0
# 後方出現敵。下端マーカー→入場→停止予告→上向き射撃→上へ離脱。
REAR_HP, REAR_RADIUS = 12, 10.0
REAR_MARKER_SECONDS, REAR_ENTRY_SPEED = 0.65, 120.0
REAR_STOP_Y, REAR_EXIT_SPEED = 288.0, 96.0
REAR_CONTACT_GRACE = 0.35
REAR_WARNING_SECONDS = 0.6
REAR_BULLET_SPEED, REAR_SHOT_INTERVAL, REAR_SHOTS = 92.0, 0.38, 2
# 出現表のpattern欄から選ぶ。小型は先手撃破可能、残した機体だけ狙い弾を撃つ。
FORMATION_PATTERNS = {
    "line": dict(speed=SMALL_SPEED, sway=FORMATION_SWAY, drift=0, shot_after=SMALL_FIRST_SHOT),
    "parade": dict(speed=64.0, sway=2.0, drift=0, shot_after=None),
    "diagonal_l": dict(speed=76.0, sway=3.0, drift=20, shot_after=1.6),
    "diagonal_r": dict(speed=76.0, sway=3.0, drift=-20, shot_after=1.6),
    "side_l": dict(speed=48.0, sway=2.0, drift=82, shot_after=1.45, spawn_y=56),
    "side_r": dict(speed=48.0, sway=2.0, drift=-82, shot_after=1.45, spawn_y=56),
}
ARMOR_PATTERNS = {
    "hold": dict(angles=(-ARMOR_SPREAD_DEGREES,0,ARMOR_SPREAD_DEGREES), speed=ARMOR_BULLET_SPEED, interval=ARMOR_FIRE_INTERVAL),
    "barrage": dict(angles=(-40,-20,0,20,40), speed=84.0, interval=0.45),
}
REAR_PATTERNS = {"rise": dict(stop_y=REAR_STOP_Y, escape_vx=0.0)}

# 出現表はここへ集約。各行=(区間内秒, 敵種, x座標, 移動パターン)。
# sectionのlengthを変えると後続の開始・出現・終了時刻が連動する。
def section(key, length, title, hint, waves):
    return dict(key=key, length=length, title=title, hint=hint, waves=waves)

# 独立した10秒ブロックを連結。同じplanを全道中の素材として再利用できる。
# 小型を片側、装甲を逆側へ。後方射撃と突進は装甲のOPENへ重ねる。
TEMPO_PLAN = (
    section("cross", 10, "01 / CROSS LANES", "SIDE STEP / CUT DURING OPEN", (
        (0.2, "armor", 104, "hold"), (0.2, "formation", 192, "line"),
        (1.4, "rear", 152, "rise"), (3.6, "formation", 56, "line"),
        (4.2, "armor", 168, "hold"),
        (7.2, "formation", 104, "line"))),
    section("flank", 10, "02 / FLANK PRESSURE", "CHOOSE TARGET / LEAVE A GAP", (
        (0.2, "armor", 80, "hold"), (0.2, "formation", 184, "line"),
        (1.3, "charger", 216, "lock"), (3.6, "formation", 128, "line"),
        (4.2, "armor", 176, "hold"), (6.7, "charger", 40, "lock"),
        (7.2, "formation", 56, "line"))),
    section("step", 10, "03 / CUT AND ADVANCE", "KILL / CUT BULLETS / STEP IN", (
        (0.2, "armor", 128, "hold"), (0.2, "formation", 56, "line"),
        (1.4, "rear", 192, "rise"), (3.6, "formation", 200, "line"),
        (4.2, "armor", 72, "hold"),
        (7.2, "formation", 144, "line"), (8.1, "rear", 104, "rise"))),
)

LEGACY_PLAN = (
    section("formation", 25, "01 / FORMATION", "LINE UP / SWEEP THE GROUP", (
        (2, "formation", 128, "line"), (8, "formation", 80, "line"),
        (14, "formation", 176, "line"))),
    section("armor", 20, "02 / ARMOR", "WAIT FOR OPEN / STEP IN", (
        (0.8, "armor", 96, "hold"), (8.8, "armor", 176, "hold"))),
    section("charger", 20, "03 / CHARGER", "READ THE LINE / CUT OR DODGE", (
        (1.5, "charger", 64, "lock"), (7.5, "charger", 192, "lock"),
        (13.5, "charger", 128, "lock"))),
    section("rear", 20, "04 / REAR ARRIVAL", "DODGE SIDEWAYS / CUT AFTER PASS", (
        (2, "rear", 128, "rise"), (11, "rear", 184, "rise"))),
    section("mix", 25, "05 / CHOOSE YOUR TARGET", "OPENING OR REAR THREAT FIRST?", (
        (0.8, "armor", 80, "hold"), (3.5, "formation", 176, "line"),
        (12, "armor", 112, "hold"), (13.2, "rear", 176, "rise"))),
    section("finale", 10, "06 / LAST SWEEP", "SWEEP THE GROUP / THEN BREATHE", (
        (0.5, "formation", 104, "parade"), (2.2, "formation", 152, "parade"))),
)
# 従来の装甲・編隊・突進の単体確認と混成。出現時刻・配置は維持。
CLASSIC_PLAN = (
    section("armor",16,"01 / ARMOR","WAIT FOR OPEN / CUT ONCE",((2,"armor",128,"hold"),)),
    section("formation",20,"02 / FORMATION","LINE UP / SWEEP THE GROUP",(
        (2,"formation",128,"line"),(9,"formation",96,"line"))),
    section("charger",20,"03 / CHARGER","WATCH LINE / CUT OR DODGE",(
        (2,"charger",64,"lock"),(9,"charger",192,"lock"))),
    section("mix",24,"04 / MIX","MAKE A GAP / KEEP MOVING",(
        (2,"armor",72,"hold"),(6,"formation",192,"line"),(11,"charger",184,"lock"),
        (13,"armor",64,"hold"),(16,"formation",152,"line"),(18,"charger",80,"lock"))),
)
# 後方出現敵だけの導入を含む確認コース。旧・上から回る動きは使用しない。
REAR_TEST_PLAN = (
    section("rear",26,"01 / REAR ARRIVAL","SIDE STEP / GET BEHIND / CUT",(
        (2,"rear",128,"rise"),(15,"rear",184,"rise"))),
    section("armor_rear",28,"02 / ARMOR + REAR","OPENING OR REAR THREAT FIRST?",(
        (1,"armor",128,"hold"),(3,"rear",80,"rise"),
        (13,"armor",176,"hold"),(15,"rear",128,"rise"))),
    section("formation_rear",26,"03 / FORMATION + REAR","SWEEP GROUP / AVOID THE LANE",(
        (1,"formation",104,"line"),(1,"rear",128,"rise"),
        (12,"rear",184,"rise"),(13,"formation",160,"line"))),
)

def compile_course(label, menu_label, plan, next_scene="retry"):
    starts, waves, elapsed = [], [], 0.0
    patterns={"formation":FORMATION_PATTERNS,"armor":ARMOR_PATTERNS,
              "charger":{"lock":{}},"rear":REAR_PATTERNS}
    for part in plan:
        if part["length"]<=0:raise ValueError("Section length must be positive")
        starts.append((elapsed,part["title"],part["hint"]))
        for offset,kind,x,pattern in part["waves"]:
            if not 0<=offset<part["length"]:raise ValueError("Wave outside section: "+part["key"])
            if pattern not in patterns[kind]:raise ValueError("Unknown enemy pattern: "+pattern)
            waves.append(dict(at=elapsed+offset,kind=kind,x=x,pattern=pattern,section=part["key"]))
        elapsed+=part["length"]
    return dict(label=label,menu_label=menu_label,sections=tuple(starts),plan=plan,
                waves=tuple(sorted(waves,key=lambda wave:wave["at"])),duration=elapsed,next_scene=next_scene)

# 各区間の主役を先に見せ、途中から別種を追加。全出現時刻はこの表から生成する。
# 小型の座標は編隊の中心。side_* は画面外の左右から斜めに入る。
STAGE_SEED = 7
MIX_SLOT_SECONDS = 15
MIX_CANDIDATES = {
    "rear_port": dict(family="rear", mirror=False, waves=(
        (0.2,"armor",104,"hold"),(0.2,"formation",192,"line"),
        (1.4,"rear",152,"rise"),(3.6,"formation",56,"line"),
        (5.8,"armor",168,"hold"),(7.2,"formation",104,"diagonal_l"),
        (10.4,"armor",80,"hold"),(11.2,"formation",184,"line"))),
    "rear_starboard": dict(family="rear", mirror=True, source="rear_port"),
    "charge_port": dict(family="charge", mirror=False, waves=(
        (0.2,"armor",80,"hold"),(0.2,"formation",184,"line"),
        (1.3,"charger",216,"lock"),(3.6,"formation",128,"line"),
        (5.8,"armor",176,"hold"),(7.2,"formation",56,"diagonal_l"),
        (10.4,"armor",104,"hold"),(11.2,"formation",184,"line"))),
    "charge_starboard": dict(family="charge", mirror=True, source="charge_port"),
}


def mixed_waves(seed, candidates=None):
    import random
    rng=random.Random(seed)
    candidates=MIX_CANDIDATES if candidates is None else candidates
    waves,chosen=[],[]
    previous=None
    for slot in range(6):
        pool=[key for key,p in candidates.items() if p["family"]!=previous]
        key=rng.choice(pool)
        item=candidates[key]
        base=candidates[item.get("source",key)]
        chosen.append(key)
        previous=item["family"]
        for at,kind,x,pattern in base["waves"]:
            if item["mirror"]:
                x=WIDTH-x
                pattern={"diagonal_l":"diagonal_r","diagonal_r":"diagonal_l"}.get(pattern,pattern)
            waves.append((slot*MIX_SLOT_SECONDS+at,kind,x,pattern))
    return tuple(waves),tuple(chosen)


def stage_plan(seed=STAGE_SEED, candidates=None):
    mixed,_=mixed_waves(seed,candidates)
    return (
        section("formation",40,"01 / FORMATIONS","LINE UP / SWEEP / REPOSITION",(
            (0.8,"formation",128,"line"),(4.0,"formation",60,"diagonal_l"),
            (8.0,"formation",286,"side_r"),(9.2,"armor",80,"hold"),
            (12.4,"formation",196,"diagonal_r"),(16.0,"formation",-30,"side_l"),
            (19.8,"formation",128,"line"),(21.0,"armor",184,"hold"),
            (24.2,"formation",56,"diagonal_l"),(28.4,"formation",286,"side_r"),
            (32.2,"formation",160,"line"),(33.4,"armor",72,"hold"),
            (36.0,"formation",184,"diagonal_r"))),
        section("rear",40,"02 / BACK ATTACK","BELOW / SIDE STEP / COUNTER",(
            (1,"rear",128,"rise"),(4,"formation",64,"diagonal_l"),
            (7.8,"rear",192,"rise"),(9.4,"formation",128,"line"),
            (14.0,"rear",64,"rise"),(14.6,"armor",176,"hold"),
            (18.2,"formation",184,"diagonal_r"),(21.0,"rear",160,"rise"),
            (24.0,"formation",-30,"side_l"),(27.4,"rear",88,"rise"),
            (29,"armor",176,"hold"),(32.4,"formation",128,"line"),
            (34.2,"rear",200,"rise"),(36.2,"formation",56,"diagonal_l"))),
        section("charger",40,"03 / INTERCEPT","LOCKED LINE / CUT OR DODGE",(
            (1,"charger",64,"lock"),(4.4,"formation",192,"line"),
            (6.2,"charger",192,"lock"),(10,"charger",128,"lock"),
            (11.8,"formation",56,"diagonal_l"),(14,"armor",176,"hold"),
            (15.4,"charger",40,"lock"),(19.8,"formation",184,"diagonal_r"),
            (21.4,"charger",216,"lock"),(25,"charger",80,"lock"),
            (26.8,"formation",128,"line"),(29.2,"armor",72,"hold"),
            (31.4,"charger",208,"lock"),(34.8,"formation",286,"side_r"),
            (36.4,"charger",56,"lock"))),
        section("armor",40,"04 / ARMORED LINE","READ AIM / STEP INTO OPEN",(
            (0.6,"armor",128,"hold"),(4.4,"formation",56,"diagonal_l"),
            (6.4,"armor",72,"hold"),(9,"formation",192,"line"),
            (12.2,"armor",184,"hold"),(13.6,"rear",72,"rise"),
            (16.4,"formation",128,"line"),(18.6,"armor",96,"hold"),
            (22.4,"formation",184,"diagonal_r"),(24.4,"armor",176,"hold"),
            (25.6,"rear",128,"rise"),(28.6,"formation",56,"line"),
            (30.4,"armor",72,"hold"),(34.2,"formation",192,"line"),
            (36,"armor",160,"hold"))),
        section("barrage",50,"05 / BREAK A CORRIDOR","DODGE GAPS / CUT FORWARD FIRE",tuple(
            wave for block in range(5) for wave in (
                (block*10+0.4,"armor",64 if block%2==0 else 192,"barrage"),
                (block*10+1.8,"formation",184 if block%2==0 else 72,"line"),
                (block*10+5.4,"armor",176 if block%2==0 else 80,"hold"),
                (block*10+6.6,"formation",104 if block%2==0 else 152,"diagonal_l" if block%2==0 else "diagonal_r")))),
        section("mix",90,"06 / COMBINED ASSAULT","CHOOSE / CUT / ADVANCE",mixed),
    )


def stage_course(seed=STAGE_SEED, candidates=None):
    data=compile_course("STAGE 1 / DREADNOUGHT","1面 / 5分＋巨大戦艦",stage_plan(seed,candidates),"boss")
    data["sections"]+=((data["duration"],"07 / DREADNOUGHT","CUT A PATH / DESTROY ALL THREE"),)
    data["seed"],data["mix_choices"]=seed,mixed_waves(seed,candidates)[1]
    return data


STAGE_PLAN = stage_plan()
# ボス攻撃の全値。角度は右=0・下=90。各砲台の予告・発射ピークをずらす。
BOSS_ENTRY_SECONDS, BOSS_ENTRY_Y, BOSS_Y = 4.0, -112.0, 44.0
BOSS_HULL_RECT = (16.0,0.0,224.0,96.0)
BOSS_CYCLE_SECONDS, BOSS_OPEN_FROM = 8.4, 5.0
BOSS_RETREAT_SPEED = 180.0
BOSS_PARTS = {
    "left": dict(x=64.0,dy=100.0,hp=180,radius=14.0,warning_at=0.25,warning=0.65,
                 volleys=(0.0,0.24,0.48),angles=(38,54,70,86,102),speed=90.0),
    "right": dict(x=192.0,dy=100.0,hp=180,radius=14.0,warning_at=1.5,warning=0.65,
                  volleys=(0.0,0.24,0.48),angles=(78,94,110,126,142),speed=90.0),
    "center": dict(x=128.0,dy=106.0,hp=240,radius=16.0,warning_at=2.95,warning=0.8,
                   volleys=(0.0,0.30,0.60),angles=(66,72,78,84,90,96,102,108,114),speed=106.0),
}

# 武器/操作比較用。乱数を使わず、毎回同じ54秒・同じ条件。
COMPARE_PLAN = (
    section("formation",9,"01 / ALIGN & SWEEP","DRAG / FLICK / STEP IN",(
        (0.8,"formation",128,"line"),(3.6,"formation",60,"diagonal_l"),
        (6.0,"formation",286,"side_r"))),
    section("armor",9,"02 / ARMORED OPENING","WAIT FOR OPEN / STEP IN",(
        (0.2,"armor",176,"hold"),(1.6,"formation",72,"line"),
        (4.8,"armor",80,"hold"),(6.4,"formation",184,"diagonal_r"))),
    section("charger",9,"03 / INTERCEPT","READ LOCK / CUT OR DODGE",(
        (0.4,"charger",64,"lock"),(2.0,"formation",184,"line"),
        (4.4,"charger",192,"lock"),(6.6,"formation",56,"diagonal_l"))),
    section("barrage",9,"04 / CUT A CORRIDOR","NARROW THRUST / WIDE SWEEP",(
        (0.2,"armor",72,"barrage"),(1.6,"formation",184,"line"),
        (4.8,"armor",184,"barrage"),(6.3,"formation",72,"line"))),
    section("mix",9,"05 / CHOOSE TARGETS","TWO TYPES / OFFSET FIRE",(
        (0.2,"armor",176,"hold"),(1.5,"formation",64,"diagonal_l"),
        (4.6,"charger",56,"lock"),(5.8,"formation",184,"line"))),
    section("mix",9,"06 / THREE-WAY PASS","RETRY SAME CONDITIONS",(
        (0.2,"armor",72,"barrage"),(1.4,"formation",184,"line"),
        (3.0,"charger",208,"lock"),(5.6,"formation",56,"diagonal_l"))),
)
DEFAULT_COURSE = "stage"
COURSES = {
    "stage":stage_course(),
    "compare":compile_course("WEAPON / INPUT LAB", "54秒 / 武器・操作比較", COMPARE_PLAN),
    "tempo":compile_course("DENSITY TEST / 1.3X", "30秒混成 / 速度1.3倍", TEMPO_PLAN),
    "tempo_fast":compile_course("DENSITY TEST / 1.5X", "30秒混成 / 速度1.5倍", TEMPO_PLAN),
    "boss":dict(label="DREADNOUGHT / PRACTICE",menu_label="巨大戦艦 / 単体確認",duration=0,
                sections=((0,"07 / DREADNOUGHT","CUT A PATH / DESTROY ALL THREE"),),waves=(),next_scene="boss"),
    "legacy":compile_course("OLD ROUTE / 120 SEC","旧120秒道中",LEGACY_PLAN),
    "classic":compile_course("THREE ENEMIES","従来の敵3種テスト",CLASSIC_PLAN),
    "rear":compile_course("REAR ARRIVAL","後方出現テスト",REAR_TEST_PLAN),
}
STAGE_SECONDS = COURSES["stage"]["duration"]
# ゲーム・Editorが共用する原本。build.pyは生成・上書きせず、そのまま同梱する。
RESOURCE_FILE = "assets/blade.pyxres"
PALETTE_FILE = "assets/blade.pyxpal"
KEYBOARD_INPUTS = {
    "left": ("KEY_LEFT",), "right": ("KEY_RIGHT",),
    "up": ("KEY_UP",), "down": ("KEY_DOWN",),
    "slash": ("KEY_Z",), "confirm": ("KEY_RETURN",),
    "settings": ("KEY_X",), "pause": ("KEY_P",), "quit": ("KEY_ESCAPE",),
}
GKD_INPUTS = {
    "left": ("GAMEPAD1_BUTTON_DPAD_LEFT",), "right": ("GAMEPAD1_BUTTON_DPAD_RIGHT",),
    "up": ("GAMEPAD1_BUTTON_DPAD_UP",), "down": ("GAMEPAD1_BUTTON_DPAD_DOWN",),
    "slash": ("GAMEPAD1_BUTTON_A",), "confirm": ("GAMEPAD1_BUTTON_START",),
    "settings": ("GAMEPAD1_BUTTON_B",), "pause": ("GAMEPAD1_BUTTON_START",), "quit": ("GAMEPAD1_BUTTON_BACK",),
}
# 距離=256x320ゲームpx、時刻=ms。ドラッグの倍率は判定に掛けない。
WEB_TOUCH = {
    "drag_gain": 1.2, "move_region_ratio": 0.5, # 左側の幅。境界ちょうどは攻撃側。
    "flick_axes": {"blade":"horizontal", "axe":"horizontal", "lance":"vertical"},
    "flick_distance_px": 14.0, "flick_min_speed_px_ms": 0.40,
    "flick_window_ms": 90.0, "flick_idle_sample_ms": 1000/FPS, "flick_axis_tolerance_degrees": 35.0,
    "flick_release_speed_px_ms": 0.12, "flick_rearm_idle_ms": 90.0,
}
# 子機版の52色パレットを共用（インデックスは維持）。
PALETTE = [
    0x000000, 0x4F4F4F, 0xADADAD, 0xFFFEFF, 0x002A88, 0x4240FF,
    0x48CDDE, 0x005200, 0x5CE430, 0xBCBE00, 0xEA9E22, 0xB53120,
    0xFE6ECC, 0x7527FE, 0x9290FF, 0x994E00, 0x666666, 0x1412A7,
    0x3B00A4, 0x5C007E, 0x6E0040, 0x6C0600, 0x561D00, 0x0B4800,
    0x004F08, 0x00404D, 0x155FD9, 0xA01ACC, 0xB71E7B, 0x6B6D00,
    0x388700, 0x0C9300, 0x008F32, 0x007C8D, 0x64B0FF, 0xC676FF,
    0xF36AFF, 0xFE8170, 0x88D800, 0x45E082, 0xC0DFFF, 0xD3D2FF,
    0xE8C8FF, 0xFBC2FF, 0xFEC4EA, 0xFECCC5, 0xF7D8A5, 0xE4E594,
    0xCFEF96, 0xBDF4AB, 0xB3F3CC, 0xB5EBF2,
]

# 第2面専用の数値・固定配置・練習開始地点はstage2_config.pyに集約。
from stage2_config import practice_courses
COURSES = {"stage":COURSES["stage"], **practice_courses(),
           **{name:data for name,data in COURSES.items() if name!="stage"}}

# 第3面の固定配置・壁・反射戦・エンディング。
from stage3_config import practice_courses as stage3_practice,BARRIER,FINAL
COURSES.update(stage3_practice())
SCORING["points"].update(barrier=BARRIER["points"],boss_final=0,final_victory=FINAL["points"])
AREA_ITEM["courses"]=(*AREA_ITEM["courses"],"stage3")
