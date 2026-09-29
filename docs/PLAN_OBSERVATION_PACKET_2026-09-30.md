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

## 5b. 試験の 5 本立て(**人間の指示・2026-09-30。司令塔経由の伝聞**)

**監査でも別々に測る。**上の §5 の並びを、この 5 本に割り当て直す。

| 本 | 名前 | 何を見るか | どの束で閉じるか |
|---|---|---|---|
| **A** | **再現性** | いまの冊子の 10 の数 = packet から作った 10 の数(§2.3・§5 の 2) | **C** |
| **B** | **完全性** | 元データの 25 局 = packet の 25 局。**局 id の集合が一致**(欠けも増えも無い) | **B** |
| **C** | **粒度** | 元棋譜の対象手 = packet の対象手(本人の手 **1242**)。**局ごとの手数も一致** | **B** |
| **D** | **追跡性** | 冊子の数 → 集計行 → `derivedFrom` の局 → 事実の行 → `provenance.sources` → 材料の `sha256` まで、**道具で実際に辿って到達する**(10 の数すべて) | **C** |
| **E** | **異常検出(陽性対照 5 本)** | 1 局削除・1 手削除・`population` の変更・数の変更・`provenance` の変更で、**それぞれ落ちる** | **D** |

**人間の言葉(伝聞)**: 残る最大のリスクは **packet 生成そのものの完全性**。provenance の参照が途中で切れないことを **D** で見張る。
**余計な変更を入れず A → B → C → D を閉じることに集中する。**

**私から 1 つ足す**: **D は「辿れた」ではなく「辿った結果が材料の実物と一致した」まで見る**
― `sha256` を引いて**材料のファイルを実際に読み直し、同じ値になること**を確かめる(参照が生きているだけでは、
差し替わった材料を指していても緑になる)。

## 5c. 実験席の要望(2026-09-30)と、測って決めた結果

| 要望 | 判断 | 測った値 |
|---|---|---|
| `facts.moves[].piece`(動いた駒・打った駒の種類) | **v0.1 に入れる** | 打つ手は USI の 1 文字目。**盤の手は USI に駒種が無い**ので、指す前の局面の元の升を引く ― 材料 `sfens.json` は**全局面を持つ**(実測: 1 局に sfens 124・moves 123)。`pieceFrom`(board / hand)を対で持たせ、どちらで決めたかを残す |
| `facts.recognition.rows`(機械の判定) | **v0.1 に入れる** | rows は 25 局で **217 KB**。3 群の分け方の根拠(`proposalSignatureClass`)を含む |
| `facts.recognition.definitions`(認識の定義) | **v0.1 に入れる**(実験席の「1 割」の線を下回った) | 定義は **114 本**(`data/openings` 3 + `data/drafts/2026-09-25-knowledge/openings` 111)。ファイルの合計 164 KB。**数え方を書く(独立監査の REVISE 3。最初は数だけ書いて、どの写像で数えたかを書いていなかった)**: **(a) 全部の欄を写す・`json.dumps` の既定の区切り = 93 KB**、**(b) 同じく区切りを詰める = 90 KB**、**(c) schema が写すと決めた欄だけ・区切りを詰める = 30 KB**(写さないのは `scenario`・`source`)、**(d) 照合に要る最小の欄(id・name・side・recognition_pattern・review_status)= 21 KB**。**この束で採ったのは (c)。**ただし (c) は材料の鍵のままで数えたので、**packet に実際に入る形(鍵を camelCase に直し、行に `src` を足す)で測り直した**: **区切り詰め 31.2 KB・既定の区切り 34.6 KB**(独立監査の再計算 35.4 KB とほぼ同じ ― 差は区切りと `src` の有無)。packet の見込み 2.5〜4 MB に対して **1 % 前後**。**`recognitionPattern` が無い定義 7 本も入れる** ― 「定義が在るのに認識できない」と「定義が無い」を席が区別できるようにする |

## 5d. 束 A で schema の形を 1 つ変えた(記録)

`aggregates` の行は最初 **`oneOf` の 2 変種**(分数 / 単独の数)で書いた。**校正で嘘の緑が見つかった**:
自作の検証器の `oneOf` は「**oneOf の 0 個に合った**」しか言わないので、**行の中のどこが悪くて落ちたのかが誤りの文に出ない**。
単位を壊しても、欄名を壊しても、`derivedFrom` を空にしても**同じ文**になるため、
「意図と別の理由で落ちても試験が緑」になる(3 本がその状態だった)。

