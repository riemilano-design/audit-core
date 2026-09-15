# STEP PV-INFO 計画(候補): 読み筋に「標識なしの最後の info 行」を別欄で残す(2026-09-15)

**状態**: 計画の候補(司令塔の依頼。D-SCREEN 計画 §11 の Q-11 を切り出した)。**事前読みは B(版 `1e3711a5` に REVISE: 必須 R-1・R-2、推奨 S-1〜S-4)を取り込み、版 `f37a3b36` に B の再読み GO(任意 3 件: `referenceNodes > 0` のときだけ `engineReference` null で区別できる / `compare.ts` は meta の `dirty` を除かない / V-7 は tsc でも鳴る)**(往復 1 回。司令塔 e3 は決定の要る点なしとし、A の判断で直した)。**計画は確定。着手は D-SCREEN の校正(予-5)の結果を見てから司令塔が決める。****`apps/` に触るので、実装は独立監査の GO を経ないと承認できない**(CLAUDE.md「承認の委任」の条件 1)。
**書いた人**: A(sgogi-coach-64)。**エンジンは使っていない。**基点 HEAD `0f47688`(`cbb985f` からの差に `apps/` は無い。`apps/` の作業ツリーに未コミットの変更が無いことを確かめた)。
**やらないことの先頭**: **本番の③⑤の挙動を変えない。**`goMultiPv` の `lines`・記録の `searchPvs`・HTTP の応答・キャッシュはバイト単位でそのまま。

## 0. 実物から分かった前提

| # | 事実 | 場所 |
|---|---|---|
| E-1 | `goMultiPv` は multipv ごとに**最後に解析できた info 行**を採る(標識付きでも、pv が空でも)。生の行は `infoLines` に残る | `apps/server/src/engine/usiEngine.ts:217-240` |
| E-2 | `parseInfoLine` は `lowerbound`・`upperbound`・`pv`・`raw` を持つ。`info string` などは `pv: []`・score undefined | `apps/server/src/engine/usiInfoParser.ts:37-60`・`:82-105` |
| E-3 | 短い読み筋は標識付きの行から来ている: real-01 の 2 手の 76 本はすべて標識付き・4 手以上の 140 本は 0。20 局版の急落の根では 2 手の 15 本がすべて標識付き・3 手以上の 22 本は 0(どちらも `nodes` 4M) | D2 計画 §0.2・§12.7。20 局版の 4M は `scripts/playtest/records/real-02/kifu2-04.jsonl` の meta(A が読んだ)と D-SCREEN 計画 §11 の E-12 |
| E-7 | 試験で `MultiPvGoResult` を字面で作る場所(`apps/server` の tsconfig は試験も tsc に掛ける): `apps/server/src/analysis/candidateMoveSafetyCheck.test.ts:11-13`・`engineReference.test.ts:49-70` の受け取りと `:118`・`:124`・`:142-143`・`:154-155`・`:209`・`:215`・`:249-250`・`:270`・`api/stateResponse.test.ts:253-255`・`engine/prioritizedEngine.test.ts:14`・`game/gameSession.test.ts` の 11 か所(`:102`〜`:437`)・`scripts/playtest/lib/recorder.test.ts:95-107`・`multiPvSurvey.test.ts:84`・`:264`・`:277`・`:349`・`fixedSearchEngine.test.ts:10`。`recorder.test.ts:31-38` の `planResult` は `as` で型を逃がす | `grep infoLines\|MultiPvGoResult`(A) |
| E-8 | P-48 の「107 行がバイト一致」は **`engineReference` の欄どうし**の比べ。行全体には `elapsedMs`(ready)・`startedAt`・`gitHead`・`dirty`(meta)があり、実行ごとに変わる。`searchPvs`・`response` が再生で一致するかは誰も測っていない。`scripts/playtest/records/d0-nnue` は ready 107 行・`focus_baseline` のある行 106(1 行は王手中) | `docs/STEP_D-COST_PLAN_2026-09-15.md:354`・`compare.ts:25`・A が数えた |
| E-9 | `server.ts` に試験は無い。`backgroundPlan` は `CachedReachablePlan` 型(閉じた interface)の変数に字面で入れるので、欄を写すと tsc の余分な欄の誤りで止まる。記録へ詰め替える関数は `toCachedPlan`(`scripts/playtest/lib/recorder.ts:35`)、応答を作る関数は `buildStateResponseWithPlan`(`stateResponse.ts:1573`) | `server.ts:63`・`:184`・`stateResponse.ts:426` |
| E-4 | 記録の `searchPvs` の経路: `measureEngineReference`(focus の 2 本)→ `computeFocusText` → `computeReachablePlan` の戻り値(**必須の欄**)→ `recorder.ts` が `result.searchPvs` を写す(失敗は null)。`server.ts` は**意図的に写さない** | `engineReference.ts:141-188`・`stateResponse.ts:1785-1881`・`recorder.ts:271`・`server.ts:191` |
| E-5 | 候補手の 2 つの出どころ(`candidate_*`)は、`checkCandidateMovesSafety` が `lines` だけを持つので、`infoLines` に戻れない | `candidateMoveSafetyCheck.ts:74-81`・`:137-149` |
| E-6 | `searchPvs` を読むもの: D2 の `counterfactualOf`・`searchPvStats`・`calibrationBaseline`(U6-T)・`check.ts:374` の報告 | `scripts/playtest/lib/*.ts`・`check.ts` |

