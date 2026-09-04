# 仕様変更マネジメントルール

## 原則

**`CLAUDE.md` は薄く・安定させる。詳細は `docs/` に置く。** `CLAUDE.md` を直したくなったら、まず「これは本当にプロジェクト全体に関わる不変の方針か、それとも特定領域の詳細か」を自問する。後者なら `docs/` 側を直す。

## 変更の種類 → 直す場所

| 変更の種類 | 直す場所 |
|---|---|
| 最重要コンセプト・プロジェクトの目的そのものが変わる | `CLAUDE.md` |
| MVPスコープ(対象戦型・目標形など)が変わる | `CLAUDE.md`(現在のスコープ欄)+ `docs/PHASES.md` |
| 教育用データパイプラインの段階・意味が変わる | `docs/DATA_MODEL.md` |
| データスキーマの形式(フィールド追加・型変更)が変わる | `data/schemas/*.schema.json` + `docs/DATA_MODEL.md`(**必ず両方同時に**) |
| 個別の形・戦型・意図の内容が変わる(知識の追加・修正) | `data/`配下の実データファイルのみ。スキーマ・docsは触らない |
| 対局シナリオの設計方針が変わる | `docs/SCENARIOS.md` |
| Phaseの区切り・完了条件が変わる | `docs/PHASES.md` |
| Git運用ルールが変わる | `docs/GIT_WORKFLOW.md` |
| テスト戦略が変わる | `docs/TESTING_STRATEGY.md` |
| エージェントの責任範囲が変わる | `.claude/agents/*.md`(本体)+ `docs/ROLES.md`(表のみ更新) |
| 新しいコマンド・フックが必要になる | `.claude/commands/` または `.claude/settings.json` |
| 人間/AIの判断権限の線引きが変わる | `docs/ROLES.md` |

## スキーマの後方互換性

`data/schemas/*.schema.json` を変更する際:

1. 既存の `data/examples/` (および将来の本番データ)が新スキーマでも検証を通るか確認する
2. 通らない破壊的変更の場合、スキーマに `schemaVersion` のような版数フィールドを設け、移行方針を `docs/DATA_MODEL.md` に追記する
3. 破壊的変更は必ず人間の承認を経てから `main` にマージする([docs/GIT_WORKFLOW.md](GIT_WORKFLOW.md))

## この文書自体を変更する場合

`docs/CHANGE_MANAGEMENT.md` 自体のルールを変える変更は、必ず人間の承認を経ること(ルールを決めるルールなので、他のどの変更よりも慎重に扱う)。
