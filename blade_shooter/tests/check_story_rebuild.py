"""Prove text and pixel edits reach both packages without touching authoring originals."""
from pathlib import Path
import contextlib,hashlib,io,json,shutil,sys,tempfile,tomllib,zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import config as C,story as S,build
ROOT=build.ROOT

def main():
    folder=ROOT/'verification'/('v'+C.VERSION)
    originals={name:(ROOT/name).read_bytes() for name in (S.RESOURCE,S.SCENES['stage1']['file'])}
    with tempfile.TemporaryDirectory(prefix='story-edit-check-',dir=folder) as temporary:
        target=Path(temporary).resolve();assert target.is_relative_to(folder.resolve())
        for name in (*build.SOURCES,*build.RESOURCES,'README.md','VERIFICATION.md','blade-shooter.sh'):
            dest=target/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dest)
        shutil.copytree(ROOT/'web',target/'web')
        text_path=target/S.SCENES['stage1']['file']
        text_path.write_text('編集確認。\n\n---\n追加した日本語本文。\n',encoding='utf8')
        # Valid editable Pyxel resource: change Image 0 pixel (0,0) from 0 to 6.
        source=target/S.RESOURCE
        with zipfile.ZipFile(source) as z:entries={name:z.read(name) for name in z.namelist()}
        raw=entries['pyxel_resource.toml'].decode();edited=raw.replace('data = [[0]', 'data = [[6]',1)
        assert edited!=raw and tomllib.loads(edited)['images'][0]['data'][0][0]==6
        entries['pyxel_resource.toml']=edited.encode()
        with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED) as z:
            for name,data in entries.items():z.writestr(name,data)
        try:
            build.ROOT=target
            with contextlib.redirect_stdout(io.StringIO()):build.build()
        finally:build.ROOT=ROOT
        with zipfile.ZipFile(target/'dist/web/blade-shooter.pyxapp') as web,zipfile.ZipFile(target/'dist/blade-shooter-gkd.zip') as gkd:
            for name in originals:
                actual=(target/name).read_bytes()
                assert actual!=originals[name]
                assert web.read('blade-shooter/'+name)==gkd.read('blade-shooter/'+name)==actual
    assert all((ROOT/name).read_bytes()==data for name,data in originals.items())
    report=dict(result='PASS',version=C.VERSION,edited_text_and_image_reach_web_and_gkd=True,
                edited_image_pixel=dict(bank=0,x=0,y=0,before=0,after=6),original_authoring_files_unchanged=True,
                files={name:hashlib.sha256(data).hexdigest() for name,data in originals.items()})
    (folder/'story-rebuild.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report))
if __name__=='__main__':main()
