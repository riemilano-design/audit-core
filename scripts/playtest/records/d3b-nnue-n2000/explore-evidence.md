# 付録: 探索(explore)の最初の 1 局の検問の証拠(STEP D3b)

計画書 `docs/STEP_D3b_PLAN_2026-09-15.md` §6・§11.2 の検問(meta 行の `opponentNodes`・棋譜 JSON の tiers・「相手の go(nodes 付き)=K」)を、**コミットされる記録の外にある実物から写したもの**(司令塔の決定、監査 f2 の指摘)。

- **出どころ**: 探索の JSONL と棋譜 JSON は worktree(HEAD `e005dbb`)の `scripts/playtest/out/d3b-b/`・`scripts/playtest/out/d3b-b2/` の `game-NN.jsonl`・`game-NN.kifu.json`。標準出力は実行担当 C の scratchpad の `d3b-explore-B.stdout`・`d3b-explore-B2.stdout`(`explore.ts` の出力をそのまま保存したもの)
- **探索の JSONL と棋譜 JSON そのものはコミットしない**(`kifu/` への登録は人間の判断)。この付録は `SHA256SUMS` に入れない(`SHA256SUMS` は NNUE 版の記録 20 本の一覧)
- 各局について (1) 探索の JSONL の meta 行(そのまま 1 行)、(2) 終了行(`kind: "end"`、そのまま 1 行)、(3) 棋譜 JSON の tiers の件数と段の内訳、(4) 標準出力の「相手の go(nodes 付き)=K」の行(そのまま)を写した。**`opponentNodes` は meta 行の最上位の欄**(`explore.ts` の `meta.extra` を `lib/recorder.ts:364` の `buildMetaLine` が最上位へ展開する)

## B(`--profile B`)

### B game-01

(1) meta 行

```json
{"kind":"meta","kifuId":"explore-2026-09-14T23:41:36.952Z-01-B","startedAt":"2026-09-14T23:41:37.909Z","gitHead":"e005dbb43b8a8644437fadaafc4cabde0e99cb0f","dirty":false,"dirtyPaths":[],"dirtyCount":0,"enginePath":"/Users/midoriko/Desktop/sgogi-coach/apps/server/engine/YaneuraOu-by-gcc","mode":"explore","profile":"B","seed":2,"randomRate":0,"pliesCap":200,"referenceNodes":4000000,"opponentNodes":2000}
```

(2) 終了行

```json
{"kind":"end","reason":"game_over","ply":52}
```

(3) 棋譜 JSON: `id` `explore-2026-09-14T23:41:36.952Z-01-B`・手 52・tiers 26 件・内訳 5-i 2・5-ii 3・5-iii 4・5-iv-a 7・5-iv-b 9・5-v 1

(4) 標準出力

```text
[explore] 局 1/10 終了: 手数=52, 理由=game_over, 158232ms, 相手の go(nodes 付き)=26
```

### B game-02

(1) meta 行

```json
{"kind":"meta","kifuId":"explore-2026-09-14T23:41:36.952Z-02-B","startedAt":"2026-09-14T23:44:16.259Z","gitHead":"e005dbb43b8a8644437fadaafc4cabde0e99cb0f","dirty":false,"dirtyPaths":[],"dirtyCount":0,"enginePath":"/Users/midoriko/Desktop/sgogi-coach/apps/server/engine/YaneuraOu-by-gcc","mode":"explore","profile":"B","seed":3,"randomRate":0,"pliesCap":200,"referenceNodes":4000000,"opponentNodes":2000}
```

(2) 終了行

```json
{"kind":"end","reason":"game_over","ply":50}
```

(3) 棋譜 JSON: `id` `explore-2026-09-14T23:41:36.952Z-02-B`・手 50・tiers 25 件・内訳 5-i 4・5-ii 5・5-iii 5・5-iv-a 4・5-iv-b 7・5-v 0

(4) 標準出力

```text
[explore] 局 2/10 終了: 手数=50, 理由=game_over, 136957ms, 相手の go(nodes 付き)=25
```

### B game-03

(1) meta 行

