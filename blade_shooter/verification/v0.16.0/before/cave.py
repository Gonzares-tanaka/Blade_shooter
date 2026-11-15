"""接触する明色の岩壁。背景岩肌とは別のデータと判定。"""
from dataclasses import dataclass
import math
from stage3_config import CAVE as S,WALL_SHAPES

@dataclass
class Wall:
    side: int
    depth: float
    height: float
    shape: str
    y: float = -190.0
    def edge(self,y):
        t=(y-self.y)/self.height
        if not 0<=t<=1:return S['base_width']
        points=WALL_SHAPES[self.shape]
        for (a,x),(b,z) in zip(points,points[1:]):
            if a<=t<=b:return S['base_width']+self.depth*(x+(z-x)*(t-a)/(b-a))
        return S['base_width']
    @property
    def polygon(self):
        points=[(S['base_width']+self.depth*x,self.y+t*self.height) for t,x in WALL_SHAPES[self.shape]]
        return tuple((256-x if self.side else x,y) for x,y in ([(0,self.y)]+points+[(0,self.y+self.height)]))

class CaveWalls:
    def __init__(self):self.walls=[];self.latched=False;self.contacts=0
    def spawn(self,side,shape,depth,height):
        self.walls.append(Wall(side,depth,height,shape,-height))
    def update(self,dt):
        for wall in self.walls:wall.y+=S['scroll_speed']*dt
        self.walls=[w for w in self.walls if w.y<344]
    def bounds(self,y,radius=8):
        left=right=S['base_width']
        for w in self.walls:
            # 全ての頂点と自機の上下を評価し、壁の角を抜けない。
            samples=[y-radius,y,y+radius]+[w.y+t*w.height for t,_ in WALL_SHAPES[w.shape] if y-radius<=w.y+t*w.height<=y+radius]
            edge=max(w.edge(yy) for yy in samples)
            if w.side:right=max(right,edge)
            else:left=max(left,edge)
        return left,256-right
    def constrain(self,game,previous=None):
        left,right=self.bounds(game.py)
        blocked=game.px-8<left or game.px+8>right
        if previous is not None:
            # 高速なタッチ移動でも、壁の角を経路だけすり抜けない。
            steps=max(1,math.ceil(math.dist(previous,(game.px,game.py))/4))
            for i in range(steps+1):
                t=i/steps;x=previous[0]+(game.px-previous[0])*t;y=previous[1]+(game.py-previous[1])*t
                a,b=self.bounds(y)
                if x-8<a or x+8>b:blocked=True;break
        if blocked:
            if not self.latched:game.hurt();self.contacts+=1
            game.px=max(left+S['player_margin'],min(right-S['player_margin'],game.px))
            self.latched=True
        elif min(game.px-left,right-game.px)>=S['release_margin']:self.latched=False
