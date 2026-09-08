# docs/ 目次

このリポジトリの設計・運用ドキュメントの索引です。まず [../CLAUDE.md](../CLAUDE.md) を読んでから、必要な文書に進んでください。

| ファイル | 何が書いてあるか | 主な読者 |
|---|---|---|
| [PROJECT_VISION.md](PROJECT_VISION.md) | このアプリが最終的に何を実現しようとしているのか(核心的な強み・完成イメージ・完成の判定基準)。**正本** | 全員 |
| [LONG_TERM_VISION.md](LONG_TERM_VISION.md) | 長期構想(7層構造・Intentの宣言方式)。**MVPの完成条件ではない** | 全員 |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 全体構造とモジュールの責務境界、Unit間の境界、変えない構造上の約束。**正本** | 実装する人・エージェント全員 |
| [AGENT_PROTOCOL.md](AGENT_PROTOCOL.md) | 3役(司令塔・実装担当・承認/監査担当)と専門エージェントの協働ルール、GO/REVISE/HUMANの運用。**正本** | AIエージェントを使う人全員 |
| [DATA_MODEL.md](DATA_MODEL.md) | 教育用データパイプライン(9段階)の詳細設計、shapes/openings/intents/explanations 各スキーマの意味、将棋知識の3分類と運用区分(`review_status`) | データを作る人・ロジックを実装する人 |
| [SCENARIOS.md](SCENARIOS.md) | 「対局シナリオ」(AIに棒銀・早仕掛けなどを指させる仕組み)の設計。**Phase 7 の再定義により、これは開発・検証専用の機構であり本番の基本体験には使わない**([../CLAUDE.md](../CLAUDE.md) の「絶対的な上位原則」)。過去の方針とその撤回の経緯を残している | 開発・検証用の制御機構を扱う人 |
| [KIND3_VERIFICATION.md](KIND3_VERIFICATION.md) | 判断的知識(Kind 3)の相手AI制御データについて、有段者レビューが得られない場合の多段階検証プロトコル。**AI検証は有段者レビューと同等の保証を持たない** | Kind 3 制御データを扱う人 |
| [PHASES.md](PHASES.md) | Phase 0〜7 の開発計画、各Phaseの成果物と完了条件、および完了後の記録(実機点検・仕様変更の記録を含む) | プロジェクト全体の進行管理者(人間) |
| [GIT_WORKFLOW.md](GIT_WORKFLOW.md) | ブランチの切り方、コミットメッセージの書き方、マージの手順 | コードやデータを変更する人・エージェント全員 |
| [TESTING_STRATEGY.md](TESTING_STRATEGY.md) | 何をどう自動テストするか | ロジックを実装する人 |
| [ROLES.md](ROLES.md) | 人間が判断すべきこと・AIに任せてよいこと・エージェント間の分担 | プロジェクトを進める人全員 |
| [CHANGE_MANAGEMENT.md](CHANGE_MANAGEMENT.md) | 仕様が変わったとき、CLAUDE.md/docs/schemas/agents/コードのどこを直すべきか | 仕様変更を扱う人全員 |

## 用語メモ

- **スキーマ(schema)**: データが従うべき「型紙」。「このフィールドは必須」「この値は文字列」のようなルールをJSON形式で定義したもの。`data/schemas/` 以下にある。
- **フック(hook)**: 特定の操作(ファイル保存など)をきっかけに自動で実行される処理。`.claude/settings.json` で設定する。
- **エージェント(agent)**: 特定の役割に特化したClaude Codeの担当者設定。`.claude/agents/` 以下にある。詳しくは [ROLES.md](ROLES.md)。
