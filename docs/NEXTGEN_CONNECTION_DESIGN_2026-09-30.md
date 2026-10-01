# 設計案 ― 次世代分析パイプラインを、いま在る部品のどこに接続するか(2026-09-30。設計専用セッション)

**位置づけ**: [NEXTGEN_DESIGN_SESSION_BRIEF_2026-09-30.md](NEXTGEN_DESIGN_SESSION_BRIEF_2026-09-30.md) §3 の「出すもの」。上位の正本は [NEXTGEN_PIPELINE_BRIEF_2026-09-29.md](NEXTGEN_PIPELINE_BRIEF_2026-09-29.md)(5 層・流れ・人間の 4 つの直し + 2 点・作るもの 5 つ・変えない線)。**この文書は設計案だけで、実装・schema・データを 1 つも変えていない。** 進行中の束(packet B/C・3 席 API 計画)の schema に触れる提案は §5 に「提案」として分け、司令塔へ回す。

**読み方**: §1 が「顧客の PDF にどう出るか」、§2 が段ごとの接続表(指示書 §3 の表そのもの)、§3 が指示書が「特に決めてほしい」と言った 5 点、§4 が判断が要る点の一覧、§5 が進行中の束への提案、§6 が変えない線との照合、§7 が引いた数と測っていない数の区別。

---

## 1. 顧客の PDF にどう出るか(先に書く)

この設計が入ると、次の顧客(3 切れ 25 局か 10 切れ 25 局)の PDF は次の 5 点だけ変わる。それ以外の見た目(6 節の順・盤 2 つ・行動 + 答え合わせ・数え方・対応表)は正本([GOLDEN_MASTER_CUSTOMER_EXIT.md](GOLDEN_MASTER_CUSTOMER_EXIT.md))のまま。

| # | 変わる点 | 顧客に見える形 | 出どころ(指示書 §1 の番号) |
|---|---|---|---|
| 1 | 「第 1 候補」の 1 行定義が、本編 1 ページ目の冒頭段落の**最後の文**に固定で入る | 冒頭 4 文が 5 文になる。「ひとことで」の太字(初出)より前に定義が来る | 1 |
| 2 | 顧客の問いへの答えが、「ひとことで」の**直後の節**に出る(「明確な差は確認できませんでした」も同じ場所に出る) | 節「お預かりした問い」が 1 つ増える(問いが無い顧客では節ごと出ない) | 4・8 |
| 3 | 送付用の名前が `01_本編_対局後診断_{組の名}{局数}局.pdf`・`02_付録_数の出どころ_{組の名}{局数}局.pdf` になる | 一覧で本編が上に来る(実測: 5 人目の送付フォルダでは付録が上に来ており、本人が付録から開いた)| 2・10 |
| 4 | 「数の分母がどこから来たか」の表が本編から**付録の表紙の次のページ**へ移る | 本編 4 ページ目が空く(器の余裕 0 の直し)。付録は 1 ページ増える | 3・7 |
| 5 | 10 切れの顧客では、時間の指標(10 秒以上・4 秒以内・0〜1 秒)が**線が未定の間は出ない**。出るのは時間に依らない数(側・分かれ道・崩れ・優勢から負け・群)だけ | 「持ち時間 10 分の局の時間の線は、まだ決めていません」の固定文が数え方に 1 行 | 10 |

**変わらない点(明記)**: 本編の文の慎重さ(規則 5 の (1)〜(4))・行動 1 の表現(人間の決定)・承認済みの行動の表の外から行動を作らないこと・実名を出さないこと。

---

## 2. 段ごとの接続表(指示書 §3 の表)

上位正本 §0 の 9 段(① Observation → ② Analysis → ③ Verification → ④ Integration → ⑤ Answer selection → ⑥ Slot filling → ⑦ Rendering → ⑧ Audit → ⑨ Human release)を、いま在る部品に当てる。「いま在る部品」の欄は今日ファイルを開いて確かめたもの(§7)。

