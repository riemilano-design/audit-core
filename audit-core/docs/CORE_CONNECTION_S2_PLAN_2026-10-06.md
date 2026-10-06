# 将棋側 S-2(E-3・I-4 にも packet を渡す)の計画と予測 ― 直す前に封じる

> **封じた後は本文を変えない。** 訂正は日付つきの追記か結果文書に。予測を当てるために範囲・規則を動かさない。
>
> **前提**: 人間の決定(2026-10-06、[CORE_CONNECTION_S1_DECISIONS_AFTER_2026-10-06.md](CORE_CONNECTION_S1_DECISIONS_AFTER_2026-10-06.md) の 2): 「S-2 は GO。予測が先。S-2 の価値は H-9 の再現ではなく、**Core 化した検証の結果が最終出口までどう伝播するか**を見ること。予測は 2 層(仮説 ID 単位と顧客の出口の単位)。本番の門に触るので監査 GO 無しに承認しない」。
>
> **Base**: `6e79ad4`(Golden は S-1 の現状で書き直し済み、rc=0)。`audit-core/` は触らない。Core は触らない。

## 1. 読んで確かめた事実(読むだけの調査 2 本。この節は予測ではなく材料)

### 1.1 E-3(`lib/seatOutput.ts`)は実物の 6 封筒で `validateHypothesisLine` に届いていない

`seatOutputProblems` は最初に封筒の schema を見て、落ちれば**早期 return** する(`lib/seatOutput.ts:220-221`)。実物 6 封筒は全部 `reach.sections[N]` に必須の欄 `seal` が無く、Golden の `g9.seatOutputCheck` の problems は 6 鍵とも `schema: … 必須の欄「seal」が無い` だけ(12〜13 行)。**E-1〜E-7 の本体(したがって E-3 の `validateHypothesisLine`、`:287`)は実物で 1 行も走っていない。** `!ok` の扱いは文字列を `problems[]` に積むだけで、封筒は書き換えない(`:288`)。`SeatOutputCheckOptions` に `packet` の欄は無い(`:198-205`)。

### 1.2 I-4(`lib/integration.ts`)は 4 周で走り、統合の代表の行を検査している

`integrationProblems` は束(cluster)ごとに `representative` を `validateHypothesisLine` に掛け(`:425`)、`!ok` の message を 1 件 1 行で `I-4: <cid> の representative <check>: <message>` と積む(`:426`)。`forVerification`/`heldBack`/`dropped` は書き換えない。`IntegrationCheckOptions` にも `packet` は無い(`:346-351`)。`52ae3745-20261001-1` の周には `integration.json` が無い(Golden の `g9.integrationCheck` は 4 鍵)。

**代表の行の packetRef 観測 156 件(4 周)は、全部が席の行の観測の写し**(司令塔の走査 `s2_rep_scan.py`: (path, value) の組が席の行に無いもの **0**)。C-2 の 1 回目の state に写すと **GROUNDED 139・VALUE_MISMATCH 16・POINTER_NOT_FOUND 1** = 6 束。

### 1.3 出口への伝播は、いまの配線では**無い**

- `lib/exitSelect.ts` が packet を渡す `buildSelectionDraft` は `scripts/playtest/exitSelect.ts --draft` 専用で、パイプラインの段 `exit-select`(`lib/deliver.ts:1563-1569`)は `answer_selection.json` 1 本しか渡さない。実物 `out/c5/exit/` に `answer_selection.draft.json` は無い。**現行で packet を見る唯一の本番の呼び口は、この材料では一度も走っていない。**
- 冊子の本編を埋める `report-pdf/exit_fill.py` は `integration.json` の代表の `statement` を itemRef で引くだけで、I-4 の problems も H-9 も見ない。採用 5 本のうち `I-3-009`(q1)が H-9 NG の席の項目(`H-c5-gpt558b-005`)と同じ束 C-005 を共有するが、I-4 は行を落とさないので**何も変わらない**。
- Golden の `g8` は送付済み PDF 4 本の封(ページ数・ベクタ・sha・ページごとの文の指紋)で、**PDF を組み直さない限り動かない**。Golden は組版を回さない。

