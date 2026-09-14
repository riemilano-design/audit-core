# STEP D3b 計画: 相手を弱くして仮想人間 B・B′ の 20 局を指し直し、死因①の校正を「測れる」側へ寄せる(2026-09-15)

**状態**: 計画。**司令塔が 8. の Q-1〜Q-5 をすべて推奨どおりに決めた(2026-09-15)。** N は **N-b(2,000)を先に**回す。実装と実行は C、監査は f2(司令塔の割り振り)。予測(4.)は測る前に書いた。
**番号**: `D3b`(司令塔の命名)。
**きっかけ**: STEP D3 の実測([STEP_D3_PLAN_2026-09-14.md](STEP_D3_PLAN_2026-09-14.md) §9、記録は `scripts/playtest/records/d3-nnue/`、コミット `2e5f9f0`)。**司令塔の読み**: 道具は 20 局を通して動き、植えた答えは「急落候補のうち窓の中に王手」(B 11 / B′ 18)には出たが、死因①は両群 0。優勢(NNUE の `baseline.scoreCp ≥ +300`)は序盤の +323〜+390 の 5 行(B 4・B′ 1)しか出ず、規則の判定まで届いたのは 1 件。**死因①の校正は「測れなかった」が主なので、D3 計画書 Q-6 のとおり相手を弱くして再実行する。**
**範囲**: `scripts/playtest/` のみ(`explore.ts`・`lib/` の新しい関数とその試験)。**本番の `apps/server/src`(`gameSession.ts` の `go({ movetimeMs: 1000 })` を含む)には触らない。** `data/` にも触らない。
**前提**: HEAD `2e5f9f0`。D3 の道具(`258f374`)と JSON v0(`b46cddb`。`diagnose.ts --events` の各行に `schemaVersion` が付く)がコミット済み。

---

## 1. 位置づけ(**先に書く**)

- **これは D3 と同じく校正である。** 植える答えは B と B′ の違い(5-iii を使うか)で、作った側が知っている。**人の癖の件数として読まない**(D3 の L-1)
- **変えるのは相手の強さ 1 つだけ。** 先手の決め方(B・B′)・上限 200 手・評価(NNUE 版 `replay.ts --nodes 4000000 --threads 1`)・診断(`diagnose.ts`)・死因①の規則(+300 / −400 / 5 手、draft)は D3 と同じにする
- **本番の挙動は変えない。** 相手を弱くするのは探索モード(`explore.ts`)の**開発・検証専用の設定**で、既定(指定しないとき)は D3 と同じ本番どおりの相手
- **閾値は決めない**(CLAUDE.md ルール 4)。優勢の閾値 +300 に序盤の値が近いこと(7.)も、観測として書くだけ

---

## 2. 相手を弱くする手段(設計)

### 2.1 確かめた事実(HEAD `2e5f9f0`。担当がソースで確かめた)

| # | 事実 | 根拠 |
|---|---|---|
| E-1 | 相手の手は `explore.ts:240` の `playOpponentMove(state, engine.asHighPriority(), getApprovedScenarioVariants())` で、`gameSession.ts:242` が `engine.go({ movetimeMs: 1000 })` を呼ぶ | ソース |
| E-2 | `asHighPriority()` は**呼ぶたびに独立したハンドル**を返し、`go(options)` の options を**そのまま** `UsiEngine.go` へ渡す | `apps/server/src/engine/prioritizedEngine.ts:112-128` |
| E-3 | 先手の E 読み(S1〜S3・R の後ろ盾)は**別の** `asHighPriority()` ハンドル(`explore.ts:211`)。候補手・③・`engineReference` は `asLowPriority().goMultiPv`(`explore.ts:180-191・287-298`)で、`go` を通らない | ソース |
| E-4 | `buildGoCommand` は `nodes > 0` なら `go nodes N`(movetime は送らない)、タイムアウトは固定 60,000 ms | `apps/server/src/engine/usiEngine.ts:43`(定数)・`:51-58`(`buildGoCommand`) |
| E-5 | `HighPriorityEngine = Pick<UsiEngine, "position" \| "go">`。`gameSession.ts` はこの形を受け取る | `prioritizedEngine.ts:97` |
| E-6 | `explore.ts` は `setThreads` を送らない。**相手の探索はエンジンの既定 `Threads` 4**(駒得版の `usi` 応答の既定値) | `explore.ts` を grep、`option name Threads type spin default 4`(D0-NNUE で保存した `usi` 応答。駒得版の同じ行は T-6 F-1) |
| E-7 | 既存の `withFixedSearch`(`lib/fixedSearchEngine.ts`)は `LowPriorityEngine` の `goMultiPv` に `nodes` を足す包みで、相手の `go` には効かない | ソース |