```json
{"kind":"meta","kifuId":"explore-2026-09-14T23:41:36.952Z-03-B","startedAt":"2026-09-14T23:46:33.263Z","gitHead":"e005dbb43b8a8644437fadaafc4cabde0e99cb0f","dirty":false,"dirtyPaths":[],"dirtyCount":0,"enginePath":"/Users/midoriko/Desktop/sgogi-coach/apps/server/engine/YaneuraOu-by-gcc","mode":"explore","profile":"B","seed":4,"randomRate":0,"pliesCap":200,"referenceNodes":4000000,"opponentNodes":2000}
```

(2) 終了行

```json
{"kind":"end","reason":"game_over","ply":42}
```

(3) 棋譜 JSON: `id` `explore-2026-09-14T23:41:36.952Z-03-B`・手 42・tiers 21 件・内訳 5-i 2・5-ii 5・5-iii 2・5-iv-a 5・5-iv-b 6・5-v 1

(4) 標準出力

```text
[explore] 局 3/10 終了: 手数=42, 理由=game_over, 113318ms, 相手の go(nodes 付き)=21
```

### B game-04

(1) meta 行

```json
{"kind":"meta","kifuId":"explore-2026-09-14T23:41:36.952Z-04-B","startedAt":"2026-09-14T23:48:26.631Z","gitHead":"e005dbb43b8a8644437fadaafc4cabde0e99cb0f","dirty":false,"dirtyPaths":[],"dirtyCount":0,"enginePath":"/Users/midoriko/Desktop/sgogi-coach/apps/server/engine/YaneuraOu-by-gcc","mode":"explore","profile":"B","seed":5,"randomRate":0,"pliesCap":200,"referenceNodes":4000000,"opponentNodes":2000}
```

(2) 終了行

```json
{"kind":"end","reason":"game_over","ply":48}
```

(3) 棋譜 JSON: `id` `explore-2026-09-14T23:41:36.952Z-04-B`・手 48・tiers 24 件・内訳 5-i 2・5-ii 2・5-iii 3・5-iv-a 8・5-iv-b 8・5-v 1

(4) 標準出力

```text
[explore] 局 4/10 終了: 手数=48, 理由=game_over, 155538ms, 相手の go(nodes 付き)=24
```

### B game-05

(1) meta 行

```json
{"kind":"meta","kifuId":"explore-2026-09-14T23:41:36.952Z-05-B","startedAt":"2026-09-14T23:51:02.286Z","gitHead":"e005dbb43b8a8644437fadaafc4cabde0e99cb0f","dirty":false,"dirtyPaths":[],"dirtyCount":0,"enginePath":"/Users/midoriko/Desktop/sgogi-coach/apps/server/engine/YaneuraOu-by-gcc","mode":"explore","profile":"B","seed":6,"randomRate":0,"pliesCap":200,"referenceNodes":4000000,"opponentNodes":2000}
```

(2) 終了行

```json
{"kind":"end","reason":"game_over","ply":26}
```

(3) 棋譜 JSON: `id` `explore-2026-09-14T23:41:36.952Z-05-B`・手 26・tiers 13 件・内訳 5-i 0・5-ii 2・5-iii 2・5-iv-a 9・5-iv-b 0・5-v 0

(4) 標準出力

```text
[explore] 局 5/10 終了: 手数=26, 理由=game_over, 83958ms, 相手の go(nodes 付き)=13
```

### B game-06

(1) meta 行

```json
{"kind":"meta","kifuId":"explore-2026-09-14T23:41:36.952Z-06-B","startedAt":"2026-09-14T23:52:26.386Z","gitHead":"e005dbb43b8a8644437fadaafc4cabde0e99cb0f","dirty":false,"dirtyPaths":[],"dirtyCount":0,"enginePath":"/Users/midoriko/Desktop/sgogi-coach/apps/server/engine/YaneuraOu-by-gcc","mode":"explore","profile":"B","seed":7,"randomRate":0,"pliesCap":200,"referenceNodes":4000000,"opponentNodes":2000}
```

(2) 終了行

```json
{"kind":"end","reason":"game_over","ply":38}
```