| 段 | いま在る部品 | 足りないもの | 接続点(どのファイル・どの段・どの schema) | §1 の 10 項目 | 変えない線に触れないか |
|---|---|---|---|---|---|
| **① Observation**(事実を作る) | 束 A(`f46e2c0`): `schemas/observation-packet.v0.1.schema.json`・`observation-request.v0.1.schema.json`・`lib/observationPacket.ts`(検証の入口 `observationPacketProblems`・封 `packetIdOf`)。束 B(facts)は `lib/observationFacts.ts`・`lib/observationMaterials.ts` が未コミットで進行中。束 C(aggregates + provenance)・D(population の数え直し + 変異 5 本)は計画([PLAN_OBSERVATION_PACKET_2026-09-30.md](PLAN_OBSERVATION_PACKET_2026-09-30.md) §8) | (a) **request.json を書く入口**(顧客の問いの原文を人が写す場所。いまは無い)。(b) **持ち時間の組ごとの線の記録**(§3.4)。(c) packet を組む段を `deliver.ts` の段にするか、別コマンドにするか(**別コマンドを推す** ― 冊子を作りながら分析しない、の物理的な分離) | 出力: `out/<c>/packet/observation-packet.json`・`observation-request.json`。入力は既存の材料(`report/patient_report_data.json`・`p2/whatif-v2`・`p2/read`・`deliver1/direct/*`・`report/opening_recognition.json`)。**`deliver.ts` の 21 段には足さない**(段 `pipeline-data` 〜 `appendix4-search` の出力を読むだけ) | 4(request)・10(population・timeLimitSec) | 触れない。数はエンジンと集計から。実名は `customerRef` の符号だけ(束 A で試験済み) |
| **② Analysis**(意味を探す) | 計画のみ: [PLAN_LLM_SEATS_API_2026-09-30.md](PLAN_LLM_SEATS_API_2026-09-30.md)(`renderSeatInput`・`callSeat`・`seat-output.v0.1`・`hypothesis.v0.4`)、指示文 v1 [LLM_SEATS_INSTRUCTION_v1_2026-09-30.md](LLM_SEATS_INSTRUCTION_v1_2026-09-30.md)。実験 1・2 の実物は `out/c5/experiment-llm-25/`(人間の中継) | 実装の全部(計画 §3.5 の `scripts/playtest/llmSeats/`)。**この設計案で足すものは 1 つだけ**: seat_input の request の節に `requestedScope.timeLimitSec` と「線の組の id」(§3.4)を必ず写す ― 席が 3 切れの線を 10 切れに当てはめて読まないように | `seat_input.md` = packet + request(同一バイト・sha256)。出力 `out/<c>/llm-seats/<runId>/seat_<x>_raw.json` | 4・5・10 | 触れない。席に数えさせない(`selfComputedNumbers` に隔離)・戦型は `facts.recognition` の id だけ・`internal.*` は下流の schema に無い |
| **③ Verification**(事実と整合性) | `lib/hypothesis.ts` の H-1〜H-8(`validateHypothesisLine`。H-5 の禁止語は `check_answer.BANNED_WORDS` から読む ― いまは空)。`lib/observationPacket.ts` の検査の入口。`check_answer.py` の検査 1〜7(md の側) | (a) **H-9**(`observations[].packetRef` の値が packet に実在。計画 §2.1)。(b) **H-10**(語彙: 文に出た形・戦法の名前が `facts.recognition.definitions[].id` に在る)。(c) **分母・母集団**: `observations[].packetRef` が `aggregates` の行を指すなら、その行の `population` を packet の facts から数え直して一致(束 D の数え直しをそのまま呼ぶ)。(d) **事実か仮説か**: `factOrHypothesis: fact` の `statement` が「〜という読み」「可能性」を含めば落ちる(H-5 の裏返し)。(e) **戦型の認識の再確認**: 文が群(core / other / noSignature)や名前に触れるとき、`facts.recognition.rows[].reviewStatus` が `draft` なら顧客向けには「〜のような形」の型に落とす印を付ける(判定は作らない。印だけ) | 拡張先は `lib/hypothesis.ts`(H-9・H-10 を足す。版によらず同じ検査、の作りを保つ)。packet の照合は `lib/observationPacket.ts` を import。**`check_answer.py` は触らない**(md の側の門として ⑧ に残る) | 6 | 触れない。**一致を証拠にしない** ― 検証器は `seatCount` を読まない(計画 §4.2 の `evidence: false`) |
| **④ Integration**(整理役) | 計画のみ(`integration_input.v0.1`・`integration.v0.1`。`internal` を持たず `additionalProperties: false`) | 実装の全部。この設計案で足すものは無い | `scripts/playtest/llmSeats/integrate.ts`(計画 §3.5) | 5 | 触れない |
| **⑤ Answer selection**(検証済み ≠ 採用) | **無い。** いまは書き手(人)が候補 md から選んでいる(`exit_candidates.py` → 書き手の script `write_round7.py` → `exit_gate.py`)。承認済みの行動の表は `lib/answerMenu.ts`(M1〜M9)と `deliver1/direct/answer_menu.json` | **新しい契約 `answer-selection.v0.1`**(§3.1.3)と、それを書く場所。**採用は機械がしない** ― 道具は「検証を通った候補の一覧」を出し、司令塔(委任の範囲)か人間が採用の印を付ける。行動候補は `answer_menu.json` の id と照合し(計画 §2.2 の `menuMatch`)、表に無いものは `humanQueue` に隔離して人間へ | 入力: `integration.v0.1` + ③ の判定 + `request.json` + `answer_menu.json`。出力: `out/<c>/exit/answer_selection.json`。**`deliver.ts` の段 `exit-candidates` の直前に置く**(段の名は仮に `exit-select`。人の確認点なので `action: "gate"`、`prose-gate`・`answer-gate` と同型) | 4・6・8 | 触れない。**LLM の行動候補は人間に上げ、人間が表に足したものだけが冊子に出る**(上位正本 §2 の 3) |
| **⑥ Slot filling**(器へ配置) | `exit_candidates.py`(候補 md + `exit_candidates.json`: `opening`・`p1Numbers`・`boards`・`menuPassed`・`actionFractions`・`denominators`・`openingGroups`・`unitMismatchFractions`)、`exit_index.py`(固定文・節の定数)、`check_structure.opening_paragraph`・`scope_sentence`(冒頭の 4 文)。書き手の script は `out/c5/_final_draft_2026-09-29/write_round7.py`(153 行。**このセッションで読んだ ― 候補 md の節を正規表現で切り出し、P1 の 3 本と読みの文を直書きして組む**) | **本編 md を機械で組む道具**(仮に `exit_fill.py`)。書き手の script がやっている「切り出し + 直書き」のうち、**切り出しは器(固定)・直書きはスロット(可変)**に分ける(§3.1)。スロットの中身は `answer_selection.json` から。**書き手の道は消さない**(道具が組めない回は今までどおり人が書く ― 同じ `exit_gate.py` を通る) | `deliver.ts` の段 `exit-candidates`(候補 JSON)→ **新段 `exit-fill`**(md を組む)→ `exit-gate`(門は不変)。印の文法は `check_answer.py` の `POS_TAG_RE`・`MENU_TAG_RE` の家族に 2 つ足す(§3.1.4) | 1・3・7・8 | **文は固定文と承認済みの行動の文と、機械が出した数の組み合わせだけ**。読みの文(「〜という読みです」)は ⑤ で採用された `statement` を規則 5 の言い換え(LLM)に通したもので、**言い換えの後に必ず `check_answer` を通す**(既存の順 ― `exit_body.py` は描く前に `check_answer` を回す) |
| **⑦ Rendering** | `deliver.ts` の段 `exit-render`(`exit_cover.py` → `exit_body.py` → `exit_render.py`)、索引 `page_index.json`、盤は `board_spec.py`・`_util.py` の `Board` | (a) 送付用の名前を段にする(いまは `deliver1_送付用/README.md` のとおり**人が写して改名**している。`01_本編`・`02_付録` の形は `deliverOutPaths` の 1 か所で持つ)。(b) 分母の表を付録側に組む(§3.1.2 の余裕の直し。`exit_cover.py --out-pdf` と同じ流儀で `exit_body.render_plain`) | `lib/deliver.ts` `deliverOutPaths`・`exitRenderCommand`、`report-pdf/exit_render.py`(束ね) | 2・3 | 触れない。組版の変更は「実物から写す」の外なので、**ページ数は本番の道(`exit_body.py`)で測る**(正本 §15) |
| **⑧ Audit** | `exit_gate.py`(i)〜(ix)、`check_structure.py`(節の順・ページ・盤 2・付録のページ・見本用の差・実名 0・呼び方 1 通り)、`check_delivery.py`(`--forbid`)、`compare_render.py --seal/--verify`(3 つの数の封) | (a) **「答えの場所」の門**(§3.3): request の問いごとに `<!-- ans: qN -->` の印がちょうど 1 つ、決めた節に在り、状態の語が `answer_selection` と一致。(b) **用語の定義の門**(§3.2): 定義の文が冒頭にちょうど 1 回(既存の (vii) がそのまま見る)+「最善手」0 件(`check_delivery --forbid 最善手` を `deliver.ts` の固定引数に)。(c) **数の照合を id で**(P-178 の閉じ方): 本編の数を `<!-- agg: id -->` の印で packet の `aggregates` と突き合わせる(いまの検査 1「材料のどこかに同じ整数が在れば通る」の上に重ねる。検査 1 は残す) | `exit_gate.py` に (x)(xi) を足す。`check_structure.py` に**別の検査として**節「お預かりした問い」を足す ― **2026-10-01 の司令塔の訂正**: 当初「`SECTIONS` の表に足す」と書いたが、コードを開くと `SECTIONS` は**必須の役割**の表で(`check_sections` が「減るのは落とす」で全行を必須にし、間に節が増えるのは既に許している)、7 行目として足すと**問いが 0 件の顧客の本編が門を通れなくなる**(§3.3.2 と矛盾)。**問いの数で必須かどうかが変わるので、既存の 6 役割は動かさず別の検査にする**。`compare_render.py` はそのまま | 1・3・8 | 触れない。門は「選び終わったか」と「印字したものと同じか」を見るだけで、何を選ぶかは決めない(既存の作り) |
| **⑨ Human release** | 人間が送る。封 `compare_render.py --seal`。感想は原文のまま `docs/CUSTOMER*_FEEDBACK_*.md`、要点は [READER_UNDERSTANDING_LOG.md](READER_UNDERSTANDING_LOG.md) | **採用された解釈 ↔ 本編の文 ↔ 読者の言葉、を後で突き合わせる鍵**(§3.5): ⑥ が `slot_map.json` を書き、ログの各行が slot の id を持つ | `out/<c>/exit/slot_map.json`(gitignore)、`docs/READER_UNDERSTANDING_LOG.md` に列 `slot` を足す(記録 1 は遡って付ける) | 9 | 触れない。読者の強い解釈を断定に格上げしない(ログの規則) |

