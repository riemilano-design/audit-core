# 計画 ― Observation Packet(次世代パイプライン Phase A)/ 自動化レーン・2026-09-30

正本: [NEXTGEN_PIPELINE_BRIEF_2026-09-29.md](NEXTGEN_PIPELINE_BRIEF_2026-09-29.md)(`75ee828`)の §2 の 1・§2.5 の 5・6・§3 の 1。
**これは計画だけ。実装は司令塔の承認の後**(監査 → パス指定コミットの型は今までどおり)。

## 0. 顧客の PDF にどう出るか(先に書く)

**この束では、顧客の PDF は 1 文字も変わらない。** packet は事実の置き場所を作る仕事で、冊子の文・数・盤には触らない。
**顧客に効くのは次の 1 点だけ**: 冊子に出ている数(たとえば「65 / 107」)を指したとき、
**その数がどの局のどの手から来たかを機械で遡れる**ようになる。いまは遡るのに人が材料を辿っている
(5 人目の 6 周で私は同じ遡りを 5 回やった ― 22 の 2 つの意味・5 局と 6 局・側の語・404 の在りか・群の行)。

**遡れることが顧客に効く形**: 席や LLM が「この数はおかしい」と言ったとき、**実物の局面まで降りて 1 回で確かめられる**。
6 周のうち **④(封を覆した指摘)6 件のうち 3 件は「数と数の関係が書かれていない」型**で、
どれも「packet に在る事実を人が辿り直す」作業から出た。

## 1. 作るもの

| # | 物 | 置き場所 |
|---|---|---|
| 1 | packet の schema(JSON Schema draft-07。既存の `scripts/playtest/schemas/` と同じ流儀) | `scripts/playtest/schemas/observation-packet.v0.1.schema.json` |
| 2 | request の schema(**packet と別ファイル** ― 正本 §2.5 の 5) | `scripts/playtest/schemas/observation-request.v0.1.schema.json` |
| 3 | packet を組む道具(既存の出力を束ねるだけ。**新しい判定を作らない**) | `scripts/playtest/observationPacket.ts`(+ `lib/observationPacket.ts`) |
| 4 | 一致の固定の試験(既存の数と packet の数が 1 つ残らず一致) | `scripts/playtest/lib/observationPacket.test.ts` |
| 5 | 実データの packet(5 人目の 25 局) | `out/c5/packet/observation-packet.json`(`out/` は gitignore) |

**上位版の欄は作らない**(重要局面の解説・全局・戦型別・継続比較は、同じ packet の上に後で足す)。

## 2. schema の案(機械の語でよい ― 司令塔の許し)

### 2.1 いちばん外側

```
{ "schema_version": "0.1",
  "packet_id":      "<sha256 の先頭 16。facts+aggregates を正規化して取った値>",
  "customer_ref":   "c5",            // ★ 実名を入れない(下の 2.5)
  "facts":      { games, moves, engine, time, branches, collapse, recognition },
  "aggregates": { … },
  "provenance": { sources: {…}, inputs: […], pipeline_version, generated_at } }
```

### 2.2 `facts` の 7 つ(行の単位を先に決める)

| 欄 | 行の単位 | 主な欄(機械の語) | 実データの件数(5 人目・25 局) |
|---|---|---|---|
| `games` | 1 局 | `game_id`・`no`・`side`(sente/gote)・`result`・`plies`・`ending`・`time_limit_sec`・`mirrored` | **25** |
| `moves` | 1 手(本人の手) | `game_id`・`ply`・`usi`・`spent_sec`・`phase`・`is_fork`・`tags[]`(取る/打つ/王手/捨て駒/引く…) | **1242**(局ごとの `plies` = 本人の手の ply 番号の合計。**全部の手は 2463** ― 実測) |
| `engine` | 1 局面 | `game_id`・`ply`・`sfen`・`score_cp`・`top1_usi`・`candidates[]`(`usi`・`score_cp`・`pv[]`)・`nodes`・`multipv` | **1033**(whatif-v2 の position) |
| `time` | 1 局 + 1 手 | 局: `phase_spent_sec`・`long_think_*`・`remaining_sec`。手: `spent_sec`・`collapsed` | **25 局 / 手は `moves` に持たせる** |
| `branches` | 1 分かれ道 | `game_id`・`ply`・`display_ply`・`top1_usi`・`actual_usi`・`top1_side`・`actual_side`・`top1_tags`・`actual_tags`・`top_gap_cp`・`actual_gap_cp`・`first_visible_nodes` | **404**(read の position。うち浅い読みで差が見えたのが 103) |
| `collapse` | 1 件 | `game_id`・`ply`・`before_cp`・`after_cp`・`band_before`・`band_after`・`kind` | **155**(patient の events) |
| `recognition` | 1 局 | `game_id`・`self_signature`・`opponent_signature`・`signature_class`・`names[]`・`review_status` | **25**(opening_recognition の rows) |