### 1.4 S-1 の 21 件の原因(読むだけ。直していない)

| # | 件数 | 原因 | 一次証拠 |
|---|---|---|---|
| A | 18(VM、`rows[n].names`) | **席は潰していない。席に渡した `seat_input.md` が配列を `+` で潰して描いていた**(`lib/seatInput.ts:122-125` の `list()`、`:418-419`)。席の value は入力のセルと字面が完全一致。席の出力の器は配列を書ける(`run_summary.json` の `valueShape` に `array`)。指示文 v1.1 は「束にある値をそのまま写せ」と言い、例に `facts.recognition.rows[0].names` を挙げている → **指示と描画の矛盾** | 3 run・3 席で引用を確認 |
| B | 1(VM、`shallowVisibleGames` 25/24) | **席の書き間違い**。seat_input は 24 と正しく描いていた。席の `internal.reasoning` に「実際には 24」と自白 | `268dac98…/seat_input.md:308` |
| C | 1(VM、`groups.other.aheadThenLost.denominator` 2/4) | **packet の読み違い**。2 は `groups.noSignature` の分母。seat_input は別行に 4 と 2 を正しく描き、§0 に「分母は行の名前を読み替えない」とある。席の `internal.reasoning` に「分母 2 は署名なし」と自白 | `558b8a81…/seat_input.md:322, 326` |
| D | 1(PNF、`rows[3].reviewStatus`) | **描画が実在しない欄を出していた**。packet の builder は rows に `reviewStatus` を書かない(`lib/observationFacts.ts:457-476`)が、seat_input は列を無条件に描き `null` と出し、§0 が「null は packet でも null」と言う。既知事項(`docs/PLAN_VERIFIER_PACKET_2026-09-30.md:55`、`docs/AUTOMATION_STATUS_2026-09-26.md:636`)の残り | 席の `reach.sections` が `lastKey: reviewStatus` を報告 |

**情報損失か**: `observations[].value` を意味的に読む後段は H-9 と H-1 だけで、H-1 は文字列を見ない。名前を value から取り出す後段は無い(H-10/H-11 は散文の欄だけ、`exitSelect` は path だけ、`integration` は写すだけ)。**壊れるのは H-9 の一致だけ**。ただし packet を渡した `exitSelect` が動く配線になれば、A の 18 件は「正しく写した行が門で落ちる」になる(§6)。B・C の 2 件は H-9 が捕まえるべき席の誤りそのもの。

## 2. S-2 の範囲(狭く。Golden で測れる配線だけ)

| 直す所 | 直し | 直さない所 |
|---|---|---|
| `scripts/playtest/lib/seatOutput.ts` | `SeatOutputCheckOptions` に **`packet?: unknown`** を足し、`:287` の `validateHypothesisLine` に渡す。packet を**自分で読まない**(import も `readFileSync` も増やさない。`seatOutput.test.ts:193-200` の源の正規表現の試験が留めている) | E-1〜E-7 の規則、早期 return、封筒の schema |
| `scripts/playtest/lib/integration.ts` | `IntegrationCheckOptions` に **`packet?: unknown`**、`:425` に渡す。同じく自分で読まない(`integration.test.ts:267-273`) | I-1〜I-6 の規則、`forVerification`/`heldBack` の扱い |
| `scripts/playtest/goldenMasterCheck.ts` | `seatOutputProblems(…, {meta, request, today, packet})`・`integrationProblems(…, {today, packet})`(G-2 で読んだ `packet` を渡す。S-1 と同じ形) | 他の門 |
| `scripts/playtest/seatOutputCheck.ts`・`integrationCheck.ts`(CLI) | 任意引数 `--packet <path>`(無ければ今のまま) | 既定の挙動 |
| 試験 | `seatOutput.test.ts`・`integration.test.ts` に packet 有り/無しの対比を **+2〜4 本**(E-3 は `seal` の揃った合成の封筒で、I-4 は既存の `packet()` fixture で) | 既存の試験は書き換えない |
| ― | ― | **`lib/seatRun.ts:436/464`(実 run 時の checks.json)は S-3 の候補**。Golden では測れないので S-2 に入れない。`lib/exitSelect.ts`・`lib/deliver.ts`・`exit_fill.py`・契約 schema の説明文・`docs/STEP_LLM_SEATS_*` の文言(結果文書に「古くなった箇所」として列挙)・席の封筒・`c5_expectation.json`(書き直すかは人間) |

