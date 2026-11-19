"""UTF-8 story data and Japanese layout. No combat or Pyxel dependency."""
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESOURCE = "assets/story.pyxres"
PALETTE = "assets/story.pyxpal"
FONT = "assets/umplus_j12r.bdf"
FONT_LICENSE = "assets/story-font-LICENSE.txt"
# All coordinates are native 256x320 pixels. Body: 10 lines of 13px glyphs.
LAYOUT = dict(x=8, y=128, width=240, lines=10, line_height=15,
              title_y=107, footer_y=286, skip=(192, 284, 56, 24))
SCENES = {
    "stage1": dict(file="assets/stage1_intro.txt", title="第1面　救出へ", image=(0,0,0,256,100)),
    "stage2": dict(file="assets/stage2_intro.txt", title="第2面　船の墓場", image=(0,0,100,256,100)),
    "stage3": dict(file="assets/stage3_intro.txt", title="第3面　敵本拠地", image=(1,0,0,256,100)),
    "ending": dict(file="assets/ending_story.txt", title="依頼完了", image=(1,0,100,256,100)),
}
# Basic Japanese line-start/end prohibition; wrapping always stays inside width.
NO_START = set("、。，．？！!?）)]｝}」』】〉》〕ぁぃぅぇぉゃゅょっァィゥェォャュョッー々…")
NO_END = set("（([｛{「『【〈《〔")

@lru_cache(maxsize=1)
def glyph_widths():
    widths = {}; code = None
    for row in (ROOT/FONT).read_text(encoding="ascii").splitlines():
        if row.startswith("ENCODING "): code = int(row.split()[1])
        elif row.startswith("DWIDTH ") and code is not None and code>=0:
            widths[chr(code)] = int(row.split()[1])
    return widths

def text_width(text):
    widths = glyph_widths()
    return sum(widths.get(char, widths.get("?", 6)) for char in text)

def wrap_line(text, width):
    if not text: return [""]
    output = []; remaining = text.expandtabs(4)
    while remaining:
        end = 0
        while end < len(remaining) and text_width(remaining[:end+1]) <= width: end += 1
        if end == 0: raise ValueError("Story width is smaller than one glyph")
        if end < len(remaining):
            # Bring a preceding character with closing punctuation to the next row.
            while end > 1 and (remaining[end] in NO_START or remaining[end-1] in NO_END): end -= 1
        output.append(remaining[:end]); remaining = remaining[end:]
    return output

def paginate(text, width=LAYOUT["width"], lines=LAYOUT["lines"]):
    if lines < 1: raise ValueError("Story needs at least one body row")
    pages = []; rows = []
    def flush():
        nonlocal rows
        pages.extend(tuple(rows[i:i+lines]) for i in range(0, len(rows), lines))
        rows = []
    for row in text.replace("\r\n", "\n").replace("\r", "\n").splitlines():
        if row == "---": flush()
        else: rows.extend(wrap_line(row, width))
    flush()
    return tuple(pages) or (("",),)

@dataclass
class Story:
    key: str
    pages: tuple
    page: int = 0

    @classmethod
    def load(cls, key):
        return cls(key, paginate((ROOT/SCENES[key]["file"]).read_text(encoding="utf-8-sig")))

    @property
    def rows(self): return self.pages[self.page]
