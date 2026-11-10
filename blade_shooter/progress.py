"""ステージを跨いで引き継ぐ状態と、終了時点の変更されない記録。"""
from dataclasses import dataclass
import config as C

@dataclass
class RunState:
    current_stage: int = 1
    score: int = 0
    hp: int = C.PLAYER_HP
    weapon: str = C.DEFAULT_WEAPON
    current_cut: int = 0
    max_cut: int = 0
    cut_remaining: float = 0.0

@dataclass(frozen=True)
class Result:
    stage: int
    cleared: bool
    score: int
    best_score: int
    max_cut: int
    boss_defeated: bool
    weapon: str
    seconds: float

@dataclass
class ScorePopup:
    x: float
    y: float
    points: int
    melee: bool
    age: float = 0.0
