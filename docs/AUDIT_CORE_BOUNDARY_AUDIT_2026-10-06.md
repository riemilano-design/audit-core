# Audit Core 確定監査 ― 何が本当に Audit Core か(2026-10-06、セッション「将棋コーチ|Audit Core確定監査」)

**この文書は調査だけを書く。コード・データ・試験・schema は 1 文字も変えていない。commit もしていない(このファイル自体も未追跡)。**
前提は T-1〜T-5(`3676400` → `13e3083`)の実装結果と、計画書 `docs/AUDIT_CORE_EXTRACTION_PLAN.md`(未追跡)。
判断ごとに根拠(ファイル:行)を添える。確認できなかったものは「未確認」と書く。

| 項目 | 値 |
|---|---|
| Base Commit | `13e3083c4c966f81455aa74ed9e8e9ce84a3f5b7`(T-5。調査開始時・終了時とも同じ) |
| ブランチ | `feature/phase7-recognition-spec` |
| 作業ツリー | `?? docs/AUDIT_CORE_EXTRACTION_PLAN.md` のみ(他の変更なし) |
| 実行したもの | `git log/status/rev-parse`、`cat/sed/grep`、JSON schema の `json.load`(読み取りだけ)。試験・typecheck・門は**回していない** |
| 原則 | **依存境界(import)と意味境界(仕様)を別の列で判定する。例外 0 を Core 完成と呼ばない。代表ケース 1 件(c5)の一致で同値と言わない。**(人間の原則 2026-10-06) |

---

## 0. 先に結論

**audit-platform 作成: NO-GO(今は切り出さない)。** 理由は §8。

一文で言うと: T-5 で **依存境界は閉じた(KNOWN_EXCEPTIONS 0)が、意味境界は 4 本の分離(I-4・I-5・I-6・I-7)が未着手で、Core 候補 26 本のうち「将棋を外しても成立する」のは TS 7 本 + Python 2 本だけ**である。計画書 §8 の表では T-4 = I-4/I-5/I-6、T-5 = I-7/I-8 と書かれていたが、**実際のコミットは T-4 = I-3 のみ、T-5 = I-8 + 型 2 本のみ**(`git log --stat`、`core_boundary.test.ts` 60〜61 行のコメントも同じことを明記)。

---

## 1. Core 候補ファイル一覧(T-5 時点の再確認)

出どころ: `scripts/playtest/lib/core_boundary.test.ts` の 4 つの一覧(26〜48 行)。**依存**列は同試験の静的走査の結果(例外 0 = 将棋側 `shogiops`・`apps/server`・`report-pdf` の組版 module への import が 0)。**意味**列は本調査(§2)。

### 1.1 TS ― 将棋依存なしと分類済み(`CORE_TS_PURE`、8 本)

| ファイル | 行数 | 依存 | 意味 | 根拠(意味の判定) |
|---|---|---|---|---|
| `lib/eventSchema.ts` | ― | 0 | **汎用** | JSON Schema 部分集合(キーワード 13 個 `type enum const pattern minimum maximum properties required additionalProperties minItems minLength items oneOf`、19〜33 行)。将棋語 0 |
| `lib/prng.ts` | 32 | 0 | **汎用** | xorshift32 |
| `lib/env.ts` | ― | 0 | **汎用** | `.env`・秘匿。鍵名は LLM 3 社 |
| `lib/tokenBudget.ts` | 70 | 0 | **汎用** | 見積り・単価・上限 |
| `lib/schemaAdapters.ts` | 191 | 0 | **汎用** | schema の 3 社向け変換 |
| `lib/llmClient.ts` | 259 | 0 | **汎用** | 構造化出力の呼び出し |
| `lib/packetRef.ts` | 45 | 0 | **将棋が焼き込み** | `PACKET_FACTS_COLUMNS` 7 列(15 行)、`FACTS_REF_RE` が `recognition\.(?:rows\|definitions)` を名指し(24 行)。`AGGREGATE_REF_RE`(19 行)と関数 4 本は汎用。**I-6 未着手** |
| `lib/gitState.ts` | 235 | 0 | **汎用だが repo 配置に依存** | `COUNTED_PREFIXES = ["apps/","data/","scripts/"]`(24 行)はこの repo のフォルダ名。`renderDirtyWarnings` の引数名 `kifuId`(207〜231 行)は欄名だけ |

### 1.2 TS ― 機構は汎用・将棋依存あり(`CORE_TS_A_PRIME`、13 本)

| ファイル | 行数 | 依存 | 意味(要約。詳細は §2) |
|---|---|---|---|
| `lib/observationPacket.ts` | 244 | 0 | 封・検証入口・path 解決は汎用。**`observationPacketProblems` が将棋の 3 検査(`aggregateAgreementProblems`・`timeLimitProblems`、126〜138 行)を内包。I-5 未着手** |
| `lib/observationAggregates.ts` | 844 | 0(T-5 で型を局所化) | 数え上げ・数え直しの機構は汎用。**`ROW_DEFINITIONS` 26 行・`SIGNATURE_GROUPS`・整合関係 (1)〜(4)・`BOOKLET_EXPECTATIONS`・`aggregateCoverageProblems` は将棋。I-4 未着手** |
| `lib/observationProvenance.ts` | 297 | 0(T-4 で注入化) | 枠・sha・`traceProblems` は汎用。**`sourcesOf` の `kind` 文字列 5 本(68・73・77・89・102 行)は将棋の材料名** |
| `lib/hypothesis.ts` | 1008 | 0(T-3 で注入化) | H-1〜H-11 の骨格は汎用。**型 `knowledge.kind: "shogi"`(78 行)・`origin.kifu`(81 行)、H-10/H-11 が `facts.recognition.{definitions,rows}` の場所を直書き(843〜870・942〜953 行)、既定の登録簿補いが将棋の 30 列(`schemas/obs-registry.extra-ids.json`)、`data/governance` と `docs/` への相対 URL(111・114 行)** |
| `lib/seatOutput.ts` | 335 | 0 | 封筒・到達(封印語)の検査は汎用。`SEAT_EXCLUDED_INPUTS` が冊子のファイル名(19 行)、`origin.kifu` を書く(166 行)、既定の登録簿 path `../../../docs/OBSERVATION_ITEMS.md`(281 行) |
| `lib/integration.ts` | 485 | 0 | 統合の入出力・席のシャッフル・I-1〜I-4 は汎用。`INTEGRATOR_EXCLUDED_INPUTS`(31 行)、`SEAT_COUNT_REFERENCE_RE` が日本語「席」(35 行)、`origin.kifu`(310 行)、登録簿 path(402 行) |
| `lib/seatRun.ts` | 595 | 0 | 実行・再試行・費用上限・空席 9 種は汎用。**`FIXED_INSTRUCTION_SHA256` の 4 本は将棋の指示文(40〜46 行)で Core の定数** |
| `lib/exitSelect.ts` | 224 | 0 | 候補の並べ替え・`adoptedBy` 常に null・門は汎用。`isBoardRef` が `facts.engine[`(62〜64 行) |
| `lib/answerSelection.ts` | 228 | 0 | 状態機械・S-3〜S-8 は汎用。**`P1_COUNT = 3`・`BOARD_COUNT = 2`(25〜26 行)、S-6 の `menuIds` は承認済み行動表 M1〜M9** |
| `hypothesisCheck.ts` / `seatOutputCheck.ts` / `integrationCheck.ts` | 87/41/39 | 0 | 薄い CLI。既定の `--obs-items` が `docs/OBSERVATION_ITEMS.md`(hypothesisCheck 51 行) |
| `runSeats.ts` | 249 | 0 | 3 席 + 整理役の CLI。`instructionExamples`(指示文の例を実物に当てる)を import |

### 1.3 Python

| ファイル | 行数 | 依存(SHOGI_PY_MODULES への import) | 意味 |
|---|---|---|---|
| `compare_render.py` | 204 | 0(`fitz` のみ) | **汎用**(PDF の意味比較・封) |
| `check_fonts_embedded.py` | 51 | 0 | **汎用**。**試験が無い**(`*_test.py` に無し。`core_boundary.test.ts` は存在だけ見る) |
| `rename_list.py` | 287 | 0 | 機構は汎用。拾う規則 `S_H1)`・`_TITLE =` が将棋の組版コードの命名 |
| `exit_verification.py` | 599 | 0(標準ライブラリだけ。T-5 で新設) | 判定の機構は汎用。**`verify` の固定順と `GateRules` の必須欄(`p2_role`・`board_count` …)は冊子の形**(§2.3) |
| `check_answer.py` | 1856 | 0 | **2 層**。走査層(1566〜1856 行)は汎用寄り、材料層(268〜1554 行)と指し手・付録・メニュー・名前の検査は将棋。**I-7 未着手** |
| `check_structure.py` | 934 | 0 | 機構(役割で節を見る・ページ数・索引の整合・実名 0)は汎用。**定数が全部冊子**(`SECTIONS` 54〜62 行、`TERM_LINES` 115 行、`MAX_*_PAGES` 174〜177 行、`BOARD_COUNT` 179・`HONBUN_P1_FACT_COUNT` 192 行、`QUESTION_HEADING` 742 行)。`check_answer`・`exit_index` を import |
| `check_delivery.py` | 155 | 0 | 機構は汎用。`from check_answer import BANNED_WORDS`(24 行)、`ALWAYS_FORBIDDEN` に `水匠`(31 行)、`ALWAYS_FORBIDDEN_WORDS = ["最善手"]`(55 行) |
| `exit_index.py` | 380 | 0(import は json/os/re) | 索引の機構(置いた経路が書く)は汎用。**顧客向けの文 `COUNTING_NOTES`・`COVER_*` は将棋** |

**依存境界の現状**: `KNOWN_EXCEPTIONS = []`(`core_boundary.test.ts` 63 行)。**意味境界の現状**: 26 本中、意味まで汎用なのは **TS 6 本(eventSchema prng env tokenBudget schemaAdapters llmClient)+ gitState(repo 配置だけ)+ Python 2 本(compare_render check_fonts_embedded)**。残り 17 本は意味上の将棋を持つ。

