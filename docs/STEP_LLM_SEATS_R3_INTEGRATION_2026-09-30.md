# STEP R3 ― 統合(整理役)の契約: `integration_input.v0.1` + `integration.v0.1` + 検査(3 席 LLM API の 3 つ目の束。2026-09-30、実験席)

**位置づけ**: [PLAN_LLM_SEATS_API](PLAN_LLM_SEATS_API_2026-09-30.md) §4(一致を証拠にしない統合)と §8.1 の合わせ 3 点(clusterId・packetRef.path の文法・seatOrderRef)。R1(render、dfa7047)・R2(席の出力の契約、5a19060)の次。**LLM は呼ばない**(整理役の呼び出しは callSeat と同じく鍵の後 = R4)。この束は「整理役に渡す器」「整理役が返す器」「返ったものを機械で落とす検査」だけ。独立監査つき・パス指定(または index に blob)コミット。

## 0. 顧客の PDF にどう出るか(先に書く)

**今は何も変わらない。** 固定するのは、3 席の出力を 1 つにまとめる工程の**器の形**。ここで決まる線は 3 つ: (1) 整理役は席の名前を知らない(`seatIndex` だけ)、(2) 一致の数(`seatCount`)は記録であって証拠ではない(`evidence: false` が固定値で入り、検証器・採用はこの欄を読まない)、(3) 席の項目は黙って消えない(`clusters ∪ dropped` が全項目)。将来、採用された行から席の原文へ戻る道の **3 つ目の輪**(統合 → 席の項目 → 席の原文)が固定される。

## 1. 作るもの

| 物 | 場所 | 中身 |
|---|---|---|
| 器(入力) | `schemas/integration-input.v0.1.schema.json` | §2。`internal` の欄を**持たない**(`additionalProperties: false` で存在自体を拒む ― 人間の決定「参照できない」) |
| 器(出力) | `schemas/integration.v0.1.schema.json` | §3 |
| 整理役が書く形 | `schemas/integration.llm.v0.1.schema.json` | 出力のうち LLM が書く欄(clusters・contradictions・dropped・answersByQuestion・forVerification)。`seatOrderRef`・`evidence`・`runId`・`representative` の道具の欄は道具が埋める |
| lib | `lib/integration.ts` | `buildIntegrationInput(envelopes[], {request, packetDigest, order})`(封筒 → 器。席名を伏せ順を並べ替える。`internal` を**構造で落とす**: 器の schema に欄が無いので、写す関数は許した欄だけを写す)、`completeIntegration(llmJson, ctx)`(整理役の形 → 出力。決定的)、`integrationProblems(output, input, {meta, request, today, registry})`(§4 I-1〜I-8) |
| 試験 | `lib/integration.test.ts` | §5 |
| CLI | `scripts/playtest/integrationCheck.ts` | `--integration <json> --input <integration_input.json> --meta --request --today` |
| 記録 | LOG §9 | ― |

## 2. `integration_input.v0.1`(整理役に渡すもの)

```
{ contract: "integration-input", schemaVersion: "0.1", runId, packetId, packetSha256?, requestSha256,
  seats: [ { seatIndex: 1, present: true,  items: [ 席の行の写し(§2.1) ], answers: [...], omissions: [...] },
           { seatIndex: 2, present: false, reason: "reach_failed | no_key | schema_failed | error" },
           { seatIndex: 3, present: true,  items: [...], answers: [...], omissions: [...] } ],
  packetDigest: { thresholds: [...], aggregates: [ { packetRef: "aggregates.<id>.numerator", value, name?, unit } … 37 行 ], games: [ {gameId, side, result, totalPlyCount} … ] },
  request: { customerQuestions: [...], requestedScope: {...} },
  seatOrderRef: "run ログの中の対応表の名前(席の名前そのものは持たない)" }
```

### 2.1 席の行の写し(許した欄だけ)

