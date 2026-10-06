# Audit Core 抽出計画 ― 棚卸し・依存関係監査・移行設計(2026-10-05、セッション「Audit Core|移行設計」)

**この文書は調査と設計だけを書く。コード・データ・試験は 1 文字も変えていない。**
後続の実装担当がそのまま使えるように、判断ごとに根拠(ファイル・行・import・検索結果)を添える。
確認できなかったものは「未確認」「判定保留」「推測」と明記する。一般論で「おそらく Core」とは書かない。

---

# 1. 調査基準情報

| 項目 | 値 |
|---|---|
| **Base Commit Hash** | `783ae6e4240b803da28f8f78dc1367bf374ffba9` |
| Base Commit の日時・題 | 2026-10-05 23:12:41 +0900 `docs(AUTOMATION_STATUS): 人間の決定 ― 装置の修正後に最後の 1 回を回す GO(条件 13 件)。司令塔の読み替え(条件 5・11)` |
| ブランチ | `feature/phase7-recognition-spec` |
| 調査開始 | 2026-10-05 23:28:12 +0900(`git rev-parse HEAD` を実行した時刻) |
| 調査終了(本文書の書き出し直前) | 2026-10-05 23:38:34 +0900 |
| 調査対象 | リポジトリ全体。重点は `scripts/playtest/report-pdf/*.py`(Python 18 本 + 試験 18 本、計 25,734 行)と `scripts/playtest/lib/*.ts`(非試験 90 本前後)・`scripts/playtest/schemas/*.json`(27 本)・`apps/`・`data/`・`spike/`・`prototypes/`・`docs/` |
| 調査上の制約 | Read-Only(読み取り・静的解析・git 情報・grep のみ)。成果物はこの 1 ファイルだけ。実行したのは `git rev-parse` / `git status` / `git log` / `git ls-files` / `git diff --stat` と、JSON schema の `json.load` による**読み取り**だけ。試験・typecheck・道具は**回していない**(回すと `out/` 等に書く可能性があるため) |
| **HEAD 変化の有無** | **無し。** 調査開始・中間(23:3x)・終了の 3 回とも `783ae6e…` |
| **作業ツリー変化の有無** | **有り(別セッションが並行して作業中)。** 下表 |

### 1.1 作業ツリーの変化(調査結果には混ぜていない)

| 時点 | `git status --short` |
|---|---|
| 開始(23:28) | ` M scripts/playtest/fillTexts.ts` / ` M scripts/playtest/lib/fillTexts.test.ts` / ` M scripts/playtest/lib/fillTexts.ts` / ` M scripts/playtest/report-pdf/exit_fill.py` / ` M scripts/playtest/report-pdf/exit_fill_test.py`(`git diff --stat`: 5 files, +221 −35) |
| 中間(23:3x) | 上の 5 本 + `?? scripts/playtest/lib/fillTextsCli.test.ts`(未追跡が 1 本増えた) |
| 終了(23:38) | 上の 6 本 + ` M docs/PHASES.md` / ` M docs/PLAN_FILL_TEXTS_2026-10-05.md` / ` M scripts/playtest/report-pdf/README.md` |
| 本文書の書き出し後の確認 | さらに ` M docs/LANE_AUTOMATION_LOG_2026-09.md` が増えた(本文書は読んでいない)。HEAD は不変 |

**扱い**: 本文書の分類・行番号は作業ツリーのファイルを読んだものである。上の変更中ファイルのうち本文書が中身を引いたのは `exit_fill.py`(冒頭コメント 1〜20 行)と `lib/fillTexts.ts`(冒頭コメントと export 一覧)だけで、どちらも**冒頭の説明部分**であり diff の影響は受けにくいが、**厳密には Base Commit の内容を保証しない**(`git show 783ae6e:<path>` で読み直していない)。それ以外に深く読んだファイル(`observationPacket.ts`・`packetRef.ts`・`hypothesis.ts`・`observationAggregates.ts`・`check_answer.py`・`exit_gate.py`・`compare_render.py`・`check_structure.py` 等)は変更一覧に無いので Base Commit と同一である。
**言い換えの束(`fillTexts*`・`exit_fill.py`)は別セッションが進行中の領域であり、§7 の移行計画ではその束が落ち着くまで触らない前提にする。**

---

# 2. 全体ファイル分類マトリクス

記号: **[A]** Audit Core 候補 / **[A′]** Core 候補だが将棋依存あり(切り分けが要る) / **[B]** Shogi Adapter 候補 / **[C]** Golden Master・回帰基盤 / **[D]** 廃止・保留候補 / **[X]** 判定保留。
確度: **高** = import と中身を読んで確認 / **中** = 冒頭コメント・export 一覧・grep で確認 / **低** = 一覧と名前だけ。

## 2.1 `scripts/playtest/lib/`(TypeScript、非試験)

将棋ライブラリ(`shogiops`)または `apps/server/src` を**直接 import しない**モジュールは 51 本(`comm -23` で確認、§3.1 に一覧)。残りは直接 import する(§2.1.2)。

### 2.1.1 直接 import が無い 51 本の分類

