# BLADE 超接近戦 0.18.1

256×320・全3面の近接シューティングです。左手で弾を避け、右手で残弾を斬り、射撃の隙へ踏み込みます。52色パレットと武器・敵の性能、出現表は維持しています。

## 0.18.1 ロゴ・装備武器の色

Webのロゴは、ヘッダー・メインタイトル・起動カバー・フッター・ゲーム専用画面で「/」が水色、「BLADE」が白です。

装備武器はブレイドが水色、アックスがピンク、ランスがオレンジ。待機・戻り・再使用待ちでも色を維持し、攻撃中の刃と軌跡、HUDの武器名も同系色です。`config.py: WEAPON_COLORS`に52色パレットの既存インデックスをまとめています。画像の形状・透明部分・陰影は.pyxresを使い、表示時だけ武器の色を変えます。パレットの順番、威力・リーチ・有効時間・戻り・再使用間隔・当たり判定は変更していません。

## 0.18.0 ストーリー画面

通しプレイは各面の初回開始前に導入を表示します。コンティニュー、ステージセレクト、同じ面のリトライでは導入を省略。最終ボス撃破後はCLEAR・累計スコアを5秒表示し、エンディング本文 → 既存スタッフロール → タイトルへ進みます。本文中は戦闘・面時間・CUT猶予を止めます。初期本文は1面3ページ、2面2ページ、3面2ページ、エンディング4ページです。

次へ：GKDのA／キーボードZ・Enter／画面タップ。全文スキップ：GKDのB／X／画面右下SKIPまたはWebのSKIPボタン。SELECTは本文中も終了です。ページ送りは押し直しが必要で、接触の持ち越しや余分な指ではページを進めません。戦闘への移行時も入力を解除します。

### 本文を編集する

`assets/stage1_intro.txt`、`assets/stage2_intro.txt`、`assets/stage3_intro.txt`、`assets/ending_story.txt`をUTF-8で保存してください。改行と空行を反映し、`---`だけの行で任意改ページできます。本文が長くなっても240px幅へ自動折り返し・10行単位で改ページし、コード変更は不要です。本文は12ドット日本語BDF、行間15px、上端128px。句読点と括弧の基本的な禁則処理があります。フォントはJIS日本語・英数字を収録し、絵文字や未収録の拡張漢字を使う場合は対応BDFと`story.py: FONT`を差し替えてください。

**assets/opening.txtとassets/ending.txtは音楽データです。物語本文で上書きしないでください。** 導入は既存タイトル曲、最終CLEAR・エンディング本文・スタッフロールは既存エンディング曲を使用します。本文→スタッフロールで曲を再スタートしません。GONZARES TANAKAの表記は維持しています。

### 情景画像を編集する

専用原本は`assets/story.pyxres`、同名`story.pyxpal`です。既存の戦闘・タイトル・音楽原本は上書きしません。各場面の全ページで同じ256×100を原寸表示します。

| 場面 | イメージバンク | 左上座標 | サイズ |
|---|---:|---|---|
| 1面・救出へ出撃するアストレイヤー | 0 | (0, 0) | 256×100 |
| 2面・岩と船の残骸 | 0 | (0, 100) | 256×100 |
| 3面・巨大小惑星の基地入口 | 1 | (0, 0) | 256×100 |
| エンディング・脱出する船団 | 1 | (0, 100) | 256×100 |

Pyxel Editorで`story.pyxres`の該当範囲を編集して保存し、build.pyを実行してください。52色の順番を変えないでください。別の256×100 PNGへ差し替える場合は同じ範囲へインポートできます。参考PNGは`assets/story-stage1.png`等です。これらを取り込み直すツールは`tools/import_story_assets.py`ですが、Editorでの編集後に実行すると上書きされるため通常の再ビルドでは実行しません。build.pyは保存済み.pyxresと本文をそのまま両配布物へ収録します。

仮画像は内蔵image_genで4点を生成し、256×100・既存52色へ変換して収録しました。制作プロンプトは`verification/v0.18.0/story-art-prompts.md`、フォントの出典・ライセンスは`assets/story-font-LICENSE.txt`です。

