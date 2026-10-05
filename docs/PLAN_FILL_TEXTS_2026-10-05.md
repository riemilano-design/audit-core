# 計画(文書だけ): 言い換えの束 ― ⑤ の `statement` から `fill_texts.json` を作る(2026-10-05 起草)

**司令塔の裁定(2026-10-05・便 135 への返しの 6)**: 計画だけ先に書いてよい。入力は統合の `statement` だけ・出力は F-5 の照合に必ず通す・
落ちたら止まる・`SEAT_COST_CAP_USD` はこの実行単位。**LLM を回すのは金銭なので人間の GO の後。計画を書いても回さない。**
関連: `docs/PLAN_EXIT_FILL_2026-10-01.md` §3(5 本の線)・§7.7 の 6、`docs/PLAN_LLM_SEATS_API_2026-09-30.md` §3(API の呼び方)、
`lib/seatRun.ts`(`runSlot`: 鍵・上限・schema 再試行・保存の器)。CLAUDE.md 規則 5(言い換えに限定)・8。

## 0. 顧客の PDF にどう出るか

「ひとことで」の**太字の 1 文**と、事実 3 本の **`― 読み: ` の後の文**、`answered` / `partial` の問いの**答えの文**が、
人が書く代わりに LLM の言い換えになる。**出るのは ⑥ の照合(F-5)を通った文だけ** ― 数と指し手の字が元の `statement` の部分集合で字も同じ、
「普段」のような ⑥ が決めない語が無い。通らなければその文は無く、⑥ が「渡されていない」で止まる(= 人が書く道。今までどおり)。

## 1. 入力(**統合の `statement` だけ**)

- `out/<顧客>/exit/answer_selection.json`(⑤。採用の印つき)から **itemRef の一覧**: `lead.itemRef`・`p1[].itemRef`・`answers[].itemRefs`(status が `answered` / `partial` の行だけ。`unanswerable` は人間の文)。
- `out/<顧客>/llm-seats/<runId>/integration.json` の `clusters[].representative.statement`(itemRef → statement。読む欄は `exit_fill.statements_of` と同じ 2 つ)。
- **渡さないもの**: packet・候補の JSON・下書きの md・`internal`(schema に無い ― 参照できない)・顧客の名前・問いの原文(答えの文には問いの id と statement だけ)。
- 用語の 4 行(`check_structure.TERM_LINES`)は**指示文の中で**渡す(冊子の語に合わせるため。新しい語ではない)。

## 2. 出力 `out/<顧客>/exit/fill_texts.json`

`{"lead": 文, "p1.1": 文, "p1.2": 文, "p1.3": 文, "ans.q2": 文, …}`。**鍵は ⑥ のスロット名そのまま**(`exit_fill.LEAD_SLOT`・⑤ の `slot`・`exit_fill.answer_slot`)。
照合に落ちたスロットは**書かない**(空文字も書かない)。理由は隣の `fill_texts.problems.json` に 1 スロット 1 件で残す(費用の説明が作れるように ― 「失敗した試行の理由を保存する」)。

## 3. 道具(TS 1 本 + python の検査 1 つ。**いま作らない**)

- `scripts/playtest/fillTexts.ts`: `runSlot`(`lib/seatRun.ts`)で **1 席**(Claude。`.env` の鍵・モデル名・`SEAT_COST_CAP_USD`)。
  出力 schema は `{slot: string}` の object(canonical schema を 1 つ足す。`seat-output` とは別)。
- 指示文は**固定**し sha256 で留める(`FIXED_INSTRUCTION_SHA256` と同じ型)。中身: (1) 数・指し手・名前の字を**1 字も変えない**(足さない・計算しない・漢数字にしない)
  (2) 断定しない(「〜という読みです」「〜の可能性があります」)(3) 用語は 4 行の語を使う (4) 「普段」など**材料の外の判定を要する語**を使わない(語の表は `exit_groups.LABEL_FORBIDDEN_WORDS` を指示文に写さず参照で渡す ― 写すと 2 か所)
  (5) 手の目的・狙いを書かない(規則 8 の (3))(6) 1 文の長さの上限(**人間が決める数**。見本用 ≤ 4 ページの持ち分から ― §6)。
- **検査は python の 1 か所**: `exit_fill.py --verify-texts <fill_texts.json> --selection … --seats-dir …`(新しい入口。md は組まず `verified_text` だけを回す)。
  TS は書いた下書きをこの入口に通し、落ちたスロットの指摘を**累積して**渡して再試行(**最大 2 回**。前回の指摘を忘れさせない ― 「再試行の指摘は累積して渡す」)。
  再試行で通らなければそのスロットは書かない(**埋め直さない**。空席と同じ)。
