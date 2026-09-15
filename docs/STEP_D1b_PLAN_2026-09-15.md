# STEP D1b 計画: 相手の側の上がりと、各局の最大の下がりを、事実だけで出す(2026-09-15)

**状態**: 計画(**事前読み f2 の REVISE(必須 R-1〜R-4・推奨 S-1〜S-8)と司令塔の追加の決定 3 点を取り込み、版 `787157c3` への f2 の再読みは GO(条件 2 つ・推奨 1 つ。取り込んだ)** ― 取り込み先は 8.)。書いたのは A(sgogi-coach-64、司令塔の依頼)。**事前読みは f2**。実装は B が D2 の直後(同じ lib)。
**司令塔の決定(2026-09-15。下書き `8152fb50` に対して、すべて A の推奨どおり)**:
- **E-3**: 窓は「本人の手 → 相手の手」のまま符号を変えて取り、「相手の手で上がった」とは書かない。人間向けの文も同じ(司令塔のレポートの道具は「相手の手を含む 2 手なので分けていない」と書いている)
- **E-4**: `opponentBestmove` は `{ state: "notInRecord" }` 固定。`afterPass.bestmove` を写すのは変異 Y-3
- **E-7・Q-4**: D2 の `counterfactual` は同じ根で当てる
- **Q-1**: 別の契約 `diagnosis-moment.v0.1`(`eventClass` で `oneOf`、共通部は Failure Event のスキーマから道具で写す)。Failure Event の定義(破滅の分岐)を広げない・J-5 を踏まない
- **Q-2**: 閾値は `DRAFT_RULE_1.dropCp` の符号を変えて使う。**Q-3**: Markdown は出さない(司令塔のレポートの道具が JSONL を読む)

**司令塔の追加の決定(2026-09-15。版 `2b5142a2` への f2 の事前読みと、B が挙げたつなぎ目を受けて)**:
- **G-9・予-4 の基準は D2 のコミット後の HEAD**(D2 は Markdown に節を足し、v0.4 で Event に `counterfactual` が入る)。D1b の実装は D2(v0.4)のコミットの後
- **`rise`・`maxDrop` の行にも `counterfactual` を入れる**(Q-4 の帰結)。部分スキーマは Failure Event v0.4 から共通部と同じ道具で写す(二重に定義しない)
- **各行に `contract: "diagnosis-moment"`(const)と `schemaVersion: "0.1"` を必須で置く**(Failure Event の `"0.1"` と取り違えないため)。Failure Event の行は変えない
- B は real-01 の評価値を見ているので、D1b の予測は書き足さない(予測は A のもの)
- **Q-5(版 `787157c3` への f2 の再読みを受けて)**: A の案どおり、`rise` にも `failureEventBranchPly` を置く(G-10・Y-11 はそのまま)

**基点**: HEAD `0fa9e2c`(読んだ時点)。**実装の時点では V0.3-META(Failure Event v0.3)と D2(v0.4)が先に入る**(E-10)。**エンジンは使っていない。**記録の欄の名前と有無、Failure Event の `kinds` だけを数え、評価値は見ていない(5. の予測を盲検に保つため)。
**背景(人間の問い、司令塔を通して)**: 落差なく負けた局と、勝った局に何を書くか。**答えは「理由は書かない。事実だけ」**。人間の委任「君に任せる」で司令塔が決めた 2 つの出力を、診断に足す。

---

## 0. 実物から分かった前提

