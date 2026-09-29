# STEP R2 ― 席の出力の契約: `hypothesis.v0.4` + 封筒 `seat-output.v0.1` + 席の出力側の契約検査(3 席 LLM API の 2 つ目の束。2026-09-30、実験席)

**位置づけ**: [PLAN_LLM_SEATS_API](PLAN_LLM_SEATS_API_2026-09-30.md) §2・§8(S-1)。R1(render、dfa7047)の次。司令塔の指示(2026-09-30): H-9(packetRef の実在)・H-10(語彙)の **packet 照合は自動化レーンの検証器**なので作らない ― **R2 の試験は packet を読まない**(この計画の §6 に明記)。`answers[].missing` 必須(partial / unanswerable で空配列不可)と `packetRef.path` の文法の契約検査は R2 の範囲。
**LLM は呼ばない**(鍵は無い)。独立監査つき・パス指定コミット。

## 0. 顧客の PDF にどう出るか(先に書く)

**今は何も変わらない。** この束が固定するのは、席の出力を「機械で落とせる形」にする契約と、その検査。将来、席の項目が検証を通り人が採用したとき、本編の文 → 採用された行(`hypothesisId`)→ `observations[].packetRef` → packet の出どころ、と戻る道の **2 つ目の輪**(席の出力の形)が固定される。内部の自由分析(`internal.*`)は封筒の中にだけ在り、下流の器(統合の入力・回答生成・組版)は欄を持たない(人間の決定 2026-09-30「参照できない」。その器を作るのは R3 以降)。

## 1. 作るもの

| 物 | 場所 | 中身 |
|---|---|---|
| 契約 v0.4 | `scripts/playtest/schemas/hypothesis.v0.4.schema.json` | v0.3 の複製に**欄を足すだけ**(§2)。`schemaVersion` const `"0.4"`。古い版のファイルは消さない。`lib/schemaVersions.ts` の `KNOWN_HYPOTHESIS_SCHEMA_VERSIONS` に `"0.4"` を足す(**`HYPOTHESIS_SCHEMA_VERSION` は据え置き** ― v0.2・v0.3 のときと同じ流儀。書く側の既定を変えない) |
| 検査の版分岐 | `scripts/playtest/lib/hypothesis.ts` | H-2・H-4・H-5 に **v0.4 の行だけ**に効く分岐(§3)。v0.1〜v0.3 の行の判定は 1 つも変えない(既存の試験と records で固定) |
| 封筒 | `scripts/playtest/schemas/seat-output.v0.1.schema.json` | 席 1 つの出力(§4)。`items[]` の各要素は v0.4 の行(schema では `type: object` に留め、中身は `validateHypothesisLine` で 1 行ずつ見る ― `lib/eventSchema.ts` に `$ref` が無いため) |
| 席が書く形 | `scripts/playtest/schemas/seat-output.llm.v0.1.schema.json` | 封筒のうち **LLM が書く欄だけ**(§4.1)。`provenance`・`subject`・`knowledge`・`hypothesisId`・`status`・`schemaVersion`・`run` は道具が後から埋める(LLM に書かせない) |
| lib | `scripts/playtest/lib/seatOutput.ts` | `completeSeatOutput(llmJson, ctx)`(席が書いた形 → 封筒。決定的。数を作らない)、`seatOutputProblems(envelope, {meta, request, today, registry})`(§5 の E-1〜E-7 + 各行の H-1〜H-8)、`packetRefPathProblems(path)`(文法だけ) |
| 試験 | `scripts/playtest/lib/seatOutput.test.ts`・`hypothesis.test.ts` に追加 | §6 |
| CLI | `scripts/playtest/seatOutputCheck.ts` | `--seat-output <json> --meta <seat_input.meta.json> --request <request.json> --today YYYY-MM-DD` → 検査の一覧を出し、1 本でも落ちれば終了コード 1(`hypothesisCheck.ts` の流儀) |
| 記録 | LOG §8 | 校正・変異・実測 |