**直し**: schema を**平らな 1 つの形**にして誤りが欄を名指しするようにし、
**「分数か単独の数のどちらか 1 つ」は道具側**(`aggregateFormProblems`)で見る。
検査の入口は `observationPacketProblems`(schema の形 + 行の形 + 封の符号を束ねる)。
**型**: **oneOf は「どこが悪いか」を消す。** 変種の判別に使うのはよいが、**試験で理由まで見たい欄には使わない。**

## 5e. 束 A の独立監査(REVISE → 直し)― 2026-09-30

| # | 監査の指摘 | 実物で確かめた結果 | 直し |
|---|---|---|---|
| 1 | **封の性質のうち「aggregates が変われば符号が変わる」を見る試験が無い** ― `packetIdOf` を「facts だけを見る」に書き換えても **24 本とも緑**だった | **再現した** | 試験 **b3b** を足した(分子を 1 変える / 行を 1 つ落とす、の 2 通り)。**変異は b3b だけを赤にする** |
| 2 | **schema と実データの形が食い違う** ― 定義の `recognition_pattern` は実データ **226 件すべてが `order_hint`・`piece`・`to`** なのに、schema は `ply`・`usi`・`note`・`from` を許して `orderHint` を持っていなかった。**束 B が写した瞬間に 114 本すべてが違反**になる形 | **自分で数え直して確認**(226/226。型は `order_hint` が整数・`piece` が**日本語の駒の字**・`to` が文字列) | schema を実データの形に直し、**試験の仮の値も実データの形に直した**。さらに **`data/` の定義を読んで「schema が許す鍵」と突き合わせる試験 c1・c2** を足した(**schema を先に書いて実データを後で見る、をもう起こさないための床**) |
| 3 | **§5c の 93 KB / 21 KB が、schema の写像で数え直すと再現しない** | **数え方が違っていた**(93 KB は全欄・既定の区切り、21 KB は別の最小の欄の組)。**どの写像で数えたかを書いていなかったのが誤り** | §5c に **4 通りの数え方(a)〜(d)を全部書き、採った値((c) 30 KB)を明示**した |

**監査が次の束の条件として挙げたもの(この束の REVISE 理由ではない。束 C・D で閉じる)**

1. **`aggregates[].unit` と `population.unit` の食い違い**が素通りする。
2. **`facts.*[].src` が `provenance.sources[].id` に実在しない**場合が素通りする ― **封が「遡れる」ことの前提そのもの**。
3. **`aggregates[].derivedFrom` の `gameId` が `facts.games[]` に実在しない**場合が素通りする。
4. `provenance.sources[].path` / `inputs[].path` が自由文字列で、**絶対パス・ホームのユーザー名を書かない**が説明だけで縛られていない。
   → **1〜3 は §5b の D(追跡性)の明示の検査項目にする。4 は材料のパスを書き込む束(B)で pattern か道具側の変換で閉じる。**

**この束で私が踏んだ型**(記録): **schema を実データより先に書くと、実在しない欄を許して実在する欄を落とす。**
しかも**試験の仮の値を同じ思い込みで書くので、試験からは見えない**。
**器を書くときは、器に入れる実物の鍵を先に数える**(§68 の「一致は不一致を作れることを見せない限り証拠にならない」の家族)。

## 5f. 束 B の実測(5 人目の 25 局。2026-09-30)

**行数は計画の見込みと 1 件も違わなかった** ― `games` **25** / `moves` **1242** / `engine` **1033** / `time` **25** /
`branches` **404** / `collapse` **155** / `recognition.rows` **25** / `recognition.definitions` **114**。
**B 完全性・C 粒度の検査は問題なし**(道具が自分で測る形。試験の中だけではない)。

| 測ったもの | 値 | 読み |
|---|---|---|
| `facts` の大きさ | **0.84 MB** | 計画の見込み(2.5〜4 MB)より**小さい** ― 見込みは材料のファイルの合計から出したが、**packet は材料の全部の欄を写さない**(写さないと決めた欄と、集計に使われない欄が落ちる) |
| `usi` と駒種が付いた手 | **1238 / 1242** | 残り 4 件は **材料の `plies` が総手数と同じ添字を持つ**行(g04・g09・g16・g23。**4 局とも 負け・投了**)。**指し手が無いので欄を出さない**(作らない) |
| 秒が付いた手 | **161 / 1242** | 材料(`time_cause.midMoveSeconds`)が**中盤の手だけ**を持つ。**無い手に 0 を書かない**(「測っていない」と「0 秒」は別) |
| 分かれ道の印が付いた手 | **404 / 404** | 下の「鍵の取り違え」を直した後の値 |
| 分かれ道の側 | `top1Side` **404** / `actualSide` **404** | 側は **whatif-v2 の `candidates[0].side`**(行の直下には無い ― 既存の `check_answer.side_match_of` と同じ場所) |
| 浅い読みで差が見えた印 | **103 / 404** | direct_answers の 103 件と一致 |
| 実戦との差(`actualGapCp`) | **15 / 404** | direct の値だけを写す。**whatif の `loss` は `{value, cpValue, isLowerBound}` の組**で、下限のときに数として書けない(付録の「実戦との差: —」が多い理由もこれ) |
| 読んだ材料のファイル | **169 本** | 25 局 × 2(read・whatif-v2)+ 5 本の JSON + 定義 114 本。全部に `path`(根からの相対)・`sha256`・`bytes` を付けた |