**単位の名前を欄に書く**(`*_sec`・`*_cp`・`*_count`)。**「局」と「局面」を必ず区別する**
― 6 周目に席が見つけた穴(同じ 22 が「22 局」と「22 局面」)は、**単位を欄の名前に持たせれば機械で捕まえられる**型だった。

### 2.3 `aggregates`(冊子に出る数は全部ここ)

行は 1 つの分数または 1 つの数。**名前・分母・単位・母集団を必ず持つ**:

```
{ "id": "side_match.attack",          // 機械の id
  "numerator": 65, "denominator": 107,
  "unit": "positions",                 // positions | games | moves
  "population": "branches where top1_side == attack",   // 機械が読める形(下の 2.4)
  "derived_from": ["g01","g02", …],     // ★ 正本 §2.5 の 6
  "src": "e1" }                         // provenance の参照(下の §4)
```

**最初に入れる `aggregates`(= いま冊子に出ている数。1 つ残らず)**

| id | 5 人目の値 | いま作っている場所 |
|---|---|---|
| `side_match.attack` | 65 / 107 | `check_answer.side_match_of` → `m4_fractions` |
| `side_match.defense` | 76 / 132 | 同上 |
| `side_match.opposite_all` | 51 / 239 | 同上(`OPPOSITE_ALL_*`) |
| `time.after_long_think_quick_collapsed` | 9 / 37 | `patient_report_data.time.afterLongThink` |
| `time.by_spent_0_1_collapsed` | 22 / 531 | `patient_report_data.time.bySpent` |
| `long_think.total` / `.fork` / `.opposite` | 61 / 33 / 5 | `check_answer.long_think_fork_of(time_cause)` |
| `branches.total` / `.shallow_visible` | 404 / 103 | `direct_answers.counts.totalForkCount` / `totalCount` |
| `repro.top1_drop` | 22 / 54 | `exit_candidates.repro_rows(direct_answers)` |
| `groups.A/B/C` | 18 / 4 / 3 局(崩れ 56 / 18 / 5) | `exit_groups.group_rows(opening_recognition, patient, direct, side_match)` |
| `ahead_then_lost` | 6 / 18 | `patient_report_data.overview.fromAhead*` |

### 2.4 `population` を機械が読める形にする(**私の提案。司令塔の判断を仰ぐ**)

いまの冊子の穴の多くは「分母が何の集合か」が文でしか書かれていないことから出ている
(5 周目 ①「落ちた候補の中身」・6 周目 ④「22 の 2 つの意味」・④「5 局と 6 局」)。
そこで `population` を**式ではなく 3 つの欄**にする: `{"from": "branches", "where": [["top1_side","==","attack"]], "unit": "positions"}`。
**道具が `facts` から数え直せる形**なので、§5 の一致の試験が「名前どおりに数えたか」まで見られる。
**新しい判定は作らない** ― `where` に書けるのは `facts` に既に在る欄だけ(名前の照合は schema の `enum` で縛る)。

### 2.5 実名を packet に入れない(**ここは私から足す線**)

`patient_report_data.json` は `person`(実名)を持ち、`opening_recognition.json` は `customer` を持つ。
**packet は両方を持たない。**`customer_ref`(`"c5"` のような符号)だけにする。
**理由**: packet は **3 席の LLM(外部 API)への入力**になる(正本 §1 の図)。
いまは人間がブラウザで貼っており、**API になると実名が外部へ出る経路が初めてできる**。
入口で落とすのがいちばん安い。**試験で固定する**(下の §5 の 4)。

### 2.6 `request`(別ファイル)