## 2. `hypothesis.v0.4` で足す欄(すべて任意。v0.3 の行は `schemaVersion` を `"0.4"` にすれば**そのまま通る**ことを試験で固定)

| 欄 | 型 | 意味 | 検査 |
|---|---|---|---|
| `kind` | enum `finding / hypothesis / answer_candidate / action_candidate / unanswerable / needed_observation` | 項目の種類。無ければ `hypothesis`(v0.3 互換) | §3 |
| `factOrHypothesis` | enum `fact / hypothesis` | 事実と読みの区別。無ければ `hypothesis` | H-5 の分岐(§3) |
| `origin.seat` | enum `gpt / gemini / claude / integrator / human` | 誰が出したか(統合では席名を伏せて `seatIndex` に置き換える ― R3) | ― |
| `requestRef.questionId` | string `^q[0-9]+$` | 顧客のどの問いか。`answer_candidate` / `unanswerable` は必須 | E-3 |
| `observations[].packetRef` | `{path: string, provenanceId?: string}` | packet の中の場所 | **文法だけ**(§3 の H-2 分岐)。実在は H-9(自動化レーン) |
| `actionCandidate` | `{text, derivedFrom: string[], menuMatch: string \| null}` | 行動候補。`menuMatch` は検証器(自動化レーン)が後から埋める。席は `null` | E-3: `derivedFrom` の id が同じ封筒の項目に在る |
| `neededObservation` | `{what, whyNotInPacket, howToMeasure}` | packet に無いので答えられない・次に測るもの | `unanswerable` / `needed_observation` は必須。文に数を含めない |
| `internal` | `{reasoning: string, namesOutsideVocabulary: string[]}` | 自由分析(手の目的の推測も可)と、定義に無い名前の隔離 | 検査は**この欄を読まない**(禁止語も見ない)。封筒にだけ在る |
| `prediction` | (既存) | v0.4 では **schema 上は任意**にし、H-4 が kind で必須を決める(§3) | H-4 |

`additionalProperties: false` はそのまま。`oneOf` は既存の `observations[].value` 以外に使わない(`eventSchema.ts` の制約と、各社の構造化出力の制約の両方に合わせて平らに書く)。

## 3. 検査の版分岐(v0.4 の行だけ。v0.1〜v0.3 は今のまま)

| 検査 | v0.4 での扱い | 理由 |
|---|---|---|
| H-2(obsId の登録) | `obsId` が `packet.` で始まる観測は、登録簿でなく **`packetRef.path` の文法**で見る: `obsId` = `packet.` + `packetRef.path` であること、path が `aggregates.<id>`(`^aggregates\.[A-Za-z0-9_]+(\.[A-Za-z0-9_]+)*$`)または `facts.<列>[...]...`(`^facts\.(games|moves|engine|time|branches|collapse|recognition)(\[\d+\]\|\.[A-Za-z0-9_]+)+$`)であること。**path が packet に実在するかは見ない(H-9)**。`obs.` で始まる obsId は今までどおり登録簿 | 席は packet の場所を引く。登録簿(`OBSERVATION_ITEMS.md` §1)は既存の出力の欄名で、packet の path は載っていない。**司令塔の判断 1**(§8) |
| H-4(予測) | `kind` が `hypothesis` / `answer_candidate`(または無い)なら今までどおり必須。`finding` / `action_candidate` / `unanswerable` / `needed_observation` は **無くてよい**(あれば今までどおり見る) | 発見・行動候補・答えられないものに「次の 25 局で動く数」を書かせると、無い数を作らせることになる |
| H-5(断定しない形) | `factOrHypothesis: "fact"`(または `kind: finding`)の行は「という読みです / 可能性があります」を**要らない**代わりに、`statement` に「読み」「可能性」「のでは」「と思われ」を含めば落ちる(事実の文に読みを混ぜない)。`hypothesis` の行は今までどおり。禁止語の一覧は両方に掛ける | 事実と仮説の区別(縛るもの 3 つの 1 つ) |
| H-1・H-3・H-6・H-7・H-8 | 変えない | H-1 は `internal.*` を読まないので、内部の推測に数が混ざっても落ちない(仕様どおり) |

