# Claim Contract Specification v0.1 ― Audit Core の「主張の契約」(2026-10-06、司令塔)

**この版の性格**: 設計書であって実装ではない。**Core のコード・データ・schema・試験は触らない。** 既存の門 6 種から契約の欄を写し、5 人目の冊子の実在の主張を当てて、形と修飾が足りるかを**測る**ための文書。測った結果(§7・§11)は、分解の前に封じた予測([CLAIM_CONTRACT_PREDICTION_2026-10-06.md](CLAIM_CONTRACT_PREDICTION_2026-10-06.md))と突き合わせる。
**前提**: [AUDIT_CORE_BOUNDARY_AUDIT_2026-10-06.md](AUDIT_CORE_BOUNDARY_AUDIT_2026-10-06.md)(確定監査。audit-platform は NO-GO、意味境界 I-4〜I-7 が未着手)と [AUDIT_CORE_EXTRACTION_PLAN.md](AUDIT_CORE_EXTRACTION_PLAN.md)。Base commit `13e3083`(T-5)。
**用語**: 英語の正準語 + 日本語定義(§1)。譲渡時の正本になるので、正準語は英語で固定する。

---

## 0. 先に結論(雑談 2026-10-06 で固まった設計の骨)

1. **Claim Type は「形(form)」と「修飾(modifier)」を分ける。** 形は 4 つ、修飾は形に付く条件。平らな列挙にしない(組み合わせの数だけ型が増える)。
2. **UNVERIFIABLE は形ではなく結果。** LLM が選べる型に入れない。契約の必須欄が揃わなければ Core が付ける。
3. **許容幅(tolerance)は検証器ではなく契約に置く。** 人が承認した数を字で留め、Core は機械的に適用する。
4. **PREDICTIVE は事前登録された証拠。** 予測の封じたコミットの時刻がデータ自身の事象時刻より前であることを機械で検査する。mtime は使わない。
5. **Claim Binding を Core の 10 番目の構成要素にする。** 顧客に見える主張は検証済み Claim に束縛されていなければならない。生成側(将棋)と監査側(他者の AI の出力)の 2 系統。
6. **実在の主張で埋めてから確定する。** 門 6 種 → 契約欄、5 人目の冊子 → Claim、予測を封じてから分解。

---

## 1. 用語(Canonical terms)

| Canonical term | 日本語 | 定義 |
|---|---|---|
| Claim | 主張 | 顧客(または人)が読む文のうち、元データか登録簿に対して真偽を問える最小の単位 |
| Claim Form | 主張形式 | 主張の形。`direct_value` / `derived_value` / `aggregate` / `threshold` の 4 つ(§3.1) |
| Claim Modifier | 主張修飾子 | 形に付く条件。証拠をどう引くかを決める(§3.2) |
| Claim Contract | 主張契約 | 形ごとの必須欄・正準データの要件・正規化・検証レシピ・許容幅・承認記録(§3.3) |
| Claim Span | 主張区間 | 顧客に見える文のうち、1 つの Claim に対応する文字列の範囲 |
| Claim Binding | 主張束縛 | 主張区間 ↔ Claim ID ↔ 検証結果の対応(§8) |
| Binding Rate | 束縛率 | 主張を持つ区間のうち Claim ID が結びついた割合(§8.3) |
| Canonical Source | 正準データ | 検証が値を取りに行く先。将棋では Observation Packet と登録簿 |
| Evidence Pointer | 証拠ポインタ | 正準データの中の場所(将棋では `packetRef.path`。文法は `lib/packetRef.ts`) |
| Canonical Fetch | 正準取得 | ポインタで値を再取得すること(`resolvePacketPath`) |
| Evidence Verification | 証拠検証 | 取得した値と主張の値を契約のレシピで比べること |
| Grounded | 根拠整合 | 検証の結果 1: 値が一致 |
| Value Mismatch | 値不一致 | 検証の結果 2: ポインタは在るが値が違う |
| Pointer Not Found | ポインタ不在 | 検証の結果 3: ポインタの先が無い |
| Unverifiable | 検証不能 | 検証の結果 4: 契約の必須欄が揃わない(**形ではない**) |
| Human Review | 人間確認 | UNVERIFIABLE を人が見る工程。内訳の札(§9)はここで付く |
| Prediction Ledger | 予測台帳 | 事前登録された予測とその照合(`PREDICTIVE` → `CONFIRMED` / `REFUTED` / `INCONCLUSIVE`) |
| Registration Time | 登録時刻 | 予測を封じたコミットの時刻(§10) |
| Event Time | 事象時刻 | データ自身が持つ時刻(将棋: KIF の開始日時。XBRL: 提出日) |
| Approval Record | 承認記録 | 閾値・許容幅・契約を人が承認したことの記録(コミット・文書の節) |
| Generation-side Binding | 生成側束縛 | 検証済み Claim から文を生成する束縛(将棋の冊子) |
| Audit-side Binding | 監査側束縛 | 他者の AI が書いた文に Claim を後から結びつける束縛(B2B) |

