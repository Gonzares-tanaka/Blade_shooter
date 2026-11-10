"""Web=localStorage、PC/GKD=アプリ内save/best.json。失敗時もメモリ内で継続。"""
from pathlib import Path
import json,os
import config as C

class BestStore:
    def __init__(self,bridge=None,path=None):
        self.bridge=bridge
        self.path=Path(path) if path is not None else Path(__file__).resolve().parent/'save/best.json'
        self.failed=False
        self.best=self.load()

    @staticmethod
    def value(value):
        if isinstance(value,bool):return 0
        return max(0,min(999999999,int(value)))

    def load(self):
        try:
            if self.bridge is not None:return self.value(self.bridge.loadBestScore())
            if not self.path.exists():return 0
            return self.value(json.loads(self.path.read_text(encoding='utf8'))['best_score'])
        except Exception:
            self.failed=True;return 0

    def save(self,score):
        score=self.value(score)
        if score<=self.best:return not self.failed
        self.best=score  # 失敗してもこの起動中は記憶し、毎フレーム書き直さない。
        try:
            if self.bridge is not None:
                if not bool(self.bridge.saveBestScore(score)):raise OSError('localStorage unavailable')
            else:
                self.path.parent.mkdir(parents=True,exist_ok=True)
                temporary=self.path.with_suffix('.tmp')
                temporary.write_text(json.dumps(dict(schema=1,best_score=score)),encoding='utf8')
                os.replace(temporary,self.path)
            self.failed=False;return True
        except Exception:
            self.failed=True;return False
