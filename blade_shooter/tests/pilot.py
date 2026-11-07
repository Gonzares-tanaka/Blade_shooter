"""検証専用の自動入力。ゲーム配布物には含めない。"""
import math
import config as C
from game import Actions


def pilot_action(g, blade=False, rear_first=False):
    if g.state in ("title", "gameover", "clear"):
        return Actions(confirm=True)
    if g.boss:return boss_action(g,blade)
    armor = next((e for e in g.enemies if e.kind == "armor" and e.y >= 40 and e.age < 8.5), None)
    charger=next((e for e in g.enemies if e.kind=='charger' and e.y<g.py and e.phase!='entry'),None)
    members=[e for e in g.enemies if e.kind=='small' and e.group and e.y<g.py-20]
    rear=next((e for e in g.enemies if e.kind=='rear' and e.phase=='exit' and 40<e.y<g.py-25),None)
    attack=False
    if blade and armor and armor.resting:
        tx, ty = armor.x, armor.y+54
    elif blade and armor:
        tx, ty = armor.x+(62 if armor.x<128 else -62), C.ARMOR_Y+92
    else:
        target = armor or next((e for e in g.enemies if e.damageable and e.y < g.py-40), None)
        tx, ty = (target.x if target else 128), 275
    if blade and charger:
        ty=245
        tx=charger.x+charger.vx*(ty-charger.y)/(charger.vy or 1)
        tx=max(20,min(236,tx))
        attack=charger.phase=='dash' and abs(g.px-charger.x)<27 and 34<g.py-charger.y<76
    elif blade and members and not armor:
        group=[e for e in members if e.group==members[0].group]
        tx=sum(e.x for e in group)/len(group)
        cy=sum(e.y for e in group)/len(group)
        ty=max(84,min(260,cy+54))
        attack=abs(g.px-tx)<14 and 33<g.py-cy<65
    if rear_first and rear:
        tx,ty=rear.x,min(300,rear.y+60)
        attack=blade and abs(g.px-rear.x)<20 and 32<g.py-rear.y<72
    if not blade or not (armor and armor.resting):
        # 予告された上向きの射線を見て早めに離れる、ショット＋回避ルート。
        lanes={e.x for e in g.enemies if e.kind=='rear' and e.phase in ('marker','entry','warning','fire') and g.py<e.y}
        lanes.update(b.x for b in g.bullets if b.source=='rear' and b.y>min(g.py,ty)-20)
        for lane in sorted(lanes):
            if abs(tx-lane)<32:
                tx=lane-42 if lane>=128 else lane+42
    slash = bool(blade and g.cooldown<=0 and (attack or
                 armor and armor.resting and abs(g.px-armor.x)<22 and 30<g.py-armor.y<78))
    return steer(g,tx,ty,slash)


def steer(g,tx,ty,slash=False,precision=False):
    choices = []
    for ax, ay in ((0,0),(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,-1),(-1,1),(1,1)):
        length = max(1, math.hypot(ax, ay))
        nx = max(8,min(248,g.px+ax/length*g.player_speed*0.24))
        ny = max(32,min(312,g.py+ay/length*g.player_speed*0.24))
        nav=.06 if precision else .24
        cost = math.hypot(g.px+ax/length*g.player_speed*nav-tx,
                          g.py+ay/length*g.player_speed*nav-ty)*0.5
        for b in g.bullets:
            # 反応時間込みの予測。無敵・弾消し等の検証用優遇は使わない。
            for t in (0.08,0.16,0.24,0.4):
                px = max(8,min(248,g.px+ax/length*g.player_speed*t))
                py = max(32,min(312,g.py+ay/length*g.player_speed*t))
                distance = math.hypot(px-b.x-b.vx*t, py-b.y-b.vy*t)
                cost += max(0, 23-distance)**2*2
        for e in g.enemies:
            cost += max(0,e.radius+21-math.hypot(nx-e.x,ny-e.y))**2*3
            if e.kind=='small':
                fy=e.y+C.FORMATION_PATTERNS[e.pattern]['speed']*.24
                cost+=max(0,e.radius+20-math.hypot(nx-e.x,ny-fy))**2*4
            if e.kind=='rear' and e.phase=='exit':
                cost+=max(0,e.radius+20-math.hypot(nx-e.x,ny-e.y+C.REAR_EXIT_SPEED*.24))**2*4
            if e.kind=='charger' and e.phase in ('warning','dash'):
                wait=max(0,C.CHARGER_WARNING_SECONDS-e.phase_time) if e.phase=='warning' else 0
                for t in (.08,.16,.24,.4):
                    px=max(8,min(248,g.px+ax/length*g.player_speed*t))
                    py=max(32,min(312,g.py+ay/length*g.player_speed*t))
                    travel=max(0,t-wait)
                    distance=math.hypot(px-e.x-e.vx*travel,py-e.y-e.vy*travel)
                    cost+=max(0,e.radius+17-distance)**2*4
        choices.append((cost,ax,ay))
    _, ax, ay = min(choices)
    return Actions(x=ax,y=ay,slash=slash)


def boss_action(g,blade=True,order=('center','left','right')):
    b=g.boss
    target=next((p for key in order for p in b.parts if p.key==key and p.hp>0),None)
    if target is None:return Actions()
    if not b.active:return steer(g,128,276,precision=True)
    approach=blade and b.opening
    tx,ty=target.x,target.y+52 if approach else 274
    attack=approach and abs(g.px-target.x)<18 and 32<g.py-target.y<72
    # 前方に残った弾も、実際の斬撃入力で切り開く。無敵や弾の削除は使わない。
    cut=blade and any(32<g.py-bullet.y<68 and abs(g.px-bullet.x)<32 for bullet in g.bullets)
    return steer(g,tx,ty,slash=g.cooldown<=0 and (attack or cut),precision=True)