---

## 2. Semantic Boundary Map(成果物 A)

「依存」= import の向き。「意味」= その字・値・関係が将棋(または冊子・この repo)を知っていないと成り立たないか。
記号: **G** 汎用 / **S** 将棋固有 / **B** 冊子(納品物)の形 / **R** この repo の配置 / **J** 日本語の文言規約(将棋ではないが言語固有)。

### 2.1 `lib/observationAggregates.ts`(844 行)

| 範囲(行) | 中身 | 依存 | 意味 | 根拠 |
|---|---|---|---|---|
| 20〜28 | `MaterialNumbersSource`・`MaterialBucket` | 0 | **S** | 欄名 `patient.time.afterLongThink.quickAfterLongThink`・`bySpent` は将棋の材料の記述(T-5 コメント 16〜18 行が I-4 対象と明記) |
| 34〜35 | `ConditionOp`(8 種)・`Condition` | 0 | **G** | ― |
| 36 | `PopulationFrom` = 7 列の union | 0 | **S** | packet の列名 |
| 37 | `AggregateUnit` = `positions/games/moves/seconds/centipawns` | 0 | **S** | 単位が将棋 |
| 40〜56 | `AggregateRow` | 0 | **G**(欄 `unit`・`population.from` の型だけ S) | 行の形(id・name・population・numerator/denominator/value・derivedFrom・src・recountable・timeDependent)は汎用 |
| 62〜64 | `TIME_FIELDS` | 0 | **S** | `spentSec longThinkCount …` |
| 67〜71 | `GAME_LEVEL_FIELDS`・`RECOGNITION_FIELDS` | 0 | **S** | 局の欄・認識の欄 |
| 83〜88 `factsIndexOf` | `gameById`・`recognitionById` を `gameId` で引く | 0 | **S(鍵の概念)** | 「行は `gameId` で局に属する」という前提。`recognition` の列を特別扱い |
| 91〜98 `rowsOf` | `recognition` だけ `.rows` の下 | 0 | **S** | 92〜94 行 |
| 105〜110 `fieldValueOf` | 行に無い欄を局・認識の行から引く | 0 | **S(前提)** | `gameId`・上の 2 集合 |
| 117〜132 `matches` | 演算子 8 種、無い値は当たらない | 0 | **G** | ― |
| 135〜137 `selectRows` | 母集団 + 追加条件で行を選ぶ | 0 | **G** | ― |
| 144〜149 `countOf` | `unit === "games" && from !== "games"` なら局数で数える | 0 | **S(単位の語)** | 「局」の重複排除の規則が `games` という字と `gameId` に結びつく |
| 152〜153 `gameIdsOf` | `gameId` の集合 | 0 | **S(鍵名)** | ― |
| 157〜164 `sumOf` | 欄の合計 | 0 | **G**(誤りの文に `gameId`) | ― |
| 167〜170 `timeDependentOf` | `from === "time"` か `TIME_FIELDS` | 0 | **S** | ― |
| 179〜191 `RowDefinition` | 行の定義の型 | 0 | **G** | ― |
| 193〜237 `SIGNATURE_GROUPS`・`groupDefinitions` | 「多数の核/それ以外/署名なし」の群 × 3 行 | 0 | **S** | 値と名前が将棋 |
| 239〜404 `ROW_DEFINITIONS` | 17 行 + 群 9 行 = 26 行 | 0 | **S** | 冊子の数の定義(名前の文も将棋) |
| 410〜457 `aggregatesOf` | `ROW_DEFINITIONS` を facts で数える | 0 | **S(表に結合)**。機構は G | 413 行で表を参照 |
| 476〜559 `aggregateAgreementProblems` | (1)側の分子の和 (2)側の分母の和 (3)群の合計 = 局数・崩れ・優勢 (4)局 ≦ 局面 (5)分子 ≦ 分母・理由・timeDependent | 0 | **(1)〜(4) S / (5) G** | 490〜541 行は id を名指し。543〜556 行は行の不変条件 |
| 570〜749 `Booklet*`・`BOOKLET_EXPECTATIONS`・`bookletAgreementProblems` | 冊子の JSON・python の数と突き合わせ | 0 | **S・B** | 相手は `exit_candidates.json`・`dump_booklet_numbers.py` |
| 757〜768 `aggregateCoverageProblems` | 26 行が揃っているか | 0 | **S(表に結合)** | ― |
| 785〜827 `recountProblems` | population のとおりに数え直す・`derivedFrom` も | 0 | **G**(`derivedFrom` の意味が `gameId` の集合 = S の前提) | 820 行 `gameIdsOf` |
| 836〜844 `recountRowProblems` | 1 行だけ・数え直せない行は印 | 0 | **G** | ― |

**結論**: 機構(索引・選択・数え上げ・合計・数え直し)は汎用だが、**「行は `gameId` で局に属し、`games` 単位は局で重複排除する」という前提が汎用関数の中に在る**。Meeting の「発言は `utteranceId` で会議に属する」に当てはめるには、鍵名と単位の語を注入する形が要る(I-4 の範囲を超える。§5・§6 で扱う)。

### 2.2 `lib/observationPacket.ts`(244 行)・`lib/packetRef.ts`(45 行)・契約 schema

| 場所 | 中身 | 依存 | 意味 | 根拠 |
|---|---|---|---|---|
| observationPacket 23〜37 | schema の URL が `observation-packet.v0.1`・`observation-request.v0.1` に固定 | 0 | **S(契約が将棋)** | schema の `facts` は `additionalProperties: false`・7 列すべて `required`(json.load で確認)。行の欄も `additionalProperties: false` |
| 43〜49 `validateObservationPacket/Request` | eventSchema で照合 | 0 | **G**(schema を渡せば) | ― |
| 59〜77 `aggregateFormProblems` | 分数か単独か、ちょうど 1 つ | 0 | **G** | ― |
| 84〜100 `timeLimitProblems`・`commonTimeLimitSec` | `facts.games[].timeLimitSec` が 1 つか | 0 | **S** | 欄名・「局」「持ち時間」の文 |
| 106〜120 `requestAgreementProblems` | `requestedScope.games/timeLimitSec`・局数・`customerRef` | 0 | **S**(`customerRef` の突き合わせだけ G) | ― |
| 126〜138 `observationPacketProblems` | schema + 形 + **筋(S)** + **持ち時間(S)** + 封 | 0 | **S を内包** | 132・134 行。**I-5 未着手** |
| 144〜169 `canonicalJson`・`packetIdOf`・`packetIdProblems` | 封 | 0 | **G** | ― |
| 185〜244 `resolvePacketPath` | path を歩く | 0 | **G**(文法は packetRef に委譲 208 行) | `aggregates.<id>.<part>` と `facts.<列>[n].<欄>` の形は汎用 |
| packetRef 15 | `PACKET_FACTS_COLUMNS` | 0 | **S** | ― |
| packetRef 19 | `AGGREGATE_REF_RE` | 0 | **G** | ― |
| packetRef 24 | `FACTS_REF_RE` | 0 | **S** | 列名 6 + `recognition.(rows\|definitions)`。**I-6 未着手** |
| packetRef 27〜45 | `aggregateRef`・`packetRefPathProblems`・`packetObsIdOf`・`isPacketObsId` | 0 | **G**(文法を注入すれば) | `PACKET_OBS_ID_PREFIX = "packet."` は G |
| `schemas/observation-packet.v0.1` | 封筒 7 欄 | ― | **封筒 G / `facts` S / `aggregates[].unit`・`population.from`・`where[].field` の enum S / `provenance.sources[].type` enum `engine material recognition` S** | enum を json.load で列挙 |
| `schemas/observation-request.v0.1` | `customerQuestions[]{id,text,via}`・`requestedScope{games,timeLimitSec}` | ― | **問い G / scope S** | `requestedScope` は `additionalProperties: false` で `games`・`timeLimitSec` 必須 |
| `schemas/hypothesis.v0.4` | 行の骨格 | ― | **骨格 G**。**S**: `lane` enum 7 語(必須)、`subject{customer,groups,gamesCount}`(必須。`gamesCount` 整数 ≧ 1)、`knowledge.kind` enum `shogi/discovered/coaching`、`knowledge.origin{kifu,lane}` 必須 | json.load |
| `schemas/seat-output.v0.1`・`integration.v0.1` | 封筒・状態 | ― | **G**(`run.seat` enum は LLM 側) | ― |
| `schemas/answer-selection.v0.1` | `p1`・`boards`・`actions`・`humanQueue`・`adoptedBy` | ― | **B**(`boards` = 盤、`p1` = 数 3 つ) | ― |
| `lib/schemaVersions.ts` | 版の並び | 0 | **混在**: hypothesis の版(G)と failure-event・diagnosis-*(S)が同じファイル | 全文 |

### 2.3 `lib/hypothesis.ts`(1008 行)