将棋側 5 ファイル + 試験 2 ファイル、**+15〜40 行**(試験を除く)。`audit-core/` 0。

## 3. 予測(封じる。§1 の材料から導いた)

### 3.1 Golden Master(`--expect docs/golden_master/c5_expectation.json`、書き直さない)

- **rc=1**。差は **`g9.integrationCheck.<周>.problems` の中だけ**。`g9.seatOutputCheck` は **差 0**(§1.1 の早期 return。6 鍵とも schema の行のまま)。`g9.hypothesisCheck`(S-1 で既に packet)・`exit_gate`・`check_answer`・`check_structure`・`g8`・`identity`・`packet`・`seat_runs` は **差 0**。
- 4 周の `status` は **`fail` のまま**、`return_code` 1 のまま。
- **差の件数 35**(Golden の diff は配列の長さの差を 1 件、既存の添字のずれを 1 件ずつ数える流儀。S-1 の外れから学んだ数え方で導いた): 0f1b019e **3**(長さ 2→3 の 1 + 添字 0,1)、268dac98 **10**(12→17 の 1 + 添字 3〜11)、558b8a81 **15**(15→22 の 1 + 添字 1〜14)、f37561e1 **7**(11→15 の 1 + 添字 5〜10)。H-9 の行は同じ束の H-1〜H-8 の行の直後に入り、後ろの行が全部ずれる、として数えた。**ずれた先で偶然同じ字になれば減る**(無いはず)。

### 3.2 I-4 の H-9(束 ID・観測単位。§1.2 の写しから機械的に導いた)

| 周 | 束 | 行の数 | 観測(at)と種類 |
|---|---|---|---|
| 0f1b019e-20261001-1 | C-005(heldBack) | **1** | observations[2] `facts.recognition.rows[3].reviewStatus` **PNF**(`が packet に無い`) |
| 268dac98-20260930-1 | C-005(heldBack) | **4** | observations[1..4] `rows[3|12|16|23].names` **VM** |
| 268dac98-20260930-1 | C-010(heldBack) | **1** | observations[0] `aggregates.branches.shallowVisibleGames.value` **VM**(25/24) |
| 558b8a81-20261001-2 | C-005(forVerification) | **1** | observations[1] `rows[0].names` VM |
| 558b8a81-20261001-2 | C-006(forVerification) | **1** | observations[0] `rows[0].names` VM |
| 558b8a81-20261001-2 | C-008(forVerification) | **5** | observations[0..3] `rows[3|12|16|23].names` VM + observations[5] `aggregates.groups.other.aheadThenLost.denominator` VM(2/4) |
| f37561e1-20260930-2 | C-005(heldBack) | **4** | observations[0..3] `rows[3|12|16|23].names` VM |
| 合計 | 6 束 / 4 周 | **17**(VM 16・PNF 1) | problems は 2→3・12→17・15→22・11→15 |

- 数え直し(`数え直し:`)の行 **0**(同じ (path, value) は S-1 で数え直し 0)。
- I-4 の **H-10 NG 0・H-11 は行に出ない**(H-11 は ok+notes で、I-4 は `!ok` の message しか積まない)。**H-10 は代表の文を整理役が書き直しているので粗い予測**(S-1 の席の行では 0。代表の文に認識 16 に無い名前が出れば 1 件以上出る)。
- 他の束(C-001 など)に H-9 の行は **0**(観測が全部 GROUNDED の写し)。

### 3.3 E-3 ― **0 行**(予測というより §1.1 の帰結)。packet を渡しても 6 封筒は schema で返る。**「E-3 への伝播」はこの材料では測れない**と先に書く。

