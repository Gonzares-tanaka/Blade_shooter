# BLADE / CLOSE QUARTERS 0.3.0

256×320、80秒生存のPyxel試作です。移動と斬撃だけで、装甲・編隊・突進の異なる判断を試します。
子機、ボス、武器強化、成長、アイテムはありません。子機版 `../../shooting_1` は変更していません。

## PCですぐ遊ぶ

作業フォルダ `C:\temp\mypyxel\shooting_2` から実行します。

```powershell
powershell -ExecutionPolicy Bypass -File .\blade_shooter\run.ps1
```

専用 `.venv` がなければ既存の子機版の `.venv` を使用します。
新しい環境を作る場合は、このREADMEがある `blade_shooter/` で次を実行します。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

開発確認はPython 3.12 / Pyxel 2.9.9です。Pyxel Editorも同じ2.9.9を使います。

## 操作

| 操作 | PC / Webキーボード | Web / iPhoneタッチ | GKD Pixel 2 |
|---|---|---|---|
| 移動 | 十字キー | ドラッグした移動量に応じた相対移動 | 十字キー |
| 斬撃 | Z | ダブルタップ | A |
| 開始・リトライ | Enter / Z | 上部の開始・もう一度 | START / A |
| 一時停止・再開 | P（再開はEnterも可） | 上部の一時停止・再開 | START |
| 終了 | Esc | タブを閉じる | SELECTで即終了してPortsへ |

通常ショットは自動ですが、剣を振る全動作の間は新規発射を止めます。発射済みの味方弾は残ります。
Z/Aの押しっぱなしは連斬になりません。SELECTはタイトル・停止・結果・ヒットストップ中にも有効です。
タッチした位置へワープせず、指の移動量だけを使います。仮想十字キー・攻撃ボタンはありません。
往復ドラッグ、長押し、複数指をダブルタップに数えません。操作設定と誤認防止の値は前版から維持しています。

## 80秒の固定テスト区間

| 区間 | 出現時刻 | 試すこと |
|---|---|---|
| 0〜16秒：装甲敵 | 2秒、中央に1機 | 赤いFIRINGを見て待ち、青緑のOPEN中に近づいて一撃 |
| 16〜36秒：小型編隊 | 18秒・25秒、各3機 | 紫の逆三角3機へ位置を合わせ、一振りで巻き込む |
| 36〜56秒：突進敵 | 38秒・45秒、各1機 | ピンクの予備動作と固定の点線を見て、引きつけて斬るか横へ避ける |
| 56〜80秒：混成 | 58/62/67/69/72/74秒 | 少数の組み合わせ。弾を斬って穴を作り、移動して抜ける |

区間名とヒントを画面上部へ表示します。次の敵まで数秒の余白があり、敵も弾もいなければBREATHERと表示します。
出現順・時刻は固定です。時間だけで生存クリアし、敵を全滅させる必要はありません。
突進敵は入場後、**予告開始時の自機位置で方向を固定**します。1.2秒予告し、突進中も追尾しません。
小型編隊は同じ相対配置で飛び、一度だけ薄い射撃を行います。装甲敵の周りに密な弾幕は追加していません。

装甲HP32は通常弾32発（連続命中で約4.5秒）、斬撃威力40なら一撃です。
編隊は各HP2、突進敵はHP24。すべて通常ショットでも倒せます。突進は回避だけでも対処できます。

## 近接戦闘の維持値

- 自機16×16、HP3、敵弾に対する判定は中央の白点・半径2px。敵本体には機体の外周で接触します。
- 斬撃は支点から30〜60px、幅4px、左前方から右前方へ150度。
- 振り始め0.07秒・有効0.10秒・振り終わり0.24秒。全区間で新規ショット停止。
- 振り始めと振り終わりには攻撃・弾消し判定がなく、移動は可能です。
- 再使用1.0秒、威力40、命中停止0.05秒。これらは調整済み0.2.0から変更していません。
- 攻撃は実際に刃が通った場所と時間のみ。前フレームの軌跡は次のフレームを保護しません。
- 自機移動と刃の回転、敵弾の移動を短い時間区間で照合し、すり抜けを防ぎます。
- 同じ敵への斬撃ダメージは一振り1回。斬撃による無敵、突進する自機、消せない弾はありません。
- 横・後方・刃の内側の弾、斬ったあとに来る弾には回避が必要です。

## Editorで画像・音楽・SEを編集する