| 範囲(行) | 中身 | 依存 | 意味 | 根拠 |
|---|---|---|---|---|
| 41〜86 `HypothesisLine` 型 | ― | 0 | **G**。S は 78 行 `kind: "shogi"`・81 行 `origin: { kifu }` | ― |
| 111・114 | `../../../data/governance/banned_words.json`・`../schemas/obs-registry.extra-ids.json` への相対 URL | 0 | **R**(配置)+ **S**(補いの中身は将棋の 30 列) | T-3 の注入口は在るが**既定値が将棋** |
| 208〜223 `loadObsRegistry` | Markdown の `## 1.` 〜 `## 2.` の表を登録簿として読む | 0 | **G(機構)/ 登録簿の中身 S** | 「Markdown 文書を登録簿にする」規約自体は G |
| 306 `KINDS_WITHOUT_PREDICTION` | ― | 0 | **G** | ― |
| 309 `READING_WORDS` | 「という読み」「可能性」… | 0 | **J** | 日本語の読みの語 |
| 313〜392 H-1 | 文の数 ⊂ 観測の数値、割合は `derived` の再計算 | 0 | **G**(`％ 割 倍` は **J**) | **ISO 日付を除かない**(Python の `scan_numbers` は除く 1597・1630 行)― 2 言語で数の拾い方が違う |
| 418〜508 H-2 | 登録簿 or `packet.` の文法 | 0 | **G**(`obs.` 接頭辞 419 行は規約) | ― |
| 510〜523 H-3 | 反証の記録 | 0 | **G** | ― |
| 526〜554 H-4 | 予測は数で・測る前に | 0 | **G** | ― |
| 556〜582 H-5 | 禁止語(注入)・断定しない形 | 0 | **G / J** | 「という読みです」「可能性があります」(578 行)は日本語の形 |
| 584〜606 H-6 | 盲検(`H6_FORBIDDEN_WORDS` 584 行) | 0 | **G / J** | 「本人の言葉」「統合」 |
| 608〜622 H-7 | 昇格 | 0 | **G** | ― |
| 624〜663 H-8 | `/`・`@`・`~` | 0 | **G** | ― |
| 688〜749 H-9 | `resolvePacketPath` + `canonicalJson` 比較 + 集計行なら数え直し | 0 | **G** | 文法は packetRef 経由で S を継承 |
| 768〜816 `H10_PROSE_FIELDS`・`H10_NON_PROSE_FIELDS` | 契約の文字列欄の全分類 | 0 | **G(機構)**。欄名に `knowledge.origin.kifu`(811 行) | ― |
| 843〜870・942〜953 | `facts.recognition.definitions[].{name,nameKana,id}`・`rows[].names`・`definitions[].reviewStatus` | 0 | **S(場所の直書き)**。機構(語彙の表・最長一致・承認状態)は G | 語彙の正本の**場所**が packet の将棋の列 |
| 936 `APPROVED_REVIEW_STATUSES` | `human_reviewed/expert_verified` | 0 | **G** | ― |
| 988〜1008 `validateHypothesisLine` | 固定順で全部回す | 0 | **G** | 入口 |

### 2.4 席・統合・採用・実行(TS)

| ファイル:行 | 中身 | 依存 | 意味 |
|---|---|---|---|
| seatOutput 19 `SEAT_EXCLUDED_INPUTS` | `answer_menu.json exit_candidates.json 9_本編.md` | 0 | **B** |
| seatOutput 166 / integration 310 | `knowledge: { kind: "discovered", …, origin: { kifu: customerRef, lane } }` を**書く** | 0 | **契約の欄名(S の字)**。改名は版上げ |
| seatOutput 218〜 `seatOutputProblems`(E-1 封印語・E-2 以降) | ― | 0 | **G** |
| seatOutput 281 / integration 402 | 既定の登録簿 path `../../../docs/OBSERVATION_ITEMS.md` | 0 | **R** |
| integration 31 `INTEGRATOR_EXCLUDED_INPUTS` | 冊子のファイル名 + "seat names" | 0 | **B** |
| integration 33〜35 `SEAT_NAME_RE`・`SEAT_COUNT_REFERENCE_RE` | ― | 0 | **G / J**(「席」「一致」) |
| integration 80〜95 `seatPermutation` | PRNG で席の順を隠す | 0 | **G** |
| integration 366〜 `integrationProblems`(I-1〜I-4) | ― | 0 | **G** |
| seatRun 40〜46 `FIXED_INSTRUCTION_SHA256` | 将棋の指示文 4 本の sha | 0 | **S の値が Core の定数** |
| seatRun 49〜56 `fixedShaProblems` | 表に無い名前も誤り | 0 | **G(機構)** |
| seatRun 63 `AbsentReason` 9 種・158〜 `runSlot`・386〜 `runAll` | ― | 0 | **G** |
| exitSelect 62〜64 `isBoardRef` | `facts.engine[` | 0 | **S・B** |
| exitSelect 104・181・205 | 下書き・`adoptedBy` null・門 | 0 | **G** |
| answerSelection 25〜26 | `P1_COUNT = 3`・`BOARD_COUNT = 2` | 0 | **B** |
| answerSelection 29〜33 | `ADOPTED_STATUSES`・`STATUSES_NEEDING_OBSERVATION` | 0 | **G** |
| answerSelection 136〜 `selectionProblems` | S-2 本数(B)・S-3 集計 id(G)・S-4 itemRef(G)・S-5 問いごと 1 行(G)・S-6 `menuIds`(**承認済み行動表 = S**)・S-7(G)・S-8 数を含まない(G) | 0 | **G に B・S が 2 点** |
| seatInput 100〜110 `READING_GUIDE`・82〜98 `OMITTED/NOT_INCLUDED`・404〜450 列の描画 | LLM に送る将棋の読み方 | 0 | **S**(計画どおり [B]) |
| seatInput 143〜167 `numberTokens`・`numberInclusionProblems`、254 `sealOf`、268 `normalizeLastKey`、181 `identifierProblems` | ― | 0 | **G** |
| observationProvenance 68・73・77・89・102 | `kind` の文字列 5 本(「対局後診断の報告の材料」「分かれ道の候補と側」…) | 0 | **S** |
| observationProvenance 23〜25・31・111・135・164 | `ThresholdRow`・`metaValue`・`materialThresholds`・`provenanceOf`・`traceProblems` | 0 | **G**(T-4 で閾値は注入) |
| gitState 24 | `COUNTED_PREFIXES` | 0 | **R** |

### 2.5 Python

| ファイル:行 | 中身 | 依存 | 意味 |
|---|---|---|---|
| check_answer 97〜109 | `BANNED_WORDS_JSON` の相対 path(`data/governance`)・`load_banned_words` | 0 | **R**(機構 G) |
| check_answer 113 `ACTION_PHRASES` | 「してみては」「を目安に」… | 0 | **J・B**(冊子の行動文の規約) |
| check_answer 115〜141 `MENU_TAG_RE`・`PRIORITY_TAG_RE`・`POS_TAG_RE`・`AGG_TAG_RE`・`ANS_TAG_RE`・`MARK_TAG_RES`・144 `strip_marks` | 印の文法 | 0 | **`agg`・`ans` G / `menu`・`priority`・`pos` B** |
| check_answer 151 `POS_INNER_RE` | `G/P 付録N [組]` | 0 | **B** |
| check_answer 154〜158 `PIECE_CHARS`・`MOVE_RE`・`FIRST_CANDIDATE_WA_RE`・`GAME_PLY_REF_RE` | 指し手の字 | 0 | **S** |
| check_answer 160 `RATIO_WORD_RE` | `倍\|割` | 0 | **J** |
| check_answer 268〜1444 材料層(`PatientFile`・`side_match_of`・`SIDE_JP`・`time_cause_*`・`m1_holds`〜`m9_*`・`MENU_*`・`registered_pairs_of`・`reviewed_shape_names`・`NAME_LIKE_RE`) | ― | 0 | **S**(`reviewed_shape_names` は `data/{shapes,openings,intents}` を glob = **R・S**) |
| check_answer 1450〜1554 `build_materials` | ctx を組む | 0 | **S** |
| check_answer 1566〜1575 `DEV_SECTION_RE`・`strip_dev_section` | 「書いた側の記録」 | 0 | **J・B** |
| check_answer 1578〜1586 `find_fraction_pairs` | `a / b`・「n のうち m」「n 局のうち m 局」 | 0 | **G / J(「のうち」「局」)** |
| check_answer 1589〜1641 `mask_spans`・`ISO_DATE_RE`・`SMALL_NUMBER_MAX`・`scan_numbers` | 数の拾い方の 1 か所 | 0 | **G**(印の正規表現 B を内側で呼ぶ 1620〜1624 行) |
| check_answer 1643〜1657 `check_line_numbers` | ctx の `pairs`・`allowedNumbers` と照合 | 0 | **G** |
| check_answer 1659〜1668 `check_line_moves` | 付録 2 の印字と照合 | 0 | **S** |
| check_answer 1671〜1674 `check_line_banned` | ― | 0 | **G** |
| check_answer 1686〜1692 `check_line_action_phrases` | ― | 0 | **B・J** |
| check_answer 1694〜1699 `check_line_names` | `NAME_LIKE_RE` × `reviewedNames` | 0 | **S** |
| check_answer 1710〜1743 `check_menu_tags` | M1〜M9 の成立・minN・答え合わせの下限 | 0 | **S・B** |
| check_answer 1746〜1808 `check_pos_tags`・`check_appendix3_position` | 付録 1〜4 の局面 | 0 | **B・S** |
| check_answer 1810〜1833 `check_answer` | 7 検査を 1 行ずつ | 0 | **G(順)/ 呼ぶ先に S・B** |
| exit_verification 23〜44 `GateRules`・`AggRules` | 必須欄の束 | 0 | **B(欄の集合)**。`p1_role p2_role p3_role p1_fact_count board_count todo_marker draft_only_headings note_prefix nothing_to_hide_sentence ans_section_head ans_statuses` は冊子の形を前提にした欄 |
| exit_verification 47〜95 `sections_of`・`without_draft_only`・`section_lines` | ― | 0 | **G** |
| 96〜141 `ORDERED_ITEM_RE`・`number_claims` | ― | 0 | **G** |
| 143〜158 `normalize_mark`・`pos_marks`・`menu_marks` | ― | 0 | **G(正規表現を受ける)** |
| 161〜169 `check_todo`、171〜186 `check_opening`(cands の `opening` と突き合わせ) | ― | 0 | **G** |
| 188〜221 `check_p1`(箇条書き `- ` = 事実、本数、`cands.p1Numbers`) | ― | 0 | **B(cands の鍵・箇条書きの規約)** |
| 222〜262 `check_p1_reaches_the_actions`(`cands.actionFractions`、固定文) | ― | 0 | **B** |
| 264〜281 `check_no_unit_mismatch`(`cands.unitMismatchFractions`) | ― | 0 | **B** |
| 283〜300 `check_p2`(`cands.boards`) | ― | 0 | **B(盤)** |
| 302〜318 `check_p3`(`cands.menuPassed`) | ― | 0 | **B(行動表)** |
| 320〜335 `check_draft_leftovers` | ― | 0 | **G** |
| 337〜450 `ans_tags_of`・`question_ids_of(request.customerQuestions[].id)`・`selected_statuses_of(selection.answers[])`・`check_ans_tags` | ― | 0 | **G(契約 request/answer-selection の 2 欄に依存)** |
| 452〜577 `agg_tags_of`・`numbers_of_aggregate_row`・`fact_line_holes`・`agg_line_missing`・`check_agg_tags` | ― | 0 | **G**(型の表は `AggRules` で注入) |
| 579〜599 `verify` | **固定順で 11 検査**(`check_p2`・`check_p3` を必ず呼ぶ) | 0 | **B(順と集合)** |
| exit_verification 全体の文言 | 「(ii) 「ひとことで」の節が無い」等 | ― | **J・B**(G-9 がこの字で固定) |
| check_structure 54〜62・73・97〜99・115・132〜134・174〜192・742〜752・844 | `SECTIONS`・`SCOPE_SENTENCE_TEMPLATE`・`OPENING_*`・`TERM_LINES`・`MAX_*_PAGES`・`BOARD_COUNT`・`HONBUN_P1_FACT_COUNT`・`QUESTION_HEADING`・`GLOSSARY_FRAGMENTS` | 0 | **B・S・J** |
| check_structure 195 `heading_matches`、231 `page_texts`、310 `check_sections`、378 `check_pages`、498 `check_bundled_index`、562 `check_name_agrees`、602 `check_no_real_name`、630 `check_one_referent` | ― | 0 | **G(機構)** |
| check_delivery 24・28 | `from check_answer import BANNED_WORDS`・`BANNED_18` | 0 | **R(ハブ経由)** |
| check_delivery 31 `ALWAYS_FORBIDDEN` | `@ /Users/ 水匠 None` | 0 | **G 3 語 + S 1 語(水匠)** |
| check_delivery 55 `ALWAYS_FORBIDDEN_WORDS` | `最善手` | 0 | **S** |
| exit_index 170〜180・268〜304 | `COUNTING_NOTES`・`COVER_*` | 0 | **S・B(顧客向けの文)** |
| exit_index 359・366 | `_index_pos`・`_index_sec` を flowable から拾う | 0 | **G(reportlab の機構)** |
| compare_render 全体 | ― | 0 | **G** |
| check_fonts_embedded 全体 | ― | 0 | **G** |
| rename_list 拾う規則 | `S_H1)`・`_TITLE =`・md の `#` | 0 | **R** |

