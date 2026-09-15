# STEP D-SCREEN 計画: 全行を 40 万ノードで測り、急落の候補の前後だけ 400 万ノードで測り直す(2026-09-15)

**状態**: 計画(**司令塔の決定(版 `82344779`): Q-1〜Q-8 はすべて推奨どおり**。**事前読み 1e の REVISE(版 `7388c9b6`、必須 R-1〜R-4・推奨 S-1〜S-7)を司令塔の決定で取り込み、版 `321a274a` への 1e の再読みは GO**(K-1 を司令塔の決定 (a) で直し、K-2〜K-5 は 9. に既知事項の候補として置いた ― 取り込み先は 10.)。書いたのは A(sgogi-coach-64、司令塔の依頼。人間の指示「作業を効率よく早く」)。**エンジンは使っていない。**基点 HEAD `58b540a`。**§11(2026-09-15 の追記)は司令塔 e3 が受け、事前読み f2 の REVISE(版 `cceba809`)を司令塔の決定で取り込んだ。§11 は §1・§3・§5・Q-7 の一部を置き換える(各所に「§11 で置き換え」と書いた)**。
**司令塔の補足**: (1) 候補の閾値 −300・−200 は**判断的知識の仮置き(draft)**。校正で取りこぼしが出たら、**候補を広げる向き(絶対値を小さくする)にだけ**動かす (2) 所要を根拠にする実行は**エンジン 1 本・他のエンジンが止まっている時間帯**(規則 12 番) (3) **実装の着手は 20 局版レポートの後**。
**やらないことの先頭**: **4M 一律をやめる判断はこの STEP ではしない。**校正(5.)の結果を見て、人間が承認する。

## 0. 実物から分かった前提

| # | 事実 | 場所 |
|---|---|---|
| E-1 | **`engineReference` を測る入力は局面の sfen だけ**(baseline と passSfen の 2 本。手順を使わない)。**ただし値はエンジンの状態(同じプロセスで前に回った探索)に依る**(E-10) | `apps/server/src/analysis/engineReference.ts:141-188`・`scripts/playtest/lib/recorder.ts:252-255` |
| E-2 | 本番の導線(③と候補手)の探索は `--nodes` で全行に掛かり、省けない。`--reference-nodes` は `engineReference` だけのノード数 | `replay.ts:146-160`・D-COST 計画 C-a・C-b |
| E-3 | D-COST(固定 7 局・107 行、深い = 4M の急落候補 21): **L400k は取りこぼし 1/21・余計 0**、t_row 比 **1/8.7**(平均)。L100k は 2/21・余計 3・1/28.5。所要はすべて load > 2.0 の「参考」 | D-COST 計画 §12.2〜12.4 |
| E-4 | **同じ手順で再生すれば 4M は再現する**: 別の日・別プロセスの C4M と D4M で 107 行がバイト一致(P-48)。D-COST の取りこぼしはノード数から来ている | 同 §12.3・`docs/PHASES.md` P-48 |
| E-5 | 取りこぼしの中身: L400k は 深い −508 / 軽い **−396**。L100k は −429/−373 と **−757/−312(閾値から遠い)**。余計 3 件は深い差が −319・−396・−349 | 同 §12.3 の表 |
| E-6 | 急落の規則 `DRAFT_RULE_1` = advantageCp 300・dropCp −400・windowPlies 5・**focusDropCp 300(③の承認済みの 300cp の借用)** | `scripts/playtest/lib/failureEvent.ts:51` |
| E-7 | D2 の読み筋(`searchPvs`)は導線の探索の結果で、`engineReference` の探索の読み筋は捨てている(U6-L)。**軽い回では読み筋も 40 万ノード** | `recorder.ts:245-251`・`:271` |
| E-8 | meta の探索条件は `searchMode`・`nodes`・`threads`・`referenceNodes`。Failure Event の出どころに写すのは `nodes` まで | `replay.ts:196-214`・`lib/failureEventSchema.ts:29` |
| E-9 | 記録の行に欄を足しても、不変条件と `check.ts` は欄の名前で読むだけで拒まない。`compare.ts` は実行ごとに変わる 6 欄のほかを全部比べる | `invariants/i7-urgent-but-other-talk.ts:89-92`・`i11-focus-not-stated.ts:92-94`・`compare.ts:38-49` |
| E-10 | **4M 一律の記録は、導線の探索の直後に同じエンジン(同じプロセス)で `engineReference` を測る。**`measureEngineReference` は局面の間でエンジンの状態を消さず、`UsiEngine` にも消す手段(usinewgame・ハッシュの消去)が無い。**同じプロセスで前の探索が違う 2 つの 4M の探索は 0/59 で一致しない(P-33)** | `replay.ts:251-265`・`engineReference.ts:152-164`・`apps/server/src/engine/usiEngine.ts:155`・`docs/PHASES.md` P-33 |
| E-11 | `diagnose.ts` は同じ kifuId の記録が 2 本来ても区別しない(重複を確かめる箇所が無い)。**`records/d-cost` は同じ 7 つの kifuId が c4m・l100k・l400k に 3 本ずつあり、21 本を 1 回に掛ける使い方がある** | `scripts/playtest/diagnose.ts`・`lib/failureEvent.ts` を grep・V0.3-META 計画 F-7 |

## 1. 目的と範囲

**目的**: 次の棋譜から、1 局の評価の所要を 4M 一律より下げる。**記録には軽い値と深い値の両方を残し、どの行を・どの回で・どの並びで深く取り直したかを meta と行に書く。**

**形(Q-1)**: `replay.ts` は変えない。**段 1** = `replay.ts --nodes 400000 --reference-nodes 400000`(全行)。**段 2** = 新しい道具 `scripts/playtest/rescreen.ts <段1.jsonl> --out <段2.jsonl> --deep-nodes 4000000`。**中身は lib の純粋な組み立て `rescreenRecords(lines, screenRule, measure)`**(`measure(sfen) → EngineReferenceMeasurement` を引数で受ける ― **§11 で置き換え**。旧: `EngineReference | null`。試験はエンジン無しで偽の `measure` を渡す)。CLI は記録を読み、1 プロセス・Threads 1 のエンジンで `measureEngineReference` を `measure` として渡し、書くだけ。**段 1 のファイルは変えない。**

**実装は 2 つ(Q-8)**: **D-SCREEN-1** = 選び方と `rescreenRecords`・`rescreen.ts`・記録の形・見張り。**D-SCREEN-2** = `diagnose.ts` の規則(3.)・Failure Event v0.5・diagnosis-moment v0.2・校正の道具。**校正(5.)は 2 の後**、エンジンを持つセッションが宣言して回す。**実装の着手は 20 局版レポートの後。**`apps/`・`data/` に触らない。

## 2. 読み直す行の選び方と記録の形(段 1 の値だけで決める)

**候補の組**(連続する ready 行 i → i+1。`pairEvaluations` と同じ組、Q-3。**閾値は draft**):
- (a) 比べた組で **差 ≤ −300**(`focusDropCp` の符号を変えて使う。E-5 の −396・−312 を拾う)
- (b) **直前 ≥ +300(advantageCp)で差 ≤ −200**(優勢からの下がり。−200 は新しい値)
- (c) 直後が詰まされる読み(mateAfter < 0)、または直後の行の `afterPassMate > 0`(matedIfPass)
- (d) 比べられなかった組のうち、理由が **`notEvaluation`・`notMeasurable`**。**王手中・終局は入れない**(深くしても測らない ― E-1)

**読み直す行(Q-2)**: 候補の組ごとに **行 i−1・i・i+1・i+2**。深くすると急落が隣の組へずれうるので、隣の 2 組も両方深い組にする。端は切り、重なりは 1 回。**測る並びは ply の昇順に固定**(E-10。並びで値が変わりうるので決めて残す)。

**段 2 の記録(Q-5)**:
- 読み直した ready 行に **`engineReferenceDeep: EngineReference | null`**(null = 測ろうとして測れなかった)。**読み直していない行はキーを出さない**。`engineReference`(軽い値)は**そのまま**
- meta は段 1 の meta の写しに **`screen`** を足す: `lightNodes`・`deepNodes`・`rule`(`dropCp −300`・`advantageCp 300`・`advantageDropCp −200`・`before 1`・`after 2`)・`deepPlies`・`sourceSha256`(段 1 のファイル)・**`deepRun`(深い回の出どころ ― R-3)**: `gitHead`・`dirty`(道具が自分で読む。`buildMetaLine` と同じく渡された値を使わない)・`enginePath`・`threads`・`startedAt`・`order: "plyAscending"`・`measuredOrder`(実際に測った ply の並び)
- **不変条件(規則 11.1)**: `engineReference.nodes === lightNodes`、`engineReferenceDeep.nodes === deepNodes`、`deepPlies` = 行の欄 = `measuredOrder` の集合。どれかが破れたら `diagnose.ts` はその記録を数えない

## 3. `diagnose.ts` の規則(D-SCREEN-2。Q-4)

- **組ごと**: 組の **2 行とも `engineReferenceDeep` が measured なら 2 行とも深い値**、そうでなければ **2 行とも軽い値**(組の中でノード数を混ぜない)。深く測れなかった行を含む組は軽い値で比べ、**`deepUnavailable` を数えて出す**(規則 11.6)
- **最大の下がり(diagnosis-moment)**: 局の中の比べた組が**すべて同じ出どころならその値、混ざる局は全部の組を軽い値で選ぶ**(ノード数を混ぜない規則を局の中の比べにも当てる ― S-2)
- **版(R-2)**: Failure Event v0.5・diagnosis-moment v0.2(MINOR)。**`evaluationSource: "light" | "deep"` は `screen` のある記録にだけ書く任意の欄**(Event は `branch` に、moment は組の行に)。出どころの meta に `screen`(`deepPlies`・`measuredOrder` を除く)を写す。**`screen` の無い記録(4M 一律)は、`--events` が `schemaVersion` と `provenance.analysis` 以外バイト一致、Markdown はバイト一致**(`deepUnavailable` の列・節は `screen` のある入力があるときだけ出す)。`referenceNodes` は写さない(写すと 4M 一律の行が変わる ― S-5 は限界へ)
- **段 2 とその段 1 を一緒に渡したときだけ**(`screen` のある入力の `sourceSha256` が別の入力の sha256 と一致する、または同じ kifuId の片方にだけ `screen` がある)、名前を並べて exit 1(S-6。二重に数えない)。**`screen` の無い記録どうし(`records/d-cost` の同じ kifuId の 3 本など)は今のまま通す**(1e の再読み K-1、司令塔の決定 (a))
- **D2 の読み筋: 軽い組は段 1 の `searchPvs`(40 万ノードの③の探索)、深い組は §11 の `searchPvsDeep`**。どちらを使ったかは `pvSource` に書き、ノード数は行に書かない(`screen.lightNodes`・`deepNodes` から読める)。**§11 で置き換え**(旧: 段 1 のまま・ノード数を書く ― E-7・Q-7)
- **`check.ts`・不変条件は段 2 の記録でも `engineReference`(軽い値)を読む。変えない**(S-1。I-7・I-11 の判定は 4M 一律と変わりうる ― 限界)

## 4. 所要の見積もり(式だけ)

T₂段 = t_boot + R × t_row(400k) + D × t_ref(4M)。R = ready 行、D = 読み直した行(重なりを除く)。**T₂段 / T_4M一律 は、校正のときに 4M 一律・段 1・段 2 を同じ 1 局で、エンジン 1 本・load ≤ 2.0 で測って置く**(S-3。d3-nnue・D-COST の所要はどれも「参考」で分母に使えない)。

## 5. 校正(**4M 一律の記録と、急落の集合が一致するか**)

- **0. rescreen の床(R-1)**: `records/d3-nnue` の 20 局に、**`deepPlies` = 全 ready 行・`deepNodes` = 4M** で rescreen を当てる。(i) `engineReferenceDeep` と `engineReference` が行ごとにバイト一致する数 (ii) 全行を深い値で数えた Event の集合と、今の Event の集合の食い違い (iii) **同じ入力で rescreen を 2 回**回したバイト一致。**床(ii)が 0 でなければ、1. の食い違いは「並び(状態)で出るもの」と「ノード数で出るもの」に分けて数える**(同じ組が床でも食い違っていれば並びの側)
- **1. 本番の形**: 同じ 20 局を段 1(400k)→ 段 2 で回し、Failure Event の **(kifuId, branchPly, kinds)** を 4M 一律と比べる。**一致・取りこぼし・余計**、比べられなかった・測っていないは数えて並べる(D-COST §2.2)。死因①の一致も並べる。`counterfactual` は集合に入れず、**同じ (kifuId, branchPly) の 4M 一律の `counterfactual.state` と段 2 の state の一致率**を、**`pvSource` ごとに分けて**別に出す(§11)
- **2. 20 局版(REAL-02・REAL-03)**: D2 §5.3 の照合が済んでから、1. と同じ形で(Q-6)
- 道具: `scan-compare.ts` の lib を Event の単位に広げる(D-SCREEN-2)

## 6. 固定例と変異(規則 11.3・11.8。`plantedRecords` に軽い値・深い値を植え、段 2 は偽の `measure` で作る)

| # | 固定例 | 期待 |
|---|---|---|
| S-1 | 直前 0 で差 −299 / −300 | −300 だけが候補((b) に当たらない直前にする) |
| S-2 | 直前 +300・差 −200 / 直前 +299・差 −200 | 前だけが候補 |
| S-3 | 候補が最初の組と最後の組 | 行 i−1・i+2 は端で切れる |
| S-4 | 隣り合う 2 つの候補 | 重なりは 1 回(`deepPlies`・`measuredOrder` に重複なし、昇順) |
| S-5 | notEvaluation の組 / notMeasurable の組 / 王手中の組 | 前の 2 つだけが候補 |
| S-6 | 深い行と軽いだけの行の組 | 2 行とも軽い値 |
| S-7 | 深く測れなかった行を含む組 | 軽い値・`deepUnavailable` 1 |
| S-8 | `deepPlies` と行の欄・`measuredOrder` が食い違う / `nodes` が条件と違う | 数えない |
| S-9 | `screen` の無い記録(GAME01 と d0-nnue) | Markdown バイト一致・`--events` は `schemaVersion`・`provenance.analysis` 以外一致・`evaluationSource` のキーが無い |
| S-10 | 軽い −396・深い −508(E-5) | 深い組で cpDrop・`evaluationSource: "deep"` |
| S-11 | (c) 直後 mate −3 の組 / 直後の行の `afterPassMate` +3 の組 | どちらも候補 |
| S-12 | 記録の形(偽の `measure`・偽の git の状態) | 段 1 のバイト列が変わらない・`engineReference` が変わらない・読み直していない行にキーが無い・`sourceSha256` = 段 1 の sha・`deepRun.gitHead` は段 1 の meta でなく道具が読んだ値・`measuredOrder` = `measure` が呼ばれた順 |
| S-13 | 最大の下がり: 深い組と軽い組が混ざる局 | 全部の組を軽い値で選ぶ |
| S-14 | (i) 段 2 とその段 1(`sourceSha256` が一致)(ii) 同じ kifuId の片方にだけ `screen` (iii) `screen` の無い同じ kifuId の 2 本 | (i)(ii) exit 1・名前を出す (iii) 今のまま通る |

変異(中心): **Z-1** 候補の閾値を −400(S-1・S-10)/ **Z-2** 読み直す行を i・i+1 だけ(S-3・S-10 の隣の組)/ **Z-3** 混ざった組で深い行だけ深い値(S-6)/ **Z-4** 深く測れなかった行を数えずに軽い値(S-7)/ **Z-5** ノード数・`deepPlies` の不変条件を外す(S-8)/ **Z-6** `rescreenRecords` が `engineReference` を深い値で上書き(S-12)/ **Z-7** `screen` の無い記録にも `evaluationSource` を書く(S-9)/ **Z-10** (c) を候補から外す(S-11)/ **Z-11** 最大の下がりで出どころを混ぜて選ぶ(S-13)/ **Z-12** `deepRun.gitHead` に段 1 の meta を写す(S-12)。周辺: Z-8 重なりを除かない(S-4)・Z-9 王手中の組を候補にする(S-5)・Z-13 段 2 と段 1 の組を通す / `screen` の無い同じ kifuId を止める(S-14)。**予測は実装の後、当てる前に試験の単位で書く。**

## 7. 予測(**測る前に書く。確信はどれも弱い**)

| # | 予測 | 外れたと言える条件 |
|---|---|---|
| 予-0 | 床: (i) バイト一致する行は **0〜40%**(P-33 の側に寄る)、(ii) Event の集合の食い違いは **0〜6 件**、(iii) 2 回の rescreen は**バイト一致** | (iii) が一致しない / (ii) が 7 件以上 |
| 予-1 | 本番の形で、4M 一律に対する**取りこぼし 0〜2 件・余計 0〜3 件**(床の食い違いを含む数) | 取りこぼし 3 件以上 |
| 予-2 | 読み直す行 D は ready 行の **20〜45%** | 20% 未満か 45% 超 |
| 予-3 | T₂段 / T_4M一律 は **0.25〜0.55**(4.の 1 局で) | 0.55 超 |
| 予-4 | `counterfactual` の状態の一致率(5. の 1.。**`pvSource` ごとに分子・分母**)は、light・deep とも **80% 以上** | どちらかが 80% 未満 |

## 8. 決定(司令塔: **Q-1〜Q-8 すべて推奨どおり**。表は決定の前の選択肢)

| # | 点 | 決定 | ほかの案 |
|---|---|---|---|
| Q-1 | 段 2 の形 | 別の道具 `rescreen.ts`(導線を繰り返さない) | `replay.ts` に `--reference-plies`(導線を全行 2 回) |
| Q-2 | 読み直す範囲 | 前 1 行・後 2 行 | 組の 2 行だけ / 前 2・後 3 |
| Q-3 | 候補の閾値 | (a)〜(d)。**draft**、校正で取りこぼしが出たら広げる向きにだけ | dropCp と同じ −400(E-5 の −396 を落とす) |
| Q-4 | 深い値の使い方 | 組ごとに 2 行とも深いときだけ | 行ごとに深い値を優先(組の中で混ざる) |
| Q-5 | 記録の形 | 行に `engineReferenceDeep`、meta に `screen`。軽い値は残す | 深い値で上書き |
| Q-6 | 校正の対象 | d3-nnue 20 局 → 20 局版 | 20 局版だけ |
| Q-7 | 読み筋のノード数 | 段 1 のまま・ノード数を書く・状態の一致を別に出す | 段 2 で導線も読み直す |
| Q-8 | 実装の分け方 | D-SCREEN-1(記録)→ D-SCREEN-2(診断と版) | 1 つの STEP |
| **Q-7(置き換え)** | **2026-09-15 司令塔 e3 が §11 で置き換え**: 深い組(`evaluationSource: "deep"` の組)は同じ rescreen 呼び出しの `searchPvsDeep` を使い、軽い組は段 1 のまま。理由: D2 §12.7(`cbb985f`)で compared 37 件のうち N < 6 が 18 件、うち 15 件が 2 手・標識付き(§11 E-12・E-13)。同じ呼び出しの読み筋を写すだけで所要は増えない(E-14)。D2 計画 Q-2 で採らなかった (b) を深い組にだけ採る | — |

## 9. やらないこと・限界

- 4M 一律をやめること・次の棋譜で段 2 だけを使うこと(**校正の後、人間の承認**)。`DRAFT_RULE_1` を変えること
- `replay.ts`・本番の導線・`apps/`・`data/`・`check.ts` と不変条件を変えること。この計画でエンジンを回すこと。100,000 ノードの段 1
- **既知事項の候補(1e の再読み。登録は実装のとき司令塔)**: **K-2** 床は全行を昇順で測るので、一部の行だけを測る本番の段 2 とはエンジンの状態の並びが違い、床は並びで出る差の目安で行ごとの一致を保証しない / **K-3** `screen` の有無と `evaluationSource` の有無の対応はスキーマで縛れない(検証器に条件の語が無い。見張りは S-9・Z-7 の試験だけ)/ **K-4** (d) の notMeasurable は固定例(S-5)だけで変異が無い(実装の後、周辺に「notMeasurable を候補から外す」を足す)/ **K-5** 行数は 130 行(依頼の 120 行を超える。司令塔が了承)
- **限界**: エンジンの状態を行ごとに消す手段が無い(E-10)ので、段 2 の深い値は 4M 一律の値と同じとは言えない(床で測る)。`check.ts`・I-7・I-11 は段 2 でも軽い値で判定する。Failure Event の出どころに `referenceNodes` は無いまま(4M 一律の行を変えないため)

## 10. 事前読み 1e(版 `7388c9b6` の REVISE)と司令塔の決定の取り込み

| 指摘 | 取り込み先 |
|---|---|
| **R-1(必須)** 揺れの床 0 は rescreen に移らない | E-1 の文・E-4・E-10・2. の並びの固定・`deepRun.order`/`measuredOrder`・5. の 0(床と 2 回の再現、食い違いを並びとノード数に分ける)・予-0 |
| **R-2(必須)** バイト一致と v0.5 | 3. の版(`evaluationSource` は `screen` のある記録だけの任意の欄、主張の範囲)・S-9・Z-7 |
| **R-3(必須)** 段 2 の出どころ | 2. の `screen.deepRun`(道具が自分で読む git の状態)・S-12・Z-12 |
| **R-4(必須)** 固定例・変異の抜け | S-5 に notMeasurable・S-11(c)・S-12(記録の形)・Z-6 を S-12 に・Z-10・1. の `rescreenRecords(lines, rule, measure)` |
| S-1 check.ts が読む値 | 3. の最後・9. の限界 |
| S-2 最大の下がりの出どころ | 3. の最大の下がり・S-13・Z-11 |
| S-3 予-3 の分母 | 4.(校正で 1 局を条件どおりに測る)・予-3 |
| S-4 S-1 の直前の値 | S-1 |
| S-5 referenceNodes を写すか | 3. の版(写さない)・9. の限界 |
| S-6 同じ kifuId の 2 本 | E-11・3.・S-14・Z-13 |
| S-7 E-1 の文 | E-1 |
| **再読み(版 `321a274a`、GO)K-1** 同じ kifuId の exit 1 が `records/d-cost` に当たる | E-11・3. の同じ kifuId の規則(司令塔の決定 (a))・S-14・Z-13 |
| 再読み K-2〜K-5 | 9. の既知事項の候補 |

## 11. 追記: 急落の根の読み筋も深い探索から取る(司令塔の依頼、2026-09-15。D2 §12.7 を受けて。書いたのは A。**エンジンは使っていない**。**事前読み f2 の REVISE(版 `cceba809`)と司令塔 e3 の決定を取り込んだ版**)

**依頼の前提との食い違い(先に書く)**: 20 局版の記録は `nodes`・`referenceNodes` とも 4,000,000 で、D2 §12.7 の「2 手・標識付き 15 件」は**既に 4M の探索で出ている**(E-12)。短い読み筋はノード数より「最後に採った info 行が標識付きだった」ことと結び付いている(E-13)。**4M で取り直して N ≥ 6 が上がる根拠は弱い。**形は依頼どおりに書き、この点は予-5 と Q-11 に置く。

| # | 事実 | 場所 |
|---|---|---|
| E-12 | 20 局版(2 人目)の meta は `nodes` 4,000,000・`referenceNodes` 4,000,000。compared 37 件の N ≥ 6 は 19(51.4%)。`pvLength` 2 の 15 件はすべて標識付き、3 以上の 22 件は標識なし | `records/real-02/kifu2-04.jsonl` の meta・D2 計画 §12.7 |
| E-13 | `goMultiPv` は multipv ごとに**最後に解析できた info 行**を採る(標識付きでも)。生の行は `MultiPvGoResult.infoLines` にあるが、`measureEngineReference` は採った行の写し(`searchPvs`)だけを返す。real-01 でも 2 手の 76 本はすべて標識付き | `apps/server/src/engine/usiEngine.ts:217-240`・`engineReference.ts:141-188`・D2 計画 §0.2 |
| E-14 | **`searchPv.ts` に探索の関数は無い**(`toSearchPvObservations` は写すだけ)。`focus_baseline` は `measureEngineReference` の baseline(MultiPV 1)の探索で、戻り値の `searchPvs` に入る。**rescreen が `engineReferenceDeep` を測る呼び出しが、既に深い `focus_baseline` を返している**。戻り値の型 `EngineReferenceMeasurement` は既にある | `apps/server/src/analysis/searchPv.ts:70-87`・`engineReference.ts:116-122`・`:150-158` |
| E-15 | 記録の `searchPvs` は本番の導線(③)の探索の読み筋。ハーネスが別に測った読み筋を同じ欄に入れると区別できなくなるので、ハーネスは `measureEngineReference` の `searchPvs` を捨てる(U6-L 決定 1)。`check.ts` は `searchPvs` を報告に読む | `engineReference.ts:103-115`・`recorder.ts:245-251`・`check.ts:374` |
| E-16 | `searchPvsDeep` に入るのは `focus_baseline` と `focus_after_pass` の 2 本だけ。`counterfactualOf` は `focus_baseline` の multipv 1 しか読まないので足りる | `engineReference.ts:158`・`:165`・`lib/counterfactual.ts:232` |
| E-17 | `bestmoveAtBefore` は直前の行の評価の `bestmove`(深い組では深い探索の値)。`counterfactualOf` は `record.searchPvs` が undefined なら `unrecorded`、null なら `notMeasurable`。Markdown は行頭に「読み筋(③の探索・…)」、節見出しに「読み筋は③の探索で、急落を見つけた評価とは別の探索」と書く | `lib/failureEvent.ts:388`・`lib/diagnosisMoment.ts:47`・`:124`・`lib/counterfactual.ts:221-236`・`:353`・`lib/failureEvent.ts:646` |

**既存の決定との関係**: D2 計画 Q-2 は「読み筋の取り直しはしない・(b) 同じ探索の読み筋を記録に足す、は採らない」だった。§11 は**深い組にだけ (b) の変種**を採る(記録を取り直さず、rescreen が既に行う呼び出しの戻り値を写す。司令塔 e3、2026-09-15)。U6-L 決定 1 の心配(③の読み筋とハーネスの読み筋が区別できなくなる)は、**③の `searchPvs` を変えず、欄の名前(`searchPvsDeep`)と `pvSource` で分ける**ことで守る。Q-7 の「ノード数を行に書く」は `pvSource` で置き換える(8. の Q-7 の行)。

**形(Q-9・Q-10 は推奨どおり。Q-11 は範囲外 ― STEP PV-INFO の候補へ)**
- **段 2(D-SCREEN-1)**: `measure` を `(sfen) → EngineReferenceMeasurement` にし、読み直した行に **`searchPvsDeep: SearchPvObservation[]`** を足す。**中身は `engineReferenceDeep` と同じ呼び出しの `searchPvs` をそのまま写す(再探索しない ― E-14。所要は増えない)**。`searchPvs`(軽い・③の探索)は変えない。読み直していない行はキーを出さない。測れなかったことは `engineReferenceDeep: null` が表す(`searchPvsDeep` は測った分か `[]`。null にしない)。**不変条件(2. に足す)**: `searchPvsDeep` のキーがある ⇔ `engineReferenceDeep` のキーがある。破れたら `diagnose.ts` はその記録を数えない
- **`diagnose.ts`(D-SCREEN-2)**: `counterfactualOf` に渡す `record` を `{ sfen, searchPvs: <出どころの読み筋> }` にする。出どころは**その Event(moment の組)の `evaluationSource`**: `deep` なら直前の行の `searchPvsDeep`、`light` なら `searchPvs`(Q-10。1 件の中で評価と読み筋の出どころを混ぜない)。深い組では不変条件によりキーがあり配列なので、`unrecorded`・`notMeasurable` にはならず、`[]` は `noFocusBaseline` になる。**深い読み筋が無い・短いときも軽いほうへ戻らない**。`counterfactual` の**全状態**に `pvSource: "light" | "deep"` を書く
- **深い組での意味(司令塔の決定 2 の条件 (a)、同日の訂正)**: 深い組では読み筋と `bestmoveAtBefore` が同じ探索から来るので、`pvFirstMoveIsBestmoveAtBefore` は **true になる見込み**。**ただし `bestmoveAtBefore` は `bestmove` 行の値(`engineReference.ts:98`)、読み筋は multipv 1 の最後の info 行(`usiEngine.ts:227-236`)で、行が違う。最後の info 行が標識付きのとき 1 手目は食い違いうる**。欄の定義(読み筋の 1 手目が `bestmoveAtBefore` と一致するか)は変わらず、どの読み筋を比べたかは `pvSource` が言う(K-6)
- **Markdown(条件 (b)・S-3)**: `screen` のある入力では、深い組の行頭を「読み筋(**読み直しの探索(評価値と同じ探索)**・…)」に、軽い組は今の「読み筋(③の探索・…)」のまま。節見出しは `screen` のある入力のときだけ「軽い組の読み筋は③の探索、深い組の読み筋は読み直しの探索(評価値と同じ探索)。light n 件・deep m 件」にする。`screen` の無い入力はバイト一致(3.)
- **版(司令塔の決定 2: MINOR)**: `pvSource` は `evaluationSource` と同じく **`screen` のある記録にだけ書く任意の欄**で、Failure Event v0.5・diagnosis-moment v0.2 に入れる。根拠: `pvFirstMoveIsBestmoveAtBefore` の定義は変わらず、比べた読み筋は新しい任意の欄が言う。`screen` の無い記録はバイト一致。先例は `c16443b` の `evaluationSource`。**スキーマ(条件 (c))**: failure-event v0.4 の `counterfactual` の oneOf は **2 枝**(状態 7 つの enum の枝と compared の枝。どちらも `additionalProperties: false`)で、**両方の枝に任意の `pvSource` を足す**。diagnosis-moment v0.1 は行の 3 変種それぞれに同じ 2 枝があり、同じく足す
- **限界**: `searchPvsDeep` はハーネスの探索で、③が見た読み筋ではない。`check.ts`・不変条件は `searchPvs` を読んだまま変えない

| # | 固定例(偽の `measure`・植えた記録) | 期待 |
|---|---|---|
| S-15 | 深い組。`searchPvsDeep` の focus_baseline 20 手(1 手目 = 深い bestmove。**軽い `engineReference` の bestmove は別の手を植える** ― 軽い bestmove を使う変異が沈黙しないため。f2 の再読み N-1)、`searchPvs` 2 手 | N = 6・`pvLength` 20・`pvSource: "deep"`・`pvFirstMoveIsBestmoveAtBefore: true` |
| S-15b | 深い組。偽の `measure` で `bestmove` ≠ `searchPvsDeep` の focus_baseline の `pv[0]` を植える | `pvSource: "deep"`・`pvFirstMoveIsBestmoveAtBefore: false` |
| S-16 | `screen` あり・軽い組(読み直していない行 / 深く測れなかった行を含む組) | `searchPvs` を使う・`pvSource: "light"` |
| S-17 | 深い組で `searchPvsDeep` も 2 手・upperbound | N = 2・`pvSource: "deep"`・`pvBounded.upperbound` true |
| S-18 | 深い組で `searchPvsDeep` が `[]` | `noFocusBaseline`・`pvSource: "deep"` |
| S-19 | 記録の形 | 読み直した行の `searchPvsDeep` = 同じ `measure` 呼び出しの `searchPvs`・`measure` の回数 = `deepPlies` の数・`searchPvs` は段 1 とバイト一致・S-9 の記録に `pvSource` のキーが無い |
| S-20 | moment: 深い組と軽い組が混ざる局で、選ばれた maxDrop の組の 2 行が深く測れている | `evaluationSource: "light"`(S-13)なので `searchPvs`・`pvSource: "light"` |
| S-21 | moment: 深い組の rise | `searchPvsDeep`・`pvSource: "deep"` |
| S-22 | Markdown: 深い Event と軽い Event が 1 件ずつ | 深い行は「読み直しの探索(評価値と同じ探索)」で「③の探索」を含まない・軽い行は「③の探索」・節見出しに light 1・deep 1 |
| S-23 | `engineReferenceDeep` のキーがあり `searchPvsDeep` のキーが無い行 / その逆 | 数えない |

**変異(中心)**: Z-14 深い組でも `searchPvs` を使う(S-15)/ Z-15 `pvSource` を書かない・いつも light(S-15・S-18)/ Z-16 深い読み筋が短い・無いとき軽いほうへ戻る(S-17・S-18)/ Z-17 `searchPvsDeep` を別の `measure` 呼び出しから取る(S-19)/ **Z-20 moment で「行に `searchPvsDeep` があれば使う」**(Q-10 のほかの案。S-20 が鳴る)/ **Z-21 深い Event の行頭を「③の探索」のまま**(S-22)/ **Z-23 深い組で `pvFirstMoveIsBestmoveAtBefore` を比べずに true と書く**(S-15b)。周辺: Z-18 rescreen が `searchPvs` を上書き(S-19)・Z-19 `screen` の無い記録に `pvSource` を書く(S-19)・Z-22 `searchPvsDeep` ⇔ `engineReferenceDeep` の不変条件を外す(S-23)。

**校正の床に足す(5. の 0.)**: (iv) 2 回の rescreen で `searchPvsDeep` がバイト一致する数(**(iii) の全体のバイト一致に含まれる**。(iii) が崩れたときだけ欄ごとに分けて数える)(v) **同じプロセスで同じ sfen を続けて 2 回 `measureEngineReference`**(4M・NNUE、d3-nnue の急落の根の行)し、`focus_baseline` の `pv`・標識が一致する数(P-33 の同型。P-48 の残りの対照を兼ねる)。**道具は `scripts/playtest/measure-twice.ts`(D-SCREEN-2 の校正の道具に入れる)。エンジン 1 本で、回すセッションが本数を宣言する**(規則 12 番)(vi) 深い `focus_baseline` と 4M 一律の `searchPvs` で、長さ・標識・1 手目が一致する数 (vii) **深い組で `pvFirstMoveIsBestmoveAtBefore` が false の数 / 深い組の compared の数**(標識の有無で分けて並べる)。

| # | 予測(A。見たのは §12.7 の数と E-12〜E-14。深い読み筋はまだ誰も取っていない) | 外れたと言える条件 |
|---|---|---|
| 予-5 | 20 局版の段 2 で、**N ≥ 6 の件数 / `pvSource: "deep"` の compared の件数**が **80% 以上**(司令塔の仮説。**A の見立ては外れ** ― E-12・E-13) | 80% 未満 |
| 予-6 | **2 手・標識付きの件数 / `pvSource: "deep"` の compared の件数**が **25〜55%** | 25% 未満か 55% 超 |
| 予-7 | 床 (iv) は**全行一致**、(v) で `pv` がバイト一致する行 / 測った行は **0〜40%** | (iv) が一致しない |

| # | 点 | 決定・推奨 | ほかの案 |
|---|---|---|---|
| Q-9 | 深い読み筋の取り方 | `engineReferenceDeep` と同じ呼び出しの `searchPvs`(司令塔が受けた) | 別に探索する(所要が倍、同じ探索でなくなる) |
| Q-10 | 読み筋の出どころの決め方 | Event・moment の組の `evaluationSource` に揃える(司令塔が受けた) | 行ごとに `searchPvsDeep` があれば使う(評価と読み筋の出どころが混ざる。Z-20) |
| Q-11 | info 行の採り方 | この STEP では変えない(最後の行)。**STEP PV-INFO の候補**(予-5 の結果を見てから) | 最後の標識なしの行を採る(`apps/` を変える ― 範囲外) |

**既知事項の候補(§11。登録と番号は司令塔)**
- **K-6** 深い組では `pvFirstMoveIsBestmoveAtBefore` が、同じ探索の `bestmove` 行と最後の info 行の食い違いを示す意味になる(定義は同じ。軽い組では別の探索どうしの食い違い)(司令塔の決定 2 の条件 (d)、同日の訂正。実装のときに PHASES へ)
- **K-8** `screen` のある記録と無い記録を混ぜて渡したとき、節見出しの light の件数に `screen` の無い記録を含むかは書いていない(f2 の再読み N-2。実装のときに決めて固定例を置く)
- **K-7** `apps/server/src/analysis/engineReference.ts:103-115` と `recorder.ts:245-251` の「ハーネスは読み筋を捨てる」の注記は、段 2 が同じ戻り値の `searchPvs` を `searchPvsDeep` として記録に写すようになっても古いまま残る(D-SCREEN は `apps/` を変えない。注記を直すのは `apps/` に触る次の STEP)

**事前読み f2(版 `cceba809` の REVISE)の取り込み**: R-1 → 状態の行・§1・§3・§5 の 1.・予-4・8. の Q-7 の行・「既存の決定との関係」/ R-2 → E-17・「深い組での意味」・Markdown・版(2 枝)・K-6(司令塔の同日の訂正で S-15b・Z-23・床 (vii) を足した)/ R-3 → S-20〜S-22・Z-20・Z-21 / S-1 → E-16 / S-2 → 段 2 の不変条件・`diagnose.ts` の入力・S-23・Z-22 / S-3 → Markdown / S-4 → 床 (iv) (v) / S-5 → 予-5〜予-7 / S-6 → E-14 / S-7 → K-7

## 12. 実装の記録(D-SCREEN-1。worktree `wt-dscreen1`、基点 `d3cbdc9`。**エンジンは使っていない**。書いたのは B)

**範囲**: 司令塔 e3 の確認(2026-09-15)で、Q-8 のとおり**記録の側だけ**。
- この STEP でやったこと: 選び方・`rescreenRecords`・`rescreen.ts`・記録の形(`engineReferenceDeep`・`searchPvsDeep`・meta の `screen`)・見張り
- D-SCREEN-2 に回すもの: `diagnose.ts` の規則(§3)・「数えない」不変条件の判定・`pvSource`・Failure Event と diagnosis-moment の版・Markdown・校正の道具
  - 版の番号は、先にスキーマをコミットした方が v0.5・moment v0.2 を取る(D2.5 計画 Q-3)

### 12.1 変えたファイル(sha256)

| ファイル | sha256 | 行 |
|---|---|---|
| `scripts/playtest/lib/rescreen.ts`(新規) | `f99363d92698ec3d77e32e68094b7eb1eb6e5b262267395f55f020cdff44bbec` | 216 |
| `scripts/playtest/lib/rescreen.test.ts`(新規) | `ee09901b229bd03ed9c0093d325f4c68b1453f5a13eda1a7ed0879e1ff0dbc35` | 290 |
| `scripts/playtest/rescreen.ts`(新規) | `2452c27683856f0f2834eb7be9f927f9cc9a566312a565f98cdde2eee6675874` | 79 |
| `scripts/playtest/rescreen.test.ts`(新規) | `398bf7298573a1dc92db4f7141e0a07d2e83d5b244cade475bd6711e44cd880f` | 95 |
| `scripts/playtest/invariants/types.ts` | `885b02476f9b8a2a3e0118e38dcb8dc9c6a3bee9f4025615c4b83ec3abc7298d`(基点 `4e44301c…`。+24 / −5、差分 `scratchpad/dscreen1-types-diff.out`) | — |

### 12.2 実装で決めた点(§2・§11 の文だけでは決まらなかったもの)

- **I-1** (d) の「理由」は、`pairEvaluations` の reason をそのまま使う。
  - 直前の行が王手中で直後が notMeasurable の組は、reason が直前の側(`notMeasuredInCheck`)になり、候補にしない。
  - `unrecorded`・`mateBefore` も候補にしない。
- **I-2** 読み直す 4 行に王手中・終局の行が入っても、`measure` を呼ぶ(`measureEngineReference` が null を返す)。
  - `deepPlies` の数 = `measure` の回数 = `measuredOrder` の長さ。
- **I-3** 候補の組と読み直す行は、ready 行の並びの位置で決める(i − `before` 〜 i + `after`、端は切る)。
  - 規則は `DRAFT_SCREEN_RULE_1 = { dropCp −300, advantageCp 300, advantageDropCp −200, before 1, after 2 }` を lib の 1 か所に置いた(draft)。
- **I-4** `screen.lightNodes` は、段 1 の meta の `referenceNodes` から取る。
- **I-5** 段 1 として受け付けない入力は、`RescreenInputError` で止めて書かない。
  - 対象: meta 行がちょうど 1 つでない・meta に `screen` がある(段 2 の記録)・`referenceNodes` が正の整数でない・同じ ply の ready 行が 2 つ以上。
  - CLI は、**エンジンを起こす前に** `planRescreen` で確かめる。`--out` が入力と同じパスなら止める(段 1 のファイルは変えない)。
- **I-6** 出力の組み立て。
  - 読み直していない行(immediate 行・error 行を含む)と、改行の並びは、段 1 のバイト列のまま出す。
  - 読み直した ready 行と meta 行だけを JSON に組み直し、新しい欄を**後ろに足す**。段 1 の欄の値と並びは変えない。
- **I-7** 読み直した行の値。
  - `engineReferenceDeep` = 戻り値の `reference`(null もキーを残す)。
  - `searchPvsDeep` = **同じ呼び出し**の `searchPvs`(0 本なら `[]`。null にしない)。
  - `engineReference`・`searchPvs`(段 1)は変えない。
- **I-8** `screen.deepRun` の欄は `gitHead`・`dirty`・`enginePath`・`threads`・`startedAt`・`order: "plyAscending"`・`measuredOrder`。
  - `gitHead`・`dirty` は、道具が `readGitState` で自分で読む。段 1 の meta も、渡された値も使わない。
  - `dirtyPaths` は写さない(§2 の欄のとおり)。
- **I-9** `invariants/types.ts` に足した欄。
  - `RecordLine`: `engineReferenceDeep?`・`searchPvsDeep?`
  - `MetaLine`: `referenceNodes?`(replay.ts が既に書いていた欄の型)・`screen?`
  - 3 値の表に 2 列を足した。これらの「欄が無い」は、その STEP より前の記録ではなく、**段 2 で読み直していない行**である。
- **I-10** §2 の不変条件で記録を「数えない」判定は、`diagnose.ts` が読む側なので D-SCREEN-2 に回した。
  - 対象: `nodes`・`deepPlies` = 行の欄 = `measuredOrder`、`searchPvsDeep` ⇔ `engineReferenceDeep`。
  - この STEP では、書く側がこの形で書くことを S-12・S-19 で見張る。
- **I-11**(監査 f2 の N-3)`rescreenRecords` の引数は、計画 §1 の `(lines, screenRule, measure)` ではなく `(source のバイト列, rule, measure, run)` にした。
  - バイト列で受けるのは、`screen.sourceSha256` を段 1 のバイト列から道具が自分で計算し、読み直していない行を段 1 のバイト列のまま出すため。
  - `run` は深い回の出どころ(`deepNodes`・`enginePath`・`threads`・`startedAt`・git を読む場所)。
- K-7(`engineReference.ts`・`recorder.ts` の「ハーネスは読み筋を捨てる」の注記)は、`apps/` に触らないので古いまま。

### 12.3 試験・型検査(worktree の根から)

- **予測は実装の前に書いた**: `scratchpad/dscreen1-predictions.md`(`09bfb83fd9495b55d64be565ae264e1b87013f14a30eff7d354a6a91ef06b412`、13:45:15Z)

| # | 予測 | 実測 | 判定 |
|---|---|---|---|
| P-1 | 基点の scripts/playtest は 610 件通過 | 610 件 | 的中 |
| P-2 | 足す試験は 18〜26 件 | 20 件(lib 18・CLI 2) | 的中 |
| P-3 | typecheck:scripts は rc 0 | rc 0 | 的中 |
| P-4 | 変えるのは 5〜6 本(計画書を含む) | コード 5 本 + 計画書 | 的中 |
| P-5 | 変異は全部鳴る | 11/11 | 的中 |

- **全件**: 46 ファイル・**630 件通過**(610 + 20)
- **固定例(§6・§11 のうち D-SCREEN-1 の分)**
  - S-1・S-2・S-3・S-4・S-5(王手中・終局の組を含む)・S-11・S-12・S-19
  - 足したもの:
    - (a) と (b) の両方の理由
    - 端でない組の 4 行
    - 候補が無いとき(読み直す行も measure の呼び出しも無い)
    - 測れなかった行(null のキーを残す)
    - 入力の誤り 5 通り
    - `planRescreen` の戻り値
    - CLI のソース照合
    - CLI の子プロセス(エンジンを起こさずに exit 1 で止まる 4 通りと、git status 不変)
  - 司令塔の範囲の文には S-11 が無いが、Z-10 の見張りなので入れた。

### 12.4 変異(規則 11.3・11.8)

- **道具**: `scratchpad/dscreen1-mutate.py`(`86601e42b8e3bc2a02c69b45cb2e001c9b7e87bc4680aaa6ee989a9da0f0bfaa`)。予測は、実装と試験の後・当てる前に、道具の中に試験の単位で書いた。
- **出力**: `scratchpad/dscreen1-mutate.out`(`272c3603b1026394b516fb07b2a9944abb0481d4887455b7aa0b007965211f1f`)。道具の sha と当てた結果を、同じ逐次コマンドで記録した。
- 校正は exit 0・20 件。当てた後、2 ファイルとも元のバイト列に戻ったことを sha で確かめた。
- **適用 11 / 鳴った 11 / 沈黙 0 / 適用できなかった 0。中心 6/6。予測 11/11**
- エンジンを起こす経路に届く CLI の変異(確かめを外す・同じパスの止めを外す)は入れていない。worktree にエンジンが無く、この STEP はエンジンを使わない。

| # | 変異 | 中心 / 周辺 | 鳴った試験 | 予測 |
|---|---|---|---|---|
| Z-1 | 候補の閾値 (a) を −400 | 中心 | S-1・S-3・S-4・S-12・S-19・測れなかった行・planRescreen | 的中 |
| Z-2 | 読み直す行を i・i+1 だけ | 中心 | S-3・S-4・S-12・S-19・測れなかった行・planRescreen | 的中 |
| Z-6 | `engineReference` を深い値で上書き | 中心 | S-12 | 的中 |
| Z-8 | 重なりを除かない | 周辺 | S-4・S-12・S-19 | 的中 |
| Z-9 | 王手中の組を候補にする | 周辺 | S-5 | 的中 |
| Z-10 | (c) を候補から外す | 中心 | S-11 | 的中 |
| Z-12 | `deepRun.gitHead` に段 1 の meta を写す | 中心 | S-12 | 的中 |
| Z-17 | `searchPvsDeep` を別の `measure` 呼び出しから取る | 中心 | S-12・S-19 | 的中 |
| Z-18 | `searchPvs` を深い読み筋で上書き | 周辺 | S-12・S-19 | 的中 |
| K-4 | (d) の notMeasurable を候補から外す(1e の再読み K-4) | 周辺 | S-5 | 的中 |
| C-1 | 深い回の Threads を 2(CLI) | 周辺 | CLI のソース照合 | 的中 |

### 12.5 残っていること

- **D-SCREEN-2**: §3 の規則、`deepUnavailable`、記録を数えない不変条件(S-8・S-23)、`pvSource`、版、Markdown、S-6〜S-10・S-13〜S-18・S-20〜S-22、校正の道具(`scan-compare` の Event 単位・`measure-twice.ts`)
- **校正**(§5・§11 の床): エンジンを持つセッションが本数を宣言して回す
- **載せ替え**: 基点 `d3cbdc9` から最新の HEAD への載せ替えと測り直しは、司令塔が行う
- **限界**(監査 f2 の N-4): 次の 2 つは試験で見ていない。
  - CLI がエンジンを起こして深く測る経路(エンジンが要る。校正の実行で初めて通る)
  - 読み直した行のうち段 1 の欄の部分が、段 1 とバイト一致すること(S-12 は欄の並びと値で見る。段 1 が `JSON.stringify` で書かれていれば一致する)

### 12.6 監査 f2 の GO の後の気づき N-1〜N-4 の取り込み(司令塔 e3 の決定。**試験と文書だけで、lib と CLI は変えていない**)

- **変えたのは `scripts/playtest/lib/rescreen.test.ts` だけ**(`ee09901b…` → **`ba322f2b035921f7212d71cf692afa2e135dfbe25159704b14a658da5bdbec62`**)。差分は `scratchpad/dscreen1-revise-diff.out`(`e02b6289…`、+13 / −1)。ほかの 4 本は 12.1 のまま(`rescreen.ts` `f99363d9`・`rescreen.ts`(CLI)`2452c276`・`rescreen.test.ts`(CLI)`398bf729`・`invariants/types.ts` `885b0247`)
- **N-1**: 偽の git の `git status` が、数える対象のパス 1 つを返すようにした。
  - 深い回は `dirty: true`、段 1 の META は `dirty: false` で、値が違う。
  - S-12 に `git.dirty === true`・`inMeta.gitHead === "stage1head"`・`inMeta.dirty === false` を足した。
- **N-2**: S-5 に終局の組を足した。
  - GAME01 の直前の行 54 に測れた値を植え、組 54→56 を作る。reason は `notMeasuredGameEnd`、side は `to` で、`pairEvaluations` の値で確かめる。
  - この組が候補にならないことを確かめる。題は変えていない。
  - 本物の記録では王手中の行は null なので、この植え方は reason を作るためだけのもの。
- **N-3** → 12.2 の I-11。**N-4** → 12.5 の限界。
- 2 つの試験ファイルは 20 件、typecheck:scripts は rc 0、**全件は 630 件通過**(件数は変わらない。既存の 2 件に主張を足した)。
- **変異 2 本**
  - 道具: `scratchpad/dscreen1-revise-mutate.py`(`84caabb8…`)。予測は試験を直す前・当てる前に道具の中へ書き、道具と直しの道具 `dscreen1-revise-edit.py`(`ec8ff22d…`)の sha を、同じ逐次コマンドで記録した。
  - 出力: `scratchpad/dscreen1-revise.out`

| 変異 | 直す前(予測 → 結果) | 直した後(予測 → 結果) |
|---|---|---|
| N-1 `deepRun.dirty` を段 1 の meta から写す | 沈黙 → 沈黙(f2 の観測を再現) | S-12 → **S-12 だけ鳴った** |
| N-2 (d) に `notMeasuredGameEnd` を足す | 沈黙 → 沈黙 | S-5 → **S-5 だけ鳴った** |

  - 予測 4/4。校正は 2 回とも exit 0・20 件。
  - 当てた後、`lib/rescreen.ts` は `f99363d9` に戻った。

## 13. 実装の記録(D-SCREEN-2。worktree `wt-dscreen2`、基点 `f39fd21`。**エンジンは使っていない**。書いたのは B)

**範囲**(司令塔 e3 の合図と確認、2026-09-15):
- この STEP でやったこと: `diagnose.ts` の規則(§3)、`pvSource`・`evaluationSource`、校正の道具、固定例 S-6〜S-10・S-13〜S-18・S-20〜S-23(S-11 は D-SCREEN-1 で入れ済み)
- **版**: Failure Event v0.6・diagnosis-moment v0.3 として書いた。D2.5(1e)が先に v0.5・v0.2 のスキーマをコミットする前提(D2.5 計画 Q-3「先にスキーマをコミットした方が取る」)
  - 版の文字列と、スキーマのファイルがある版の並びは `lib/schemaVersions.ts` の 1 か所に置いた
  - 載せ替えの前(`wt-dscreen2`、13.2〜13.4)の v0.6 は「v0.4 + D-SCREEN の欄」で、並びの 0.5 が抜けていた。**コミットでは連番にする**(司令塔 e3)
  - D2.5 が `e9e7bf2` で先に v0.5・v0.2 を入れたので、B が `wt-dscreen2r` に載せ替え、同じ道具を基の版 0.5・0.2 に当てて作り直した(13.6)

### 13.1 設計の決め(計画の文だけでは決まらない点。実装の前に `scratchpad/dscreen2-predictions.md` に書いたとおり)

- **X-1 深い値を使う組**
  - 組の 2 行とも `engineReferenceDeep` のキーがあり、その値を `evaluationOf` に掛けた状態が measured のときだけ、2 行とも深い値にする。ほかは 2 行とも軽い値
  - 深い組は、行の `engineReference`・`searchPvs` を深い欄に差し替えた行として渡す(評価も読み筋も同じ読み直しの探索から取る ― §11)
- **X-2 deepUnavailable**
  - 読み直したのに(キーがある)、深い状態が notMeasurable か notEvaluation の行を含む組を数える
  - 王手中・終局で測らなかった行(notMeasuredInCheck・notMeasuredGameEnd)は数えない
- **X-3 件数の数え方**
  - 表「評価の状態と組」の行の件数(ready 行・測った…)は、段 1 の値のまま
  - 組の件数と Failure Event は、組ごとに選んだ出どころで数える
- **X-4 規則の置き場所**
  - 新しい `lib/screenDiagnosis.ts` に置いたもの: 組の出どころ・不変条件・段 2 とその段 1 の組・Markdown の節
  - `failureEvent.ts`・`diagnosisMoment.ts`・`counterfactual.ts`・`failureEventSchema.ts`・`diagnose.ts` には「出どころを受けて渡す」だけを足した
- **X-5 数えない記録(S-8・S-23)**
  - 対象:
    - screen の形が違う
    - ready 行の `engineReference.nodes` ≠ lightNodes、`engineReferenceDeep.nodes` ≠ deepNodes
    - 深い欄を持つ ready 行の集合・deepPlies・measuredOrder が一致しない
    - `searchPvsDeep` と `engineReferenceDeep` のキーの有無が食い違う
    - ready でない行に深い欄がある
    - screen が無いのに深い欄がある
  - 扱い: `InvalidScreenRecordError` を投げ、`buildDiagnosisReport` が「数えられなかった」の行にする
- **X-6 段 2 とその段 1(S-14)**
  - `diagnose.ts` が表を書く前に確かめ、名前を並べて `ScreenInputConflictError` で exit 1 にする(判定は lib の純粋関数)
  - 止める組: (i) screen のある入力の `sourceSha256` が、別の入力の sha256 と同じ (ii) 同じ kifuId に、screen のある入力と無い入力がある
  - 同じ kifuId の screen の無い入力どうし・screen のある入力どうしは、今のまま通す
- **X-7 最大の下がり(S-13・S-20)**
  - 組ごとの出どころで compared になった組の出どころが 2 種類なら、全部の組を軽い値で作り直して選ぶ(excludedPairs も選んだほうの組で数える)
  - rise は組ごとの出どころのまま(S-21)
- **X-8 欄の置き場所**
  - `evaluationSource` は Event の `branch` の最後、moment の組の行では `evaluationAfter` の後ろ
  - `pvSource` は counterfactual の `state` の直後
  - どちらも screen のある記録だけに書く
  - 出どころの meta の `screen`: deepPlies・measuredOrder を除き、deepRun.enginePath は根からの相対、dirty は DirtyState の 4 値。置き場所はそろえ・打ち切りの欄の後ろ・unrecordedKeys の前
  - screen の無い記録はキーを出さない
- **X-9 Markdown(K-8 の決め)**
  - screen のある入力があるときだけ、読み筋の節の見出しを §11 の文にする
    - light・deep は、screen のある記録の Event だけを数える
    - screen の無い記録の Event があれば「・screen の無い記録 k 件」を足す
  - 新しい節「## 読み直し(STEP D-SCREEN。meta に screen のある記録だけ)」を足す
  - 深い組の行頭は「読み筋(読み直しの探索(評価値と同じ探索)・…)」
  - compared でない深い行は「読み筋(読み直しの探索(評価値と同じ探索)): …」で、noFocusBaseline の文から「③の」を外す
- **X-10 スキーマ**
  - 道具 `scratchpad/dscreen2-schema-gen.py`(基の版を引数に取る)で、基の版に任意の欄を足して作った。古い版のファイルは変えていない
  - 今の版が「基の版 + D-SCREEN の欄」であることを試験で見る(`FAILURE_EVENT_SCREEN_BASE_VERSION`・`DIAGNOSIS_MOMENT_SCREEN_BASE_VERSION`)
- **X-11 校正の道具**
  - `lib/screenCalibration.ts`(純粋関数)に置いたもの:
    - Event の集合の一致・相手にだけある・段 2 にだけある
    - counterfactual の状態の一致(pvSource ごとの分子・分母)
    - 深い組の 1 手目(標識の有無で分ける)
    - 床の行 (i)・(vi)
    - 2 回の rescreen (iii)・(iv)(meta は deepRun の startedAt・gitHead・dirty を除く)
    - 同じ局面の 2 回の測定 (v)
    - measure-twice の測る行の決め方
  - CLI は 2 本: `screen-calibrate.ts`(記録を読むだけ)・`measure-twice.ts`(エンジンを起こす。試験はソース照合と、起こさずに止まる経路だけ)
  - 床は全 ready 行を読み直す必要があるので、`rescreen.ts` に `--all-plies`(lib の `allPlies`)を足した。D-SCREEN-1 のファイルに触った
- **X-12 校正の lib の置き場所**(監査 N-7): §5 の「`scan-compare.ts` の lib を Event の単位に広げる」とは違い、新しい `lib/screenCalibration.ts` に置いた(`scan-compare.ts` とその lib は変えていない)
- **K-8(§11 の既知事項の候補)** は X-9 で決めて、固定例を置いた
- **K-7**(`apps/` の「ハーネスは読み筋を捨てる」の注記)は、`apps/` に触らないので古いまま

### 13.2 変えたファイル(sha256。worktree の `scripts/playtest/` から)

| ファイル | sha256 | 行 |
|---|---|---|
| `lib/schemaVersions.ts`(新規) | `a1f06e760842f9699f764e477bfe4a8a333efefe34e1f3886bded040c0dacdf6` | 21 |
| `lib/screenDiagnosis.ts`(新規) | `106d8d5d1844967445944188b8e11611cb39877a0e6f4435a59a34779a6bd3b8` | 272 |
| `lib/screenDiagnosis.test.ts`(新規) | `1879c4110fe5c8c5af65921361d85289ecc1282e2ab28beb4824ac6560b782f9` | 530 |
| `lib/screenCalibration.ts`(新規) | `96a89222b5e8dc5e8ca9c55a8b1dba82fdf841c42ff16473ada5007357b90992` | 344 |
| `lib/screenCalibration.test.ts`(新規) | `52770fc3d7d4a9ca5343ca11fb8a9d141ade9289aff621f4d5016dc364497091` | 182 |
| `screen-calibrate.ts`(新規) | `a7b298dc792fbd5f22dc510e8a5ee109b19c5f3b0c4a18d8cb3704001c3041c7` | 88 |
| `screen-calibrate.test.ts`(新規。measure-twice.ts の見張りも持つ) | `e8a25e0ad9d1374d44a5f6ff09481235c3b10273946e4a5a205d2379d034e043` | 160 |
| `measure-twice.ts`(新規) | `dc3725aa8d51606a6c8adfc4dd69b5bc3e27c6bf7484e96a42d4356a8ab8fcda` | 114 |
| `schemas/failure-event.v0.6.schema.json`(新規) | `9c163f527d496b91c09daaab7f5bfd38b141dc5b9c43446f748f64d00365cd31` | 3132 |
| `schemas/diagnosis-moment.v0.3.schema.json`(新規) | `036e81ce01c0d64a0f87aff78a3a4795d022f0072f2a63d94224e48b5cda8e09` | 12500 |
| `lib/failureEvent.ts` | `0d5f693a02e0cafa80118b1095e4ff831991feee09fa1e2b94b05916dfc7936d` | 685 |
| `lib/diagnosisMoment.ts` | `49a2a8b92534d32ce1845b721fd023f67d3c779a54330923f0a909b7badacd7f` | 220 |
| `lib/counterfactual.ts` | `085c1b55d369dfc54d5bfd00848808aef2a66c8a5b4818f9449646aa3bb7c341` | 365 |
| `lib/failureEventSchema.ts` | `eb1f221c3ca23aacaecef245fe898b8654d4569548a7c28877fb4615c46a104e` | 275 |
| `diagnose.ts` | `254d9d055ec8b4769a9a1b452e784f1edf62f93cc4501a504c01a27e35ec5f12` | 153 |
| `lib/rescreen.ts`(D-SCREEN-1 のファイル。`allPlies`) | `ad7af055e23a28ad5ca4265fc32f96fd4081f69f7d2e08d1fc17f97951fcf5ea` | 234 |
| `rescreen.ts`(D-SCREEN-1 のファイル。`--all-plies`) | `bfbd87ce612801733c41b98cb0681deb0ad74916b2d376d90bd69780722b2f27` | 81 |
| `diagnose.test.ts` | `9608ceb56c875137c1bd84cda35f9601e040d5b49dfbb6f4fc019738e182d66c` | 656 |
| `lib/counterfactual.test.ts` | `c8c37784905bb227c206a31f05be8013c33bee700c020087c234326dd2bcc5b7` | 386 |
| `lib/diagnosisMoment.test.ts` | `2b5b9ab35a7e82ea8e6e7ced944b0b075bbef4f5d86e6f6243daa842011ce98e` | 419 |
| `lib/failureEventSchema.test.ts` | `b587be1acc8c839e2564ca07143319026996875c5dda9fc3b97bf09dbb9490e4` | 1031 |
| `lib/rescreen.test.ts` | `4415fc589db7bf4cd17c1b6a9ed3a139ff99b25de1ffa0117cb44b9d567b7a66` | 313 |
| `rescreen.test.ts` | `35087cf9287f28e4cd65ec470c81f93abb65cdbb9e0c0b05b8adefe91d4bb4a1` | 98 |

- 変更した 13 本の差分: `scratchpad/dscreen2-diff.out`(`84f7a165…`、+269 / −65)。新規 10 本は差分に入らない
- スキーマの道具: `scratchpad/dscreen2-schema-gen.py`(`9c93ea89…`)を `<worktree> 0.4 0.6 0.1 0.3` で回した。古い版の 5 ファイルは sha が変わらないことを道具の中で確かめた
- 既存の試験で直したのは、今の版の文字列を見ていたところだけ(値 → `lib/schemaVersions.ts` の定数)と、source 照合の 1 行。v0.4 の構造の試験は v0.4 のファイルを読むようにした。0.6 → 0.4 → 0.3 → 0.2 → 0.1 の鎖に 0.4 の段を足した

### 13.3 試験・型検査と予測(worktree の根から)

- **予測は実装の前に書いた**: `scratchpad/dscreen2-predictions.md`(`24e563d3ee7a54bd67f3699e27d90eca865f911f6f6729e8aff0dff3aa28b227`、14:21:38Z)

| # | 予測 | 実測 | 判定 |
|---|---|---|---|
| Q-1 | 基点の scripts/playtest は 643 件 | 643 件(司令塔のコミットの記録。この worktree の全件 691 − 足した 48) | 的中 |
| Q-2 | 足す試験は 45〜80 件 | **48 件**(screenDiagnosis 33・screenCalibration 9・CLI 4・rescreen 1・diagnose の S-14 1) | 的中 |
| Q-3 | typecheck:scripts は rc 0 | rc 0 | 的中 |
| Q-4 | screen の無い記録でバイト一致 | 下の表のとおり全部一致 | 的中 |
| Q-5 | 変異は全部鳴る | 27/27 | 的中 |
| Q-6 | 変えるファイルは 14〜22 本 | **23 本**(新規 10・変更 13)+ 計画書 | **外れ**(rescreen の `--all-plies` と、版の定数に移した既存の試験 4 本が、見立てより多かった) |

- **全件**: 49 ファイル・**691 件通過**
- **screen の無い記録のバイト一致(S-9・Q-4)**
  - 手順: f39fd21 の worktree(`wt-dscreen2-base`)と新しい worktree で、同じ記録に `diagnose.ts … --events --events-rise --events-maxdrop` を掛けて比べた
  - 道具: `scratchpad/dscreen2-g9-base.py`・`dscreen2-g9-base-real.py`(基点)、`dscreen2-g9-compare.py`(`83f56d01…`)
  - 出力: `dscreen2-g9-compare.out`(`b38404b5…`)
  - 比べた記録: コミット済みの 9 か所・94 本。**real-03 の kifu-01・04・07・09(1 人目の後手 4 局)は、D3 の定義承認まで開かないので掛けていない**
  - **Markdown 9/9 がバイト一致**
  - **--events・--events-rise・--events-maxdrop の 559/559 行が、`schemaVersion` と `provenance.analysis` を除いて一致**(欄の並びも比べた)
  - **新しい欄の文字列(evaluationSource・pvSource・screen)の漏れ 0**

### 13.4 変異(規則 11.3・11.8)

- **道具**: `scratchpad/dscreen2-mutate.py`(`76c66f9c2bde71350d4037959ced6719712a4be3dc1df7a2990e85700b292d1a`)。予測は、実装と試験の後・当てる前に、道具の中に試験の単位で書いた
- **出力**: `scratchpad/dscreen2-mutate.out`(`70d081f7fabdadcbea55e446b31106c9e3541913c4f95bda213e7f20b23825b5`)。道具と予測のファイルの sha を、同じ逐次コマンドで記録した
- **試験の範囲**: 新しい試験 5 ファイル(67 件)で当てた。全件は変異なしで回した
- 校正は exit 0・67 件。当てた後、9 ファイルとも元の sha に戻った
- **適用 27 / 鳴った 27 / 沈黙 0 / 適用できなかった 0。中心 12/12。予測 27/27**
- エンジンを起こす経路に届く変異は入れていない

| # | 変異 | 中心 / 周辺 | 鳴った試験 |
|---|---|---|---|
| Z-3 | 混ざった組で、深く測れた行だけ深い値 | 中心 | S-6・S-16・X-3 |
| Z-4 | 深く測れなかった行を含む組を数えない | 中心 | S-7 |
| Z-5a | ノード数の不変条件を外す | 中心 | S-8(lightNodes・deepNodes) |
| Z-5b | deepPlies・measuredOrder の不変条件を外す | 中心 | S-8(deepPlies・measuredOrder) |
| Z-7 | screen の無い記録にも evaluationSource | 中心 | S-9 の行 |
| Z-11 | 最大の下がりで出どころを混ぜる | 中心 | S-13・S-20 |
| Z-13a | 段 2 とその段 1(sha の一致)を通す | 周辺 | S-14 (i) |
| Z-13b | screen の無い同じ kifuId も止める | 周辺 | S-14 (iii) |
| Z-14 | 深い組でも searchPvs を使う | 中心 | S-15・S-15b・S-17・S-18・S-21・S-22・校正の Event |
| Z-15 | pvSource をいつも light | 中心 | S-15・S-15b・S-17・S-18・S-21・S-22・段 2 の行 |
| Z-16 | 深い読み筋が短い・無いとき軽いほうへ戻る | 中心 | S-17・S-18 |
| Z-19 | screen の無い記録にも pvSource | 周辺 | S-9 の行 |
| Z-20 | moment で行に searchPvsDeep があれば使う | 中心 | S-20 |
| Z-21 | 深い Event の行頭を「③の探索」のまま | 中心 | S-22 |
| Z-22 | searchPvsDeep ⇔ engineReferenceDeep の不変条件を外す | 周辺 | S-23 の 2 件 |
| Z-23 | 深い組で pvFirstMoveIsBestmoveAtBefore を比べずに true | 中心 | S-15b・校正の Event |
| P-1 | 王手中で測らなかった行も深く測れなかった数に入れる | 周辺 | S-7 |
| P-2 | 見出しの light に screen の無い記録の Event を入れる | 周辺 | K-8 |
| P-3 | 出どころの screen に deepPlies も写す | 周辺 | 段 2 の行・スキーマの境目 |
| P-4 | 今の版の文字列を基の版にする(1 か所の定数) | 周辺 | 段 2 の行・moment の構造・スキーマの境目 |
| P-5 | Event の集合のキーから当たり方を落とす | 周辺 | 校正の Event・キー |
| P-6 | 状態の一致の分母に相手の無い Event を入れる | 周辺 | 校正の Event |
| P-7 | 2 回の rescreen の meta で startedAt も比べる | 周辺 | 2 回の rescreen |
| P-8 | rescreen の allPlies を無視する | 周辺 | allPlies |
| P-9 | measure-twice が 1 回だけ測って使い回す | 周辺 | measure-twice のソース照合 |
| P-10 | 深い組の noFocusBaseline の文に「③の」を残す | 周辺 | 深い組の compared でない状態 |
| P-11 | 読み直しの節を描かない | 周辺 | S-22・K-8 |

- **P-4 の限界**: 今の版の文字列を基の版にしても、「今の版の Failure Event のスキーマは基の版 + D-SCREEN の欄」の試験そのものは通る(比べる 2 つが同じファイルになる)。鳴らしているのは、段 2 の行・moment の構造・境目の試験である

### 13.5 残っていること・限界

- **載せ替え**: 済み(13.6)。コミットするのは `wt-dscreen2r` の版
- **校正の実行**(§5・§11 の床)
  - 回すのは C(エンジン)
  - 床の手順: `rescreen.ts --all-plies --deep-nodes 4000000` を d3-nnue に 2 回 → `screen-calibrate.ts --base <d3-nnue> --stage2 <1 回目> --stage2-repeat <2 回目>` → `measure-twice.ts` を急落の根に
  - 本番の形の手順: 段 1(400k)→ `rescreen.ts` → `screen-calibrate.ts --base <4M 一律>`
- **試験で見ていないこと**: `screen-calibrate.ts` の数は記録を読むだけで試験で見ているが、`measure-twice.ts` と `rescreen.ts` のエンジンを起こす経路は試験で見ていない(エンジンが要る)
- **既知事項の候補(登録と番号は司令塔)**: 床の (iii) は、2 回の rescreen の meta を deepRun の startedAt・gitHead・dirty を除いて比べる。2 回が同じコードで回ったかは、報告を読む人が gitHead で見る
- **既知事項の候補(登録と番号は司令塔)**: 床の段 2 の `allPlies: true`(13.7 の N-6)は出どころ(provenance)に写さない。床の出力を `diagnose.ts` に掛けると、Failure Event と moment の行からは本番の段 2 と区別できない(記録の meta では読める)

### 13.6 載せ替えの記録(D2.5 `e9e7bf2` の上へ。worktree `wt-dscreen2r`。**エンジンは使っていない**。書いたのは B)

- **手順**(司令塔 e3 の合図): 監査中の `wt-dscreen2`(`f39fd21`)は変えず、`e9e7bf2` の新しい worktree に取り込んだ
- **衝突の解き方**: D2.5 は欄を足しただけなので、両方を残した
  - `branch` は `standingPair` の後に `evaluationSource`(X-8 の「branch の最後」は変わらない)。moment の組の行も `standingPair` の後
  - D2.5 が書いていた版の文字列は `lib/schemaVersions.ts` の定数にした
  - `buildProvenance` の引数(D2.5 の `standingBounds`・`positionFactsRules`)を D-SCREEN の試験にも渡した
- **版**: `KNOWN_SCHEMA_VERSIONS` = 0.1〜0.6、`KNOWN_DIAGNOSIS_MOMENT_SCHEMA_VERSIONS` = 0.1〜0.3(連番)。`FAILURE_EVENT_SCREEN_BASE_VERSION` = 0.5、`DIAGNOSIS_MOMENT_SCREEN_BASE_VERSION` = 0.2
- **スキーマ**: `scratchpad/dscreen2r-schema-gen.py`(`ba4694c0…`)を `<worktree> 0.5 0.6 0.2 0.3` で回した。古い版のファイル(FE 0.1〜0.5・moment 0.1〜0.2)は変えていない
  - 基の版からの差分: `scratchpad/dscreen2r-failure-event.v0.6-from-base.diff`(`058989eb…`)・`dscreen2r-diagnosis-moment.v0.3-from-base.diff`(`cff927c1…`)
- **試験で直したところ**: 版の鎖を 0.6 → 0.5 → 0.4 → … にし(D2.5 の欄を剥がす段は 1e の道具のまま)、D2.5 の v0.5 の構造の試験は v0.5 のファイルを読むようにした

#### 13.6.1 変えたファイル(sha256。worktree の `scripts/playtest/` から。13.2 と違うものに ◆)

| ファイル | sha256 |
|---|---|
| `lib/schemaVersions.ts`(新規)◆ | `24157012633892b1…` |
| `lib/screenDiagnosis.ts`(新規) | `106d8d5d18449674…` |
| `lib/screenDiagnosis.test.ts`(新規)◆ | `e2c0c1e1…` |
| `lib/screenCalibration.ts`(新規) | `96a89222b5e8dc5e…` |
| `lib/screenCalibration.test.ts`(新規) | `52770fc3…` |
| `screen-calibrate.ts`(新規) | `a7b298dc…` |
| `screen-calibrate.test.ts`(新規) | `e8a25e0a…` |
| `measure-twice.ts`(新規) | `dc3725aa8d51606a…` |
| `schemas/failure-event.v0.6.schema.json`(新規)◆ | `637a6814…` |
| `schemas/diagnosis-moment.v0.3.schema.json`(新規)◆ | `97e4c45c…` |
| `lib/failureEvent.ts` ◆ | `2f7571cf02de84c8…` |
| `lib/diagnosisMoment.ts` ◆ | `5c8c6e4c1772495e…` |
| `lib/counterfactual.ts` ◆ | `f78ba2a0da341b50…` |
| `lib/failureEventSchema.ts` ◆ | `32534f4c060bb473…` |
| `diagnose.ts` ◆ | `0166310b…` |
| `lib/rescreen.ts` | `ad7af055e23a28ad…` |
| `rescreen.ts` | `bfbd87ce…` |
| `diagnose.test.ts` ◆ | `3ee5bc88…` |
| `lib/counterfactual.test.ts` ◆ | `58b8dea9…` |
| `lib/diagnosisMoment.test.ts` ◆ | `a85515f0…` |
| `lib/failureEventSchema.test.ts` ◆ | `f4d9e6b2…` |
| `lib/rescreen.test.ts` | `4415fc58…` |
| `rescreen.test.ts` | `35087cf9…` |

- 載せ替えの前後の差分(スキーマの 2 本を除く 21 本): `scratchpad/dscreen2r-vs-dscreen2.diff`(`8f17be57…`)。違うのは 11 本、同じは 10 本

#### 13.6.2 測り直し(worktree の根から)

- **typecheck:scripts**: rc 0(`scratchpad/dscreen2r-typecheck.out`)
- **全件**: 51 ファイル・**712 件通過**(= `e9e7bf2` の 664 + D-SCREEN-2 の 48。`scratchpad/dscreen2r-suite.out`、`e826d0ea…`)
- **screen の無い記録のバイト一致(S-9)**: 今度は `e9e7bf2` の worktree(`wt-dscreen2r-base`)の出力と比べた
  - 道具: `scratchpad/dscreen2r-g9-compare.py`(`535a57e6…`)。出力: `dscreen2r-g9-compare.out`(`d037814c…`)
  - 比べた記録は 13.3 と同じ 9 か所・94 本(real-03 の kifu-01・04・07・09 は開いていない)
  - **Markdown 9/9 がバイト一致。--events・--events-rise・--events-maxdrop の 559/559 行が `schemaVersion` と `provenance.analysis` を除いて一致。新しい欄の漏れ 0**
- **変異**: `scratchpad/dscreen2r-mutate.py`(`def4e98b…`)。13.4 と同じ 27 本・同じ予測(`dscreen2-predictions.md` `24e563d3…`)。P-4 だけ置き換える値を基の版 "0.5" にした
  - 出力: `dscreen2r-mutate.out`(`cd02b31a…`)。道具と予測の sha を同じ逐次コマンドで記録した
  - 校正は exit 0・67 件。**適用 27 / 鳴った 27 / 沈黙 0。中心 12/12。予測 27/27**。当てた後、9 ファイルとも元の sha に戻った

### 13.7 監査 f2 の REVISE(R-1)と気づき N-1〜N-7 の直し(司令塔 e3 の決定。worktree `wt-dscreen2r`。**エンジンは使っていない**。書いたのは B)

- **R-1(必須)**: 校正の道具が、もう片方の同じ組が比べられなかった Event と組が無い Event を「相手にだけある = 取りこぼし」に入れていた(§5 の 1.・D-COST §2.2 と違う)
- **決定(e3)と実装**
  - 突き合わせは組 (fromReadyPly, toReadyPly) で行う
    - 同じ組に両方の Event があり、kinds(並べ替えて比べる)が同じなら一致
    - kinds だけ違えば「当たり方だけ違う」。取りこぼし・余計に入れず、別に数える
  - **取りこぼし**: 相手にだけあり、段 2 の同じ組は比べられた(compared か mateAfter。2 行とも measured)
  - **比べられない**: 段 2 の同じ組が notCompared(理由はその reason。mateBefore を含む)か、組が無い(noPair。記録が途中で終わった等)。件数と理由を並べ、率の分母に入れない
  - **取りこぼし率** = 取りこぼし ÷(取りこぼし + 一致 + 当たり方だけ違う)
  - **余計の側も同じに分けた(B の判断。e3 の決定の文より細かい)**
    - 段 2 にだけあり、相手の同じ組が比べられない・組が無い Event は、余計に入れず別に数える(D-COST §2.2 の「逆向きも同じ 4 つに分け」)
    - 余計率 = 余計 ÷(余計 + 一致 + 当たり方だけ違う)
  - 表の列: 一致・当たり方だけ違う・取りこぼし・取りこぼし率・比べられない(相手にだけある)・余計・余計率・比べられない(段 2 にだけある)。合計の行は、比べられないを理由ごとの件数で書く
- **予-1 の判定(e3)**: §7 の予-1 の外れ「取りこぼし 3 件以上」は、**この「取りこぼし」の件数で判定する**(比べられない・当たり方だけ違うは入れない)
- **N の扱い(e3)**
  - N-1〜N-5: 試験を足した
    - N-1: X-7 の excludedPairs
    - N-2: ready でない行の深い欄
    - N-3: deepUnavailable の notEvaluation
    - N-4: 軽い組の compared の行頭
    - N-5: evaluationSource の位置
    - f2 の変異で沈黙したもの(M-1・M-3・M-4・M-11)と同じ変異(N1〜N4)と、M-6 に当たる変異(N5a・N5b)が鳴ることを確かめた(13.7.2)
  - N-5 の並び: 載せ替えの後、Event の branch は evaluationSource が最後、moment の組の行は standingPair の直後(行の並びは `momentOrder` が決める)。X-8 の「moment の組の行では evaluationAfter の後ろ」は、載せ替えで間に standingPair が入った
  - N-6: rescreen の allPlies のときだけ、meta の screen の `rule` の直後に `allPlies: true` を書く
    - screen の形の確かめは「キーが無いか true」だけを通す
    - **出どころ(provenance)には写さない**(スキーマ v0.6 を変えない。13.5 の既知事項の候補)
  - N-7: 13.1 に X-12 を足した

#### 13.7.1 変えたファイル(sha256。worktree の `scripts/playtest/` から。ほかの 16 本は 13.6.1 のまま)

| ファイル | 直す前(13.6.1) | 直した後 | 差 |
|---|---|---|---|
| `lib/screenCalibration.ts` | `96a89222…` | `ca47f9dd16880a63dec7d012de2df2ba61e659c0928e1491376f3f8f5d42ae4b` | +115 −25 |
| `lib/screenCalibration.test.ts` | `52770fc3…` | `0208a2ab832912572931ca4a7a174c3e1971305504721c47fb3fcb9e5f5e6c94` | +70 −12 |
| `screen-calibrate.test.ts` | `e8a25e0a…` | `ba3975d171202dd97e542b51d6b74d978f2654bbc47a0ad9462555a4c10b02f6` | +1 −1 |
| `lib/screenDiagnosis.ts` | `106d8d5d…` | `e1b4c8a4646496bc863b2f6fd53df1d270280e6825643265299471afa5df7ed0` | +2 −0 |
| `lib/screenDiagnosis.test.ts` | `e2c0c1e1…` | `646c94e158e25b3cccf92d392ab77dde4f2fb3e215bf4e44bba0dbbc6af209fc` | +58 −0 |
| `lib/rescreen.ts` | `ad7af055…` | `a4466b55a675ddbe2b7f3f02c4cfbc0095e06fde41062bad7bb3143ddc2c626d` | +4 −1 |
| `lib/rescreen.test.ts` | `4415fc58…` | `b93824480d876e682a6147a67c22130872ef5a0ac1b84648bffe32600c4c4a6e` | +6 −3 |

- 7 本の差分: `scratchpad/dscreen2r-r1.diff`(`50d0c151…`)。当て方: `scratchpad/dscreen2r-r1-patch.py`(`98c37eb0…`。当てる前の 7 本の sha を道具の中で確かめた)と、N-5 の試験の期待の 1 行の手直し(下の予測の外れ)
- `scan-compare.ts` とその lib は変わっていない(`git status`)

#### 13.7.2 測り直し(worktree の根から)

- **予測は実装の前に書いた**: `scratchpad/dscreen2r-r1-predictions.md`(`69216909368cab52b6df3cd9c402d792a5d21f9456a3621cba970605391efb7c`、15:22:10Z)
- **追記の予測**(実装と試験の後・変異の前): `scratchpad/dscreen2r-r1-predictions-add.md`(`aca8c8bf…`)。道具・予測・追記の sha は、変異と同じ逐次コマンドの先頭で記録した

| # | 予測 | 実測 | 判定 |
|---|---|---|---|
| R-Q1 | typecheck:scripts は rc 0 | rc 0(`dscreen2r-r1-typecheck2.out`) | 的中 |
| R-Q2 | 全件 51 ファイル・720 件(幅 718〜724) | **51 ファイル・720 件通過**(`dscreen2r-r1-suite.out` `9c5bf271…`) | 的中 |
| R-Q3 | 変える本は 7 本(幅 6〜9)+ 計画書 | 7 本 + 計画書 | 的中 |
| R-Q4 | screen の無い記録のバイト一致は変わらない | Markdown 9/9・行 559/559・新しい欄の漏れ 0(`e9e7bf2` の出力と。`dscreen2r-r1-g9-compare.out` `bc4fa16b…`) | 的中 |
| R-Q5 | 変異で使う 5 試験ファイルの校正は 75 件 | 75 件 | 的中 |
| R-Q6 | 足した変異は全部鳴り、鳴る試験は表どおり。既存 27 本は P-5′ のほか同じ集合 | 足した 15 本と P-5′ は 16/16 表どおり。**既存の Z-4・Z-11 は集合が増えた** | **外れ 2**(追記の予測では 2/2 当たり) |

- **N-5 の試験の最初の版の外れ**: 上がりを deep 1 件と書いたが、植えた記録には軽い上がりがもう 1 件あった。試験の期待の誤りで、実装は変えていない(["deep", "light"] に直した)

- **変異**: `scratchpad/dscreen2r-r1-mutate.py`(`c3bc2969…`。13.6.2 の道具から `dscreen2r-r1-mutate-gen.py` で作った)→ `dscreen2r-r1-mutate.out`(`336250f7…`)
  - 校正は exit 0・75 件。当てた後、9 ファイルとも元の sha に戻った
  - **適用 42 / 鳴った 42 / 沈黙 0。中心 12/12。記録した予測の的中 40/42、追記の予測を入れて 42/42**

| # | 変異 | 鳴った試験 |
|---|---|---|
| Z-4(既存) | 深く測れなかった行を含む組を数えない | S-7・**S-7b**(追記の予測) |
| Z-11(既存) | 最大の下がりで出どころを混ぜて選ぶ | S-13・S-20・**N-1**(追記の予測) |
| P-5′(P-5 を置き換え) | Event の突き合わせで kinds を並べ替えない | compareEventSets の試験 |
| R1-a | 比べられない(notCompared)を取りこぼしに入れる | compareEventSets の試験・R-1 |
| R1-b | 組が無い(noPair)を取りこぼしに入れる | compareEventSets の試験・R-1 |
| R1-c | 当たり方だけ違うを分けず、取りこぼしと余計に入れる | compareEventSets の試験 |
| R1-d | 取りこぼし率の分母から当たり方だけ違うを外す | compareEventSets の試験 |
| R1-e | mateAfter の組を比べられないにする | compareEventSets の試験 |
| R1-f | 逆向きを分けない(相手の組が比べられない Event も余計) | compareEventSets の試験 |
| R1-g | 比べられないの理由を表に書かない | R-1 |
| N1(f2 の M-1) | 混ざる局の excludedPairs を組ごとの出どころの組で数える | N-1 |
| N2(f2 の M-3) | ready でない行の深い欄の不変条件を外す | S-8(ready でない行) |
| N3(f2 の M-4) | deepUnavailable から notEvaluation を外す | S-7b |
| N4(f2 の M-11) | 軽い組の compared の行頭も読み直しの探索 | N-4 |
| N5a(f2 の M-6 に当たる) | Event の branch で evaluationSource を evaluationAfter の前に置く | N-5 |
| N5b | moment の組の行で evaluationSource を前に置く(`momentOrder`) | N-5 |
| N6a | rescreen が allPlies を meta に書かない | allPlies の試験 |
| N6b | screen の形の確かめが allPlies の値を見ない | S-8(allPlies が true でない) |

- ほかの既存 25 本は 13.6.2 と同じ試験で鳴った
