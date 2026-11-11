"""第2面の調整表。秒・ゲームpx・px/秒。固定配置、乱数は使用しない。"""
import math

ROCK = dict(radius=12.0, hp=1, speed=68.0, spacing=28.0, gap_width=76.0,
            drift=20.0, drift_frequency=.65, shot_spark_seconds=.10)
ROCK_PATTERNS = {
    'left_gap':dict(gap=44.0, direction=0, speed=68.0),
    'right_gap':dict(gap=212.0, direction=0, speed=68.0),
    'drift_left':dict(gap=184.0, direction=-1, speed=76.0),
    'drift_right':dict(gap=72.0, direction=1, speed=76.0),
    'center_gap':dict(gap=128.0, direction=0, speed=82.0),
}
MISSILE = dict(hp=18, radius=11.0, entry_speed=180.0, stop_y=78.0,
               warning=.65, interval=3.3, volleys=2, exit_speed=170.0,
               speed=102.0, turn_degrees_second=65.0, homing_seconds=1.25,
               radius_bullet=5.0, hit_radius=3.0, life_seconds=6.0, points=350)
STEALTH = dict(count=6, hp=90, radius=11.0, entry_seconds=3.0,
               delay=.48, center_x=128.0, center_y=110.0,
               sweep_width=77.0, sweep_height=37.0, angular_speed=.48,
               cycle=8.4, warning=.65, part_offset=.62, open_from=4.4,
               bullet_speed=92.0, angles=(65,90,115),
               part_points=2000, defeat_points=8000)

# 6区間×30秒。各区間長を変えても後続の時刻・アイテム時刻は再計算する。
AREA_SECONDS = (30.0,30.0,30.0,30.0,30.0,30.0)

def rock_row(pattern):
    p=ROCK_PATTERNS[pattern]
    return tuple(x for x in (16+i*ROCK['spacing'] for i in range(9))
                 if abs(x-p['gap'])>=ROCK['gap_width']/2)


def section(key,title,hint,waves,length):
    return dict(key=key,title=title,hint=hint,waves=tuple(waves),length=length)


def stage2_plan():
    rocks=lambda times,patterns:tuple((t,'rock_row',0,patterns[i%len(patterns)]) for i,t in enumerate(times))
    return (
        section('rocks','01 / ASTEROID GATE','ROCKS: SHOT IMMUNE / CUT OR SIDE STEP',
                rocks((1,5,9,13,17,21,25),('left_gap','right_gap'))+
                ((11,'formation',184,'diagonal_r'),(23,'formation',64,'diagonal_l')),AREA_SECONDS[0]),
        section('missile','02 / HOMING SIGNAL','FLASH / DRAW MISSILE / SIDE STEP OR CUT',
                ((1,'missile',176,'launch'),(10,'missile',64,'launch'),
                 (17,'formation',184,'line'),(24,'missile',192,'launch'))+
                rocks((14,19,25),('left_gap','right_gap')),AREA_SECONDS[1]),
        section('crossing','03 / CROSS CURRENT','CUT ONE ROW / DODGE THE NEXT',
                rocks((0,3.2,6.4,10,13.2,16.4,20,23.2,26.4),('drift_left','drift_right','center_gap'))+
                ((2,'formation',64,'line'),(9,'missile',192,'launch'),
                 (16,'formation',184,'diagonal_r'),(23,'missile',64,'launch')),AREA_SECONDS[2]),
        section('armor','04 / MINING ESCORT','ROCK GAPS / ARMOR OPENINGS',
                rocks((0,3.5,7,12,15.5,19,24,27),('center_gap','drift_left','drift_right'))+
                ((1,'armor',64,'hold'),(8,'formation',184,'line'),(13,'armor',192,'hold'),
                 (20,'missile',64,'launch'),(26,'formation',184,'line')),AREA_SECONDS[3]),
        section('intercept','05 / INTERCEPT CURRENT','LOCKED DASH / LEAVE A SIDE EXIT',
                rocks((0,3.2,6.4,11,14.2,17.4,22,25.2),('right_gap','left_gap','center_gap'))+
                ((1,'charger',64,'lock'),(8,'missile',192,'launch'),(14,'formation',64,'line'),
                 (20,'charger',192,'lock'),(27,'formation',64,'line')),AREA_SECONDS[4]),
        section('mix','06 / STEALTH APPROACH','ROCK / MISSILE / CHOOSE A CORRIDOR',
                rocks((0,3.4,6.8,11,14.4,17.8,22,25.4),('drift_right','center_gap','drift_left'))+
                ((1,'missile',192,'launch'),(5,'formation',64,'diagonal_l'),
                 (12,'armor',64,'hold'),(18,'formation',184,'line'),(23,'missile',64,'launch')),AREA_SECONDS[5]),
    )


def compile_route(plan,label='STAGE 2 / ASTEROID BELT',menu='2面 / アステロイド帯',next_scene='boss'):
    waves=[];sections=[];elapsed=0.0
    for part in plan:
        sections.append((elapsed,part['title'],part['hint']))
        for at,kind,x,pattern in part['waves']:
            # 短く調整した区間の末尾を越える編隊は生成しない。
            if 0<=at<part['length']:
                waves.append(dict(at=elapsed+at,kind=kind,x=x,pattern=pattern,section=part['key']))
        elapsed+=part['length']
    return dict(label=label,menu_label=menu,plan=plan,sections=tuple(sections),duration=elapsed,
                waves=tuple(sorted(waves,key=lambda w:w['at'])),next_scene=next_scene,stage_number=2)


def stage2_course(seed=7,candidates=None):
    return compile_route(stage2_plan())


def practice_courses():
    return dict(stage2=stage2_course(),
                rocks=compile_route((stage2_plan()[0],),'ASTEROID / PRACTICE','2面 / 岩配置確認','retry'),
                missiles=compile_route((section('missile','HOMING / PRACTICE','FLASH / DODGE / CUT',
                    ((1,'missile',176,'launch'),(10,'missile',64,'launch'),
                     (18,'rock_row',0,'center_gap'),(20,'missile',192,'launch')),30),),
                    'MISSILE / PRACTICE','2面 / ミサイル確認','retry'),
                stealth=compile_route((section('boss','STEALTH CHAIN','DESTROY EVERY AIRCRAFT',(),0),),
                    'STEALTH / PRACTICE','2面 / 連結編隊ボス確認'))


def steer_missile(b,px,py,dt):
    """追尾は短時間だけ、最大旋回量を超えない。ロック後は直進。"""
    b.age+=dt
    turn_dt=min(dt,max(0,b.homing_remaining))
    if turn_dt:
        angle=math.atan2(b.vy,b.vx);target=math.atan2(py-b.y,px-b.x)
        delta=(target-angle+math.pi)%(2*math.pi)-math.pi
        limit=math.radians(MISSILE['turn_degrees_second'])*turn_dt
        angle+=max(-limit,min(limit,delta))
        b.vx,b.vy=math.cos(angle)*MISSILE['speed'],math.sin(angle)*MISSILE['speed']
    b.homing_remaining=max(0,b.homing_remaining-dt)