| # | 事実 | 場所 |
|---|---|---|
| E-1 | **評価があるのは本人番の局面だけ。**ready 行は ply 0・2・4…(本人 = 先手の手番)にだけあり、行 k の `senteMove`・`goteMove` はその行に至る 2 手(ply k−1 の本人の手、ply k の相手の手) | real-01 `kifu-02` の行の欄(f2 も確かめた)。`scripts/playtest/lib/recorder.ts:252-259` |
| E-2 | **2 手の組は「本人の手 → 相手の手」の窓だけ。**`pairEvaluations` は連続する ready 行を組にし、`diffCp = to.scoreCp − from.scoreCp`(本人視点)。急落は `diffCp ≤ dropCp(−400)` か `mateAfter < 0` | `scripts/playtest/lib/failureEvent.ts:135-160`・`:407-409`・`:418`(`branchPly = from.ply + 1`) |
| E-3 | **「相手の手 → 本人の応手」の窓は記録から作れない。**その窓の始まり(本人の手の後の相手番の局面)に評価が無い。`afterPass` は**本人が指す前の盤**で手番を相手にした探索で、本人の手の後の局面ではない | `apps/server/src/analysis/engineReference.ts:155`(baseline は `position(sfen)`)・`:71`・`:161-164`(afterPass は `passSfen(sfen)`) |
| E-4 | **したがって `afterPass.bestmove` は「相手番の局面での第一候補」ではない。**欄は real-01 の ready 行 222 のうち 219 行で文字列(3 行は `engineReference: null`) | 欄の有無だけを数えた |
| E-5 | **今のスキーマの形に上がりは入らない。**`branch.kinds` は `minItems: 1` で列挙 `cpDrop`・`mateDrop`・`matedIfPass`、`candidateModes[].matchedBy` も同じ列挙 | `scripts/playtest/schemas/failure-event.v0.2.schema.json` |
| E-6 | **Failure Event は「破滅の分岐」**(「この着手を境に、何が壊れたか」)。上がり・最大の下がりはこの定義に当たらない | `docs/DIAGNOSIS_CONCEPT_2026-09-14.md` §5.1 |
| E-7 | D2 の `counterfactual` の根は直前の ready 行(本人番)で、読み筋は `focus_baseline`。**上がり・最大の下がりも同じ組(同じ根)なので、関数はそのまま当たる**。ただし読み筋の 2 手目は「エンジンの 1 手目への相手の応手」で、**本人の実戦の手が読み筋の 1 手目と同じ(`pvFirstMoveIsPlayedMove`)ときだけ、相手の手と同じ局面の手を比べる形になる**(記録の形から。実測していない) | `docs/STEP_D2_PLAN_2026-09-15.md` §2.1・§2.2 |
| E-8 | **上がりの組も Failure Event になりうる。**`diagnoseRecords` は、直後の行の `afterPassMate > 0` なら、差に関係なく `matedIfPass` の Event を作る | `scripts/playtest/lib/failureEvent.ts:410-414`(f2 の事前読み R-1) |
| E-9 | **試験の道具 `engineRef` は `afterPass.bestmove` を `null` に固定している**(選べる引数が無い) | `scripts/playtest/lib/failureEventFixtures.ts:34`(f2 の R-2) |
| E-10 | **Failure Event の行は D1b より前に 2 回変わる**: V0.3-META(v0.3。`provenance.record.meta` に 7 欄)と D2(v0.4。`counterfactual`)。D1b は D2 のコミットの後に実装する | V0.3-META 計画 `0fa9e2c`・D2 計画 `a84689b` |
| E-11 | **real-01 の Failure Event 5 件はすべて `cpDrop`**(`kifu-02` 31・`kifu-05` 17 と 77・`kifu-06` 75・`kifu-10` 33。`03`・`08` は 0 件) | `0fa9e2c` の `diagnose.ts --events` の出力の `kinds` だけを見た(A、V0.3-META 監査の基準の出力) |

## 1. 目的と範囲

**目的**: 急落が無い局・勝った局にも、**事実だけの 2 つの出力**を足す。理由・評価語は書かない。
1. **上がり(`eventClass: "rise"`)**: E-2 と同じ窓(本人の手 → 相手の手)で、本人視点の評価が **`−dropCp`(+400)以上上がった**組、または `mateAfter > 0`(直前が cp、直後に本人が詰ませる読み)の組。**窓は 2 手を分けない**(E-3)
2. **最大の下がり(`eventClass: "maxDrop"`)**: 局ごとに、`compared` の組のうち `diffCp` が最も小さい 1 件。**閾値未満でも出す**