### 戦闘なしでプレビュー・配布物を更新する

```powershell
.\blade_shooter\run.ps1 --story-preview all
.\blade_shooter\run.ps1 --story-preview stage1
.\blade_shooter\run.ps1 --story-preview stage2
.\blade_shooter\run.ps1 --story-preview stage3
.\blade_shooter\run.ps1 --story-preview ending
python blade_shooter/build.py
python -m unittest discover -s blade_shooter/tests -q
python blade_shooter/tests/check_delivery.py
```

`all`は4場面を順に表示し、最後にタイトルへ戻ります。個別指定は1場面だけ表示します。通常メニューにプレビューのモードは追加しません。GKDでも`python3 main.py --gkd --story-preview all`で確認できます。Webは再生成した`dist/blade-shooter-web.zip`／`dist/web`、GKDは`dist/blade-shooter-gkd.zip`を更新してください。Pagesへの反映は変更をGitHubへpushするとワークフローが行います。

通常プレイでは敵の射線・突進経路・ボス移動先の線を非表示にしました。砲口発光、点滅、移動前の発光、下端のバックアタック予告、最終ボス初回の反射説明は残します。武器・敵HP・弾速・射撃間隔は変更していません。線の調整確認だけ必要な開発時は`--attack-guides`、または`config.py: DEBUG_ATTACK_GUIDES`で表示できます。

## 0.17.1の更新

編集済みのアイテムと1面戦艦を原本から反映しました。Image 0のアイテム4種（各16×16）、船体224×104、左右砲台24×24、中央・破壊画像32×32を参照します。武器3種と戦艦に差分があり、HP回復アイコンは前版と同じ画素です。全音源バンクの画像も同期しました。取得効果・判定、砲台のHP・射撃・破壊順は維持しています。

スタッフロールの制作担当名はすべてGONZARES TANAKAへ更新しました。役職・表示順・スクロール速度は維持。1UPは30,000／60,000／90,000点…で1機ずつです。CONTINUEの次回1UPは、復元した面開始スコアより大きい最初の30,000点の倍数から再開します。

## タイトルとモード

添付のtitle.png（256×100）をImage 2の(0,0)へ取り込み、画面上部に原寸で全体表示します。52色の既存順へ色を変換しています。ロゴ・副題の縦横比と範囲は維持しています。

- START → 通しプレイ（CAMPAIGN）：1→2→3面。面リザルトのNEXT STAGEで状態を引き継ぎ、最終ボス撃破後にCLEAR・累計スコアを5秒表示してエンディング本文、スタッフロールへ。終了後はタイトルです。
- START → ステージセレクト：1・2・3面から選び、選んだ面だけを残機3・HP3・スコア0で開始。クリア後はリザルトで終了し、次の面やスタッフロールへ自動進行しません。
- CONTINUE：全残機を失ったプレイを、その失敗した面の0秒から再開。再開情報がない場合はグレー表示。ゲームオーバーからも選択できます。
- 武器設定：X／GKDのBまたはWebの設定ボタン。左右でブレイド／アックス／ランスを選び、Z・Enter／A・Bで戻ります。

通常メニューには上記2モードだけを表示します。比較コース・途中開始・ボス直行は開発用CLIに残してあります。

## 操作

| 操作 | PC / Webキーボード | スマホWeb | GKD Pixel 2 / PlumOS |
|---|---|---|---|
| 移動 | 十字キー | 左側から触れた指でドラッグ | 十字キー |
| 近接 | Z | 右側から触れた指でフリック | A |
| メニュー選択 | 上下＋Z / Enter | 画面内の項目、または画面上のボタン | 上下＋A / START |
| 武器設定 | X | 武器設定ボタン | B |
| 一時停止 | P | 一時停止ボタン | START |
| 終了 | Escape | 紹介ページへ戻る | SELECT |