### 2.2 形(**本番のコードは変えず、`explore.ts` の側で相手に渡すハンドルだけを包む**)

- **`lib/opponentEngine.ts`(新規)**
  - `withOpponentNodes(engine: HighPriorityEngine, nodes: number | undefined): HighPriorityEngine` ― `nodes` が undefined なら `engine` をそのまま返す。そうでなければ `go: (options) => engine.go({ ...options, nodes })`、`position` はそのまま
  - `parseOpponentNodesOption(argv: readonly string[]): number | undefined` ― `--opponent-nodes` が無ければ undefined。**値が正の整数でない・値が無いときはエラーで止める**(D3 の `--profile` と同じ。黙って本番どおりの相手にしない)
  - `buildHighPriorityHandles(engine: { asHighPriority(): HighPriorityEngine }, opponentNodes: number | undefined): { opponent: HighPriorityEngine; sente: HighPriorityEngine }` ― **相手のハンドルだけを包み、先手(E 読み)のハンドルは包まない**。「相手にだけ渡る」を試験できる形にするための関数
- **`explore.ts`**: `parseArgs` で `opponentNodes` を読み、局ごとに `buildHighPriorityHandles(engine, opponentNodes)` を作って、`playOpponentMove(state, handles.opponent, …)` と `pickMoveWithTier(…, { engine: handles.sente, … })` に渡す。**`asLowPriority()` の呼び出し(候補手・③・`engineReference`)は変えない**
- **`meta` 行の `extra` に `opponentNodes`(指定なしは null)を足す**(P-43 と同じ理由: 記録から対局の条件を読めるようにする)。棋譜 JSON の形は変えない(`replay.ts` は `id`・`moves` しか読まない)
- **`explore.ts` 冒頭の文を書き直す**: 「相手AIの手加減・強さ調整もしない(相手は本番と同一 …)」→「**既定では相手は本番と同一**(`playOpponentMove`、movetime 1000ms)。**`--opponent-nodes N` は開発・検証専用の設定で、相手の `go` にだけ `nodes` を渡す**(本番の `gameSession.ts` は変えない。先手の E 読み・候補手・③・`engineReference` には渡らない)」

---

## 3. N の候補と根拠(**選ぶのは司令塔**)

### 3.1 足場にした数字(どれも**根拠ではなく目安**。条件をそのまま書く ― 規則 11.2)

| # | 数字 | 条件 | 出どころ |
|---|---|---|---|
| N-1 | `go movetime 2000` で **Threads 4 → 約 890 万ノード(depth 21)、Threads 1 → 約 380 万ノード(depth 20)** | 駒得版(MaterialLv1)、1 局面、2026-09-11、「到達ノード数は機械の負荷で変わる」 | [STEP_T-6_PLAN_2026-09-11.md](STEP_T-6_PLAN_2026-09-11.md) F-2(`docs/STEP_T-6_PLAN_2026-09-11.md:15`) |
| N-2 | `go nodes 20000` を Threads 1 で 3 回与えると、bestmove・score・pv・nodes(20057)が 3 回とも一致 | 駒得版、1 局面 | 同 F-1(`docs/STEP_T-6_PLAN_2026-09-11.md:14`) |
| N-3 | **いまの相手(movetime 1000ms・Threads 4)は、N-1 を時間で比例させると約 450 万ノード**と見積もれる。**ただし `MinimumThinkingTime` の既定は 2000 で、movetime 1000 がそのとおり 1 秒で返っているかは確かめていない** | 見積もり | N-1 と E-6(`apps/server/src/game/gameSession.ts:242` の `movetimeMs: 1000`。Threads の既定 4 は `docs/STEP_T-6_PLAN_2026-09-11.md:14`(駒得版)と、担当が D0-NNUE で保存した `usi` 応答 `scratchpad/d0-b1.log:4`(NNUE 版、リポジトリの外)) |
| N-4 | 先手の E 読み(movetime 100ms・Threads 4)は、同じ比例で約 45 万ノード | 見積もり(E は B・B′ では使わない) | N-1 |
| N-5 | 1 手詰の局面で NNUE 版は **677 ノード(depth 8)**で `mate 1` を返した | NNUE 版、1 局面 | [STEP_D0-NNUE_PLAN_2026-09-14.md](STEP_D0-NNUE_PLAN_2026-09-14.md) 6.9(`docs/STEP_D0-NNUE_PLAN_2026-09-14.md:220`。nps 約 58〜59 万は同 `:250`) |
| N-6 | D3 の 20 局で優勢の行は **409 行中 5 行**(B 4・B′ 1)、どれも ply 4〜14。「直前が優勢」の急落候補は 1 件 | NNUE 版の評価、相手はいまの本番どおり | D3 §9.4(`docs/STEP_D3_PLAN_2026-09-14.md:528-529`) |

