"""Editorの原本を読み込むだけ。起動・ビルド時に素材を生成しない。"""
from pathlib import Path
import config as C

SPRITES = {
    "player": (0, 0, 16, 16), "arm": (16, 0, 8, 4), "blade": (32, 0, 30, 4),
    "axe": (192, 0, 14, 14), "lance": (208, 0, 28, 16),
    "small": (64, 0, 16, 16), "shot": (80, 0, 4, 8), "bullet": (88, 0, 8, 8),
    "joint": (96, 0, 4, 4), "engine": (104, 0, 8, 8),
    "stars": (128, 0, 16, 16), "lane": (144, 0, 8, 16),
    "armor": (0, 32, 32, 32), "armor_open": (32, 32, 32, 32),
    "charger": (64, 32, 24, 24), "charger_warning": (88, 32, 24, 24),
    "charger_dash": (112, 32, 24, 24),
    "rear": (144, 32, 24, 24), "rear_warning": (168, 32, 24, 24),
    "impact": (0, 80, 16, 16), "spark": (16, 80, 8, 8),
    "pop": (24, 80, 16, 16), "hurt": (40, 80, 16, 16), "split": (56, 80, 16, 16),
    "boss_hull": (0,112,224,104),
    "boss_left": (0,224,24,24), "boss_right": (24,224,24,24),
    "boss_center": (48,224,32,32), "boss_destroyed": (80,224,32,32),
}


def load_resources(p, filename=None):
    path = Path(filename) if filename else Path(__file__).resolve().parent/C.RESOURCE_FILE
    p.colors[:] = C.PALETTE
    p.load(str(path))
    if list(p.colors) != C.PALETTE:
        raise RuntimeError("Keep the 52 colors in blade.pyxpal in config.py order")


def sprite(p, name, x, y, rotate=0, scale=1):
    u, v, w, h = SPRITES[name]
    p.blt(x-w/2, y-h/2, 0, u, v, w, h, 0, rotate=rotate, scale=scale)
