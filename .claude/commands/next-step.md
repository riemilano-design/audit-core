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
- このSTEPの Tier(A / B)を判定する。判断に迷った場合は Tier A とする([docs/AGENT_PROTOCOL.md](../../docs/AGENT_PROTOCOL.md) 10.)
- `node scripts/check-docs.mjs` を実行し、未処遇の「ユーザーに見える=はい」既知事項の一覧を得て、提案に併記する(この一覧の選定・編集・更新は行わない。[docs/AGENT_PROTOCOL.md](../../docs/AGENT_PROTOCOL.md) 10.)
- [docs/AGENT_PROTOCOL.md](../../docs/AGENT_PROTOCOL.md) 5. に照らし、**人間承認が必要な事項**を抽出する

**人間承認が必要な事項が未解決なら、ここで HUMAN として停止する。** 選択肢・各選択肢の影響・判断材料・推奨案を提示し、実装には進まない。

## 2. 監査担当に計画をレビューさせる

**このSTEPの変更対象が文書のみ(`docs/` ・ `CLAUDE.md` ・ `.claude/` 配下)の場合、この計画レビューは省略してよい。** 3.(実装)へ進み、4.(成果物レビュー)で1回だけ独立監査を行う([docs/AGENT_PROTOCOL.md](../../docs/AGENT_PROTOCOL.md) 10.)。

**`apps/` または `data/` を変更する STEP は、従来どおり計画レビューを行う。** `step-auditor` サブエージェントに計画を渡し、GO / REVISE / HUMAN の判定を得る。GO 以外なら停止して報告する。

## 3. 実装担当に指示する

`step-implementer` サブエージェントに、範囲を明示して実装させる。対象ディレクトリに専門知識が必要な場合は、`step-implementer` の代わりに該当する専門エージェント(`apps/server/src/analysis/` は `coach-logic-dev`、`apps/server/src/engine/` は `engine-integration`、`apps/web/` は `frontend-ui`、`data/` は `shogi-content-curator`)を実装担当として使い、[docs/AGENT_PROTOCOL.md](../../docs/AGENT_PROTOCOL.md) の実装担当の禁止事項を必ず指示に含める。

実装担当が停止して報告してきた場合は、その内容を司令塔として分類する(機械的に解決できるなら再指示、仕様判断が必要なら HUMAN として停止)。

## 3a. 対局回帰を回す

`apps/` を変更した STEP では、実装担当に固定棋譜モード(`scripts/playtest/replay.ts`)で `scripts/playtest/kifu/` の全棋譜を再生させ、`check.ts` の報告を成果とともに監査担当へ渡す。探索モードは STEP の完了条件には使わない(発見用)。

## 4. 監査担当に成果をレビューさせる

`step-auditor` サブエージェントに実装結果をレビューさせる。**Tier B([docs/AGENT_PROTOCOL.md](../../docs/AGENT_PROTOCOL.md) 10.)に該当する STEP は、確認作業自体は省略せず、報告のみ「何を・なぜ・検証結果」の3行で受け取ってよい。** 判定に応じて:

- **GO** → 次STEPへ進んでよい状態として記録する
- **REVISE** → 修正内容を実装担当へ差し戻す(最大2回まで。解決しなければ HUMAN として停止)
- **HUMAN** → 停止して人間へ提示する

## 5. 次STEPを決める

次に実施するSTEPと、その実施条件を示す。ブラウザ実測が必要なSTEPは、実測を経るまで完了として扱わない。

## 報告

[docs/AGENT_PROTOCOL.md](../../docs/AGENT_PROTOCOL.md) 7. の形式(【司令塔判断】【承認/監査結果】【実装担当結果】【次STEP】【STOP理由】)で報告する。

**コミットは人間承認前に行わないこと。**
