# 将棋側 S-4(unanswerable を契約で言えるようにする + claude 席の封筒を器に届かせる)の計画と予測 ― 直す前に封じる

> **封じた後は本文を変えない。** 訂正は日付つきの追記か結果文書に。予測を当てるために範囲・規則・上限を動かさない。外れは外れのまま記録する。
>
> **前提**: 人間の決定(2026-10-06、S-3 の結果への返答): S-3 は GO、Golden には反映しない、S-3 の外れ 6 つのうち次の判断材料は a4(claude 席の schema 不通)・b5(配列の観測が席 → Core まで届くかは**未検証のまま残す**)・c3(schema が unanswerable を実質封じた = 契約同士の矛盾)。**S-4 = (b) schema の契約変更 + (c) claude 席の v1.4 を同じ封の中で別々の予測にし、独立監査の後に実 run を 1 回だけ。** schema を甘くする(`items2` や文字列の `items` を許す)ことはしない。営業の実証範囲の更新は S-4 の後。
>
> **Base**: `8595b7c`。Core 4 本は `f917f02` から不変。S-3 の実 run `ae40ec51-20261006-1` は `scripts/playtest/out/c5/llm-seats-s3/` に置いたまま(Golden は動かさない)。

## 1. 読んで確かめた事実(S-4 の設計の根拠)

| # | 事実 | どこで |
|---|---|---|
| 1 | `observations` の minItems 1 は **契約 4 本**にある: `hypothesis.v0.4`(項目)、`seat-output.llm.v0.1`(席の tool 用。`items[].observations`)、`integration-input.v0.1`(整理役への入力の `seats[].items[].observations`)、`integration.llm.v0.1`(整理役の出力の `representative.observations`)。`seat-output.v0.1`(器の封筒)には無い | `scripts/playtest/schemas/` を読んだ |
| 2 | 4 本とも `kind` の enum に `unanswerable`・`needed_observation` が在り、項目の `neededObservation`(what / whyNotInPacket / howToMeasure、全部 required)も在る。`required` に `neededObservation` は無い | 同上 |
| 3 | 正本の検証器 `lib/eventSchema.ts` が扱う語は type・enum・pattern・minimum・maximum・minLength・properties・required・additionalProperties(false だけ)・minItems・items・**oneOf・const**。`if/then`・`anyOf`・`$ref` は例外を投げる(黙って見ない、にならない) | `eventSchema.ts` 先頭の注記 |
| 4 | 既に同じ形の前例がある: `hypothesis.v0.4` の `prediction` は「schema 上は任意。**H-4 が kind で必須を決める**」(`KINDS_WITHOUT_PREDICTION` = finding / action_candidate / unanswerable / needed_observation) | `lib/hypothesis.ts:306,534` |
| 5 | 各社向けの写し: OpenAI strict は `minItems` を**元々落としている**(`toOpenAIStrict`)ので gpt の API は minItems を強制していない。落としたのは正本の検証器。Anthropic / Gemini の写しは minItems を残す。Anthropic は `tool_use` の `input_schema`(strict 無し)で、`additionalProperties: false` は API 側で強制されない(S-3 の `items2` が通ってきた理由) | `lib/schemaAdapters.ts`、`lib/llmClient.ts:148-156` |
| 6 | 行の照合に使う版は行の `schemaVersion` が決める(`KNOWN_HYPOTHESIS_SCHEMA_VERSIONS = 0.1〜0.4`)。古い版のファイルは消さない | `lib/schemaVersions.ts:52-54`、`hypothesis.ts:5,661-670` |
| 7 | 再試行の文 `retryUserText` は「落ちた欄と理由」を累積して渡し、前回の出力は渡さない。S-3 の claude は累積を渡されても `items2` ↔ `items` 文字列化を往復した(試行 1・3 が同じ理由) | `lib/seatRun.ts:150-153,213-216`、S-3 結果 §3.2 |
| 8 | 指示文 v1.3 に **`itemId` の形(`^S-[0-9]{3}$`)が書かれていない**。S-3 の gpt の試行 1 は `f1`/`f2`/`f3`/`h1`/`n1` で 5 件落ちた(+ `n1` の観測 0)。schema の pattern を指示文が言っていない | v1.3 全文、`seat_gpt_attempt_1_problems.txt` |
| 9 | 整理役への入力は席の項目を `ITEM_COPY_KEYS`(`neededObservation` を含む)で写す。I-4 は代表の観測が成員の観測の和集合に入ることと kind の一致を見る(観測 0 なら空集合で通る)。I-1 は全項目がちょうど 1 回 | `lib/integration.ts:111,381,430-436` |
| 10 | draft は代表が H 検査に通れば `items` に入れ、`aggregateIds` は観測の packetRef から導く(観測 0 なら `[]`)。採用の契約 `answer-selection.v0.1` の `p1[].aggregateIds` は **minItems 1** = 観測 0 の候補は人が採用しても門が落とす | `lib/exitSelect.ts:66-74,118-137`、`answer-selection.v0.1.schema.json` |
| 11 | Core の経路(`run_core_path_shogi.py`)は観測ごとに Claim を作る。観測 0 の項目は Claim 0 件(落ちない) | `adapters/shogi/recipes.py:143-160` |
| 12 | S-3 の実費 4.5351 USD(gpt 1.5597/2 試行・claude 2.8448/3 試行・整理役 0.1307)、dry-run の見込み 3.19、束 226,568 B。vitest 2333・typecheck 新しい赤 0 | S-3 結果 §2・§3 |