---

## 2. Core の構成(10 項目)

| # | 構成要素 | 将棋での現在地(確定監査 §3.2 の対応) |
|---|---|---|
| 1 | Claim Contract Registry(形・必須欄・正準データ要件・正規化・レシピ・許容幅・承認記録) | **無い。** 欄は門 6 種に散っている(§4) |
| 2 | Claim Validation(契約の必須欄が揃っているか) | 部分的: `hypothesis.ts` の schema 検査 + H-4(予測の欄)。H-1(数の実在)は検証に近い |
| 3 | Canonical Fetch | `resolvePacketPath`(observationPacket)。文法は `packetRef.ts`(I-6 待ち) |
| 4 | Deterministic Verification(レシピ + 承認済み許容幅) | H-9(値一致)、`recountProblems`(集計の再計算)、門 (xi)(集計行の数との照合)。**許容幅の概念は無い**(整数の完全一致) |
| 5 | Result State(4 状態) | **語が無い。** `CheckResult{check, ok, messages}` の形。確定監査 §6.2「H-9 の value 不一致 = VALUE_MISMATCH と読み替える」 |
| 6 | Provenance | `provenance.{sources, inputs, thresholds}`・`observationProvenance.ts`(T-4 済み) |
| 7 | Prediction Ledger | `prediction{writtenAt, window, metric, comparator, value}`(hypothesis v0.4)+ `status` enum(`verified`/`missed`/`unmeasured`/`expired`)。**INCONCLUSIVE に当たる語は無い**(`unmeasured` は「測っていない」で、「測ったが決められない」ではない) |
| 8 | Human Approval Gate | `reviewStatus`(`human_reviewed`/`expert_verified`)、`ANSWER_MENU`(承認済みの表)、CLAUDE.md 4 番の承認の委任 |
| 9 | Meta Audit(変異・回帰・境界) | Golden Master(T-1)、`core_boundary.test.ts`(T-2)、変異試験 |
| **10** | **Claim Binding**(§8) | 生成側だけ在る: 門 (xi) の `<!-- agg: -->`、(iii) `<!-- pos: -->`、(iv) `<!-- menu: -->`、(x) `<!-- ans: -->`、(vii) 固定文、型からの再構成(`fact_templates`)。**監査側は無い** |

---

## 3. Claim Contract の構造

### 3.1 Claim Form(4 つ)

| form | 主張の形 | 値 | 検証レシピの核 |
|---|---|---|---|
| `direct_value` | 「X は v である」 | 1 つの値(数・文字列・列挙) | ポインタで取得 → 正規化 → 比較 |
| `derived_value` | 「X から計算すると v である」 | 式と入力の値 | 入力を取得 → 式を再計算 → 許容幅つき比較 |
| `aggregate` | 「母集団 P のうち条件 Q を満たすものが n(/ d)」 | 件数・分子分母・合計 | 母集団を選び直して数え直す(`selectRows/countOf/sumOf`) |
| `threshold` | 「値 v は線 t を上回る / 下回る」 | 真偽(比較の結果) | 値を取得(または再計算)→ 承認済みの線と比較子で判定 |

### 3.2 Claim Modifier(形に付く条件)

| modifier | 何を決めるか | 将棋での対応 |
|---|---|---|
| `population` | 母集団の表と絞り込み(where)・分子の絞り込み(numeratorWhere) | `aggregates[].population.{from, where}`・`numeratorWhere` |
| `time_range` | 事象時刻の範囲・基準日 | (将棋の 25 局では局の日時を使った主張が無い。§7 で測る) |
| `normalization` | 値の正規化(単位・語彙への写し・丸め) | `unit` enum、tags/side → 日本語(`SIDE_JP`)、手の表記 |
| 予測で足すとした候補 | `source_kind`(packet / 登録簿 / 文書自身 / 承認済み固定文 / 人間の文)、`join`(表を鍵で結ぶ) | §7 で要るかを測る |

### 3.3 Claim Contract の欄(形ごとに必須が違う)

| 欄 | direct | derived | aggregate | threshold | 意味 |
|---|---|---|---|---|---|
| `claim_id` | ✔ | ✔ | ✔ | ✔ | 一意の id |
| `form` | ✔ | ✔ | ✔ | ✔ | 4 つのうち 1 つ |
| `span` | ✔ | ✔ | ✔ | ✔ | 顧客に見える文の区間(行・文字範囲) |
| `subject` | ✔ | ✔ | ✔ | ✔ | 何についてか(顧客・局・局面・集計の id) |
| `value` | ✔ | ✔ | ✔(n, d) | ✔(真偽) | 主張している値 |
| `pointer` | ✔ | ✔(入力ごと) | ✔(集計 id または母集団の定義) | ✔(値の pointer) | Evidence Pointer |
| `source_kind` | ✔ | ✔ | ✔ | ✔ | 正準データの種類 |
| `unit` | △ | ✔ | ✔ | ✔ | 単位 |
| `formula` | ― | ✔ | ― | ― | 式(入力 id → 出力) |
| `population` | ― | ― | ✔ | △ | 母集団の定義 |
| `threshold_ref` | ― | ― | ― | ✔ | 線の id(`provenance.thresholds` か承認済みの表) |
| `comparator` | ― | ― | ― | ✔ | `<`, `<=`, `>`, `>=`, `==` |
| `tolerance` | △ | ✔ | ― | ― | 許容幅(人が承認した数。字で留める) |
| `approval_record` | ― | △(式) | ― | ✔(線) | 承認記録への参照 |
| `normalization` | △ | △ | △ | △ | 正規化の規則の id |
| `registration_time` | ― | ― | ― | ― | 予測のときだけ(Prediction Ledger 側) |