**順序(接続の順)**: 上位正本 §3 のとおり **① packet C → ③ を packet に載せる(H-9・H-10・id 照合)→ ② と ④ → ⑤ → ⑥ → ⑧ の門**。⑦ の名前の段と分母の表の移動、⑧ の用語の門は **①〜⑥ に依存しない**ので、次の顧客の前に単独の束で入れられる(§4 の H-3・H-4)。

---

## 3. 特に決めてほしいこと 5 点

### 3.1 スロット ― 器のどこが固定で、どこが可変か

**いまの実物(5 人目の最終版 `_final_sealed_2026-09-29/9_本編_最終版.md` と、それを組んだ `write_round7.py`)を読んで、行ごとに「固定」「可変」「機械が出した数」に分けた。**

#### 3.1.1 器(固定)― 道具が既に 1 か所で持っているもの

| 器の部品 | 正本の 1 か所 | 今のまま |
|---|---|---|
| 表題 `# {games} 局で起きていたこと` | `exit_candidates.build_md` | ○ |
| 冒頭の段落(4 文。組が 2 つなら 6 文) | `check_structure.opening_paragraph`(門 (vii) が 1 文ずつちょうど 1 回を見る) | **5 文にする**(§3.2) |
| 6 節の見出しと順 | `check_structure.SECTIONS` | **「お預かりした問い」を間に足す**(§3.3) |
| 「なぜこの N つだけか」の 1 文 | `exit_index.selection_sentence` | ○ |
| 「無いものは無いと書きます。」 | `exit_index.NOTHING_TO_HIDE_SENTENCE` | ○ |
| 行動の文の芯・答え合わせの表の 3 列 | `lib/answerMenu.ts`(承認済み)・`exit_candidates.VERIFY_TABLE_HEADER`・`facts_cell`・`values_cell` | ○ |
| 数え方の固定文 | `exit_index.COUNTING_NOTES` | ○ |
| 付録の節を指す印 `<!-- sec: -->`・表紙 | `exit_index.COVER_SECTIONS`・`exit_cover.py` | ○ |
| 対応表 | `exit_candidates.mapping_rows` | ○ |
| 商品の範囲の 1 文 | `check_structure.scope_sentence` | ○ |

#### 3.1.2 スロット(可変)― いま人が直書きしている場所と、次世代で何が入るか