### 3.2 候補

| 段 | N | いまの相手(N-3)との比 | 読み |
|---|---|---|---|
| **N-a(強め)** | **20,000** | 約 1/200 | N-2 で動くことを確かめてある値。E 読み(N-4)の約 1/20。**それでも浅い手筋(駒のただ取り・数手の詰み)は読める**と見る(N-5: 1 手詰は 1,000 ノード未満で見つかる) |
| **N-b(弱め)** | **2,000** | 約 1/2,000 | N-a の 1/10。**短い詰みは読めるが、数手先の駒得の比べは浅くなる**と見る。B が「取れるなら取る」で駒を得る場面が増えると読む |

- **2 段を 1 桁ずつ離した理由**: N と強さの関係を持つ数字が無い(N-1〜N-5 は速さ・再現性の数字で、強さの数字ではない)。**1 桁の差なら、どちらかで D3 と違いが見えると読む**
- **Threads は変えない**(E-6 の既定 4 のまま)。`setThreads` はエンジン 1 本の全体に効き、候補手・③・`engineReference` の探索条件まで変わる(1. の「変えるのは相手の強さ 1 つだけ」に反する)。**`go nodes N` を Threads 4 で読むと、同じ局面でも手が 1 つに決まらない**(N-2 は Threads 1 の結果)ことを限り(9.)に書く

---

## 4. 予測(**測る前に書く**。N-a・N-b それぞれ。群は B・B′ 各 10 局)

**根拠にした観測**: D3(N-6、20 局とも後手の詰み勝ち、手数の中央値 B 36・B′ 40、急落候補 B 41・B′ 44、窓の中に王手 B 11・B′ 18、死因① 0・0)と、3.2 の読み。**N と強さの関係を持つ数字が無いので、幅は広く、外れ条件で判定する。**

| # | 予測 | N-a(20,000) | N-b(2,000) | 外れたと言える条件 |
|---|---|---|---|---|
| 予-E1 | **先手が勝つ局** | 各群 **0〜2 局** | 各群 **0〜4 局** | 範囲の外 |
| 予-E2 | **上限(200 手)で止まる局** | 各群 **0〜2 局** | 各群 **0〜3 局** | 範囲の外 |
| 予-E3 | **手数の中央値**(上限で止まった局を含む) | D3 より長く、各群 **40〜90** | 各群 **50〜120** | 範囲の外、または D3 の値(B 36・B′ 40)以下 |
| 予-E4 | **優勢の行**(NNUE の `baseline.scoreCp ≥ +300`。\|cp\| ≥ 30000 を除く) | 各群 **5〜40 行**、それを持つ局 **3〜10 局** | 各群 **15〜80 行**、局 **5〜10 局** | どちらかの群で範囲の外 |
| 予-E5 | **「直前が優勢」の急落候補** | 各群 **1〜10 件** | 各群 **2〜20 件** | どちらかの群で範囲の外 |
| 予-E6 | **死因①(draft)** | 各群 **0〜4 件**、2 群の合計 **1 件以上** | 各群 **0〜8 件**、2 群の合計 **2 件以上** | 合計が下限未満、またはどちらかの群で上限を超える |
| 予-E7 | **B と B′ の差の向き**: 死因①と「窓の中に王手」は **B′ ≥ B** | 同左 | 同左 | B′ < B。**当たっても外れても「癖の効果」とは読まない**(L-7: 10 局ずつ・対にならない) |
| 予-E8 | **急落候補の直前の形**は、D3 と同じく **9 割以上が `none`** | 同左 | 同左 | どちらかの群で 9 割未満 |

**当たった場合・外れた場合の読み方(先に書く)**

- **予-E6 の合計が下限に届かなかった場合**: 相手を弱くしても死因①の判定まで届かない。**「規則の 3 つ目(窓の中に王手か詰み)が、弱い相手では満たされにくい」可能性と「優勢そのものが出ない」可能性を、予-E4・E5 で分ける**(E4・E5 が出ていて E6 が 0 なら前者)
- **予-E1 が上限を超えた場合**(先手が勝ちすぎる): 急落が「相手の読みの浅さ」ではなく「先手の勝ち」になり、死因①の校正材料にならない。**そのときは N を戻す向きで司令塔が決める**
- **予-E7**: 向きがどちらでも、群の差は局の揺れと混ざる(L-7)。**件数を並べるだけ**

**予測しないもの**: 1 局の所要(並行しているので根拠にしない)、急落候補の総数(相手の強さで増えるか減るかの向きの根拠が無い)。**数えて出す。**

---

## 5. 見張り

### 5.1 固定例(`lib/opponentEngine.test.ts`。**エンジンは呼ばない**。`go` の options を記録するだけの偽のエンジンを使う。期待値は試験を回す前に手で書く)