| パス(`lib/`) | 分類 | 根拠 | 将棋依存 | 確度 |
|---|---|---|---|---|
| `packetRef.ts`(45 行) | **[A′]** | packet 内の場所の文法 1 か所。`observationPacket*.ts` を import しない(同ファイル 5 行目の宣言どおり、import 0 本) | **文法に将棋の列名が焼き込み**: `PACKET_FACTS_COLUMNS = ["games","moves","engine","time","branches","collapse","recognition"]`(15 行)、`FACTS_REF_RE` が `recognition\.(?:rows\|definitions)` を名指し(24 行)。列の集合を adapter から注入すれば Core | 高 |
| `eventSchema.ts` | **[A]** | 外部ライブラリ無しの JSON Schema 部分集合検証器(type・enum・pattern・min/max・properties・required・additionalProperties・items・oneOf・const。`$ref`・`anyOf`・`maxItems` は例外)。import は無し | 無し | 高 |
| `prng.ts`(32 行) | **[A]** | xorshift32。コメント「将棋の判断は一切行わない、汎用の乱数ユーティリティ」。import 無し | 無し | 高 |
| `env.ts` | **[A]** | `.env` 読み・`redactSecrets`。鍵名の表 `ENV_NAMES`(OPENAI/GEMINI/ANTHROPIC・席のモデル名) | 無し(席名 gpt/gemini/claude は LLM 側の語彙で将棋ではない) | 高 |
| `tokenBudget.ts`(70 行) | **[A]** | トークン見積り・単価・上限判定。import 無し | 無し | 高 |
| `schemaAdapters.ts`(191 行) | **[A]** | canonical JSON Schema → OpenAI strict / Gemini / Anthropic の形へ変換。import 無し | 無し | 高 |
| `llmClient.ts`(259 行) | **[A]** | 3 社への構造化出力呼び出し(`callStructured`・`parseStructuredResponse`)。import は `./env.js` のみ | 無し | 高 |
| `observationPacket.ts`(244 行) | **[A′]** | packet の schema 読み・検証入口 `observationPacketProblems`・`canonicalJson`・`packetIdOf`(封)・`resolvePacketPath`(参照の解決)。import: `eventSchema`・`observationAggregates`・`packetRef` | (1) `timeLimitProblems`/`commonTimeLimitSec`(84〜103 行)が `facts.games[].timeLimitSec` を名指し、(2) `requestAgreementProblems`(106 行)が `requestedScope.games/timeLimitSec` を名指し、(3) `observationPacketProblems` が `aggregateAgreementProblems`(将棋固有の整合関係。下記)を呼ぶ(126〜135 行)。**検証入口・封・参照解決は汎用、3 つの検査は adapter 側** | 高 |
| `observationAggregates.ts`(829 行) | **[A′]** | **汎用部分**: `Population`(from/where/unit)・`Condition`(op 8 種)・`selectRows`/`countOf`/`sumOf`(1〜223 行)・`recountProblems`/`recountRowProblems`(769〜829 行、集計を facts から数え直す)。**将棋部分**: `ROW_DEFINITIONS`(224〜394 行。`sideMatch.attack` 等 26 行の定義)・`aggregateAgreementProblems`(460 行〜。「側が逆の分子 = 攻め→自玉側 + 自玉側→攻め」等の関係)・`Booklet*` 型(555〜)。import は `type FactsMaterials`(**型のみ**。実行時依存無し) | 行の定義と整合関係は将棋。数え直しの機構は汎用 | 高 |
| `observationProvenance.ts`(305 行) | **[A′]** | `sourcesOf`/`provenanceOf`/`traceProblems`(出どころ・入力の sha256・閾値の表)。**import に `AHEAD_CP`(`./observationFacts.js`)と `TIME_VALUES`(`./reportData.js`)**(16〜17 行)→ **実行時に将棋側を読み込む** | 閾値の表 `toolThresholds()`(31〜43 行)が `ahead_cp`(出どころ `exit_groups.py AHEAD_CP`)を直書き。`sourcesOf` の `kind` 文字列に「対局後診断の報告の材料」(81 行) | 高 |
| `hypothesis.ts`(960 行) | **[A′]** | 契約 hypothesis の schema 読み + 機械検査 H-1〜H-11 を「全部回して全部返す」`validateHypothesisLine`。H-1 数の実在(263〜)・H-2 ID 登録(368〜)・H-3 反証の記録・H-4 予測は数で・H-5 禁止語と断定形・H-6 盲検・H-7 昇格は human_reviewed 以上・H-8 人名/絶対パス(574〜609、`/`・`@`・`~` を見る)・H-9 packetRef の実在と値(628〜)・H-10 語彙(700〜)・H-11 名前を顧客に出せる段か | **4 本の将棋依存**: (1) `import { SEARCH_COLUMNS } from "./timeSearch.js"`(30 行。`loadObsRegistry` 173 行で使用)→ `timeSearch`→`reportData`→`apps/server`+`shogiops` を**実行時に引く**。(2) `CHECK_ANSWER_PY = new URL("../report-pdf/check_answer.py")`(110 行)を正規表現 `BANNED_WORDS_RE` で**ソースとして読む**(130〜)。(3) `knowledge.kind: "shogi" \| "discovered" \| "coaching"`(77 行)・`origin.kifu`(80 行・763 行)。(4) `loadObsRegistry` が `docs/OBSERVATION_ITEMS.md` の §1 の表を読む(155〜)。**検査の骨格(数の実在・ID 登録・反証・予測・禁止語・盲検・昇格・PII・参照の実在・語彙)は汎用** | 高 |
| `seatOutput.ts`(335 行) | **[A′]** | 席の出力の封筒(seat-output.v0.1)の検証・補完 `completeSeatOutput`・`seatOutputProblems`。import: eventSchema・hypothesis・packetRef・seatInput | `SEAT_EXCLUDED_INPUTS = ["answer_menu.json","exit_candidates.json","9_本編.md"]`(19 行。将棋の冊子のファイル名)、`origin: { kifu: … }`(166 行)。hypothesis 経由で上の依存を継承 | 高 |
| `integration.ts`(485 行) | **[A′]** | 整理役(LLM)の入出力の契約・席の順序のシャッフル(`seatPermutation`、PRNG)・`INTEGRATOR_EXCLUDED_INPUTS`・`SEAT_NAME_RE`・`SEAT_COUNT_REFERENCE_RE`(一致を証拠にしない)・`integrationProblems` | `origin: { kifu: … }`(310 行)。`INTEGRATOR_EXCLUDED_INPUTS` に冊子のファイル名(31 行)。hypothesis 経由の継承 | 高 |
| `seatRun.ts`(595 行) | **[A′]** | 席と整理役の実行・再試行(形 2 回・長さ 1 回)・費用上限・`FIXED_INSTRUCTION_SHA256`(40〜46 行。指示文 4 本の sha を固定)・`AbsentReason` 9 種 | 指示文は将棋の依頼文(`docs/LLM_SEATS_INSTRUCTION_v1.2…md` 冒頭「将棋の対局後診断サービスの内部で使う」)。**実行機構は汎用、指示文とその sha は adapter** | 中 |
| `seatInput.ts`(482 行) | **[B]**(Core の縁) | packet + request + 指示文 → 席に渡す md(`renderSeatInput`)。`numberInclusionProblems`(154 行。数の包含の証拠)・封印語 `sealOf`・`normalizeLastKey` は汎用 | **読み方の案内 `READING_GUIDE`(100〜110 行)が USI・centipawn・先手後手・戦型の説明を実行時文字列として持つ**。表の列名(404〜450 行)が packet の将棋の欄を名指し。→ **描画は adapter、封印語・数の包含検査は Core へ** | 高 |
| `exitSelect.ts`(224 行) | **[A′]** | ⑤ の候補の一覧 `buildSelectionDraft`・`adoptedBy` が常に `null`(機械が採用しない)・`selectionGateProblems`。import: hypothesis・packetRef | `isBoardRef`(62 行。盤 = 将棋の器の概念)。それ以外は id の並べ替え | 中 |
| `answerSelection.ts` | **[A′]** | 契約 answer-selection.v0.1 の入口。`ADOPTED_STATUSES = ["answered","partial","unanswerable"]`・`STATUSES_NEEDING_OBSERVATION` | `P1_COUNT = 3`・`BOARD_COUNT = 2`(25〜26 行。器の形の定数 = 将棋の冊子の約束)。状態機械は汎用 | 中 |
| `fillTexts.ts`(378 行、**変更中**) | **[D]/[X]** | 冒頭「1 回限りの境界測定実験」「出口 ⑥ の照合 F-5 を通った文だけ」。別セッションが進行中 | `RULES_LINES`・`TermLine` は冊子の語 | 中 |
| `gitState.ts`(236 行) | **[A]**(名前だけ将棋) | `git rev-parse HEAD`・`git status --porcelain` を 1 か所で読む。import は `../invariants/types.js`(**型のみ** `MetaLine`) | `renderDirtyWarnings` の引数名 `kifuId`(208〜231 行)。欄名だけ | 高 |
| `schemaVersions.ts`(54 行) | **[X]** | 契約の「今の版」と既知の版の並び(failure-event・diagnosis-moment・gate・condition)。定数だけ | 版の対象が将棋の契約。**「版の並びを 1 か所に持つ」規約は Core、値は adapter**。どこに置くかは契約の所属が決まってから | 高 |
| `deliver.ts`(1658 行) | **[X]** | 段の一覧 `DELIVER_STAGES`(58 行)・段ごとの `action: run/skip/gate/fail`・`stagesFrom`・「済み」判定・`--out` の安全装置。冒頭「子プロセスの起動・fs は呼び出し側が注入」 | **段の表(1351〜1649 行、24 種の段名: pipeline-gate … exit-send)は将棋の冊子の工程そのもの**。段の実行機構(run/skip/gate、--from、済み判定)は汎用の state machine 候補 | 高 |
| `pipeline.ts`(1227 行) | **[X]** | 局の一覧・段の済み判定・上限つき並行実行 `runWithLimit`・`--dry-run`。`spawnProcess` は 77 行(deliver と同型) | 入力が `.kif` と先後(`-sente/-gote`)。並行実行と済み判定は汎用 | 中 |
| `condition.ts`(650 行) | **[X]** | 条件式の定義ファイルを `await import(pathToFileURL(...))`(296 行)で**動的に読み込み**、sha256 を取る `loadCondition`。import: diagnosisMoment・failureEvent・kifuImport(将棋) | 定義の中身は将棋。**「定義を module として読み込み sha で固定する」機構**は plugin 機構として Core 候補 | 中 |
| `gate.ts`・`gateOutput.ts`・`conditionReport.ts` | **[B]** | 条件式ごとの崩れ率比較と Gate 記録(STEP D4)。`gateOutput` は `../invariants/types.js`・`condition`・`eventSchema` を import | 評価値・崩れ = 将棋 | 中 |
| `instructionExamples.ts` | **[X]** | 指示文に書いた packet の場所の例を実物に当てて確かめる(書き方の誤りは止める・材料の薄さは警告) | 指示文が将棋。機構は「例を機械で当てる」汎用 | 中 |
| `answerMenu.ts`・`findingTexts.ts`・`directAnswers.ts`・`diagnosisMoment.ts`・`diagnosisReport.ts`・`diagnosisTotals.ts`・`failureEventSchema.ts`・`denominators.ts`・`adviceSource.ts`・`calibrationBaseline.ts`・`baselineTable.ts`・`obsExtra.ts`・`obsSnapshot.ts`・`scanCompare.ts`・`screenDiagnosis.ts`・`standing.ts`・`timeSearch.ts`・`type.ts`・`userSide.ts`・`usiRotation.ts`・`whatifBaseline.ts`・`replayPlan.ts`・`reportTemplates.ts` | **[B]** | 直接 import は無いが、`timeSearch`→`reportData`(将棋)・`usiRotation`(USI)・`answerMenu`(行動の表 M1〜M9)・`findingTexts`(冊子の固定文)など、中身が将棋の計測・文言 | 有り(名前・中身) | 中(名前と冒頭のみ) |
| `observationMaterials.ts` | **[B]** | `observationFacts` を import(材料の読み込み) | 有り | 高 |

### 2.1.2 `shogiops` または `apps/server/src` を直接 import する非試験モジュール(全部 **[B]**、確度 高)

`beginnerProfile` `engineReference` `counterfactual` `checkBaseline` `failureEvent` `failureEventFixtures` `fixedSearchEngine` `intentStatement` `finalPosition` `kingSurroundings` `moveFacts` `multiPvSurvey` `obsGeo` `observationFacts` `opponentEngine` `kifuImport` `read` `reportData` `rescreen` `positionFacts` `players` `recognitionMeasure` `searchPvStats` `recorder` `sideAlignment` `timeCause` `screenCalibration` `timeFeatures` `whatifReport` `whatif`(grep `from "(shogiops|.*apps/server)"` の結果)。
`observationFacts.ts` は packet の `facts` 7 欄を**既存の将棋の出力から組む**(冒頭コメント)ので、**Shogi Adapter の中核**(packet の生産者)。

## 2.2 `scripts/playtest/*.ts`(CLI、非試験)

| パス | 分類 | 根拠 | 確度 |
|---|---|---|---|
| `hypothesisCheck.ts`(87 行)・`seatOutputCheck.ts`(41 行)・`integrationCheck.ts`(39 行) | **[A′]** | lib の検証器を呼ぶ薄い CLI | 中 |
| `runSeats.ts`(249 行) | **[A′]** | 3 席 + 整理役の実行 CLI。`git rev-parse HEAD` を読む(47 行) | 中 |
| `observationPacket.ts`(203 行) | **[B]** | packet を組む道具。**`dump_booklet_numbers.py` を `spawnSync` で呼び**(61〜64 行)、冊子の python の数と突き合わせる | 高 |
| `seatInput.ts`・`exitSelect.ts`・`fillTexts.ts`(変更中) | 上の lib に同じ | | 中 |
| `deliver.ts`(530 行)・`pipeline.ts`(201 行) | **[X]** | 段の実行。`spawn` で `npx tsx` と `python3 -X utf8`(`lib/deliver.ts` 132〜134 行) | 高 |
| `replay.ts` `explore.ts` `check.ts` `compare.ts` `diagnose.ts` `gate.ts` `report.ts` `rescreen.ts` `scan-compare.ts` `screen-calibrate.ts` `measure-twice.ts` `multipv-survey.ts` `kifu-import-check.ts` `kifu-times.ts` `read.ts` `type.ts` `whatif.ts` `whatifReport.ts` `timeCause.ts` `timeSearch.ts` `directAnswers.ts` `finalPositions.ts` `answerMenu.ts` `baselineTable.ts` `reportData.ts` `obsGeo.ts` `obsExtra.ts` `obsSnapshot.ts` `recognitionMeasure.ts` `figShapeCandidates.ts` | **[B]** | 対局ハーネス・エンジン再生・分かれ道・時間・認識など将棋の計測の CLI(冒頭 1 行で確認) | 中 |

## 2.3 `scripts/playtest/report-pdf/*.py`(Python)

import 図(§3.3)から、**`check_answer.py` が中心のハブ**で、`exit_gate`・`exit_fill`・`exit_body`・`exit_candidates`・`check_structure`・`check_delivery`・`answer_facts`・`render_answer`・`render_direct`・`fig1`・`render_time_cause`・`exit_groups`・`exit_cover`・`exit_render`・`dump_booklet_numbers` が import する。