| slot id | 場所 | いま(`write_round7.py` が直書き) | 次世代で入るもの | 器の門 |
|---|---|---|---|---|
| `p1.lead` | 「ひとことで」の太字 1 文 + 「数は 3 つ。」 | 書き手の文 | ⑤ で採用された**代表の `statement`**(統合の `representative`)を規則 5 の言い換えに通したもの。**「― という読みです。」の尾は固定** | 既存 (ii)(v) |
| `p1.1`〜`p1.3` | 「ひとことで」の箇条書き 3 本(事実 + 「― 読み:」) | 書き手の文(数は候補から) | 事実の部分 = `aggregates` の行(名前・分子・分母・単位を型に流す)。読みの部分 = ⑤ で採用された項目の `statement`(言い換え後)。**印 `<!-- agg: side_match.attack,side_match.defense -->` を行末に置く** | 既存 (ii)(viii) + 新 (xi)(id 照合) |
| `ans.q1`… | **新節「お預かりした問い」**(ひとことで の直後) | 5 人目では「数え方」の 4 ページ目に 3 群の表 + 読み(RETRO §1 の A-1「2 周ぶん遅れた」) | 問いごとに 1 段落: 問いの原文の写し(request の `text`)→ 答えの型(§3.3.3)→ 根拠の数(`aggregates`)→ 状態(answered / partial / unanswerable)。**印 `<!-- ans: q1 answered -->`** | 新 (x) |
| `p2.1`・`p2.2` | 盤 2 つ | 書き手が候補 103 から 2 つ | ⑤ が採用した項目の `observations[].packetRef` が指す局面(`facts.engine` の索引)から。候補に無い局面は選べない(既存 (iii)) | 既存 (iii) |
| `act.1`… | 試せること + 答え合わせの表の行 | `menuPassed` から書き手が本数を決める | ⑤ の `actionCandidate.menuMatch` が承認済みの id を持つものだけ。**本数は ⑤ で決める**(人) | 既存 (iv)(vi)・項目 6 |
| `act.lines` | 「行動 1 の線: …」「候補にしたものの行動にしなかったもの: …」 | 固定文(`threshold_sentences`)+ 書き手の文 | 固定文のまま + ⑤ の `unanswerable` / `dropped` を型に流す | 既存 (v) |
| `cnt.groups` | 数え方の中の群の表 + 読み | 書き手が 4 周目で落とし、最終版で戻した(器の余裕 0) | **`ans.q1` へ移す**(問いが「型」に関するときだけ出る。問いが無い顧客では出ない) | 新 (x) |
| `cnt.denoms` | 「数の分母がどこから来たか」の表(17 行 → 12 行に削った) | 書き手が行を削って余裕を作った | **付録の表紙の次のページ**へ(§3.1.3)。本編には残さない | `check_structure` の付録のページ上限 25 の内 |

**器の余裕 0 の直し方(RETRO §3 の「分母の表を付録に移す等」)**:

| 案 | 中身 | 効き目(見込み) | 副作用 |
|---|---|---|---|
| **A(推す)** | `cnt.denoms` を付録へ。本編の「数え方」は `COUNTING_NOTES` + 群の注だけ | 最終版の本編 4 ページ目は分母の表 12 行 + 群の表 5 行で埋まっていた(封 5 ページ)。表 12 行が消えれば **1 ページ弱の余裕**(**未実測** ― 正本 §15 の規則で `exit_body.py` の本番の道で測ってから採る) | 付録が 1 ページ増える(上限 25 の内。5 人目の付録は 5 ページ) |
| B | 分母の表を残し、行を「本編に出た数だけ」に機械で絞る(いま書き手が手でやっている `_num_of` の削り) | 行数が 12 前後で止まる。余裕は増えない | 「表にだけある数」の指摘(席 (a) R4)は閉じるが、余裕 0 は続く |
| C | 字を小さくする・2 列組 | ― | 「実物から写す」の外(正本 §12 が採らなかった道) |

A の理由をもう 1 つ: packet が入れば **本編の全部の数に `aggregates` の id が付く**ので、分母の表は「本編が使った id の行を packet から機械で並べる」だけになる。**人が行を選ぶ余地が無くなる**ので、本編に置く理由(書き手が数え方を説明する)も消える。

#### 3.1.3 新しい契約 `answer-selection.v0.1`(⑤ の出力。⑥ の唯一の入力)

```
{ contract: "answer-selection", schemaVersion: "0.1", customerRef, packetId, runId,
  lead:      { itemRef: {seatIndex, itemId}, statementSource: "integration.representative" },
  p1:        [ { slot: "p1.1", aggregateIds: ["side_match.attack","side_match.defense"], itemRef, readingRequired: true }, … 3 本 ],
  answers:   [ { questionId: "q1", status: "answered|partial|unanswerable", itemRefs: [...], aggregateIds: [...],
                 neededObservation?: {what, howToMeasure} } ],           // request の問いごとに必ず 1 行
  boards:    [ { slot: "p2.1", gameId, ply, packetRef: "facts.engine[…]" }, … 2 つ ],
  actions:   [ { slot: "act.1", menuId: "M4", itemRef } … ],            // menuId は answer_menu.json に実在
  humanQueue:[ { itemRef, actionCandidateText, why: "menuMatch: null" } ], // 表に無い行動候補。冊子に出ない
  adoptedBy: { who: "commander|human", at, basis: "…" } }               // 承認の根拠(委任の条件 2)
```

- **`internal` の欄を持たない・`additionalProperties: false`**(人間の決定「参照できない」を ⑥ の入口にも掛ける)。
- **数はここに書かない**(id だけ)。数は ⑥ が packet から引く ― 「途中の編集で数字が変わった」の道を作らない。
- `readingRequired: true` の行は `statement` が無ければ ⑥ が落ちる(読みの無い数だけの行を本編に出さない ― 4 人目の型)。

#### 3.1.4 印の文法(2 つ足す。`check_answer.py` の印の家族と同じ場所に置く)

