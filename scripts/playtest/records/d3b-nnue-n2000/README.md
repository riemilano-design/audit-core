# records/d3b-nnue-n2000 ― 相手を `go nodes 2000` に弱めて、縛った初心者の決め方(B・B′)で指した 20 局を NNUE 版で付け直した記録(STEP D3b)

**対局 = 駒得版(相手だけ `--opponent-nodes 2000`)/ 評価 = NNUE 版。** 記録の `meta.enginePath` は評価(再生)に使ったエンジンのパスで、対局のエンジンと相手のノード数はここに残らない(P-43)。**この README が正本である。**

| 項目 | 値 |
|---|---|
| ファイル | `b-game-01.jsonl`〜`b-game-10.jsonl`(B)・`b2-game-01.jsonl`〜`b2-game-10.jsonl`(B′。コードでは `B2`)。`SHA256SUMS` に 20 本の sha256 |
| コード | HEAD `e005dbb`(STEP D3b の道具)の worktree。汚れ 0(`node_modules` のリンクと `scripts/playtest/out/` だけ) |
| 対局(explore) | `SHOGI_ENGINE_PATH=<共有ツリー>/apps/server/engine/YaneuraOu-by-gcc npx tsx scripts/playtest/explore.ts --profile B --games 10 --seed 1 --plies 200 --opponent-nodes 2000 --out-dir scripts/playtest/out/d3b-b`(B′ は `--profile B2`・`--out-dir scripts/playtest/out/d3b-b2`)。**駒得版**、sha256 `1a6bbf963980dce9fe9f994e837c00ccdbe15ca82c1d9331791bb983ea206e87`。**相手は `playOpponentMove` に渡すハンドルだけを包み、`go nodes 2000` で指す(Threads はエンジンの既定 4 のまま ― 計画 Q-3)。同じ局面・同じ N でも相手の手は 1 つに決まらない(L-D3b-2)。** 先手の E 読み・候補手・③・`engineReference` の探索は D3 と同じ。B・B2 は乱数を使わないので seed は記録のためだけ |
| 相手のノード数の確かめ | explore の JSONL(`out/` のまま)の meta 行の最上位の `opponentNodes`(explore.ts の `meta.extra` を `buildMetaLine` が最上位へ展開する ― `lib/recorder.ts:364`)が 20 局とも 2000。**相手の go に nodes を付けて渡した回数 K は JSONL に残らず、explore の出力に出る**(L-D3b-6)。20 局とも K ≥ 1 で、K は各局の相手の手数(手数 ÷ 2)と一致した(B 12〜28・B′ 17〜29) |
| 評価(replay) | `SHOGI_ENGINE_PATH=<共有ツリー>/apps/server/engine/nnue/YaneuraOu-by-gcc npx tsx scripts/playtest/replay.ts <game-NN.kifu.json> --nodes 4000000 --threads 1 --out <この記録>`。**3 本並行**(別の局を別プロセスで。AGENT_PROTOCOL 10 番の注記)。**NNUE 版**、実行ファイル sha256 `53999a5abdf6e4a29872fa5e0416aa9b592560ed2a464ef50f8f75fd74674351`、`eval/nn.bin`(水匠 5)sha256 `768068f0d534a0603a5d38bcd143de6bbca820d5f1c95a14d40863e5b7892d76`、`eval/eval_options.txt` = `FV_SCALE 24` |
| 期間(2026-09-15 JST) | explore: B 08:41:33〜09:02:01(1,228 秒)・B′ 09:02:01〜09:21:40(1,179 秒) / replay: 09:22:24〜10:27:34(壁時計 3,911 秒、局ごとの所要の和 11,515 秒) |
| load average(1 分) | explore 中 最大 16.47(B の間。別セッションの vitest・変異と重なった)〜B′ の終わり 4.57、replay 中 4.29〜6.47。**所要は根拠にしない**(L-D3b-5) |
| 並行していたもの | **エンジンを使ったのはこの担当だけ**(B の D-COST の解放を待ってから始めた)。始める前・終わった後に機械全体の YaneuraOu 系のプロセスを数え、explore・replay とも始める前 0 本・終わった後 0 本。同時に見えたエンジンの最大本数は explore 1 本・replay 3 本(宣言どおり)。**エンジン以外の作業は並行していた**(explore の間は B の vitest・変異)。replay の前には B に知らせ、B の vitest・変異が終わった(09:07:49)返事を受けてから始めた。replay の間、B は vitest・tsx・変異を回さなかった(B の申告) |
| エンジンの最大 RSS | explore 1,442,608 KB / replay 1,453,616 KB(5 秒おきの標本、1 本あたり) |
| 失敗 | explore 20 局・replay 20 局とも exit 0。replay の出力に Error・UsiEngineTimeoutError の行を持つ局は 0 |
| 診断(diagnose) | 同じ worktree(HEAD `e005dbb`)の `diagnose.ts` を群ごとに `--events` 付きで(Failure Event の `schemaVersion` は `"0.1"`。`a7fe6e9` の v0.2 ではない)。結果は計画書 §11 |
| 棋譜 JSON | `scripts/playtest/out/d3b-b`・`d3b-b2` の `game-NN.kifu.json`(moves・tiers)。**`kifu/` への登録は人間の判断**なので、ここには置かない |

