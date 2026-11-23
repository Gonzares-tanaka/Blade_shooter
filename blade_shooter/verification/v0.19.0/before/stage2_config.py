"""第2面の調整表。秒・ゲームpx・px/秒。固定配置、乱数は使用しない。"""
import math

ROCK = dict(radius=12.0, hp=1, speed=68.0, spacing=28.0, gap_width=76.0,
            drift=20.0, drift_frequency=.65, shot_spark_seconds=.10)
# 旧横列の回帰確認用。本道中・個別コースの配置は下のROCK_FLOWSを使う。
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
               delay=.78, bullet_speed=126.0,
               cross_speed=150.0, break_speed=174.0,
               wing_offset=14.0, open_seconds=.95,
               part_points=2000, defeat_points=8000)

# 終点・所要秒・状態。速度は距離/秒で決まり、急加速の前に0.7秒の予告を置く。
STEALTH_START=(48.0,82.0)
STEALTH_ROUTE=(
    (1.80,(176.0,82.0),'cruise'), (.70,(202.0,90.0),'turn_warning'),
    (.85,(54.0,170.0),'sweep'), (1.50,(78.0,172.0),'open'),
    (.70,(96.0,166.0),'break_warning'), (.65,(212.0,64.0),'escape'),
    (1.50,(80.0,64.0),'cruise'), (.70,(54.0,72.0),'turn_warning'),
    (.75,(202.0,170.0),'sweep'), (1.50,(178.0,172.0),'open'),
    (.70,(160.0,166.0),'break_warning'), (.65,STEALTH_START,'escape'))
# 射撃時計は編隊全体で共通。移動時計・HPは従来どおり。
# 先頭3機(予告0.7+射撃1.3) / 全休止5 / 後尾3機 / 全休止5 = 14秒。
STEALTH_ATTACK=dict(group_size=3, warning=.70, fire_seconds=1.30, rest_seconds=5.0,
                    stagger=.20, residual_seconds=.65,
                    bursts=((0.0,'cross'),(.32,'break'),(.64,'trail')),
                    cross_offsets=(-20,0,20),break_offsets=(-11,11),trail_offsets=(-12,0,12))
STEALTH_ATTACK['half_cycle']=sum(STEALTH_ATTACK[k] for k in ('warning','fire_seconds','rest_seconds'))
STEALTH_ATTACK['cycle']=2*STEALTH_ATTACK['half_cycle']
assert max(at for at,_ in STEALTH_ATTACK['bursts'])+(STEALTH_ATTACK['group_size']-1)*STEALTH_ATTACK['stagger']<STEALTH_ATTACK['fire_seconds']
elapsed=0.0;opens=[];warnings=[]
for duration,_,kind in STEALTH_ROUTE:
    if kind=='open':opens.append((round(elapsed,8),round(elapsed+min(duration,STEALTH['open_seconds']),8)))
    if kind.endswith('warning'):warnings.append((elapsed,elapsed+duration))
    elapsed+=duration
STEALTH['cycle']=round(elapsed,8)
STEALTH['open_windows']=tuple(opens)
STEALTH['break_warning_windows']=tuple(warnings)
# グループ先頭機の発射時刻。後続機はstaggerだけずれる。
STEALTH_FIRE=tuple((STEALTH_ATTACK['warning']+at,style) for at,style in STEALTH_ATTACK['bursts'])

# (時差, x, y, vx, vy, 半径, 回転度/秒)。端の高速岩は全て予告後に動く。
ROCK['edge_warning']=.85
ROCK_FLOWS={
    'cut_cross':((0,100,-24,0,68,12,35),(.18,128,-24,0,68,12,-28),
                 (.36,156,-24,0,68,12,42),(3.6,-20,232,138,36,8,-110),
                 (4.8,276,190,-112,38,8,95)),
    'diagonal':((0,40,-24,36,76,12,35),(.5,218,-24,-32,62,18,-22),
                (1.2,94,-24,26,114,8,105),(2.1,230,-24,-46,98,8,-85),
                (2.8,16,-24,22,68,12,50)),
    'crossing':((0,-24,122,102,42,12,-70),(.6,-20,210,128,42,8,110),
                (1.4,280,150,-106,36,12,55),(2.1,276,232,-128,-10,8,-120),
                (3.2,72,-24,16,88,8,90)),
    'large_wake':((0,76,-24,8,38,18,14),(.45,180,-24,-8,42,18,-18),
                  (.9,38,-24,18,122,8,130),(1.4,128,-24,0,118,8,-110),
                  (1.9,218,-24,-18,126,8,95),(3.2,250,-24,-24,86,12,-40)),
    'wait_gap':((0,100,-24,-6,44,18,-18),(.5,156,-24,6,44,18,16),
                (1.8,64,-24,-10,110,8,100),(2.2,192,-24,10,106,8,-100),
                (3.7,128,-24,0,68,8,125)),
    'shear':((0,-20,180,116,18,8,110),(.4,128,-24,0,46,18,16),
              (1.6,280,238,-96,-18,12,-60),(2.2,72,-24,24,104,8,-115),
              (3.4,220,-24,-32,88,12,45))}


