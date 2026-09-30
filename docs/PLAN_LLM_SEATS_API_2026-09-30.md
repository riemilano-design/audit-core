# 計画 ― 3 席 LLM API(GPT / Gemini / Claude に同一入力・構造化出力)― 次世代パイプラインの 2(2026-09-30、実験席)

**位置づけ**: [NEXTGEN_PIPELINE_BRIEF](NEXTGEN_PIPELINE_BRIEF_2026-09-29.md) §3 の 2。**計画だけ**(司令塔の依頼、人間の合図「進めて」2026-09-30)。実装は 1(Observation Packet、自動化レーン)の schema が固まってから。
**触らないもの**: 冊子・`deliver.ts`・`report-pdf/`・`out/c5/deliver1/` の封。CLAUDE.md(規則 8 (3) の内部での緩和は人間の承認の後)。
**前提にした実物**: 実験 1・2 の記録 [LOG](EXPERIMENT_LLM_DISCOVERY_25GAMES_LOG.md)(§1.5 束の穴・§2.1 入力到達・§2.2 束に無い数・§6.2 独立性の保留)、契約 [hypothesis.v0.3](../scripts/playtest/schemas/hypothesis.v0.3.schema.json) と検査 H-1〜H-8(`scripts/playtest/lib/hypothesis.ts`)、束 `bundle.md`(405,344 字。§7 候補 5 つ = 215,023 字で全体の 53%、§8 読み直し = 79,647 字で 20%)。

**この計画で決めること 5 つ**(司令塔の依頼の (1)〜(5))と、**人間・司令塔に決めてもらうこと**(§7)。数は「見込み」と「実測」を分ける。実測は 1 つも無い(まだ 1 回も API を呼んでいない)。

---

## 0. 一枚の絵

```
packet.json ─┐                                        (事実。数はここだけ)
             ├─ render(抽出だけ) → seat_input.md ── 同一バイト ──┬→ GPT 席   ─┐
request.json ┘   + 固定の指示文            (sha256 を記録)        ├→ Gemini 席 ─┼→ seat_output.v0.1(構造化) ×3
                                                                  └→ Claude 席 ─┘        │
                                                                                          ▼
                                                              席の名前を伏せて並べる → 整理役(LLM、4 回目の呼び出し)
                                                                                          │ integration.v0.1
                                                                                          ▼
                                                     機械検証(H-1〜H-8 + packet 照合 + 語彙 + 分母。3 = 自動化レーン)
                                                                                          │
                                                                        採用可能な候補(検証済み ≠ 採用)→ 司令塔 → 人間
```

- LLM は **4 回**呼ぶ(席 3 + 整理役 1)。どの呼び出しも**新しい文脈**(会話履歴なし)。
- **数は packet から引くだけ**。席の出力に「数を書く自由欄」は無い(§2)。席が自分で作った数は専用の欄に隔離し、採用候補にしない(§5.3)。
- **一致は証拠にしない**。整理役の出力に「何席が言ったか」は残るが、検証器はそれを読まない(§4)。

---

## 1. 入力 ― packet + request を同じ形で 3 席に渡す(依頼の (1))

### 1.1 席に渡すもの = 1 本のテキスト `seat_input.md`(抽出だけで作る)

実験 1・2 の `bundle.md` / `request.md` の型を引き継ぐ。作るのは道具 `renderSeatInput`(packet.json + request.json → md)。**再計算・丸め直し・欠損の補完をしない**(実験 1 の `build_bundle.py` と同じ規則。`v()` は `json.dumps` の写し)。

| 順 | 節 | 中身 | 出どころ | 周をまたいで変えるか |
|---|---|---|---|---|
| 1 | 指示文(固定) | 守ること(数え直さない・束に無い数の印・目的を統合出力に書かない・名前は認識の id だけ・「答えられない」も結果)、出力の形(§2)、末尾の合言葉の写し方(§1.3) | この計画の付録 A | **変えない**(周をまたいで席の答えを比べるため。実験 1 の依頼文を土台にする) |
| 2 | request | `customer_questions[]`(問い id・本文)・`requested_scope`(局の範囲・持ち時間の組) | request.json | 顧客ごと |
| 3 | packet §0 読み方 | 鍵の意味・閾値(仮置きの値である旨)・手数の 2 種類・USI の読み方・**定義の中身**(認識の `recognition_pattern` など、席が照合に使うもの ― 実験 1 の穴 §1.5 を塞ぐ) | packet.provenance・packet.facts.recognition.definitions | packet の版ごと |
| 4 | packet §1〜 | 局の表 → 時間 → 崩れ → 分かれ道(直接の答え)→ 認識 → 指し手 → 候補 5 つ → 読み直し(**小さい節を先、大きい表を後**) | packet.facts / aggregates | packet の版ごと |
| 5 | 末尾 | `(束はここまで。合言葉: <run_id の先頭 8 桁>)` | 道具が生成 | 実行ごとに変わる |

