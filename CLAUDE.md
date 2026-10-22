# CLAUDE.md

このリポジトリには資産が 2 つある。**いまの作業は `audit-core/`(Audit Core: XBRL 等の監査エンジン。売却を目指す技術資産)** で、直近 200 コミットはすべてそこだけを触っている(2026-10-19 時点)。将棋アプリ(`apps/`・`data/`・`scripts/`)の憲法は [docs/SHOGI_CONSTITUTION.md](docs/SHOGI_CONSTITUTION.md) に原文のまま移した ― **将棋側を触るときだけ読む。**

## Audit Core の作法(毎セッション効く 6 つ)

1. **封を先に commit する。** 実装・材料・測定・採点より前に、封(対象条件・除外・分母・事前予測)を commit する。予測は欄ごとに**外れうる形**で書き、外れ方も書く。**結果を見てから封も予測も書き換えない**(外れは外れとして残す。補足は日付つきの追記)。
2. **engine(`audit-core/core/`・`adapters/`)は人間の承認なしに変えない。** 実験の入口は `measure/` に置く。`tests/adapters/xbrl/test_boundary.py` の import 一覧を自分の都合で広げない。
3. **動きを変える変更(コード・データ)は、独立監査(`step-auditor`)の GO を経てから commit する。** 文書だけの変更は不要。監査中は木を触らない(sha256 で凍結し、監査の前後で一致を見る)。
4. **0 USD が既定。** LLM の席(API)を呼ぶ・外部へ出す・金が動く変更は人間が決める。
5. **測っていないことは書かない。** 数の正本は `fixtures/**/*.json`。文書の数は `tests/measure` の門で記録に縛り、**門は変異で赤くなることを確かめてから門と呼ぶ。** 「0 件」は先に自分の欠陥を疑う(key の取り違え・母集団の回し漏れ)。
6. **`main` へのマージ・スコープの拡大・この節の変更は人間が決める。** `feature/` 上のコミット承認は司令塔に委任(条件は [docs/AGENT_PROTOCOL.md](docs/AGENT_PROTOCOL.md) の「承認の委任」: 監査 GO なしに承認しない・根拠を書く・測っていないものを承認しない)。

## コマンド(`cd audit-core` で)

- `python3 -m pytest -q tests/measure` ― 門だけ(約 90 秒)
- `sh run_tests.sh` ― 全部(約 40 分。覆いの検査 → pytest → unittest)
- 試験 file を足したら `python3 measure/suite_coverage_2026-10-16.py --write` を走らせ、`docs/SUITE_COVERAGE_2026-10-16.md` §2-1 の数も直す(忘れると門が赤くなる ― それが狙い)

## git

- commit は**パス指定**。`git add -A`・`stash`・`reset`・`checkout` で他の席の作業を消さない。
- 共有ツリーを赤くしうる実測は worktree で。

## 正本の在りか

- 封・結果・診断: `audit-core/docs/XBRL_*_<日付>.md`(`_SEAL_` → `_RESULT_` の対)。記録: `audit-core/fixtures/xbrl/cd8/`
- 席(誰がどこに)と権限: [docs/COMMAND_STRUCTURE.md](docs/COMMAND_STRUCTURE.md)・[docs/AGENT_PROTOCOL.md](docs/AGENT_PROTOCOL.md)
- 文書は日本語で書く。数は字で留め、推測で埋めない。
