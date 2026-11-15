"""第3面。秒・ゲームpx・px/秒・度数。固定配置でルートを調整する。"""
from stage2_config import section,compile_route

AREA_SECONDS=(30.0,30.0,30.0,30.0,30.0)
CAVE=dict(base_width=14.0,scroll_speed=54.0,player_margin=11.0,
          release_margin=18.0,minimum_corridor=96.0)
# 横位置の奥行き。先端を斜面にして急に進路を塞がない。
WALL_SHAPES={'shelf':((0,0),(.35,1),(.70,1),(1,0)),
             'tooth':((0,0),(.45,1),(.65,.85),(1,0)),
             'step':((0,0),(.30,.6),(.55,1),(.75,1),(1,0))}
BARRIER=dict(hp=24,radius=12.0,entry_speed=165.0,y=90.0,
             shield_seconds=2.4,fade_seconds=.5,open_seconds=1.9,
             fire_at=(.40,1.05),angles=(-18,0,18),bullet_speed=105.0,
             lifetime=12.0,exit_speed=160.0,points=600)
FINAL=dict(hp=240,radius=13.0,entry_seconds=2.4,move_warning=.65,
           dash_seconds=.55,aim_warning=.65,rest_seconds=4.35,
           positions=((64.,96.),(192.,112.),(88.,144.),(176.,88.)),
           volleys=(0.0,1.50),angles=(-14,0,14),bullet_speed=108.0,
           reflected_speed=260.0,reflected_damage=12,reflected_lifetime=4.0,
           points=20000)
FINAL['cycle']=sum(FINAL[k] for k in ('move_warning','dash_seconds','aim_warning','rest_seconds'))
ENDING=dict(clear_seconds=5.0,scroll_speed=20.0,line_spacing=24.0,tail_seconds=2.0,
            bgm=6,credits=('BLADE / CLOSE QUARTERS','','THANK YOU FOR PLAYING','',
            'PLANNING / DESIGN','TBD','','PROGRAMMING','TBD','','ART / SOUND','TBD','',
            'SPECIAL THANKS','PYXEL / KITA O','','PLAYER','YOU','','THE END'))

def stage3_plan():
    # wall行のxは0=左/1=右、patternは形、wall=(深さ,高さ)。
    return (
      section('walls','01 / LUNAR CAVERN','BRIGHT EDGES ARE SOLID / MOVE AROUND',(
        (1,'wall',0,'shelf',124,150),(8,'wall',1,'tooth',126,160),
        (12,'formation',164,'line'),(16,'rear',78,'rise'),
        (20,'wall',0,'step',122,140),(24,'formation',180,'diagonal_r')),AREA_SECONDS[0]),
      section('barrier','02 / BARRIER CARRIER','SHIELD / FLASH / OPEN',(
        (1,'barrier',128,'cycle'),(12,'barrier',88,'cycle'),
        (16,'formation',182,'line'),(21,'wall',1,'shelf',116,145)),AREA_SECONDS[1]),
      section('choice','03 / CHOOSE THE OPEN SIDE','LET THE SHIELD FALL / CHANGE TARGETS',(
        (0,'wall',0,'tooth',128,175),(4,'formation',172,'line'),
        (8,'barrier',84,'cycle'),(12,'wall',1,'step',122,155),
        (17,'missile',80,'launch'),(22,'wall',0,'shelf',116,145),
        (26,'rear',184,'rise')),AREA_SECONDS[2]),
      section('cross','04 / SHIFT YOUR ROUTE','WALL FIRST / THEN INTERCEPT',(
        (0,'wall',1,'shelf',132,155),(4,'charger',72,'lock'),
        (8,'wall',0,'step',118,140),(12,'barrier',180,'cycle'),
        (16,'formation',76,'diagonal_l'),(20,'wall',1,'tooth',126,170),
        (25,'armor',76,'hold')),AREA_SECONDS[3]),
      section('final','05 / INNER CORE','CHOOSE TARGETS / LEAVE A SIDE EXIT',(
        (0,'wall',0,'shelf',124,155),(4,'barrier',172,'cycle'),
        (8,'formation',80,'line'),(11,'wall',1,'step',128,160),
        (16,'missile',76,'launch'),(19,'rear',180,'rise'),
        (22,'wall',0,'tooth',120,140),(26,'formation',170,'diagonal_r')),AREA_SECONDS[4]))

def compile_cave(plan,label='STAGE 3 / LUNAR CAVERN',menu='3面 / 月面洞窟（仮）',next_scene='boss'):
    # 共通route形式へ変換。壁だけ追加データを付ける。
    plain=[];walls=[];elapsed=0.0
    for part in plan:
        ordinary=[]
        for row in part['waves']:
            if row[1]=='wall':
                at,_,side,shape,depth,height=row
                if 0<=at<part['length']:
                    walls.append(dict(at=elapsed+at,kind='wall',x=side,pattern=shape,
                                      wall=(depth,height),section=part['key']))
            else:ordinary.append(row)
        plain.append(dict(part,waves=tuple(ordinary)));elapsed+=part['length']
    data=compile_route(tuple(plain),label,menu,next_scene)
    data.update(stage_number=3,plan=plan,waves=tuple(sorted((*data['waves'],*walls),key=lambda w:w['at'])))
    return data

def stage3_course(seed=7,candidates=None):return compile_cave(stage3_plan())

def practice_courses():
    return dict(stage3=stage3_course(),
      cave=compile_cave(stage3_plan(),'CAVERN / PRACTICE','3面道中 / 区間開始可','retry'),
      final=compile_cave((section('boss','FINAL / REFLECTOR','REFLECT BULLETS WITH MELEE',(),0),),
                         'FINAL / PRACTICE','最終ボス / 反射確認'))