必須(✔)が 1 つでも欠ければ **Claim Validation で落ち、結果は UNVERIFIABLE**。△は在れば使う。

### 3.4 結果状態(Core が付ける。LLM は選べない)

```
Claim(form + modifiers)
  ↓ Claim Validation(必須欄)
  ├─ 揃わない ─────────────────────────→ UNVERIFIABLE → Human Review(内訳の札 §9)
  └─ 揃う → Canonical Fetch
            ├─ ポインタの先が無い ───────→ POINTER_NOT_FOUND
            └─ 在る → Deterministic Verification
                      ├─ 一致(許容幅内)─→ GROUNDED
                      └─ 違う ──────────→ VALUE_MISMATCH
```

---

## 4. 門 6 種の採取と契約欄への転記(手順 1・2)

門 6 種 = Golden Master `c5_expectation.json` の `g9` の 6 つ(`exit_gate` / `check_answer` / `check_structure` / `hypothesisCheck` / `seatOutputCheck` / `integrationCheck`)。それぞれの検査を「何を数え・何と比べ・どの条件で・どのデータを参照し・どこまで機械で決めるか」で写す。**門に無い契約欄**を最後に数える。

### 4.1 `exit_gate`(機構 `exit_verification.py` (i)〜(xi)。定数は Adapter `exit_gate.py` が `GateRules` で渡す)

| 検査 | 何を数える | 何と比べる | 条件 | 参照データ | 機械判定の範囲 | 契約欄への写し |
|---|---|---|---|---|---|---|
| (i) `check_todo` 161 | `todo_marker` の出現数 | 0 | 書いた側の記録も含む | 文書自身 | 全部 | `aggregate`(source_kind=文書、value=0 を要求 = threshold) |
| (vii) `check_opening` 171 | 冒頭の固定文の出現数(文ごと) | ちょうど 1 | 候補 JSON `opening` | 承認済み固定文 + 文書 | 全部 | `direct_value`(source_kind=承認済み固定文。文字列の完全一致) |
| (ii) `check_p1` 188 | 節 P1 の箇条書きの本数 / 節の中の数 | 本数 = `p1_fact_count`(3) / 数 ⊂ `p1Numbers` | 下書きだけの節は外す | 文書 + 候補 JSON | 全部(ただし「数」の拾い方 `scan_numbers` は将棋側) | `aggregate`(文書)+ 「数が候補に在る」= `direct_value` の集合版 |
| (viii) `check_p1_reaches_the_actions` 222 | 行動の根拠の分数(分子・分母)が事実の行に出ているか | 届かない事実 ≤ 許容(0 か 1) | 固定文が節に在れば 1 本許す | 文書 + `actionFractions` | 全部 | **Claim Binding の規則**(主張どうしの対応。契約欄ではなく束縛の欄) |
| (ix) `check_no_unit_mismatch` 264 | 単位が違う分数の文字列の出現 | 0 | `unitMismatchFractions` | 文書 + 候補 JSON | 全部 | `normalization`(単位)の違反の検出 = 契約の `unit` 欄 |
| (iii) `check_p2` 283 | 盤の印の数 / 印が候補に在るか | ちょうど 2 / ⊂ `boards` | ― | 文書 + 候補 JSON | 全部 | `aggregate`(文書)+ `direct_value`(pointer = 局/手目/付録) |
| (iv) `check_p3` 302 | 行動の印 | ⊂ `menuPassed` | ― | 文書 + 候補 JSON | 全部 | `direct_value`(source_kind=登録簿 `ANSWER_MENU` + 下限を通った集合) |
| (vi) `check_draft_leftovers` 320 | 下書きの見出し・書き手への注の出現 | 0 | ― | 文書 | 全部 | `aggregate`(文書)value=0 |
| (x) `check_ans_tags` 401 | 問いごとの印の数 / 印の場所 / 状態の語 | ちょうど 1 / 節の中 / `answer_selection` と一致 | request が無ければ報告だけ | 文書 + request + selection | 全部(形が違えば落とす) | `direct_value`(状態の語。source_kind=採用の記録)+ 束縛の規則(問い ↔ 印) |
| (xi) `check_agg_tags` 531 | 印の行の数 | 集計行の `value/numerator/denominator` に在るか | 型に当たれば穴の数だけ。倍割の語の行は照合しない。0 と % は拾えない | 文書 + packet.aggregates | **部分**(0・%・倍割は見ない ― docstring に明記) | **生成側 Claim Binding の実体**(`<!-- agg: id -->` = Claim ID)。`aggregate` の pointer = 集計 id |
| `check_sentences`(呼ぶ側が渡す。= `check_answer`) | ― | ― | ― | ― | ― | §4.2 |

