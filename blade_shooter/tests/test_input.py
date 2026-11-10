import sys
from pathlib import Path
import unittest
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import config as C
from main import Input,App
from game import Game


class FakePyxel:
    def __init__(self):
        names=sorted({k for m in (C.KEYBOARD_INPUTS,C.GKD_INPUTS) for keys in m.values() for k in keys})
        for i,k in enumerate(names): setattr(self,k,i+1)
        self.held=set(); self.edges=set(); self.exited=False
    def btn(self,k): return k in self.held
    def btnp(self,k): return k in self.edges
    def quit(self): self.exited=True


class InputTests(unittest.TestCase):
    def test_gkd_profile_isolated_and_edge_triggered(self):
        p=FakePyxel();i=Input(p,'gkd')
        p.held={p.KEY_Z};p.edges=set(p.held)
        self.assertFalse(i.read().slash)
        p.held={p.GAMEPAD1_BUTTON_A};p.edges=set(p.held)
        self.assertTrue(i.read().slash)
        p.edges.clear()
        self.assertFalse(i.read().slash)

    def test_select_exits_all_states_including_hitstop(self):
        for state in ('title','settings','playing','paused','gameover','clear','stage_clear','result'):
            app=App.__new__(App)
            p=FakePyxel();p.held={p.GAMEPAD1_BUTTON_BACK};p.edges=set(p.held)
            app.p,app.input,app.game=p,Input(p,'gkd'),Game()
            app.game.state=state;app.game.hitstop=.05
            app.update()
            self.assertTrue(p.exited)
            self.assertEqual(app.game.state,state)

    def test_gkd_result_select_title_then_start_with_a(self):
        p=FakePyxel();i=Input(p,'gkd');g=Game();g.reset();g.hp=1;g.hurt()
        p.held={p.GAMEPAD1_BUTTON_DPAD_DOWN};p.edges=set(p.held)
        g.step(.01,i.read());self.assertEqual(g.result_choice,1)
        p.held={p.GAMEPAD1_BUTTON_A};p.edges=set(p.held)
        g.step(.01,i.read());self.assertEqual(g.state,'title')
        p.held.clear();p.edges.clear();g.step(.01,i.read())
        p.held={p.GAMEPAD1_BUTTON_A};p.edges=set(p.held)
        g.step(.01,i.read());self.assertEqual((g.state,g.hp,g.score),('playing',3,0))

    def test_bridge_movement_consumed_once_and_focus_releases_keys(self):
        p=FakePyxel();i=Input(p,'web')
        i.bridge=SimpleNamespace(slashSerial=0,confirmSerial=0,pauseSerial=0,focusSerial=0,
                                 dragX=10,dragY=-20,suspended=False)
        action=i.read()
        self.assertEqual((action.drag_x,action.drag_y),(10,-20))
        # 前のreadが両成分を消費する。
        self.assertEqual(i.read().drag_x,0)
        p.held={p.KEY_LEFT};i.bridge.focusSerial+=1;i.bridge.suspended=True
        self.assertTrue(i.read().focus_lost)
        i.bridge.suspended=False
        self.assertEqual(i.read().x,0)
        p.held.clear();i.read();p.held={p.KEY_LEFT}
        self.assertEqual(i.read().x,-1)

    def test_web_course_pulse_is_consumed_once(self):
        i=Input(FakePyxel(),'web')
        i.bridge=SimpleNamespace(slashSerial=0,confirmSerial=0,pauseSerial=0,focusSerial=0,
                                 courseSerial=1,sectionSerial=1,dragX=0,dragY=0,suspended=False)
        self.assertTrue(i.read().course)
        self.assertFalse(i.read().course)
        i.bridge.sectionSerial+=1
        self.assertEqual(i.read().section,1)
        self.assertEqual(i.read().section,0)

    def test_settings_transition_releases_held_physical_direction(self):
        app=App.__new__(App);p=FakePyxel();app.p=p;app.input=Input(p,'gkd');app.game=Game()
        app.audio=SimpleNamespace(update=lambda game:None)
        app.store=SimpleNamespace(failed=False,save=lambda score:True)
        p.held={p.GAMEPAD1_BUTTON_B,p.GAMEPAD1_BUTTON_DPAD_RIGHT};p.edges=set(p.held)
        app.update();self.assertEqual(app.game.state,'settings')
        p.edges.clear();app.update();self.assertEqual(app.game.weapon,'blade')
        p.held.clear();app.update()
        p.held={p.GAMEPAD1_BUTTON_DPAD_RIGHT};p.edges=set(p.held);app.update()
        self.assertEqual(app.game.weapon,'axe')

    def test_reset_discards_only_attack_queued_before_reset(self):
        p=FakePyxel();i=Input(p,'web')
        i.bridge=SimpleNamespace(slashSerial=1,cancelSlashSerial=1,inputResetSerial=1,
                                 dragX=0,dragY=0,suspended=False)
        self.assertFalse(i.read().slash)
        # A fresh press after the reset must not be swallowed by its next frame.
        p.held={p.KEY_RIGHT};p.edges=set(p.held)
        i.bridge.inputResetSerial+=1;i.bridge.slashSerial=2
        a=i.read();self.assertTrue(a.slash);self.assertEqual(a.x,1)


if __name__=='__main__': unittest.main()
