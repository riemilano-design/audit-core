# STEP R4 ― callSeat: 3 席と整理役の実際の呼び出し・再試行・原文保存・1 回の実行の器(3 席 LLM API の 4 つ目の束。2026-09-30、実験席)

**位置づけ**: [PLAN_LLM_SEATS_API](PLAN_LLM_SEATS_API_2026-09-30.md) §3(API の呼び方)・§6(初回の実行 = 実験 1 の再現)。R1 render(dfa7047)・R2 席の出力の契約(5a19060)・R3 統合の契約(cf9e4cb)の上に、**外へ出る呼び出し**を載せる最初の束。**実行は鍵・モデル名・上限額(人間)が `.env` に置かれてから**。この束の実装(呼び出し層・器・試験)は鍵なしで作り、試験は網に出ない(fetch を差し替える)。独立監査つき・パス指定コミット。

**司令塔の先決め 3 つ(2026-09-30)を規則として固定**: (1) `SEAT_COST_CAP_USD` を越える見込みなら送らない ― 実行前に概算トークン × 単価で止める。(2) 鍵は `.env` からだけ読み、`process.env` 以外に写さない・ログに出さない。(3) 失敗した席は他の席で埋めない(空席として封筒・器に残す)。

## 0. 顧客の PDF にどう出るか(先に書く)

**今は何も変わらない。** 冊子は今のままの数で出る。この束で初めて **3 席の LLM の発見(発見レイヤー)が機械で落とせる形で得られる**が、それは検証(自動化レーンの H-9・H-10・分母)と司令塔の採用(⑤)の前の材料であり、顧客の文には 1 字も出ない。初回の実行は「実験 1 の再現」(計画 §6.0 の表)として測るだけ。

## 1. 作るもの

| 物 | 場所 | 中身 |
|---|---|---|
| 呼び出し層 | `scripts/playtest/lib/llmClient.ts` | 3 社の REST を **Node の `fetch` で薄く**呼ぶ(SDK を足さない: 依存 0・試験で差し替えやすい・鍵の流れが 1 か所)。`callStructured({provider, model, system, user, schema, maxOutputTokens, temperature, seed?}, {fetch, apiKey})` → `{text, json?, raw, usage, finishReason, modelVersion?, requestId?}`。**鍵は引数で受け取り、戻り値・例外・ログに含めない**(例外の文からも `Authorization` 等の値を消す) |
| 構造化の掛け方 | `scripts/playtest/lib/schemaAdapters.ts` | 正本の schema(`seat-output.llm.v0.1`・`integration.llm.v0.1`)を各社の制約に写す: OpenAI strict(全欄 required + 任意の欄は `anyOf [T, null]`・`additionalProperties: false`・`oneOf` を `anyOf` に)/ Gemini `responseSchema`(`nullable`・`additionalProperties` 無し・`oneOf` 無し ― `value` は `type` を外して自由に)/ Anthropic tool `input_schema`(正本のまま)。**返った JSON は必ず正本の検証器(`validateSeatOutputLlm` / `validateIntegrationLlm`)で見直す**(各社の写しは「席がこの形で書きやすくする」ためで、判定は正本だけ)。`null` で返った任意の欄は落としてから正本に掛ける |
| 数え・費用 | `scripts/playtest/lib/tokenBudget.ts` | 送る前の概算: Anthropic `count_tokens`・Gemini `countTokens` は API で、OpenAI は API が無いので `chars/3`(方法を記録)。`estimatedCostUsd = in × PRICE_IN + out × PRICE_OUT`(単価は `.env` の `PRICE_<SEAT>_IN/OUT`、人間が置く)。**cap を越える見込みなら送らず「席なし(cost_cap)」**。実行後は実測の usage で費用を書き直す |
| 1 席の実行 | `scripts/playtest/lib/seatRun.ts` | `runSeat(seat, {seatInput, meta, request, schema, instruction, keys, prices, cap, fetch})` → 封筒(R2 の `completeSeatOutput`)または空席の理由。再試行は §4。原文(`raw` の全 JSON と本文)を保存 |
| 1 回の実行 | `scripts/playtest/lib/seatRun.ts` の `runAll` + CLI `scripts/playtest/runSeats.ts` | render(R1)→ 3 席(順に。並行はしない ― 費用の上限の判定を 1 本ずつ)→ `buildIntegrationInput`(R3)→ 整理役 → `completeIntegration` → R2/R3 の検査 → `run_summary.json`。**どこで止まっても、そこまでの原文と理由を残す** |
| 指示文 v1.1 | `docs/LLM_SEATS_INSTRUCTION_v1.1_2026-09-30.md` | v1 に 3 点(問いの自由分析の 1 句 / packetRef の例を `aggregates.<id>.numerator` の形に / 「第 1 候補」の 1 も H-1 の数に掛かるので数を書かない欄で使う語の注意)。**sha を取り直すのは初回の実行の直前に 1 回だけ**(司令塔 2026-09-30)。文面は司令塔が見てから固定 |
| 整理役の指示文 v1 | `docs/LLM_SEATS_INTEGRATOR_INSTRUCTION_v1_2026-09-30.md` | 席名を知らない前提・同じ packetRef を根拠にしたものを束ねる・黙って落とさない(dropped に理由)・外す束は heldBack に理由(一致の数を理由にしない)・数を作らない・`internal` は無い。司令塔が見てから固定 |
| 試験 | `lib/llmClient.test.ts`・`lib/schemaAdapters.test.ts`・`lib/seatRun.test.ts` | §6。**網に出ない**(fetch は差し替え) |
| 記録 | LOG §10 | 初回の実行の数(§7) |