### 2.6 見落としの点検(依頼に名指しされた 4 点以外)

| 見つけたもの | 場所 | 分類 |
|---|---|---|
| **`gameId` と `games` 単位が汎用関数の中に在る** | observationAggregates 85〜87・107〜109・146〜147・152〜153・820 行 | S(前提)。I-4(表の分離)だけでは消えない |
| **TS と Python で数の拾い方が 2 本**(TS H-1 は ISO 日付を除かない、Python `scan_numbers` は除く。小数・全角の扱いも別) | hypothesis 360〜375 行 / check_answer 1604〜1641 行 | 計画 §6.3 の「統一は Phase 5 以降」のまま |
| **語彙の正本の「場所」が packet の列名に直書き**(H-10/H-11) | hypothesis 843〜870・942〜953 行 | S。計画 §4.2 の `vocabulary(packet)` に相当する注入口が無い |
| **指示文の sha 表が Core の定数** | seatRun 40〜46 行 | S の値。`fixedShaProblems` の機構は G |
| **登録簿・禁止語・補いの既定 path が repo 配置に固定** | hypothesis 111・114 行、seatOutput 281 行、integration 402 行、check_answer 97 行 | R |
| **`GateRules` の必須欄が冊子の形を前提**(欠けると namedtuple が落とす = 冊子以外の器では `p2_role` 等にダミーが要る) | exit_verification 23〜35 行 | B |
| **`verify` の固定順が `check_p2`・`check_p3` を必ず呼ぶ** | exit_verification 585〜598 行 | B。個々の関数は G |
| **`schemaVersions.ts` が将棋の契約と hypothesis の版を 1 ファイルに持つ** | 全文 | 混在 |
| **`check_fonts_embedded.py` に試験が無い** | `ls report-pdf/*_test.py` | 切り出し時に単体試験なしで Core に入る |
| **`exit_verification.py` の試験は `exit_gate_test.py` の中**(e1〜e6、1280〜1373 行。`exit_verification_test.py` は無い) | ― | 切り出すと試験が Adapter 側に残る |
| **`check_structure.py`・`check_delivery.py`・`exit_fill.py`・`exit_gate.py` が `check_answer` をハブとして import**(走査層と材料層が同じ module) | 各ファイル先頭 | I-7 未着手の帰結 |
| **日本語の規約(J)** が多数(読みの形・「のうち」・「席」・問題文の字) | 上の表 | 将棋ではないが言語固有。Core を日本語前提にするかは**未決** |

---

## 3. Adapter に移すべき仕様 / Core に残す汎用機構 / 判断保留

### 3.1 Shogi Adapter へ移す(将棋固有の仕様)

| # | 仕様 | 今の場所 | 移し方の型(計画 §7 の I) |
|---|---|---|---|
| A-1 | `ROW_DEFINITIONS`・`SIGNATURE_GROUPS`・`groupDefinitions`・`aggregatesOf` の表への結合・`aggregateCoverageProblems`・`Booklet*`・`BOOKLET_EXPECTATIONS`・`bookletAgreementProblems`・`MaterialNumbersSource` | observationAggregates 20〜28・193〜457・570〜768 | **I-4**(写し → 照合 → 元を re-export) |
| A-2 | `aggregateAgreementProblems` の (1)〜(4)(id 名指しの関係) | observationAggregates 490〜541 | **I-4/I-5**(関係の表を注入。(5) は Core に残す) |
| A-3 | `timeLimitProblems`・`commonTimeLimitSec`・`requestAgreementProblems`(scope の欄) | observationPacket 84〜120 | **I-5**(`observationPacketProblems(packet, schema, spec)`) |
| A-4 | `PACKET_FACTS_COLUMNS`・`FACTS_REF_RE` の列の集合 | packetRef 15・24 | **I-6**(`makePacketRefGrammar(columns, nested)`、既定は現行) |
| A-5 | `PopulationFrom`・`AggregateUnit`・`TIME_FIELDS`・`GAME_LEVEL_FIELDS`・`RECOGNITION_FIELDS`・`gameId`/`games` の鍵と単位 | observationAggregates 36〜37・62〜71・85〜153 | **I-4 の拡張**(鍵名・単位の語を `spec` で渡す。計画に無い追加) |
| A-6 | `facts.recognition.{definitions,rows}` の場所(H-10/H-11 の語彙の正本) | hypothesis 843〜870・942〜953 | **新 I**(`vocabulary(packet)` を opts で渡す。計画 §4.2 に名前だけ在る) |
| A-7 | `knowledge.kind: "shogi"`・`origin.kifu`・`lane` enum・`subject.gamesCount` | hypothesis 78・81 行、schema v0.4 | **契約の版上げ = 人間の承認**。移行中は触らない(計画 §7「やらないこと」) |
| A-8 | `SEAT_EXCLUDED_INPUTS`・`INTEGRATOR_EXCLUDED_INPUTS` | seatOutput 19・integration 31 | **I-9**(設定へ) |
| A-9 | `FIXED_INSTRUCTION_SHA256` の値 | seatRun 40〜46 | 新 I(表を注入。機構 `fixedShaProblems` は残す) |
| A-10 | `isBoardRef`(`facts.engine[`)・`P1_COUNT`・`BOARD_COUNT`・S-6 の `menuIds` | exitSelect 62、answerSelection 25〜26・136〜 | 器の形の定数として注入 |
| A-11 | `sourcesOf` の `kind` 文字列 5 本 | observationProvenance 68〜102 | 呼ぶ側(将棋 CLI)が `kind` を渡す |
| A-12 | `check_answer.py` の材料層・`check_line_moves`・`check_line_names`・`check_menu_tags`・`check_pos_tags`・`PIECE_CHARS`・`MOVE_RE`・`NAME_LIKE_RE`・`reviewed_shape_names`・`build_materials`・`SIDE_JP`・`MENU_*` | check_answer 139〜1554・1659〜1808 | **I-7**(走査層を `text_claims.py` へ写し、材料層は check_answer に残して Adapter に再分類) |
| A-13 | `check_structure.py` の定数すべて(`SECTIONS` …)と `exit_index.py` の顧客向け文 | 上表 | 定数を Adapter 側へ、機構を Core 側へ(分離は未設計) |
| A-14 | `check_delivery.py` の `水匠`・`最善手` | check_delivery 31・55 | 語の表を注入 |
| A-15 | `obs-registry.extra-ids.json` の 30 列、`docs/OBSERVATION_ITEMS.md` §1 の中身、`READING_GUIDE`・`renderSeatInput` の列、指示文 4 本、`deliver.ts` の段表、`observationFacts`/`observationMaterials`/CLI `observationPacket.ts` | 既に Adapter 側(または仕様データ) | 動かさない |

### 3.2 Core に残す汎用機構

