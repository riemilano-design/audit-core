# data/ について

将棋の知識(形・戦型・意図・説明)を扱う、コードとは切り離されたデータ置き場です。

## 現在の中身

```
data/
├── schemas/     # 4つのデータ型の「型紙」(JSON Schema)。確定版。
│   ├── shapes.schema.json
│   ├── openings.schema.json
│   ├── intents.schema.json
│   └── explanations.schema.json
└── examples/    # 各スキーマにつき1件だけの最小サンプル。スキーマが実際に使えるかの確認用。
    ├── shapes.example.json
    ├── openings.example.json
    ├── intents.example.json
    └── explanations.example.json
```

**本番用の実データ(大量の定跡・形データ)はまだ存在しません。** これは意図的な状態です。理由は [../CLAUDE.md](../CLAUDE.md) の「絶対に守るルール」4番、および [../docs/PHASES.md](../docs/PHASES.md) の Phase 1 の説明を参照してください。

`examples/` の中身は本番データではなく、スキーマ設計が破綻していないかを確認するための最小限のサンプルです。本番データは Phase 1 着手時に、`data/shapes/`・`data/openings/`・`data/intents/`・`data/explanations/` のような形で別途追加していく想定です(ディレクトリはまだ作成していません)。

## 各スキーマの意味

4つのスキーマの関係と、教育用データパイプラインとの対応は [../docs/DATA_MODEL.md](../docs/DATA_MODEL.md) に詳しく書いています。ここでは一行ずつだけ。

- **shapes**: 囲い・陣形そのもの(例: 本美濃囲い)。自分が目指す形にも、相手の陣形の判定にも使う共通の型。
- **openings**: 戦型(例: 四間飛車、居飛車)。どちらの側の戦型か、どの shapes につながるかを持つ。将来の「対局シナリオ」もここに拡張する。
- **intents**: 相手の指し手から読み取れる意図(例: 棒銀)。今の狙いと次の狙いをセットで持つ。
- **explanations**: 「目的→手→理由」の説明そのもの。教育用データパイプラインの9段階のうち、局面判定以外のほぼ全段階(現在の形の説明、相手の意図の説明、候補手の説明など)がこの型で出力される。

## データを追加・変更する人へ

1. 必ず `data/schemas/` のスキーマに準拠すること。
2. 将棋知識として自信が持てない内容は `confidence_level` を下げ、出典(`source`)を書くこと。
3. 一度に大量のレコードを作らないこと。数件ずつ、人間のレビューを挟みながら進める。
4. スキーマ自体を変えたくなった場合は、まず [../docs/DATA_MODEL.md](../docs/DATA_MODEL.md) を更新してから `data/schemas/*.schema.json` を変更する(順序はどちらでもよいが、両方を必ず同時に直す)。