## 2. 呼び出しの形(3 社)

| 席 | 入口 | 構造化 | 温度・再現 | 記録するもの |
|---|---|---|---|---|
| GPT | `POST /v1/responses`(または chat.completions ― モデルで決まる。`.env` の `SEAT_GPT_MODEL`) | `text.format = json_schema` strict(写し) | `temperature: 0`(推論モデルで受け付けなければ送らず記録)・`seed` | `model`・`system_fingerprint`・`id`・`usage`・`finish_reason` |
| Gemini | `POST …/models/{model}:generateContent` | `generationConfig.responseMimeType: application/json` + `responseSchema`(写し) | `temperature: 0` | `modelVersion`・`usageMetadata`・`finishReason`・`responseId` |
| Claude | `POST /v1/messages` | `tools: [submit_seat_output(input_schema = 正本)]` + `tool_choice` で強制 | `temperature: 0` | `model`・`id`・`usage`・`stop_reason` |
| 整理役 | 上のどれか 1 つ(`.env` の `INTEGRATOR_PROVIDER/MODEL`。案は Claude ― 席と同じ社でもよい: 整理役は席の出力を見る立場で独立性は求めない) | `integration.llm.v0.1` の写し | 同上 | 同上 |

- 入力は **1 通(system = 指示文、user = seat_input.md 全文)**。会話履歴なし・検索なし・他席の出力なし。
- `maxOutputTokens` の取り置き: 席 3 万、整理役 2 万(count-tokens の結果 + 取り置きが上限を越えるなら送らない)。

## 3. 止まる条件(送らない・埋めない)

| 条件 | 扱い |
|---|---|
| 鍵が無い(`.env` に無い)/ モデル名が無い | その席は「席なし(no_key / no_model)」。他の席は回す。**空席は封筒・器に残す** |
| 概算費用 > `SEAT_COST_CAP_USD`(1 回の実行の累計で見る) | 送らない(cost_cap)。**残りの席も送らない**(上限は実行単位) |
| count-tokens + 取り置き > その社の入力上限(`.env` の `SEAT_<X>_INPUT_LIMIT`) | 送らない(input_limit) |
| 指示文の sha が固定値と違う | 実行を始めない(R1 の render が止まる) |
| 席の返答が schema を通らない(2 回目も) | 席なし(schema_failed)。原文は残す |
| 合言葉が meta と違う | 席なし(reach_failed)。原文は残す。**再試行しない**(§4) |
| 整理役が失敗 | `integration` 無しで止め、3 席の封筒と `run_summary` は残す(統合は後から回し直せる ― 入力の器は決定的) |

## 4. 再試行(計画 §3.4 のとおり)

| 失敗 | 扱い | 上限 |
|---|---|---|
| 429 / 5xx / 接続 | 指数バックオフ(1・4・16 秒)で同じ入力を再送 | 3 回 |
| schema 不通過 | 検証器の落ちた理由を添えて**同じ入力で**もう 1 回(会話にしない: 前の出力を「直させる」のではなく、新しい 1 通に「前回はこの欄で落ちた」を足す) | 2 回 |
| 途中で切れた(`length` / `max_tokens`) | 取り置きを 1.5 倍にして 1 回 | 1 回 |
| 合言葉不一致 | 再試行しない(入力が届いていない) | ― |

各試行の原文を `attempt_<n>_raw.json` として全部残す(直す・消すをしない)。

## 5. 保存物(`scripts/playtest/out/<顧客>/llm-seats/<runId>/`、gitignore)