(3) 棋譜 JSON: `id` `explore-2026-09-14T23:41:36.952Z-06-B`・手 38・tiers 19 件・内訳 5-i 2・5-ii 2・5-iii 4・5-iv-a 7・5-iv-b 2・5-v 2

(4) 標準出力

```text
[explore] 局 6/10 終了: 手数=38, 理由=game_over, 102953ms, 相手の go(nodes 付き)=19
```

### B game-07

(1) meta 行

```json
{"kind":"meta","kifuId":"explore-2026-09-14T23:41:36.952Z-07-B","startedAt":"2026-09-14T23:54:09.472Z","gitHead":"e005dbb43b8a8644437fadaafc4cabde0e99cb0f","dirty":false,"dirtyPaths":[],"dirtyCount":0,"enginePath":"/Users/midoriko/Desktop/sgogi-coach/apps/server/engine/YaneuraOu-by-gcc","mode":"explore","profile":"B","seed":8,"randomRate":0,"pliesCap":200,"referenceNodes":4000000,"opponentNodes":2000}
```

(2) 終了行

```json
{"kind":"end","reason":"game_over","ply":24}
```

(3) 棋譜 JSON: `id` `explore-2026-09-14T23:41:36.952Z-07-B`・手 24・tiers 12 件・内訳 5-i 0・5-ii 2・5-iii 2・5-iv-a 8・5-iv-b 0・5-v 0

(4) 標準出力

```text
[explore] 局 7/10 終了: 手数=24, 理由=game_over, 75440ms, 相手の go(nodes 付き)=12
```

### B game-08

(1) meta 行

```json
{"kind":"meta","kifuId":"explore-2026-09-14T23:41:36.952Z-08-B","startedAt":"2026-09-14T23:55:24.954Z","gitHead":"e005dbb43b8a8644437fadaafc4cabde0e99cb0f","dirty":false,"dirtyPaths":[],"dirtyCount":0,"enginePath":"/Users/midoriko/Desktop/sgogi-coach/apps/server/engine/YaneuraOu-by-gcc","mode":"explore","profile":"B","seed":9,"randomRate":0,"pliesCap":200,"referenceNodes":4000000,"opponentNodes":2000}
```

(2) 終了行

```json
{"kind":"end","reason":"game_over","ply":28}
```

(3) 棋譜 JSON: `id` `explore-2026-09-14T23:41:36.952Z-08-B`・手 28・tiers 14 件・内訳 5-i 1・5-ii 2・5-iii 2・5-iv-a 9・5-iv-b 0・5-v 0

(4) 標準出力

```text
[explore] 局 8/10 終了: 手数=28, 理由=game_over, 96618ms, 相手の go(nodes 付き)=14
```

### B game-09

(1) meta 行

```json
{"kind":"meta","kifuId":"explore-2026-09-14T23:41:36.952Z-09-B","startedAt":"2026-09-14T23:57:01.634Z","gitHead":"e005dbb43b8a8644437fadaafc4cabde0e99cb0f","dirty":false,"dirtyPaths":[],"dirtyCount":0,"enginePath":"/Users/midoriko/Desktop/sgogi-coach/apps/server/engine/YaneuraOu-by-gcc","mode":"explore","profile":"B","seed":10,"randomRate":0,"pliesCap":200,"referenceNodes":4000000,"opponentNodes":2000}
```

(2) 終了行

```json
{"kind":"end","reason":"game_over","ply":34}
```

(3) 棋譜 JSON: `id` `explore-2026-09-14T23:41:36.952Z-09-B`・手 34・tiers 17 件・内訳 5-i 1・5-ii 4・5-iii 2・5-iv-a 9・5-iv-b 1・5-v 0

(4) 標準出力

```text
[explore] 局 9/10 終了: 手数=34, 理由=game_over, 100575ms, 相手の go(nodes 付き)=17
```

### B game-10

(1) meta 行

```json
{"kind":"meta","kifuId":"explore-2026-09-14T23:41:36.952Z-10-B","startedAt":"2026-09-14T23:58:42.324Z","gitHead":"e005dbb43b8a8644437fadaafc4cabde0e99cb0f","dirty":false,"dirtyPaths":[],"dirtyCount":0,"enginePath":"/Users/midoriko/Desktop/sgogi-coach/apps/server/engine/YaneuraOu-by-gcc","mode":"explore","profile":"B","seed":11,"randomRate":0,"pliesCap":200,"referenceNodes":4000000,"opponentNodes":2000}
```