| 印 | 形 | 誰が書く | 誰が読む |
|---|---|---|---|
| `<!-- agg: id[,id…] -->` | 行末。id は packet の `aggregates[].id` | ⑥ | ⑧ (xi): 行の数(分数は左右とも)が、その id の行の分子・分母に**全部**在る。id が packet に無ければ落ちる |
| `<!-- ans: qN status -->` | 段落の末尾。`status` は answered / partial / unanswerable | ⑥ | ⑧ (x): request の問いごとにちょうど 1 つ・節「お預かりした問い」の中・status が `answer_selection` と一致 |

`exit_body.py` は `pos` の印を自分で取り除く(P-123)。**同じ関数に 2 つの印を足す**(黙って捨てられる道に頼らない)。

### 3.2 用語の 1 行定義の置き場所(§1 の 1)

**推す: 器の固定文。冒頭の段落の 5 文目**(`check_structure.opening_paragraph` に 1 文足す)。

| 案 | 置き場所 | 初出より前か | 門 | 余裕 |
|---|---|---|---|---|
| **(a) 推す** | 冒頭の段落の 5 文目(「数の出どころは付録で引けます。」の後) | **前**(冒頭は「ひとことで」の太字より上) | 既存 (vii) がそのまま「ちょうど 1 回」を見る。**文は候補の JSON の `opening` から来る**ので、書き手にも道具にも消せない | 1 文 = 1〜2 行(**未実測**) |
| (b) | スロット `p1.lead` の前文 | 前 | 新しい門が要る | 同じ |
| (c) | 「数え方」の節 | **後**(初出は p1) | ― | ― |

文(人間の言葉をそのまま): 「**第 1 候補: この局面でエンジンが 1 番に挙げた手。正解と決めるものではなく、実戦の手と比べるために使っています。**」

**「最善手」を出さない門**: `check_answer.BANNED_WORDS` はいま空の一覧(語を消した経緯があるので足さない)。**`check_delivery.py` の語の表(`ALWAYS_FORBIDDEN_WORDS = ["最善手"]`)に置く**(2026-09-30 の司令塔の訂正。当初は「`checkDeliveryCommand` の固定引数」と書いたが、`--forbid` の値は顧客の実名で**記録に値を書かない決まり**があるため、固定語をそこに乗せると記録から見えない語になる。道具の表なら原本と出力の両方から読める。`ALWAYS_FORBIDDEN` は「語以外」の表なので混ぜない)(PDF 全冊 + md を見る。`fitz` なので P-112 の穴は無い)。**付録の表紙の `COVER_TAIL`「エンジンの候補は「正解」ではなく、比べるための材料です。」はこの定義と同じ向き**なのでそのまま。

**残りの 3 語(分かれ道・自玉側・一致率)**: 人間が固定したのは「第 1 候補」だけ(指示書 §1 の 1)。席 (a) R6 と本人の両方が 4 語を挙げたので、**同じ仕組み(冒頭の固定文)で 3 文足すか**は司令塔の判断(§4 の H-4)。足すと冒頭が 8 文になり、**正本 §15 の実測では冒頭 1 文 → 4 文で表の余裕が 4 行 → 1 行に減った**。3.1.2 の案 A(分母の表を付録へ)と組にしないと入らない見込み。

### 3.3 顧客の問いの通り道(§1 の 4・8)

```
人が原文を写す ─→ request.json(customerQuestions[].text = 原文。via: relayed)
                      │ (packet は request を参照しない ― 一方通行)
                      ▼
② seat_input.md の節 2(request)── 席の answers[] は問いごとに必ず 1 行(answered/partial/unanswerable + reason)
                      ▼
④ integration.answersByQuestion[](「答えられない」を多数決で消さない)
                      ▼
③ 検証: answer_candidate の requestRef が request に実在 / observations の H-1・H-9 / 語彙 H-10 /
        unanswerable の reason が neededObservation(what・howToMeasure)を持つ(数を含まない)
                      ▼
⑤ answer_selection.answers[](問いごとにちょうど 1 行。採用は人)
                      ▼
⑥ 節「お預かりした問い」に 1 段落ずつ + <!-- ans: qN status -->
                      ▼
⑧ exit_gate (x): 問いごとにちょうど 1 つ・節の中・status 一致
   check_structure: 節の役割を登録・索引に ans の印のページを書く(「答えは本編の何ページか」を数で残す ― RETRO §3 の 1 行目)
                      ▼
⑨ 読者理解ログ reached.question ↔ slot ans.q1
```

#### 3.3.1 節の置き場所

| 案 | 場所 | 正本との関係 |
|---|---|---|
| **(a) 推す** | 「ひとことで」の**直後**、「局面で見る」の前(3 人目 v3 が「その 6 局で、何が起きたか」を置いた位置) | 正本 §6 (2)「間に節が増えるのは許す」の範囲。**ただし「問いがあるときは必須」にするのは新しい規則**(§4 の H-1) |
| (b) | 「ひとことで」の 4 本目の箇条書き | (ii) の「ちょうど 3 本」に当たる。**採らない** |
| (c) | 「数え方」の中(5 人目の実物) | 4 ページ目。人間の言葉「顧客の問いに直接答える商品」に合わない。**採らない** |

#### 3.3.2 問いが無い顧客

request の `customerQuestions` が 0 件なら**節ごと出ない**(門 (x) は「問いの数 = 印の数」を見るので 0 = 0 で通る)。「問いは無かった」と冊子に書かない。

#### 3.3.3 答えの型(顧客に出る文は固定文 + 数 + 承認済みの言い方だけ)

| status | 型 |
|---|---|
| answered / partial | 「お預かりした問い: 「{原文}」」→ 根拠の数の行(`aggregates` から。群の表はここ)→「― 読み: {採用された statement(言い換え後)}」→ partial のときは「{neededObservation.what} は、今回の数には無いので、次の {games} 局で測ります。」 |
| unanswerable | 「お預かりした問い: 「{原文}」」→「**今回の数からは、明確な差は確認できませんでした。**」(固定文)→「次の {games} 局で測るもの: {neededObservation.what}」 |