def rock_position(e,age=None):
    """実体と予測表示が使う同じ軌道。marker中は停止、接触判定なし。"""
    age=e.age if age is None else age
    if e.pattern in ROCK_FLOWS:
        t=max(0,age-e.warning_duration)
        return e.home_x+e.vx*t,e.home_y+e.vy*t
    p=ROCK_PATTERNS[e.pattern]
    return e.home_x+p['direction']*ROCK['drift']*math.sin(age*ROCK['drift_frequency']),e.home_y+p['speed']*age

# 6区間×30秒。各区間長を変えても後続の時刻・アイテム時刻は再計算する。
AREA_SECONDS = (30.0,30.0,30.0,30.0,30.0,30.0)

def rock_row(pattern):
    p=ROCK_PATTERNS[pattern]
    return tuple(x for x in (16+i*ROCK['spacing'] for i in range(9))
                 if abs(x-p['gap'])>=ROCK['gap_width']/2)


def section(key,title,hint,waves,length):
    return dict(key=key,title=title,hint=hint,waves=tuple(waves),length=length)


def stage2_plan():
    flows=lambda times,names:tuple((t,'rock_flow',0,names[i%len(names)]) for i,t in enumerate(times))
    return (
        section('rocks','01 / CUT THEN SIDESTEP','CUT FRONT / WATCH THE SIDE',
                flows((1,9,17,24),('cut_cross','diagonal','wait_gap','large_wake'))+
                ((12,'formation',184,'diagonal_r'),(24,'formation',64,'diagonal_l')),AREA_SECONDS[0]),
        section('missile','02 / READ THE WAKE','LET THE FRONT PASS / CHOOSE THE GAP',
                ((1,'missile',176,'launch'),(10,'missile',64,'launch'),
                 (17,'formation',184,'line'),(24,'missile',192,'launch'))+
                flows((10,18,25),('wait_gap','large_wake','diagonal')),AREA_SECONDS[1]),
        section('crossing','03 / CROSSING STREAMS','SIDE SIGNAL / CHANGE YOUR ROUTE',
                flows((0,7,14,22),('crossing','diagonal','shear','crossing'))+
                ((3,'formation',64,'line'),(11,'missile',192,'launch'),
                 (18,'formation',184,'diagonal_r'),(25,'missile',64,'launch')),AREA_SECONDS[2]),
        section('armor','04 / FAST ROCKS / SLOW ROCKS','WATCH THE WAKE / ARMOR OPENINGS',
                flows((0,7.4,15,23),('large_wake','wait_gap','diagonal','large_wake'))+
                ((2,'armor',64,'hold'),(10,'formation',184,'line'),(16,'armor',192,'hold'),
                 (22,'missile',64,'launch')),AREA_SECONDS[3]),
        section('intercept','05 / SHEAR CURRENT','CUT ONE THREAT / LEAVE A SIDE EXIT',
                flows((0,7,14.5,22),('shear','crossing','cut_cross','diagonal'))+
                ((3,'charger',64,'lock'),(10,'missile',192,'launch'),(17,'formation',64,'line'),
                 (25,'charger',192,'lock')),AREA_SECONDS[4]),
        section('mix','06 / STAGGERED APPROACH','ROCK FIRST / MISSILE AFTER / MOVE',
                flows((0,8,16,23),('large_wake','crossing','wait_gap','shear'))+
                ((2.8,'missile',192,'launch'),(6,'formation',64,'diagonal_l'),
                 (11,'armor',64,'hold'),(18.8,'missile',64,'launch'),(26,'formation',184,'line')),AREA_SECONDS[5]),
    )


def compile_route(plan,label='STAGE 2 / ASTEROID BELT',menu='2面 / アステロイド帯',next_scene='boss'):
    waves=[];sections=[];elapsed=0.0
    for part in plan:
        sections.append((elapsed,part['title'],part['hint']))
        for at,kind,x,pattern in part['waves']:
            # 短く調整した区間の末尾を越える編隊は生成しない。
            if 0<=at<part['length']:
                if kind=='rock_flow':
                    for spec in ROCK_FLOWS[pattern]:
                        lag,rx,ry,vx,vy,radius,spin=spec
                        if at+lag>=part['length']:continue
                        waves.append(dict(at=elapsed+at+lag,kind='rock',x=rx,pattern=pattern,
                                          rock=(rx,ry,vx,vy,radius,spin),section=part['key']))
                else:waves.append(dict(at=elapsed+at,kind=kind,x=x,pattern=pattern,section=part['key']))
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
                     (18,'rock_flow',0,'shear'),(20,'missile',192,'launch')),30),),
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