- **同一バイト**: 3 席に送る本文は同じファイル 1 本。sha256 を記録し、各席の API 送信ログにも同じ sha を書く(実験 1 は貼り付けだったので「同じ文」を人間の申告で担保していた。API では機械で担保する)。
- **request は packet に混ぜない**(人間の直し 5)。seat_input.md の中でも節を分け、request の節に「この問いに合わせて事実の作り方を変えていない」と固定文で書く。
- **顧客の名前・相手の名前は入れない**(`〇〇さん`・棋譜のヘッダは開かない)。packet 側の規則でもあるが、render の側でも人名の検査(H-8 と同じ一覧)を掛けてから送る。
- **顧客の符号は載せてよい**(監査の条件、2026-09-30、束 B 5eda3c7): packet の `customerRef`(符号だけ。例 `c5`)と、`provenance.inputs[].path` の中の同じ符号(`out/c5/...`)は**同じ扱い**とし、どちらも seat_input.md に写してよい。実名は元から packet に無い(符号は実名ではない)ので、render の人名検査(H-8 の一覧)は符号を止めない。逆に、符号以外の識別子(メールアドレス・対局サイトの ID・棋譜のヘッダの語)が path や値に混ざっていれば render は止まる。

### 1.2 大きさの扱い(入力の切れ ― 実験 1 の席 C が §11 に届かなかった)

実験 1 の束は 405,344 字(概算 13 万トークン)。送る前に **各社の count-tokens API で数え**、その席の入力上限 − 出力の取り置き(3 万トークン)を越えるなら送らない(送って切れるより、送らないで「席なし」と記録する方がよい ― §5.1)。

| 選び方 | 中身 | 採るか |
|---|---|---|
| (a) 全部を 1 回で | 小さい節を先、大きい表(候補 5 つ・読み直し)を後に置く。上限は各社の count-tokens で機械確認 | **基本版はこれ**。実験 1・2 と同じ型で比べられる |
| (b) 大きい表を要約 | §7.2(分かれ道でない局面)の候補 2〜5 番目を省く(実験 1 で既にやった) | (a) の中で採る(packet の写しを落とすので、落としたものは §0 に列挙) |
| (c) 席が packet を引く(function calling で局面を取りに行く) | 上限を気にせず全局面を渡せる | **上位版**。基本版ではやらない(会話が多段になり、席ごとに見た範囲が変わって「同一入力」が崩れる) |

### 1.3 入力到達の機械検査(実験 1 §2.1 の欄を自動に)

- 出力の必須欄 `reach.passphrase` に末尾の合言葉を写させる。合言葉が一致しなければ**届いていない**として、その席の出力は比較・統合に入れない(埋め直さない)。
- 加えて `reach.sections[]` に「読んだ節の番号と、その節の最後の鍵名」を写させ、render 側の目次と機械で照合する(実験 1 では席の引用を人が見て判定した)。
- 合言葉は実行ごとに変える(前の実行の答えを写しても通らない)。

---

## 2. 出力の構造 ― `hypothesis.v0.4` + 席の封筒 `seat-output.v0.1`(依頼の (2))

### 2.1 方針

- **契約の版を 1 つ上げる(v0.3 → v0.4)。v0.3 の行はそのまま v0.4 として通る(足すだけ、消さない・変えない)**。検査 H-1〜H-8 は版によらず同じ(`lib/hypothesis.ts` の作り)。
- 席の出力は **1 本の封筒 `seat-output.v0.1`** で、中身の各項目が v0.4 の行。封筒には席・モデル・入力の sha・到達・自分で作った数の隔離欄が付く。
- 縛るのは **出力形式・事実と仮説の区別・安全性** の 3 つだけ(人間の直し 2)。内部の分析(手の目的の推測を含む)は `internal.reasoning` に自由に書いてよいが、**この欄は統合と検証が読まず、顧客側の工程へ渡らない**(**参照できない**、の形で: 統合の入力・回答生成・組版の入力 schema に `internal.*` をそもそも含めず、`additionalProperties: false` で存在自体を拒む。「写さない」規則ではなく器の形で漏れ道を消す ― 人間の決定 2026-09-30)。
- **数を書く自由欄は無い。** 数は `observations[].value` に packet の値を写すだけ。文(`statement`・`counterEvidence.items[].text`)に出た数は H-1 で `observations` の値に無ければ落ちる(既存)。**加えて新検査 H-9: `observations[].packetRef` が指す packet の値と `value` が一致する**(席が「packet にある」と言った数が実在するかを検証器が packet を開いて確かめる。実験 1 §2.2 の「束に無い数の照合」を自動に)。

### 2.2 `hypothesis.v0.4` で足す欄(全部 optional。v0.3 に無い欄は「無くてもよい」、あれば検査が見る)