```
{ "schema_version": "0.1", "customer_ref": "c5",
  "customer_questions": [ { "id": "q1", "text": "<顧客の問いの原文>", "asked_at": "…" } ],
  "requested_scope":    { "games": 25, "time_limit_sec": 180, "note": "…" } }
```

**packet は request を参照しない**(向きを一方通行にする)。両方を LLM 分析の入力にするのは次の段。

## 3. どの既存 JSON がどの欄に入るか

| 既存の出力 | 作る道具 | 入る欄 |
|---|---|---|
| `report/patient_report_data.json` | `reportData.ts` | `facts.games`・`facts.collapse`(events)・`facts.time`(局)・`aggregates.time.*`・`aggregates.ahead_then_lost` |
| `p2/whatif-v2/g*.jsonl`(position 1033・scene 500) | `whatif.ts` | `facts.engine`・`facts.branches` の側(`*_side`)・`aggregates.side_match.*` |
| `p2/read/g*.jsonl`(position 404) | `read.ts` | `facts.branches`(本体)・`aggregates.branches.*` |
| `deliver1/direct/direct_answers.json`(answers 103) | `directAnswers.ts` | `facts.branches` の浅い読みの側・`aggregates.repro.*` |
| `deliver1/direct/time_cause.json`(games 25) | `timeCause.ts` | `facts.time`・`aggregates.long_think.*` |
| `report/opening_recognition.json`(rows 25) | `recognitionMeasure.ts` ほか | `facts.recognition`・`aggregates.groups.*` |
| `deliver1/direct/final_positions.json`・`sfens.json` | 既存 | `facts.engine.sfen`(局面の索引。下の 3.1) |
| `deliver1/direct/answer_menu.json` | 承認済みの表 | **packet に入れない**(承認済みの行動は事実層ではない。Phase の後段) |
| `obsSnapshot` / `obsGeo` / `obsExtra` | `obsSnapshot.ts` ほか | **v0.1 では入れない**(§10 の 3。観測項目の層は別の束で足す) |

### 3.1 局面の実在の索引(正本 §3 の 1 の「局面の実在の索引」)

`facts.engine` を `(game_id, ply)` で引ける索引にする。**1 行に `sfen`・`top1_usi`・`actual_usi` を必ず持たせる**
― いまの検査 7(`<!-- pos: -->` の照合)が材料を 2 本またいで確かめているものを、packet の 1 本で引けるようにする。
**向きの規約は既存のものをそのまま使う**(`sfens.json` の `side`・`mirrored`。新しい判定を作らない ― `board_spec.py` の教訓)。

## 4. provenance の付け方 ― **参照方式にする(測った理由つき)**

正本 §2.5 の 6 は「全部の値に provenance」。**素直に値ごとに埋め込むと大きくなりすぎる**ので、
**値は `src` の符号を持ち、`provenance.sources` が中身を持つ**形にする。

```
"provenance": {
  "pipeline_version": "<git head>",
  "generated_at": "…",
  "sources": {
    "e1": {"type":"engine","engine_version":"…","nodes_limit":…,"multipv":…,"generated_at":"…"},
    "m1": {"type":"material","path":"…/direct_answers.json","sha256":"…","kind":"…","git_head":"…"},
    "r1": {"type":"recognition","definitions_dirs":[…],"review_status":"draft"} },
  "inputs": [ {"path":"…","sha256":"…","bytes":…} ] }
```

**大きさの見込み(実測から計算)**: `facts` の行は約 **3200 行**(1242 + 1033 + 404 + 500 + 25×4)、
1 行あたり数値が約 10 個 = **数値は約 3 万個**。
- 値ごとに `source` を埋め込む: 1 個あたり約 120 バイト → **provenance だけで約 3.6 MB**。
- **参照方式**(`"src":"e1"`): 1 個あたり約 12 バイト → **約 360 KB**。**10 分の 1。**

**遡れること**は参照方式でも失われない(`src` → `sources` → 材料の `path` と `sha256`)。
**`sha256` を持つのがこの方式の要** ― 「途中で材料が差し替わった」を後から機械で言える(封の考え方と同じ。P-145・§67 の家族)。