### 束 B で踏んだ間違い(記録)

1. **駒の升の番号を自分で書いて落ちた。** `parseSquareName`(`shogiops/util`。既存の `lib/beginnerProfile.ts` が使っている)を使わず
   自分で `rankIndex * 9 + (9 - file)` を組み、実物で「元の升に駒が無い」と言われた。**既存の道具に在る計算を写さない**(P-111 の家族)。
   直した後、**材料が持つ日本語の手の字と突き合わせて 155 / 155 一致**(`patient_report_data` の `events[].played` の駒の字 ―
   **独立な出どころ**で校正した)。本人の手 **1238 件で例外 0**。
2. **分かれ道の印の鍵を `displayPly` にしていた。** 実測すると **`(局, ply)` は本人の手と 404 / 404 一致、`displayPly` は 141 / 404 しか一致しない**
   (263 行で 2 つの値が違う)。**印が 141 しか立たないのを数で見て気づいた。**
   **whatif-v2 との結合は `displayPly`**(既存の `check_answer` と同じ鍵)なので、**2 つの鍵を用途で使い分ける**。
   同じ取り違えを**機械で捕まえる検査 2 つ**(分かれ道の `(局, 手)` が本人の手に在るか・印の数が行の数と合うか)を `completenessProblems` に足した。
3. **合成材料が `ply == displayPly` だったので、2 の取り違えを試験が見逃していた。** 22 本が一発で緑になったのを疑い、
   **材料を実物寄り(`ply ≠ displayPly`)に直した**。**型**: **合成材料は「実物で違っている欄」をわざと違わせる。**

### 束 B の独立監査(REVISE → 直し)― 2026-09-30

監査は**自分で SFEN の読み手をゼロから書いて** 1242 手を突き合わせ(**不一致 0。後手の局 760 手も 0**)、
鍵の使い分け・浅い読みの印・`actualGapCp` が 15 件しかない理由まで独立に再現した。そのうえで **2 つの穴**を見つけた。

| # | 指摘 | 実物で確かめた結果 | 直し |
|---|---|---|---|
| 1 | **「道具が毎回自分で測る」と書いた検査が、7 欄のうち 3 欄で無かった** ― 同じ定義のフォルダを 2 回渡すと定義が 114 → 117、崩れ・時間の材料の 1 行を複製すると 155 → 156・25 → 26 になるのに、**検査は 0 件** | **再現した** | `completenessProblems` に **崩れ・時間・定義の件数**と、**時間の局 id・定義の id の重複**の検査を足した。試験 **f7b**(行が増える方向の壊れ 3 通り)を足し、**検査を 1 つずつ外す変異 3 本が f7b を赤にする**ことを確かめた |
| 2 | **読み手(`observationMaterials.ts`)に試験が無かった** ― 根の外を拒む門・`sha256`・相対パスを持つ唯一の層なのに、自動の網が無い | そのとおり(監査は手で確かめていた) | `lib/observationMaterials.test.ts` を新設(**6 本**)。一時フォルダを「根」として渡し、**実ファイルで**相対パス・指紋・門・壊れた材料・同じフォルダ 2 回を固定。**門を外す変異と指紋を空にする変異が赤**になることを確かめた |

**私が §5f に「問題なし」と書いたのは、測っていた 4 欄についてだった** ― 残る 3 欄を測っていないことを書いていなかった。
**型**: **「検査は問題なし」と書くときは、何を検査したかを並べる**(束 A の §5e では次の束の条件を並べたのに、ここでは並べなかった)。

**変異 7 本**(予測を先に書いた)はすべて赤 ― 手の `ply` の +1・印の鍵・側の在りか・写さない欄・候補の評価・分数の分子・秒の鍵。
**私の予測は「赤が少ない」向きに 3 件外れた**(契約の試験 g1 が一緒に赤くなる分を見落とした)。5 周の集計と**逆向き**の外れ。

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
