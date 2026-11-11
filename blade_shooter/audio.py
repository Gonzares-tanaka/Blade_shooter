"""BGMは0/1/2、SEは3/4。道中・ボス・SEはEditor原本のpyxres。"""
from pathlib import Path
import config as C


def load_stage_bgm(p):
    # Pyxel 2.9.9のsave/loadはMMLを保持しないので、毎回原文から設定する。
    path=Path(__file__).resolve().parent/C.STAGE_BGM_MML_FILE
    tracks=[line.strip() for line in path.read_text(encoding="utf-8-sig").splitlines()
            if line.strip() and not line.strip().startswith("https://")]
    if len(tracks)!=len(C.STAGE_BGM_SOUNDS):
        raise ValueError("stage1_MML.txt must contain four MML tracks")
    for slot,track in zip(C.STAGE_BGM_SOUNDS,tracks):p.sounds[slot].mml(track)
    p.musics[0].set(*([C.STAGE_BGM_SOUNDS[i]] for i in C.STAGE_BGM_AUDIBLE_TRACKS),[])

# 優先順位順。Sound番号、最短発音間隔（秒）。各ch最大1回/フレーム。
MOTION = (("missile_warning",10,.2),("missile_launch",21,.15),("rock_ricochet",19,.12),("boss_arrival",12,.2),("boss_warning",13,.15),("boss_fire",14,.12),("swing", 1, .08), ("erase", 3, .10),
          ("rear_warning", 10, .15), ("rear_fire", 11, .15),
          ("charge", 9, .10), ("shot", 0, .10))
IMPACT = (("rock_break",20,.08),("boss_defeat",16,.1),("boss_part_break",15,.1),("over", 8, .10), ("clear", 7, .10), ("hurt", 5, .10),
          ("pickup_heal",17,0.0),("pickup_weapon",18,0.0),
          ("cut", 2, .06), ("kill", 4, .08), ("start", 6, .10))


class Audio:
    def __init__(self, p):
        self.p, self.time = p, 0
        self.music_playing = False
        self.music_number=0
        while len(p.channels) <= max((*C.AUDIO_BGM_CHANNELS,*C.AUDIO_SE_CHANNELS)):
            p.channels.append(p.Channel())
        if C.STAGE_BGM_MODE=="mml":load_stage_bgm(p)
        self.next_play = dict.fromkeys(C.AUDIO_SE_CHANNELS,0)
        self.last_priority = dict.fromkeys(C.AUDIO_SE_CHANNELS,99)

    def update(self, game):
        self.time += 1/C.FPS
        if not C.SOUND_ENABLED:
            return
        playing = game.state == "playing"
        stage=getattr(game,"stage_definition",None)
        music=(stage.boss_bgm if stage else 1) if getattr(game,"boss",None) else (stage.bgm if stage else 0)
        if playing and (not self.music_playing or music!=self.music_number):
            if self.music_playing:
                for ch in C.AUDIO_BGM_CHANNELS:self.p.stop(ch)
            self.p.playm(music, loop=True)
            self.music_number=music
        elif not playing and self.music_playing:
            for ch in C.AUDIO_BGM_CHANNELS:self.p.stop(ch)
        self.music_playing = playing
        for ch, table in zip(C.AUDIO_SE_CHANNELS,(MOTION,IMPACT)):
            for rank, (name, sound, interval) in enumerate(table):
                if name in game.events:
                    if self.time >= self.next_play[ch] or rank < self.last_priority[ch]:
                        self.p.play(ch, sound)
                        self.next_play[ch] = self.time+interval
                        self.last_priority[ch] = rank
                    break
