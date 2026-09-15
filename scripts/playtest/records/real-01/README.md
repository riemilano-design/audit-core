# records/real-01 ― 実棋譜 1 人目の、本人が先手の 6 局を NNUE 版で評価した記録(STEP REAL-01)

**人間の実棋譜を評価した記録である**(リポジトリに置くことは、司令塔を通して伝えられた人間の承認による。2026-09-15)。本人は「1 人目」と書き、**相手の名前・元のファイル名・元の棋譜のパスはこの記録に書かない**。元の KIF は置かない。**この README が正本である。**

| 項目 | 値 |
|---|---|
| ファイル | `kifu-02.jsonl`・`kifu-03.jsonl`・`kifu-05.jsonl`・`kifu-06.jsonl`・`kifu-08.jsonl`・`kifu-10.jsonl`(NNUE 版の replay の記録)。`SHA256SUMS` に 6 本の sha256 |
| 固定棋譜 | `kifu/kifu-NN.fixed.json`(欄は `id`・`source`・`ending`・`moves`)。手順は STEP D0-KIFU の道具で作られた版のまま。**STEP D0-KIFU3(`9d838ad`)の `kifu-import-check.ts --fixed` で元の棋譜から作り直し、棋譜に書かれた終局の種類と手数 `ending` を足した**(2026-09-15。`ending` を除くと作り直す前のファイルとバイト一致。形は `scripts/playtest/README.md`)。**記録の JSONL は作り直す前の固定棋譜から回したもので、評価はし直していない**(再生は `ending` を読まない)。`kifu/SHA256SUMS` に 6 本の sha256(作り直した後の値)。**`SHA256SUMS`(記録)とは別の一覧** |
| 対象 | 1 人目の 10 局のうち、**本人が先手の 6 局**。**6 局とも本人の勝ち**。手数 37・69・107・107・43・75(**6 局とも奇数**)。`kifu-05`・`kifu-08` は詰みで終わった局 |
| コード | HEAD `5a2dc84`(STEP D0-SIDE 段 1)の worktree。汚れ 0(`node_modules` のリンクと `scripts/playtest/out/` だけ)。`scripts/playtest/replay.ts` sha256 `77ecff61…`・`scripts/playtest/lib/replayPlan.ts` sha256 `072aea1f…` |
| 評価(replay) | `SHOGI_ENGINE_PATH=<共有ツリー>/apps/server/engine/nnue/YaneuraOu-by-gcc npx tsx scripts/playtest/replay.ts <固定棋譜 JSON> --nodes 4000000 --threads 1 --out <この記録>`。**NNUE 版**、実行ファイル sha256 `53999a5abdf6e4a29872fa5e0416aa9b592560ed2a464ef50f8f75fd74674351`、`eval/nn.bin`(水匠 5)sha256 `768068f0d534a0603a5d38bcd143de6bbca820d5f1c95a14d40863e5b7892d76`、`eval/eval_options.txt` = `FV_SCALE 24`(records/d0-nnue・d3-nnue・d3b-nnue-n2000 と同じ条件) |
| R-8(奇数手数) | 6 局とも**最後の先手の手(本人の手)を落として再生した**。meta に `trailingMoveTruncated: true` と `truncatedTrailingMove`(落とした手の USI)。**6 局とも、落とした手が固定棋譜の最後の手と一致し、error 行 0、ready 行 19・35・54・54・22・38((n−1)/2 + 1)であることを確かめた**。`kifu-05`・`kifu-08` で落としたのは本人が詰ませた手で、Failure Event の行では「窓が足りない」側に見えうる(STEP D0-SIDE 計画 3.1 の限界) |
| 期間(2026-09-15 JST) | replay: 11:28:30〜12:26:04(壁時計 3,453.6 秒、局ごとの所要の和 8,993.0 秒) |
| 並行 | 宣言は「本数 3」。**最初の 1 局(`kifu-02`)を単独で回して R-8 を確かめてから、残り 5 局を 3 本並行**。始める前・終わった後に機械全体の YaneuraOu 系のプロセスを数え、どちらも 0 本。同時に見えたエンジンは最大 3 本 |
| load average(1 分) | 2.94〜5.30(局の終わりの値)。**所要は根拠にしない** |
| エンジンの最大 RSS | 1,455,936 KB(5 秒おきの標本、1 本あたり) |
| 失敗 | 6 局とも exit 0。出力に Error・UsiEngineTimeoutError の行を持つ局は 0 |
| 記録に入っているパス | meta の `enginePath` だけ(既存の記録と同じ)。**固定棋譜のパスや `source` は meta に書かれない**(`replay.ts` `5a2dc84` の meta の欄で確かめた) |
| 診断 | 同じ worktree の `diagnose.ts`(Failure Event JSON v0.2)を 6 本まとめて 1 群、`--events` 付き。結果は計画書 `docs/STEP_REAL-01_PLAN_2026-09-15.md` |

## `kifuId` の組

`kifuId` は固定棋譜の `id` をそのまま使う。

| この記録 | `kifuId` | 固定棋譜 |
|---|---|---|
| `kifu-02.jsonl` | `kifu-02` | `kifu/kifu-02.fixed.json` |
| `kifu-03.jsonl` | `kifu-03` | `kifu/kifu-03.fixed.json` |
| `kifu-05.jsonl` | `kifu-05` | `kifu/kifu-05.fixed.json` |
| `kifu-06.jsonl` | `kifu-06` | `kifu/kifu-06.fixed.json` |
| `kifu-08.jsonl` | `kifu-08` | `kifu/kifu-08.fixed.json` |
| `kifu-10.jsonl` | `kifu-10` | `kifu/kifu-10.fixed.json` |

**読み方**: 1 人・6 局・6 局とも本人の勝ちの記録であり、件数を人の癖として一般化しない。死因①の規則と閾値は draft のまま。評価は 1 回の探索の値で、同じ局面でも別の探索では揺れる(P-33)。
