---
name: schema-consistency-check
description: data/配下のJSONファイルが、対応するdata/schemas/のスキーマとdocs/DATA_MODEL.mdの説明の両方に整合しているかを確認する手順。スキーマを変更したとき、または大量の検証が必要なときに使う。
---

# データとスキーマの整合性確認

Node.js環境の有無で手順が変わります。

## Node.js環境がある場合

```bash
node scripts/validate-data.mjs
```

これで `data/examples/` および `data/<type>/`(存在する場合)配下の全JSONファイルを、対応するスキーマに照らして検証し、IDの相互参照(`opening_id` が実在する `openings.id` を指しているか等)もチェックする。examples配下の参照切れは警告(想定内)、本番データ(`data/<type>/`)配下の参照切れはエラー扱いになる。

エラーが出た場合、`scripts/validate-data.mjs` の出力に「どのファイルの」「どのフィールドが」「何と食い違うか」が表示されるので、該当ファイルを修正して再実行する。

## Node.js環境がない場合(目視チェック)

1. 対象の `data/schemas/<type>.schema.json` を開き、`required` 配列を確認する
2. 対象のデータファイルに、その全フィールドが存在するか確認する
3. `enum` が指定されているフィールド(`side`, `confidence_level` など)の値が、許可された選択肢に含まれているか確認する
4. `id` を参照するフィールド(`opening_id`, `refers_to_shape_id` など。一覧は [docs/DATA_MODEL.md](../../../docs/DATA_MODEL.md) の「IDの参照関係」)が、実在する `id` を指しているか、他のファイルを開いて確認する

## スキーマ自体を変更した場合

スキーマ変更後は、必ず以下の両方を確認すること([docs/CHANGE_MANAGEMENT.md](../../../docs/CHANGE_MANAGEMENT.md) 参照)。

1. `docs/DATA_MODEL.md` の該当スキーマの説明を更新したか
2. 既存の `data/examples/*.example.json` が新スキーマでも検証を通るか(通らない場合は破壊的変更。移行方針を `docs/DATA_MODEL.md` に追記する)