**「明確な差は確認できない」も正式な結果**(指示書 §1「答えを作らせない」)。固定文の文言は顧客に出る文なので**人間の承認**(§4 の H-7)。**読みの部分に「試験的な将棋だから外れる」のような因果を書かない**(ログの `do_not`)。

### 3.4 母集団の分離 ― 3 切れと 10 切れを別データセットにする(§1 の 10)

#### 3.4.1 いまの持ち方(実物)

| 持ち時間の情報 | どこに在るか |
|---|---|
| 組の持ち時間 | `deliver.ts` の `--time-limit-sec`(組ごと)。`check_answer.tag_of_time_limit_sec`(180 → `min3`・600 → `min10`・他は無印)。組の名は `groupLabelOfTimeLimitSec` |
| packet | `facts.games[].timeLimitSec`(必須)・`request.requestedScope.timeLimitSec`(**任意**) |
| 時間の線 | `lib/reportData.ts` の `TIME_VALUES` の 1 か所(`spentBucketsSec: [1, 4, 9]`・`longThinkSec: 10`・`quickSec: 4`)。**持ち時間に依らず 1 組** |
| 行動の判定の線 | `check_answer.MENU_THRESHOLDS`(M4 `rate_below 0.7`・M5 `times_of_other_rate 2`)。M1/M2/M8 だけが `min3` の組を要る |

**つまり、10 切れの棋譜を今の道具に通すと、3 切れの線(10 秒・4 秒・0〜1 秒)でそのまま数えて冊子に出る。**止まる仕組みが無い。

#### 3.4.2 設計(4 点)

1. **1 packet = 1 データセット(1 顧客 × 1 持ち時間)。** `request.requestedScope.timeLimitSec` を**必須**にし(§5 の提案 R-1)、`facts.games[].timeLimitSec` が**全部それと一致**することを packet の検査の入口(`observationPacketProblems`)に足す。3 切れと 10 切れを 1 つの packet に混ぜない ― `aggregates` の id が同じでも母集団が違う数を、同じ id で並べる道ができるため。継続比較(3 切れ 25 局と 10 切れ 25 局を並べる)は上位正本 §3 の「上位版」であって、基本版では**やらない**。
2. **線の組(threshold set)を packet の provenance に記録する。** `provenance.thresholds: { id: "t180-v1", timeLimitSec: 180, spentBucketsSec: [1,4,9], longThinkSec: 10, quickSec: 4, rateBelowLine: 0.7, timesOfOtherRate: 2 }` の形(§5 の提案 P-1)。**値の正本は今までどおり `TIME_VALUES`・`MENU_THRESHOLDS`**で、packet はその写し + 持ち時間の鍵。席は seat_input の §0 でこれを読む(「この線は 3 分切れ負け用の仮置き」)。
3. **線を持ち時間ごとの表にし、無い持ち時間では時間の集計を出さない。** `TIME_VALUES` → `TIME_VALUES_BY_LIMIT = { 180: {...}, 600: null }` の形(鍵は `tag_of_time_limit_sec` と同じ 180/600)。**600 は「未定」で登録し、`null` なら時間の `aggregates`(`time.*`・`long_think.*`)と時間系の行動(M1・M5・M9)を作らずに「線が未定」と記録する。** 黙って 180 の線を使わない(止まるのは良く、流用は悪い)。**10 切れの線を決めるのは判断的知識**(§4 の H-2)― 10 切れの 25 局を測ってから人間が決める。
4. **比べられるもの / 比べられないものを機械で分ける。** `aggregates[].population.where` に `spentSec`・`timeUpLoss`・`longThink*` の欄が出る行と、`thresholds` を参照する行を**時間依存**と判定し(手で旗を立てない ― 欄名から導く)、`aggregates[].timeDependent: true/false` を束 C が書く(§5 の提案 P-2)。答え合わせの表の行には `requiresSameTimeLimit` を持たせ、**次の 25 局が別の持ち時間なら、その行は「同じ持ち時間の局でだけ答え合わせできます」の固定文に置き換わる**(M5 の行がこれに当たる)。

**束 B の実測との関係(計画 §5f、2026-09-30 に自動化レーンが追記)**: `facts.moves[].spentSec` が付いた手は **161 / 1242**(材料 `time_cause.midMoveSeconds` が中盤の手だけを持つ)。したがって `time.by_spent_0_1_collapsed`(22 / 531)の `population.where` を `spentSec` で書いても、**v0.1 の facts からは数え直せない**(531 は全時期の手)。上の 4 点目(`where` の欄名から時間依存を導く)は成り立つが、**束 D の数え直しは時間の行だけ「材料の側に秒が無い」で止まる**見込み ― 束 C/D の側で `facts.moves` に全時期の秒を持たせるか、時間の行は `derivedFrom` の照合までにするかを、自動化レーンに確かめてもらう(§5 の P-4)。

**5 人目に当てるとどうなるか(見込み)**: 時間に依らない = `side_match.*`・`branches.*`・`repro.*`・`collapse` の数・`ahead_then_lost`・`groups.*`。時間依存 = `time.*`・`long_think.*`・M1/M5/M9。**P1 の 2 本目(長考直後)と行動 2 は、10 切れでは線が未定なので出ない**。P1 は 3 本必要なので、⑤ が時間に依らない 3 本を採る(候補は足りる ― 5 人目の候補 JSON `p1Numbers` は 61 行)。

### 3.5 読者理解ログとの接続(§1 の 9)

**足りないのは鍵 1 つ**: 「採用された解釈」と「本編の文」と「読者の言葉」を同じ id で結ぶもの。