### 4.2 `check_answer`(検査 1〜7。[DELIVER_GATES.md](DELIVER_GATES.md) §2.3)

| 検査 | 何を数える | 何と比べる | 条件 | 参照データ | 機械判定の範囲 | 契約欄への写し |
|---|---|---|---|---|---|---|
| 1 数の照合 `check_line_numbers` 1643 | 「a / b」「n のうち m」の組・単位つきの数 | 登録済みの組 / 材料 JSON の値 | 9 以下の単独の数と日付は対象外。倍・割は常に落ちる | 材料 JSON | 部分(小さい数・日付を見ない) | `aggregate`(分数)+ `direct_value`(単位つきの数) |
| 2 手の答え合わせ `check_line_moves` 1659 | ▲△ で始まる手 | 付録 PDF の印字 | 「第 1 候補は」なら同じ段落に「n 局目 m 手目」 | 付録 PDF の文字 | 全部 | `direct_value`(pointer = 局/手目、source_kind = 付録 = 文書) |
| 3 禁止語 `check_line_banned` 1671 | 禁止語の出現 | 0 | 断定の形は機械で見ない(人間の決定) | 語の表 | **部分**(断定は人が読む) | 契約欄ではなく **文の形の規則**(H-5 と同族) |
| 4 行動のメニュー `check_menu_tags` 1710 | 印の外の行動の言い方 9 語 / 印の M の条件と分母 | 0 / `MENU_HOLDS`・`minN` | 太字だけの見出しは対象外 | `ANSWER_MENU`・材料 | 部分(**印の隣の文が承認済みの文言と合うかは見ない** ― §2.5) | `direct_value`(source_kind=登録簿)+ `threshold`(minN) |
| 5 数が足りなければ言わない | 選んだ M の分母 | ≥ `minN` | ― | 材料 | 全部 | `threshold`(threshold_ref = minN、approval = 承認済みの表) |
| 6 戦法・陣形の名前 `check_line_names` 1694 | 名前らしい語(`NAME_LIKE_RE`) | `review_status` ∈ {human_reviewed, expert_verified} | 「〜のような形」なら通す | `data/shapes` 等 | 部分(接尾辞の規則で名前を拾う) | `direct_value`(source_kind=登録簿、承認状態つき) |
| 7 局面の参照 `check_pos_tags` 1765 | `<!-- pos: -->` の局/手目/付録 | その付録に盤が印字される局面 | 付録 4 は常に落ちる。宣言を忘れた参照は見ない | 付録 PDF の索引 | 部分(宣言されたものだけ) | 束縛の欄(主張区間 ↔ 盤) |

### 4.3 `check_structure`(冊子の形。関数名は `check_structure.py`)

| 検査 | 何を数える | 何と比べる | 参照データ | 契約欄への写し |
|---|---|---|---|---|
| `check_sections` 310 | `## ` の見出しの役割の並び | `SECTIONS` | 文書 | 文書の形(契約ではない) |
| `check_verify_table` 344 | 答え合わせの表の行 | 行動と同数・列の形 | 文書 | **Prediction Ledger の登録の形**(§7 で C-32 として測る) |
| `check_pages` 378 / `check_appendix_pages` 461 / `check_bundled_index` 498 | ページ数・付録の索引 | 上限 5 / 25 / 30、索引と実体の一致 | PDF | 文書の形 |
| `check_boards` 447 | 盤の数 | 2 | PDF | `aggregate`(文書) |
| `check_sample_difference` 406 | 本人用と見本用の差 | 対応表だけ | PDF | 文書の形 |
| `check_name_agrees` 562 / `check_no_real_name` 602 / `check_one_referent` 630 | 呼び名・実名 | 一致 / 0 / 1 種類 | PDF + person | `direct_value`(語彙)・`aggregate`(文書)value=0 |
| `check_scope_and_mapping` 661 | 商品の範囲の文・対応表の局数 | 固定文・`games` | 文書 | `direct_value`(固定文)+ `aggregate` |
| `check_term_lines` 684 | 用語の説明の出現 | ちょうど 1 | 文書 | `aggregate`(文書)。**c5 の G-9 ではここが落ちている**(用語 4 語が 0 か所 ― 冊子の形が変わった後の門の古さ) |
| `check_question_section` 781 | 問いの節 | 問いが在れば節が在る・200 字以内 | 文書 + request | 文書の形 |

### 4.4 `hypothesisCheck`(H-1〜H-11。`lib/hypothesis.ts`)

