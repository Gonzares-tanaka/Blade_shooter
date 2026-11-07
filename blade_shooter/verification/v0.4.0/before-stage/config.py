"""調整箇所。時間=秒、距離=ゲーム内px、速度=px/秒。変更後build.pyで配布版更新。"""
TITLE, VERSION = "BLADE / CLOSE QUARTERS", "0.4.0"
WIDTH, HEIGHT, HUD_HEIGHT, FPS = 256, 320, 24, 60
STAGE_SECONDS = 80.0
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
# 区間開始秒、見出し、判断のヒント。各区間の出現後には次の出現まで余白を置く。
TEST_SECTIONS = (
    (0, "01 / ARMOR", "WAIT FOR OPEN / CUT ONCE"),
    (16, "02 / FORMATION", "LINE UP / SWEEP THE GROUP"),
    (36, "03 / CHARGER", "WATCH LINE / CUT OR DODGE"),
    (56, "04 / MIX", "MAKE A GAP / KEEP MOVING"),
)
ARMOR_WAVES = ((2, 128), (58, 72), (69, 64))
# 小型編隊の中心と、中心からの相対配置。個々の機体HP・速度はSMALL_*。
FORMATION_OFFSETS = ((-22, 0), (0, -6), (22, 0))
FORMATION_WAVES = ((18, 128), (25, 96), (62, 192), (72, 152))
FORMATION_SWAY = 5.0
SMALL_FIRST_SHOT = 2.0
# 予告開始時点で進路を固定。突進中も追尾しない。
CHARGER_HP, CHARGER_RADIUS = 24, 11.0
CHARGER_ENTRY_SPEED, CHARGER_Y = 64.0, 96.0
CHARGER_WARNING_SECONDS, CHARGER_SPEED = 1.2, 140.0
CHARGER_WAVES = ((38, 64), (45, 192), (67, 184), (74, 80))
# 回り込み敵。経路末尾に固定停止位置を追加する。自機位置は参照しない。
REAR_HP, REAR_RADIUS = 12, 10.0
REAR_SPEED, REAR_EXIT_SPEED = 78.0, 86.0
REAR_PATHS = {
    "left": ((100, -20), (32, 72), (32, 228)),
    "right": ((156, -20), (224, 72), (224, 228)),
}
REAR_STOPS = {"left": (128, 290), "right": (176, 286)}
REAR_WARNING_SECONDS = 1.4
REAR_BULLET_SPEED, REAR_SHOT_INTERVAL, REAR_SHOTS = 42.0, 0.55, 3
REAR_WAVES = ((2, "left"), (10, "right"), (27, "left"),
              (39, "right"), (55, "left"), (66, "right"))
REAR_SECTIONS = (
    (0, "01 / REAR INTRO", "CUT BEFORE PASS / AVOID LANE"),
    (26, "02 / ARMOR + REAR", "OPENING OR FLANKER FIRST?"),
    (54, "03 / FORMATION + REAR", "SWEEP GROUP / LEAVE THE LANE"),
)
REAR_ARMOR_WAVES = ((28, 128), (40, 176))
REAR_FORMATION_WAVES = ((56, 104), (68, 160))
DEFAULT_COURSE = "rear"
COURSES = {
    "rear": {"label": "REAR PRESSURE", "sections": REAR_SECTIONS,
             "armor": REAR_ARMOR_WAVES, "formation": REAR_FORMATION_WAVES,
             "charger": (), "rear": REAR_WAVES},
    "classic": {"label": "THREE ENEMIES", "sections": TEST_SECTIONS,
                "armor": ARMOR_WAVES, "formation": FORMATION_WAVES,
                "charger": CHARGER_WAVES, "rear": ()},
}
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