| 欄 | 型 | 意味 | 検査 |
|---|---|---|---|
| `kind` | enum `finding / hypothesis / answer_candidate / action_candidate / unanswerable / needed_observation` | 項目の種類(人間の直し 2 の 6 つ)。無ければ `hypothesis`(v0.3 互換) | `hypothesis` と `answer_candidate` は `prediction` 必須(H-4)。`finding` は数の写しだけで `statement` は「〜が N だった」の形。`unanswerable` は `reason` 必須 |
| `origin.seat` | enum `gpt / gemini / claude / integrator / human` | どの席が出したか | 統合の出力では席の名前を伏せて `seatIndex`(1〜3) に置き換える(§4.2) |
| `requestRef` | `{questionId}` | 顧客のどの問いに答えるか(`answer_candidate` / `unanswerable` は必須) | request.json に実在する id |
| `observations[].packetRef` | `{path, provenanceId}` | packet の中の場所(`facts.games[3].result` の形)と provenance の id | **H-9**: 検証器が packet を開き、値が一致しない行は落ちる |
| `factOrHypothesis` | enum `fact / hypothesis` | **事実と仮説の区別**。`fact` は packet の値の写しと、その写しからの「〜が N だった」の文だけ。`hypothesis` は読み(H-5 の形) | `fact` の `statement` に「読み・可能性・のでは」を含む → 落ちる。`hypothesis` の `statement` が断定形 → 落ちる(H-5) |
| `actionCandidate` | `{text, derivedFrom: [hypothesisId…], menuMatch: null \| "M1".."M9"}` | 行動候補。承認済みの表(`answer_menu.json`)と同じかどうかは**検証器が後から埋める**(席には表を見せない ― 独立性) | `derivedFrom` が同じ封筒の項目 id を指す。表の外の行動は**内部の記録に残り、人間に上がる**(人間の直し 3) |
| `neededObservation` | `{what, whyNotInPacket, howToMeasure}` | 「packet に無いので答えられない。次はこれを測る」 | 数を含まない(H-1) |
| `internal.reasoning` | string | 自由分析(手の目的の推測・「○○を狙っていたのでは」も可) | **下流から参照できない**(人間の決定 2026-09-30): `integration_input.v0.1`・回答生成・組版の入力 schema はこの欄を持たず、`additionalProperties: false` で `internal` の存在自体を拒む。検証器はこの欄の中身を読まない(禁止語も見ない)。残るのは席の原文 `seat_<x>_raw.json` の中だけ |
| `internal.namesOutsideVocabulary` | string[] | 席が使いたかったが認識の id に無い名前 | 分類・比較に使わない。知識レーン向けの材料に隔離(実験 2 §3 と同じ扱い) |

- `statement`・`counterEvidence`・`prediction`・`knowledge`・`provenance` は v0.3 のまま。`prediction.writtenAt` は実行日(道具が埋める。席には日付を書かせない)。
- `provenance.inputs` は `seat_input.md` の sha と packet の版、`excludedInputs` に `answer_menu.json`・`exit_candidates.json`・本編(H-6 の盲検の記録)。

### 2.3 席の封筒 `seat-output.v0.1`

```
{
  schemaVersion: "0.1",
  run: { runId, seat: "gpt|gemini|claude", model, modelVersion?, inputSha256, requestedAt, usage: {inputTokens, outputTokens}, finishReason, attempts },
  reach: { passphrase, sections: [{section, lastKey}] },
  items: [ hypothesis.v0.4 の行 … ],                       // kind 別に何本でも。0 本でもよい
  answers: [{ questionId, status: "answered|partial|unanswerable", itemIds: [...], reason? }],   // request の問い 1 つにつき必ず 1 行
  selfComputedNumbers: [{ value, how, fromPaths: [...], note }],   // 席が作った数の隔離欄(§5.3)。採用候補にしない
  omissions: [ string … ]                                   // 席が「無い・読めない・判断できない」と申告したもの
}
```

- `answers` は **request の問いごとに必ず 1 行**(「答えられない」を空で済ませない。人間の直し 4)。
- 構造化の掛け方は各社の仕組みを使う(OpenAI: `response_format: json_schema` strict / Gemini: `responseSchema` / Claude: tool_use の `input_schema` で 1 本のツール「submit_seat_output」に強制)。**3 社とも同じ JSON schema を渡す**。各社の strict モードの制約(`oneOf` 不可・`additionalProperties:false` 必須など)に合わせ、封筒の schema は**平らに**書く(ネストは 3 段まで、`oneOf` を使わない)。契約 v0.4 本体の `oneOf`(observations.value)は検証器側で見る。
- 席の出力は**原文のまま**保存する(実験 1・2 と同じ。`out/<顧客>/llm-seats/<runId>/seat_<x>_raw.json` と sha256)。検証器が落とした項目も消さず、判定を横に付ける。

### 2.4 縛らないこと(明記)

- 仮説の本数・粒度・順番。
- `internal.reasoning` の書き方(手の目的の推測、「狙っていたのでは」、将棋の一般知識による読み。**ただし結論の根拠には使えない**: `observations` に packet の値が無い項目は H-1/H-9 で落ちる)。
- 席ごとの温度・思考の長さ(§3.3 で席ごとに固定して記録する。縛るのは「記録する」こと)。

---

## 3. API の呼び方(依頼の (3))

### 3.1 鍵の置き場(人間が置く)

- リポジトリ直下の `.env`(**既に `.gitignore` 済み**: `.env`・`.env.local`)。人間が `chmod 600` で置く。中身は `OPENAI_API_KEY`・`GEMINI_API_KEY`・`ANTHROPIC_API_KEY` と、席ごとのモデル名 `SEAT_GPT_MODEL`・`SEAT_GEMINI_MODEL`・`SEAT_CLAUDE_MODEL`。
- 道具は `process.env` からだけ読む。**鍵をログ・`out/`・記録・エラーメッセージに書かない**(送信ログには鍵の有無だけ `hasKey: true`)。鍵が無い席は「席なし」で記録して他の席は回す。
- 鍵の発行・課金の設定・上限額の設定は**人間の作業**(金銭が動く判断。CLAUDE.md 承認の委任の外)。この計画は「置き場と読み方」だけ決める。