| 検査 | 何を数える | 何と比べる | 参照データ | 機械判定の範囲 | 契約欄への写し |
|---|---|---|---|---|---|
| schema | 契約 v0.4 の形 | JSON Schema | ― | 全部 | **Claim Validation の原型**(必須欄) |
| H-1 数の実在 311 | statement の数 | `observations[].value` | 観測の値は数値だけ(文字列の中の数は拾わない)。ISO 日付から数を拾う(Python と規則が違う) | 行の中 | 部分(言語で規則が違う) | `value` ↔ `pointer` の対応(Binding の最小形) |
| H-2 ID の登録 416 | `obsId` | 登録簿(`OBSERVATION_ITEMS.md`) | ― | 登録簿 | 全部 | `pointer` の文法と実在(登録簿) |
| H-3 反証の記録 508 | `counterEvidence.attempted` | true | ― | 行の中 | 全部 | **仮説の工程の欄**(契約の欄ではない。Prediction Ledger の前段) |
| H-4 予測は数で測る前に 524 | `prediction{metric, comparator, value, window, writtenAt}` | 必須 | kind で免除あり | 行の中 | 全部 | **Prediction Ledger の登録の必須欄**(§10) |
| H-5 禁止語・断定しない形 554 | 読みの語尾 | 「という読みです」「可能性があります」 | ― | 行の中 | 全部(日本語前提 ― 確定監査 H-1) | 文の形の規則 |
| H-6 盲検 580 | 入力の由来 | 他レーンの出力・本人の言葉を含まない | ― | provenance.inputs | 全部 | 工程の規則 |
| H-7 昇格 606 | `knowledge.reviewStatus` | human_reviewed 以上だけ beginners_general に | ― | 行の中 | 全部 | `approval_record`(知識の) |
| H-8 人名・絶対パス 622 | 文字列 | 0 | ― | 行の中 | 全部 | 文の規則 |
| H-9 packetRef の実在と値 676 | `packetRef.path` の先の値 | `observations[].value` と一致 | 文法は H-2 | packet | 全部 | **Deterministic Verification そのもの**(GROUNDED / VALUE_MISMATCH / POINTER_NOT_FOUND の 3 つを `messages` の字で返す) |
| H-10 名前 748 | 散文の名前 | `facts.recognition.definitions` の名前 | 登録簿に無い名前は落とせない(既知の穴) | packet | 部分 | `direct_value`(語彙。source_kind=packet の認識) |
| H-11 名前の段 921 | 名前の `reviewStatus` | 印だけ(落とさない) | ― | packet | 全部 | `approval_record` の表示 |

### 4.5 `seatOutputCheck`(E-1〜E-7。`lib/seatOutput.ts` 227〜326)

| 検査 | 何を見るか | 契約欄への写し |
|---|---|---|
| E-1 到達 | 席が読んだ節の封(`seal`) | 入力の provenance(Claim の `pointer` が指す packet が席の読んだものと同じか) |
| E-2 答え | 問いごとの答えの状態 | Prediction Ledger / UNVERIFIABLE の語(`unanswerable`・`needed_observation`・`partial`) |
| E-3 行 / E-4 文法 | 行ごとに schema + H-1〜H-8、packetRef の文法 | Claim Validation |
| E-5 隔離 / E-6 内部 | 除外入力・`internal.reasoning` が外に出ない | 工程の規則(§8.2 の「内部推論は顧客の文へ流れない」) |
| E-7 run | run の同一性 | provenance |

### 4.6 `integrationCheck`(I-1〜I-8。`lib/integration.ts` 387〜474)

| 検査 | 何を見るか | 契約欄への写し |
|---|---|---|
| I-1 全項目がちょうど 1 回 | 席の項目の束ね漏れ・重複 | 束縛の規則(項目 ↔ 束) |
| I-2 束の根 / I-3 一致は証拠でない / I-4 代表の行 | 束の代表が H-3・H-5 を満たす、複数席の一致を証拠に数えない | 工程の規則(CLAUDE.md 8 番 (2)) |
| I-5 問い | 機械で決まる内訳と一致 | E-2 と同じ |
| I-6 隔離 / I-7 席名 / I-8 run | 除外・名前・run | provenance |

### 4.7 門に在る欄 / 無い欄(集計)

**門が持っている契約欄**: `value`、`pointer`(集計 id・packetRef・局/手目・問い id・M の id)、`population`(集計行の `population`・`numeratorWhere`)、`unit`(enum)、`threshold_ref`(`provenance.thresholds` 6 本・`minN`)、`comparator`(集計の `op`、予測の `comparator`)、`source_kind` に当たる区別(packet / 候補 JSON / 登録簿 / 付録 PDF / 文書自身 ― **ただし欄としては無く、門ごとに引数が違う**)、承認状態(`reviewStatus`)、予測の欄(H-4)。

**門のどれも持っていない欄**(予測 §2 の 4 つ + 実測で足したもの):