**行の単位の provenance**: `facts` の行は `src` を 1 つ持つ(行の全部の数値が同じ材料から来るため)。
**行の中で出どころが違う数値だけ**、その数値の隣に `src_<欄名>` を置く(例: `branches` の `first_visible_nodes` は read、`top_gap_cp` は whatif-v2)。
**「全部の値に provenance」は、行の `src` + 例外の `src_*` で満たす**(この読み替えは司令塔の確認を仰ぐ ― §10 の 1)。

## 5. 試験(何が固定されるか)

1. **schema 検証**: 実データの packet が JSON Schema に通る(`ajv` は既存の `schemas/` と同じ流儀で)。
   **わざと壊した packet(必須欄を落とす・単位を別の語にする)が落ちることを校正する** ―
   「通った」は、落ちるものを見せない限り証拠にならない(§68 の教訓)。
2. **一致の固定(この束の中心・正本 §3 の 1 の 4)**: **いま `check_answer` が materials から出している数と、packet の `aggregates` が 1 つ残らず一致**。
   固定する組は §2.3 の 10 行(65/107・76/132・51/239・9/37・22/531・61・33・5・404・103・22/54・18/4/3 と崩れ 56/18/5・6/18)。
   **比べ方は「packet 側と materials 側の両方を同じ試験の中で作って突き合わせる」** ―
   期待値を試験に書き写すと、材料が変わったときに試験だけが古くなる(5 人目で踏んだ型)。
   **ただし 1 件だけ数を直接書く**(`branches.total = 404`)― 全部を「両方作って比べる」にすると、
   **両方が同じ間違いをしたときに緑になる**(P-159 の家族)。
3. **`population` の数え直し**(§2.4 を採るなら): `population` の `from`・`where` で `facts` を数えた結果が、
   その行の `denominator` と一致する。**名前と数が食い違ったら落ちる**ようにする。
4. **実名が入っていない**: packet の全文に顧客の実名・姓が 0 件(`patient_report_data.person` を読んで照合する形。
   **語を試験に書き写さない**)。`customer_ref` は符号だけ。
5. **変異(予測を先に書く)**: (a) `aggregates` の分子を 1 ずらす → 一致の試験が赤。
   (b) `population` の `where` を別の側にする → 数え直しが赤。(c) `src` を落とす → schema が赤。
   (d) 実名を 1 か所入れる → 4 が赤。(e) 行の単位(`positions` → `games`)を入れ替える → 一致か数え直しが赤。
   **(e) は「単位の名前が効いているか」の試験**(22 の 2 つの意味の型を機械で閉じられるか)。
6. **門は今までどおり 2 本**(`npx vitest run --root scripts/playtest`・`npm run typecheck:scripts`)。
   packet は TS で組むので python の門は増えない。

## 6. 大きさ・所要の見込み

| 物 | 見込み | 根拠 |
|---|---|---|
| packet(25 局) | **2.5〜4 MB**(整形なし) | 材料の合計が 3.1 MB(whatif-v2 2.0 + read 0.46 + patient 0.1 + direct 0.1 + time_cause 0.07 + recognition 0.38)。**recognition は rows だけ取るので 0.38 → 0.05 程度に減り**、provenance が 0.36 増える |
| 組む所要 | **1 分未満**(エンジンを回さない。既存の JSON/JSONL を読んで束ねるだけ) | read/whatif-v2 の 50 ファイルを読む所要は既存の道具で数秒 |
| LLM への入力 | **そのままでは大きい** ― 3 席へ渡すのは packet の**要約された view**(実験席の bundle.md が既にやっている形)。**view を作るのは Phase B**(この束では作らない) | 実験 1・2 の bundle は 25 局で数十 KB |
| 実装の分量 | **lib 側 400〜600 行 + 試験 300〜500 行**(4 つの束に分ける。§8) | 既存の `directAnswers.ts`・`timeCause.ts` と同程度 |

## 7. 触らないもの

- **`deliver.ts` の 21 段・冊子の組版・封**(この束では顧客の出口に一切触らない)。
- **`check_answer.py` の検査 1〜3・門**(packet を読む形にするのは**次の束**。正本 §3 の 5)。
- **承認済みの行動の表**(`answer_menu.json`)と**顧客に出る文**。
- **既存の材料を作る道具**(`whatif.ts`・`read.ts`・`directAnswers.ts` ほか)― packet は**読むだけ**。
- **`data/` の認識**(`opening_recognition` の判定を作り直さない ― `useOfThisFile` のとおり読む)。

