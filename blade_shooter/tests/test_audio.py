from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from audio import Audio,load_stage_bgm
import config as C


class Fake:
    def __init__(self):
        self.calls=[];self.channels=[None]*4;self.Channel=lambda:None
        self.mml={};self.music_sequences={}
        self.sounds=[SimpleNamespace(mml=lambda code,i=i:self.mml.update({i:code})) for i in range(64)]
        self.musics=[SimpleNamespace(set=lambda *seqs,i=i:self.music_sequences.update({i:seqs})) for i in range(8)]
    def playm(self,*args,**kwargs):self.calls.append(('music',args,kwargs))
    def play(self,*args,**kwargs):self.calls.append(('se',args,kwargs))
    def stop(self,*args):self.calls.append(('stop',args))


class AudioTests(unittest.TestCase):
    def test_item_pickup_uses_editable_dedicated_sound_on_sfx_channel(self):
        for event,sound in (("pickup_heal",17),("pickup_weapon",18)):
            p=Fake();a=Audio(p)
            a.update(SimpleNamespace(state='playing',events=[event,'kill','shot']))
            self.assertIn(('se',(4,sound),{}),p.calls)

    def test_sfx_never_use_bgm_channels_and_deduplicate(self):
        p=Fake();a=Audio(p)
        a.update(SimpleNamespace(state='playing',events=['erase']*30+['kill']*8+['cut']*8+['shot']))
        self.assertEqual([call[1] for call in p.calls if call[0]=='se'],[(3,3),(4,2)])
        self.assertEqual(sum(call[0]=='music' for call in p.calls),1)
        p.calls.clear()
        a.update(SimpleNamespace(state='playing',events=['erase']*20+['cut']))
        self.assertEqual(p.calls,[])

    def test_bgm_stops_only_on_state_transition(self):
        p=Fake();a=Audio(p)
        a.update(SimpleNamespace(state='playing',events=[]))
        for _ in range(20):a.update(SimpleNamespace(state='playing',events=['shot']))
        self.assertEqual(sum(call[0]=='music' for call in p.calls),1)
        self.assertFalse(any(call[0]=='stop' for call in p.calls))
        a.update(SimpleNamespace(state='paused',events=[]))
        self.assertEqual([call[1] for call in p.calls if call[0]=='stop'],[(0,),(1,),(2,)])

    def test_all_mml_tracks_load_verbatim_and_loop_without_effect_collisions(self):
        p=Fake();a=Audio(p)
        self.assertEqual(C.STAGE_BGM_MODE,'resource')
        self.assertEqual(p.mml,{})
        load_stage_bgm(p)  # 原文の完全再生も明示設定で残す。通常はEditor原本優先。
        rows=[s.strip() for s in (Path(__file__).resolve().parents[1]/C.STAGE_BGM_MML_FILE).read_text(encoding='utf-8-sig').splitlines() if s.strip() and not s.startswith('https://')]
        self.assertEqual(list(p.mml.values()),rows)
        self.assertEqual(p.music_sequences[0],([40],[41],[43],[]))
        self.assertEqual(len(p.channels),5)
        a.update(SimpleNamespace(state='playing',events=[]))
        self.assertIn(('music',(0,),{'loop':True}),p.calls)
        a.update(SimpleNamespace(state='playing',events=[],boss=object()))
        self.assertIn(('music',(1,),{'loop':True}),p.calls)
        self.assertEqual([c[1] for c in p.calls if c[0]=='stop'],[(0,),(1,),(2,)])


if __name__=='__main__':unittest.main()
