# records/d-cost ― 固定棋譜 7 局を軽い走査(100,000・400,000 ノード)と深い走査の対照(4,000,000 ノード)で再生した記録(STEP D-COST)

`replay.ts --nodes N --reference-nodes N --threads 1` で固定棋譜 7 局(`scripts/playtest/kifu/`)を再生した JSONL。深い走査 `records/d0-nnue`(D4M)と組ごとに比べる材料(計画書 `docs/STEP_D-COST_PLAN_2026-09-15.md` §2・§4、比べは `scripts/playtest/scan-compare.ts`)。**記録は観測であり、何も拘束しない。**

| 項目 | 値 |
|---|---|
| フォルダ | `l100k/`(N = 100,000)・`l400k/`(N = 400,000)・`c4m/`(N = 4,000,000。D4M と同じ条件をもう 1 回 = 揺れの床)。各 7 本、ファイル名は `records/d0-nnue` と同じ。各フォルダに `SHA256SUMS` |
| 回した順 | L100k → L400k → C4M → L400k → L100k(計画 §4 の 4)。**ここに置いたのは 1 回目だけ**。2 回目(L400k・L100k)は所要を見るためだけに回し、記録は置かない(計画 §4 の 4) |
| コード | HEAD `05d3c4e` の worktree。**meta の `dirty` は 35 本とも `false`**(`node_modules` のリンクは数えない ― `lib/gitState.ts`) |
| 評価(replay) | `SHOGI_ENGINE_PATH=<共有ツリー>/apps/server/engine/nnue/YaneuraOu-by-gcc npx tsx scripts/playtest/replay.ts <kifu.json> --out <記録> --nodes N --reference-nodes N --threads 1`(1 局ずつ、`/usr/bin/time -l` で包む)。**NNUE 版**、実行ファイル sha256 `53999a5abdf6e4a29872fa5e0416aa9b592560ed2a464ef50f8f75fd74674351`、`eval/nn.bin`(水匠 5)sha256 `768068f0d534a0603a5d38bcd143de6bbca820d5f1c95a14d40863e5b7892d76`、`eval/eval_options.txt` = `FV_SCALE 24`(始める前に確かめた)。**`meta.enginePath` は `records/d0-nnue` と同じ絶対パス**(`scan-compare.ts` の G-3 がパスの一致を見るため、共有ツリーのエンジンを指した)。**meta に評価関数は残らない(P-43)。この README が正本** |
| 期間(2026-09-15 JST) | L100k 1 回目 07:21:11〜07:23:35 / L400k 1 回目 〜07:30:52 / C4M 〜08:33:03 / L400k 2 回目 〜08:38:42 / L100k 2 回目 〜08:40:20 |
| load average(1 分) | 1 局の直前・直後で 3.35〜7.41。**35 局すべて 2.0 を超えた = 所要は全局「参考」で、根拠にしない**(計画 Q-3)。load が 2.0 を超えた局は、直前・直後の CPU の上位プロセスを残した: どの局も Google Chrome の renderer(約 100%)・coreaudiod(約 80%)・ApogeeTalkbackHelper(約 30%)。**L400k 1 回目の最初の局の後に、別セッションの vitest(`diagnose.test.ts`、約 80%)が 1 回見えた** |
| 並行していたもの | **エンジンを使ったのはこの担当だけ**(宣言のうえ、各局の前後で機械全体の YaneuraOu 系プロセスを数え、始める前 0 本・各局の後 0 本・終わった後 0 本)。**この版の ListAgents には busy / idle の列が無い**ので、代わりに上の CPU の上位プロセスを残した |
| 機械 | Apple M2(8 コア: 性能 4・効率 4)、24 GiB、macOS 13(Darwin 22.5.0)、AC 電源、`pmset -g therm` の警告なし(始める前・終わった後) |
| 失敗 | 35 回とも exit 0。記録に `error` 行 0、標準出力・標準エラーに Error・Timeout を含む行 0。`engineReference.nodes` は各記録で全行 N |
| 最大 RSS | `/usr/bin/time -l` の値は **Node のプロセスだけ**で約 97 MB(エンジンの子プロセスは含まない) |

**読み方**: 所要と取りこぼしの数は計画書 §12(実測)。**この 7 局は Claude が初心者を演じた 20〜30 手の局で、実棋譜の代わりにならない**(計画 L-7)。所要はこの Mac のこの日の、load が高い状態の値である(L-3)。
