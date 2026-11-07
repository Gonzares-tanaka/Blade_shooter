from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from audio import Audio


class Fake:
    def __init__(self):self.calls=[]
    def playm(self,*args,**kwargs):self.calls.append(('music',args,kwargs))
    def play(self,*args,**kwargs):self.calls.append(('se',args,kwargs))
    def stop(self,*args):self.calls.append(('stop',args))


class AudioTests(unittest.TestCase):
    def test_sfx_never_use_bgm_channels_and_deduplicate(self):
        p=Fake();a=Audio(p)
        a.update(SimpleNamespace(state='playing',events=['erase']*30+['kill']*8+['cut']*8+['shot']))
        self.assertEqual([call[1] for call in p.calls if call[0]=='se'],[(2,3),(3,2)])
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
        self.assertEqual([call[1] for call in p.calls if call[0]=='stop'],[(0,),(1,)])


if __name__=='__main__':unittest.main()