(2) 終了行

```json
{"kind":"end","reason":"game_over","ply":56}
```

(3) 棋譜 JSON: `id` `explore-2026-09-14T23:41:36.952Z-10-B`・手 56・tiers 28 件・内訳 5-i 2・5-ii 5・5-iii 5・5-iv-a 7・5-iv-b 9・5-v 0

(4) 標準出力

```text
[explore] 局 10/10 終了: 手数=56, 理由=game_over, 195438ms, 相手の go(nodes 付き)=28
```

## B′(`--profile B2`)

### B2 game-01

(1) meta 行

```json
{"kind":"meta","kifuId":"explore-2026-09-15T00:02:02.301Z-01-B2","startedAt":"2026-09-15T00:02:02.636Z","gitHead":"e005dbb43b8a8644437fadaafc4cabde0e99cb0f","dirty":false,"dirtyPaths":[],"dirtyCount":0,"enginePath":"/Users/midoriko/Desktop/sgogi-coach/apps/server/engine/YaneuraOu-by-gcc","mode":"explore","profile":"B2","seed":2,"randomRate":0,"pliesCap":200,"referenceNodes":4000000,"opponentNodes":2000}
```

(2) 終了行

```json
{"kind":"end","reason":"game_over","ply":50}
```

(3) 棋譜 JSON: `id` `explore-2026-09-15T00:02:02.301Z-01-B2`・手 50・tiers 25 件・内訳 5-i 5・5-ii 4・5-iii 0・5-iv-a 5・5-iv-b 8・5-v 3

(4) 標準出力

```text
[explore] 局 1/10 終了: 手数=50, 理由=game_over, 170529ms, 相手の go(nodes 付き)=25
```

### B2 game-02

(1) meta 行

```json
{"kind":"meta","kifuId":"explore-2026-09-15T00:02:02.301Z-02-B2","startedAt":"2026-09-15T00:04:53.266Z","gitHead":"e005dbb43b8a8644437fadaafc4cabde0e99cb0f","dirty":false,"dirtyPaths":[],"dirtyCount":0,"enginePath":"/Users/midoriko/Desktop/sgogi-coach/apps/server/engine/YaneuraOu-by-gcc","mode":"explore","profile":"B2","seed":3,"randomRate":0,"pliesCap":200,"referenceNodes":4000000,"opponentNodes":2000}
```

(2) 終了行

```json
{"kind":"end","reason":"game_over","ply":48}
```

(3) 棋譜 JSON: `id` `explore-2026-09-15T00:02:02.301Z-02-B2`・手 48・tiers 24 件・内訳 5-i 3・5-ii 6・5-iii 0・5-iv-a 6・5-iv-b 7・5-v 2

(4) 標準出力

```text
[explore] 局 2/10 終了: 手数=48, 理由=game_over, 121059ms, 相手の go(nodes 付き)=24
```

### B2 game-03

(1) meta 行

```json
{"kind":"meta","kifuId":"explore-2026-09-15T00:02:02.301Z-03-B2","startedAt":"2026-09-15T00:06:54.417Z","gitHead":"e005dbb43b8a8644437fadaafc4cabde0e99cb0f","dirty":false,"dirtyPaths":[],"dirtyCount":0,"enginePath":"/Users/midoriko/Desktop/sgogi-coach/apps/server/engine/YaneuraOu-by-gcc","mode":"explore","profile":"B2","seed":4,"randomRate":0,"pliesCap":200,"referenceNodes":4000000,"opponentNodes":2000}
```

(2) 終了行

```json
{"kind":"end","reason":"game_over","ply":56}
```

(3) 棋譜 JSON: `id` `explore-2026-09-15T00:02:02.301Z-03-B2`・手 56・tiers 28 件・内訳 5-i 3・5-ii 7・5-iii 0・5-iv-a 6・5-iv-b 9・5-v 3