| # | 入力 | 期待 |
|---|---|---|
| F-O1 | `withOpponentNodes(偽, 2000)` の `go({ movetimeMs: 1000 })` | 偽のエンジンに渡った options が `{ movetimeMs: 1000, nodes: 2000 }` |
| F-O2 | `withOpponentNodes(偽, undefined)` | 返り値が偽のエンジンそのもの(同じ参照)で、`go({ movetimeMs: 1000 })` の options は `{ movetimeMs: 1000 }`(`nodes` の欄が無い) |
| F-O3 | `buildHighPriorityHandles(偽の PrioritizedEngine, 20000)` の `opponent.go({ movetimeMs: 1000 })` と `sente.go({ movetimeMs: 100 })` | 相手の options は `{ movetimeMs: 1000, nodes: 20000 }`、**先手の options は `{ movetimeMs: 100 }`(`nodes` が無い)**。`asHighPriority()` が 2 回呼ばれ、別々のハンドルであること |
| F-O4 | `buildHighPriorityHandles(偽, undefined)` | 相手・先手とも options がそのまま |
| F-O5 | `parseOpponentNodesOption` | `[]` → undefined / `["--opponent-nodes", "2000"]` → 2000 / `"0"`・`"-5"`・`"1.5"`・`"abc"`・値なし → **エラー** |
| F-O6 | **ソース照合**(`explore.ts`) | `playOpponentMove(state, handles.opponent,` を含み、`playOpponentMove(state, engine.asHighPriority()` を含まない / 先手の `engine:` に `handles.sente` を渡している。**一方向の見張り**(P-32。書き方を変えれば通り抜ける) |
| F-O7 | 候補手・③・`engineReference` に `nodes` が渡らない | **型で守る**: 包みは `HighPriorityEngine`(`go` だけ)で、`asLowPriority()` のハンドル(`goMultiPv`)を包めない。F-O6 の照合で `asLowPriority()` の呼び出しが変わっていない(3 か所 × 2)ことも見る |

### 5.2 変異(**予測は実装の後、当てる前に試験名で書く**。中心を壊す変異を必ず入れる ― 規則 11.8)

| # | 壊し方 | 壊すもの | 鳴るはずの固定例 |
|---|---|---|---|
| **V-O1** | **`nodes` を先手のハンドルに渡し、相手には渡さない** | **中心**(相手にだけ渡る) | F-O3 |
| **V-O2** | **包みが `nodes` を捨てる**(`go(options)` をそのまま渡す) | **中心**(値が届く) | F-O1・F-O3 |
| V-O3 | 未指定でも `nodes: 0` を足す | 未指定なら従来どおり | F-O2・F-O4 |
| V-O4 | 相手と先手に同じハンドルを使う(`asHighPriority()` を 1 回だけ呼ぶ) | 別々のハンドル | F-O3 |
| V-O5 | `parseOpponentNodesOption` が 0・負・小数を通す | 黙って本番どおりの相手にしない | F-O5 |
| V-O6 | `explore.ts` で `playOpponentMove` に `engine.asHighPriority()` を戻す | 配線 | F-O6 |

---

## 6. 実行(**監査 GO・コミットの後**。司令塔が N を 1 段選んでから)

```
explore.ts --profile B  --games 10 --seed 1 --plies 200 --opponent-nodes <N> --out-dir out/d3b-b    (駒得版を SHOGI_ENGINE_PATH で明示。D3 §9.1 と同じ)
explore.ts --profile B2 --games 10 --seed 1 --plies 200 --opponent-nodes <N> --out-dir out/d3b-b2
replay.ts <game-NN.kifu.json> --nodes 4000000 --threads 1 --out out/d3b-nnue/<群>-game-NN.jsonl   (NNUE 版。**3 本並行**)
diagnose.ts out/d3b-nnue/b-game-*.jsonl  --events …
diagnose.ts out/d3b-nnue/b2-game-*.jsonl --events …
```