## 4. 封筒 `seat-output.v0.1`(道具が保存する形)

```
{ contract: "seat-output", schemaVersion: "0.1",
  run: { runId, seat: "gpt|gemini|claude", model, modelVersion?, inputSha256, instructionSha256, requestedAt, usage: {inputTokens, outputTokens}, finishReason, attempts },
  reach: { passphrase, sections: [{ section, lastKey }] },
  items: [ hypothesis.v0.4 の行 … ],                           // 0 本でもよい
  answers: [{ questionId, status: "answered|partial|unanswerable", itemIds: [...], reason?, missing: [{ what, howToMeasure }] }],
  selfComputedNumbers: [{ value: number, how, fromPaths: [...], note? }],
  omissions: [ string … ] }
```

### 4.1 席が書く形 `seat-output.llm.v0.1`(LLM に渡す schema。封筒の部分集合)

- `items[]` の各要素: `itemId`(席が付ける `S-001` の形)・`kind`・`factOrHypothesis`・`lane`・`statement`・`observations[]`(`obsId`・`path`・`value`・`unit?`・`derived?`・`packetRef`)・`counterEvidence`・`prediction?`・`requestRef?`・`actionCandidate?`・`neededObservation?`・`internal?`。
- `reach`・`answers`・`selfComputedNumbers`・`omissions` は封筒と同じ。
- **道具が埋める欄**(`completeSeatOutput`): `schemaVersion: "0.4"`、`hypothesisId`(`H-<customerRef>-<seat><runId 先頭 4>-<連番 3 桁>` の形。契約の pattern `^H-p[0-9]+-[a-z0-9]+-[0-9]{3}$` に合わせるため `customerRef` の `c5` を `p5` に写す ― **司令塔の判断 2**)、`subject`(customerRef・groups = [meta の持ち時間の組]・gamesCount = meta.games)、`scope: "this_user"`、`status: "proposed"`、`knowledge`(`kind: discovered`・`reviewStatus: draft`・`origin {kifu: <customerRef>, lane: llm-seat}`・`range: this_user`)、`provenance`(`gitHead`・`inputs: [seat_input の sha]`・`excludedInputs: [answer_menu.json, exit_candidates.json, 本編]`)、`prediction.writtenAt`(実行日。席には書かせない)、`origin.seat`。**数は 1 つも作らない**(値を写すのは `meta` の数だけ)。
- 各社の strict モード用の変換(任意欄の nullable 化など)は **R3(callSeat)** の仕事。R2 は「席が返した JSON がこの schema を通るか」まで。

## 5. 封筒の検査 `seatOutputProblems`(E-1〜E-7。**packet を読まない**)

| # | 見るもの | 落ちる例 |
|---|---|---|
| E-1 到達 | `reach.passphrase` = `meta.passphrase`。`reach.sections[]` の各 `section` が `meta.sections` に在り、`lastKey` が meta の `lastKey` と**前方一致**。meta に在って席に無い節は「読めなかった節」として `omissions` に無ければ落ちる | 合言葉違い・節の取り違え |
| E-2 答え | `request.customerQuestions` の id ごとに `answers` が**ちょうど 1 行**。`status` が `partial` / `unanswerable` なら `missing` が **1 件以上**(S-1)。`missing[].what`・`howToMeasure` に数を含めない。`itemIds` は `items` に在る | 問いに答えが無い・空の missing |
| E-3 行 | 各 `items[]` を `validateHypothesisLine`(schema v0.4 + H-1〜H-8 の分岐)に掛け、全部通る。`kind` 別の必須(§3)。`actionCandidate.derivedFrom`・`answers[].itemIds` の参照先が在る。`itemId` は封筒内で一意 | 予測の無い hypothesis・断定した statement |
| E-4 packetRef の文法 | 全 `observations[].packetRef.path` が §3 の文法。`obsId` = `packet.` + path | `facts.time.bySpent[3].collapsed`(v0.1 の packet に無い列 ― 文法で落ちる)・`aggregates[0]` |
| E-5 隔離 | `selfComputedNumbers[].value` の字面が、どの `statement`・`answers[].reason`・`missing` にも出ない(隔離欄の数を文に持ち込まない) | 席が作った率を statement に書く |
| E-6 内部 | `internal` は `items[]` の中にだけ在ってよい。封筒の他の場所(`answers`・`reach` …)に `internal` という鍵があれば落ちる。`items[].internal` は検査が読まない | ― |
| E-7 run | `run.inputSha256` = `meta.seatInputSha256`、`run.instructionSha256` = `meta.instructionSha256`。各行の `provenance.inputs` に `run.inputSha256` が在る | 別の入力で得た出力を混ぜる |

