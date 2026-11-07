"""標準ライブラリだけで共通ソースからWebとGKD ZIPを生成する。"""
from pathlib import Path
from io import BytesIO
import base64
import hashlib
import json
import zipfile
import config as C

ROOT = Path(__file__).resolve().parent
SOURCES = ("main.py", "config.py", "game.py", "boss.py", "view.py", "assets.py", "audio.py")
RESOURCES = (C.RESOURCE_FILE, C.PALETTE_FILE)


def zip_write(archive, name, data, executable=False):
    info = zipfile.ZipInfo(name, date_time=(2026, 11, 7, 0, 0, 0))
    info.create_system = 3
    info.external_attr = (0o100755 if executable else 0o100644) << 16
    archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED)


def build():
    dist = ROOT / "dist"
    web = dist / "web"
    web.mkdir(parents=True, exist_ok=True)
    contents = {name: (ROOT/name).read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8")
                for name in SOURCES}
    # Editorの原本をそのまま収録。初期生成ツールはビルドから呼ばない。
    contents.update({name: (ROOT/name).read_bytes() for name in RESOURCES})
    palette=[int(line,16) for line in (ROOT/C.PALETTE_FILE).read_text().splitlines() if line.strip()]
    if palette!=C.PALETTE:
        raise ValueError("Keep the original 52-color order in assets/blade.pyxpal")
    app = BytesIO()
    with zipfile.ZipFile(app, "w") as archive:
        zip_write(archive, "blade-shooter/.pyxapp_startup_script", b"main.py")
        for name, data in contents.items():
            zip_write(archive, f"blade-shooter/{name}", data)
    app_data = app.getvalue()
    (web/"blade-shooter.pyxapp").write_bytes(app_data)
    # 埋め込みpyxappにより、importした共通ソースを別途fetchする必要がない。
    boot = ('launchPyxel({command:"play", name:"blade-shooter.pyxapp", '
            'gamepad:"disabled", base64:' + json.dumps(base64.b64encode(app_data).decode()) + '});\n')
    (web/"boot.js").write_text(boot, encoding="utf-8", newline="\n")
    for name in ("index.html", "style.css", "gestures.js", "controls.js"):
        (web/name).write_bytes((ROOT/"web"/name).read_bytes())
    touch_config = dict(C.WEB_TOUCH, game_width=C.WIDTH, game_height=C.HEIGHT)
    (web/"touch-config.js").write_text("window.BLADE_TOUCH_CONFIG = "+json.dumps(touch_config)+";\n",
                                       encoding="utf-8", newline="\n")
    (web/".nojekyll").write_bytes(b"")
    manifest = {"version": C.VERSION, "pyxel_web_version": "2.9.9",
                "sources": {name: hashlib.sha256(data).hexdigest() for name, data in contents.items()}}
    (dist/"manifest.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
    with zipfile.ZipFile(dist/"blade-shooter-web.zip", "w") as archive:
        for path in sorted(web.iterdir()):
            zip_write(archive, path.name, path.read_bytes())
    with zipfile.ZipFile(dist/"blade-shooter-gkd.zip", "w") as archive:
        script = (ROOT/"blade-shooter.sh").read_text(encoding="utf-8").replace("\r\n", "\n")
        zip_write(archive, "blade-shooter.sh", script.encode(), True)
        for name, data in contents.items():
            zip_write(archive, f"blade-shooter/{name}", data)
        readme = (ROOT/"README.md").read_text(encoding="utf-8")
        zip_write(archive, "blade-shooter/README.txt", readme.encode("utf-8"))
        zip_write(archive, "blade-shooter/VERIFICATION.md", (ROOT/"VERIFICATION.md").read_bytes())
    print(f"Built {web} and {dist/'blade-shooter-gkd.zip'} (v{C.VERSION})")


if __name__ == "__main__":
    build()
