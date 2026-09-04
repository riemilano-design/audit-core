# Git運用方法

ソロ開発+複数のClaude Codeセッション/エージェントが並行して触ることを前提にした、シンプルな運用ルール。

## ブランチ戦略

- `main`: 常に動く状態を保つ。直接pushしない。
- `feature/<phase>-<topic>`: 作業用ブランチ。例: `feature/phase1-formation-detector`, `feature/phase0-usi-bridge`
- `data/<topic>`: データ(`data/`配下)だけを変更するブランチ。コードの変更と混ぜない。例: `data/mino-shapes`

コードとデータを同じブランチ・同じコミットに混ぜないことを推奨する。理由: データは将棋知識としてのレビュー、コードは動作としてのレビューが必要で、観点が異なるため。

## コミットメッセージ規約

[Conventional Commits](https://www.conventionalcommits.org/) 風のプレフィックスを使う。

```
<種類>: <変更内容(日本語で良い)>
```

種類の一覧:

| プレフィックス | 意味 |
|---|---|
| `feat` | 新機能の実装 |
| `fix` | 不具合の修正 |
| `data` | `data/`配下の知識データの追加・修正 |
| `docs` | ドキュメント(CLAUDE.md, docs/)の変更 |
| `config` | `.claude/`配下(agents/skills/commands/hooks)の変更 |
| `test` | テストの追加・修正 |
| `chore` | 上記に当てはまらない雑務(依存関係更新など) |

例: `data: 本美濃・高美濃・銀冠のshapesを追加`、`feat: 形判定ロジックの実装`

## セルフレビューの手順(mainへのマージ前)

このプロジェクトは基本ソロ開発のため、他人によるPRレビューの代わりに、マージ前チェックリストで代替する。

1. [../CLAUDE.md](../CLAUDE.md) の「絶対に守るルール」に反していないか
2. `data/`配下の変更がある場合、[../CLAUDE.md](../CLAUDE.md) ルール4番(大量生成禁止)・出典・confidence_levelの記載を確認したか
3. 該当するdocsの更新が必要な変更であれば、同じブランチ内でdocsも更新したか([CHANGE_MANAGEMENT.md](CHANGE_MANAGEMENT.md) 参照)
4. テストがある場合、通っているか([TESTING_STRATEGY.md](TESTING_STRATEGY.md))

このチェックリストを満たしたら、人間(あなた)が最終承認して `main` にマージする。**マージの実行自体は人間が行う**([ROLES.md](ROLES.md))。

## Claude Codeエージェント/セッションが複数並行する場合

- 各エージェントは自分の担当ディレクトリに対応するブランチで作業する(担当範囲は [ROLES.md](ROLES.md) と `.claude/agents/*.md` を参照)
- 同じファイルを複数のブランチで同時に触らない。担当分けが [ROLES.md](ROLES.md) の想定と食い違う変更が必要になったら、作業前に人間に確認する
- ブランチのマージ順序で衝突が起きそうな場合(例: スキーマ変更とそのスキーマを使うロジック実装が同時進行)は、スキーマ側を先にmainへ入れてから、ロジック側のブランチをリベースする