### 3.2 費用の見込み(**実測ではない**。単価は人間が各社の料金表で確かめる)

| 数 | 見込み | 出どころ |
|---|---|---|
| 入力(1 席) | 約 13 万トークン | 実験 1 の束 405,344 字の概算(日本語 + 英数字混在で 3 字 ≈ 1 トークン)。実測は count-tokens で送る前に出す |
| 出力(1 席) | 1〜2 万トークン | 実験 1 の席 A の原文 39,738 バイト(≈ 1.5 万トークン)から |
| 整理役 | 入力 = 3 席の出力(≈ 5 万)+ packet の要約節(≈ 3 万)、出力 1 万 | §4 |
| 1 回の実行(4 呼び出し) | 入力 ≈ 47 万・出力 ≈ 5 万トークン | 上の和 |
| 揺れの実測(§3.3)を含む初回 | 上の 2 倍 | 各席 2 回 |

費用 = 入力トークン × 入力単価 + 出力トークン × 出力単価。**この計画には単価を書かない**(日付で変わる。人間が埋める)。目安の桁として、入力 1M あたり数ドル・出力 1M あたり数十ドルの帯なら、1 回の実行は **数ドル〜十数ドル**の桁になる。上限額を `.env` に `SEAT_COST_CAP_USD` として置き、count-tokens の結果 × 単価(`.env` の `PRICE_*`)が上限を越えるなら送らない。

### 3.3 席ごとの温度・再現性

| 席 | 温度 | 記録するもの | 再現性の測り方 |
|---|---|---|---|
| GPT | 0(推論モデルで温度を受け付けない場合はその旨を記録し既定のまま)。`seed` を渡す(保証ではない) | モデル名・`system_fingerprint`・response id・`usage`・`finish_reason` | 同じ入力で 2 回。項目の `observations[].packetRef` の集合で比べる(文の揺れではなく「どの数を引いたか」の揺れ) |
| Gemini | 0 | モデル名・`modelVersion`・`usageMetadata`・`finishReason` | 同上 |
| Claude | 0 | モデル名・`id`・`usage`・`stop_reason` | 同上 |

- **揺れの床**を先に測る(D-COST の型)。同じ入力で 2 回回し、引いた数の集合の一致率と、`kind` 別の本数の差を記録する。床が分からないまま「席 X と席 Y が違う」を読まない。
- 温度 0 でも同じ出力は保証されない。**「同じ入力・同じ設定で 2 回回した差」を、周をまたいだ比較の誤差の下限として使う**。

### 3.4 失敗時の再試行(埋め直さない)

| 失敗 | 扱い | 上限 |
|---|---|---|
| 429 / 5xx / 接続 | 指数バックオフで再送(同じ入力) | 3 回 |
| 出力が schema を通らない | 検証器の落ちた理由(欄名と理由)を添えて**同じ入力で**もう 1 回。文脈は引き継がない(前の失敗出力を「直させる」会話にしない ― 独立性) | 2 回 |
| 途中で切れた(`finish_reason = length` など) | 出力の取り置きを増やして 1 回 | 1 回 |
| 合言葉不一致(届いていない) | **失敗として記録。席の出力は比較に入れない**。他の席で埋めない | 再試行しない(入力が上限を越えているので、送り直しても同じ) |
| 鍵が無い・モデル名が無効 | 席なしで記録 | ― |

- 失敗した席は**空席**として整理役に渡す(整理役には「この席は無い」と伝える。ほかの席の出力を複製して埋めない)。
- 手で出力を直さない(実験 1・2 の「原文のまま」)。

### 3.5 置き場と道具(実装時の形。いま作らない)

- `scripts/playtest/llmSeats/`(新規): `renderSeatInput.ts`(packet + request → md)・`callSeat.ts`(3 社の薄い呼び出し。SDK は各社公式の npm。**apps/ に入れない**、`scripts/playtest/package.json` の devDependencies)・`seatOutputSchema.json`・`integrate.ts`(§4)・`run.ts`(1 本の入口: render → count → 3 席 → 整理役 → 検証器を呼ぶ)。
- 出力: `scripts/playtest/out/<顧客>/llm-seats/<runId>/`(gitignore)。記録は `docs/` に数と sha だけ(顧客の材料はコミットしない)。
- 型検査は `typecheck:scripts`。**校正**: 既知の正解で 1 本 ― 実験 1 の `request.md` を新しい render で作り直し、旧 `bundle.md` と数の集合が一致することを確かめる(数え方: 束の中の数値トークンの多重集合)。**わざとずらした写しで検査器が捕まることも見せる**(自動化レーン §68 の型)。

---

## 4. 一致を証拠にしない統合(整理役)― 入力の形(依頼の (4))

### 4.1 整理役に渡すもの `integration_input.v0.1`

