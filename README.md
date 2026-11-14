# 近接ブレイドSTG

0.15.1は全3面からエンディングまでの一巡版です。第1面300秒＋巨大戦艦、第2面180秒＋連結編隊、第3面150秒の月面洞窟＋反射で倒す最終ボスを収録。HP・武器・スコア・最大CUTを引き継ぎ、CLEARで累計スコアを表示してスタッフロールへ進みます。左手移動＋右手フリック、3武器、Editor編集可能な画像・BGM・SEを使用します。

**[紹介ページ・ブラウザで遊ぶ](https://gonzares-tanaka.github.io/Blade_shooter/)**

スマホは画面左側から触れた指でドラッグ移動、右側から触れた指で素早くフリックして即攻撃。境界を越えても、指を離すまで担当は変わりません。開始前に武器を選べます。専用画面は[こちら](https://gonzares-tanaka.github.io/Blade_shooter/play.html)。

- [操作・Editor編集・調整・配布方法](blade_shooter/README.md)
- [GitHub Pages用Web ZIP](blade_shooter/dist/blade-shooter-web.zip)
- [GKD Pixel 2 / PlumOS用ZIP](blade_shooter/dist/blade-shooter-gkd.zip)
- [検証報告](blade_shooter/VERIFICATION.md)

引数なしで1面を起動します。シード固定は `blade_shooter/run.ps1 --seed 42`、第3面は `--course stage3`、洞窟道中は `--course cave --section 2`、最終ボスは `--course final`。
Pagesの公開対象は `blade_shooter/dist/web/` の中身です。子機版 `../shooting_1/` は変更していません。