**範囲**
- `failureEvent.ts` の隣に純粋関数(`pairEvaluations` の結果を読むだけ。**`diagnoseRecords` の Failure Event の値は変えない**)
- `diagnose.ts` に `--events-rise <out>`・`--events-maxdrop <out>`。**`--events`・`--events-rise`・`--events-maxdrop` は、3 つの行をすべて作ってから書く**(V0.3-META の K-3 の例外で一部のファイルだけが書かれる形を避ける。S-8)
- 新しいスキーマ `scripts/playtest/schemas/diagnosis-moment.v0.1.schema.json`
- **既存の `--events` の行と Markdown は変えない**(Q-3)。`apps/`・`data/` に触らない。エンジンを回さない

## 2. 行の形(契約 `diagnosis-moment` v0.1)

**共通の欄**(すべての行): `contract: "diagnosis-moment"`(const)・`schemaVersion: "0.1"`(const)・`eventClass`・`kifuId`・`provenance`(`buildProvenance` をそのまま。`record.meta` は v0.3 の形)。

**組の行**(`rise` と、`maxDrop` の組の行)がさらに持つ欄: `branchPly`(本人の手の ply)・`fromReadyPly`・`toReadyPly`・`trigger`(`triggerOf(from)` をそのまま)・`consequences`(`actualContinuation` をそのまま)・`counterfactual`(D2 の関数をそのまま。下)。**`kinds`・`candidateModes` は持たない**(E-5)。

| 欄 | `rise` | `maxDrop`(組の行) |
|---|---|---|
| `change` | `{ kind: "cp", diffCp }` か `{ kind: "mateAfter", mateAfter }`(> 0) | `{ kind: "cp", diffCp }`(`compared` の組だけ) |
| `moves` | `{ userMove, opponentMove }`(窓の 2 手。記録の手数 `branchPly`・`branchPly + 1`) | 同じ |
| `userBestmoveAtBefore` | 直前の行の `baseline.bestmove`(Failure Event の `bestmoveAtBefore` と同じ値) | 同じ |
| `opponentBestmove` | **`{ state: "notInRecord" }` 固定**(E-3・E-4。`afterPass.bestmove` を写さない) | 同じ |
| `evaluationAfter` | 直後の行の評価(Failure Event の `branch.evaluationAfter` と同じ形) | 同じ |
| `failureEventBranchPly` | **同じ組の Failure Event があればその `branchPly`、無ければ `null`**(E-8。R-1) | 同じ |
| `excludedPairs` | ― | `{ mateDrop, mateRise, notCompared }`(比べなかった組の数。`mateAfter < 0` と `> 0` を分ける。S-5) |

**`counterfactual`**: D2 の関数に、根 = 直前の行、実戦 = `moves[branchPly − 1]` から、読み筋 = 直前の行の `focus_baseline` を渡す(Failure Event と同じ)。D2 の `playedMove` には `moves.userMove`、`bestmoveAtBefore` には `userBestmoveAtBefore` を渡す。**`rise` の行では、`pvFirstMoveIsPlayedMove` が false のとき、読み筋の 2 手目は実戦の相手の手と同じ局面の手ではない**、とスキーマの説明に書く(E-7)。

**状態の行**(`maxDrop` で組の行が出ない局。局を黙って落とさない ― 規則 11.6。S-6): 共通の欄 + `state` + `excludedPairs`。
- `{ state: "noComparedPair" }`: `compared` の組が 1 つも無い
- `{ state: "noDrop", minDiffCp }`: 最小の `diffCp` が **0 以上**(0 は `noDrop`、−1 は組の行。S-4)

