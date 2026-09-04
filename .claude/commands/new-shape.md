---
description: shapes.schema.json に準拠した「形」データの下書きを1件作成する(人間レビュー前提)
argument-hint: [形の名前(例: 高美濃囲い)]
---

`shogi-content-curator` の役割で、`$ARGUMENTS` の形データの下書きを1件だけ作成してください。

手順:

1. `data/schemas/shapes.schema.json` を読み、必須フィールドを確認する
2. `docs/DATA_MODEL.md` の shapes の説明を読み、各フィールドの意味を確認する
3. 既存の `data/shapes/`(存在すれば)や `data/examples/shapes.example.json` を確認し、`family` や `parent_shape_id` の関係に矛盾がないか確認する
4. 下書きJSONを作成する。将棋知識として自信が持てない項目は `confidence_level` を `"low"` にし、`source` に「要確認」と明記する
5. `scripts/validate-data.mjs` が使える環境であれば実行し、スキーマ違反がないか確認する(Node未導入ならスキップしてその旨を報告する)

**この下書きをそのまま `main` にコミットしない。** ユーザーに内容を提示し、将棋知識として正しいかのレビューを依頼してください。一度の実行で作成するのは1件のみとし、[CLAUDE.md](../../CLAUDE.md) のルール4番(大量生成禁止)を守ってください。