```
{
  runId, packetSha256, requestSha256,
  seats: [
    { seatIndex: 1, present: true,  items: [...],  answers: [...], omissions: [...] },   // 席の名前(gpt/gemini/claude)は伏せる
    { seatIndex: 2, present: false, reason: "reach_failed" },
    { seatIndex: 3, present: true,  items: [...],  answers: [...], omissions: [...] }
  ],
  packetDigest: packet の §0(読み方・定義)+ aggregates,    // 整理役が数を確かめるため。facts の大きい表は渡さない
  request
}
```

- `integration_input.v0.1` の schema は `internal` の欄を**持たない**(`additionalProperties: false`。`internal` が 1 つでも残っていれば、整理役に渡す前に schema 照合で落ちる)。内部の自由分析は整理役に見せない ― 「削って渡す」ではなく**「渡す器に入らない」**(人間の決定 2026-09-30)。同じ形を回答生成・組版の入力 schema にも掛ける(自動化レーンの 3・4 へ)。
- 席の順は実行ごとに**無作為に並べ替え**、`seatIndex` だけ付ける(整理役が「Claude が言ったから」で重みを付けない)。並べ替えの対応表は run のログに残す。

### 4.2 整理役の出力 `integration.v0.1`

| 欄 | 中身 | 縛り |
|---|---|---|
| `clusters[]` | 同じ packet の場所(`packetRef` の集合)を根拠にした項目の束。`itemRefs: [{seatIndex, itemId}]`、`representative`(v0.4 の行 1 本。整理役が書き直してよいが、`observations` は元の項目の和集合の**部分集合**) | **同じ数を根拠にしたもの**を同じ束にする(文の似ている・似ていないで束ねない ― 実験 1 §3.1 の表の作り方) |
| `clusters[].seatCount` | 何席が入っているか | **記録だけ**。`evidence: false` を固定値で持ち、検証器と採用の段はこの欄を読まない。使い道は「再検証の順番」だけ(人間の言葉: 3 席一致は「再検証する価値がある」の印) |
| `contradictions[]` | 席どうしで逆のことを言った組(同じ `packetRef` から逆の読み) | 両方を残す。整理役が勝敗を付けない |
| `dropped[]` | 束に入れなかった項目と理由 | 席の項目を**黙って落とさない**(全項目がどこかに現れる。検証器が「席の項目 id の全数 = clusters ∪ dropped」を確かめる) |
| `answersByQuestion[]` | 問いごとに、席の `answers` を並べたもの(answered / partial / unanswerable の内訳) | 「答えられない」を多数決で消さない。1 席でも `unanswerable` と言えば理由を残す |
| `forVerification[]` | 機械検証に回す候補(v0.4 の行) | 数は元の項目から写すだけ(整理役も H-1/H-9 を通る) |
| `selfComputedNumbers` | 3 席の隔離欄の和 | 採用候補にしない。自動化レーンへの「packet に足す集計の候補」(実験 1 §3.3 の読み) |

- 整理役も **LLM の 1 席**として同じ縛り(数を作らない・名前は id だけ・断定しない)。整理役の出力も原文のまま保存。
- 整理役の後の**機械検証(3、自動化レーン)**: H-1〜H-8 + H-9(packet 照合)+ H-10(語彙: 文に出た形・戦法の名前が packet の認識の id 一覧にあるか)+ 分母・母集団(自動化レーンの設計)。**通ったものが「採用可能な候補」で、採用ではない**(司令塔 → 人間)。

---

## 5. 実験 1・2 の落とし穴の塞ぎ方(依頼の (5))

| 落とし穴(実物) | 何が起きたか | 塞ぎ方(この計画のどこ) | 塞げないもの |
|---|---|---|---|
| **入力の切れ**(実験 1 席 C が §11 を「無い」と申告。LOG §2.1) | 貼り付けの上限か見落としか束からは判別できなかった | §1.2 送る前に count-tokens で上限を機械確認、越えるなら送らない / §1.3 合言葉 + 節の目次の写しで**到達を機械判定** / 小さい節を先に置く | モデルが「読んだが使わなかった」は判別できない。到達は「末尾まで届いた」までしか言えない |
| **独立性**(実験 2 席 B2 が「本編・付録も確認した」と書き、人間が保留。LOG §6.2) | ブラウザの会話は前の会話・検索・記憶が混ざりうる | §3 API は呼び出しごとに新しい文脈・履歴なし・検索なし。system に他席の出力を入れない / §4.1 整理役には席名を伏せ、順を無作為に / `provenance.excludedInputs` に現行ルートの出力を列挙(H-6) | モデルの学習データに何が入っているかは制御できない。「この席は現行の冊子を知らない」は API でも証明できない ― 記録できるのは「こちらが渡していない」まで |
| **自分で数える**(実験 1 席 A の束に無い数 約 25 か所、うち 2 つ誤り。LOG §2.2) | 席が表を横に拾って和・率を作った | §2.1 数を書く自由欄を無くし `observations[].value` は packet の写しだけ、**H-9 で packet を開いて照合** / §2.3 `selfComputedNumbers` に隔離して印付きで残す(禁止すると文の中に隠れる。逃がし道を作って**採用しない**) / §4.2 隔離欄は自動化レーンへ「packet に足す集計の候補」 | 席が `internal.reasoning` の中で数えるのは止めない(止めなくてよい ― 下流に出ない) |
| **定義の中身が無かった**(実験 1 §1.5 の束の穴) | 席は「draft だから判断できない」で止まった | §1.1 の節 3 に定義の中身(認識の pattern・鍵の意味・閾値)を必ず入れる。render は packet の `definitions` を写す(packet 側に持つよう自動化レーンへ ― §7 の 3) | ― |
| **USI から駒の種類を取り違える**(実験 2 席 B2 の 28 件) | USI に駒の文字が無い | packet の `moves[]` に動いた駒の種類を持つ(SFEN から読める = 抽出。自動化レーンへの依頼、§7 の 3)。render はそれを添える | ― |
| **席が「完全一致」を機械より緩く読む**(実験 2 §6.3) | 判定の定義が席の側で揺れた | 席に判定させない。判定は機械の rows を packet に載せ、席は「機械の判定はこう、私の読みはこう」の形(`factOrHypothesis`)で分ける | ― |
| **周をまたいだ比較**(5 周目〜6 周目の批評席) | 席へ渡す文を変えると周の差が測れない | §1.1 指示文は固定、変えるときは版番号を上げて両方残す / §3.3 揺れの床を先に測る | ― |