## 1. 形(推奨)

- **`MultiPvGoResult` に `stableLines: MultiPvLine[]`(必須)を足す**: multipv ごとに「**`info string` で始まらず、`pv` が 1 手以上で、`lowerbound`・`upperbound` がどちらも付いていない最後の行**」(`PV_PATTERN` は行のどこでも当たるので `info string … pv …` を候補から外す ― B の S-3)。無い multipv は入れない。`lines` の作り方は 1 文字も変えない
- **focus の 2 本だけに運ぶ**(Q-2): `EngineReferenceMeasurement` に `searchPvsStable: SearchPvObservation[]`(`toSearchPvObservations` を `stableLines` に当てる)、`computeReachablePlan` の戻り値にも**必須の欄**で足し、`recorder.ts` が ready 行に `searchPvsStable` を書く。3 値は `searchPvs` と同じ(欄が無い = 測っていない / null = 解析が失敗 / `[]` = 標識なしの行が 1 本も無い)。**王手中・終局で測らなかった行も `[]` になり、「測ったが標識なしの行が無い」と同じ値になる。区別は同じ行の `engineReference` が null かどうかで読めるので、欄では分けない**(B の S-4)。`server.ts`・`ReachablePlanBody`・`CachedReachablePlan` には写さない
- 使う側(D2 の `pvSource` に `stable` を足すか)は**この STEP では決めない**。記録に残して数えるまで

## 2. 固定例(`usiEngine.test.ts` の `dispatchLine` の形。期待は手で導いた)

| # | info 行の並び(multipv 1) | `lines` の pv(今と同じ) | `stableLines` の pv |
|---|---|---|---|
| F-1 | d10 標識なし 12 手 → d11 `upperbound` 2 手 | 2 手・upperbound | 12 手 |
| F-1b | F-1 の標識を `lowerbound` に | 2 手・lowerbound | 12 手 |
| F-2 | d1 `lowerbound` 2 手だけ | 2 手 | multipv 1 が無い |
| F-3 | d9 標識なし 15 手 → d10 upperbound 2 手 → d10 標識なし 9 手 | 9 手 | 9 手(最後。長さで選ばない) |
| F-4 | multipv 1 は標識なし→標識付き、multipv 2 は標識なしだけ(交互に流す) | 各最後 | 1 は標識なしの行・2 はその行(番号で分ける) |
| F-5 | 標識なし 8 手 → `info string …` → `info depth 12 nodes …`(pv なし) | 今と同じ(空で上書き ― U6-L の観測の試験) | 8 手(pv の無い行は候補にしない) |
| F-5b | 標識付き 2 手 → `info string foo pv 7g7f`(pv 1 手・標識なし) | 今と同じ | 候補にしない(`multipv 1` が無い) |
| F-6 | `measureEngineReference` の偽のエンジン | `searchPvs` は今と同じ・`searchPvsStable` は `stableLines` の写し・王手中 / 終局は両方 `[]` | |
| F-7 | 記録と応答 | 記録の ready 行に `searchPvsStable` がある・解析失敗で null・**HTTP の応答とキャッシュに `searchPvsStable` も `searchPvs` も無い**(キーで確かめる) | |
| F-7b | `toCachedPlan`・`buildStateResponseWithPlan` の出力 | `searchPvsStable` も `searchPvs` もキーが無い(`toCachedPlan` の「欄を増やしたら見張りも増やす」の件に当てる) | |

**既存の試験の主張(`expect`)は変えない**(本番の挙動を変えない、の見張り)。**変えるのは E-7 の字面の `MultiPvGoResult` に `stableLines: []` を足すことだけ**(偽の結果は `infoLines: []` なので、それと矛盾しない値は `[]`。既存の主張は `searchPvsStable` を見ていないので、この値で期待が決まることはない。**`EngineReferenceMeasurement` や `computeReachablePlan` の戻り値を丸ごと `toEqual` で比べる主張があれば、実装の報告に例外として名前を挙げる**)。`recorder.test.ts` の `planResult` にも `searchPvsStable: []` を足す(`as` で型が止めないため)。

