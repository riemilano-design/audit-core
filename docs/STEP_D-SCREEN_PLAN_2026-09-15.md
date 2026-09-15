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