## 6. 校正と変異(予測を先に書く)

**校正(既知の正解)**:
1. 実験 1 の契約 6 本(`records/experiment-llm-25/E-001…E-007`、v0.3)の `schemaVersion` を `"0.4"` に書き換えた写しが、v0.4 の schema と H-1〜H-8 を **全部通る**(足すだけ、の証拠)。予測: 6/6 で 9 検査 ok。元の v0.3 のままの 6 本も引き続き ok(既存の CLI で)。
2. 手で組んだ最小の封筒(席 1・項目 3 = finding / hypothesis / unanswerable・問い 1)が E-1〜E-7 を通る。予測: ok。
3. `hypothesis.test.ts` の既存の試験が 1 本も変わらず緑(v0.1〜v0.3 の判定を変えていない)。
4. **packet を読まない**: `seatOutput.ts` が `observationPacket*.ts` を import しない・ファイルを開かない(試験が import の一覧を見る)。

**変異**(それぞれ 1 件だけ赤くなること):
| 変異 | 予測 |
|---|---|
| `unanswerable` の `missing: []` | E-2 |
| `packetRef.path` を `facts.time.bySpent[3].collapsed` に | E-4(v0.1 の packet に `time.bySpent` の列は無い ― 文法で落ちる。実在の照合ではない) |
| `reach.passphrase` を 1 字変える | E-1 |
| `selfComputedNumbers[0].value` を statement に書く | E-5(H-1 も落ちる) |
| `fact` の statement に「という読みです」 | E-3(H-5 の分岐) |
| `hypothesis` から `prediction` を外す | E-3(H-4) |
| `finding` から `prediction` を外す | **通る**(kind で必須が変わる証拠) |
| `answers` の中に `internal` を置く | E-6 |
| 席が書く形の JSON に `provenance` を入れる | `seat-output.llm.v0.1` の `additionalProperties: false` で落ちる(道具の欄を LLM に書かせない) |

## 7. 触らないもの

`deliver.ts`・`report-pdf/`・packet の道具と schema・`OBSERVATION_ITEMS.md`(登録簿。自動化レーン)・`answer_menu.json`・指示文 v1・R1 の render(`seatInput.ts`。E-1 は meta を読むだけ)・`records/experiment-llm-25/`(校正は写しで)。**packet を読まない・LLM を呼ばない・鍵を読まない。**

## 8. 司令塔に決めてもらうこと

1. **H-2 の分岐**: `packet.` で始まる obsId を「登録簿でなく path の文法」で通す(実在は H-9)。代案は自動化レーンが packet の path を登録簿に載せること(登録簿は自動化レーンの正本なので、そちらを選ぶなら R2 は待つ)。実験席の案は**分岐**(登録簿を packet の欄名で膨らませない)。
2. **`hypothesisId` と `subject.customer` の形**: 契約の pattern は `p[0-9]+`、packet の符号は `c5`。案は `c5 → p5` に写す(数字は同じ、接頭辞だけ)。代案は v0.4 で pattern を `[a-z][0-9]+` に広げる(既存の行はそのまま通る)。実験席の案は**後者**(写しに規則を挟まない)。
3. `kind` が無い v0.4 の行を `hypothesis` と読む(v0.3 互換)でよいか。
4. 席が書く形で `prediction.writtenAt` を道具が埋める(席に日付を書かせない)でよいか(H-4 の「測る前に書く」は実行日で担保)。