同じ最小値が 2 組あれば**早い組**。

**スキーマの `oneOf` の変種は 5 つ**: `rise` の `cp` / `rise` の `mateAfter` / `maxDrop` の組 / `maxDrop` の `noDrop` / `maxDrop` の `noComparedPair`。**共通部(`trigger`・`consequences`・`counterfactual`・`provenance`)は、実装の時点の Failure Event v0.4 のスキーマから道具で写す**(`record.meta` は v0.3 の形。R-4)。

## 3. 固定例(`failureEventFixtures.ts` の `plantedRecords`・`engineRef` で評価を植える。期待は手で書き、**G ごとに `rise` と `maxDrop` の両方の出力を書く**)

| # | 植える評価(本人視点の scoreCp の並び) | `rise` | `maxDrop` |
|---|---|---|---|
| G-1 上がりの境目 | 0 → +399 → +799 | 2→4(`branchPly` 3、+400)の 1 行。0→2(+399)は無し | `noDrop`・`minDiffCp` 399 |
| G-2 詰みの上がり | +200 → mate +3 | 0→2 の `mateAfter` の 1 行 | `noComparedPair`・`excludedPairs` `{ mateDrop 0, mateRise 1, notCompared 0 }` |
| G-2′ 詰みの下がり | +200 → mate −3 | 無し(`mateDrop` の Failure Event がある) | `noComparedPair`・`excludedPairs.mateDrop` 1 |
| G-3 最大の下がり(閾値未満) | +100 → +50 → −100 → −30 | 無し(+70) | 2→4(−150)、`failureEventBranchPly` null、Failure Event 0 件 |
| G-4 急落と重なる | +300 → −300 → −250 | 無し(+50) | 0→2(−600)、`failureEventBranchPly` 1。Failure Event の値は D1 と同じ |
| G-5 同じ最小値 | 0 → −100 → −200 → −300 | 無し | 3 組とも −100 → 早い組(0→2) |
| G-6 下がりが無い | 0 → +10 → +20 | 無し | `noDrop`・`minDiffCp` 10 |
| G-7 比べられる組が無い | 1 行目 `engineReference: null`・2 行目だけ測った | 無し | `noComparedPair`・`excludedPairs.notCompared` 1 |
| G-8 afterPass の値が無い | G-1 の 2 行目で `afterPass.scoreCp` null | G-1 と同じ(判定は baseline だけ) | G-1 と同じ |
| G-10 上がりと `matedIfPass` が重なる | 0 → +500、2 行目に `afterPassMate` +3 | 0→2 の 1 行、`failureEventBranchPly` 1(同じ組に `matedIfPass` の Event) | `noDrop`・`minDiffCp` 500 |
| G-11 afterPass に最善手がある | G-1 の 2 行目の `afterPass.bestmove` に **null でない手**を植える(`engineRef` に引数を足すか手で書き換える。E-9) | G-1 と同じで、`opponentBestmove` は `{ state: "notInRecord" }` のまま(R-2) | G-1 と同じ |
| G-12 読み筋の 1 手目 | G-1 と G-4 の直前の行に `focus_baseline` を植える。(i) 1 手目 = 本人の手 (ii) 違う手 | `counterfactual.pvFirstMoveIsPlayedMove` (i) true (ii) false | G-4 の組の行の `counterfactual` は、同じ組の Failure Event の `counterfactual` と等しい(R-3) |
| G-13 `noDrop` の境目 | (a) 0 → 0 (b) 0 → −1 | 無し | (a) `noDrop`・`minDiffCp` 0 (b) 組の行・−1(S-4) |
| G-14 詰みの下がりのある局 | +100 → +80 → mate −3 | 無し | 0→2(−20)、`failureEventBranchPly` null、`excludedPairs.mateDrop` 1(「最大」が詰みの組の外にあることを数で残す。S-5) |
| G-15 行の全体 | `GAME01_MOVES` に評価を植えた記録 | `rise` の 1 行を `toEqual` で書く(`contract`・`schemaVersion`・`moves` の本人と相手・`userBestmoveAtBefore`・`evaluationAfter`・`failureEventBranchPly`・`counterfactual`) | 組の行 1 つを `toEqual` で書く(`excludedPairs` を含む)。どちらも v0.1 のスキーマを通る(S-3) |
| G-16 3 つのファイル | 子プロセス: 2 本目の記録の meta が V0.3-META の K-3 に当たる | ― | `--events`・`--events-rise`・`--events-maxdrop` のどれも書かれず、前もって置いたファイルのバイト列が変わらない(S-8) |
| G-9 既存の出力 | G-1〜G-16 と `GAME01_MOVES`・コミット済みの記録 | ― | **`--events` の行と Markdown が、D2 のコミット後の HEAD の出力とバイト一致**(`provenance.analysis` を除く) |

