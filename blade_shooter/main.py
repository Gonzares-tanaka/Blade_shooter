# title: Blade Close Quarters
# version: 0.13.0
"""PC / GKD / Web共通入口。SELECTは状態・ヒットストップより先に処理。"""
import sys
import config as C
from game import Game, Actions
from view import View
from assets import load_resources
from audio import Audio
from persistence import BestStore


class Input:
    def __init__(self, p, profile="pc"):
        self.p, self.profile = p, profile
        mapping = C.GKD_INPUTS if profile == "gkd" else C.KEYBOARD_INPUTS
        self.keys = {name: tuple(getattr(p, k) if isinstance(k, str) else k for k in keys)
                     for name, keys in mapping.items()}
        self.bridge = None
        self.serials = {"slash": 0, "confirm": 0, "pause": 0, "focus": 0, "course": 0, "section": 0, "settings": 0, "weapon": 0, "touchMode": 0, "lab": 0, "inputReset": 0, "title":0,"retry":0,"nextStage":0}
        self.blocked = set()
        if sys.platform == "emscripten":
            from js import window
            self.bridge = window.bladeInput

    def read(self):
        held = {key for keys in self.keys.values() for key in keys if self.p.btn(key)}
        self.blocked.intersection_update(held)
        pulses, dx, dy, lost = set(), 0, 0, False
        if self.bridge is not None:
            b = self.bridge
            for name, previous in self.serials.items():
                current = int(getattr(b, name+"Serial", 0))
                if current != previous:
                    pulses.add(name)
                self.serials[name] = current
            lost = "focus" in pulses
            if lost:
                self.blocked.update(held)
            if ("inputReset" in pulses and
                    int(getattr(b,"slashSerial",0)) == int(getattr(b,"cancelSlashSerial",0))):
                pulses.discard("slash")
            dx, dy = float(b.dragX), float(b.dragY)
            b.dragX = b.dragY = 0
            if bool(b.suspended):
                held.clear()
                pulses.clear()
                dx = dy = 0
        def down(name):
            return any(k in held and k not in self.blocked for k in self.keys[name])
        def pressed(name):
            return name in pulses or any(k in held and k not in self.blocked and self.p.btnp(k) for k in self.keys[name])
        return Actions(x=int(down("right"))-int(down("left")),
                       y=int(down("down"))-int(down("up")), drag_x=dx, drag_y=dy,
                       slash=pressed("slash"), confirm=pressed("confirm"), pause=pressed("pause"),
                       focus_lost=lost, quit=pressed("quit"), course="course" in pulses,section=int("section" in pulses),
                       settings=pressed("settings"),weapon=int("weapon" in pulses),
                       touch_mode=int("touchMode" in pulses),
                       lab=int(getattr(self.bridge,"labValue",2)) if "lab" in pulses else 0,title="title" in pulses,retry="retry" in pulses,next_stage="nextStage" in pulses)


class App:
    def __init__(self):
        import pyxel
        self.p = pyxel
        self.profile = "web" if sys.platform == "emscripten" else "gkd" if "--gkd" in sys.argv else "pc"
        course,section=self.options(sys.argv[1:])
        pyxel.init(C.WIDTH, C.HEIGHT, title=C.TITLE, fps=C.FPS, quit_key=pyxel.KEY_NONE)
        load_resources(pyxel)
        if C.FULLSCREEN:
            pyxel.fullscreen(True)
        self.game, self.input, self.view = Game(course,section,self.seed_option(sys.argv[1:])), Input(pyxel, self.profile), View(pyxel, self.profile)
        self.store=BestStore(self.input.bridge)
        self.game.best_score=self.store.best
        self.game.debug="--debug" in sys.argv or bool(getattr(self.input.bridge,"debug",False))
        for flag,attribute in (("--weapon","weapon"),("--touch-mode","touch_mode")):
            if flag in sys.argv:
                value=sys.argv[sys.argv.index(flag)+1]
                choices=C.WEAPONS if attribute=="weapon" else C.TOUCH_MODES
                if value not in choices:raise ValueError("Unknown "+flag)
                setattr(self.game,attribute,value)
                if attribute=="weapon":self.game.selected_weapon=value
        self.audio = Audio(pyxel)
        pyxel.run(self.update, self.draw)

    @staticmethod
    def seed_option(args):
        if "--seed" not in args:return None
        i=args.index("--seed")
        if i+1>=len(args):raise ValueError("Missing value for --seed")
        return int(args[i+1])

    @staticmethod
    def options(args):
        course,section=C.DEFAULT_COURSE,0
        for i,arg in enumerate(args):
            if arg in ("--course","--section") and i+1>=len(args):raise ValueError("Missing value for "+arg)
            if arg=="--course":course=args[i+1]
            elif arg=="--section":section=int(args[i+1])-1
        if course not in C.COURSES:raise ValueError("Unknown course: "+course)
        if not 0<=section<len(C.COURSES[course]["sections"]):raise ValueError("Section number outside course")
        return course,section

    def update(self):
        action = self.input.read()
        if action.quit:
            self.p.quit()
            return
        previous_state=self.game.state
        self.game.step(1/C.FPS, action)
        if self.game.result is not None:self.store.save(self.game.best_score)
        self.game.save_failed=self.store.failed
        if previous_state!=self.game.state and "settings" in (previous_state,self.game.state):
            # 設定への出入りで物理キーの保持も持ち越さず、離してから再入力する。
            self.input.blocked.update(k for keys in self.input.keys.values() for k in keys if self.p.btn(k))
        if self.input.bridge is not None:
            self.input.bridge.canAdvanceStage = self.game.can_advance_stage
            self.input.bridge.state = self.game.state
            self.input.bridge.meleeReady = self.game.state=="playing" and self.game.cooldown<=1e-6 and self.game.swing<0
            self.input.bridge.weapon = self.game.weapon
            self.input.bridge.touchMode = self.game.touch_mode
            self.input.bridge.labMode = self.game.lab_mode
            self.input.bridge.course = self.game.course
            self.input.bridge.courseLabel = self.game.course_config["menu_label"]
            self.input.bridge.sectionLabel = ("最初から" if self.game.checkpoint==0 else
                                            self.game.course_config["sections"][self.game.checkpoint][1])
        self.audio.update(self.game)

    def draw(self):
        self.view.draw(self.game)


if __name__ == "__main__":
    App()