## 8. 実装の分割(束)と順序

| 束 | 中身 | 出す証拠 |
|---|---|---|
| **A** | schema 2 本(packet・request)+ schema 検証の試験と**壊した packet の校正** | 壊した packet が落ちる |
| **B** | `facts` を組む(games・moves・engine・branches・collapse・recognition・time)+ 局面の索引 | 行数が実測と一致(25 / 1242 / 1033 / 404 / 155 / 25) |
| **C** | `aggregates` と provenance(参照方式)+ **一致の固定**(§5 の 2) | **10 行の数が 1 つ残らず一致** |
| **D** | `population` の数え直し(§2.4 が承認されたら)+ 変異 5 本 | 変異が予測どおり赤 |

**順序**: A → B → C → D。**C が閉じた時点が「packet が事実の基準点になった」** ― ここで司令塔に 1 行入れる。
D は「分母の名前と数が食い違わない」ための床で、**次の束(検証器を packet に載せる)の前提**。

## 9. 受け入れ基準(測るもの)

1. schema 検証が通り、**壊した packet 5 通りが全部落ちる**。
2. **§2.3 の 10 行が、いまの冊子の数と 1 つ残らず一致**(食い違いが 1 件でもあれば、packet ではなく**私の束ね方**を直す。
   材料の数を packet に合わせて書き換えることは**しない**)。
3. 実名 0 件(§5 の 4)。
4. 変異 5 本が予測どおり赤(予測は変異と同じ逐次コマンドで**先に書く**)。
5. 門 2 本が緑(typecheck の既知の赤 10 本は `out/` 配下のまま)。
6. **packet から冊子の数へ戻る道が 1 本で書ける**ことを、**実際に 1 つやって記録する**
   (例: 冊子の「65 / 107」→ `aggregates.side_match.attack` → `derived_from` の局 → `facts.branches` の行 → `facts.engine` の `sfen`)。

## 10. 決めていない点(司令塔・人間に上げる)

1. **「全部の値に provenance」の読み替え**(§4)。行の `src` + 例外の `src_*` で満たす形でよいか。
   値ごとに埋め込むと **3.6 MB が provenance だけ**になる(実測から計算した)。
2. **`population` を機械が読める 3 欄にするか**(§2.4)。採ると「分母の名前どおりに数えたか」を機械で言えるが、
   **schema と試験が 1 段重くなる**。採らなければ `population` は文のままで、22 の 2 つの意味の型は**人の目に戻る**。
3. **`obsSnapshot` / `obsGeo` / `obsExtra` を v0.1 に入れるか**。正本 §3 の 1 は挙げているが、
   **いま冊子に出ている数には使われていない**(観測項目の層)。**v0.1 では入れず、v0.2 で足す**を私の案とする。
4. **`moves` の行を「本人の手だけ」にするか、相手の手も持つか**。
   いま冊子の数は全部本人の手で、相手の手は `facts.engine` の局面に含まれる。**本人の手だけ**を私の案とする(小さく始める)。**測った**: 本人の手 1242 / 全部の手 2463(25 局)。相手の手も持つなら行が倍になる。
5. **packet に封を掛けるか**(`packet_id` + 材料の `sha256`)。私の案は**掛ける** ― 分析が走った後に材料が差し替わった、を機械で言えるようにする。
6. **`customer_ref` の符号の付け方**(`c5` のような既存の出力フォルダ名でよいか。人が見て誰か分かる符号にしない)。

## 11. 次の段の下見(この束では作らない)

- **既存の検証器を packet に載せる**(正本 §3 の 5): `check_answer` の検査 1(数が材料に在るか)は、
  **packet の `aggregates` と `facts` を見る形**にすると、いまの弱さ(P-177 の小数の桁・P-178 の「どこかに同じ整数が在れば通る」)が同時に閉じる。
  **これは動きを変えるので、別の束 + 独立監査。**
- **`hypothesisCheck.ts`** は既に「引いた数が観測項目に実在するか」を見ているので、**観測項目を packet に置き換える**のが素直。
- LLM への **view**(3 席に渡す形)は Phase B。**packet をそのまま渡さない**(大きさと、要らない欄が意味探索を散らす)。