**不変条件の試験**(S-1): **「局に `cpDrop` の Failure Event がある ⇒ `maxDrop` の組の行の `failureEventBranchPly` が null でなく、指す Event の `kinds` に `cpDrop` がある」**(`diffCp ≤ −400` の組は必ず `cpDrop` の Event なので、最小の組は必ずその組になる)。**逆向き(pointer が null でない ⇒ `cpDrop` の Event がある)は書かない**: `failureEventBranchPly` は `matedIfPass` だけの Event にも付く(E-8)ので、`cpDrop` の無い局でも最小の組がその Event と重なれば null でなくなる(f2 の再読みの条件 1)。言い換えると「pointer が `cpDrop` の Event を指す ⇔ 局に `cpDrop` の Event がある」。real-01 で `cpDrop` の Event がある局は 4 局(E-11)。固定例とコミット済みの記録で見る。

## 4. 変異(**中心を壊すもの ― 規則 11.8**。予測は実装の後、当てる前に道具と同じ逐次コマンドで書く)

| # | 壊し方 | 中心 | 見張る |
|---|---|---|---|
| Y-1 | 上がりの符号を変えない(`diffCp ≤ dropCp` を使う) | 中心 | G-1・G-4 |
| Y-2 | 境目を `>` にする | 中心 | G-1 |
| Y-3 | `opponentBestmove` に `afterPass.bestmove` を写す(E-4 の罠) | 中心 | **G-11**(R-2) |
| Y-4 | 最大の下がりに `diffCp` の最大(上がり)を選ぶ | 中心 | G-3 |
| Y-5 | 最大の下がりを急落だけから選ぶ(閾値未満を出さない) | 中心 | G-3 |
| Y-6 | `maxDrop` の `failureEventBranchPly` を常に null / 別の組を指す | 中心 | G-4・不変条件 |
| Y-7 | `noDrop`・`noComparedPair` の行を書かない | 中心 | G-6・G-7 |
| Y-8 | 上がりの行を既存の `--events` にも書く | 中心 | G-9 |
| Y-9 | 同じ最小値で遅い組を選ぶ | 周辺 | G-5 |
| Y-10 | `mateAfter > 0` を上がりにしない | 周辺 | G-2 |
| Y-11 | `rise` の `failureEventBranchPly` を常に null にする | 中心 | G-10(R-1) |
| Y-12 | `moves.userMove` と `opponentMove` を入れ替える | 中心 | G-15 |
| Y-13 | `counterfactual` に相手の手を `playedMove` として渡す | 中心 | G-12(R-3) |
| Y-14 | `maxDrop` を `mateAfter`・`notCompared` の組からも選ぶ | 中心 | G-7・G-14 |
| Y-15 | `excludedPairs` の `mateDrop` と `mateRise` を 1 つに畳む / 数を違える | 周辺 | G-2・G-14 |
| Y-16 | `noDrop` の境目を `> 0` にする | 周辺 | G-13 |
| Y-17 | `contract` を書かない / `schemaVersion` を Failure Event の版にする | 中心 | G-15(スキーマ) |
| Y-18 | 3 つのファイルを行を作りながら 1 つずつ書く | 中心 | G-16(S-8) |

