# STEP D-SCREEN 計画: 全行を 40 万ノードで測り、急落の候補の前後だけ 400 万ノードで測り直す(2026-09-15)

**状態**: 計画(**司令塔の決定(版 `82344779`): Q-1〜Q-8 はすべて推奨どおり**。**事前読み 1e の REVISE(版 `7388c9b6`、必須 R-1〜R-4・推奨 S-1〜S-7)を司令塔の決定で取り込み、版 `321a274a` への 1e の再読みは GO**(K-1 を司令塔の決定 (a) で直し、K-2〜K-5 は 9. に既知事項の候補として置いた ― 取り込み先は 10.)。書いたのは A(sgogi-coach-64、司令塔の依頼。人間の指示「作業を効率よく早く」)。**エンジンは使っていない。**基点 HEAD `58b540a`。
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

**形(Q-1)**: `replay.ts` は変えない。**段 1** = `replay.ts --nodes 400000 --reference-nodes 400000`(全行)。**段 2** = 新しい道具 `scripts/playtest/rescreen.ts <段1.jsonl> --out <段2.jsonl> --deep-nodes 4000000`。**中身は lib の純粋な組み立て `rescreenRecords(lines, screenRule, measure)`**(`measure(sfen) → EngineReference | null` を引数で受ける。試験はエンジン無しで偽の `measure` を渡す)。CLI は記録を読み、1 プロセス・Threads 1 のエンジンで `measureEngineReference` を `measure` として渡し、書くだけ。**段 1 のファイルは変えない。**

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
- D2 の読み筋は段 1(40 万ノード)のまま。`counterfactual` の出どころのノード数を行に書く(E-7・Q-7)
- **`check.ts`・不変条件は段 2 の記録でも `engineReference`(軽い値)を読む。変えない**(S-1。I-7・I-11 の判定は 4M 一律と変わりうる ― 限界)

## 4. 所要の見積もり(式だけ)

T₂段 = t_boot + R × t_row(400k) + D × t_ref(4M)。R = ready 行、D = 読み直した行(重なりを除く)。**T₂段 / T_4M一律 は、校正のときに 4M 一律・段 1・段 2 を同じ 1 局で、エンジン 1 本・load ≤ 2.0 で測って置く**(S-3。d3-nnue・D-COST の所要はどれも「参考」で分母に使えない)。

## 5. 校正(**4M 一律の記録と、急落の集合が一致するか**)

- **0. rescreen の床(R-1)**: `records/d3-nnue` の 20 局に、**`deepPlies` = 全 ready 行・`deepNodes` = 4M** で rescreen を当てる。(i) `engineReferenceDeep` と `engineReference` が行ごとにバイト一致する数 (ii) 全行を深い値で数えた Event の集合と、今の Event の集合の食い違い (iii) **同じ入力で rescreen を 2 回**回したバイト一致。**床(ii)が 0 でなければ、1. の食い違いは「並び(状態)で出るもの」と「ノード数で出るもの」に分けて数える**(同じ組が床でも食い違っていれば並びの側)
- **1. 本番の形**: 同じ 20 局を段 1(400k)→ 段 2 で回し、Failure Event の **(kifuId, branchPly, kinds)** を 4M 一律と比べる。**一致・取りこぼし・余計**、比べられなかった・測っていないは数えて並べる(D-COST §2.2)。死因①の一致も並べる。`counterfactual` は集合に入れず、**状態の一致率**を別に出す
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
| 予-4 | `counterfactual` の状態の一致率は **80% 以上** | 80% 未満 |

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