- **エンジンの宣言**: explore は 1 本(相手・候補手・③・`engineReference` が 1 本のエンジンを共有するため、並行しない)。**replay は宣言に「本数 3」と書き、別の局を別プロセスで同時に回す**([AGENT_PROTOCOL.md](AGENT_PROTOCOL.md) 10 番の注記、`38755c2`)。**宣言の前に、機械全体の YaneuraOu 系のプロセスを数え、他のセッション(いまは B の D-COST)が解放していることを確かめる**
- **最初の 1 局で確かめること**(D3 の L-11 と同じ形): B の game-01 の `meta.extra.opponentNodes` が N であること、kifu JSON の tiers、**そして局の終わりの出力「相手の go(nodes 付き)=K」の K が 1 以上であること**(相手の go に実際に nodes が届いた ― 司令塔の決定、10.4)。**3 つとも確かめてから残りを回す**
- **3 本並行の所要**: 20 局の replay の壁時計の所要と、1 局ごとの所要・load を記録する(**根拠にしない**)。**見込み 50 分前後と比べて報告に添える**。D3 の 1 本ずつの replay は合計 7,987 秒(約 133 分、load 3.6〜4.3)で、3 本で割ると約 44 分。**ただし予-E3 のとおり局が長くなれば、その分だけ延びる**
- **失敗で止める**: exit が 0 でない・出力が空・`UsiEngineTimeoutError` やエラー行。**並行している他の 2 本は、その局が終わるまで待ってから止める**(途中で切った記録を残さない)
- **N-a(20,000)を回すかの条件(司令塔の決定、2026-09-15。N-b を回す前に書いた。「結果を見て条件を選ぶ」形にしないため)**: N-b の 20 局で、**どちらかの群で先手の勝ちが 10 局中 8 局以上**、または **どちらかの群で上限(200 手)で止まる局が 3 局以上**なら、**相手が弱すぎた側に振れた**として N-a を回す。**どちらにも当たらなければ N-a は回さない**(回すかは司令塔が改めて決める)。「どちらかの群で」は担当の読み(司令塔の文は群を指定していない ― 報告で確かめる)
- **記録を置く**: NNUE 版で付け直した 20 本の JSONL を `scripts/playtest/records/d3b-nnue-n<N>/` に、`SHA256SUMS` と README(対局 = 駒得版・`--opponent-nodes N` / 評価 = NNUE 版、両方のエンジンと `nn.bin` の sha256、HEAD、コマンド、期間、load、並行本数)付きで。**`kifuId` は explore の実行ごとに一意だが、同じ `kifuId` が駒得版の explore の JSONL と NNUE 版の replay の JSONL の両方に出る**(P-46)ので、README にその組を書く。棋譜 JSON は `out/` のまま(`kifu/` への登録は人間の判断)

---

## 7. D3 から持ち越す観測(**書くだけ。この STEP では変えない**)

- **優勢の閾値 +300 に、序盤の値が近い**: D3 の優勢の 5 行は ply 4〜14 の +311〜+390。**閾値の +300 のすぐ上に集まっている。** 閾値は判断的知識の仮置き(D1 計画書)で、**この STEP では変えない**。D3b で優勢の行が増えたとき、値がどこに分布するかを数えて並べる
- **急落候補の直前の形は 85 件すべて `none`**: 植えた「玉を囲わない」は、D1 が写す `current_shape` の欄では見えない(D3 の L-8・予-D9)。**A 層の数「玉の隣の自分の駒の数」を Failure Event に足す案は、Failure Event JSON の版 0.2 の候補として書くだけ**(JSON v0 の計画の外。足すかは別の判断)

---

## 8. 決定(司令塔、2026-09-15。すべて担当の推奨どおり)

| # | 判断 | 決定 | 理由 |
|---|---|---|---|
| **Q-1** | N を 1 段選ぶ | **N-b(2,000)を先に回す。N-a(20,000)は 6. の条件に当たったときだけ回す** | D3 の優勢は 409 行中 5 行で、「直前が優勢」の急落候補は 1 件。**材料を増やすことが目的なので、変化が大きい方から測る**。予-E1(先手の勝ちすぎ)が外れたら、N-a へ戻す判断を足場にできる。**ただし N と強さの関係を持つ数字は無い**(3.2) |
| Q-2 | 本実行の前に、N-a・N-b で数局の下見をするか | **しない**(1 段を 20 局で回す) | 下見の結果を見て N を選ぶと「結果を見てから条件を選ぶ」形になる(D3 Q-6 の理由と同じ)。予測は 4. に 2 段とも書いてあるので、1 段を回せばその段の予測と照合できる |
| Q-3 | 相手の `Threads` | **変えない**(既定 4 のまま。**README と 9. の実測に「相手は Threads 4(既定)」と書く**) | 3.2 のとおり、変えると候補手・③・`engineReference` の条件も変わる。**N ノードを 4 スレッドで読むので、同じ局面でも手が決まらない**(L-D3b-2) |
| Q-4 | `opponentNodes` の置き場所 | **`meta.extra` と README だけ**(棋譜 JSON の形は変えない) | `replay.ts` は棋譜 JSON の `id`・`moves` しか読まない。探索モードの JSONL の `meta` に条件が残れば足りる |
| Q-5 | 記録のフォルダ名 | `records/d3b-nnue-n<N>/` | 別の N で回したときに混ざらない |

---

## 9. 分からないこと・限界

