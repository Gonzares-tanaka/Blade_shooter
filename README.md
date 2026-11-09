# 近接ブレイドSTG

0.11.1は添付MMLを1面BGMとしてループ再生。エリア終了ごとに、HP回復／武器交換が切り替わるアイテムを追加。左手で移動、右手で近接攻撃するマルチタッチ操作。ブレイド・アックスは横、ランスは縦へ払います。ランスの穂先は自機と同じ16px幅です。54秒の固定比較コースと、300秒の道中＋巨大戦艦を収録しています。

**[紹介ページ・ブラウザで遊ぶ](https://gonzares-tanaka.github.io/Blade_shooter/)**

スマホは画面左側から触れた指でドラッグ移動、右側から触れた指で素早くフリックして即攻撃。境界を越えても、指を離すまで担当は変わりません。開始前に武器を選べます。専用画面は[こちら](https://gonzares-tanaka.github.io/Blade_shooter/play.html)。

- [操作・Editor編集・調整・配布方法](blade_shooter/README.md)
- [GitHub Pages用Web ZIP](blade_shooter/dist/blade-shooter-web.zip)
- [GKD Pixel 2 / PlumOS用ZIP](blade_shooter/dist/blade-shooter-gkd.zip)
- [検証報告](blade_shooter/VERIFICATION.md)

引数なしで1面を起動します。シード固定は `blade_shooter/run.ps1 --seed 42`、ボス単体は `--course boss`。
Pagesの公開対象は `blade_shooter/dist/web/` の中身です。子機版 `../shooting_1/` は変更していません。
