"""第3面。秒・ゲームpx・px/秒・度数。固定配置でルートを調整する。"""
from stage2_config import section,compile_route

AREA_SECONDS=(30.0,30.0,30.0,30.0,30.0)
CAVE=dict(base_width=14.0,scroll_speed=54.0,player_margin=11.0,
          release_margin=18.0,minimum_corridor=96.0,
          rim_profile=((0.,0.),(13.,4.),(28.,1.),(41.,5.),(57.,2.),(73.,0.)))
# 大きな岩塊・割れ目の輪郭。描画と接触判定は同じ折れ線を使う。
WALL_SHAPES={
 'shelf':((0,0),(.12,.23),(.23,.62),(.37,.83),(.43,.68),(.53,1),(.66,.92),(.77,.53),(.88,.31),(1,0)),
 'tooth':((0,0),(.14,.19),(.27,.50),(.40,.94),(.49,1),(.57,.70),(.68,.82),(.80,.42),(.92,.16),(1,0)),
 'step':((0,0),(.13,.38),(.28,.46),(.37,.72),(.49,.64),(.60,1),(.72,.89),(.81,.51),(.91,.33),(1,0))}
BARRIER=dict(hp=24,radius=12.0,entry_speed=165.0,y=90.0,
             shield_seconds=2.4,fade_seconds=.5,open_seconds=1.9,
             fire_at=(.40,1.05),angles=(-18,0,18),bullet_speed=105.0,
             lifetime=12.0,exit_speed=160.0,points=600)
FINAL=dict(hp=240,radius=13.0,entry_seconds=2.4,move_warning=.50,
           dash_seconds=.32,aim_warning=.48,rest_seconds=3.50,
           positions=((56.,100.),(200.,124.),(64.,152.),(192.,88.)),
           volleys=(0.0,.32,1.60,1.92,2.90),angles=(-24,-12,0,12,24),bullet_speed=108.0,
           reflected_speed=260.0,reflected_damage=12,reflected_lifetime=4.0,
           points=20000)
FINAL['cycle']=sum(FINAL[k] for k in ('move_warning','dash_seconds','aim_warning','rest_seconds'))
ENDING=dict(clear_seconds=5.0,scroll_speed=20.0,line_spacing=24.0,tail_seconds=2.0,
            bgm=6,credits=('BLADE / CLOSE QUARTERS','','THANK YOU FOR PLAYING','',
            'PLANNING / DESIGN','GONZARES TANAKA','','PROGRAMMING','GONZARES TANAKA','','ART / SOUND','GONZARES TANAKA','',
            'SPECIAL THANKS','PYXEL / KITA O','','PLAYER','YOU','','THE END'))

def stage3_plan():
    # 固定の混成セル。バリアの初弾は登場後約4秒、装甲は約1秒。
    # 後方予告・突進・ミサイルを1.5〜3秒ずらし、左右の出口を交互に残す。
    return (
      section('walls','01 / CROSS FIRE','BARRIER + ARMOR / KEEP A SIDE EXIT',(
        (0,'wall',0,'shelf',118,165),(1,'barrier',72,'cycle'),(2,'armor',184,'hold'),
        (4,'formation',174,'diagonal_l'),(8,'charger',48,'lock'),
        (10,'wall',1,'tooth',120,175),(11,'barrier',180,'cycle'),(12.5,'rear',76,'rise'),
        (15,'formation',82,'line'),(17,'missile',176,'launch'),
        (20,'wall',0,'step',116,160),(21,'armor',176,'hold'),(23,'rear',82,'rise'),
        (25,'barrier',72,'cycle'),(26,'formation',178,'diagonal_r')),AREA_SECONDS[0]),
      section('barrier','02 / SHIELD AND FLANK','CHOOSE A TARGET / WATCH THE CHARGE',(
        (0,'wall',1,'step',122,170),(1,'barrier',176,'cycle'),(2.5,'missile',80,'launch'),
        (5,'charger',192,'lock'),(8,'formation',78,'diagonal_r'),
        (10,'wall',0,'tooth',120,175),(11,'barrier',80,'cycle'),(12.5,'armor',180,'hold'),
        (15,'formation',172,'line'),(18,'rear',180,'rise'),
        (20,'wall',1,'shelf',116,160),(21,'barrier',174,'cycle'),(23,'charger',64,'lock'),
        (25,'missile',80,'launch'),(27,'formation',180,'diagonal_l')),AREA_SECONDS[1]),
      section('choice','03 / RESIDUAL LANES','ARMOR FIRE / REAR SIGNAL / CHANGE LANES',(
        (0,'wall',0,'tooth',124,180),(1,'armor',178,'hold'),(2.5,'rear',76,'rise'),
        (4,'barrier',78,'cycle'),(7,'formation',180,'line'),
        (10,'wall',1,'step',120,170),(11,'armor',78,'hold'),(12.5,'rear',180,'rise'),
        (14,'barrier',176,'cycle'),(17,'charger',64,'lock'),
        (20,'wall',0,'shelf',116,160),(21,'barrier',76,'cycle'),(22.5,'missile',178,'launch'),
        (25,'formation',176,'diagonal_r'),(27,'rear',82,'rise')),AREA_SECONDS[2]),
      section('cross','04 / THREE WAY PRESSURE','CUT A LANE / THEN LEAVE IT',(
        (0,'wall',1,'shelf',122,175),(1,'barrier',178,'cycle'),(2.5,'armor',78,'hold'),
        (4.5,'charger',194,'lock'),(7,'formation',78,'diagonal_l'),
        (10,'wall',0,'step',118,170),(11,'barrier',76,'cycle'),(12.5,'missile',178,'launch'),
        (15,'rear',80,'rise'),(18,'formation',176,'line'),
        (20,'wall',1,'tooth',120,180),(21,'armor',78,'hold'),(22.5,'barrier',176,'cycle'),
        (25,'charger',62,'lock'),(27,'formation',176,'diagonal_r')),AREA_SECONDS[3]),
      section('final','05 / INNER CORE','READ THE ROCK / OPEN THE NEXT LANE',(
        (0,'wall',0,'step',122,175),(1,'barrier',76,'cycle'),(2.5,'armor',178,'hold'),
        (4.5,'rear',80,'rise'),(7,'formation',176,'diagonal_l'),
        (10,'wall',1,'shelf',120,170),(11,'barrier',176,'cycle'),(12.5,'missile',78,'launch'),
        (15,'charger',194,'lock'),(18,'formation',80,'line'),
        (20,'wall',0,'tooth',116,170),(21,'armor',178,'hold'),(22.5,'barrier',76,'cycle'),
        (25,'rear',178,'rise'),(27,'formation',78,'diagonal_r')),AREA_SECONDS[4]))

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