| パス(行数) | 分類 | 根拠 | 将棋依存 | 確度 |
|---|---|---|---|---|
| `check_answer.py`(1841) | **[A′]**(2 層) | **汎用層**(1554〜1841 行): `strip_dev_section`・`find_fraction_pairs`・`mask_spans`・`scan_numbers`(1589)・`check_line_numbers`・`check_line_banned`・`check_line_action_phrases`・`check_line_names`・`check_menu_tags`・`check_pos_tags`・`check_answer(markdown_text, ctx)`(1795)。「文に出た数は材料に在る数だけ」「印の文法」「禁止語」の走査。**材料層**(268〜1554 行): `build_materials`(1435)が patient/whatif/read/direct/time_cause/time_search/prose を読み、M1〜M9 の成立判定(916〜1206)・`SIDE_JP`(521)・`PIECE_CHARS = "歩香桂銀金角飛玉と杏圭全馬竜"`(139)・`reviewed_shape_names`(1419。`data/{shapes,openings,intents}/*.json` を glob)を持つ | 材料層は全部将棋。汎用層にも `POS_TAG_RE`(`付録N`)・指し手の照合 `check_line_moves`(1644)が混ざる | 高 |
| `exit_gate.py`(742) | **[A′]** | ⑧ の門。`sections_of`・`number_claims`・`check_agg_tags`(606。`<!-- agg: id -->` の数を packet の集計行と照合)・`check_ans_tags`(440。`<!-- ans: qN status -->` が request の問いごとに 1 つ、状態が answer_selection と一致)・`run`(678)。「新しい判定・文言を作らない」と宣言し、数の拾い方は `check_answer.scan_numbers` を使う | `check_p1`/`check_p2`/`check_p3`(数 3 つ・盤 2 つ・行動)の本数と見出しは将棋の冊子の形(`check_structure.SECTIONS` 由来) | 高 |
| `check_structure.py`(934) | **[A′]** | 器の門。`SECTIONS`(54〜62 行、役割 6 つ)・`heading_matches`・`check_pages`・`check_boards`・`check_bundled_index`(索引の鍵と値の突き合わせ)・`check_no_real_name`・`check_one_referent`・`check_question_section`。`fitz`(pymupdf)でページの文字を読む | `SECTIONS`・`TERM_LINES`(115)・`SCOPE_SENTENCE_TEMPLATE`(「エンジンの解析と機械の集計から…」)は将棋の冊子の文。**「節の役割の表 + ページ数 + 索引の整合 + 実名 0」の機構は汎用** | 高 |
| `compare_render.py`(204) | **[A]** | 2 つの PDF を「組版が変わったか」で比べる(ページ数・ページごとの文字 NFKC・`get_drawings()` のベクタ指紋)。`--seal/--verify` で 3 つの数の封。import は `fitz` だけ(関数内) | **無し**(reportlab の PDF 一般に効く) | 高 |
| `check_delivery.py`(155) | **[A′]** | 納品フォルダの `*.pdf`・`*.md` に禁止語・`@`・`/Users/`・`None` が無いか。`from check_answer import BANNED_WORDS`(24 行) | `ALWAYS_FORBIDDEN_WORDS`(「最善手」)・`水匠` の固定語。機構は汎用 | 高 |
| `rename_list.py`(287) | **[A]** | コミットの diff から「改名の一覧」を作る(実物から文を写す前に通す)。拾う行の規則は `S_H1)`・`_TITLE =`・md の `#` | 規則の字面が将棋の組版コードの命名に依存(`S_H1` 等)。機構は汎用 | 中 |
| `exit_index.py`(380) | **[A′]** | 局面・節 → 付録ページの索引を**置いた経路が書く**(`doc.afterFlowable` で `doc.page` を読むだけ・flowable を足さない)。`mark_pos`/`mark_sec` | `COUNTING_NOTES`(170〜)・`COVER_*`(268〜)が顧客向けの将棋の文。「鍵の形は組ごと/組なし」(付録 3)は将棋の納品の事情 | 高 |
| `exit_fill.py`(1184、**変更中**) | **[B]** | ⑥ Slot filling。冒頭「ここで初めて顧客の文ができる」。`sfens_from_env(os.environ)`(1145 行) | 盤・指し手の字(`move_text`)・群の行 | 中 |
| `exit_candidates.py`(1186) | **[B]** | 本編 md の下書き(候補を出すだけ)。`THRESHOLD_SENTENCES`・`findings[].kind` で分岐(714・866 行) | 冊子の候補 = 将棋 | 中 |
| `exit_body.py`(677)・`exit_cover.py`(306)・`exit_render.py`(327)・`exit_groups.py`(310)・`answer_facts.py`(567)・`render_*.py`(6 本)・`fig1.py`・`board_draw.py`・`board_spec.py`・`move_text.py`・`_head.py`・`_util.py`・`_mid.py`・`_app_head.py`・`_app.py`・`_tail.py`・`dump_booklet_numbers.py` | **[B]** | 組版(reportlab)・盤(SFEN → 図)・指し手の字・群の再集計(`AHEAD_CP = 300`、`exit_groups.py` 81 行) | 有り | 高〜中 |
| `check_fonts_embedded.py`(51) | **[A]** | PDF の書体埋め込み確認(`fitz`) | 無し | 中 |
| `render_main.py`・`render_appendix.py`(作業ツリーに在るが **git 未追跡**) | **[D]** | `build.sh` が `_head.py` 等を `cat` で連結して作る生成物(`git ls-files` に無い) | ― | 高 |
| `build.sh` | **[B]** | 上の連結 | ― | 高 |
| `report-pdf/fonts/` | **[D]**(環境依存) | `git ls-files` に無い(README「埋め込める日本語フォントが無ければ `_head.py` が止まる」) | ― | 高 |

## 2.4 `scripts/playtest/schemas/*.json`(契約)

| ファイル | 分類 | 根拠 |
|---|---|---|
| `observation-packet.v0.1`・`observation-request.v0.1` | **[A′]** | 封筒(`contract`・`schemaVersion`・`packetId`・`customerRef`・`facts`・`aggregates`・`provenance{pipelineVersion,generatedAt,sources,inputs,thresholds}`)は汎用。**`facts` の 7 欄(games/moves/engine/time/branches/collapse/recognition)と各行の欄(`sfen`・`usi`・`scoreCp`・`top1Usi`…)は将棋** |
| `hypothesis.v0.1〜v0.4` | **[A′]** | 骨格(observations → statement → counterEvidence → prediction、`kind` 6 種、`factOrHypothesis`、`knowledge.reviewStatus` 4 種)は汎用。`lane` enum(`time side shape prior alternative reply fork`)・`knowledge.kind` の `"shogi"`・`knowledge.origin.kifu` は将棋 |
| `seat-output.v0.1`・`seat-output.llm.v0.1`・`integration*.v0.1`・`answer-selection.v0.1`・`fill-text.v0.1` | **[A′]** | 封筒・状態・`selfComputedNumbers`・`contradictions`・`heldBack`・`humanQueue`・`adoptedBy` は汎用。`boards`(answer-selection)は器の形 |
| `failure-event.v0.1〜0.7`・`diagnosis-*`・`diagnosis-gate`・`diagnosis-condition` | **[B]** | 評価値・崩れ・条件式(将棋の診断の契約)。版の並びは `lib/schemaVersions.ts` |

## 2.5 その他