- **L-D3b-1 N と強さの関係を持つ数字が無い。** 3.1 は速さと再現性の数字で、「N ノードの相手がどれだけ間違えるか」は測っていない。予測(4.)の幅が広いのはそのため
- **L-D3b-2 `go nodes N` を Threads 4 で読むので、同じ局面・同じ N でも相手の手は 1 つに決まらない**(T-6 F-1 の一致は Threads 1)。**再現の単位は保存した棋譜 JSON**(D3 の L-4 と同じ)
- **L-D3b-3 いまの相手の実際の思考時間を確かめていない**(`MinimumThinkingTime` の既定 2000 と movetime 1000 の関係)。3.1 の N-3 の「約 1/200」「約 1/2,000」は見積もりの比である
- **L-D3b-4 相手を弱くした 20 局は、アプリの利用者が指す相手の記録ではない。** D3 の Q-2(「利用者が実際に指す相手がこれ」)の意味は失われる。**死因①の規則が、弱い相手の記録で当たる・当たらないことは、本番の相手の記録で当たるかを示さない**
- **L-D3b-5 並行した replay の所要**は、3 本が同じ機械の CPU を取り合う値で、1 本ずつの D3 の値と比べられない。**枠の見積もりにだけ使う**
- **L-D3b-6 F-O6 のソース照合は一方向**(P-32)。`explore.ts` の配線は、実行の最初の 1 局の `meta.extra.opponentNodes` で確かめるまで、**相手のハンドルに実際に `nodes` が渡ったかは記録から直接は見えない**(記録に相手の探索のノード数は残らない)。見えるのは `meta` の値と、F-O3 の試験までである。**相手の go(nodes 付き)の回数 K は JSONL には残らず、実行の出力に出る**(§6 の最初の 1 局で K ≥ 1 を確かめる。監査 f2 の指摘で司令塔がコミット時に足した)
- D3 の L-1(演じた癖と本物の初心者の差)・L-5(千日手を判定しない)・L-6(評価の揺れ)・L-7(群の差は局の揺れと混ざる)・L-9(記録に評価関数の種類が残らない、P-43)はそのまま

---

## 10. 実装の記録(実装担当 C が書く)

### 10.1 実装(2026-09-15。基準 HEAD `b18007d`、worktree `scratchpad/wt-d3b`)

- **新規 `lib/opponentEngine.ts`**: `withOpponentNodes`(nodes が undefined なら同じエンジンを返す。そうでなければ go の options に nodes を足し、position はそのまま通す)・`parseOpponentNodesOption`(先頭が 0 でない数字だけを受け付け、それ以外と値なしはエラー)・`buildHighPriorityHandles`(`asHighPriority()` を 2 回呼び、相手のハンドルだけを包む)
- **新規 `lib/opponentEngine.test.ts`**: F-O1〜F-O7(7 件)。偽のエンジンは go の options と position の引数を記録するだけ。**F-O3 は、どちらのハンドルが先に作られたかに頼らず、届いた options の中身で相手と先手を見分ける**
- **`explore.ts`**: 冒頭の文を 2.2 のとおり書き直し(使い方に `[--opponent-nodes <N>]`)、T-7 の「条件を一切変えない」に「--opponent-nodes を付けたときだけ相手の探索量が変わる」を足した。`CliOptions`・`parseArgs` に `opponentNodes`、`runOneGame` の引数に `opponentNodes`、局ごとに `buildHighPriorityHandles(engine, opponentNodes)` を作って `pickMoveWithTier` に `handles.sente`・`playOpponentMove` に `handles.opponent` を渡す。`meta.extra` に `opponentNodes`(指定なしは null)。局の開始の出力に `opponentNodes` を足した。**`engine.asHighPriority()` を直接使う箇所は 0、`engine.asLowPriority()` の 6 か所は変えていない**
- **ハンドルの作り方の違い(監査で見てほしい点)**: これまで先手の E 読みと相手は、**手番ごとに** `engine.asHighPriority()` を作っていた。いまは**局ごとに 1 回**作ったハンドルを使い回す。`asHighPriority()` のハンドルは position を覚えておき、go のたびにそのときの position を送る(`prioritizedEngine.ts:112-128`)ので、使い回しても送る内容は変わらないと読む。**B・B2 は E 読みを使わない**ので、D3b の実行にはこの違いは効かない
- `npx vitest run --dir scripts/playtest`: 36 ファイル・**395 件すべて通過**(基準 388 件 + F-O1〜F-O7 の 7 件)。`npm run typecheck:scripts` rc=0。変えたファイルは `explore.ts`(+22 / −10)と新規 2 ファイルだけ

### 10.2 変異の予測(**実装して試験が通った後、変異を 1 つも当てる前に書いた**。当て方は D3 の 8.9 と同じ ― 試験の全体を回して基準との差で数え、型検査を別に数える。最初に型検査を校正する)