## 3. 変異(規則 11.3・11.8。予測は実装の後、当てる前に試験の単位で書く)

中心: **V-1** `stableLines` に標識を見ない(F-1)/ **V-2** `upperbound` だけ見る(F-1b)/ **V-3** 最初の標識なしの行を採る(F-3)/ **V-4** 最も長い pv の行を採る(F-3)/ **V-5** `lines` を `stableLines` で作る(③が変わる。F-1 の `lines` と既存の試験)/ **V-6** multipv を分けない(F-4)/ **V-7** `toCachedPlan` で `searchPvsStable` を写す(F-7b)。周辺: V-8 pv が空の行も候補にする(F-5)・V-9 解析失敗で `[]`(F-7)・V-10 `info string` を候補にする(F-5b)。**`server.ts` で写す変異は試験では鳴らない(E-9)。実装の監査で `apps/server` の `tsc --noEmit` を worktree で回し、型で止まることを確かめる**(B の S-1)。

## 4. 測り方と予測(**測る前に書く。書いた人 A、見たもの: E-3 の数だけ。標識なしの行が info の中にどれだけあるかは誰も見ていない**)

- エンジンを持つセッションが本数を宣言して回す: (1) `scripts/playtest/records/d0-nnue` の 7 局を 4M・Threads 1 で再生し、**欄を名前で決めて**今の記録と ready 行ごとに比べる(`elapsedMs` と meta は比べない ― E-8)(2) 20 局版の 2 人目のうち Event のある 12 局を 4M で再生し、急落の根の `focus_baseline` を数える

| # | 予測 | 外れたと言える条件 |
|---|---|---|
| 予-1 | (1) の ready 107 行で、`engineReference` がバイト一致(P-48 の再現) | 1 行でも違う |
| 予-1b | (1) の ready 107 行で、`searchPvs` と `response` もバイト一致(**確信は弱い。誰も測っていない ― E-8**) | 1 行でも違う(外れても PV-INFO の変更のせいとは言えない。まず今のコードで 2 回再生して比べる) |
| 予-2 | (1) の `focus_baseline` のある 106 行のうち最後の行が標識付きの行を分母に、`searchPvsStable` に `focus_baseline` がある行は **95% 以上** | 95% 未満 |
| 予-3 | 20 局版の急落の根 37 件で、`searchPvsStable` の読み筋が 2 手以下は **0〜2 件**(今の `searchPvs` は 15 件)、6 手以上は **32 件以上** | 2 手以下が 3 件以上 |
| 予-4 | 標識付きだった 15 件のうち、標識なしの行の 1 手目が最後の行の 1 手目と違うのは **3〜10 件**(確信は弱い) | 3 件未満か 10 件超 |

## 5. 決定が要る点

| # | 点 | 推奨 | ほかの案 |
|---|---|---|---|
| Q-1 | どの行を残すか | 標識なしの**最後**の行(一番新しい確定値) | 標識なしで**最も長い** pv の行(古い反復の読み筋を採りうる)/ 両方 |
| Q-2 | 運ぶ範囲 | focus の 2 本(D2 が使う) | 候補手の 2 本も(`checkCandidateMovesSafety` の戻り値を変える ― E-5) |
| Q-3 | 形 | 別欄 `searchPvsStable` | `infoLines` を記録に全部残す(記録が大きくなる)/ `searchPvs` を置き換える(③の読み筋でなくなる。U6-L 決定 1 に反する) |

## 6. やらないこと・限界

- ③⑤の文・候補手の除外・閾値を変えること。`lines` の採り方を変えること(U6-L の観測の試験の件も直さない)。HTTP の応答・キャッシュに読み筋を載せること。D2・D-SCREEN の使い方を決めること
- **限界**: 標識なしの行は最後の行より浅い反復の値で、**③が使った評価値でも最善手でもない**。`bestmove` と 1 手目が違いうる(予-4 で数える)。D-SCREEN §11 の `searchPvsDeep` は `measureEngineReference` の写しなので、この STEP の後なら同じ呼び出しから `stableLines` 側も取れる(使うかは D-SCREEN の実装で決める)

**事前読み B(版 `1e3711a5` の REVISE)の取り込み**: R-1 → E-7・2. の既存の試験の段落・F-7b / R-2 → E-8・4. の (1)・予-1・予-1b・予-2 の分母 / S-1 → E-9・V-7・監査の tsc / S-2 → E-3 の出どころ / S-3 → 1. の候補の条件・F-5b・V-10 / S-4 → 1. の 3 値の段落