## `kifuId` の組(P-46)

`kifuId` は explore の実行ごとに一意だが、**同じ `kifuId` が駒得版の explore の JSONL(`out/d3b-*/game-NN.jsonl`)と、この記録(NNUE 版の replay の JSONL)の両方に出る。** 評価関数をまたいで一意ではない(P-46)ので、どちらの値かはファイルで区別する。

| この記録 | `kifuId` | explore の JSONL |
|---|---|---|
| `b-game-01.jsonl` | `explore-2026-09-14T23:41:36.952Z-01-B` | `scripts/playtest/out/d3b-b/game-01.jsonl`(記録の外) |
| `b-game-02.jsonl` | `explore-2026-09-14T23:41:36.952Z-02-B` | `scripts/playtest/out/d3b-b/game-02.jsonl`(記録の外) |
| `b-game-03.jsonl` | `explore-2026-09-14T23:41:36.952Z-03-B` | `scripts/playtest/out/d3b-b/game-03.jsonl`(記録の外) |
| `b-game-04.jsonl` | `explore-2026-09-14T23:41:36.952Z-04-B` | `scripts/playtest/out/d3b-b/game-04.jsonl`(記録の外) |
| `b-game-05.jsonl` | `explore-2026-09-14T23:41:36.952Z-05-B` | `scripts/playtest/out/d3b-b/game-05.jsonl`(記録の外) |
| `b-game-06.jsonl` | `explore-2026-09-14T23:41:36.952Z-06-B` | `scripts/playtest/out/d3b-b/game-06.jsonl`(記録の外) |
| `b-game-07.jsonl` | `explore-2026-09-14T23:41:36.952Z-07-B` | `scripts/playtest/out/d3b-b/game-07.jsonl`(記録の外) |
| `b-game-08.jsonl` | `explore-2026-09-14T23:41:36.952Z-08-B` | `scripts/playtest/out/d3b-b/game-08.jsonl`(記録の外) |
| `b-game-09.jsonl` | `explore-2026-09-14T23:41:36.952Z-09-B` | `scripts/playtest/out/d3b-b/game-09.jsonl`(記録の外) |
| `b-game-10.jsonl` | `explore-2026-09-14T23:41:36.952Z-10-B` | `scripts/playtest/out/d3b-b/game-10.jsonl`(記録の外) |
| `b2-game-01.jsonl` | `explore-2026-09-15T00:02:02.301Z-01-B2` | `scripts/playtest/out/d3b-b2/game-01.jsonl`(記録の外) |
| `b2-game-02.jsonl` | `explore-2026-09-15T00:02:02.301Z-02-B2` | `scripts/playtest/out/d3b-b2/game-02.jsonl`(記録の外) |
| `b2-game-03.jsonl` | `explore-2026-09-15T00:02:02.301Z-03-B2` | `scripts/playtest/out/d3b-b2/game-03.jsonl`(記録の外) |
| `b2-game-04.jsonl` | `explore-2026-09-15T00:02:02.301Z-04-B2` | `scripts/playtest/out/d3b-b2/game-04.jsonl`(記録の外) |
| `b2-game-05.jsonl` | `explore-2026-09-15T00:02:02.301Z-05-B2` | `scripts/playtest/out/d3b-b2/game-05.jsonl`(記録の外) |
| `b2-game-06.jsonl` | `explore-2026-09-15T00:02:02.301Z-06-B2` | `scripts/playtest/out/d3b-b2/game-06.jsonl`(記録の外) |
| `b2-game-07.jsonl` | `explore-2026-09-15T00:02:02.301Z-07-B2` | `scripts/playtest/out/d3b-b2/game-07.jsonl`(記録の外) |
| `b2-game-08.jsonl` | `explore-2026-09-15T00:02:02.301Z-08-B2` | `scripts/playtest/out/d3b-b2/game-08.jsonl`(記録の外) |
| `b2-game-09.jsonl` | `explore-2026-09-15T00:02:02.301Z-09-B2` | `scripts/playtest/out/d3b-b2/game-09.jsonl`(記録の外) |
| `b2-game-10.jsonl` | `explore-2026-09-15T00:02:02.301Z-10-B2` | `scripts/playtest/out/d3b-b2/game-10.jsonl`(記録の外) |

**読み方**(計画書 `docs/STEP_D3b_PLAN_2026-09-15.md` §1・§9): これは校正の記録であり、20 局の件数を人の癖として読まない。相手を弱くした記録は、アプリの利用者が指す相手の記録ではない(L-D3b-4)。B と B′ の差は局どうしの揺れと分けられない(L-7)。死因①の規則と閾値は draft のまま。

**付録**: 探索の最初の 1 局の検問の証拠(20 局それぞれの meta 行・終了行・tiers の内訳・「相手の go(nodes 付き)=K」の行)は [`explore-evidence.md`](explore-evidence.md)(`SHA256SUMS` には入れない)。