| 欄 | 無いとどうなるか(c5 で実際に起きていること) |
|---|---|
| `approval_record`(線・許容幅の承認) | 線 0.7・「2 つぶん」が「道具の仮置き」のまま顧客に出ている(本編 32・34 行)。`provenance.thresholds` には無い。門は「仮置きか承認済みか」を区別しない |
| `tolerance` | 整数の完全一致しか無い。割合(%)は門 (xi) が照合しない(docstring)。XBRL の「約 15%」はこのままでは全部落ちる |
| `source_kind`(欄として) | 門ごとに引数で渡しているので、Claim 1 件を見て「どこから取ったか」が分からない。監査側 Binding(§8.2)では必須 |
| `registration_time` / `event_time` | 予測の `writtenAt` は文字列で、コミット時刻やデータの事象時刻と機械で比べていない(§10) |
| 主張どうしの整合 | C-17 と C-36c(§7)のように、本編の 2 文が両立しない組を門は見ない(集計の整合関係 (5) は集計行の間だけ) |

---

## 5. 5 人目の冊子の実在の Claim(手順 3。**分解していない** ― 原文の区間と行番号だけ)

対象: `scripts/playtest/out/c5/deliver1/9_本編.md`(sha256 `eb4c0b1e…`、Golden Master の identity と同じ)。行番号は `cat -n`。**顧客に見える文のうち、元データか登録簿に対して真偽を問える区間**を単位にした。固定文(4〜6 行)・人間の注(29 行)・見出しは単位にしない(§8.3 の分母の定義に関わるので、数だけ記す: 固定文 4 文・人間の文 1 文)。

| id | 行 | 原文の区間(要約でなく抜粋) |
|---|---|---|
| C-01a | 3 | 「3 分切れ負け 25 局を … 調べました(2026-09-28)」 |
| C-01b | 3 | 「1 手ずつ将棋エンジンで」 |
| C-02 | 10 | 「第 1 候補と違う側になった局面が両方の側に残り」 |
| C-03 | 10 | 「長考の直後の 1 手は崩れやすく」 |
| C-04 | 10 | 「一度良くなった局を落としていた」 |
| C-05 | 10 | 「(普段と違う型の 4 局で目立った)」 |
| C-06 | 10 | 「数は 3 つ」 |
| C-07 | 12 | 「第 1 候補が攻めの手だった分かれ道 107 局面のうち、実戦も攻めの手だった局面が 65」 |
| C-08 | 12 | 「第 1 候補が自玉側の手だった分かれ道 132 局面のうち、実戦も自玉側の手だった局面が 76」 |
| C-09 | 12 | 「どちらの一致率も、道具が仮に置いている線(0.7)を下回りました」 |
| C-10 | 12 | 「一方の側への偏りではなく、両方の側で第 1 候補と違う側になった局面が残った」 |
| C-11 | 13 | 「直前の自分の手が 10 秒以上で、この手は 4 秒以内だった 37 手のうち、崩れた手が 9」 |
| C-12 | 13 | 「0〜1 秒で指した 531 手では崩れが 22 手」 |
| C-13 | 13 | 「長考の直後の 1 手は、それより崩れる割合が高かった」 |
| C-14 | 14 | 「一度は優勢(+300 以上)になった対局が 18 局」 |
| C-15 | 14 | 「そのうち負けた対局が 6 局」 |
| C-16 | 14 | 「負けた局の多くは、初めから悪かったのではなく、一度は良くなってからのもの」 |
| C-17 | 14 | 「優勢になった後の局面を分けて数えた材料がまだ無い」 |
| C-18 | 14 | 「次の 25 局で分けて数えます」 |
| C-19 | 18 | 「第 1 候補と実戦の側が逆だった分かれ道(25 局で 51 局面)」 |
| C-20 | 18 | 「攻めと自玉側を 1 つずつ選びました」 |
| C-21 | 20 | 「11 局目 48 手目 ― 実戦 ▲４四歩打(自玉側に駒を打つ手)、第 1 候補は ▲８七歩成(攻めの側で駒を取る手)」 |
| C-22 | 22 | 「12 局目 70 手目 ― 実戦 ▲３三角(攻めの側で駒を取る手)、第 1 候補は ▲４三歩打(自玉側に駒を打つ手)」 |
| C-23a | 26 | 「2 つです」 |
| C-23b | 26 | 「判定で差が確認でき、次の 25 局で同じ数を測り直せるものだけ」 |
| C-24 | 28 | 行動 1 の文(M4)+「根拠は … 65 / 107 … 76 / 132」 |
| C-25 | 30 | 行動 2 の文(M5)+「根拠は … 9 / 37」 |
| C-26 | 32 | 「道具の仮置きの線は 0.7 … どちらも線を下回ったので行動にしました」 |
| C-27 | 32 | 「10 秒以上考えた手 61 手のうち分かれ道は 33 手、そのうち側が逆は 5 手」 |
| C-28 | 32 | 「全部の分かれ道 239 局面のうち逆は 51 局面」 |
| C-29 | 32 | 「逆の多くは 10 秒未満で指した手でした」 |
| C-30 | 34 | 「線は「0〜1 秒で指した手のうち崩れた手」(22 / 531)の 2 つぶん … 9 / 37 … 上回ったので行動にしました」 |
| C-31a | 36 | 「駒を打つ手(54 局面)」 |
| C-31b | 36 | 「比べる線がまだ無く」 |
| C-31c | 36 | 「駒を捨てる手は分母の数え方を確かめ直している」 |
| C-32 | 40〜43 | 答え合わせの表(試したこと / 動くはずの事実 / いまの値 65/107・76/132・9/37) |
| C-33 | 47 | 「崩れ」の定義(「区分が 1 段以上下がった」「+300 以上を優勢、−300 以下を劣勢」) |
| C-34a | 48 | 「普段の型 18 局・普段と違う型 4 局・型が取れない 3 局」 |
| C-34b | 48 | 「戦型の名前は定義が下書きなので付けていません」 |
| C-35 | 52〜54 | 群の表 3 行 × 4 列(12(3) 56 70(38) 111(65) / 4(3) 18 29(20) 15(8) / 2(0) 5 8(7) 6(3)) |
| C-36a | 56 | 「4 局は 4 局とも一度は優勢になり 3 局を落とし」 |
| C-36b | 56 | 「崩れも 18 回(普段の型は 18 局で 56 回)と 1 局あたり多く出ました」 |
| C-36c | 56 | 「優勢になってからの崩れが、普段と違う型の局で出やすかった」 |
| C-37 | 67〜76 | 分母の表 10 行(25・107・132・37・54・0.7・531・61・33・239) |
| C-38 | 82〜106 | 対応表 25 行(ファイル名・先後・手数・結果) |