剣・斧は横フリック、槍は縦フリック。攻撃は常に前方です。左右の指の役割は接触開始地点で決め、離すまで固定。右手で移動せず、左手の高速移動では攻撃しません。余分な指は無視し、担当の自動引継ぎもしません。設定・画面遷移、タッチキャンセル、フォーカス喪失・バックグラウンド化で入力を解除します。再使用待ち中の攻撃予約はしません。

判定は表示倍率を戻した256×320のゲーム座標。`config.py: WEB_TOUCH`に境界、距離・速度・方向許容・再判定条件をまとめ、build.pyがtouch-config.jsを生成します。ページ側はtouch-actionとpreventDefaultでスクロール等の競合を抑えます。

## HP・残機・エクステンド

初期残機は現在の自機を含めて3機、1機のHPは3。実際にHPが減った瞬間だけ被弾SEを鳴らします。通常の被弾無敵は1.2秒。HP0で残機を1減らし、残機があれば同じ場面・同じ位置でHP3へ戻し、2秒の復帰無敵を付けます。敵・発射済み弾・面進行はリセットしません。HPとLIFEをHUDで別々に表示します。

スコア30,000点ごとに1機追加。1回の加点で複数の到達点を越えた場合も加算し、EXTEND表示とSE6で通知します。`RunState.next_extend`で次の到達点を管理し、重複付与を防ぎます。設定は`config.py: LIVES`。

全機を失うとゲームオーバー。CONTINUEは失敗した面の開始スコア・開始武器へ戻し、残機3・HP3でその面の道中を再開します。次の1UPは復元スコアより大きい最初の30,000点の倍数へ合わせます。現在CUTは0、最大CUTは同じプレイの記録を保持します。敵・弾・アイテム・ボスを作り直します。やり直した面の得点を二重に加算しません。面の通常クリアでは残機・HP・武器・スコア・最大CUTを引き継ぎます。

再開情報はメモリ内だけです。タイトルへ戻ってもCONTINUEできますが、新しいプレイを開始すると破棄します。アプリ終了・ページ再読込後の再開保存はありません。クリアリザルトのRETRYは、その面をスコア0・残機3から新規プレイします。

## 3面の流れ・スコア

第1面の道中300秒＋巨大戦艦、第2面180秒＋連結ステルス機、第3面150秒＋反射専用の最終ボス。道中終了後は最大2秒で通常敵と残弾を整理し、ボス登場・予告後に初撃を出します。各エリア終了の変化アイテムは0.8秒周期でHP回復／3武器へ変化し、触れた時点の種類を取得します。アイテムの滞在・出現位置はAREA_ITEM、各面表はstage2_config.py／stage3_config.py等にあります。

敵の基本点：小型100、突進200、後方250、装甲500、戦艦左右各3,000・中央5,000・撃破10,000。他の敵・ボスも`SCORING`と各面設定へ集約。ショット撃破は基本点、近接は2倍。一振りの2体目以降は各200点を追加。得点は撃破ごとに1回だけ、岩と弾切りでは加点しません。

有効な刃で敵弾を消す／最終ボス弾を反射すると1発1CUT。最後のCUTから1.5秒または被弾で現在CUTを0へ戻し、最大CUTを保持します。ポーズ・登場・結果では猶予を進めません。CUTは得点に換算しません。設定は`CUT`。

`stages.py: STAGES`が出現表・背景・BGM・アイテム・ボス・クリア後遷移を定義します。`progress.py: RunState`が現在面・HP・残機・武器・スコア・現在／最大CUT・次のエクステンドを保持。`StageEntry`が面開始時のCONTINUE用スナップショットです。

## 音楽・画像・SEの編集

Pyxel 2.9.9のEditorを使用します。全バンクは64音源枠、各フレーズ32音符以下で、標準Editorから編集可能です。同名.pyxpalを置き、元の52色の並びを変更しないでください。起動やbuild.pyで編集原本を生成し直しません。

| 原本 | 編集するもの |
|---|---|
| assets/blade.pyxres | 戦闘・タイトル画像、SE、1面道中Music0・ボスMusic1 |
| assets/story.pyxres | 4場面の情景画像（専用バンク） |
| assets/stage2_music.pyxres | 2面道中Music2・ボスMusic3 |
| assets/stage3_music.pyxres | 3面道中Music4・最終ボスMusic5 |
| assets/menu_music.pyxres | タイトルMusic7・スタッフロールMusic6 |