(4) 標準出力

```text
[explore] 局 3/10 終了: 手数=56, 理由=game_over, 124385ms, 相手の go(nodes 付き)=28
```

### B2 game-04

(1) meta 行

```json
{"kind":"meta","kifuId":"explore-2026-09-15T00:02:02.301Z-04-B2","startedAt":"2026-09-15T00:08:58.884Z","gitHead":"e005dbb43b8a8644437fadaafc4cabde0e99cb0f","dirty":false,"dirtyPaths":[],"dirtyCount":0,"enginePath":"/Users/midoriko/Desktop/sgogi-coach/apps/server/engine/YaneuraOu-by-gcc","mode":"explore","profile":"B2","seed":5,"randomRate":0,"pliesCap":200,"referenceNodes":4000000,"opponentNodes":2000}
```

(2) 終了行

```json
{"kind":"end","reason":"game_over","ply":58}
```

(3) 棋譜 JSON: `id` `explore-2026-09-15T00:02:02.301Z-04-B2`・手 58・tiers 29 件・内訳 5-i 3・5-ii 5・5-iii 0・5-iv-a 6・5-iv-b 11・5-v 4

(4) 標準出力

```text
[explore] 局 4/10 終了: 手数=58, 理由=game_over, 181294ms, 相手の go(nodes 付き)=29
```

### B2 game-05

(1) meta 行

```json
{"kind":"meta","kifuId":"explore-2026-09-15T00:02:02.301Z-05-B2","startedAt":"2026-09-15T00:12:00.250Z","gitHead":"e005dbb43b8a8644437fadaafc4cabde0e99cb0f","dirty":false,"dirtyPaths":[],"dirtyCount":0,"enginePath":"/Users/midoriko/Desktop/sgogi-coach/apps/server/engine/YaneuraOu-by-gcc","mode":"explore","profile":"B2","seed":6,"randomRate":0,"pliesCap":200,"referenceNodes":4000000,"opponentNodes":2000}
```

(2) 終了行

```json
{"kind":"end","reason":"game_over","ply":36}
```

(3) 棋譜 JSON: `id` `explore-2026-09-15T00:02:02.301Z-05-B2`・手 36・tiers 18 件・内訳 5-i 1・5-ii 3・5-iii 0・5-iv-a 6・5-iv-b 6・5-v 2

(4) 標準出力

```text
[explore] 局 5/10 終了: 手数=36, 理由=game_over, 79182ms, 相手の go(nodes 付き)=18
```

### B2 game-06

(1) meta 行

```json
{"kind":"meta","kifuId":"explore-2026-09-15T00:02:02.301Z-06-B2","startedAt":"2026-09-15T00:13:19.517Z","gitHead":"e005dbb43b8a8644437fadaafc4cabde0e99cb0f","dirty":false,"dirtyPaths":[],"dirtyCount":0,"enginePath":"/Users/midoriko/Desktop/sgogi-coach/apps/server/engine/YaneuraOu-by-gcc","mode":"explore","profile":"B2","seed":7,"randomRate":0,"pliesCap":200,"referenceNodes":4000000,"opponentNodes":2000}
```

(2) 終了行

```json
{"kind":"end","reason":"game_over","ply":34}
```

(3) 棋譜 JSON: `id` `explore-2026-09-15T00:02:02.301Z-06-B2`・手 34・tiers 17 件・内訳 5-i 2・5-ii 2・5-iii 0・5-iv-a 4・5-iv-b 6・5-v 3

(4) 標準出力

```text
[explore] 局 6/10 終了: 手数=34, 理由=game_over, 72370ms, 相手の go(nodes 付き)=17
```

### B2 game-07

(1) meta 行

```json
{"kind":"meta","kifuId":"explore-2026-09-15T00:02:02.301Z-07-B2","startedAt":"2026-09-15T00:14:31.966Z","gitHead":"e005dbb43b8a8644437fadaafc4cabde0e99cb0f","dirty":false,"dirtyPaths":[],"dirtyCount":0,"enginePath":"/Users/midoriko/Desktop/sgogi-coach/apps/server/engine/YaneuraOu-by-gcc","mode":"explore","profile":"B2","seed":8,"randomRate":0,"pliesCap":200,"referenceNodes":4000000,"opponentNodes":2000}
```

