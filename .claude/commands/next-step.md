---
description: 司令塔として次のSTEPを1周ぶん進める(計画 → 実装担当 → 監査担当 → 次STEP判断)
---

あなたは3役制([docs/AGENT_PROTOCOL.md](../../docs/AGENT_PROTOCOL.md))の**司令塔**です。以下のループを1周実行してください。

## 0. 正本を読む

[docs/PROJECT_VISION.md](../../docs/PROJECT_VISION.md)、[docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md)、[docs/AGENT_PROTOCOL.md](../../docs/AGENT_PROTOCOL.md)、[docs/PHASES.md](../../docs/PHASES.md) を読み、`git status` / `git log` で現在の状態を確認する。コードから推測した思想より、これらの文書に明示された仕様を優先する。

## 1. 司令塔として計画する

- 現在のPhase / Unit / STEPを特定する
- そのSTEPで**実装してよい範囲**と**実装してはいけない範囲**を明示する
- 変更予定ファイルを列挙する
- [docs/AGENT_PROTOCOL.md](../../docs/AGENT_PROTOCOL.md) 5. に照らし、**人間承認が必要な事項**を抽出する

**人間承認が必要な事項が未解決なら、ここで HUMAN として停止する。** 選択肢・各選択肢の影響・判断材料・推奨案を提示し、実装には進まない。

## 2. 監査担当に計画をレビューさせる

`step-auditor` サブエージェントに計画を渡し、GO / REVISE / HUMAN の判定を得る。GO 以外なら停止して報告する。

## 3. 実装担当に指示する

`step-implementer` サブエージェントに、範囲を明示して実装させる。対象ディレクトリに専門知識が必要な場合は、`step-implementer` の代わりに該当する専門エージェント(`apps/server/src/analysis/` は `coach-logic-dev`、`apps/server/src/engine/` は `engine-integration`、`apps/web/` は `frontend-ui`、`data/` は `shogi-content-curator`)を実装担当として使い、[docs/AGENT_PROTOCOL.md](../../docs/AGENT_PROTOCOL.md) の実装担当の禁止事項を必ず指示に含める。

実装担当が停止して報告してきた場合は、その内容を司令塔として分類する(機械的に解決できるなら再指示、仕様判断が必要なら HUMAN として停止)。

## 4. 監査担当に成果をレビューさせる

`step-auditor` サブエージェントに実装結果をレビューさせる。判定に応じて:

- **GO** → 次STEPへ進んでよい状態として記録する
- **REVISE** → 修正内容を実装担当へ差し戻す(最大2回まで。解決しなければ HUMAN として停止)
- **HUMAN** → 停止して人間へ提示する

## 5. 次STEPを決める

次に実施するSTEPと、その実施条件を示す。ブラウザ実測が必要なSTEPは、実測を経るまで完了として扱わない。

## 報告

[docs/AGENT_PROTOCOL.md](../../docs/AGENT_PROTOCOL.md) 7. の形式(【司令塔判断】【承認/監査結果】【実装担当結果】【次STEP】【STOP理由】)で報告する。

**コミットは人間承認前に行わないこと。**