| # | 当て方 | 落ちると予測する試験 | 型検査 |
|---|---|---|---|
| **V-O1** | `buildHighPriorityHandles` で nodes を先手のハンドルに渡し、相手には渡さない | F-O3 | rc=0 |
| **V-O2** | `withOpponentNodes` の go が nodes を捨てる(`engine.go(options)`) | F-O1・F-O3 | rc=0 |
| V-O3 | nodes が undefined でも包み、`nodes: nodes ?? 0` を足す | F-O2・F-O4 | rc=0 |
| V-O4 | `asHighPriority()` を 1 回だけ呼び、相手と先手に同じハンドルを使う | F-O3(**F-O4 は落ちない**: nodes が無ければ同じハンドルでも options は変わらず、見分けがつかない) | rc=0 |
| V-O5 | `parseOpponentNodesOption` が 0・負・小数を通す | F-O5 | rc=0 |
| V-O6 | `explore.ts` で `playOpponentMove` に `engine.asHighPriority()` を戻す | F-O6 | rc=0 |
| V-O7 | `explore.ts` の `meta.extra` から `opponentNodes` を消す | F-O6 | rc=0 |
| V-O8 | `explore.ts` の `parseArgs` が `--opponent-nodes` を読まない(`opponentNodes: undefined`) | F-O6 | rc=0 |

- **V-O6〜V-O8 を捕まえるのは F-O6(ソース照合)だけで、一方向の見張り**(P-32)。書き方を変えれば通り抜ける。**実行の最初の 1 局で `meta.extra.opponentNodes` が N であることを確かめる**(6.)まで、配線は実物で確かめていない

### 10.3 変異を当てた結果・1 回目(2026-09-15。10.2 の予測と突き合わせた。**実装の 1 版目**に対して)

`scratchpad/d3b_mutate.py`。基準は 395 件・失敗 0・tsc rc=0。**型検査の校正 C-0**(わざと型の誤りを 1 行入れる)で tsc rc=1。

**適用 8 / 鳴った(試験で)8 / 型検査だけ 0 / 沈黙 0 / 適用できなかった 0**。**8 件とも、落ちた試験の集合と型検査の rc が予測どおり**(V-O4 で F-O4 が落ちなかったことも予測どおり)。2 ファイルとも元のバイト列に戻ったことを sha256 で確かめた。

**このあと f2 の事前読みの指摘(10.4)を取り込んでコードを変えたので、変異は 10.5 で全部当て直す。**

### 10.4 f2 の事前読みと司令塔の決定を取り込んだ(2026-09-15。**取り込んだコードに対する変異の予測を、当て直す前に書いた**)

**f2 の事前読み**: §2.1 の E-1〜E-7 は HEAD のソースで全部一致(写しの食い違い 0)。鳴らなくなる恐れ 1 つと勧め 3 つ。**司令塔が 4 つとも取り込むと決めた**(2 は任意ではなく入れる)。§3.1 の数字に出典の file:line を添えた(f2 は突き合わせていないため)。

| # | 指摘 | 取り込み方 |
|---|---|---|
| 1 | F-O6 のソース照合がコメントに当たる(否定の文字列がコメントに残ると赤、肯定の文字列をコメントに書くと沈黙) | **照合の前にコメントを除く**(`stripComments`。行コメントとブロックコメント)。**除く関数を先に校正する試験**を足した(コメントの中の照合文字列は消え、コードの行は残る)。F-O6 に「`playOpponentMove(state, handles.sente` を含まない」を足した。変異 V-O9(相手に `handles.sente` を渡し、コメントに正しい行を書く)と、**緑のままであるべき校正 C-1**(コメントに旧い否定の文字列を書く)を足した |
| 2 | 最初の 1 局の確かめを強くする(`meta` の値は「読んだ値」だけ) | `withOpponentNodes` に数える入れ物を渡し、**相手の go に nodes を付けて渡した回数**を数える。`buildHighPriorityHandles` が `opponentNodesGoCalls()` を返し、`explore.ts` は局の終わりの出力に「相手の go(nodes 付き)=K」を出す(**JSONL の形は変えない**)。固定例 F-O8(相手の go だけを数える、先手は数えない、未指定なら 0)。§6 の最初の 1 局の確かめに K ≥ 1 を足した。変異 V-O10(数えない)・V-O11(explore が 0 を報告)・V-O12(出力から消す) |
| 3 | 「正の整数」の判定 | 実装は最初から `/^[1-9][0-9]*$/`。**F-O5 の赤の例に `"2e3"`・`"+2000"`・`" 2000"`・`"2000 "` を足して、通さないことを試験で見る** |
| 4 | V-O3 の分類 | **V-O3 は「形の変異」**: 未指定で `nodes: 0` を足しても、`buildGoCommand` は 0 を movetime として扱うので本番の挙動は変わらない。F-O2・F-O4(と数える入れ物を入れた後は F-O8)は options の形と回数を見るので鳴る |

