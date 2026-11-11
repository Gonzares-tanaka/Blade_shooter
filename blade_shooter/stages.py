"""第1・2面を登録。RunStateを保って次の面へ進む。"""
from dataclasses import dataclass
import config as C
from boss import Battleship
from stealth import StealthChain
from stage2_config import stage2_course

PLANNED_STAGE_COUNT = 3

@dataclass(frozen=True)
class StageDefinition:
    number: int
    route_factory: object
    mixed_candidates: dict
    background: str
    bgm: int
    boss_factory: object
    boss_bgm: int
    clear_target: str
    next_stage: object = None
    item_positions: tuple = C.AREA_ITEM['positions']

    def build(self,seed):
        data=self.route_factory(seed,self.mixed_candidates)
        elapsed=0.0;points=[]
        for part in data['plan']:
            elapsed+=part['length'];points.append(elapsed)
        data.update(stage_number=self.number, background=self.background, bgm=self.bgm,
                    boss=self.boss_factory, boss_bgm=self.boss_bgm,
                    mixed_candidates=self.mixed_candidates,item_points=tuple(points),item_positions=self.item_positions,
                    clear_target=self.clear_target,next_stage=self.next_stage)
        return data

STAGES = {1:StageDefinition(1,C.stage_course,C.MIX_CANDIDATES,"star_lanes",0,
                           Battleship,1,"result",next_stage=2),
          2:StageDefinition(2,stage2_course,{},"asteroid_belt",2,StealthChain,3,"result")}

def get_stage(number):
    if number not in STAGES:raise ValueError("Stage content has not been implemented: "+str(number))
    return STAGES[number]