**原本は `assets/blade.pyxres`。52色パレットは同じ場所の同名 `assets/blade.pyxpal` です。**
起動時は読み込むだけで、画像やSound/Musicをコードで再生成しません。
ビルドも原本のバイト列をそのままコピーします。Editorで保存した変更を上書きしません。

作業フォルダから：

```powershell
powershell -ExecutionPolicy Bypass -File .\blade_shooter\edit.ps1
```

または `blade_shooter/` から、インストール済みPythonで直接開きます。

```powershell
..\..\shooting_1\.venv\Scripts\python.exe -m pyxel edit assets\blade.pyxres
```

1. Image / Sound / Musicのタブを選んで編集します。
2. Ctrl+Sまたは上部の保存アイコンで保存します。
3. ゲームを再起動して確認します。起動中の自動再読込は行いません。
4. Web/GKDへ反映するには、下記のビルドを実行します。

`.pyxpal` は色番号0〜51を順番どおり52行のRGB16進数で保持します。並べ替え・16色化をしないでください。
Editor 2.9.9は同名の `.pyxpal` を読み、52色の選択欄を表示します。ゲームも同じファイルを読みます。
`config.py` の `PALETTE` と異なる順序のパレットはビルド時に検出します。色番号0はスプライトの透明色です。
パレットの仕様：[Pyxel公式FAQ](https://github.com/kitao/pyxel/blob/main/docs/faq-ja.md)。

### イメージ配置表

すべて **Image Bank 0**。座標は左上 `(u,v)`、大きさは `幅×高さ` です。Bank 1/2は未使用で自由領域です。

| 素材 | 座標 | 大きさ |
|---|---|---|
| 自機 | (0,0) | 16×16 |
| 腕テクスチャ | (16,0) | 8×4 |
| 刃テクスチャ | (32,0) | 30×4 |
| 小型編隊の1機 | (64,0) | 16×16 |
| 味方弾 | (80,0) | 4×8 |
| 敵弾 | (88,0) | 8×8 |
| 腕の関節 | (96,0) | 4×4 |
| 噴射炎 | (104,0) | 8×8 |
| 背景の星 | (128,0) | 16×16 |
| スクロールするレーン | (144,0) | 8×16 |
| 装甲敵・発射中 | (0,32) | 32×32 |
| 装甲敵・停止中 | (32,32) | 32×32 |
| 突進敵・入場 | (64,32) | 24×24 |
| 突進敵・予告 | (88,32) | 24×24 |
| 突進敵・突進 | (112,32) | 24×24 |
| 斬撃命中火花 | (0,80) | 16×16 |
| 弾消去火花 | (16,80) | 8×8 |
| 通常撃破 | (24,80) | 16×16 |
| 被弾 | (40,80) | 16×16 |
| 両断の光 | (56,80) | 16×16 |

両断される敵本体には、その敵のスプライトを左右半分ずつ使います。
腕・刃は原本の画素を幾何上の実寸へ投影します。リソースのバンクには書き込みません。
当たり判定は設定した寸法で決まり、Editorで絵の輪郭を変えても自動変更されません。大きく描き替えるときは `config.py` の半径・刃寸法も合わせます。

コード描画を残した部分：刃の掃引軌跡、突進の点線・照準・文字、HUD・HP・敵HP、枠線、命中フラッシュ枠、動く火花の追加線、画面揺れ。
星やレーン、主要エフェクトの元画像、機体・腕・剣・敵・弾はすべてリソースを参照します。

### Sound / Musicとチャンネル

| Sound番号 | 用途 |
|---|---|
| 0 | 通常ショット |
| 1 | 空振り・剣を振る音 |
| 2 | 斬撃命中 |
| 3 | 弾消し |
| 4 | 敵撃破（通常ショット） |
| 5 | 自機被弾 |
| 6 | 開始・リトライ |
| 7 | ステージクリア |
| 8 | ゲームオーバー |
| 9 | 突進開始 |
| 32 / 33 | BGMのメロディ素材 |
| 34 / 35 | BGMのベース素材 |

**Music 0** が短い仮BGMです。現在はCH0=`33,32,33`、CH1=`34,35`。Editorで順番や音符を編集できます。
MusicのCH2/CH3は空のままにしてください。SE用に予約しています。

| 音声チャンネル | 役割・同時発生時の優先順位（左が高い） |
|---|---|
| 0 | BGMメロディ。SEからは使用しない |
| 1 | BGMベース。SEからは使用しない |
| 2 | 空振り → 弾消し → 突進開始 → ショット |
| 3 | ゲームオーバー → クリア → 被弾 → 斬撃命中 → 通常撃破 → 開始 |

同じイベントが複数機・複数弾から来ても各チャンネル最大1回/フレームです。
弾消しは最短0.10秒、斬撃命中は0.06秒、通常撃破は0.08秒の間隔を置きます。高優先のSEは低優先音を中断できます。
斬撃で複数機を倒した場合は斬撃命中を優先し、撃破数だけSEを重ねません。
SEのためにBGMを停止しません。一時停止・タイトル・結果では意図的にBGMを停止し、再開時は先頭から再生します。

## 一か所で調整する

戦闘・出現の調整は **`config.py`** です。変更後はゲームを再起動し、配布版は再ビルドします。

| 対象 | 設定 |
|---|---|
| 敵HP | `ARMOR_HP=32`, `SMALL_HP=2`, `CHARGER_HP=24` |
| 敵弾速度 | `ARMOR_BULLET_SPEED=38`, `SMALL_BULLET_SPEED=48` px/秒 |
| 装甲射撃間隔・発射/停止時間 | `ARMOR_FIRE_INTERVAL=0.55`, `ARMOR_FIRE_SECONDS=1.65`, `ARMOR_REST_SECONDS=2.5` 秒 |
| 小型の射撃時刻 | `SMALL_FIRST_SHOT=2.0` 秒（各機1回） |
| 突進予告・速度 | `CHARGER_WARNING_SECONDS=1.2`, `CHARGER_SPEED=140` px/秒 |
| 編隊配置 | `FORMATION_OFFSETS`, `FORMATION_SWAY`, `SMALL_SPEED` |
| 出現時刻・場所 | `ARMOR_WAVES`, `FORMATION_WAVES`, `CHARGER_WAVES` |
| 区間名・開始 | `TEST_SECTIONS`, `STAGE_SECONDS=80` |
| 斬撃の範囲・時間 | `BLADE_*`（0.2.0から維持） |
| タッチ・実ボタン割当 | `WEB_TOUCH`, `KEYBOARD_INPUTS`, `GKD_INPUTS` |

## 編集後のビルドとWeb

`blade_shooter/` で実行します。ビルド自体はPython標準ライブラリのみです。

```powershell
..\..\shooting_1\.venv\Scripts\python.exe build.py
```

生成物：`dist/web/`、`dist/blade-shooter-web.zip`、`dist/blade-shooter-gkd.zip`。
`.pyxres` と `.pyxpal` はWebのpyxapp内とGKD ZIP内へ同じバイト列で収録します。
`tools/create_placeholder_resource.py` は初期作成用で、起動・ビルドから呼びません。既存原本があれば書き込まず終了します。

```powershell
python -m http.server 8000 --directory dist/web
```

PCは `http://localhost:8000/`。iPhoneは同一LANのPCのIPとポートで開きます。
最初にPyxel画面をタップして音声を有効にし、上部の開始を押します。CDNランタイムのためインターネット接続が必要です。
GitHub Pagesには `dist/web/` の中身全部を公開用 `docs/` 等へコピーします。リポジトリ配下でも動く相対URLです。
公開先リポジトリは未指定なので、今回GitHubへ公開する操作はしていません。

## GKD Pixel 2 / PlumOS

`dist/blade-shooter-gkd.zip` を展開し、次の2つを既存Portsへ並べてコピーします。

```text
Ports/
  blade-shooter.sh
  blade-shooter/
    main.py / config.py / game.py / view.py / assets.py / audio.py
    assets/
      blade.pyxres
      blade.pyxpal
    README.txt / VERIFICATION.md
```

既存の動作済みランチャー方式は変更していません。
`/storage/pyxel_Python/bin/python3 -u main.py --gkd` で実行し、SELECTで終了してPortsへ制御を戻します。
ログはランチャー横の `blade_shooter_launch.log`。権限が失われた場合は `chmod +x blade-shooter.sh` が必要です。
既存子機版とは名前が別なので共存できます。Python・OSを書き換えません。

## 検証

[VERIFICATION.md](VERIFICATION.md) に、通し確認・Editor編集反映・配布物整合性と実機未確認事項を記載しています。
GKD実機の表示・速度・ボタン・Ports復帰、iPhone Safari全体の起動と操作感は未確認です。
Windows WebKitでは以前、公式ランタイム単体でも初期化が停止しました。Edge確認と実機確認を区別しています。

```powershell
python -m unittest discover -s tests -v
node --test tests/test_gestures.cjs
python tests/check_balance.py
python tests/smoke_resources.py
python tests/smoke_desktop.py
```