`hypothesisId`・`kind`・`factOrHypothesis`・`lane`・`statement`・`observations[]`(`obsId`・`path`・`value`・`unit`・`derived`・`packetRef`)・`counterEvidence`(`attempted`・`items`・`result`)・`prediction`・`requestRef`・`actionCandidate`・`neededObservation`・`origin.itemId`。**写さない**: `internal`(器に欄が無い)・`origin.seat`(席名)・`subject`・`knowledge`・`provenance`・`status`(道具の欄。整理役の判断に要らない)。`selfComputedNumbers` は席ごとの欄として渡す(隔離のまま。整理役はこれを根拠にできない ― §4 I-6)。

- **席の順は無作為**(`order` は呼び出し側が渡す置換。既定は runId から決定的に作る PRNG ― `lib/prng.ts` があれば使う。試験で「同じ runId なら同じ順、違う runId なら順が変わりうる」を固定)。対応表 `seatIndex → seat` は run のログ(`out/<顧客>/llm-seats/<runId>/seat_order.json`)に書き、器には `seatOrderRef` の名前だけ。
- `packetDigest` は packet の写し(R1 と同じ規則: 値は `JSON.stringify`、数を作らない)。**渡すのは線の組・集計 37 行・局の表だけ**(facts の大きい表は渡さない ― 整理役は数を確かめる側であり、分析し直す側ではない)。
- 空席(`present: false`)は理由つきで残す。他の席の写しで埋めない。

## 3. `integration.v0.1`(整理役の出力。道具が保存する形)

```
{ contract: "integration", schemaVersion: "0.1", runId, seatOrderRef,
  run: { model, modelVersion?, inputSha256, requestedAt, usage, finishReason, attempts },
  clusters: [ { clusterId: "C-001", packetRefs: [ path … ], itemRefs: [ {seatIndex, hypothesisId} … ],
                seatCount: { value: 2, evidence: false },
                representative: hypothesis.v0.4 の行(origin.seat = "integrator"。observations は成員の和集合の部分集合) } … ],
  contradictions: [ { clusterIds: [...], itemRefs: [...], packetRefs: [...], text } … ],
  dropped: [ { itemRef, reason } … ],
  answersByQuestion: [ { questionId, bySeat: [ {seatIndex, status, itemRefs, missing} … ], summary: "answered|partial|unanswerable|mixed" } … ],
  forVerification: [ clusterId … ],
  selfComputedNumbers: [ { seatIndex, value, how, fromPaths } … ] }
```

- `seatCount.evidence` は **schema で `const: false`**(整理役にも道具にも true を書かせない)。
- `representative` は v0.4 の行。`hypothesisId` は道具が `H-<customerRef>-integ<runId 先頭 4>-<連番>` で埋め、`origin: {seat: "integrator"}`、`provenance.inputs` は席の行の id の列(`seat_input:` の sha ではなく `integration_input:<sha>`)。
- `internal` の欄は**どこにも無い**(`additionalProperties: false`)。

## 4. 検査 `integrationProblems`(I-1〜I-8。packet を読まない。実在は H-9)