単位 45(a/b/c を分けて)。

---

## 6. 予測の封印(手順 8)

予測は [CLAIM_CONTRACT_PREDICTION_2026-10-06.md](CLAIM_CONTRACT_PREDICTION_2026-10-06.md)。**§7 を書く前にコミットする**(Registration Time = そのコミットの時刻。§11 にコミット id を書く)。

---

## 7. 分解の結果(手順 4・9。**§6 のコミットの後に書く**)

(封印後に埋める)

---

## 8. Claim Binding(手順 5・6)

### 8.1 生成側束縛(Generation-side Binding。将棋の冊子)

```
packet.aggregates[id] ──→ 型(fact_templates / AHEAD_THEN_LOST_TEMPLATE)──→ 文 + <!-- agg: id -->
承認済みの表 ANSWER_MENU ──→ 行動の文 + <!-- menu: Mx -->
facts.engine[i] ──→ 盤の見出し + <!-- pos: 局/手目 付録 組 -->
answer_selection ──→ 問いの答え + <!-- ans: qN 状態 -->
固定文 opening ──→ 冒頭 4 文(門 (vii) がちょうど 1 回を確かめる)
```

文は検証済みの値から**生成**されるので、束縛は構造で成り立つ。門 (xi) は印の行の数が集計行の数に在るかを**後から**確かめる(生成と検査を 2 つにしない: `agg_line_missing` は 1 か所)。
**穴**(§4.7): 読みの文(「― 読み: 」以降)は型ではなく、数の照合だけ。比較の語(多く・高かった・目立った)は束縛されない。

### 8.2 監査側束縛(Audit-side Binding。他者の AI の出力。**将棋には無い**)

```
他者の AI の文
  ↓ Claim Extraction(LLM。区間 → Claim の候補。form と modifiers を書く。UNVERIFIABLE は書けない)
  ↓ Claim Validation(必須欄)
  ↓ Canonical Fetch → Deterministic Verification
  ↓ 札を貼る(GROUNDED / VALUE_MISMATCH / POINTER_NOT_FOUND / UNVERIFIABLE)
  ↓ 出力は止められない ― 束縛率と結果の分布を出す
```

- 抽出は LLM の工程なので、**抽出の失敗と本当の検証不能を機械は区別できない**。区別は §9 の人の確認の表で人が付ける札。
- 抽出の規則: 区間ごとに**ちょうど 1 つ**の Claim か「主張を持たない」の札。修飾を落とした抽出(「約 15%」→「15%」、「長考の後に崩れた」→「崩れた」)を捕まえる唯一の手は、原文の区間を Claim の横に並べること(§9 の列 1 と 2)。
- 抽出器が `internal.reasoning` に当たる欄を持つなら、CLAUDE.md 8 番 (3) と同じく下流の schema に含めない。

### 8.3 束縛率(Binding Rate)の契約