タイトル画像はImage 2 (0,0) 256×100。敵画像はImage 0、洞窟の岩肌はImage 1。添付title.pngもassetsへ同梱しています。音源バンク切替では画像を再ロードしません。

被弾は全バンク共通のSound5、6音・speed2・約0.1秒。短い下降音とノイズを組み合わせ、同時発生した撃破・斬撃等のSEより優先します。被弾時は0.18秒だけBGMを45%、効果音CH5を160%へ調整し、元へ戻します。`AUDIO_MIX`で変更可能。SE5を編集する場合は全バンクの同じ枠へ反映してください。

添付opening.txtはT120・4声・16秒ループ、ending.txtはT133・4声・約14.436秒ループ。原文は変更せずassetsに保存。通常は`UI_BGM_MODE="mml"`で添付のメロディ・テンポ・ENV/VIB/GLIを原文から再生します。タイトルと選択画面でMusic7、最終CLEAR・エンディング本文・スタッフロールでMusic6。前の曲を止めて切り替えます。Safariではゲームを起動する最初のタップ等で音声を解放し、タイトル曲を開始します。

Editorで音符版を編集した場合は`UI_BGM_MODE="resource"`へ変更してください。音符版は16分音符単位・音量0〜7へENVを近似し、VIB/GLIも近似。タイトルはT120を維持。エンディングは整数speed14なので約T128.57・14.933秒です。通常のMML再生ではT133を維持します。取り込みツールはtools/import_menu_assets.py（初回のみ）。

第2・第3面も`LATER_BGM_MODE="mml"`が標準、Editor版は`"resource"`。1面は`STAGE_BGM_MODE="resource"`が標準です。BGMはCH0〜3、SEはCH4／5の計6ch。MusicのCH4以降は空にしてください。

## 起動・配布

```powershell
.\blade_shooter\run.ps1
python blade_shooter/build.py
```

Web：`dist/blade-shooter-web.zip`を展開し、index.html（紹介）からplay.html（ゲーム）へ。GitHub Pagesは.github/workflows/pages.ymlでdist/webを公開します。

GKD：`dist/blade-shooter-gkd.zip`をPortsへ展開し、blade-shooter.shとblade-shooterフォルダを隣に配置します。既定Pythonは`/storage/pyxel_Python/bin/python3`。`BLADE_SHOOTER_PYTHON`で変更可能。画像・MML・説明書を共通で収録します。

ベストスコア：WebはlocalStorageの`blade-shooter.best.v1`、PC／GKDはゲーム内`save/best.json`。保存失敗でも停止せず、その起動中の記録を保持します。CONTINUEはこれとは別のメモリ内情報です。

## 開発用（通常メニューには表示しない）

```powershell
.\blade_shooter\run.ps1 --course stage --section 6 --seed 42
.\blade_shooter\run.ps1 --course compare --weapon lance
.\blade_shooter\run.ps1 --course stage2
.\blade_shooter\run.ps1 --course stealth
.\blade_shooter\run.ps1 --course stage3
.\blade_shooter\run.ps1 --course cave
.\blade_shooter\run.ps1 --course final --debug
```

54秒比較、tempo、tempo_fast、各ボス・洞窟直行等はCLIのみに残します。`--debug`（Webは?debug=1）でスコア・CUT・被弾・残機・エクステンド・CONTINUE・ステージ終了をログ出力できます。本番では非表示です。武器の威力・軌跡・時間はWEAPONSへ集約し、今回変更していません。再使用間隔は攻撃入力の受理から起算。攻撃中も移動でき、攻撃無敵はありません。通常ショットは開始〜戻り終了まで停止し、残りの再使用待ち中は再開します。

確認記録はVERIFICATION.mdとverification/v0.17.1/を参照してください。iPhone Safari・GKD Pixel 2／PlumOS実機の音量・操作・表示は別途未確認です。