---

## 6. 順番と、最初の実行で測るもの

1. **packet の schema が固まる**(自動化レーン、1)を待つ。待つ間にできること: 付録 A の指示文の草案・`seat-output.v0.1` の schema の草案・各社の構造化出力の制約の確認(実装ではなく調べ)。
2. `renderSeatInput` を実験 1 の材料(`out/c5/`)で校正(旧 `bundle.md` と数の多重集合が一致・ずらした写しで捕まる)。
3. **初回の実行 = 実験 1 の再現**(5 人目の 25 局、同じ問い)。人間の中継で得た SEAT_A/B/C と並べる。

### 6.0 3 席で何を比べるか(席ごとの比較の目的。司令塔の依頼 2026-09-30 ― モデル名はこの表を固定した後)

3 席は**同じ入力**を受けるので、席ごとに測る数は同じ 5 つ。違うのは「その席で何の差を見たいか」と「実験 1 のどの席の実測と並べるか」。

| 比較の目的 | 測る数(分子 / 分母) | 席どうしの差が意味すること | 実験 1 の比べる相手 | 揺れの床との関係 |
|---|---|---|---|---|
| **到達率** | 合言葉一致の回数 / 呼び出し回数、`reach.sections` が目次と一致した節 / 全節 | 入力上限の差(同じバイト列を最後まで受け取れるか)。**Gemini 席 ↔ 実験 1 席 C の不達**を再現するかが最初の問い | 席 C 不達(2/3) | 床の外(到達は 0/1 で揺れない) |
| **自分で数える率** | `selfComputedNumbers` の本数 + 文に漏れて H-1/H-9 で落ちた本数 / 項目の全数。漏れた数のうち packet で確かめて誤りだった数 | 指示と schema で数え直しを止められる度合いの差。**Claude 席 ↔ 実験 1 席 A の約 25 か所・誤り 2** | 席 A 約 25 か所・誤り 2、席 B・C は 0 | 同じ席 2 回の差を先に引く |
| **発見の重なり** | `clusters` のうち seatCount = 3 / 2 / 1 の数(整理役の出力。証拠ではなく再検証の順番)と、H を通った項目 / 全項目 | どの席が「現行の本編に無い、packet の値で裏づく」項目を出すか。**seatCount は差の記述に使うだけで、多い方を良いとしない** | 3 席共通 3(本編の観測 3 つ)、現行に無い仮説は席 A に集中(根拠は束に無い数) | 同じ席 2 回で `packetRef` 集合の一致率を測り、席どうしの差がその床を越えるときだけ「席の差」と書く |
| **戦型の問いへの answers** | request の問いごとの `answered / partial / unanswerable` の内訳と、`unanswerable` の `reason` が「packet に無いもの」を指しているか(機械で照合) | 「答えられない」を正式な結果として出せるか、それとも無理に答えるかの差。**GPT 席 ↔ 実験 1 席 B**(独立性の疑いが出た席なので、API では「渡していない」を記録できる) | 3 席とも結論なし(束 §11 に定義の中身が無かった) | 床の外(内訳は揺れを 2 回で記録するだけ) |
| **揺れの床** | 同じ席・同じ入力 2 回の `packetRef` 集合の一致率、`kind` 別の本数の差、`answers` の内訳の一致 | 席の「性格」ではなく、比較の誤差の下限。**これを先に測らない限り、上の 4 行の差を読まない** | ―(未測) | ― |

- 席と実験 1 の席の対応(Claude ↔ A、GPT ↔ B、Gemini ↔ C)は「同じ会社のモデル」という以上の意味を持たせない(実験 1 は貼り付け・API は構造化出力で、条件が違う)。
- 費用・所要は席ごとに記録するが、比較の目的には入れない(人間の上限額が来てから)。

測る数(実験 1 の実測と並べる):

