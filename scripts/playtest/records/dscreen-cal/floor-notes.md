# 床の読み(C = 5b、2026-09-16 05:xx。エンジン無しの分析。次の報告に入れる)

道具: `analyze.mts`(sha1 efdcc1f2)。90ea1f1 の lib(`diagnoseRecords`・`screenOfRecord`・`choosePairSources`・`readEvaluations`)をそのまま呼ぶ。
**校正**: 4M → 床 1 回目の件数は screen-calibrate の合計と一致(一致 93・取りこぼし 8・余計 7・当たり方だけ違う 8・比べられない 段 2 側 1)。床 1 回目 → 2 回目は食い違い 0(一致 109)。
出力: `analysis-floor.json`・`analysis-repeat.json`

## 確認 1: replay.ts と rescreen.ts のエンジンの使い方

- **共通**: `UsiEngine` を 1 本起こし、`usiHandshake` → `isready` → `setThreads(1)` の後、同じプロセスで最後まで回す
  - `usinewgame` を送る所・ハッシュを消す所・`USI_Hash` を設定する所は、`apps/server/src/engine`・`scripts/playtest/lib` に 0(grep)
  - 置換表・履歴は、どちらの道具でもプロセスの中で持ち越される。`measureEngineReference` は `position <sfen>` → `go nodes N`(MultiPV 1)を現局面とパスした局面で 1 回ずつ(`engineReference.ts:155-164`)
- **replay.ts**: ready 行ごとに `buildReadyRecord` が次を同じプロセスで順に行う
  - まず `safeComputeReachablePlan` で候補手の探索(`withFixedSearch(nodes)`)と③の探索(focusEngine、`withFixedSearch(nodes)`)を**同じ局面**で走らせる
  - その後で `measureEngineReference(sfen, referenceEngine, referenceNodes)`(`recorder.ts:233-255`)
  - 相手の手は固定の偽エンジンで、探索しない
- **rescreen.ts**: 読み直す ready 行を ply の昇順に、`measureEngineReference` だけを続けて呼ぶ(`lib/rescreen.ts:199-203`。間にほかの探索を挟まない)
- **読み**: 違いは探索の履歴。4M 一律の参考評価は、同じ局面を候補手・③で 4M 読んだ直後の置換表から始まる。床の値は、1 つ前の ready 行の 2 回の探索の置換表から始まる。P-33(同じプロセスで履歴が違えば値が違う)で説明できる
  - 各道具の中では並びが決まっているので再現する。(iii) の 836/836 と P-48 に合う。「エンジンの揺れ」ではなく、道具ごとに系統的に決まる差
  - **ただし「replay の値のほうが深い・正しい」とは測っていない**(同じ局面を先に読んだ置換表を持つ、という事実だけ)

## 確認 2: 全行を読み直した床の「軽い組 81・深く測れなかった行を含む組 4」

床 1 回目の ready 409 行の状態(軽い = `engineReference`、深い = `engineReferenceDeep` を同じ `evaluationOf` で読む):

| 軽い \ 深い | 件数 |
|---|---|
| measured / measured | 343 |
| notMeasuredInCheck / notMeasuredInCheck(王手中で測らない) | 42 |
| notMeasuredGameEnd / notMeasuredGameEnd(終局で測らない) | 20 |
| notEvaluation / measured | 2 |
| measured / notEvaluation | 2 |

- 組は ready 行の連続 389 = 深い 308 + 軽い 81
- `choosePairSources` は **2 行とも深い値が measured のときだけ深い組**。軽い 81 の内訳:

| 軽い組になった理由(直前 / 直後の深い状態) | 件数 |
|---|---|
| measured / notMeasuredInCheck | 23 |
| notMeasuredInCheck / notMeasuredInCheck | 19 |
| notMeasuredInCheck / measured | 15 |
| measured / notMeasuredGameEnd | 12 |
| notMeasuredInCheck / notMeasuredGameEnd | 8 |
| measured / notEvaluation(deepUnavailable) | 2 |
| notEvaluation / measured(deepUnavailable) | 2 |

- 王手中・終局の 62 行(記録の `engineReference` も null)に触れる組 77 と、深い値が評価値でない行(notEvaluation)を含む組 4(= 深く測れなかった行を含む組)。**道具の定義どおりで、床の欠陥ではない**

## 指示 2: 床の食い違い 24 件(取りこぼし 8・余計 7・当たり方だけ違う 8・比べられない 1)を、境 −400 からの位置で分ける

**注: Event の閾値は `DRAFT_RULE_1.dropCp` = −400**。±300 は優勢(`advantageCp`)と rescreen の候補 (a) の値。以下は −400 に対して数えた。

4M の値の境からの距離:

| 4M の値 | 取りこぼし | 余計 | 当たり方だけ違う | 比べられない |
|---|---|---|---|---|
| 境から 50 以内 | 5 | 3 | 0 | 0 |
| 51〜150 | 2 | 4 | 0 | 0 |
| 151〜300 | 1 | 0 | 1 | 0 |
| 300 超 | 0 | 0 | 3 | 0 |
| cp の差ではない(4M 側が詰み・評価値でない) | 0 | 0 | 4 | 1 |

動いた大きさ(|床 − 4M|。両方が cp の差の組だけ):

| 動き | 取りこぼし | 余計 | 当たり方だけ違う |
|---|---|---|---|
| ≤ 50 | 1 | 0 | 0 |
| 51〜150 | 2 | 5 | 0 |
| 151〜300 | 4 | 2 | 0 |
| 300 超 | 1 | 0 | 3 |
| 片方が cp の差でない | 0 | 0 | 5(比べられない 1 も) |

直後の行の評価の大きさ(4M):

| |直後の cp| | 取りこぼし | 余計 | 当たり方だけ違う | 比べられない |
|---|---|---|---|---|
| < 1000 | 1 | 0 | 0 | 0 |
| 1000〜3000 | 2 | 2 | 0 | 0 |
| ≥ 3000 | 5 | 5 | 4 | 0 |
| 直後が詰み・評価値でない | 0 | 0 | 4 | 1 |

**読み(数えた事実だけ)**
- 取りこぼし・余計の 15 件(どれも cpDrop)は、4M の値が境から 150 以内のものが 14 件
- ただし「境の上で数 cp 揺れた」ではない。動きは 50 cp 以下が 1 件だけで、残り 14 件は 51〜370 cp 動いている
- 15 件のうち 14 件は、直後の評価が ±1000 cp を超える局面(10 件は 3000 以上)。**勝負が決まった後の局面で、差の値が数百 cp 動いて境をまたいだ**
- 当たり方だけ違う 8 件は、どれも matedIfPass が両方に付いたまま。直後の afterPassMate は 8 件とも両方で同じ値。変わったのは次の 2 通り:
  - 直後の行が詰みか大きな cp か(mateAfter −18 ↔ cp −5087 の型、4 件)
  - cpDrop の有無(差が −567 ↔ −240 など。直後が −5000〜−8000 の局面)
- 比べられない 1 件: 4M 側の組が評価値でない(notEvaluation)。床側は −23771 cp の差で cpDrop+matedIfPass

1 件ずつの値は `analysis-floor.json` の `cases`。