- 段にはしない(⑤ と同じく deliver の外。費用が動く)。回すのは**人間の GO の後**、1 回ずつ。

## 4. 測ること(最初の 1 回で)

費用(実費・上限)/ スロットごとに通った・落ちた(理由の種類: 数の字・指し手・禁止語・空)/ 再試行の回数 / 通った文の長さ(§6 の上限に対して)/
⑥ を通して組んだ本編の見本用のページ数(≤ 4)/ **封じた最終版の読みの文との差**(同じにする目的ではない。違うなら理由が言えること)。

## 5. 線(破る変異を実装のときに当てる)

| 線 | 破る変異 |
|---|---|
| 入力は statement だけ | packet の数を指示文に混ぜる / 問いの原文を渡す |
| 出力は F-5 の照合に必ず通す | 照合を飛ばして書く / 落ちたスロットを空文字で書く |
| 落ちたら止まる(埋め直さない) | 再試行の上限を外す / 別の席で埋める |
| 上限は実行単位 | 上限をスロット単位にする |
| 指示文は固定 | sha を見ない |

## 6. 人間・司令塔に決めてもらうこと(**回す前**)

1. **金銭の GO**(1 回の実行。費用の見込みは §4 の前に `runSeats.ts --dry-run` と同じ形で出す)。
2. モデル・温度(§3.3 の既定で可か)。
3. **文の長さの上限**(太字の 1 文・読み 1 本・答え 1 件)。封じた最終版の実測(2026-10-05 に 9_本編_最終版.md を数えた): 太字 1 文 **89** 字・読み 3 本 **79・80・105** 字(数え方の群の表の読みは 155 字で、この束の対象外)。
4. 答えの文(`answered` / `partial`)を今回の顧客で作るか(5 人目は `unanswerable` 1 件のみ → **作る文が無い**。lead と読み 3 本だけ)。

## 7. 人間の GO(2026-10-05・伝聞 = 司令塔の中継。原文は `docs/AUTOMATION_STATUS_2026-09-26.md`)と、作った道具

**GO は正式機能化ではなく、1 回限りの境界測定実験。** 固定値(原文の数を字で留める ― `lib/fillTexts.ts` の `EXPERIMENT`、試験 t1):
Claude 1 席 / 4 スロット(lead + 読み 3 本。`readingRequired: false` の行は作らない)/ 最大 3 試行 / 最大 12 呼び出し / 取り置き 1,000 トークン/回 /
`SEAT_COST_CAP_USD=1`(**有効な値が 1 でなければ回さない** ― 上限を道具の中で上書きしない。**置き方は司令塔の決定(2026-10-05): .env は書き換えず、回すその 1 回のコマンドの環境変数で渡す**。`loadDotEnv` は既に在る環境変数を上書きしない)/ 太字 1 文・読み 1 本とも 200 字以内 / 5 人目の答えの文(answered / partial)は生成しない /
入力は ⑤ の承認済み statement だけ / F-5 を通った文だけ候補として残す。追加条件 1〜7 は report と手順に落とした(下)。

### 7.1 作ったもの(段にしない。`deliver.ts` は触らない ― 条件 6)

| もの | 中身 |
|---|---|
| `scripts/playtest/lib/fillTexts.ts` | 純粋部。`slotJobsOf`(lead + p1 true。答えは作らない・5 つ目で止まる)/ `instructionText`(規則 7 行 `RULES_LINES`。sha `RULES_SHA256` で固定・用語 4 行と禁止語は python から参照)/ `userTextOf`(statement だけ)/ `runFillTexts`(**1 試行 = 1 呼び出し**。`callStructured` を直接呼ぶ ― `runSlot` は形の再試行を内に持ち 1 試行が最大 3 呼び出しになるので「3 試行・12 呼び出し」の数え方が合わない。**`runSlot` の形の再試行が内側に隠れると、report の「試行数」が人間の条件の表(最大 3 試行)と合わなくなる ― 数え方を人間の条件と一致させるための判断(司令塔 2026-10-05 妥当)**。落ちた理由は累積して渡す・前の出力は渡さない)/ `maxCostBefore`(実行前の最大費用 = スロットごとに 3 × (入力の実測 + 1,000))/ `capProblems` |
| `scripts/playtest/fillTexts.ts` | CLI。`--dry-run`(鍵を使わない・送らない)/ 本番は同じ out-dir に `fill_texts.report.json` が在れば**回さない**(条件 7 = 2 回目を回さない)。出力は out/ にだけ: `fill_texts.json`(F-5 を通った文だけ)・`fill_texts.problems.json`・`fill_texts.report.json`・`attempts/`(原文・指摘) |
| `scripts/playtest/schemas/fill-text.v0.1.schema.json` | 席が返す形 `{text}` だけ(数・理由・内部の欄を持たない) |
| `exit_fill.py --print-terms` / `--verify-texts` | 用語 4 行と禁止語の参照 / F-5 + 長さ(≤ 200)の照合(`text_problems` ― ⑥ の `verified_text` と同じ 1 か所)。⑤ に無いスロット・false の行は落ちる |