| # | 見るもの | 落ちる例 |
|---|---|---|
| I-1 全項目 | 入力の全 `hypothesisId`(present の席)が `clusters[].itemRefs ∪ dropped[].itemRef` に**ちょうど 1 回**現れる | 黙って落とした・二重に入れた |
| I-2 束の根 | 各 cluster の `packetRefs` が空でなく、**成員の全員**がその path の少なくとも 1 つを `observations[].packetRef.path` に持つ(同じ数を根拠にしたものを束ねる。文の似ている・似ていないで束ねない) | 根拠の場所を共有しない項目を同じ束に |
| I-3 一致は証拠でない | `seatCount.value` = 成員の `seatIndex` の異なる数、`evidence` = false。**`forVerification` の順が `seatCount` で決まっていない**ことは検査できないので、代わりに `forVerification` に 1 席だけの束も入っていることを**要求しない**が、`seatCount = 3` の束が `forVerification` から外れているときに理由(`dropped` と同じ型の `reason`)が無ければ落とす(逆方向の偏り = 一致した束を黙って外す、も見る) | seatCount を書き間違え・evidence: true |
| I-4 代表の行 | `representative` が `validateHypothesisLine`(v0.4)を全部通り、`observations[].packetRef.path` の集合が成員の和集合の部分集合、`statement` の数が成員の観測の値に在る(H-1 で担保)。`kind` は成員の kind のいずれか | 整理役が数を足した・成員に無い数を書いた |
| I-5 問い | `request.customerQuestions` の id ごとに `answersByQuestion` が 1 行、`bySeat` は present の席ごとに 1 行、`summary` は bySeat の status から機械で決まる(全部同じならその値、違えば `mixed`。**多数決で unanswerable を消さない**: 1 席でも unanswerable なら `mixed` か `unanswerable`) | 席の「答えられない」を落とした |
| I-6 隔離 | `selfComputedNumbers` の値が `representative.statement`・`contradictions[].text` に出ない | 席の作った率を代表の文に |
| I-7 席名 | 出力のどこにも `gpt` / `gemini` / `claude` / モデル名の字が無い(`run.model` を除く)。`seatOrderRef` が在る | 整理役が席を名指し |
| I-8 run | `run.inputSha256` = 入力の sha。`representative.provenance.inputs` が `integration_input:<sha>` を持つ | 別の入力で得た出力 |

## 5. 校正と変異(予測を先に書く)

**校正**: 1 R2 の最小の封筒 3 つ(席 1〜3。うち 1 つは `present: false`)から入力を組み、`internal` が入力に**存在しない**(鍵を歩いて 0)/ 2 手で組んだ最小の出力(束 2・dropped 1・contradiction 1)が I-1〜I-8 を通る / 3 同じ runId で入力が 2 回とも同じ(順も同じ)、runId を変えると順が変わりうる(試験は「対応表が違う」を 1 例で見る)/ 4 packet を読まない(import の一覧)。
**変異**(それぞれ 1 件): 項目を clusters からも dropped からも落とす → I-1 / 根拠の場所を共有しない項目を束に → I-2 / `evidence: true` → schema / `seatCount.value` を +1 → I-3 / 代表の statement に成員に無い数 → I-4(H-1)/ 1 席 unanswerable なのに summary を answered → I-5 / 隔離欄の数を contradiction の text に → I-6 / representative に `origin.seat: "gpt"` → I-7 / 入力に `internal` を入れる → 入力の schema で落ちる(構造で拒む)。

## 6. 触らないもの

R1・R2 のコード(`packetRef.ts` の文法は読むだけ)・packet の道具と schema・冊子・`deliver.ts`・`answer_menu.json`・指示文 v1・`OBSERVATION_ITEMS.md`。**LLM を呼ばない・鍵を読まない・packet を読まない**(`packetDigest` は R1 の render と同じ写しの規則で、入力を組む側が packet の JSON を受け取って写す ― 検査は読まない)。

## 7. 決めていない点(司令塔へ)

1. **`packetDigest` の範囲**: 線の組・集計 37 行・局の表(案)。facts の大きい表を渡さないことでよいか(整理役は「数を確かめる側」)。
2. **I-3 の逆方向**: `seatCount = 3` の束を `forVerification` から外すときに理由を要求する(案)でよいか。一致を証拠にしない、は「多い方を良いとしない」だが、「多い方を黙って捨てる」も偏りなので両方向を見る。
3. **整理役の指示文**(付録)は R4(呼び出し)で司令塔が見る。この束では器だけ。
4. 席の順の置換を runId から決定的に作る(案)か、run ごとに真の乱数にして対応表だけ残すか。決定的だと再現できるが、同じ runId を使い回すと順が同じになる。案は**決定的**(再現を優先。runId は実行ごとに新しい)。
