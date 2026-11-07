"""調整箇所。時間=秒、距離=ゲーム内px、速度=px/秒。変更後build.pyで配布版更新。"""
TITLE, VERSION = "BLADE / CLOSE QUARTERS", "0.5.0"
WIDTH, HEIGHT, HUD_HEIGHT, FPS = 256, 320, 24, 60
PLAYER_SIZE, PLAYER_HIT_RADIUS = 16, 2.0
PLAYER_SPEED, PLAYER_HP, INVINCIBLE_SECONDS = 125.0, 3, 1.2
SHOT_INTERVAL, SHOT_SPEED, SHOT_DAMAGE = 0.14, 300.0, 1
BLADE_REACH, BLADE_INNER, BLADE_WIDTH = 60.0, 30.0, 4.0
BLADE_DAMAGE, BLADE_COOLDOWN = 40, 1.0
# ショットはこの3区間すべてで停止。攻撃・弾消しはACTIVEだけ。
# RECOVERYは移動できる振り終わり。追加延長は実測して必要な場合だけ行う。
BLADE_WINDUP, BLADE_ACTIVE, BLADE_RECOVERY = 0.07, 0.10, 0.24
BLADE_START_ANGLE, BLADE_END_ANGLE = -165.0, -15.0
HITSTOP_SECONDS, SHAKE_SECONDS, SHAKE_PIXELS = 0.05, 0.16, 1.5
SMALL_HP, SMALL_RADIUS, SMALL_SPEED = 2, 8.0, 38.0
ARMOR_HP, ARMOR_RADIUS = 32, 15.0
ARMOR_ENTRY_SPEED, ARMOR_Y, ARMOR_LIFETIME = 54.0, 112.0, 9.0
ARMOR_FIRE_SECONDS, ARMOR_REST_SECONDS = 1.65, 2.5
ARMOR_FIRE_INTERVAL, ARMOR_SPREAD_DEGREES = 0.55, 18.0
ARMOR_BULLET_SPEED, SMALL_BULLET_SPEED = 38.0, 48.0
BULLET_RADIUS, BULLET_HIT_RADIUS = 3.0, 2.0
FULLSCREEN, SOUND_ENABLED = False, True
# 小型編隊の中心と、中心からの相対配置。個々の機体HP・速度はSMALL_*。
FORMATION_OFFSETS = ((-22, 0), (0, -6), (22, 0))
FORMATION_SWAY = 5.0
SMALL_FIRST_SHOT = 2.0
# 予告開始時点で進路を固定。突進中も追尾しない。
CHARGER_HP, CHARGER_RADIUS = 24, 11.0
CHARGER_ENTRY_SPEED, CHARGER_Y = 64.0, 96.0
CHARGER_WARNING_SECONDS, CHARGER_SPEED = 1.2, 140.0
# 後方出現敵。下端マーカー→入場→停止予告→上向き射撃→上へ離脱。
REAR_HP, REAR_RADIUS = 12, 10.0
REAR_MARKER_SECONDS, REAR_ENTRY_SPEED = 1.2, 56.0
REAR_STOP_Y, REAR_EXIT_SPEED = 288.0, 44.0
REAR_CONTACT_GRACE = 0.35
REAR_WARNING_SECONDS = 1.4
REAR_BULLET_SPEED, REAR_SHOT_INTERVAL, REAR_SHOTS = 42.0, 0.55, 3
# 出現表のpattern欄から選ぶ。通常編隊の既存速度・射撃は維持。
FORMATION_PATTERNS = {
    "line": dict(speed=SMALL_SPEED, sway=FORMATION_SWAY, drift=0, shot_after=SMALL_FIRST_SHOT),
    "parade": dict(speed=64.0, sway=2.0, drift=0, shot_after=None),
}
REAR_PATTERNS = {"rise": dict(stop_y=REAR_STOP_Y, escape_vx=0.0)}

# 出現表はここへ集約。各行=(区間内秒, 敵種, x座標, 移動パターン)。
# sectionのlengthを変えると後続の開始・出現・終了時刻が連動する。
def section(key, length, title, hint, waves):
    return dict(key=key, length=length, title=title, hint=hint, waves=waves)

STAGE_PLAN = (
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
    patterns={"formation":FORMATION_PATTERNS,"armor":{"hold":{}},
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

DEFAULT_COURSE = "stage"
COURSES = {
    "stage":compile_course("STAGE 1 / APPROACH","1面の道中",STAGE_PLAN,"boss"),
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
    "pause": ("KEY_P",), "quit": ("KEY_ESCAPE",),
}
GKD_INPUTS = {
    "left": ("GAMEPAD1_BUTTON_DPAD_LEFT",), "right": ("GAMEPAD1_BUTTON_DPAD_RIGHT",),
    "up": ("GAMEPAD1_BUTTON_DPAD_UP",), "down": ("GAMEPAD1_BUTTON_DPAD_DOWN",),
    "slash": ("GAMEPAD1_BUTTON_A",), "confirm": ("GAMEPAD1_BUTTON_START",),
    "pause": ("GAMEPAD1_BUTTON_START",), "quit": ("GAMEPAD1_BUTTON_BACK",),
}
WEB_TOUCH = {
    "drag_gain": 1.2, "tap_max_movement_px": 10.0, "tap_max_duration_ms": 220.0,
    "double_tap_min_interval_ms": 40.0, "double_tap_max_interval_ms": 300.0,
    "double_tap_max_distance_px": 32.0,
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