(2) 終了行

```json
{"kind":"end","reason":"game_over","ply":50}
```

(3) 棋譜 JSON: `id` `explore-2026-09-15T00:02:02.301Z-07-B2`・手 50・tiers 25 件・内訳 5-i 5・5-ii 4・5-iii 0・5-iv-a 5・5-iv-b 7・5-v 4

(4) 標準出力

```text
[explore] 局 7/10 終了: 手数=50, 理由=game_over, 110146ms, 相手の go(nodes 付き)=25
```

### B2 game-08

(1) meta 行

```json
{"kind":"meta","kifuId":"explore-2026-09-15T00:02:02.301Z-08-B2","startedAt":"2026-09-15T00:16:22.132Z","gitHead":"e005dbb43b8a8644437fadaafc4cabde0e99cb0f","dirty":false,"dirtyPaths":[],"dirtyCount":0,"enginePath":"/Users/midoriko/Desktop/sgogi-coach/apps/server/engine/YaneuraOu-by-gcc","mode":"explore","profile":"B2","seed":9,"randomRate":0,"pliesCap":200,"referenceNodes":4000000,"opponentNodes":2000}
```

(2) 終了行

```json
{"kind":"end","reason":"game_over","ply":58}
```

(3) 棋譜 JSON: `id` `explore-2026-09-15T00:02:02.301Z-08-B2`・手 58・tiers 29 件・内訳 5-i 3・5-ii 8・5-iii 0・5-iv-a 6・5-iv-b 11・5-v 1

(4) 標準出力

```text
[explore] 局 8/10 終了: 手数=58, 理由=game_over, 139643ms, 相手の go(nodes 付き)=29
```

### B2 game-09

(1) meta 行

```json
{"kind":"meta","kifuId":"explore-2026-09-15T00:02:02.301Z-09-B2","startedAt":"2026-09-15T00:18:41.800Z","gitHead":"e005dbb43b8a8644437fadaafc4cabde0e99cb0f","dirty":false,"dirtyPaths":[],"dirtyCount":0,"enginePath":"/Users/midoriko/Desktop/sgogi-coach/apps/server/engine/YaneuraOu-by-gcc","mode":"explore","profile":"B2","seed":10,"randomRate":0,"pliesCap":200,"referenceNodes":4000000,"opponentNodes":2000}
```

(2) 終了行

```json
{"kind":"end","reason":"game_over","ply":38}
```

(3) 棋譜 JSON: `id` `explore-2026-09-15T00:02:02.301Z-09-B2`・手 38・tiers 19 件・内訳 5-i 2・5-ii 3・5-iii 0・5-iv-a 6・5-iv-b 6・5-v 2

(4) 標準出力

```text
[explore] 局 9/10 終了: 手数=38, 理由=game_over, 85810ms, 相手の go(nodes 付き)=19
```

### B2 game-10

(1) meta 行

```json
{"kind":"meta","kifuId":"explore-2026-09-15T00:02:02.301Z-10-B2","startedAt":"2026-09-15T00:20:07.628Z","gitHead":"e005dbb43b8a8644437fadaafc4cabde0e99cb0f","dirty":false,"dirtyPaths":[],"dirtyCount":0,"enginePath":"/Users/midoriko/Desktop/sgogi-coach/apps/server/engine/YaneuraOu-by-gcc","mode":"explore","profile":"B2","seed":11,"randomRate":0,"pliesCap":200,"referenceNodes":4000000,"opponentNodes":2000}
```

(2) 終了行

```json
{"kind":"end","reason":"game_over","ply":50}
```

(3) 棋譜 JSON: `id` `explore-2026-09-15T00:02:02.301Z-10-B2`・手 50・tiers 25 件・内訳 5-i 3・5-ii 6・5-iii 0・5-iv-a 6・5-iv-b 5・5-v 5

(4) 標準出力

```text
[explore] 局 10/10 終了: 手数=50, 理由=game_over, 91505ms, 相手の go(nodes 付き)=25
```