**取り込んだ後の試験**: 36 ファイル・**397 件すべて通過**(F-O6 の校正と F-O8 の 2 件を足した)、`npm run typecheck:scripts` rc=0。`explore.ts` は +26 / −11。

**当て直す変異の予測**(10.2 の V-O1〜V-O8 は数える入れ物を入れたので書き方と予測が変わるものがある。**当て方は 10.3 と同じ**)

| # | 当て方 | 分類 | 落ちると予測する試験 | 型検査 |
|---|---|---|---|---|
| **V-O1** | nodes を先手のハンドルに渡し、相手には渡さない | 中心 | F-O3・**F-O8**(数える入れ物も先手の側に付くので、相手の go の回数が 0 になる) | rc=0 |
| **V-O2** | 包みの go が nodes を捨てる(`engine.go(options)`。数えるのは残る) | 中心 | F-O1・F-O3(**F-O8 は落ちない**: 回数は数えている) | rc=0 |
| V-O3 | nodes が undefined でも包み、`nodes: nodes ?? 0` を足す | **形の変異** | F-O2・F-O4・**F-O8**(未指定でも数える) | rc=0 |
| V-O4 | `asHighPriority()` を 1 回だけ呼び、相手と先手に同じハンドルを使う | 配線 | F-O3(F-O4・F-O8 は落ちない: 包みは相手の側だけで、先手の go は包みを通らないので数えない) | rc=0 |
| V-O5 | `parseOpponentNodesOption` が 0・負・小数を通す | 入口 | F-O5 | rc=0 |
| V-O6 | `explore.ts` で `playOpponentMove` に `engine.asHighPriority()` を戻す | 配線 | F-O6 | rc=0 |
| V-O7 | `meta.extra` から `opponentNodes` を消す | 記録 | F-O6 | rc=0 |
| V-O8 | `parseArgs` が `--opponent-nodes` を読まない | 入口 | F-O6 | rc=0 |
| **V-O9** | 相手に `handles.sente` を渡し、**すぐ上のコメントに正しい行を書く**(f2 の穴) | 配線 | F-O6 | rc=0 |
| **C-1** | 相手の呼び出しの上に、**旧い否定の文字列をコメントで書く**(コードは正しいまま) | 校正(**緑のままが正しい**) | **無し** | rc=0 |
| V-O10 | 数える入れ物を増やさない | 記録 | F-O8 | rc=0 |
| V-O11 | `explore.ts` が回数を 0 と報告する(`opponentNodesGoCalls: 0`) | 記録 | F-O6 | rc=0 |
| V-O12 | `explore.ts` の局の終わりの出力から回数を消す | 記録 | F-O6 | rc=0 |

- **F-O6(と V-O6〜V-O9・V-O11・V-O12 を捕まえる照合)は一方向の見張り**(P-32)。コメントを除いたので「コメントで通る・コメントで赤になる」は塞いだが、**書き方を変えたコード**(変数を経由して渡す等)は通り抜ける。**実行の最初の 1 局の「相手の go(nodes 付き)=K」(K ≥ 1)で、配線を実物で確かめる**(§6)

### 10.5 取り込んだ後に当て直した結果(2026-09-15。10.4 の予測と突き合わせた)

`scratchpad/d3b_mutate_r2.py`(当て方は 10.3 と同じ。変異ごとに試験の全体を回し、基準との差で数え、型検査を別に数える)。基準は 397 件・失敗 0・tsc rc=0。**型検査の校正 C-0 で tsc rc=1。**

**適用 13 / 鳴った(試験で)12 / 型検査だけ 0 / 沈黙 1 / 適用できなかった 0。沈黙の 1 件は校正 C-1 で、緑のままであることが予測どおり**(コメントに旧い否定の文字列を書いても、コメントを除いた照合は赤にならない)。

**13 件すべて、落ちた試験の集合と型検査の rc が 10.4 の予測と一致した**:

- V-O1 → F-O3・F-O8 / V-O2 → F-O1・F-O3(F-O8 は落ちない)/ V-O3(形の変異)→ F-O2・F-O4・F-O8 / V-O4 → F-O3 / V-O5 → F-O5
- V-O6・V-O7・V-O8・**V-O9(f2 の穴: 相手に `handles.sente`、コメントに正しい行)**・V-O11・V-O12 → F-O6
- V-O10 → F-O8
- **C-1 → 落ちた試験なし**(予測どおり)

2 ファイルとも元のバイト列に戻ったことを sha256 で確かめた。**限り**: F-O6 は一方向の見張り(10.4 の最後)。配線は実行の最初の 1 局の「相手の go(nodes 付き)=K」(K ≥ 1)で実物で確かめる
