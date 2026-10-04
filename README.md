# 公民館サークル検索（ダンス・太極拳）

福岡市の公民館サークル（ダンス・太極拳）を検索できる静的サイトです。

- 一覧表で検索: `docs/index.html`
- 週間カレンダー: `docs/calendar.html`

## 再生成

```
python3 spa/build.py
```

`data/target-*.csv` を `spa/*.template.html` に埋め込み、`docs/` に出力します（GitHub Pages は `docs/` を公開）。

## 公開

```
./publish.sh              # または make publish
./publish.sh "メッセージ"  # コミットメッセージを指定
```

ビルド → commit → push → GitHub Pages のビルド完了待ち までを一括で行います。