## 5. 予測(**測る前に書く**)

**盲検の扱い(S-2)**: A は real-01 の評価値を見ていない。**REAL-01 計画 §6(局ごとの最大・最小、+300 以上の行の数、急落の前後の値)と、司令塔の 20 局版のレポートは開いていない**(この会話の記録で、そのファイルを開いた道具の呼び出しは 0 件。前の会話の記録は確かめていない)。**V0.3-META の実装の監査でも、`diagnose.ts --events` の行(評価値を含む)は表示していない**: 基準と監査の出力は道具の中で行ごとに比べて行数と一致の数だけを出し、real-01 の 5 行は `kifuId`・`branchPly`・`kinds` だけを表示した(同じ会話の記録で確かめた。f2 の再読みの推奨)。知っているのは Failure Event の局ごとの件数と `kinds`(E-11)だけ。**B は評価値を見ているので予測を足さない**(司令塔の決定)。

| # | 予測 | 外れたと言える条件 |
|---|---|---|
| 予-1 | real-01 の 6 局で `rise` は **3〜12 件** | 2 件以下か 13 件以上 |
| 予-2 | `maxDrop` は 6 局とも組の行(`noDrop`・`noComparedPair` は 0) | どれかが状態の行 |
| 予-4 | 既存の `--events`(real-01 5 行・74 本 335 行)と Markdown は、**D2 のコミット後の HEAD の出力**とバイト一致(`provenance.analysis` を除く) | 1 行でも違う |

**予-3 は予測から外した**(S-1): `failureEventBranchPly` が `cpDrop` の Event を指す局の数は事実から決まる(3. の不変条件。real-01 はちょうど 4 局)。

## 6. 決定が要る点

**決定(司令塔、2026-09-15): Q-1〜Q-4 はすべて推奨どおり**(冒頭の「状態」)。**Q-5 も推奨どおり**(A が f2 の R-1 を受けて置いた案。f2 の再読みで賛成、司令塔が決定。冒頭の「状態」)。下の表は決定の前に書いた選択肢のまま残す。

| # | 点 | 推奨 | ほかの案 |
|---|---|---|---|
| **Q-1** | 版・契約 | **(a) 別の契約にする**(`schemas/diagnosis-moment.v0.1.schema.json`。`eventClass` を判別の欄にした `oneOf`。`trigger`・`consequences`・`provenance` の部分は Failure Event のスキーマから道具で写す)。理由: E-5(`kinds` の列挙にも `minItems` にも触れない)・E-6(Failure Event の定義を広げない)・D2(v0.4)と V0.3-META の監査の面を増やさない | (b) Failure Event v0.5 に `eventClass` を足す: 上がりの行の `kinds` に入れるものが無く、`minItems` を外すと既存の欄の約束を緩める(MAJOR と読める)/ (c) D2 と同じ v0.4 に同梱: (b) と同じ問題に加え、D2 の監査の面を倍にする(D2 計画 Q-1 で meta の欄を切り離したのと同じ理由) |
| **Q-2** | 上がりの閾値 | **`DRAFT_RULE_1.dropCp` の符号を変えて使う**(新しい閾値の定数を置かない。判断的知識の仮置きのまま) | 別の `riseCp` を置く(値が同じなら 1 か所で足りる。変えるときは人間の承認) |
| **Q-3** | Markdown | **この STEP では出さない**(JSON だけ。人に見せる形は D4) | 局ごとの表に `rise` の件数と最大の下がりの列を足す |
| **Q-4** | D2 の `counterfactual` | **D2 の関数を `rise`・`maxDrop` にも同じ根で当てる**(E-7)。`rise` では `pvFirstMoveIsPlayedMove` が false のとき、読み筋の 2 手目は実戦の相手の手と同じ局面の手ではない、と欄の説明に書く | `rise` には付けない(状態 `notApplicable`) |
| **Q-5** | 上がりと Failure Event の重なり(E-8) | **`rise` にも `failureEventBranchPly` を置く**(`maxDrop` と同じ形。重なりを行だけで読める) | 置かない: 読む側が `--events` と突き合わせる。「上がった組が同時に破滅の分岐でもある」ことが行から見えない |

