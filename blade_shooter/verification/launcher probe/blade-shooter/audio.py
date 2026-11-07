"""BGMは0/1、SEは2/3。音の内容はpyxresだけで編集する。"""
import config as C

# 優先順位順。Sound番号、最短発音間隔（秒）。各ch最大1回/フレーム。
MOTION = (("boss_arrival",12,.2),("boss_warning",13,.15),("boss_fire",14,.12),("swing", 1, .08), ("erase", 3, .10),
          ("rear_warning", 10, .15), ("rear_fire", 11, .15),
          ("charge", 9, .10), ("shot", 0, .10))
IMPACT = (("boss_defeat",16,.1),("boss_part_break",15,.1),("over", 8, .10), ("clear", 7, .10), ("hurt", 5, .10),
          ("cut", 2, .06), ("kill", 4, .08), ("start", 6, .10))


class Audio:
    def __init__(self, p):
        self.p, self.time = p, 0
        self.music_playing = False
        self.music_number=0
        self.next_play = {2: 0, 3: 0}
        self.last_priority = {2: 99, 3: 99}

    def update(self, game):
        self.time += 1/C.FPS
        if not C.SOUND_ENABLED:
            return
        playing = game.state == "playing"
        music=1 if getattr(game,"boss",None) else 0
        if playing and (not self.music_playing or music!=self.music_number):
            self.p.playm(music, loop=True)
            self.music_number=music
        elif not playing and self.music_playing:
            self.p.stop(0)
            self.p.stop(1)
        self.music_playing = playing
        for ch, table in ((2, MOTION), (3, IMPACT)):
            for rank, (name, sound, interval) in enumerate(table):
                if name in game.events:
                    if self.time >= self.next_play[ch] or rank < self.last_priority[ch]:
                        self.p.play(ch, sound)
                        self.next_play[ch] = self.time+interval
                        self.last_priority[ch] = rank
                    break