| 測るもの | 実験 1 の実測(比べる相手) |
|---|---|
| 到達(合言葉一致)| 3 席のうち 2(席 C 不達) |
| schema を 1 回目で通った席の数 | ―(実験 1 は自由文) |
| 束に無い数(隔離欄の本数と、文に漏れて H-1/H-9 で落ちた本数) | 席 A 約 25 か所・誤り 2 |
| H-1〜H-9 を通った項目 / 全項目 | 契約に載せられたのは 6 本、載せられなかった 10 |
| 3 席共通の束(clusters の seatCount = 3)の数 | 3(本編の観測 3 つと同じ) |
| 顧客の問い(戦型)への `answers` の内訳 | 3 席とも結論なし |
| 揺れの床(同じ席 2 回の `packetRef` 集合の一致率) | ―(未測) |
| 費用・所要 | ―(未測) |

4. 数を LOG(実験の記録の続き、または新しい `docs/LANE_LLM_SEATS_LOG` ― 司令塔が決める)に書き、司令塔へ報告。**採用の話はしない**(検証済み ≠ 採用)。

---

## 7. 人間・司令塔に決めてもらうこと

| # | 決めること | 実験席の案 | 誰が |
|---|---|---|---|
| 1 | 鍵の発行・課金上限・モデル名(3 席) | `.env` に人間が置く。上限額 `SEAT_COST_CAP_USD`。**人間の答え 2026-09-30: 急がなくていい。実装の段階で各社の現行料金を見て決める。その前に「3 席で何を比べるか」を §6.0 の表で固定する** | 人間(実装の段階で) |
| 2 | Claude 席を API にするか、実験 1 と同じ subagent(セッション内)にするか | **API**(3 席を同じ仕組み・同じ記録で比べるため。subagent は文脈が実験席と同じプロセスで、独立性の記録が弱い) | 司令塔 |
| 3 | packet に足してほしい欄: `facts.recognition.definitions`(認識の pattern と鍵の意味)、`facts.moves[].piece`(動いた駒の種類)、`facts.recognition.rows`(機械の判定) | 自動化レーンの schema に入れる | 司令塔 → 自動化レーン |
| 4 | 契約の版上げ v0.3 → v0.4(足すだけ)と、新検査 H-9(packet 照合)・H-10(語彙)を `lib/hypothesis.ts` に足すこと | 設計判断として司令塔の承認、実装は 3(自動化レーン)と同じ工程で監査 | 司令塔(委任の範囲) |
| 5 | 指示文(付録 A)の固定 | 実験 1 の依頼文を土台に、§2 の出力形式の指定を足した版を v1 として固定 | 司令塔 |
| 6 | 「内部の自由分析(`internal.reasoning`)に手の目的の推測を許す」の文面 | **人間の決定 2026-09-30: 案の方向で承認。ただし「写さない」でなく「参照できない」** ― 下流(統合の入力・回答生成・組版)の schema が `internal.*` を持たず存在自体を拒む(§2.2・§4.1 に反映)。指示文 v1 の 7 行目はそのまま確定(sha 3b09bec2…) | 人間(決定済み) |

---

## 8. 接続設計案 [NEXTGEN_CONNECTION_DESIGN](NEXTGEN_CONNECTION_DESIGN_2026-09-30.md)(fc8a8a8)§5 の提案 S-1・S-2・A-1 への判断(2026-09-30、司令塔の依頼。記録だけ、今は動かさない)

| # | 提案 | 判断 | 実装計画での形 | 前提 |
|---|---|---|---|---|
| S-1 | `answers[].reason` の隣に機械が読める `missing: [{what, howToMeasure}]` | **採用** | `seat-output.v0.1` の `answers[]` に `missing[]` を足す。`status` が `partial` / `unanswerable` のとき **必須**(空配列は不可 ― 「無い」を空で埋めない、H-3 と同じ型)。`items[kind=needed_observation]` は残すが任意にし、正式な置き場は `answers[].missing` に 1 本化(二重に書かせない)。③ の照合(欄で見る): `missing[].what` に packet の `aggregates[].id` または `facts` の欄名が字面で含まれていれば「在るものを無いと言った」で落とす。`what`・`howToMeasure` に数を含めない(H-1) | ― |
| S-2 | seat_input の request の節に `thresholds.id` と `timeLimitSec` を必ず写す(render の規則) | **採用**(§5 の「3 切れと 10 切れを混ぜない」と同じ向き) | render は packet の `provenance.thresholds.id` と `request.requestedScope.timeLimitSec` を request の節の先頭行と seat_input の 1 行目の両方に印字する。**どちらかが無い packet / request は render が止まる**(黙って 180 の線で送らない)。`facts.games[].timeLimitSec` が全部一致することは packet の入口(P-3)が見る前提で、render は二重に数えない(写すだけ) | P-1(`provenance.thresholds`)・R-1(`requestedScope.timeLimitSec` 必須)が束 A・C に入ること ― **P-1・P-2・P-3・R-1 は束 C に入ることが決まった(4c33ed2、司令塔 2026-09-30)ので、前提は満たされる見込み** |
| A-1 | 新契約 `answer-selection.v0.1`(⑤ の出力・⑥ の唯一の入力) | **`integration.v0.1` から流せる。ただし合わせが 3 点** | 下の表 | ― |

### 8.1 `integration.v0.1` → `answer-selection.v0.1` の対応(欄ごとに見た)