`seat_input.md`・`seat_input.meta.json`(R1)/ `seat_<x>_attempt_<n>_raw.json`・`seat_<x>_raw.txt`・`seat_<x>.json`(封筒)/ `seat_order.json`(seatOrder + itemMap)/ `integration_input.json`・`integrator_attempt_<n>_raw.json`・`integration.json` / `checks.json`(R2・R3 の検査の結果)/ `run_summary.json`(席ごとの状態・usage・費用の概算と実測・所要・sha の一覧)。**鍵・`Authorization` ヘッダ・`.env` の中身はどこにも書かない**(試験が保存物の全文に `sk-`・`AIza`・鍵の値そのものが無いことを見る)。記録(LOG)に写すのは数と sha だけ。

## 6. 試験(網に出ない)

- `llmClient`: fetch を差し替え、3 社の**実物の返答の形**(公開 API の応答例を手で写した fixture)から `text/json/usage/finishReason` を取り出す。429 → バックオフ → 成功、5xx × 4 → 失敗、`length` → 取り置き増、をそれぞれ 1 本。**鍵が例外・戻り値・ログに出ない**(鍵を `sk-test-…` にして全出力を grep)。
- `schemaAdapters`: 各社の写しが**正本の受理集合を狭めない**こと ― 正本を通る fixture(R2・R3 の試験の fixture)が写しでも通る(OpenAI strict は `null` を許すので、`null` を落とす前処理まで含めて往復)。`oneOf` が残っていない・`additionalProperties` が要らない社に残っていない、を機械で見る。
- `seatRun`: 席なし(no_key / cost_cap / input_limit / reach_failed / schema_failed)がそれぞれ空席として封筒・器に残り、他の席で埋めないこと。cost_cap は残りの席も送らないこと。`run_summary` の形。
- 変異: 鍵をログに書く変異 → grep の試験が赤 / cost_cap の判定を外す → 送ってしまう(fetch の呼び出し回数が増える)試験が赤 / 空席を他の席で埋める変異 → I-1 か封筒の試験が赤。

## 7. 初回の実行(鍵が来てから。計画 §6.0 の表で測る)

1. 指示文 v1.1 を固定(sha 1 回)。整理役の指示文 v1 を固定。
2. 5 人目の packet + request(gitignore)で `runSeats` を **1 回**。費用の上限は人間の値。
3. 測る数(計画 §6.0): 到達率 / 自分で数える率(隔離欄 + H-1/H-9 で落ちた数、うち誤り)/ 発見の重なり(seatCount 1・2・3 の束の数 ― 記述だけ)/ 戦型の問いへの answers の内訳 / 費用・所要。**揺れの床は 2 回目の実行**(同じ入力・同じ設定。上限額が許せば)。
4. 数を LOG §10 に、司令塔へ報告。**採用の話はしない**(検証 ③ は自動化レーン、採用 ⑤ は司令塔・人間)。

## 8. 触らないもの

R1〜R3 のコード(読むだけ)・packet の道具・検証器(H-9・H-10 は自動化レーン)・冊子・`deliver.ts`・`answer_menu.json`・CLAUDE.md。**SDK を足さない**(依存 0)。**`.env` を読む場所は `lib/env.ts` の 1 か所**(`process.env` の必要な鍵だけを名前で読む。全部を dump しない)。

## 9. 人間・司令塔に決めてもらうこと

| # | 決めること | 実験席の案 | 誰が |
|---|---|---|---|
| 1 | 鍵・モデル名・単価・上限額・入力上限を `.env` に(`OPENAI_API_KEY`・`GEMINI_API_KEY`・`ANTHROPIC_API_KEY`・`SEAT_GPT_MODEL`・`SEAT_GEMINI_MODEL`・`SEAT_CLAUDE_MODEL`・`INTEGRATOR_PROVIDER`・`INTEGRATOR_MODEL`・`PRICE_*`・`SEAT_COST_CAP_USD`・`SEAT_*_INPUT_LIMIT`) | 実装は変数名だけ決める。`.env.example` をコミットする(値は空) | 人間 |
| 2 | SDK を足さず `fetch` で呼ぶ | 案: fetch(依存 0・鍵の流れ 1 か所・試験で差し替え) | 司令塔 |
| 3 | 整理役の社と席の社が同じでよいか | 案: よい(独立性は席どうしに求める。整理役は席の出力を見る立場) | 司令塔 |
| 4 | 指示文 v1.1 と整理役の指示文 v1 の文面 | 実文を書いて見せる(R1 と同じ手順) | 司令塔 |
| 5 | 揺れの床の 2 回目の実行(費用 2 倍)を初回に含めるか | 案: 上限額が許せば含める。許さなければ 1 回で始め、床は後で | 人間(費用) |
| 6 | OpenAI の count-tokens が無いので `chars/3` の概算で上限を見る | 案: 概算で可(越えたら送らない側に倒れる) | 司令塔 |