### 3.4 顧客の出口(人間の問い「最終出口までどう伝播するか」への予測)

- **伝播しない。** g8 の 4 冊 差 0、`exit_gate`/`check_answer`/`check_structure` 差 0。理由は §1.3(I-4 は記録するだけ、出口の選別の packet 経路は走っていない、組版は I-4 を見ない)。S-2 で分かるのは「Core 化した結果は統合の検査の**記録**までは届き、**選別・組版には届かない**」こと。届かせるかは規則の変更(§6)。

### 3.5 その他

| # | 項目 | 予測 |
|---|---|---|
| a | `audit-core/` 差分 | 0 |
| b | typecheck:scripts | 既存の `out/` の赤 10 以外 0 |
| c | vitest | 既存 2327 本は落ちない(packet は任意の欄で、渡さない試験は skip のまま)。新規 +2〜4 → **2329〜2331** |
| d | 源の正規表現の試験 2 本(`seatOutput.test.ts:193`・`integration.test.ts:267`) | 緑のまま(import・readFileSync を増やさない) |
| e | 1 回目で予測と違う項目 | **0〜2**(疑うのは 3.1 の 35 件(normalize の掛かり方・偶然の一致)と 3.2 の H-10) |

## 4. 手順(3 役)

1. この文書を封(コミット)。
2. 実装担当(§2 の 5 ファイル + 試験。**作業木を書き換える git 操作を使わない。Golden・`seatOutputCheck.ts`・`integrationCheck.ts` を実物 c5 で回さない**。合成材料だけ。コミットしない)。
3. 司令塔が凍結し、**1 回目を 1 回だけ**: (a) Golden を回し差を `docs/golden_master/s2_first_run_diff.txt` に保存、(b) `--write` は scratchpad の一時コピーに向ける、(c) 新しい `g9.integrationCheck` の H-9 行を §3.2 と束・観測単位で突き合わせる(`s2_compare.py`)。
4. 独立監査 → GO でコミット → 結果文書。
5. **人間の判断**(§6)。

## 5. この文書がしないこと

席の封筒の修正。`seat_input` の描画(`list()`・`reviewStatus` 列)の修正。`seatRun.ts` の配線(S-3)。出口の選別・組版への配線。E-1〜E-7・I-1〜I-6・H-10/H-11 の規則の変更。期待値の書き直し。`audit-core/` の変更。

## 6. S-2 の後に人間が決める物(§1 の調査で出た。S-2 の範囲外)

| # | 問い | 材料 |
|---|---|---|
| (a) | **E-3 が実物で一度も走っていない**(6 封筒とも `reach.sections[].seal` が無く schema で返る)。席の出力に `seal` を書かせる(指示文/器)か、schema を緩めるか | §1.1。どちらも席の再実行か契約の変更 |
| (b) | **18 件の元 = `seat_input` の描画**(`list()` の `+` 連結)と **PNF 1 件 = 実在しない `reviewStatus` 列**を直すか。直しても **c5 の席ファイルは変わらない**(席を回し直さないと測れない = LLM の費用)。直すなら「描画を配列の字面(JSON)にする」か「H-9 側で `+` 連結を正規化する」か ― 後者は H-9 の厳密一致を緩めるので司令塔は推さない | §1.4 A・D |
| (c) | 数の差 2 件(席の書き間違い・分母の読み違い)は **H-9 が捕まえるべき誤りそのもの**。直す物は無い。席の指示文に「observations は埋め草を書かない」を足すかは席の指示文の版の話 | §1.4 B・C |
| (d) | **I-4/E-3 の H-9 NG を選別・組版に届かせるか**(いまは記録止まり。届かせるなら `forVerification` から外す/出口で `rejected` にする規則の変更。(b) を直す前に届かせると、正しく写した 18 件が落ちる) | §1.3、§3.4 |
| (e) | S-3 = `lib/seatRun.ts` の実 run 時の checks.json にも packet を渡すか(次の実 run で初めて測れる) | §2 |