| 機構 | 場所 | 条件 |
|---|---|---|
| JSON Schema 部分集合の検証 | eventSchema | そのまま |
| 封(`canonicalJson`・`packetIdOf`・`packetIdProblems`)・`aggregateFormProblems`・`resolvePacketPath` | observationPacket 59〜77・144〜244 | 文法を注入(I-6) |
| `Condition`・`Population`・`AggregateRow`・`matches`・`selectRows`・`countOf`・`sumOf`・`recountProblems`・`recountRowProblems`・整合関係 (5) | observationAggregates | 鍵名・単位の語を注入(A-5) |
| H-1〜H-11 の骨格・`CheckResult`・`validateHypothesisLine`・`loadObsRegistry`(Markdown 登録簿の読み方)・`H10_*` の全分類・`namesInText`・`APPROVED_REVIEW_STATUSES` | hypothesis | 登録簿・禁止語・語彙の場所を注入(A-6) |
| 席の封筒(E-1 封印語〜)・統合(I-1〜I-4・`seatPermutation`)・実行(再試行・費用上限・`AbsentReason`)・`fixedShaProblems` | seatOutput・integration・seatRun | 除外一覧・sha 表を注入 |
| 採用の門(`adoptedBy` null・`selectionGateProblems`)・状態機械(`ADOPTED_STATUSES`・S-3〜S-5・S-7・S-8) | exitSelect・answerSelection | 本数・menuIds を注入 |
| provenance の枠・`traceProblems`・`metaValue`・`ThresholdRow` | observationProvenance | そのまま(T-4 済み) |
| `readGitState`・dirty の表示 | gitState | `COUNTED_PREFIXES` を引数に |
| LLM 呼び出し・schema 変換・費用・env・PRNG | llmClient・schemaAdapters・tokenBudget・env・prng | そのまま |
| `numberInclusionProblems`・`sealOf`・`normalizeLastKey`・`identifierProblems` | seatInput 143〜298 | seatInput から**切り出し**が要る(描画と同居) |
| Python: `sections_of`・`number_claims`・印の拾い・`check_todo`・`check_opening`・`check_draft_leftovers`・`check_ans_tags`・`check_agg_tags`・`agg_line_missing`・`numbers_of_aggregate_row` | exit_verification | `GateRules` の冊子欄を任意化するか、`verify` を冊子側へ(未設計) |
| Python: `scan_numbers`・`find_fraction_pairs`・`mask_spans`・`strip_marks`・`check_line_numbers`・`check_line_banned`・`check_answer`(順) | check_answer 1566〜1833 | **I-7** |
| Python: `compare_render`・`check_fonts_embedded`・`check_delivery` の機構・`check_structure` の機構・`exit_index` の索引機構・`rename_list` の機構 | 各ファイル | 定数の注入(A-13・A-14) |

### 3.3 判断保留(人間か司令塔が決めること)

| # | 論点 | なぜ保留か |
|---|---|---|
| H-1 | **Core を日本語前提にするか**(読みの形「という読みです」、「のうち」、問題文の字、`SEAT_COUNT_REFERENCE_RE` の「席」) | 将棋ではないが言語固有。Meeting(日本語)なら困らないが、Core の約束として書くかは設計判断 |
| H-2 | **`origin.kifu`・`knowledge.kind: "shogi"`・`lane`・`subject.gamesCount` の改名/一般化** | 契約の版上げ = 人間の承認(CLAUDE.md 4 番の構造的知識) |
| H-3 | **TS と Python の数の拾い方を 1 本にするか** | 計画 §6.3「Phase 5 以降」。G-9 の文言が両方に固定されている |
| H-4 | **`exit_verification.verify` の固定順と `GateRules` の必須欄を Core に置くか、冊子側に戻すか** | T-5 で Core に入れたが、`check_p2`(盤)・`check_p3`(行動表)は冊子の形。順は G-9 に固定 |
| H-5 | **`gameId`/`games` の一般化**(行の所属鍵・重複排除の単位) | 計画の I-4 の範囲外。変えると `recountProblems` の `derivedFrom` の意味が動く |
| H-6 | **`schemaVersions.ts` の分割** | 版の並びの正本をどちらの repo に置くか |
| H-7 | **`check_fonts_embedded.py` を試験なしで Core に数えるか** | 単体試験が無い |
| H-8 | **Golden Master の正本の置き場**(`out/` は gitignore、期待値 JSON は `out/c5/...` の path を `inputs` に持つ) | 計画 §5 冒頭の人間判断がまだ(追跡するか、sha と数だけか) |

---

## 4. Core の最小 API(成果物 C。現在の実装から写した。新設しない)

**束ねた `PacketSpec` 型は今も存在しない**(計画 §4.2 と同じ)。各要素は別 module の定数・引数・既定値に散っている。下は「今ある入口」の一覧で、**列「注入口」が `無`** のものは将棋の値が Core の中に残っている。

### 4.1 入力 → 出口(TS)

| 概念 | 入口(関数 ― ファイル:行) | 入力 | 返り値 | 注入口(今あるもの) |
|---|---|---|---|---|
| 契約の形 | `validate(instance, schema)` eventSchema:76 | JSON + JSON Schema | `string[]`(空 = 通過) | schema を渡す |
| packet の封 | `packetIdOf(facts, aggregates)` observationPacket:159、`canonicalJson` :144、`packetIdProblems(packet)` :165 | facts・aggregates | 16 桁 / `string[]` | ― |
| packet の検査入口 | `observationPacketProblems(packet, schema?)` :126 | packet | `string[]` | schema のみ。**筋・持ち時間は注入口 無(I-5)** |
| 集計の形 | `aggregateFormProblems(aggregates)` :59 | aggregates | `string[]` | ― |
| 参照の文法 | `packetRefPathProblems(path)` packetRef:32、`aggregateRef(id, part)` :27 | path | `string[]` / path | **列の集合 無(I-6)** |
| 参照の解決 | `resolvePacketPath(packet, path)` observationPacket:204 | packet・path | `{ok,value}\|{ok:false,reason}` | 文法は packetRef に委譲 |
| 数え直し | `recountProblems(packet, onlyId?)` observationAggregates:785、`recountRowProblems(packet, id)` :836、`selectRows/countOf/sumOf(index, population, …)` :135〜164 | packet / FactsIndex | `string[]` / `{problems, notes}` / 数 | **鍵名 `gameId`・単位 `games` 無(A-5)** |
| 主張の検証 | `validateHypothesisLine(line, {today, registry, schema?, bannedWords?, packet?})` hypothesis:988 | 1 行 + opts | `CheckResult[]`(`{check, ok, messages, skipped?, notes?}` :227) | `registry`・`bannedWords`・`schema`・`packet`。**語彙の場所 無(A-6)** |
| 登録簿 | `loadObsRegistry(mdPath, extraIds?)` :208、`loadHypothesisBannedWords(path?)` :145、`loadObsRegistryExtraIds(path?)` :171 | path | `Set<string>` / `string[]` | path(既定は repo 配置) |
| 席の封筒 | `completeSeatOutput(llm, ctx)` seatOutput:104、`seatOutputProblems(envelope, {meta, request, today, registry?, bannedWords?, obsItemsPath?})` :218 | LLM 出力 / 封筒 | 封筒 / `string[]` | `registry`・`bannedWords`。**`SEAT_EXCLUDED_INPUTS`・`origin.kifu` 無** |
| 統合 | `buildIntegrationInput(slots, ctx)` integration:169、`completeIntegration(llm, ctx)` :261、`integrationProblems(output, input, {today, registry?, bannedWords?, obsItemsPath?})` :366、`seatPermutation(runId, n)` :85 | ― | ― | 同上 |
| 実行 | `runSlot/runSeat/runAll(cfg, deps)` seatRun:158/311/386、`fixedShaProblems(basename, content)` :49 | 設定 + 依存注入(`SlotDeps`) | `SlotRunResult`・`RunAllResult` | deps は注入。**sha 表 無(A-9)** |
| 採用 | `buildSelectionDraft(materials)` exitSelect:104、`adoptedByProblems(selection)` :181、`selectionGateProblems(…)` :205、`validateAnswerSelection` answerSelection:45、`selectionProblems(selection, {aggregateIds, statementByItemRef, questionIds, menuIds})` :136 | ― | `string[]` | `ctx` は注入。**`P1_COUNT`・`BOARD_COUNT`・`isBoardRef` 無** |
| 出どころ | `provenanceOf({…, toolThresholds})` observationProvenance:135、`sourcesOf(input)` :59、`traceProblems(packet, options)` :164 | ― | provenance / `string[]` | 閾値は注入(T-4)。**`kind` の文字列 無(A-11)** |
| git | `readGitState(cwd, runGit?)` gitState:105 | cwd | `GitState` | `runGit`。**`COUNTED_PREFIXES` 無** |
| LLM | `callStructured(req, deps)` llmClient、`adaptSchema` schemaAdapters、`budgetDecision` tokenBudget、`loadDotEnv/readEnv` env、`Prng` prng | ― | ― | 全部注入済み |
| 校正 | `numberInclusionProblems(dataText, packet, request)` seatInput:154、`sealOf(runId, section)` :254、`normalizeLastKey` :268 | ― | `string[]` / 語 | ― |

### 4.2 入力 → 出口(Python)

| 概念 | 入口 | 入力 | 返り値 | 注入口 |
|---|---|---|---|---|
| 門の判定 | `verify(raw_md, cands, packet, request, selection, rules, notes, check_sentences)` exit_verification:579 | md 文字列・候補 JSON・packet・request・selection・`GateRules`・文の検査の callable | `problems: list[str]`(`notes` に報告) | **`GateRules`・`AggRules` で全部注入**(T-5)。ただし欄の集合は冊子の形 |
| 個々の判定 | `number_claims(lines, scan_numbers, menu_tag_re)` :99、`check_ans_tags(md, request, selection, problems, notes, rules)` :401、`check_agg_tags(md, packet, problems, notes, cands, rules)` :531、`agg_line_missing(line, allowed, cands, agg_rules)` :517 | ― | 破壊的に `problems`/`notes` へ追記 | 同上 |
| 数の拾い方 | `scan_numbers(line, small_max=None)` check_answer:1604 | 1 行 | `(倍割か, 分数[(a,b,span)], 割合[n], 単独[n])` | **無**(印の正規表現・`RATIO_WORD_RE` が同 module の定数。I-7) |
| 文の検査 | `check_answer(markdown_text, ctx)` check_answer:1810 | md + `ctx`(`pairs allowedNumbers menuIds materials menuMinN menuItemsById positions whatifPdfText reviewedNames` ― `build_materials` が組む) | `[(line_no, reason, line)]` | ctx は注入だが**ctx の鍵の集合が将棋の材料の形** |
| PDF の封 | `profile(path)`・`differences(a, b)`・`write_seal(seal_path, pdfs)`・`verify_seal(seal_path)` compare_render:59〜145 | PDF path | dict / 差分一覧 / rc | ― |
| 納品の衛生 | `check_delivery.py <dir> [--forbid 語]` CLI | フォルダ | rc + stderr | `--forbid`。**固定語 無** |
| 器の門 | `check_structure.py` CLI(`main` :860) | md・PDF・索引 | rc + stderr | **無**(定数が module 内) |