| 層 | 持つもの | 置き場所 |
|---|---|---|
| ⑤ 採用 | `answer_selection.json` の slot id(`p1.1`…`ans.q1`・`act.1`)と `itemRef`(席・項目 id) | `out/<c>/exit/`(gitignore) |
| ⑥ 配置 | **`slot_map.json`**: slot ごとに `{ slot, marks, itemRef, aggregateIds, text(本編の文そのもの), textSha256 }` | 同上 |
| ⑦ 組版 | `page_index.json` に slot の印のページ(`pos` と同じ仕組みで `agg`・`ans` の印を索引に書く)→ `slot_map.json` に `page` を足す | 同上 |
| ⑨ 読者 | [READER_UNDERSTANDING_LOG.md](READER_UNDERSTANDING_LOG.md) の各行に列 **`slot`** を足す(`reached.new` = `p1.2`、`reinterpreted` の 1 行目 = `act.1`、2 行目 = `ans.q1`、のように)。記録 1(c5)は遡って付ける(5 人目の本編は slot の印を持たないので、**人が読んで対応させた**と注記する) | `docs/` |

**顧客の数は docs に写さない**: ログに書くのは slot の id・封の符号(packetId・runId)・読者の言葉だけ。文そのものと数は `slot_map.json`(out/)にある。

**次回から比べられるもの**: (i) 同じ slot(`p1.2`)が `reached.new` になる率、(ii) `reinterpreted` が付く slot の偏り(5 人目は `act.1` と `ans.q1` = 因果に進んだ 2 か所)、(iii) `not_reached.term` の語(用語の門の効き目)。**評価データの契約(`reader-understanding.v0.1`)は、記録が 3 件を超えてから**(1 件で器を作らない)。

---

## 4. 判断が要る点の一覧(誰が決めるか)

| # | 決めること | この設計案の案 | 誰が | 理由(なぜ委任の外/内か) |
|---|---|---|---|---|
| H-1 | 節「お預かりした問い」を器に足し、**問いがあるときは必須**にする(位置は「ひとことで」の直後) | 足す | **人間** | 正本の 5 節に 1 節足す(正本は「書き換えない」なので訂正の追記の形)。顧客の PDF の形が変わる |
| H-2 | 時間の線を持ち時間ごとの表にし、**10 切れ(600 秒)は未定 = 時間の集計を出さない** | そうする | **人間** | 判断的知識(閾値の持ち方)。10 切れの線の値は 25 局を測ってから別途 |
| H-3 | 「数の分母がどこから来たか」の表を本編から付録へ(案 A) | 案 A | 司令塔(委任の範囲。ただし**ページ数を本番の道で測ってから**) | 器の余裕の直し。文の内容は変えない |
| H-4 | 用語の定義 = 冒頭の 5 文目 + `--forbid 最善手`。**残り 3 語(分かれ道・自玉側・一致率)も同じ仕組みで足すか** | 第 1 候補は入れる。3 語は H-3 と組にして測ってから | 司令塔(第 1 候補の文は人間の言葉そのまま) | 文は人間が固定済み。置き場所と門は道具の話 |
| H-5 | 1 packet = 1 データセット(`requestedScope.timeLimitSec` 必須・全局一致の検査) | そうする | 司令塔 → 自動化レーン(束 C/D の schema に触れる。§5) | 進行中の束の契約 |
| H-6 | 印 `<!-- agg: -->`・`<!-- ans: -->` の文法と、検査 1 の id 照合(検査 (xi)) | 足す | 司令塔(委任の範囲。動きを変えるので独立監査) | P-178(材料のどこかに同じ整数が在れば通る)の閉じ方 |
| H-7 | unanswerable の固定文「今回の数からは、明確な差は確認できませんでした。」 | この文 | **人間** | 顧客に出る文 |
| H-8 | 読者理解ログに列 `slot` を足し、記録 1 に遡って付ける | 足す | 司令塔 | docs だけの変更 |
| H-9 | ⑤ の「採用」の席(司令塔か人間か)。行動候補で表に無いものは人間へ、はそのまま | 答え・読みの採用は司令塔(委任の設計判断)、**行動の表への追加と送るかは人間** | **人間** | 上位正本 §2 の 3 の線引きを段に落とすときの「誰」 |
| H-10 | 送付用の名前を段にする(いま人が改名) | **決定(2026-09-30)**: `01_本編_対局後診断_{組の名}{局数}局.pdf` / `02_付録_数の出どころ_{組の名}{局数}局.pdf`。局数を含むので静的な表に置けず **`deliverSendNames(games, groupLabel)` の関数 1 か所**。`原本/` と `送付/` の 2 段は残す。試験は並べ替えの先頭が `01_本編…` であることを見る | 司令塔(決定済み) | 人間が固定したのは「本編が先」まで。名前の形は器の持ち物 |

---

## 5. 進行中の束への提案(schema を変えない。司令塔へ回す)