### 7.2 report(条件 5)の欄

スロットごとに **試行数 / F-5 通過数 / 採用可能数 / 失敗理由 / 実費 / 最大費用(実行前)**。全体に 呼び出し数・実費・最大費用(実行前)・上限・止めた理由。
**最大費用は実行の前の数**(12 呼び出し × 入力の実測 + 取り置き 1,000。再試行の指摘の字は入っていない ― 上限 1 USD が守る。P-197)、**実費は実行の後の数**。別の欄で持つ(司令塔の追加 1)。
`measured.byMachine`(F-5 の数と指し手の字・禁止語・長さ)と `measured.notMeasured`(**因果関係・条件・対象の保存・新しい事実の有無・文としての自然さ ― 機械では測れない。通った文を人間が読む**)を分けて持つ(司令塔の追加 2)。
`note`: 生成結果は監査済みの事実ではない(条件 4)。

### 7.3 線 → 変異(§5 の表の実装)

| 線 | 赤になる試験 |
|---|---|
| 入力は statement だけ | t6(user に packet の数を混ぜる)|
| 出力は F-5 の照合に必ず通す | t8・t14(照合を飛ばす / 落ちたスロットを空文字で書く)|
| 落ちたら止まる(埋め直さない・2 回目を回さない) | t8・t11・t12(再試行の上限を外す / 13 本目を送る / HTTP の失敗で再試行)、CLI は report が在れば回さない |
| 上限は実行単位 | t10・t15(スロットごとに累計を戻す)|
| 指示文は固定 | t2(規則の 1 字を変える → sha が外れる)|
| 答えの文は作らない・false は作らない・4 まで | t4・t5 |
| 固定値は字 | t1 |
| 長さ・⑤ に無いスロット・false のスロットは照合側が落とす | f82・f83・f85(python)|

### 7.4 下見の実測(2026-10-05・合成の材料 `measure/c5`)

スロット 4(statement 123・123・94・92 字)。入力 ≒ 280〜290 トークン/呼び出し(指示文 ≒ 850 字 + statement)。**最大費用(実行前)≒ 0.317 USD**(上限 1 USD の内。.env の `SEAT_COST_CAP_USD` は 10 のまま ― 回すコマンドの環境変数で 1 を渡す。下見で「有効な上限 = 1」の印字を確かめる)。送っていない。

### 7.5 回し方(司令塔の合図の後に 1 回だけ)

1. `.env` は書き換えない。回すコマンドの先頭に `SEAT_COST_CAP_USD=1` を置く(司令塔の決定 2026-10-05。道具は有効な上限が 1 でなければ回さない)。
2. `SEAT_COST_CAP_USD=1 npx tsx scripts/playtest/fillTexts.ts --selection out/<顧客>/exit/answer_selection.json --seats-dir out/<顧客>/llm-seats --out-dir out/<顧客>/exit --dry-run` で下見し「有効な上限 SEAT_COST_CAP_USD = 1」の印字を確かめる → 同じコマンドから `--dry-run` を外して 1 回。**実際に打ったコマンドの字を report と LANE に残す。**
   回す前に out-dir(`out/<顧客>/exit`)の中身を目で見る ― 守りは `fill_texts.report.json` の有無だけで、report を書く前に落ちた 1 回目の `attempts/` が残っていても 2 回目を止めない(監査の指摘 2026-10-05)。`--dry-run` もローカルの python(`--print-terms`)を呼ぶ(鍵・送信は無い)。
3. 条件 5 の表(report)を司令塔に返して**停止**。成功しても Audit Core に組み込まない(条件 6)。失敗しても追加実行しない(条件 7)。この本編は顧客に送らない。