### 4.3 Core が返すものの形(現行で統一されていない 3 種)

| 形 | 使う所 |
|---|---|
| `string[]`(空 = 通過、1 件 1 行) | observationPacket・observationAggregates・seatOutput・integration・exitSelect・answerSelection・observationProvenance・seatInput |
| `CheckResult[]`(検査名 × ok × messages、`skipped`・`notes`) | hypothesis(`validateHypothesisLine`)。「0 件」と「検査していない」を分けられる唯一の形 |
| rc + stderr の行(`(報告)`/`注記:` で始まる行は警告) | Python CLI(goldenMasterCheck:95〜111 がこの規約で分類) |

**Core 最小 API 案(成果物 C)としての結論**: 新しい API を設計せず、**今ある 3 入口を Core の口とする** ― TS `observationPacketProblems`(+ 封・解決・数え直し)、TS `validateHypothesisLine`(+ 席・統合・採用の `*Problems`)、Python `exit_verification.verify`(+ `scan_numbers`)。足りないのは API の形ではなく **注入口 7 か所**(I-5・I-6・A-5・A-6・A-9・A-10・A-11)と **Python の走査層の分離(I-7)** である。

---

## 5. 将棋を完全に外しても成立する部分(Shogi Adapter を外した状態の想定)

「外す」= `scripts/playtest/lib/` の §2.1.2 の将棋 module 群・`report-pdf/` の `SHOGI_PY_MODULES`・`data/`・`apps/`・`docs/OBSERVATION_ITEMS.md`・`schemas/obs-registry.extra-ids.json` が無い、と仮定する。

### 5.1 そのまま動く(入力を与えれば将棋なしで実行できる)

| 部分 | 根拠 |
|---|---|
| `eventSchema.validate`・`prng`・`env`・`tokenBudget`・`schemaAdapters`・`llmClient` | import 0・将棋語 0 |
| `canonicalJson`・`packetIdOf`・`packetIdProblems`・`aggregateFormProblems` | facts の中身を見ない |
| `resolvePacketPath` の **`aggregates.<id>.<part>` 側** | 文法 `AGGREGATE_REF_RE` は汎用 |
| H-3・H-4・H-6・H-7・H-8 | 行の欄だけを見る |
| H-9 の **集計側**(値の一致 + `recountRowProblems`) | `aggregates` の行の形に `population` が在れば数え直せる(ただし `facts` の列名と `gameId` は前提) |
| `seatPermutation`・`seatOutputProblems` の E-1(封印語)・`integrationProblems` I-1〜I-4 | ― |
| `runSlot/runAll`・`fixedShaProblems`(表に名前が在れば) | ― |
| `adoptedByProblems`・`selectionGateProblems`・`ADOPTED_STATUSES`・S-3/S-4/S-5/S-7/S-8 | ― |
| `provenanceOf`・`traceProblems`(閾値を渡す) | T-4 |
| `readGitState`(この repo の配置なら) | ― |
| `numberInclusionProblems`・`sealOf`・`normalizeLastKey` | ― |
| Python `compare_render`・`check_fonts_embedded` | `fitz` だけ |
| Python `exit_verification` の `sections_of`・`number_claims`・`check_ans_tags`・`check_agg_tags`・`agg_line_missing`(`scan_numbers` と正規表現を渡せば) | 標準ライブラリだけ。**ただし `scan_numbers` の実体は `check_answer.py`(将棋側のハブ)に在る**ので、I-7 前は「渡す物」を将棋側から借りる |

### 5.2 仕様注入だけで動く(値を差し替えれば動く。注入口の有無は §4)

| 部分 | 注入するもの | 注入口 |
|---|---|---|
| `packetRefPathProblems`・`resolvePacketPath` の `facts.*` 側 | 列の集合・入れ子 | **無(I-6)** |
| `observationPacketProblems` | 筋の関係・scope の検査・schema | schema のみ(I-5) |
| `selectRows/countOf/sumOf/recountProblems` | 所属の鍵名・重複排除の単位・局レベル欄 | **無(A-5)** |
| H-1 | ―(動く。割合の語 `％ 割 倍` は日本語) | ― |
| H-2 | 登録簿 | `registry` 引数(有) |
| H-5 | 禁止語 | `bannedWords` 引数(有)。読みの形は日本語固定 |
| H-10・H-11 | 語彙の表と承認状態の**場所** | **無(A-6)**。今は `facts.recognition.*` に置けば動く(欄名が将棋のまま) |
| `seatOutput`・`integration` の除外一覧・`origin.kifu` | 一覧・欄名 | **無(I-9・契約)** |
| `seatRun` の sha 表 | 表 | **無(A-9)** |
| `answerSelection` の本数・`menuIds`、`exitSelect.isBoardRef` | 定数 | `menuIds` は ctx(有)。本数・盤は**無** |
| `exit_verification.verify` | `GateRules`・`AggRules` | **有**(T-5)。ただし `p2_role`・`board_count` 等は必須で、`check_p2/p3` は必ず走る |
| `check_structure` の機構 | `SECTIONS` 等 | **無** |
| `check_delivery` の機構 | 語 | `--forbid`(有)。固定語は無 |
| `gitState` | `COUNTED_PREFIXES` | **無** |

### 5.3 将棋固有のため成立しない(外せば消えるもの)

`ROW_DEFINITIONS`・`aggregatesOf`・`aggregateAgreementProblems` (1)〜(4)・`bookletAgreementProblems`・`aggregateCoverageProblems`・`timeLimitProblems`・`requestAgreementProblems`・`observation-packet.v0.1` の `facts`・`hypothesis.v0.4` の `lane`/`knowledge.kind`/`subject.gamesCount`/`origin.kifu`・`answer-selection.v0.1` の `boards`・`check_answer.py` の材料層と検査 2・4・5・6・7・`check_structure.py` の定数・`exit_index.py` の文・`exit_gate.py` 全体・`loadObsRegistry` の中身・`obs-registry.extra-ids.json`・`READING_GUIDE`・指示文 4 本・`deliver.ts` の段表・`observationFacts`/`observationMaterials`。

**数で言うと**: Core 候補 26 本のうち、5.1 に全部が入るのは **TS 7 本(eventSchema prng env tokenBudget schemaAdapters llmClient gitState※)+ Python 2 本(compare_render check_fonts_embedded)**。残り 17 本は 5.2 か 5.3 を含む。

---

## 6. Meeting Adapter への再利用可能性(成果物 E。コードは書かない)

### 6.1 仮想入力を現行の契約に置くとどうなるか

| 仮想入力 | 現行の器に置く形(案) | 現行で起きること(根拠) |
|---|---|---|
| 発言 3 件(時刻・話者・原文) | `facts.utterances[i]{at, speaker, text, src}` | **`observation-packet.v0.1` の schema を通らない** ― `facts` は `additionalProperties: false` で 7 列が `required`(json.load)。→ 新しい契約(別 schema)か版上げが要る |
| 数(500 万円) | `facts.numbers[i]{value: 500, unit: "万円", utteranceRef}` | H-1 は観測の**数値**だけを許す(`collectValueNumbers` 313〜329 行。文字列の中の数は拾わない)。原文 `text` を観測の値にしても 500 は許されない。**数値の行が別に要る** |
| 日付(11 月 1 日) | `facts.dates[i]{iso: "2026-11-01", utteranceRef}` | H-9 の `canonicalJson` 比較は文字列でも効く。**H-1 は「11月1日」から 11 と 1 を、「2026-11-01」から 2026・11・1 を数として拾う**(360〜375 行。ISO を除かない)→ 観測に 11・1(・2026)の数値が無いと落ちる。Python `scan_numbers` は ISO を除く(1630 行)。**2 言語で規則が違う** |
| 固有名詞(佐藤・山田・鈴木) | `facts.recognition.definitions[]{id, name, reviewStatus}` + `rows[]{names}`(欄名は将棋のまま借りる) | H-10 の機構(語彙の表・最長一致)は**そのまま効く**。場所が `facts.recognition` 固定(843〜870 行)なので**この欄名で置けば動く**。H-11 の承認状態も `reviewStatus: human_reviewed` で動く |
| 参照 | `packetRef.path = "facts.utterances[0].text"` | **`FACTS_REF_RE` が落とす**(packetRef 24 行。列名 6 + recognition だけ)→ H-2・H-9 が「文法に合わない」で止まる。**I-6 が無いと Meeting は 1 件も GROUNDED にならない** |

### 6.2 4 つの Claim の表現可能性

