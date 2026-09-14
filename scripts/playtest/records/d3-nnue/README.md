# records/d3-nnue ― 縛った初心者の決め方(B・B′)で指した 20 局を NNUE 版で付け直した記録(STEP D3)

**対局 = 駒得版 / 評価 = NNUE 版。** 記録の `meta.enginePath` は評価(再生)に使ったエンジンのパスで、対局の相手のエンジンはここに残らない(P-43)。この README が正本である。

| 項目 | 値 |
|---|---|
| ファイル | `b-game-01.jsonl`〜`b-game-10.jsonl`(B)・`b2-game-01.jsonl`〜`b2-game-10.jsonl`(B′。コードでは `B2`)。`SHA256SUMS` に 20 本の sha256 |
| コード | HEAD `258f374`(STEP D3 の道具)の worktree。汚れ 0(`node_modules` のリンクと `scripts/playtest/out/` だけ) |
| 対局(explore) | `SHOGI_ENGINE_PATH=<共有ツリー>/apps/server/engine/YaneuraOu-by-gcc npx tsx scripts/playtest/explore.ts --profile B --games 10 --seed 1 --plies 200 --out-dir scripts/playtest/out/d3-b`(B′ は `--profile B2`・`--out-dir scripts/playtest/out/d3-b2`)。**駒得版**、sha256 `1a6bbf963980dce9fe9f994e837c00ccdbe15ca82c1d9331791bb983ea206e87`。相手は本番の `playOpponentMove`(movetime 1000ms)。B・B2 は乱数を使わないので seed は記録のためだけ |
| 評価(replay) | `SHOGI_ENGINE_PATH=<共有ツリー>/apps/server/engine/nnue/YaneuraOu-by-gcc npx tsx scripts/playtest/replay.ts <game-NN.kifu.json> --nodes 4000000 --threads 1 --out <この記録>`(1 局ずつ)。**NNUE 版**、実行ファイル sha256 `53999a5abdf6e4a29872fa5e0416aa9b592560ed2a464ef50f8f75fd74674351`、`eval/nn.bin`(水匠 5)sha256 `768068f0d534a0603a5d38bcd143de6bbca820d5f1c95a14d40863e5b7892d76`、`eval/eval_options.txt` = `FV_SCALE 24` |
| 期間(2026-09-15 JST) | explore: B 04:01〜04:24(1,358 秒)・B′ 04:24〜04:45(1,288 秒) / replay: 04:46〜06:59(20 局) |
| load average(1 分) | explore 中 4.9〜13.9、replay 中 3.6〜4.3(1 局ごとの値は計画書 §9)。**所要は根拠にしない** |
| 並行していたもの | **エンジンを使ったのはこの担当だけ**: explore の前後・replay の前後に機械全体の YaneuraOu 系のプロセスを数え、始める前・終わった後とも 0 本。**エンジン以外の作業は並行していた**(explore 中の load が高い)。どのセッションが何をしていたかは記録していない |
| エンジンの最大 RSS | explore 1,498,288 KB / replay 1,454,416 KB(5 秒おきの標本) |
| 失敗 | explore 20 局・replay 20 局とも exit 0。replay の出力に Error・UsiEngineTimeoutError の行を持つ局は 0 |
| 棋譜 JSON | `scripts/playtest/out/d3-b`・`d3-b2` の `game-NN.kifu.json`(moves・tiers)。**`kifu/` への登録は人間の判断**なので、ここには置かない |

**読み方**(計画書 `docs/STEP_D3_PLAN_2026-09-14.md` §1・§5): これは校正の記録であり、20 局の件数を人の癖として読まない。B と B′ の差は局どうしの揺れと分けられない(L-7)。死因①の規則と閾値は draft のまま。