| パス | 分類 | 根拠 | 確度 |
|---|---|---|---|
| `apps/server/src/**`(analysis 37・engine 8・rules 7・notation 3・game・api) | **[B]** | 対局中コーチ本体。USI エンジン・局面・形判定 | 高(一覧) |
| `apps/web/src/**` | **[B]** | 盤面 UI(`sfenBoard.ts`・`pieceKanji.ts`) | 高(一覧) |
| `apps/server/engine/`・`spike/engine/`(やねうら王・NNUE) | **[B]/[C]** | エンジンのバイナリ・評価関数。回帰の前提だが**リポジトリ外の成果物**(追跡状況は未確認) | 低 |
| `data/schemas/*.json`・`data/{shapes,openings,intents,explanations,drafts}/` | **[B]**(語彙の正本) | 形・戦型・狙いの定義。`check_answer.reviewed_shape_names` と packet の `facts.recognition.definitions` が読む | 高 |
| `scripts/validate-data.mjs`・`scripts/validate-data.test.ts`・`scripts/verify-shapes.ts`・`scripts/u6j-precheck.ts`・`scripts/lib/usi-coordinates.*`・`scripts/hooks/validate-data-hook.sh` | **[B]** | data/ の検証・USI 座標 | 中 |
| `scripts/typecheck-scripts.mjs`・`scripts/check-docs.mjs` | **[C]**(門) | 2 つの tsconfig を「必ず両方」走らせる門 | 高 |
| `scripts/playtest/invariants/*`(i1〜i11 + types + index) | **[B]** | 対局中コーチの不変条件(沈黙・矛盾・断定…)。`types.ts` は `apps/server/src/api/stateResponse.ts` を import | 高 |
| `scripts/playtest/gateFixtures/`(jsonl 9 本 + specs.ts)・`lib/__fixtures__/`(hypothesis v0.1/v0.2 例・obsSnapshot 9 本)・`lib/conditionFixtures/`・`lib/conditions/` | **[C]** | 試験だけの固定材料(「将棋の判断を含めない」と宣言) | 高 |
| `scripts/playtest/kifu/*.json`(7)・`records/**`(345、全追跡)・`reports/`(2)・`fig/`(2)・`__snapshots__/` | **[C]** | 固定棋譜・評価記録・実験記録 `records/experiment-llm-25/E-00x.json`・python 試験名のスナップショット | 高 |
| `scripts/playtest/out/`(3,570 ファイル、**gitignore**) | **[C]**(候補)/**[D]** | 顧客ごとの実物(`c5/packet/observation-packet.json` = 1,715,395 バイト、sha256 `1c43582b…fbc7`、packetId `22aee8fe696d0262`、facts 25/1242/1033/25/404/155/25 行・aggregates 26 行、`c5/llm-seats/` 席の出力 7 run、`c5/exit/answer_selection.json`)。**追跡されていないので Golden Master の正本にはできない**(§5 で扱う) | 高 |
| `spike/`(usi-client・smoke-test) | **[D]** | CLAUDE.md「Phase 0 着手前の技術検証」 | 高 |
| `prototypes/shape-matcher/` | **[D]** | 同上 | 高 |
| `scripts/playtest/node_modules/`(中に `node_modules` が 1 つだけ) | **[D]** | 空の入れ子。`scripts/playtest/package.json` は無い(依存はルートと `apps/*` の workspace) | 高 |
| `docs/GOLDEN_MASTER_CUSTOMER_EXIT.md`・`docs/DELIVER_GATES.md`・`docs/OBSERVATION_ITEMS.md`・`docs/LLM_SEATS_INSTRUCTION*.md`・`docs/LLM_SEATS_INTEGRATOR_INSTRUCTION*.md` | **[C]**(実行時に読まれる正本) | `OBSERVATION_ITEMS.md` は `hypothesis.loadObsRegistry` が**実行時に読む**。指示文 4 本は `seatRun.FIXED_INSTRUCTION_SHA256` で sha 固定 | 高 |
| `docs/CRITIQUE_*`・`SEALED_READING_*`・`LANE_*_LOG`・`STEP_*_PLAN`・`EXPERIMENT_*` | **[D]**(記録) | 経緯。移行対象ではない | 中 |

## 2.6 試験の分類(テスト監査)

| 区分 | 本数 | 根拠・代表 |
|---|---|---|
| TS 試験(vitest) | 115(`lib/` 90・root 14・`invariants/` 11)+ `apps/` 55 + `scripts/` 2 | `ls *.test.ts` |
| Python 試験 | 18(`*_test.py`) | `__snapshots__/reportPdfPythonTests.test.ts.snap` が名前の集合を固定し、`reportPdfPythonTests.test.ts` が `readdirSync` で全部回す(床 `MIN_PYTHON_TESTS = 10`、1 本 30 秒上限) |
| **Core 単体テスト候補** | `eventSchema` `packetRef` `prng` `env` `tokenBudget` `schemaAdapters` `llmClient` `gitState` の `.test.ts`、`compare_render_test.py` | 対象 module に将棋 import が無い(§2.1.1)。**中身は未読(推測)** |
| **Core × Adapter 結合テスト候補** | `observationPacket.test.ts` `observationPacketRef.test.ts` `hypothesis.test.ts` `seatOutput.test.ts` `integration.test.ts` `seatRun.test.ts` `exitSelect.test.ts` `answerSelection.test.ts`、`check_answer_test.py` `exit_gate_test.py` `check_structure_test.py` `check_delivery_test.py` | 対象が [A′]。**どの試験が将棋の材料を合成しているかは未確認** |
| **Adapter 単体テスト** | §2.1.2 の module の `.test.ts`、`apps/` 55 本、`board_*`・`move_text`・`exit_*`・`render` 系 python 試験、`invariants/*.test.ts` | |
| **Golden Master / byte-for-byte** | `__snapshots__/…snap`(python 試験名の集合、`toMatchSnapshot` は TS 試験全体で 1 本だけ)、`sourceFilesAreText.test.ts`、`gateFixtures/*.jsonl`(「`gateFixtureText` の出力とバイト一致」をコメントで宣言)、`lib/fillTexts.ts` の `RULES_SHA256`、`seatRun.FIXED_INSTRUCTION_SHA256`、`board_spec_test.py`・`exit_fill_test.py`(sha256 を使う) | **PDF のバイト一致試験は無い**(`compare_render.py` 冒頭: reportlab の `/CreationDate` 等で同じコードでも変わる。実測 64 バイト差)。PDF は**意味比較**(ページ数・文字・ベクタ指紋)で固定 |
| **変異試験(mutation)** | TS 試験 115 本のうち「変異」を含む 27 本、「陽性対照」2 本。Python 試験 18 本のうち「変異/陽性対照/mutation」を含む 15 本 | 方針は `docs/TESTING_STRATEGY.md` §「変異は両向きに回す」・§「python の変異試験とバイトコード(`pycache_prefix`)」 |
| **negative control** | 上の「陽性対照」2 本と、各試験中の「落ちるべき入力」(未集計) | **[X]** 本数は未確認 |
| **独立監査用** | `records/**`(345)・`reports/`・`docs/SEALED_READING_*`・`compare_render.py --seal` の 3 つの数 | 監査の手順は `docs/AGENT_PROTOCOL.md`(未読、名前のみ) |
| 実物(gitignore)を読む試験 | `check_answer_test.py` が `out/tatsunami3/…` 等を**docstring で言及**(354・358・545 行)。**実際に読んでいるかは未確認** ― 実データで回る試験があれば worktree で落ちる(記憶 `test-must-not-read-ignored-material`) | **[X]** |

---

# 3. Core 候補における将棋依存・禁止語検出ログ

5 つの層を分けて記録する。**「語が在る」≠「依存している」** を守り、各項目に「実行時に意味を持つか」を書く。

## 3.1 ① 実行時 import / 実行時依存(Core → 将棋側)

| Core 候補 | 依存先 | 種類 | 経路 | 判定 |
|---|---|---|---|---|
| `lib/hypothesis.ts:30` | `./timeSearch.js` の `SEARCH_COLUMNS` | 通常 import(値) | `timeSearch → reportData → apps/server/src/{analysis,notation,rules}/* + shogiops`(`grep ^import` で確認) | **逆依存。** `loadObsRegistry` の `obs.timeSearch.col.*` 30 本を作るためだけ。登録簿(§3.3)に書き切るか、列の一覧を引数で注入すれば切れる |
| `lib/observationProvenance.ts:16-17` | `./observationFacts.js` の `AHEAD_CP`、`./reportData.js` の `TIME_VALUES` | 通常 import(値) | `observationFacts → apps/server/src/rules/sfenPosition + moveFacts + read + shogiops/util` | **逆依存。** `toolThresholds()`(31〜43 行)の閾値の表を作るため。閾値の表は adapter が渡す `ThresholdRow[]` にすれば切れる |
| `lib/observationAggregates.ts:13` | `./observationFacts.js` の `FactsMaterials` | **`import type`(型のみ)** | 実行時は無し | 型の境界だけ。`aggregatesOf(facts, materials)`(395 行)の第 2 引数の型を generic にすれば切れる |
| `lib/observationPacket.ts:14` | `./observationAggregates.js` の `aggregateAgreementProblems` | 通常 import(値) | 同ファイル内の `ROW_DEFINITIONS`(将棋の 26 行) | 機構(packet 検証入口)が将棋の整合関係を内包。関係の表を adapter から注入 |
| `lib/seatOutput.ts:10`・`integration.ts:14`・`exitSelect.ts`・`seatInput.ts:11` | `hypothesis.js`・`observationPacket.js` | 通常 import | 上の 2 本を継承 | 上が切れれば切れる |
| `lib/gitState.ts:21` | `../invariants/types.js` の `MetaLine` | **型のみ** | `invariants/types.ts` は `apps/server/src/api/stateResponse.js` を import(型) | 型だけ。`Pick<MetaLine,"dirty">` を局所型に置き換えれば切れる |
| `lib/observationAggregates.ts`(汎用部) | ― | ― | ― | `Population.from` の型 `PopulationFrom` が 7 列の union(21 行)、`AggregateUnit` が `"positions"\|"games"\|"moves"\|"seconds"\|"centipawns"`(22 行)。**型リテラルに将棋の単位** |
| `report-pdf/exit_gate.py:36-39` | `check_answer`(材料層込み)・`check_structure`・`exit_candidates`・`exit_index` | `import`(モジュール先頭) | 材料層 = 将棋 | **汎用部(`number_claims`・`check_agg_tags`・`check_ans_tags`)が、材料層のある `check_answer` を丸ごと import**。`scan_numbers`/`strip_marks`/印の正規表現だけを別 module に切れば、門の汎用部は材料層無しで動く(関数の引数は md 文字列と JSON) |
| `report-pdf/exit_gate.py:544,567,593` | `exit_fill` | **関数内 import**(「循環 import を避けて」) | ⑥ = 将棋 | 検査 (xi) の型の再構成(`fact_templates` 等)が ⑥ の表を読む。逆依存 |
| `report-pdf/check_delivery.py:24` | `check_answer.BANNED_WORDS` | `from … import` | 材料層込みの module を読み込む(副作用は無い見込み・**未確認**) | 語の一覧を 1 か所に置く意図。一覧を**データ(JSON)**にすれば両言語から読める |
| `report-pdf/check_answer.py:1419-1427` | `data/{shapes,openings,intents}/*.json`(`glob`) | **将棋固有データファイル**への参照(`reviewed_shape_names`) | `review_status in ("human_reviewed","expert_verified")` の名前だけ | 「承認済み語彙の一覧」は adapter が返す関数に |
| `scripts/playtest/observationPacket.ts:61-64` | `report-pdf/dump_booklet_numbers.py`(`spawnSync python3`) | **プロセス境界**を越えた依存 | 冊子の数を python に数えさせて突き合わせ | packet の生産者(adapter)側の事情。Core ではない |
| `lib/deliver.ts:132-134` | `npx tsx` と `python3 -X utf8 <py>`(`spawn`) | プロセス境界 | 段の表が TS/Python の道具を名指し | 段の実行機構を Core に出すなら「コマンドの組み立て」は adapter |

## 3.2 ② 動的参照(importlib / getattr / `await import` / 正規表現でソースを読む)

| 場所 | 中身 | 実行時の意味 |
|---|---|---|
| `lib/hypothesis.ts:110-137` | `CHECK_ANSWER_PY = new URL("../report-pdf/check_answer.py")` を `readFileSync` し、`BANNED_WORDS_RE = /BANNED_WORDS\s*=\s*\[([\s\S]*?)\]/` で**Python のソースから配列リテラルを抜く**。読めなければ例外 | **言語をまたぐテキスト依存。** TS Core が Python Adapter のソースの字面に依存している。一覧が空(`BANNED_WORDS = []`)でも検査 H-5 の「〜という読みです」の形の検査は残る(125 行) |
| `lib/condition.ts:296` | `await import(pathToFileURL(absolute).href)` で条件式の定義 module を読み込み、バイト列の sha256 を取る | plugin 機構。定義の中身は将棋。**機構は Core 候補** |
| `report-pdf/exit_index.py:359,366` | `getattr(flowable, "_index_pos", None)` / `_index_sec` | reportlab の flowable に印を付けて `afterFlowable` で拾う。組版の機構(adapter) |
| `report-pdf/check_answer.py` 各所 | `row.get("kind") != "position"`(458)・`"summary"`(566)・`data.get("kind")` が `time_cause`/`time_cause_search`/`direct_answers`/`final_positions`(614〜895) | **辞書キーによる分岐**。材料の種類の判別 = 将棋の材料層 |
| `report-pdf/exit_candidates.py:714,866` | `THRESHOLD_SENTENCES.get(t["kind"])`・`fdata["findings"].get(f["kind"])` | 発見の種類で文面を引く。adapter |

`importlib`・`__import__` の使用は Python 側で **0 件**(grep)。TS 側の `require(` も 0 件。

## 3.3 ③ 設定・JSONPath・辞書・登録簿による実行時参照

| Core 候補 | 参照先 | 中身 |
|---|---|---|
| `lib/hypothesis.ts:155-175` `loadObsRegistry(mdPath)` | `docs/OBSERVATION_ITEMS.md` の `## 1.` 〜 `## 2.` の表の先頭欄 `obs.*` | **Markdown 文書を実行時の登録簿として読む**(H-2 の許す集合)。登録簿の中身は将棋の観測項目 |
| `lib/packetRef.ts:15,19,24` | 列名 7 つと `recognition.rows|definitions` | 文法そのものに**設定値が焼き込み** |
| `lib/observationPacket.ts:204` `resolvePacketPath` | `aggregates.<id>.{numerator,denominator,value}` / `facts.<列>[n].<欄>` | 解決器は汎用(path を辿るだけ)。列の集合は packetRef 由来 |
| `lib/observationAggregates.ts` `Population{from,where,unit}` | facts の列と欄名を**文字列**で指す(`field: "top1Side"` 等) | 機構は汎用(JSONPath 風)。`ROW_DEFINITIONS` の値が将棋 |
| `lib/hypothesis.ts:720-768` `H10_PROSE_FIELDS`/`H10_NON_PROSE_FIELDS` | 契約の文字列欄の**全部を 2 つの表で分類**(欄が増えたら試験が赤) | 機構は汎用。欄名は契約(§2.4 の [A′]) |
| `lib/hypothesis.ts:795-830` `recognitionNameCorpus`/`recognizedNames` | `facts.recognition.definitions[].{name,nameKana,id}`・`facts.recognition.rows[].names` | **H-10 が「語彙の正本」を packet の中から読む**。Meeting では「固有名詞の登録簿」に相当(§6.4) |
| `lib/hypothesis.ts:888` `APPROVED_REVIEW_STATUSES = ["human_reviewed","expert_verified"]` | 定義側の `reviewStatus` | 汎用(承認状態の語彙) |
| `lib/seatRun.ts:40-46` `FIXED_INSTRUCTION_SHA256` | `docs/LLM_SEATS_INSTRUCTION_v1*.md` 等 4 本の sha | 指示文(将棋)を**固定値で照合**。表に無い名前も誤り |
| `lib/seatInput.ts:16` `INSTRUCTION_V1_SHA256` | 同上の v1 | 同上 |
| `lib/env.ts:8` `ENV_NAMES` | `.env` の鍵名 | 汎用 |
| `report-pdf/exit_gate.py:606` `check_agg_tags(md, packet, …)` | `<!-- agg: id -->` → `aggregates[].id` | 汎用(id → 行 → 分子・分母・値) |
| `report-pdf/exit_gate.py:440` `check_ans_tags(md, request, selection, …)` | `<!-- ans: qN status -->` → `request.customerQuestions` と `answer_selection.answers[]` | 汎用(問い id → 状態の一致) |
| `report-pdf/check_structure.py:54-62` `SECTIONS` | 見出しの役割 6 つ(ひとことで/局面で見る/試せること/答え合わせ/数え方/対応表) | **設定値が将棋の冊子**。役割の表を外から渡せば機構は汎用 |
| `report-pdf/exit_fill.py:1145` `sfens_from_env(os.environ)` | 環境変数 | adapter |
| `report-pdf/_head.py`・`_util.py`・`_mid.py` | `REPORT_DATA_DIR` 環境変数(README) | adapter |

## 3.4 ④ 文字列リテラル(実行時に意味を持つもの / 持たないもの)

| Core 候補 | 文字列 | 実行時の意味 |
|---|---|---|
| `lib/hypothesis.ts:77` | `kind: "shogi" \| "discovered" \| "coaching"`(型)+ schema の enum `["shogi","discovered","coaching"]` | **持つ**(検証で enum 照合)。Core 化するなら `knowledge.kind` の値域は adapter の設定 |
| `lib/seatOutput.ts:19`・`integration.ts:31` | `"answer_menu.json"`・`"exit_candidates.json"`・`"9_本編.md"` | **持つ**(席に渡していないことの検査 `SEAT_EXCLUDED_INPUTS`)。ファイル名 = 将棋の納品物。設定へ |
| `lib/seatOutput.ts:166`・`integration.ts:310` | `origin: { kifu: ctx.customerRef, lane: "llm-seat"/"llm-integrator" }` | **持つ**(契約の欄名 `kifu`)。欄名の改名は契約の版上げ |
| `lib/integration.ts:33-35` | `SEAT_NAME_RE = /gpt\|gemini\|claude\|openai\|anthropic\|google/i`、`SEAT_COUNT_REFERENCE_RE = /seatCount\|一致\|[0-9０-９]\s*席\|…/` | **持つ**(一致を証拠にしない検査)。日本語の字面に依存するが将棋ではない |
| `lib/observationProvenance.ts:81,86` | `kind: "patient_report_data・sfens・time_cause(対局後診断の報告の材料)"`・`"direct_answers(…局面)"` | **持つ**(provenance の `sources[].kind` の値)。adapter の記述 |
| `lib/observationPacket.ts:84-101` | 「持ち時間」「局」のメッセージ | 持つのはメッセージ文だけ。欄名 `timeLimitSec` の依存は §3.3 |
| `lib/seatInput.ts:84-110` | `READING_GUIDE`・`OMITTED`・`NOT_INCLUDED`(USI・centipawn・先手後手・戦型の説明) | **持つ(LLM に送られる)**。adapter |
| `lib/gitState.ts:208-231` | 引数名 `kifuId` | 持たない(欄名) |
| `lib/packetRef.ts` | 列名(§3.3) | 持つ |
| `report-pdf/check_answer.py:139` | `PIECE_CHARS = "歩香桂銀金角飛玉と杏圭全馬竜"` | **持つ**(指し手の照合 `check_line_moves`)。材料層 |
| `report-pdf/check_answer.py:521-522` | `SIDE_JP = {"attack": "攻め", "defense": "自玉側", …}` | 持つ(`fig1.py`・`render_time_cause.py` も import)。材料層 |
| `report-pdf/check_answer.py:103-110` | `POS_TAG_RE`(`付録N`) | 持つ。印の文法だが「付録」は将棋の納品の器 |
| `report-pdf/check_delivery.py` | `"最善手"`・`"水匠"`・`"/Users/"`・`"None"` | 持つ。前 2 つは adapter の語、後 2 つは汎用の PII/事故検知 |
| `report-pdf/compare_render.py` | 無し(将棋語 0 件。grep で `fitz` のみ) | ― |
| `report-pdf/exit_index.py:170-180,268-304` | `COUNTING_NOTES`・`COVER_LEAD`・`COVER_TAIL`(「+300 以上を優勢」「分かれ道…600」「盤の図は…本人を下に」) | **持つ(顧客に出る文)**。adapter |
| `report-pdf/check_structure.py:115-140` | `TERM_LINES`・`SCOPE_SENTENCE_TEMPLATE`・`OPENING_*_TEMPLATE` | 持つ(顧客に出る文 + 門の照合)。adapter |

## 3.5 ⑤ コメント・docstring・ドキュメント(依存ではない)

| Core 候補 | 将棋語の例 | 扱い |
|---|---|---|
| `lib/observationPacket.ts` | 「25 局で 1 つか」「局によって違う」(85〜101 行コメント) | 説明のみ |
| `lib/observationAggregates.ts` | 「冊子の 65 / 107・76 / 132」(225 行) | 説明のみ |
| `lib/hypothesis.ts` | 冒頭「将棋の判断・仮説の妥当性の判断(をしない)」 | 説明のみ(むしろ境界の宣言) |
| `lib/prng.ts` | 「対局者(自分側)の 5 プロファイル」「将棋の判断は一切行わない」 | 説明のみ |
| `lib/eventSchema.ts` | 無し | ― |
| `report-pdf/check_answer.py` 1〜127 行 | 「局面」「指し手」「付録」「盤」 | 使い方の説明。ただし**同ファイルの材料層は実行時依存**(§3.1) |
| `report-pdf/exit_gate.py` 1〜32 行 | 「数 3 つ・盤 2 つ」 | 説明。実体は `check_p1/p2` の本数定数(`check_structure.HONBUN_P1_FACT_COUNT`・`BOARD_COUNT`) |
| `report-pdf/compare_render.py` | 「盤は埋め込み画像ではなくベクタ描画」(docstring) | 説明のみ。コードは PDF 一般 |

**結論(§3)**: 純粋に将棋非依存で今すぐ Core に置けるのは **TS 8 本**(`eventSchema` `packetRef`※ `prng` `env` `tokenBudget` `schemaAdapters` `llmClient` `gitState`※)と **Python 3 本**(`compare_render` `check_fonts_embedded` `rename_list`※)。※は設定値の注入か欄名の局所化が要る。それ以外の Core 候補は「機構は汎用・設定値と整合関係が将棋」の **[A′]** で、§7 Phase 2 の切り分けが要る。

---

# 4. 現行アーキテクチャから Core 抽象インターフェースへのマッピング表

## 4.1 主要概念 → 現行実装

| 概念 | ファイル | クラス / 関数 | 現在の責務 | 将棋依存 | Core / Adapter | 根拠 |
|---|---|---|---|---|---|---|
| **ObservationPacket** | `schemas/observation-packet.v0.1.schema.json`、`lib/observationPacket.ts` | `validateObservationPacket`・`observationPacketProblems`・`packetIdOf`・`canonicalJson`・`loadObservationPacketSchema` | 「唯一の事実入力」の封筒・schema 照合・封(canonical JSON の sha)・検査入口 | 封筒は無し。`facts` の 7 欄と `timeLimitSec` は有り | **Core(封筒・封・入口)/ Adapter(`facts` の形・`timeLimit`・整合関係)** | §2.1.1・§3.1 |
| ObservationPacket の生産 | `lib/observationFacts.ts`・`observationMaterials.ts`・`observationAggregates.aggregatesOf`・`observationProvenance.provenanceOf`、CLI `observationPacket.ts` | `aggregatesOf(facts, materials)`・`provenanceOf` | 既存の将棋の出力から facts/aggregates/provenance を組む | 有り(shogiops・apps/server) | **Adapter** | §2.1.2 |
| ObservationRequest(顧客の問い) | `schemas/observation-request.v0.1`、`observationPacket.requestAgreementProblems` | ― | packet と分離された分析の条件(`customerQuestions`・`requestedScope`) | `requestedScope.games/timeLimitSec` | Core(分離の原則)/ Adapter(scope の欄) | `NEXTGEN_PIPELINE_BRIEF` §2.5 |
| **Claim**(主張) | `lib/hypothesis.ts`(`HypothesisLine`、`kind` 6 種、`factOrHypothesis`)、`seatOutput.ts`(席の封筒 `items[]`・`answers[]`・`selfComputedNumbers`)、`integration.ts`(`clusters`・`contradictions`・`forVerification`)、`exit_gate.py`(md の数の主張 `number_claims`) | `validateHypothesisLine`・`seatOutputProblems`・`integrationProblems`・`number_claims` | 「観測 → 文 → 反証 → 予測」の 1 行。顧客向け md では「文に出た数・印」が主張 | 骨格は無し。`lane`・`knowledge.kind`・`origin.kifu` は有り | **Core(骨格・kind・状態)/ Adapter(lane 等の値域)** | §2.4 |
| **EvidencePointer** | `lib/packetRef.ts`(`packetRef.path` の文法)、`check_answer.py`(`<!-- menu: Mx -->`・`<!-- pos: G/P 付録N [組] -->`)、`exit_gate.py`(`<!-- agg: id -->`・`<!-- ans: qN status -->`)、`exit_render.py`(`<!-- sec: 付録N/節 -->`) | `packetRefPathProblems`・`aggregateRef`・`POS_TAG_RE`・`MENU_TAG_RE`・`agg_tags_of`・`ans_tags_of` | 文や仮説が packet / 材料のどこを指すかの**機械で読める印** | `packetRef` は列名が焼き込み。`pos`/`menu` は将棋の器 | **Core(`aggregates.<id>.<part>` / `facts.<列>[i].<欄>` の文法・`agg`・`ans`)/ Adapter(`pos`・`menu`・`sec`・列の集合)** | §3.3 |
| **Canonical Fetch**(参照の解決・数え直し) | `lib/observationPacket.ts:204 resolvePacketPath`、`lib/observationAggregates.ts:769-829 recountProblems / recountRowProblems`、`hypothesis.ts` H-9 | ― | path を packet の中で解決し値を返す/集計行を `population` から facts で数え直す | 解決器・数え直しは無し。行の定義は有り | **Core** | §2.1.1 |
| **Verification** | `lib/hypothesis.ts`(H-1〜H-11)、`report-pdf/check_answer.py`(検査 1〜7: 数・指し手・禁止語・行動の句・印・局面)、`exit_gate.py`((i)〜(xi))、`check_structure.py`、`seatInput.numberInclusionProblems`、`integration.integrationProblems` | `validateHypothesisLine(line, {packet, registry, bannedWords, …})` → `CheckResult[]`(全部回して全部返す) | 事実と整合性の機械検証。**「0 件」と「検査していない」を分ける**(読めなければ例外) | H-1〜H-9・H-10 の機構は無し。SEARCH_COLUMNS・BANNED_WORDS 読み・`check_answer` の材料層は有り | **Core(検査の骨格と `CheckResult` の形)/ Adapter(材料層・指し手照合・付録の印)** | §3.1 |
| **ApprovalGate** | `lib/deliver.ts`(`action: "gate"` の段 `prose-gate`・`answer-gate`・`exit-select`・`exit-gate`)、`exitSelect.adoptedBy` 常に `null`・`adoptedByProblems`、`answerSelection.ADOPTED_STATUSES`、`hypothesis` H-7(`APPROVED_REVIEW_STATUSES`)、`data/*.json` の `review_status` | `selectionGateProblems`・`checkH7` | 人が埋めるまで止まる段/機械は採用しない/昇格は human_reviewed 以上 | 無し(状態の語彙は汎用) | **Core** | §2.1.1 |
| **Provenance** | `schemas/observation-packet` の `provenance{pipelineVersion,generatedAt,sources,inputs(sha256),thresholds}`、`lib/observationProvenance.ts`(`sourcesOf`・`traceProblems`)、`packetIdOf`、`gitState.readGitState`、`seatRun.FIXED_INSTRUCTION_SHA256`、`condition.loadCondition` の sha、`compare_render --seal` | ― | 数から packet・材料・閾値・コミット・指示文へ戻れること | 閾値の表(`AHEAD_CP`・`TIME_VALUES`)の import が有り | **Core(枠・sha・git・固定指示文の照合・封)/ Adapter(閾値の値)** | §3.1 |
| **MutationAudit** | `docs/TESTING_STRATEGY.md` §「変異は両向きに回す」・§`pycache_prefix`、TS 試験 27 本・Python 試験 15 本が「変異」を扱う、`reportPdfPythonTests.test.ts`(名前の集合のスナップショット) | ― | 検査を無効化する変異で赤になることを確かめる。沈黙を「通った」と読まない | 無し(方法論) | **Core(方法論・雛形)**。個々の変異は Adapter の試験 | §2.6 |
| **contradiction detection** | `integration.ts`(契約の `contradictions`・`heldBack`、`SEAT_COUNT_REFERENCE_RE` で一致を証拠にしない)、`observationAggregates.aggregateAgreementProblems`(行どうしの関係)、`hypothesis` H-3(反証を空で埋めない)、`check_structure.check_one_referent`・`check_name_agrees` | ― | 席どうしの矛盾の並置/集計の筋の一致/呼び方 1 通り | 整合関係の**中身**は将棋 | **Core(矛盾を並べて消さない枠・関係の検査器)/ Adapter(関係の表)** | §2.1.1 |
| **state machine** | `lib/deliver.ts`(`DELIVER_STAGES`・`action: run/skip/gate/fail`・`stagesFrom(--from)`・済み判定)、`lib/pipeline.ts`(`runWithLimit`・`planPipeline`)、`hypothesis.status`・`knowledge.reviewStatus{draft,human_reviewed,expert_verified,expired}`、`answerSelection.ADOPTED_STATUSES`、`seatRun.AbsentReason` 9 種 | ― | 段を不可逆に近く分け、人の席で止まり、済みは飛ばす | 段の表は将棋。機構は無し | **[X] → Core 候補(段の runner)/ Adapter(段の表)** | §2.1.1 |
| **validation**(契約の形) | `lib/eventSchema.ts`(`validate`)、`schemas/*.json`、`lib/schemaVersions.ts`、`seatOutput.validateSeatOutputEnvelope`、`answerSelection.validateAnswerSelection`(`maxItems` を扱わないので本数は道具で数える) | ― | JSON Schema 部分集合での検証。知らないキーワードは例外 | 無し | **Core** | §2.1.1 |
| **rendering / output** | `report-pdf/render_*.py`・`exit_body.py`・`exit_cover.py`・`exit_render.py`(pypdf でページ抜き)・`board_draw.py`・`exit_index.py`(索引)、`exit_fill.py`(⑥) | ― | reportlab で PDF。索引は置いた経路が書く | 有り | **Adapter** | §2.3 |
| 出力の封・比較 | `report-pdf/compare_render.py`(`profile`・`differences`・`write_seal`・`verify_seal`)、`check_fonts_embedded.py` | ― | PDF の意味比較(ページ数・文字・ベクタ指紋)と封 | 無し | **Core** | §2.3 |
| 納品の衛生 | `report-pdf/check_delivery.py`、`hypothesis` H-8 | ― | 実名・`@`・絶対パス・`None` の検出 | 固定語 2 つだけ | **Core(機構)/ Adapter(語)** | §2.3 |
| LLM 呼び出し | `lib/llmClient.ts`・`schemaAdapters.ts`・`tokenBudget.ts`・`env.ts`・`seatRun.ts`(再試行・費用上限・空席・`held_back`)・`integration.seatPermutation`(PRNG) | `callStructured`・`runSlot`(未読、名前のみ)・`budgetDecision` | 3 社への構造化出力・上限・再試行・席の盲検 | 指示文と sha は将棋 | **Core(機構)/ Adapter(指示文)** | §2.1.1 |
| 語彙の統制 | `hypothesis` H-10/H-11(`recognizedNames`・`approvedRecognitionWords`)、`check_answer.reviewed_shape_names`、`check_answer.NAME_LIKE_RE`(`(戦法\|囲い\|飛車\|銀)$`)、`exit_groups.GROUP_LABELS` | ― | 名前は認識された・承認されたものだけ | 語彙の出どころ(packet の `recognition`・`data/`)と `NAME_LIKE_RE` は将棋 | **Core(「登録簿に在る語だけ」の検査器)/ Adapter(登録簿)** | §3.3 |

## 4.2 現行コードから導いた Core の抽象インターフェース(机上ではなく、上の表の関数の形から)

```
// 名前は仮。型は現行の関数の引数・返り値から写した。
type Problems = string[]                       // 現行: 空なら通った(observationPacketProblems 等)
type CheckResult = { check: string; ok: boolean; messages: string[]; skipped?: … }  // 現行: hypothesis.ts 179 行

interface PacketSpec {                          // adapter が渡す(§3.3 の焼き込みを外に出す)
  factsColumns: readonly string[]               // 現行: packetRef.PACKET_FACTS_COLUMNS
  nestedColumns: Record<string, readonly string[]>   // 現行: recognition → rows|definitions
  rowDefinitions: readonly RowDefinition[]      // 現行: observationAggregates.ROW_DEFINITIONS
  agreementRelations: (aggregates, facts) => Problems   // 現行: aggregateAgreementProblems
  scopeProblems: (facts, request) => Problems   // 現行: timeLimitProblems + requestAgreementProblems
  thresholds: () => ThresholdRow[]              // 現行: observationProvenance.toolThresholds
  vocabulary: (packet) => { recognized: Set<string>; approved: Set<string> }  // 現行: hypothesis.recognizedNames / approvedRecognitionWords
  bannedWords: readonly string[]                // 現行: check_answer.BANNED_WORDS(TS が Python を正規表現で読む → データ化)
  registry: Set<string>                         // 現行: hypothesis.loadObsRegistry(docs/OBSERVATION_ITEMS.md + SEARCH_COLUMNS)
}

// 封と検証の入口(現行のまま)
packetId(facts, aggregates): string             // observationPacket.packetIdOf(canonicalJson の sha256 16 桁)
validatePacket(packet, spec): Problems          // observationPacketProblems − 将棋の 3 検査 + spec.scopeProblems/agreementRelations
resolve(packet, path): {ok, value} | {ok:false, reason}   // observationPacket.resolvePacketPath
recount(packet, aggregateId): {problems, notes} // observationAggregates.recountRowProblems

// 主張の検証(現行 validateHypothesisLine の形)
verify(packet, claims: HypothesisLine[], spec, opts): CheckResult[][]
//   H-1 数の実在 / H-2 ID 登録(spec.registry, packetRef 文法) / H-3 反証 / H-4 予測 / H-5 禁止語・断定形
//   H-6 盲検 / H-7 昇格 / H-8 PII / H-9 参照の実在と値(resolve + recount) / H-10 語彙(spec.vocabulary.recognized)
//   H-11 顧客に出せる段か(spec.vocabulary.approved)
verifyText(md, packet, request?, selection?, spec): Problems   // exit_gate.number_claims + check_agg_tags + check_ans_tags + check_answer の走査層

// 席(LLM)の封筒と統合(現行のまま)
completeSeatOutput / seatOutputProblems / buildIntegrationInput / integrationProblems

// 承認の門(現行のまま)
selectionGateProblems(selection, …)             // exitSelect: adoptedBy が埋まるまで止まる
```

**現行で未定義のもの(推測で足さない)**: `PacketSpec` という**束ねた型は存在しない**。上の各要素はそれぞれ別の module の定数・関数として散っている。束ねるのは §7 Phase 2 の仕事で、**束ね方そのものは実装担当が決める**(ここでは「何を束ねれば逆依存が切れるか」だけを列挙した)。

---

# 5. Golden Master 凍結対象アーティファクト一覧

**前提**: `scripts/playtest/out/` は gitignore(3,570 ファイル、追跡 0)。**いま「実物」と呼ばれているもの(c5 の packet・席の出力・冊子 PDF)はどれも git に無い。** Golden Master にするには、(a) 追跡する場所へ写すか、(b) **sha256 と形の数だけを追跡し、実物は人間が別に保管する**か、どちらかを人間が決める必要がある(個人情報・顧客の棋譜を含むため (b) を推す。既存の `docs/GOLDEN_MASTER_CUSTOMER_EXIT.md` も (b) の形 ― sha256 とページ数だけを固定している)。

| # | 固定するもの | いま在る場所(追跡?) | 比較の仕方 | byte-for-byte か | 根拠・注意 |
|---|---|---|---|---|---|
| G-1 | **入力の棋譜(固定棋譜 JSON)** | `scripts/playtest/kifu/*.json`(7、追跡) | バイト一致 | **要る** | 既存。顧客の KIF は `out/` にあり追跡しない(実名) |
| G-2 | **Observation Packet** | `out/c5/packet/observation-packet.json`(**未追跡**。sha256 `1c43582b…a7fbc7`、1,715,395 バイト、packetId `22aee8fe696d0262`、facts 25/1242/1033/25/404/155/25、aggregates 26) | (1) `packetId`(canonical JSON の sha)の一致 (2) `observationPacketProblems` が 0 件 (3) `recountProblems` が 0 件 | **意味比較**(canonical JSON)。生のバイトは `generatedAt` が動くので不可 | `packetIdOf` は `facts`+`aggregates` だけを封じ `provenance` を含めない(observationPacket.ts 159 行)。**provenance の変化は別に `inputs[].sha256` で追う** |
| G-3 | **request** | `out/c5/packet/observation-request.json`(未追跡) | バイト一致 | 要る(小さい) | 問いの原文 |
| G-4 | **契約(schema)27 本** | `scripts/playtest/schemas/`(追跡) | バイト一致 + 版の並び(`schemaVersions.ts`) | **要る** | 「古い版のファイルは消さない」(schemaVersions.ts 冒頭) |
| G-5 | **席の出力・統合の出力**(LLM の非決定的な文) | `out/c5/llm-seats/<runId>/`(未追跡、7 run) | **出力は再現しない。固定するのは「門を通るか」**: `seatOutputProblems`・`integrationProblems`・`validateHypothesisLine` の結果が同じ(`AUTOMATION_STATUS` §1「出力は再現しない。通るか落ちるかは再現する」) | 不可 | 回帰の対象は**検証器の判定**であって文ではない。記録した run の封筒を固定入力にし、判定の一覧(check 名 × ok)を固定する |
| G-6 | **answer_selection** | `out/c5/exit/answer_selection.json`(未追跡) | バイト一致(人が採用の印を付けたもの) | 要る | `adoptedBy` が埋まった実物は人間の判断の記録 |
| G-7 | **本編 md(書き手の成果)** | `out/c5/_round6_sealed_2026-09-29/` 等(未追跡) | バイト一致 + `exit_gate`/`check_answer`/`check_structure` が 0 件 | 要る | 封(sealed)の写しがある |
| G-8 | **PDF(本編・付録)** | `docs/GOLDEN_MASTER_CUSTOMER_EXIT.md` §2 に sha256 とページ数(追跡)。実物は `out/kori/deliver1_送付用/` と別リポジトリ(未追跡) | **意味比較**: `compare_render.py --seal` の 3 つの数(ページ数・ページごとの文字・ベクタ指紋) | **不可**(`/CreationDate` 等で 64 バイト動く。実測) | 既存の封の仕組みをそのまま使う |
| G-9 | **検査結果**(門の rc と落ちた項目の一覧) | 無い(標準エラーに出るだけ) | 一覧のバイト一致 | 要る(文は決定的) | **新しく記録する場所が要る**(§7 Phase 0) |
| G-10 | **変異試験の結果** | `docs/TESTING_STRATEGY.md`・各試験の中 | 「変異 N 本中 N 本が赤」の数 | 数の一致 | 変異の一覧を文書で固定(記憶 `count-lines-not-guesses`: 一覧は切り詰められる) |
| G-11 | **独立監査の結果** | `docs/SEALED_READING_*`・`docs/CRITIQUE_*`(追跡) | 文書のまま | ― | 記録 |
| G-12 | **固定指示文 4 本の sha** | `lib/seatRun.ts:40-46`・`docs/LLM_SEATS_*.md`(追跡) | sha 一致 | 要る | 既存 |
| G-13 | **登録簿**(`docs/OBSERVATION_ITEMS.md` §1)・**語彙**(`data/**/*.json` と `review_status`) | 追跡 | バイト一致 | 要る | H-2・H-10・`reviewed_shape_names` の入力 |
| G-14 | **閾値**(`AHEAD_CP = 300`・`branch_min_loss_cp = 600`・`TIME_VALUES`・`long_think_sec`・`quick_sec`・`shallow_first_nodes`) | `exit_groups.py:81`・`observationProvenance.toolThresholds`・packet の `provenance.thresholds` | 値の一致(packet の `thresholds` と道具の定数) | 要る | 「人が決めた数は字で留める」(記憶 `pin-human-decided-numbers-literally`) |
| G-15 | **試験の名前の集合** | `__snapshots__/reportPdfPythonTests.test.ts.snap`(18 本) | スナップショット | 要る | 既存 |
| G-16 | **評価記録・実験記録** | `records/**`(345、追跡)・`records/experiment-llm-25/E-00x.json` | バイト一致 | 要る | 既存 |
| G-17 | **エンジン**(やねうら王 + NNUE) | `apps/server/engine/`(追跡状況**未確認**) | 版と評価関数の sha | ― | エンジンが変われば G-2 の数が変わる。**packet の `provenance.sources` に engine_version が入る設計**(NEXTGEN §2.5 の 6) |
| G-18 | **Base Commit** | `783ae6e…`(本文書 §1) | ― | ― | Phase 0 の起点 |

**「何を比較するか」の原則**(現行から写した): 数は canonical JSON と id で、文は「門を通るか」で、PDF は 3 つの数で、LLM の出力は固定しない。

---

# 6. 新リポジトリ / ディレクトリ構成案

## 6.1 現行の実態から見た制約(構成案より先に)

1. **二言語**: 検証器は TS(`lib/hypothesis.ts` 等)と Python(`check_answer.py`・`exit_gate.py`)に分かれ、互いに**文字列・プロセス境界**で繋がっている(`hypothesis.ts` が Python ソースを正規表現で読む、`deliver.ts` が `python3` を spawn、`observationPacket.ts` が `dump_booklet_numbers.py` を spawn)。
2. **工程の正本は TS の段表**(`lib/deliver.ts` の 24 段)で、Python は段ごとの道具。
3. **門は 2 本**(`npx vitest run --root scripts/playtest`・`npm run typecheck:scripts`)で、Python 試験は vitest の中から回す(`reportPdfPythonTests.test.ts`)。運用文書(RUNBOOK)は「門は 2 本」を前提にしている。
4. `scripts/playtest/tsconfig.json` の `include` が `../../apps/server/src` を含む(型検査がアプリ本体に依存)。
5. 別セッションが `fillTexts*`・`exit_fill.py` を変更中。

したがって**新リポジトリを先に作ると、(1)(2)(3) の結線を全部作り直すことになり、Golden Master との回帰が最後まで取れない**。**同一リポジトリの中に境界を引き、import の向きを試験で固定し、回帰が取れてから切り出す**順を推す。

## 6.2 構成案(段階 1: 同一リポジトリ内。ファイルは**動かさず**、境界だけ先に引く)

```
sgogi-coach/                       (現行のまま)
├── scripts/playtest/
│   ├── lib/                       ← 現行。Core 候補はここに残したまま「import の向き」を試験で固定(§7 Phase 1)
│   ├── report-pdf/                ← 現行
│   └── schemas/                   ← 現行
└── docs/AUDIT_CORE_EXTRACTION_PLAN.md(本文書)
```

段階 1 で**新しく置くのは試験 1 本と設計文書だけ**(§7 Phase 1 の I-1)。Core 候補の module が将棋側を import していないことを `import` 文の静的走査で固定する(現行の `sourceFilesAreText.test.ts` と同じ流儀)。

## 6.3 構成案(段階 2: 切り出し後。**今回は作らない**)

```
audit-platform/                    (新リポジトリは Phase 4 の回帰が緑になってから)
├── core/
│   ├── ts/                        packetRef / eventSchema / observationPacket(封・入口・resolve)
│   │                              observationAggregates(Population・recount)/ hypothesis(H-1〜H-11 の骨格)
│   │                              seatOutput / integration / seatRun / llmClient / schemaAdapters / tokenBudget / env / prng / gitState
│   │                              exitSelect / answerSelection(採用は機械がしない)
│   ├── py/                        text_claims(check_answer の走査層: scan_numbers・strip_marks・印の文法)
│   │                              exit_gate の汎用部(number_claims・agg・ans)/ compare_render / check_delivery(機構)/ rename_list / fonts_embedded
│   └── schemas/                   封筒だけの schema(packet 封筒・hypothesis 骨格・seat-output・integration・answer-selection)
│                                  ※ facts の中身は `additionalProperties` を adapter の schema で絞る(未設計)
├── adapters/
│   ├── shogi/                     observationFacts / observationMaterials / ROW_DEFINITIONS / agreementRelations
│   │                              thresholds / vocabulary(data/ と recognition)/ READING_GUIDE / 指示文 + sha
│   │                              report-pdf の組版(render_*・board_*・move_text・exit_body/cover/render/index/fill/candidates/groups)
│   │                              check_structure の SECTIONS・TERM_LINES / pos・menu・sec の印 / deliver の段表
│   └── meeting/                   §6.4 の最小要件だけ(実装しない)
├── tests/
│   ├── core/                      Core 単体 + 変異(両向き)
│   ├── golden/shogi/              §5 の G-2〜G-9 の sha・判定一覧・3 つの数(実物は含めない)
│   └── boundary/                  import 方向の試験(Adapter → Core のみ)
├── demos/
└── docs/
```

**現行より適切と考える点**: 「Core は将棋を知らない」を**試験で測れる形**(import 走査 + 「将棋語の実行時依存 0 件」の走査)にし、文書の約束にしない。
**未確定**: `core/py` と `core/ts` の重複(数の走査が TS `hypothesis` H-1 と Python `scan_numbers` の 2 か所にある。現行は md は Python・JSON は TS と役割が分かれているので、**統一は Phase 5 以降の判断**)。

## 6.4 Meeting Adapter の最小要件(境界を検証するためだけ。仕様確定ではない)

| Core が機械で再取得・比較できる候補 | packet での形(案。現行の facts の行に倣う) | 現行の対応物 |
|---|---|---|
| timestamp | `facts.utterances[i].at`(ISO 8601) | `facts.moves[].ply`・`spentSec` |
| speaker | `facts.utterances[i].speaker`(符号。実名は入れない) | `customerRef`(符号だけ。H-8) |
| utterance(原文) | `facts.utterances[i].text`(正規化は NFKC を 1 か所で) | `facts.engine[].sfen`(原文) |
| numeric value | `facts.numbers[i].{value, unit, utteranceRef}` | H-1「文に出る数は観測にある数だけ」 |
| date | `facts.dates[i].{iso, utteranceRef}`(ISO だけ。「来週」は入れない) | `check_structure.TODAY_RE`(ISO だけを通す) |
| proper noun | `facts.entities[i].{name, registryId}` + `definitions[]`(登録簿) | `facts.recognition.{rows,definitions}` + H-10/H-11 |
| source locator | `src`(ファイル + 行/オフセット) | `src`・`provenance.sources[].inputPaths`・`inputs[].sha256` |
| aggregates | `{id, population{from,where,unit}, numerator/denominator or value, derived_from}` | 現行の `AggregateRow` そのまま(from の値域だけ変わる) |

| Core が**自動検証すべきでない**もの | 現行での扱い(そのまま持ち込む) |
|---|---|
| 文脈依存の表現(「来週」「あれ」) | packet に入れない。席が書けば `kind: "needed_observation"` か `unanswerable`(hypothesis v0.4)。**席は `unanswerable` を選ばず `partial` に逃げる**(記憶 `seats-escape-to-partial`)ので**止めるのは検証器**(`STATUSES_NEEDING_OBSERVATION` に `neededObservation` を要求) |
| 因果関係・評価・解釈 | `factOrHypothesis: "hypothesis"` に限定。顧客向けは断定しない形(H-5) |
| 「誰が正しいか」 | `integration.contradictions` に**並べて消さない**。一致を証拠にしない(`SEAT_COUNT_REFERENCE_RE`) |

**UNVERIFIABLE との関係**: 現行は `unanswerable`(kind と status の両方)と `needed_observation` が「答えられない」の正式な結果で、`answerSelection.STATUSES_NEEDING_OBSERVATION` が「何を測れば答えられるか」を必須にする。Meeting でもこの 3 語を**そのまま使う**(新しい語を作らない)。

**境界の検証に使う最小の問い**: Core の `verify(packet, claims, spec)` が、`spec` を Meeting 用に差し替えるだけで H-1・H-2・H-8・H-9・H-10 が動くか。動かない検査があれば、その検査に将棋が残っている。

---

# 7. 段階的移行手順(将棋を壊さずに Core を切り出す)

**順序の原則(現行コードから)**: (a) 葉(import が無い module)から切る。(b) 切るたびに**既存の 2 本の門 + §5 の Golden Master**で回帰を取る。(c) 逆依存は**削るのではなく注入に替える**(動きが変わらないことを G-2・G-5・G-9 で測る)。(d) ファイルの移動は最後(移動は diff を読めなくし、並行セッションを壊す)。(e) 別セッションが触っている `fillTexts*`・`exit_fill.py` は束が閉じるまで対象外。

| Phase | やること | 完了の測り方 | 動きを変えるか |
|---|---|---|---|
| **0 現状固定** | §5 の G-1〜G-18 を記録する。特に **G-9(門の判定一覧)を初めて書き出す**: `exit_gate`・`check_answer`・`check_structure`・`hypothesisCheck`・`seatOutputCheck`・`integrationCheck` を c5 の実物に当て、rc と落ちた項目の一覧を保存。PDF は `compare_render.py --seal`。packet は `packetId` と `observationPacketProblems` 0 件。**実物を追跡するかは人間の判断**(§5 冒頭) | 記録ファイルが揃い、同じ入力で 2 回回して一致 | 変えない |
| **1 Core 候補抽出(境界の試験)** | **I-1**: Core 候補(§3 結論の TS 8 本 + Python 3 本と、[A′] の一覧)について「`shogiops`・`apps/server`・`report-pdf`(Python 側は `board_*`・`move_text`・`render_*`)を import しない」を**静的走査の試験 1 本**で固定(新規ファイル 1 本。既存は触らない)。[A′] は**既知の例外として名指し**し、Phase 2 で 1 本ずつ外す(外したら試験の例外から消す ― 「消し忘れ」が赤になる向き) | 試験が緑。例外の一覧 = §3.1 の表と一致 | 変えない |
| **2 依存方向の確立(注入に替える)** | **I-2** `hypothesis.ts`: `SEARCH_COLUMNS` の import を `loadObsRegistry(mdPath, extraIds)` の引数に(呼ぶ側 `hypothesisCheck.ts` が将棋側から渡す)。`BANNED_WORDS` は **JSON ファイル 1 本**に出し、`check_answer.py`・`check_delivery.py`・`hypothesis.ts` の 3 か所が同じファイルを読む(「一覧は 1 か所」の意図を保つ)。**I-3** `observationProvenance.ts`: `toolThresholds()` を引数 `thresholds: ThresholdRow[]` に。**I-4** `observationAggregates.ts`: `ROW_DEFINITIONS`・`aggregateAgreementProblems`・`Booklet*` を将棋側 module(例 `lib/shogiAggregates.ts`、名前は実装担当)へ**写してから**元を re-export に(写し→照合→元を削る、の順。記憶 `restore-by-replace-lands-elsewhere`)。`PopulationFrom`/`AggregateUnit` を `string` 系の generic に。**I-5** `observationPacket.ts`: `timeLimitProblems`・`requestAgreementProblems`・`aggregateAgreementProblems` の呼び出しを `observationPacketProblems(packet, schema, spec)` の `spec` 経由に。**I-6** `packetRef.ts`: 列の集合を `makePacketRefGrammar(columns, nested)` で作る形に(既定値を現行の 7 列にして呼び出し側を変えない)。**I-7** Python: `check_answer.py` の走査層(1554〜1841 行の `strip_dev_section`〜`check_answer`)と印の正規表現・`scan_numbers` を別 module(例 `text_claims.py`)へ写し、`check_answer.py`・`exit_gate.py` はそこを import。**I-8** `exit_gate.py` の `check_agg_tags`・`check_ans_tags`・`number_claims` を同じく別 module へ。**I-9** `seatOutput`/`integration` の `SEAT_EXCLUDED_INPUTS`・`INTEGRATOR_EXCLUDED_INPUTS` を設定へ。**各 I ごとに 1 コミット**、各コミットで Phase 0 の G-2・G-5・G-9・G-15 が不変 | 各 I の後で (1) 2 本の門が緑 (2) G-9 の判定一覧がバイト一致 (3) Phase 1 の例外一覧から当該 module が消えて試験が緑 (4) **両向きの変異**(注入を外すと赤・注入を壊すと赤) | **変えない**(動きが同じことを G-9 で測る)。注入の既定値は現行の値 |
| **3 Shogi Adapter 接続** | 将棋側の `spec`(§4.2 の要素)を 1 か所(例 `lib/shogiSpec.ts` + `report-pdf/shogi_spec.py`)に束ね、CLI(`hypothesisCheck`・`seatOutputCheck`・`integrationCheck`・`observationPacket`・`exit_gate`・`check_structure`)がそれを渡す。`deliver.ts` の段表は触らない | 門 2 本 + G-9 不変 | 変えない |
| **4 Golden Master 回帰** | Phase 0 の記録と全項目を比較(G-2 packetId、G-5 判定、G-7 md の門、G-8 の 3 つの数、G-9 一覧、G-14 閾値)。**別の顧客の実物が 1 つでもあれば 2 組で回す**(記憶 `verify-peer-claims-and-path-coverage`: 回帰は問題の経路を通る材料で) | 全項目一致。違えば Phase 2 の該当 I に戻る | ― |
| **5 Meeting Adapter(最小)** | §6.4 の packet を**合成データ**で 1 つ作り、`verify(packet, claims, meetingSpec)` を H-1・H-2・H-8・H-9・H-10 に通す。文は書かない・組版しない・LLM は呼ばない | 動かない検査の一覧 = Core に残った将棋(それを Phase 2 に戻す) | 将棋側は変えない |
| **6 独立監査** | 監査担当が Phase 1 の境界試験・Phase 2 の変異・Phase 4 の回帰を**実物で**再現(記憶 `freeze-before-audit`: 監査に出したら凍結。diff は scratchpad に写す) | GO/REVISE | ― |
| **(その後)** ファイル移動・新リポジトリ(§6.3) | Phase 6 の GO の後。移動は `git mv` で 1 コミット 1 方向 | 門 2 本 + G 全部 | ― |

**より安全な順序として現行から変えた点**: 指示文では Phase 1「Core 候補抽出」が切り出しを含むが、ここでは **Phase 1 を「境界の試験を置くだけ」**にし、切り出し(注入への置き換え)を Phase 2 に寄せた。理由は (1) 現行の Core 候補が全部「機構は汎用・値は将棋」の混在で、抽出 = 注入化と同義であること、(2) 注入化は 1 本ずつ測れるが、まとめて動かすと G-9 のどの差がどの I のせいか分からなくなること。

**やらないこと(移行中)**: 新しい判定・閾値・文言を作らない / schema の版を上げない(欄名 `origin.kifu` 等の改名は**契約の版上げ = 人間の承認**。Phase 2 では触らない) / `deliver.ts` の段を増減しない / LLM を呼ばない。

---

# 8. 次に人間が GO を出すべき実装タスク

| # | タスク | 規模 | 前提 | 人間が決めること |
|---|---|---|---|---|
| **T-1** | **Phase 0: Golden Master の記録**(§5 G-2〜G-9 を c5 の実物で書き出す。門の判定一覧 G-9 を初めてファイルにする) | 小(道具は既存。新規は記録ファイルと手順書) | `out/c5/` の実物が手元にあること(`ls` で確認済み) | **実物(packet・席の出力・md・PDF)を追跡するか、sha と数だけを追跡するか**(§5 冒頭。個人情報を含む) |
| **T-2** | **Phase 1: 境界の試験 1 本**(Core 候補が将棋側を import しないことの静的走査。[A′] は名指しの例外) | 小(試験 1 本) | T-1 | 例外の一覧(§3.1)を承認 |
| **T-3** | **Phase 2 の I-2**: `hypothesis.ts` の 2 本の逆依存(`SEARCH_COLUMNS` の import、`check_answer.py` のソースを正規表現で読む `BANNED_WORDS`)を注入と JSON 化に替える | 中(TS 1 本・Python 2 本・試験) | T-2 | 禁止語の一覧を JSON に出すこと(「一覧は 1 か所」は保たれる)。**今は空の一覧**なので動きは変わらない |
| **T-4** | **Phase 2 の I-4・I-5・I-6**: `observationAggregates`(`ROW_DEFINITIONS`・整合関係の分離)・`observationPacket`(3 検査の注入化)・`packetRef`(列の注入化) | 中〜大(packet 検証の中核。変異両向き) | T-3 | 将棋側の `spec` の置き場(1 か所)の名前 |
| **T-5** | **Phase 2 の I-7・I-8**: Python の走査層(`scan_numbers`・印の文法・`check_agg_tags`・`check_ans_tags`)を `check_answer.py`/`exit_gate.py` から別 module へ(写し→照合→元を re-export) | 中(Python 2 本 + 試験。`reportPdfPythonTests` のスナップショット更新 = 人が `-u` で承認) | T-2(T-3・T-4 とは独立に進められる) | 新しい試験ファイル名の承認(スナップショットが赤になる向き) |

T-3〜T-5 は互いに独立(別の module)なので、席が複数あれば並行できる。ただし**各 I ごとに G-9 の一致を測ってからコミット**し、「直したはず」で次へ進まない(CLAUDE.md 承認の委任・条件 3)。Meeting Adapter(Phase 5)と新リポジトリ(§6.3)は、T-1〜T-5 と Phase 4 の回帰が緑になるまで着手しない。