| Claim | 期待 | 現行の検査でどう出るか | 再利用 | 詰まる所 |
|---|---|---|---|---|
| A社担当 = 佐藤 | GROUNDED | `kind: finding, factOrHypothesis: fact`、observations = `[{obsId: "packet.facts.utterances[0].text", packetRef.path 同, value: "A社の担当は佐藤さんです。"}]`。H-9: `resolvePacketPath` → 値一致 → ok。H-10: 「佐藤」が `rows[].names` に在れば ok。H-5: fact 行は読みの語が無ければ ok。H-3/H-4/H-6/H-7/H-8 ok | H-3〜H-11 の機構すべて | **文法(I-6)**。schema 検査は `lane`・`subject.gamesCount`・`knowledge.origin.kifu` で落ちる(新契約まで `schema` の行だけ false。H は回る ― 988〜1007 行は schema が落ちても H を返す) |
| 契約金額 = 600 万円 | VALUE_MISMATCH | (a) 観測に `facts.numbers[0].value = 500` を引き、文に 600 → **H-1「数「600」が observations の値に無い」**。(b) 観測の `value` を 600 と書き packet は 500 → **H-9「value が packet と違う(行 600 / packet 500)」**。どちらも**落ちる**という形で出る | H-1・H-9 | 「VALUE_MISMATCH」という**語は現行に無い**。出るのは `CheckResult{check:"H-1"\|"H-9", ok:false}`。**判定の語彙を増やさないなら、Meeting 側で「H-9 の value 不一致 = VALUE_MISMATCH」と読み替える**(Core は変えない) |
| 田中が担当 | VALUE_MISMATCH または POINTER_NOT_FOUND | (a) `utterances[0]` を引いて value を「田中」と書く → H-9 value 不一致。(b) 存在しない `utterances[7]` を引く → `resolvePacketPath`「facts.utterances.7 は列の外(長さ 3)」(231 行)→ **POINTER_NOT_FOUND に相当**。(c) 語彙: 「田中」は定義の表に無い → **H-10 は落とさない**(hypothesis.ts の H-10 コメント「名前の表に無い名前は文字として一致しないので落ちない」= 既知の穴) | H-9 の 2 つの理由(値・場所) | **登録簿に無い固有名詞は検出できない**。`check_answer.NAME_LIKE_RE`(接尾辞で名前らしさを見る)は将棋の語で、汎用の代替は無い |
| 契約成功の可能性が高い | UNVERIFIABLE | (a) `kind: hypothesis` にすると H-4 が `prediction{metric,comparator,value,window,writtenAt}` を要求し、H-2 が `metric` の `obs.*` を登録簿に求める → Meeting の登録簿が要る。H-5 は「可能性があります」の形を要求し**「可能性が高い」は落ちる**(578 行)。(b) `kind: unanswerable` または `needed_observation` にすると H-4 は飛ぶ(306・534 行)、`answers[].status = "unanswerable"` + `neededObservation`(answerSelection S-8、数を含まない)→ **現行の語 3 つ(`unanswerable`・`needed_observation`・`partial`)で表現できる**(計画 §6.4 と同じ結論) | H-4・H-5・S-8・`STATUSES_NEEDING_OBSERVATION` | 新しい語を作らない。ただし「席は `unanswerable` を選ばず `partial` に逃げる」(記憶)ので**止めるのは検証器** |

### 6.3 Meeting が借りられるもの(表)

| Core の部分 | 再利用 | 条件 |
|---|---|---|
| `eventSchema`・`prng`・`env`・`tokenBudget`・`schemaAdapters`・`llmClient` | **そのまま** | ― |
| `canonicalJson`・`packetIdOf`・`packetIdProblems`・`aggregateFormProblems` | **そのまま** | ― |
| `resolvePacketPath`・`packetRefPathProblems` | **I-6 の後** | 列の集合 `["utterances","numbers","dates","entities"]` を注入 |
| `selectRows/countOf/sumOf/recountProblems` | **A-5 の後**(集計を使うなら) | 所属鍵 `meetingId`、重複排除の単位 `meetings` |
| H-1 | そのまま(日付と「万」の扱いに注意) | 観測の値は数値で置く |
| H-2 | そのまま | Meeting の登録簿(Markdown でも Set でも) |
| H-3・H-4・H-6・H-7・H-8 | **そのまま** | ― |
| H-5 | そのまま | 日本語の読みの形を受け入れる(H-1 の保留) |
| H-9 | **I-6 の後** | ― |
| H-10・H-11 | そのまま(**欄名 `facts.recognition` を借りる**)/ A-6 の後は自前の欄名 | 定義に `reviewStatus` |
| `seatOutput`・`integration`・`seatRun`・`exitSelect`・`answerSelection` の機構 | そのまま(除外一覧・sha 表・本数は値を変える) | 契約の `boards`・`p1` は Meeting では空か別契約 |
| `exit_verification` の `sections_of`・`number_claims`・`check_ans_tags`・`check_agg_tags` | そのまま(規則を渡す) | `verify` の固定順は冊子なので**使わず個別に呼ぶ** |
| `scan_numbers` | **I-7 の後** | 今は `check_answer.py`(将棋側)にある |
| `compare_render`・`check_fonts_embedded`・`check_delivery` の機構 | そのまま | ― |
| **契約 schema 5 本**(packet・request・hypothesis・answer-selection・seat-output/integration) | **再利用できない(そのままでは)** | `facts` の列・`lane`・`subject.gamesCount`・`origin.kifu`・`requestedScope.games/timeLimitSec`・`boards` が将棋/冊子。**封筒だけの版が要る = 人間の承認** |

**判定**: 現行の Core 設計で、Meeting の 4 Claim のうち **GROUNDED・VALUE_MISMATCH・POINTER_NOT_FOUND は I-6(文法の注入)が入れば H-9 の 3 つの結果(一致・値が違う・場所が無い)で表現できる**。**UNVERIFIABLE は今の語彙で表現できる**。**表現できないのは「登録簿に無い固有名詞(田中)の検出」**で、これは現行 Core にも無い(将棋側は接尾辞の規則で代用している)。

---

## 7. audit-platform 切り出し境界(成果物 D・F・G)

### 7.1 Shogi Adapter 境界(成果物 D)― 将棋側に残るもの

`scripts/playtest/lib/` の §2.1.2 の 30 本(`observationFacts`・`observationMaterials`・`reportData`・`timeSearch` …)、CLI `observationPacket.ts`(`dump_booklet_numbers.py` を spawn)・`seatInput.ts`(描画)・`exitSelect.ts`(CLI)・`deliver.ts`/`pipeline.ts`(段表・並行実行)・`fillTexts*`、`report-pdf/` の `SHOGI_PY_MODULES` 27 本(`exit_gate.py` を含む)、`data/`、`apps/`、`invariants/`、`docs/OBSERVATION_ITEMS.md`、`schemas/obs-registry.extra-ids.json`、`docs/LLM_SEATS_*INSTRUCTION*.md`、`schemas/failure-event.*`・`diagnosis-*`。
加えて §3.1 の A-1〜A-14 が**移った後の受け皿**(今は Core 候補の中に在る)。

### 7.2 audit-platform 初期ディレクトリ案(成果物 F。計画 §6.3 を現状で読み直した。**作らない**)

```
audit-platform/
├── core/ts/
│   ├── schema/        eventSchema
│   ├── packet/        observationPacket(封・入口・解決・形)/ packetRef(文法 factory)/ observationAggregates(Population・recount。鍵名・単位は spec)
│   ├── claims/        hypothesis(H-1〜H-11。registry・bannedWords・vocabulary・schema は opts)
│   ├── seats/         seatOutput / integration / seatRun / llmClient / schemaAdapters / tokenBudget / env / prng(除外一覧・sha 表は spec)
│   ├── approval/      exitSelect / answerSelection(本数・menuIds は spec)
│   ├── provenance/    observationProvenance / gitState(prefixes は引数)
│   └── proof/         seatInput の numberInclusion・sealOf・normalizeLastKey(**切り出しが要る**)
├── core/py/
│   ├── text_claims.py        ← I-7(check_answer の走査層: scan_numbers・印の正規表現・strip_marks・check_line_numbers/banned)
│   ├── exit_verification.py  ← 既存(GateRules の冊子欄の扱いは H-4 の保留)
│   ├── compare_render.py / check_fonts_embedded.py
│   └── delivery_hygiene.py   ← check_delivery の機構(語は引数)
├── core/schemas/      **封筒だけの新しい版**(packet 封筒・hypothesis 骨格・seat-output・integration・answer-selection の骨格)。**今は 1 本も無い**
├── adapters/shogi/    §7.1 のうち Core を呼ぶ側の spec(shogiSpec.ts / shogi_spec.py。**今は無い** = 計画 Phase 3)
├── adapters/meeting/  §6 の最小要件だけ(**作らない**)
├── governance/        banned_words.json(既存)・obs registry・approved action table・instruction sha 表・thresholds・review statuses・section roles(**今は code 定数のものが多い**)
└── tests/
    ├── core/          §7.4 の「跨がない」試験
    ├── boundary/      core_boundary.test.ts(**両側を歩くので跨ぐ**)
    └── golden/shogi/  c5_expectation.json + goldenMasterCheck.ts(**deliver.ts と out/ に依存 = 跨ぐ**)
```

### 7.3 Governance / Policy data として外に置く候補

| 今の場所 | 中身 | 既にデータか |
|---|---|---|
| `data/governance/banned_words.json` | 禁止語(空) | **データ**(T-3) |
| `schemas/obs-registry.extra-ids.json` | 登録簿の補い 30 列 | **データ**(T-3) |
| `docs/OBSERVATION_ITEMS.md` §1 | 登録簿 | **文書を実行時に読む** |
| `lib/answerMenu.ts` の `ANSWER_MENU`(M1〜M9) | 承認済み行動表 | code 定数 |
| `lib/seatRun.ts` 40〜46 | 指示文 sha 表 | code 定数 |
| `lib/observationFacts.ts` 43・`reportData.ts` の `TIME_VALUES`・`exit_groups.py` 81 | 閾値 | code 定数(packet の `provenance.thresholds` に写る) |
| `lib/hypothesis.ts` 936 | `APPROVED_REVIEW_STATUSES` | code 定数 |
| `check_structure.py` 54〜62・174〜192、`answerSelection.ts` 25〜26 | 節の役割・ページ上限・本数 | code 定数 |
| `check_delivery.py` 31・55 | 常に伏せる語 | code 定数 |
| `seatOutput.ts` 19・`integration.ts` 31 | 席に渡さない入力の名 | code 定数 |