| # | 束 | 提案 | なぜ今言うか |
|---|---|---|---|
| P-1 | packet(束 C) | `provenance.thresholds`(線の組: id・timeLimitSec・`TIME_VALUES` の写し・`MENU_THRESHOLDS` の写し)を足す | 席と検証器が「この数はどの線で数えたか」を packet から読める。値の正本は動かさない(写しであることを試験で固定 ― `answerMenu.test.ts` が docs との一致を見るのと同じ型) |
| P-2 | packet(束 C) | `aggregates[].timeDependent: boolean` を**欄名から機械で導いて**書く(`population.where` に `spentSec`・`timeUpLoss`・`longThink*` が出る行) | 3 切れ / 10 切れで比べられる行を手で選ばない |
| P-3 | packet(束 A の検査の入口) | `facts.games[].timeLimitSec` が全部同じ値、かつ request の `requestedScope.timeLimitSec` と一致、を `observationPacketProblems` に足す | 1 packet = 1 データセットの床 |
| P-4 | packet(束 C/D) | 時間の集計行(`time.*`・`long_think.*`)の `population` を facts から数え直すには全時期の `spentSec` が要るが、束 B の実測は 161 / 1242(中盤だけ)。**全時期の秒を `facts.moves` に持たせる**か、時間の行は数え直しの対象外と schema に明記するか | §3.4 の分離が「数え直し」で担保できるかが、この 1 点で決まる |
| R-1 | request(束 A) | `requestedScope.timeLimitSec` を**必須**にする(今は任意) | データセットの宣言が無い request を通さない |
| S-1 | seat-output(実験席) | `answers[].reason` の隣に機械が読める `missing: [ {what, howToMeasure} ]` を持たせる(`neededObservation` と同じ形) | ③ が「答えられない理由が packet に無いものを指しているか」を文ではなく欄で見る(計画 §6.0 の 4 行目の照合を自動に) |
| S-2 | seat-output(実験席) | seat_input の request の節に `thresholds.id` と `timeLimitSec` を必ず写す(render 側の規則) | 席が別の持ち時間の線で読まない |
| A-1 | 新契約 | `answer-selection.v0.1`(§3.1.3)を `scripts/playtest/schemas/` に足す。`internal` を持たない・`additionalProperties: false` | ⑤ と ⑥ の境界。実装は ⑤ の束で |

---

## 6. 変えない線との照合

| 線(上位正本 §4・指示書 §4) | この設計でどう守るか |
|---|---|
| LLM に数えさせない | 数は packet の `aggregates` だけ。⑤ は id、⑥ が packet から引く。席の数は `selfComputedNumbers` に隔離(計画のまま) |
| 顧客に出る文は規則 5 の (1)〜(4) | ⑥ の文 = 固定文 + 承認済みの行動の文 + packet の数 + 言い換え後の `statement`。**言い換えの後に `check_answer` を通す**(既存の順)。断定しない尾(「― という読みです。」)は固定 |
| 規則 8 (2) 一致を証拠にしない | ③ は `seatCount` を読まない。⑤ の `adoptedBy.basis` に「N 席一致」を書かない(基準は「検証を通った + 問いに合う」) |
| 規則 8 (4) 名前は `data/` の認識だけ | H-10(語彙)。`reviewStatus: draft` の群は「普段の型 / 普段と違う型 / 型が取れない」の呼び方のまま(5 人目の実物の語)。戦型の名前は出さない |
| 規則 8 (3) 内部の自由分析は下流から参照できない | `answer-selection.v0.1` と `slot_map.json` に `internal` の欄を持たせない(`additionalProperties: false`) |
| 実名を冊子に出さない・本人に聞かない・送るかは人間 | packet の `customerRef`、`check_structure.check_no_real_name`、⑨ は人間。request の問いは**既に聞かれたもの**の写しだけ(追加で聞かない) |
| 冊子(最終版)は直さない | この文書は次の顧客から効かせる。5 人目の封 `d2ae002` には触れない |
| 進行中の束の schema を変えない | §5 は提案として司令塔へ。このセッションでは 1 文字も変えていない(`git status` で確認 ― 変更は本文書 1 本) |
| 「冊子を作りながら分析しない」 | ①〜⑤ は `deliver.ts` の外(別コマンド)、⑥ から段。⑥ の入力は `answer_selection.json` だけで、⑥ 以降の直しは ⑤ に戻れない(印と id で片方向) |

---

## 7. 引いた数と、測っていない数

**今日ファイルを開いて確かめたもの(実測)**:

| 数・事実 | 出どころ |
|---|---|
| `deliver.ts` の段は 21(`pipeline-gate` … `check-delivery`。出口の段は `exit-candidates`・`exit-gate`・`exit-render`・`exit-check`) | `lib/deliver.ts` `DELIVER_STAGES` |
| `exit_gate.py` の検査は (i)〜(ix)(TODO・冒頭・P1 3 本・P1 → 行動・単位・盤 2・行動・文・下書きの残り) | `report-pdf/exit_gate.py` |
| 5 人目の候補 JSON(7 周目): `p1Numbers` 61・`denominators` 17・`boards` 103・`menuPassed` 3・`menuDropped` 6・`opening` 4・`openingGroups` 3 | `out/c5/_final_draft_2026-09-29/exit_candidates_7周目.json` |
| 書き手の script は分母の表 19 行 → 12 行、数え方 6 → 1 行に削って組んでいる | `write_round7.py` の `assert` |
| 最終版の封: 本編 5 ページ・見本 4・付録 5・表紙 1 | `_final_sealed_2026-09-29/README.md` |
| 送付用の名前は人が改名(`対局後診断_25局_本編.pdf`)。中身は `cmp` で原本と同一 | `deliver1_送付用/README.md` |
| `TIME_VALUES` = `[1,4,9]`・10・4。`MENU_THRESHOLDS` = M4 0.7・M5 2 倍。`tag_of_time_limit_sec` = 180/600 | `lib/reportData.ts`・`report-pdf/check_answer.py` |
| packet の schema: `facts.games[].timeLimitSec` 必須、`aggregates[].population.{from,where,unit}`、`provenance.sources[]`。request の `requestedScope.timeLimitSec` は任意 | `schemas/observation-packet.v0.1.schema.json`・`observation-request.v0.1.schema.json` |
| `BANNED_WORDS` は空。`check_delivery.ALWAYS_FORBIDDEN` = `@`・`/Users/`・`水匠`・`None` | `check_answer.py:94`・`check_delivery.py:30` |
| 5 人目の本編で問いの答え(3 群の表)が在る場所は「数え方」(4 ページ目) | `9_本編_最終版.md` |

**測っていないもの(採る前に測る)**: 分母の表を付録へ移したときの本編のページ数(§3.1.2 案 A)/ 冒頭を 5 文・8 文にしたときの余裕(§3.2)/ 節「お預かりした問い」を足したときのページ数 / どれも **`exit_body.py` の本番の道で**(正本 §15)。