## 2. S-4 の範囲

### 2.1 直す物(3 つ。予測は別々に立てる)

**(b) 契約: 観測 0 を kind で許す**

| 直す所 | 直し |
|---|---|
| `schemas/hypothesis.v0.5.schema.json`(新)| v0.4 の複製で `schemaVersion` const を `0.5`、`observations` の `minItems` を外す。**それ以外は 1 字も変えない**。v0.4 のファイルは残す |
| `schemas/seat-output.llm.v0.2.schema.json`・`integration-input.v0.2.schema.json`・`integration.llm.v0.2.schema.json`(新)| 同じく複製 + `observations` の `minItems` を外すだけ。読み込み先(`seatOutput.ts:36`、`integration.ts:66` の名前、`seatRun.ts:484`)を新版に向ける。v0.1 のファイルは残す |
| `lib/schemaVersions.ts` | `KNOWN_HYPOTHESIS_SCHEMA_VERSIONS` に `"0.5"`。**席の封筒の項目に書く版を 0.5 に上げる定数**(1 か所。実装担当が見つけて報告する) |
| `lib/hypothesis.ts` | 新しい検査 **H-12**(`HypothesisCheckName` に足す): 行の `schemaVersion` が **0.5 以上のときだけ**走る(0.4 以下は skip で ok = 既存の記録と Golden を動かさない)。規則: `kind` が `unanswerable` / `needed_observation` なら `neededObservation` が在って `what`・`whyNotInPacket`・`howToMeasure` の 3 つが空でない文字列(observations は 0 件でよい)。それ以外の kind なら `observations` が 1 件以上。NG の文は `observations が 0 件(kind <kind> には 1 件以上要る)` / `neededObservation が無い(kind <kind> には要る)` / `neededObservation.<欄> が空` |
| 効き先 | `validateHypothesisLine` を呼ぶ 5 か所(E-3・I-4・Golden g9・draft・CLI)に自動で届く。**Core(`audit-core/`)は 0 行** |

**(c1) 指示文 v1.4** = `docs/LLM_SEATS_INSTRUCTION_v1.4_2026-10-06.md`。v1.3 の複製で、変えるのは次の 4 か所だけ(他は 1 バイトも変えない。`diff v1.3 v1.4` がこの 4 ブロックだけであることを監査が見る):

1. 1 行目の版名 `v1.3` → `v1.4`。
2. 21 行目(埋め草禁止の行)の末尾の文「根拠が束に無い項目は `kind` を `unanswerable` にして `neededObservation` を書く。」を次に置き換える: 「根拠が束に無い項目は `kind` を `unanswerable` か `needed_observation` にし、`observations` は**空の配列 `[]`** にして、代わりに `neededObservation`(`what`・`whyNotInPacket`・`howToMeasure` の 3 つ)を必ず書く。それ以外の `kind` の項目は `observations` を 1 件以上写す。」
3. 22 行目(配列の行)の**後ろ**に 2 行を足す:
   - 「- `itemId` は `S-001`・`S-002` … の形(`S-` + 3 桁の連番)。別の形(`f1`・`h1` など)は機械の検査で落ちます。」
   - 「- 出力の最上位の鍵は `reach`・`items`・`answers`・`selfComputedNumbers`・`omissions` の 5 つだけ。**`items` は 1 つの配列で、分けない(`items2` のような鍵を作らない)**。配列を JSON の文字列にして入れない(配列は配列のまま)。」
4. `FIXED_INSTRUCTION_SHA256` に v1.4 の 1 行(古い版は残す)。