### 7.4 現時点で切り出してよいもの / まだ切り出してはいけないもの(成果物 G)

| 判定 | 対象 | 理由 |
|---|---|---|
| **切り出してよい(単独で成立)** | `eventSchema` `prng` `env` `tokenBudget` `schemaAdapters` `llmClient`、`compare_render.py` `check_fonts_embedded.py`(試験なしのまま) | 依存 0・意味 0。試験(`*.test.ts`)も将棋 module・`out/` を読まない(§7.5) |
| **切り出してよいが引数化が先** | `gitState`(`COUNTED_PREFIXES`)、`observationProvenance`(`kind` 文字列は呼ぶ側へ) | 小さい。ただし `gitState.test.ts` が `apps/server` の字を 4 か所持つ(中身は未読) |
| **まだ切り出してはいけない** | `observationAggregates`(I-4 + A-5 未)、`observationPacket`(I-5 未)、`packetRef`(I-6 未)、`check_answer.py`(I-7 未。4 本の Python module のハブ)、`hypothesis`(A-6 未・既定 path が repo 配置・`hypothesis.test.ts` が `timeSearch.SEARCH_COLUMNS` を import)、`seatOutput`/`integration`(`origin.kifu`・除外一覧・登録簿 path)、`seatRun`(sha 表)、`exitSelect`/`answerSelection`(盤・本数・`answerSelection.test.ts` が `ANSWER_MENU` を import)、`exit_verification.py`(試験が `exit_gate_test.py` の中・`scan_numbers` を将棋側から借りる)、`check_structure.py`/`check_delivery.py`/`exit_index.py`(定数の分離が未設計)、`schemaVersions.ts`(混在)、**契約 schema 全部**(将棋の enum を持つ。封筒だけの版が無い)、`fillTexts*`(別束)、Golden Master(`out/` と `deliver.ts` に結合) | 上の各節 |

### 7.5 repo 分割後に試験が跨ぐ箇所(実測: import と `out/` 参照の数)

| 試験 | 跨ぎ方 | 根拠 |
|---|---|---|
| `lib/core_boundary.test.ts` | Core と将棋側の**両方のファイル一覧**を持ち(26〜48 行)、`apps/server`・`scripts/playtest/tsconfig.json` を解決する | 設計上「境界を歩く」試験 |
| `goldenMasterCheck.ts` + `docs/golden_master/c5_expectation.json` | `lib/deliver.ts`(将棋)から門の引数を組む(28〜38 行)、Python の門 3 本を spawn、`out/c5/...` の path を `inputs` に持つ、`docs/OBSERVATION_ITEMS.md` を読む | goldenMasterCheck 19〜30・136〜160 行 |
| `lib/hypothesis.test.ts` | `import { SEARCH_COLUMNS } from "./timeSearch.js"`(23 行。パリティ試験)、`out/` 2 か所・`__fixtures__` 3 か所 | grep |
| `lib/observationAggregates.test.ts` | `import type { FactsMaterials } from "./observationFacts.js"`・`DEFAULT_SOURCES from "./observationMaterials.js"`(17〜18 行) | grep |
| `lib/answerSelection.test.ts` | `import { ANSWER_MENU } from "./answerMenu.js"`(11 行) | grep |
| `lib/exitSelect.test.ts` | `out/` の字 15 か所 | grep(読んでいるか、文字列か は未確認) |
| `lib/observationPacket.test.ts` 5・`lib/seatRun.test.ts` 4・`lib/seatInput.test.ts` 5・`lib/answerSelection.test.ts` 1 | `out/` の字 | grep(同上。記憶 `test-must-not-read-ignored-material`) |
| `lib/gitState.test.ts` | `shogiops\|apps/server` の字 4 か所 | grep(中身は未読) |
| `lib/schemaAdapters.test.ts` | `validateIntegrationLlm`・`validateSeatOutputLlm` を import(Core 内。跨がない) | grep |
| `report-pdf/exit_gate_test.py` | `exit_verification` の試験 e1〜e6(1280〜1373 行)が Adapter の試験ファイルの中。`check_answer`・`check_structure`・`exit_candidates`・`exit_index` を import | grep |
| `report-pdf/check_answer_test.py`・`check_structure_test.py`・`exit_fill_test.py` | `out/` の字を持つ | grep(読んでいるかは未確認) |
| `lib/reportPdfPythonTests.test.ts`(**`scripts/playtest/` 直下ではなく `lib/`**) | `readdirSync` で `report-pdf/*_test.py` を**全部**回し、名前の集合を `__snapshots__` に固定(床 10 本)。Python を 2 repo に割ると**スナップショットが赤**(= 人が `-u` で承認) | 10・23・30・39 行 |
| `scripts/playtest/tsconfig.json` | `include: [".", "../../apps/server/src"]` ― Core の型検査がアプリ本体に依存 | 全文 |
| `scripts/typecheck-scripts.mjs` | 2 つの tsconfig を必ず両方走らせる門 | 全文 |
| 門 2 本の運用(`npx vitest run --root scripts/playtest`・`npm run typecheck:scripts`) | RUNBOOK が「門は 2 本」を前提(計画 §6.1 の 3) | ― |

---

## 8. audit-platform 作成 GO / NO-GO

### 判定: **NO-GO**(新 repo は今は作らない。同一 repo 内で意味境界を閉じる作業が先)

| # | 根拠 | どこで確かめたか |
|---|---|---|
| 1 | **意味境界の 4 本(I-4・I-5・I-6・I-7)が未着手**。計画 §8 の T-4/T-5 の中身と実際のコミットが違う(T-4 = I-3 のみ、T-5 = I-8 + 型 2 本) | `git log --stat` 4 コミット、`core_boundary.test.ts` 60〜61 行 |
| 2 | 計画に無い意味依存が 3 つ見つかった(所属鍵 `gameId`/単位 `games` A-5、語彙の場所 A-6、sha 表 A-9) | §2.6 |
| 3 | **契約 schema 5 本すべてが将棋/冊子の enum・必須欄を持つ**。Core 用の封筒だけの版は 1 本も無く、版上げは人間の承認 | §2.2 の json.load |
| 4 | **Python は `check_answer.py` がハブ**(exit_verification・exit_gate・exit_fill・check_structure・check_delivery が `scan_numbers`・印の正規表現・`BANNED_WORDS` を借りる)。I-7 なしで割ると Core 側の Python が将棋側を import する | §2.5・§7.5 |
| 5 | **試験が跨ぐ**(§7.5 に 14 件)。特に `reportPdfPythonTests` のスナップショット・`hypothesis.test.ts` のパリティ・`goldenMasterCheck` の `deliver.ts` 依存 | §7.5 |
| 6 | Golden Master の正本の置き場(`out/` 未追跡)が未決(計画 §5 冒頭の人間判断) | `c5_expectation.json` の `inputs` |
| 7 | 計画書 §6.1・§7 の順序(「同一 repo で境界を引き、Phase 4 回帰 → Phase 6 監査の GO の後に移動・新 repo」)に対し、Phase 2 の途中 | 計画書 |
| 8 | 「同値」の証明は T-5 で関数レベル Golden(972 呼び出し)まで要した。I-4〜I-7 は同じ強さの測り方がまだ無い | 記憶 `audit-core-t5-done`、人間の原則 2 |

### GO に変わる条件(すべて満たしたら再判定)

1. I-6(文法 factory)→ I-5(packet 検査の spec 化)→ I-4(表・関係・鍵名/単位の分離)→ I-7(走査層 `text_claims.py`)を**1 本 1 コミット**で入れ、各回で (a) 門 2 本緑 (b) G-9 バイト一致 (c) **関数レベル Golden**(T-5 と同じ方法)で同値 (d) 両向きの変異が赤。
2. A-6・A-9・A-10・A-11 の注入口を足す(値は現行のまま)。
3. Phase 3: 将棋側の spec を 1 か所(`shogiSpec.ts`・`shogi_spec.py`)に束ね、CLI がそれを渡す。
4. Phase 5: §6 の合成 Meeting packet を**schema 検査を除いて** H-1・H-2・H-8・H-9・H-10 に通し、動かない検査 = 0。
5. 人間の決定 3 つ: (a) 封筒だけの契約の版を作るか、(b) Golden Master の正本の置き場、(c) Core を日本語前提にするか(§3.3 H-1)。
6. 跨ぐ試験(§7.5)の置き場を決め、`reportPdfPythonTests` のスナップショット更新を人が承認する。

### 今すぐできること(新 repo を作らずに)

- `tests/boundary` 相当として、**意味境界の走査**(Core 候補の文字列定数に将棋の列名・`gameId`・`付録`・`盤` が残っていないか)を試験に足す案 ― ただし「字面の試験は自分の説明文に当たる」(記憶)ので、AST の文字列定数(docstring 除外)で見る。**本調査では実装していない。**
- 単独で成立する 8 本(§7.4 の 1 行目)は、ファイルを動かさずに「Core 単体」の一覧として文書に固定してよい(動きは変わらない)。

---

## 9. この調査が見ていないもの(正直に)

- 試験の**中身**(`out/` の字が path として読まれているか、文字列として比べているか)は grep の件数だけで、読んでいない。
- `gitState.test.ts` の `apps/server` 4 か所の中身。
- `check_structure.py`・`exit_index.py`・`check_delivery.py` の関数の中身は def 一覧と定数だけ(機構/定数の分け方は未設計)。
- `deliver.ts` の 24 段の表の中身(段名の一覧は取ったが、段ごとの引数の組み立ては読んでいない)。
- `runSeats.ts`・`instructionExamples.ts` の中身。
- 門・試験・typecheck は**回していない**(回すと `out/` に書く可能性があるため。T-5 時点で緑であることは記憶とコミットメッセージに拠る)。
