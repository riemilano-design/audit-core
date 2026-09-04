---
description: CLAUDE.md・docs・data/schemas・.claude/agentsの整合性を点検する
---

`docs-spec-guardian` の役割で、このリポジトリの仕様一貫性を点検してください。

手順:

1. `CLAUDE.md` を読み、「最重要コンセプト」「現在のスコープ」「絶対に守るルール」を把握する
2. `docs/` 配下の全ファイルを読み、`CLAUDE.md` と矛盾する記述がないか確認する
3. `docs/ROLES.md` の表と `.claude/agents/*.md` の内容(責任範囲・やって良い/悪いこと)が一致しているか確認する
4. `data/schemas/*.schema.json` と `docs/DATA_MODEL.md` のフィールド説明が一致しているか確認する
5. `docs/PHASES.md` の「現在地」が実際のディレクトリ構成(`apps/` の有無など)と矛盾していないか確認する

矛盾や古い記述を見つけたら、`docs/CHANGE_MANAGEMENT.md` の対応表に従ってどのファイルを直すべきか判断し、一覧にして報告してください。**この時点ではまだ編集しない。** 報告を見てユーザーが修正を指示したら、対応するファイルを編集してください。
