"""Open the unmodified official Editor and select every newly used sound/music."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pyxel as p
from pyxel.editor import App
import config as C
root=Path(__file__).resolve().parents[1];folder=root/'verification'/('v'+C.VERSION)/'standard-editor'
folder.mkdir(parents=True,exist_ok=True)
original_run=p.run;cases=[(2,n) for n in (22,23,32,33,34,35,62,63)]+[(3,n) for n in (4,5,6)]
results=[];frame=0

def run(update,draw):
    global app
    app=update.__self__;original_run(tick,draw)
def tick():
    global frame
    frame+=1
    if frame%3:return
    index=(frame//3)-1
    if index>=len(cases):
        assert len(p.sounds)==p.NUM_SOUNDS==64
        (folder/'result.json').write_text(json.dumps(dict(result='PASS',official_editor=True,
            sound_count=64,saved_original=False,cases=results),indent=2),encoding='utf8')
        print('STANDARD_EDITOR_PASS',flush=True);p.quit();return
    kind,slot=cases[index];app.editor_type_var=kind;editor=app._editors[kind]
    if kind==2:
        editor.sound_index_var=slot;assert editor.sound_index_var==slot
        assert p.sounds[slot].notes and len(p.sounds[slot].notes)<=48
    else:editor.music_index_var=slot;assert editor.music_index_var==slot
    app.draw_all();p.screenshot(str(folder/(('sound-' if kind==2 else 'music-')+str(slot)+'.png')),scale=2)
    results.append(dict(editor=kind,slot=slot))
p.run=run
App(str(root/C.RESOURCE_FILE),'sound')