| answer-selection の欄 | integration の出どころ | 通るか | 合わせ |
|---|---|---|---|
| `lead.itemRef {seatIndex, itemId}` + `statementSource: "integration.representative"` | `clusters[].representative`(整理役が書き直した v0.4 の行)と `clusters[].itemRefs[]` | **半分**: `itemRef` は席の項目を指すが、`representative` は束(cluster)に属するので、どの束の文かが `itemRef` からは一意に決まらない(1 項目が複数の束に入りうる) | **(i)** `clusters[].clusterId` を足し、answer-selection の `lead` と `p1[]` の参照を `{clusterId}` または `{seatIndex, itemId}` のどちらかで書けるようにする(A-1 への提案) |
| `p1[].aggregateIds` | 項目の `observations[].packetRef.path` | **半分**: いまの計画は `packetRef.path` を `facts.time.bySpent[3].collapsed` の形で例示していて、`aggregates[].id` を機械で取り出す規則が無い | **(ii)** `packetRef.path` の文法を固定: 集計の数は **`aggregates.<id>.numerator` / `.denominator` / `.value`(数ごと。単独の `aggregates.<id>` は受けない ― 司令塔の決定 2026-09-30、H-9 の実測で分子と分母のどちらを引いたかが決まらないため)**、事実は `facts.<列>[添字].欄名…`。文法は `lib/packetRef.ts` の 1 か所。⑤ は `aggregates.` で始まる path から id と part を機械で抜く。指示文 v1 の 5 行目の例も v1.1 でこの形に(sha 取り直しのとき) |
| `answers[] {questionId, status, itemRefs, aggregateIds, neededObservation}` | `answersByQuestion[]` + 席の `answers[].missing`(S-1) | **通る**(S-1 を採るとそのまま写せる) | ― |
| `boards[] {gameId, ply, packetRef: "facts.engine[…]"}` | 採用された項目の `observations[].packetRef` が局面を指す行 | **通る**(項目が局面の path を持つときだけ。持たない項目からは盤を選べない = 既存の門 (iii) と同じ) | ― |
| `actions[] {menuId}` / `humanQueue[]` | 項目の `actionCandidate.menuMatch`(③ が埋める)/ `menuMatch: null` の項目 | **通る** | ― |
| `adoptedBy` | ―(⑤ の人が書く) | integration の外 | ― |
| `internal` 無し・`additionalProperties: false` | integration の入力・出力とも `internal` を持たない(§4.1) | **通る** | ― |
| 席の原文へ戻る道 | `seatIndex` は実行ごとの無作為な番号(§4.1) | **半分**: answer-selection の `itemRef.seatIndex` から原文 `seat_<x>_raw.json` へ戻るには対応表が要る | **(iii)** `integration.v0.1` に `seatOrderRef`(run のログの中の対応表への参照。**席の名前そのものは持たない** ― 整理役に見せないため)を足す。⑤ 以降はログを引いて戻れる |

- (i)〜(iii) はいずれも `integration.v0.1` の欄を足す・path の文法を固めるだけで、§4 の縛り(席名を伏せる・seatCount を証拠にしない・dropped で明示)は変えない。
- 実装の順: packet C(P-1・P-3・R-1)→ render(S-2)→ seat-output(S-1)→ integration(i〜iii)→ 検証器 ③ → answer-selection(A-1、⑤ の束)。この節は計画の変更ではなく**実装計画に入れる項目の記録**。

## 付録 A ― 席への指示文(草案。固定するのは司令塔の承認の後)

- 実験 1 の `request.md` 冒頭の「守ってほしいこと」6 項目を土台にする(数え直さない・束に無い数の印・束以外を根拠にしない・目的を書かない・名前は認識の id だけ・「差がない」も結果)。
- 変える点: (a) 出力は自由文でなく `seat-output.v0.1`(schema は API の構造化出力で渡すので、文では「各欄の意味」だけ書く)。(b) 「手の目的・狙いの推測は `internal.reasoning` にだけ書いてよい。`statement` には書かない」。(c) 「request の問いごとに `answers` を必ず 1 行。答えられないときは `unanswerable` と理由」。(d) 「末尾の合言葉を `reach.passphrase` に写す。読んだ節の番号と最後の鍵名を `reach.sections` に写す」。(e) 「自分で作った数は `selfComputedNumbers` に入れ、`statement` に書かない」。
- 依頼主の本文(実験の指示書 §1〜§7)は request の一部としてそのまま置く(人間の言葉を変えない)。

## 付録 B ― この計画が前提にした数(すべて実験 1・2 の実測。この計画で新しく測った数は無い)

| 数 | 出どころ |
|---|---|
| 束 405,344 字、§7 = 215,023 字(53%)、§8 = 79,647 字(20%) | `out/c5/experiment-llm-25/bundle.md` を節ごとに数えた(2026-09-30) |
| 席 A の原文 39,738 バイト、席 B 21,024、席 C 6,163 | LOG §2 |
| 束に無い数 約 25 か所・誤り 2(席 A) | LOG §2.2 |
| 到達 2/3(席 C 不達) | LOG §2.1 |
| 契約に載せた 6 本・載せられない 10 | LOG §4 |
| 実験 2: A2 一致 43/50・C2 28/50・B2 保留、検査器 253/253 | LOG §6 |
