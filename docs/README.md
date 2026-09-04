# docs/ 目次

このリポジトリの設計・運用ドキュメントの索引です。まず [../CLAUDE.md](../CLAUDE.md) を読んでから、必要な文書に進んでください。

| ファイル | 何が書いてあるか | 主な読者 |
|---|---|---|
| [DATA_MODEL.md](DATA_MODEL.md) | 教育用データパイプライン(9段階)の詳細設計と、shapes/openings/intents/explanations 各スキーマの意味 | データを作る人・ロジックを実装する人 |
| [SCENARIOS.md](SCENARIOS.md) | 「対局シナリオ」(AIに棒銀・早仕掛けなどを指させて練習させる仕組み)の将来設計。今は未実装 | 将来Phase4以降の実装者 |
| [PHASES.md](PHASES.md) | Phase 0〜5 の開発計画、各Phaseの成果物と完了条件 | プロジェクト全体の進行管理者(人間) |
| [GIT_WORKFLOW.md](GIT_WORKFLOW.md) | ブランチの切り方、コミットメッセージの書き方、マージの手順 | コードやデータを変更する人・エージェント全員 |
| [TESTING_STRATEGY.md](TESTING_STRATEGY.md) | 何をどう自動テストするか | ロジックを実装する人 |
| [ROLES.md](ROLES.md) | 人間が判断すべきこと・AIに任せてよいこと・エージェント間の分担 | プロジェクトを進める人全員 |
| [CHANGE_MANAGEMENT.md](CHANGE_MANAGEMENT.md) | 仕様が変わったとき、CLAUDE.md/docs/schemas/agents/コードのどこを直すべきか | 仕様変更を扱う人全員 |

## 用語メモ

- **スキーマ(schema)**: データが従うべき「型紙」。「このフィールドは必須」「この値は文字列」のようなルールをJSON形式で定義したもの。`data/schemas/` 以下にある。
- **フック(hook)**: 特定の操作(ファイル保存など)をきっかけに自動で実行される処理。`.claude/settings.json` で設定する。
- **エージェント(agent)**: 特定の役割に特化したClaude Codeの担当者設定。`.claude/agents/` 以下にある。詳しくは [ROLES.md](ROLES.md)。