| 数 | 定義 | 分母の出どころ |
|---|---|---|
| 主張区間数 | 文書のうち、主張を持つと判定された区間の数 | 生成側: 型と印の数。監査側: 抽出器の出力(人が確認) |
| 束縛数 | Claim ID が結びついた区間の数 | ― |
| **Binding Rate** | 束縛数 / 主張区間数 | 固定文・人間の文・見出しは分母に入れない(§5 の数え方) |
| 検証通過率 | GROUNDED / 束縛数 | 分母は束縛数(主張区間数ではない ― 「一致率を 2 つ並べて比べない」) |
| UNVERIFIABLE 率 | UNVERIFIABLE / 束縛数 | 内訳は §9 の札で分ける |
| 未束縛区間 | 主張区間 − 束縛 | 一覧で出す(数だけにしない) |

**通過率は束縛率と一緒にしか意味を持たない。** 束縛率が低ければ、通過率は「束縛できた易しい主張の通過率」でしかない。

---

## 9. 人の確認の表(手順 7。列の定義まで。画面は設計しない)

| 列 | 中身 |
|---|---|
| 1 原文の区間 | 行番号と文字列(顧客が読む字そのもの) |
| 2 Claim ID | 束縛された id(無ければ空 = 未束縛) |
| 3 Form | 4 つのうち 1 つ |
| 4 Modifiers | 付いた修飾(population / time_range / normalization / …) |
| 5 Evidence Pointer | packet の path・集計 id・登録簿の id |
| 6 判定 | GROUNDED / VALUE_MISMATCH / POINTER_NOT_FOUND / UNVERIFIABLE |
| 7 内訳の札(人が付ける) | UNVERIFIABLE のとき: `extraction_failure` / `binding_failure` / `genuinely_unverifiable`。GROUNDED のとき: `claim_matches_span` / `claim_narrower_than_span`(修飾が落ちた) |

**札は捨てずに溜める。** 列 7 の蓄積が抽出器の性能を測る唯一のデータで、ラベル付きデータセット(資産)の原型。

---

## 10. 時刻の契約(Registration Time / Event Time)

| 時刻 | 出どころ | 将棋(c5) | XBRL(候補) |
|---|---|---|---|
| Registration Time | 予測を封じた**コミットの時刻**(`git log --format=%ci`) | 6 周目の封 `SEALED_READING_C5_EXIT_R6`(2026-09-29)。本仕様の予測は §11 のコミット | 同じ |
| Event Time | **データ自身が持つ時刻** | KIF の `開始日時`(将棋ウォーズが付けた。c5 は 2026/09/25 08:33 〜 2026/09/26 12:12) | 提出日 |
| 使わない | ファイルの mtime・`generatedAt` だけの文字列 | (`done-check-must-see-code` の実測: mtime 比較は 5 段ぜんぶ外れた) | ― |

PREDICTIVE の成立条件: `registration_time < min(event_time of 照合に使うデータ)`。
照合の結果 3 値: `CONFIRMED` / `REFUTED` / `INCONCLUSIVE`(標本が契約の最小数に届かない)。現行の `status` enum には `INCONCLUSIVE` に当たる語が無い(`unmeasured` は別の意味)― 契約の版上げは人間の承認(CLAUDE.md 4 番)。

---

## 11. 予測と実測の照合(手順 10。**§7 の後に書く**)

(封印後に埋める)

---

## 12. Core 変更の分類(手順 11。2 つ目の Adapter を繋ぐときに数える表)

| 分類 | 意味 | 合格の読み方 |
|---|---|---|
| 0 | 既存 Core で表現可能(変更なし) | 完全互換 |
| 登録追加 | Claim Form / Modifier / Recipe / Contract を登録簿に足しただけ | 想定内 |
| インターフェース拡張 | Core の入力契約(引数・schema の任意欄)を広げた | 黄 ― 境界が足りなかった |
| 意味変更 | Core の検証の意味(比較・状態機械・結果の語)を変えた | 赤 ― 将棋が Core に漏れていた |

**0 を合格条件にしない。** 分類ごとの本数を予測してから繋ぎ、外れを記録する(§11 と同じ型)。

---

## 13. 埋めながら決める論点(3 つ。仕様に残す)

1. **Claim Binding の向き**: 生成側は将棋に在る。監査側は無く、製品になるのはこちら。束縛率・UNVERIFIABLE の内訳・原文との対照表示は監査側の仕様(§8.2・§8.3・§9)。
2. **門 6 種がレシピの最初の下書き**: 門に無い契約欄(§4.7)は将棋が持っていない情報で、XBRL で初めて試される。
3. **表現可能性は予測してから測る**: §6 → §7 → §11。設計した席と予測した席と埋める席が**同じ**(司令塔)であることを明記する。独立性が要るなら、埋める工程を別の席に出す。

## 14. この版が見ていないもの

- Core のコード・schema・試験は 1 文字も変えていない。`INCONCLUSIVE`・結果状態の語・`tolerance` の欄は**提案**で、契約の版上げは人間の承認。
- XBRL は調べていない(EDINET の API・XBRL の構造・利用条件は実物で確かめてから 2 つ目の Adapter に採用する)。
- 監査側束縛の抽出器は設計していない(LLM をどう使うかは別途)。
- `check_structure` の c5 での落ち(用語 4 語・問いの節)は冊子の形の話で、本仕様の対象外。