### 7.6 修正の束(人間の GO 2026-10-05「実験装置の修正後に行う最後の 1 回」― 司令塔が本人の言葉で直接受けた・原文は LANE §86)

**1 回限りの実行は LLM 1 回の後に道具の不具合で落ちた**(LANE §86: `fillTexts.ts` の `pyJson` が python を cwd = report-pdf で起こす一方、道の引数を打った相対のまま渡していた。下見は照合を呼ばないので出なかった)。人間の決定: **その停止は実験結果ではなく道具の不具合として扱い、修正後に最後の 1 回を回す。** 修正条件 13 件(原文は LANE §86)に対する実装:

| 条件 | 実装 | 試験 |
|---|---|---|
| 1 相対パス依存をなくす | CLI の `--selection`・`--seats-dir`・`--out-dir`・`--env` は**打った場所(cwd)から `path.resolve`** して使う(`requiredPath`)。python には絶対の道だけ渡る | `lib/fillTextsCli.test.ts` c2(repo の根・相対)・c4(別の cwd `scripts/playtest`・その cwd 相対) |
| 2 dry-run でも本番の照合経路を通す | 下見は API だけ省き、**本番と同じ `verifyTexts`**(文を書く → python 起動 → JSON の往復)を**文を空にした入力**で 1 回通す。結果は `fill_texts.dryrun.json` の `verifyWiring`(calls・checked・problemCounts・f5・inputPath) | c3(calls 1・checked 4・空の入力 4 本・attempts/ は作らない) |
| 3 落ちたケースを陽性対照として固定 | `FAILED_COMMAND_2026_10_05`(落ちた手の字そのもの)を試験に留め、**同じ旗の並び・同じ相対の道の形**で合成の材料に打つ(顧客の道は書けない)。直す前は落ちた手と同じ理由で赤(scratchpad `fix/positive_control_before.txt`・変異 M01)、直した後は緑 | c1(旗の並びの一致)+ c2 |
| 4 試行ごとに記録を先に作り、後に必ず書く | `attempts/<runId>/attempt_<slot>_<n>.json` を**呼び出しの前**に(試行 ID `<runId>:<slot>:<n>`・slot・試行番号・費用の欄は null)、**呼び出しの後**に同じファイルへ status(`responded` / `send_failed`)+ usage・実費・累計、**照合の後**に `adoptable` / `rejected` + 問題を書く(`FillTextsDeps.persist`、同じ name は上書き)。report はこれらの集計(`attemptRows`)。**前の実行の記録は上書きしない**(runId の下) | `lib/fillTexts.test.ts` t16(照合が落ちても usage・実費が残る・send_failed・persist 無しでも files に 1 本ずつ) |
| 5 指示文は変えない | `RULES_LINES`・`RULES_SHA256` は 1 字も触っていない(t2 で固定)。lead の 1 本への観察 3 つは LANE §86 に記録だけ | t2 |
| 6 既存試験・変異・dry-run・陽性対照 | LANE §87 | ― |
| 7 凍結・独立監査 1 往復 | LANE §87 | ― |
| 8〜10・12・13 | 固定値 `EXPERIMENT` は不変(t1)。report の列は条件 10 の 6 つ + `columns` の説明。`measured.notMeasured` 不変。段にしない | t1・t13 |
| 11 「F-5 通過」と「採用可能」は別項目 | python `--verify-texts` が `f5`(スロット → bool。**F-5 そのもの** = 数と指し手の字が statement の部分集合で字も同じ。禁止語・長さは見ない ― `f5_only_problems`)を `problems` と別に返す。lib は `f5Passed` = F-5 を通った**試行の数**(禁止語・長さで落ちた試行も数える)、`adoptable` = 機械の検査を全部通って残った数(0 か 1)。⑥ の `verified_text` が通す検査(`paraphrase_problems` = F-5 + 禁止語、+ 長さ)は変わらない | python f85(`f5` の欄)・f86(禁止語だけ / 長さだけ → F-5 は True)・TS t14(F-5 通過 2・採用可能 1) |

**回し方の変更**: 下見は `fill_texts.dryrun.verify_input.json` と `fill_texts.dryrun.json` を out-dir に書く(前の下見の 2 本を**上書き**する)。本番は `attempts/<runId>/` の下に書くので、2026-10-05 に落ちた実行の `attempts/verify_input_1.json` は残る。**2 回目を止める守りは引き続き `fill_texts.report.json` の有無だけ**(人間の条件 9「今回の実行後は追加実行しない」は運用で持つ)。