## 7. やらないこと

- 理由の推定(「相手が間違えた」「本人がうまく指した」「粘った」など)と、評価語(良い・悪い・好手・悪手・逆転)
- 「相手の手 → 本人の応手」の窓(E-3。記録に評価が無い。作るにはエンジンで相手番の局面を測り直す)
- `afterPass.bestmove` を相手の第一候補として出すこと(E-4)
- 既存の `--events` の行・Failure Event の値・列挙を変えること。Failure Event の行に `contract` の欄を足すこと
- 死因のタグ(`candidateModes`)を上がり・最大の下がりに付けること
- 新しい閾値(Q-2)。エンジンを回すこと

## 8. 事前読み f2(版 `2b5142a2` に対する REVISE・必須 4・推奨 8)と司令塔の追加の決定の取り込み

| 指摘・決定 | 取り込み先 |
|---|---|
| **R-1(必須)** 上がりと Failure Event(`matedIfPass`)の重なり | E-8・2. の `rise` の `failureEventBranchPly`・G-10・Y-11・Q-5 |
| **R-2(必須)** Y-3 が沈黙しうる(`engineRef` の `afterPass.bestmove` が null 固定) | E-9・G-11・Y-3 の見張りを G-11 に |
| **R-3(必須)** Q-4 が 2.〜4. に無い | 2. の `counterfactual`・G-12・Y-13。**司令塔の決定: 入れる、部分スキーマは FE v0.4 から道具で写す** |
| **R-4(必須)** 基点と契約の版 | E-10・G-9 と予-4 の基準(**司令塔の決定: D2 のコミット後の HEAD**)・2. の共通部を写す元(FE v0.4、`record.meta` は v0.3)・**`contract`・`schemaVersion` を必須(司令塔の決定)**・Y-17 |
| S-1 予-3 は事実から決まる | E-11・3. の不変条件・予-3 を外した |
| S-2 盲検 | 5. の冒頭(REAL-01 計画 §6 とレポートは開いていない) |
| S-3 行ごとの期待・両方の出力・変異 | 3. の表を 2 列に・G-15・Y-12・Y-14・Y-15 |
| S-4 `noDrop` の境目 | 2. の状態の行・G-13・Y-16 |
| S-5 `mateAfter` の組を外すこと | 2. の `excludedPairs` を `mateDrop`・`mateRise`・`notCompared` に・G-14 |
| S-6 状態の行の欄と `oneOf` の変種 | 2. の状態の行(`provenance`・`excludedPairs`)と 5 つの変種 |
| S-7 E-3 の場所 | E-3・E-4 に `apps/server/src/analysis/engineReference.ts` と行番号 |
| S-8 3 つのファイルは全部作ってから書く | 1. の範囲・G-16・Y-18 |
| B は予測を足さない(司令塔) | 5. の冒頭 |
| **再読み(版 `787157c3`)の条件 1** 不変条件の「⇐」は `matedIfPass` だけの Event で破れうる | 3. の不変条件を「⇒」と「指す Event が `cpDrop`」に・5. の予-3 の注 |
| **再読みの条件 2** Q-5 の決定を状態の行に | 冒頭の司令塔の追加の決定・6. の決定の注 |
| 再読みの推奨: 盲検の注に V0.3-META の監査で events を表示したか | 5. の冒頭 |