**(c2) 再試行の文**(`lib/seatRun.ts` の `retryUserText`): 累積した理由の一覧の**前に** 1 文を足す: 「落ちた欄以外は形が合っていました。直すのはここに挙げた欄だけで、他の欄の形・鍵の名前・配列の形は変えないでください。余計な鍵を足さない・配列を文字列にしない。」 文言はこの字で固定(試験が字で留める)。前回の出力を渡さない作りは変えない。

### 2.2 試験(既存の作りに合わせる)

H-12 の試験(kind 4 通り × 観測 0/1 × 版 0.4/0.5)、4 schema の新版が「複製 + minItems 無し」であること(構造で比べる: minItems を足し戻すと旧版と同一)、読み込み先が新版、v1.4 の sha と diff の 4 ブロック、`retryUserText` の 1 文、`forbiddenKeywords` の試験が新版でも緑、draft に観測 0 の候補が `aggregateIds: []` で入り**採用の門が落とす**こと(合成の選択で)。段の一覧・件数・sha 表の件数など字で留めた試験の書き換えは可。

### 2.3 直さない物

Core。`audit-core/`。E/I/H の既存の規則(H-1〜H-11)。`additionalProperties`(緩めない)。Anthropic の tool に `strict` を付ける案(鍵無しで確かめられず、効かなければ 400 で席が立たない。**人間の判断 (c') として別に**)。(d) draft が `heldBack` を読むか。(e) E-5 の字面一致。Golden の書き直し。gemini。`.env`。組版・納品・fill_texts。整理役の指示文(v1 のまま。観測 0 の代表は器の写しで書ける)。

### 2.4 実 run(司令塔、1 回)

- out-dir **`scripts/playtest/out/c5/llm-seats-s4/`**(S-3 の `llm-seats-s3/` と Golden の `llm-seats/` を動かさない)、`--runs 1`、`--hold-back-seat gemini --hold-back-reason "S-4: 費用上限と S-3 と同条件"`、v1.4、c5 の packet/request、整理役 v1。
- **費用上限は人間の承認待ち**(推し: S-3 と同じ `SEAT_COST_CAP_USD=5` を環境変数で。`.env` は不変)。承認が無ければ実 run は回さない(実装・監査・コミットまでは進める)。
- 司令塔が `--dry-run` 1 回 → 見込みを記録 → 実 run 1 回 → `run_summary.json` から席ごとの実費 → 事後の照合: `seatOutputCheck --packet`(席ごと)・`integrationCheck --packet`・`exitSelect --draft`(単体、`--out` は scratchpad)・`run_core_path_shogi.py --seats-dir llm-seats-s4`・Golden c5 `--expect`・照合 script(S-3 の `s3_compare.py` に H-12 の行・観測 0 の項目・claude の試行の理由の分類・`aggregateIds` 空の候補を足す)。

## 3. 予測(封じる。0/1 = 二値、幅 = 席の出力に依るので粗い。**S-3 で席に依る欄が全部「見込みより保守的」に外れたので、幅は下を 0 まで広げた所がある**)

### 3.1 (b) 契約

| # | 観測対象 | 予測 | 種別 |
|---|---|---|---|
| b1 | 新版 4 本は旧版 + 「`observations` の minItems 無し」+ 版の const だけ(構造比較) | そのとおり | 0/1 |
| b2 | Golden c5 `--expect`(実 run の後も) | **rc=0 のまま**(H-12 は 0.5 以上だけ、既存 6 封筒は 0.4) | 0/1 |
| b3 | 実 run で `kind` が `unanswerable` / `needed_observation` かつ `observations: []` の項目 | 2 席合計 **0〜6**(S-3 では契約が塞いで 0。下を 0 にするのは席が捨てる癖の可能性) | 幅・粗い |
| b4 | b3 のうち H-12 NG(`neededObservation` 欠落・空) | **0〜2** | 幅 |
| b5 | `finding` など他の kind で `observations: []`(0 件の許しの濫用)→ H-12 NG | **0 件** | 0/1 |
| b6 | 観測 0 の項目が整理役への入力の schema を通り、I-1(全項目ちょうど 1 回)が通る | 通る | 0/1(b3 が 0 なら測れない、と先に書く) |
| b7 | draft の `items` に `aggregateIds: []` の候補 | b3 で H に通った束の数と**同じ**(0〜6)。合成の選択でその候補を採用すると **門が落とす**(試験) | 幅 + 0/1 |
| b8 | Core の経路の Claim 数 | = 観測の数 + counterEvidence の観測の数(観測 0 の項目は Claim 0)。H-9 の自前の再導出と 100% 一致 | 0/1 |
| b9 | `audit-core/` 差分 | 0 | 0/1 |

### 3.2 (c1) 指示文 v1.4

| # | 観測対象 | 予測 | 種別 |
|---|---|---|---|
| c1 | gpt の試行 1 が schema を通る(`itemId` の形を書いた) | **通る** | 0/1(粗い: strict の gpt でも別の欄で落ちうる) |
| c2 | claude の 3 試行のうち schema を通る試行が出る | **出る**。**出ても v1.4 の効果とは断定しない**(1 回では揺れと区別できない。結果文書にそう書く) | 0/1 |
| c3 | claude の試行の理由に「知らない欄 `items2`」「`items` の型が array ではない」が **1 件も無い** | 無い | 0/1 |
| c4 | 空席(3 試行とも落ちる) | **0 席** | 0/1 |
| c5 | 返ってきた封筒の封印語 | 全封筒 **12/12** | 0/1 |
| c6 | 配列の欄を根拠に引いた観測で value が配列のまま **GROUNDED** | **1 件以上**(S-3 の claude の失われた封筒に 6 件あった。claude が立てば出る。**claude が立たなければ外れ**で、b5(S-3)の未検証は続く) | 0/1 |
| c7 | H-9 の VM + PNF の合計(2 席) | **0〜3** | 幅 |
| c8 | 埋め草の印(落ちた観測で文にも反証にも答えにも値が出ない) | **0** | 0/1 |
| c9 | `answers[].status` | gpt・claude とも **`partial`**(S-3 の 2 席 + 失われた claude が全部 partial。問いの「普段指すか」の印は束に無いまま) | 0/1・粗い |

### 3.3 (c2) 再試行の文

| # | 観測対象 | 予測 | 種別 |
|---|---|---|---|
| r1 | `retryUserText` の出力に固定の 1 文が入る(試験) | 入る | 0/1 |
| r2 | 実 run で schema_retry が起きた席について、**連続する試行で同じ理由の文が繰り返されない**(往復 0) | **0 回**(再試行が無ければ測れない、と先に書く) | 0/1・粗い |

### 3.4 費用

| # | 観測対象 | 予測 | 種別 |
|---|---|---|---|
| f1 | `--dry-run` の見込み(1 周・2 席 + 整理役) | **3.0〜3.6 USD**(S-3 3.19 + v1.4 の数百バイト) | 幅 |
| f2 | 実費の合計 | **2.3〜4.8 USD**(claude が試行 1 で通れば下側、3 試行なら S-3 並み) | 幅 |
| f3 | claude 席の実費 | **0.9〜2.0**(1〜2 試行) | 幅・粗い |
| f4 | 上限で止まる | 止まらない | 0/1 |
| f5 | 上限を超える | 超えない(道具が送る前に止める) | 0/1 |

### 3.5 その他

| # | 観測対象 | 予測 |
|---|---|---|
| g1 | checks.json の E-3 / I-4 に H-12 の行 | **0〜2** |
| g2 | CLI 2 本と checks.json の一致 | 一致 |
| g3 | draft の rejected の割合 | **0〜50%**(S-3 は 0%) |
| g4 | 冊子の変わるページ | 0(設計の帰結) |
| g5 | typecheck 新しい赤 | 0 |
| g6 | vitest | 既存は落ちない(字で留めた試験の書き換えを除く)。新規 **+8〜24**(3 段続けて下に外しているので上を広げた) |
| g7 | 行数(本体、試験を除く) | +60〜160 |
| g8 | 違う 0/1 の欄 | **0〜4**(疑うのは c1・c2・c6・c9) |

## 4. 手順(3 役)

1. この文書を封(コミット)。
2. 実装担当(§2.1〜2.2。**作業木を書き換える git 操作を使わない。API の鍵を使わない(`--dry-run` も禁止)。席を回さない。deliver・Golden を実物で回さない**。合成材料だけ。コミットしない)。
3. 司令塔が凍結 → 独立監査(別木の変異: H-12 の各枝・minItems を足し戻す・v1.4 の 1 文を消す・再試行の 1 文を消す)→ GO でコミット。
4. **人間が費用上限を承認したら**司令塔が実 run を 1 回(§2.4)→ 項目別に §3 と照合 → 結果文書 → 人間の判断。

## 5. 止まる所

`SEAT_COST_CAP_USD` で道具が止めたらそこまで。Golden c5 が rc≠0 になったら HUMAN(H-12 が 0.4 の行に掛かっている等)。Core の変更が要ると分かったら HUMAN。描画の数の包含検査が落ちたら送らず REVISE。

## 6. この文書がしないこと

Core の変更。`additionalProperties` を緩めること。Anthropic の strict(人間へ)。(d)(e)。Golden の書き直し。gemini。採用(`adoptedBy`)を機械が付けること。費用上限を司令塔が決めること。
