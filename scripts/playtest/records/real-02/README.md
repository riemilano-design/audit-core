# records/real-02 ― 実棋譜 2 人目の、本人が先手の 9 局を NNUE 版で評価した記録(STEP REAL-02)

**人間の実棋譜を評価した記録である**(リポジトリに置くことは、司令塔を通して伝えられた人間の承認による。2026-09-15)。本人は「2 人目」と書き、**相手の名前・元のファイル名・元の棋譜のパスはこの記録に書かない**。元の KIF は置かない。**この README が正本である。**

| 項目 | 値 |
|---|---|
| ファイル | `kifu2-01.jsonl`・`kifu2-04.jsonl`・`kifu2-09.jsonl`・`kifu2-11.jsonl`・`kifu2-15.jsonl`・`kifu2-16.jsonl`・`kifu2-17.jsonl`・`kifu2-18.jsonl`・`kifu2-20.jsonl`(NNUE 版の replay の記録)。`SHA256SUMS` に 9 本の sha256(名前順) |
| 固定棋譜 | `kifu/kifu2-NN.fixed.json`(欄は `id`・`source`・`ending`・`moves`)。手順は STEP D0-KIFU の道具で作られた版のまま。**STEP D0-KIFU3(`9d838ad`)の `kifu-import-check.ts --fixed` で元の棋譜から作り直し、棋譜に書かれた終局の種類と手数 `ending` を足した**(2026-09-15。`ending` を除くと作り直す前のファイルとバイト一致。形は `scripts/playtest/README.md`)。**記録の JSONL は作り直す前の固定棋譜から回したもので、評価はし直していない**(再生は `ending` を読まない)。`kifu/SHA256SUMS` に 9 本の sha256(名前順、作り直した後の値)。**`SHA256SUMS`(記録)とは別の一覧**。`kifu2-15`・`kifu2-20` の 2 本は **STEP D0-KIFU2(`b87b2f2`)で 1 文字の成り駒を揃えてから読めた版**(揃えた手は `kifu2-15` が 7 手、`kifu2-20` が 1 手) |
| 対象 | 2 人目の 20 局のうち、**本人が先手の 9 局すべて**。**負け 3 局**(`kifu2-01` 66 手・`kifu2-04` 126 手・`kifu2-09` 50 手、**3 局とも偶数**)と**勝ち 6 局**(`kifu2-11` 41 手・`kifu2-15` 127 手・`kifu2-16` 15 手・`kifu2-17` 83 手・`kifu2-18` 39 手・`kifu2-20` 55 手、**6 局とも奇数**)。**勝ち負けは固定棋譜に入っておらず、棋譜を用意した側の一覧による**。本人が後手の局は含まない(STEP REAL-03) |
| 置いた順 | 先に 7 局(`kifu2-15`・`kifu2-20` 以外)を回して置き、STEP D0-KIFU2 の後に読めた 2 局を同じ条件で回して足した。**足したとき、先の 7 局の JSONL と固定棋譜のバイトは変えていない**(足す前後の sha256 で確かめた) |
| コード | HEAD `5a2dc84`(STEP D0-SIDE 段 1)の worktree(records/real-01 と同じ worktree。出力は `scripts/playtest/out/real-02/` に分けた)。汚れ 0(`node_modules` のリンクと `scripts/playtest/out/` だけ)。`scripts/playtest/replay.ts` sha256 `77ecff61…`・`scripts/playtest/lib/replayPlan.ts` sha256 `072aea1f…`。**`5a2dc84` と D0-KIFU2 の間で `replay.ts`・`lib/replayPlan.ts`・`diagnose.ts`・診断の lib は変わっていない**(D0-KIFU2 は `lib/kifuImport.ts` とその試験だけ) |
| 評価(replay) | `SHOGI_ENGINE_PATH=<共有ツリー>/apps/server/engine/nnue/YaneuraOu-by-gcc npx tsx scripts/playtest/replay.ts <固定棋譜 JSON> --nodes 4000000 --threads 1 --out <この記録>`。**NNUE 版**、実行ファイル sha256 `53999a5abdf6e4a29872fa5e0416aa9b592560ed2a464ef50f8f75fd74674351`、`eval/nn.bin`(水匠 5)sha256 `768068f0d534a0603a5d38bcd143de6bbca820d5f1c95a14d40863e5b7892d76`、`eval/eval_options.txt` = `FV_SCALE 24`(records/real-01 と同じ条件) |
| R-8 | **勝ち 6 局(奇数手数)は最後の先手の手(本人の手)を落として再生した**。meta に `trailingMoveTruncated: true` と `truncatedTrailingMove`(落とした手の USI)。落とした手が固定棋譜の最後の手と一致。**負け 3 局(偶数手数)は落とさない**。meta に `trailingMoveTruncated: false`、`truncatedTrailingMove` の欄は無い。**9 局とも error 行 0、ready 行は 34・64・26・21・64・8・42・20・28(偶数 n/2 + 1・奇数 (n−1)/2 + 1)であることを確かめた**。「落とさない」側を実物で確かめたのはこの記録が初めて(records/real-01 は 6 局とも奇数) |
| 期間(2026-09-15 JST) | 7 局: 12:33:06〜14:12:18(壁時計 5,952.2 秒、局ごとの所要の和 12,171.3 秒)。追加 2 局: 14:18:37〜15:07:44(壁時計 2,947.1 秒、所要の和 2,941.0 秒) |
| 並行 | 7 局: 宣言は「本数 3」。**最初の 1 局(負け局 `kifu2-01`、偶数手数)を単独で回して R-8 の「落とさない」側を確かめてから、残り 6 局を 3 本並行**。同時に見えたエンジンは最大 3 本。追加 2 局: 宣言は「本数 2」。`kifu2-15` を単独で回して確かめてから `kifu2-20` を回した(ログの「並行本数 3」はスクリプトの定数で、残りが 1 局なので**同時に見えたエンジンは最大 1 本**)。どちらも始める前・終わった後に機械全体の YaneuraOu 系のプロセスを数え、0 本 |
| load average(1 分) | 7 局: 3.04〜10.45(局の終わりの値)。13:25〜13:31 の 8.23〜10.45 は、**同じ機械で別セッションの vitest が走っていた**時間に当たる(エンジンはこの記録の 3 本だけ)。追加 2 局: 2.75〜3.85。**所要は根拠にしない** |
| エンジンの最大 RSS | 7 局: 1,454,960 KB・追加 2 局: 1,455,136 KB(5 秒おきの標本、1 本あたり) |
| 失敗 | 9 局とも exit 0。出力に Error・UsiEngineTimeoutError の行を持つ局は 0 |
| `engineReference` が null の行 | `kifu2-04` ply 48・`kifu2-09` ply 32・`kifu2-15` ply 90・94・98・100・106・110・116・124 の 10 行。**どれも先手が王手をかけられている局面**で、replay は終局と先手の王手中では測らない。`diagnose.ts` が「測らない(王手中)」と数えた行と、局・数が一致する(`kifu2-04` 1・`kifu2-09` 1・`kifu2-15` 8)。ほかに `kifu2-17` ply 82 は `baseline.mate` 1(値ではなく詰みの読み) |
| 記録に入っているパス | meta の `enginePath` だけ(既存の記録と同じ)。**固定棋譜のパスや `source` は meta に書かれない** |
| 診断 | 同じ worktree の `diagnose.ts`(Failure Event JSON v0.2)を、**9 局 1 群と、負け 3 局・勝ち 6 局の 2 群**に、`--events` 付きで(先に 7 局 1 群・負け 3・勝ち 4 と、追加 2 局 1 群にも掛けた)。結果は計画書 `docs/STEP_REAL-02_PLAN_2026-09-15.md` |

## `kifuId` の組

`kifuId` は固定棋譜の `id` をそのまま使う。

| この記録 | `kifuId` | 固定棋譜 | 勝ち負け | 置いた順 |
|---|---|---|---|---|
| `kifu2-01.jsonl` | `kifu2-01` | `kifu/kifu2-01.fixed.json` | 負け | 7 局 |
| `kifu2-04.jsonl` | `kifu2-04` | `kifu/kifu2-04.fixed.json` | 負け | 7 局 |
| `kifu2-09.jsonl` | `kifu2-09` | `kifu/kifu2-09.fixed.json` | 負け | 7 局 |
| `kifu2-11.jsonl` | `kifu2-11` | `kifu/kifu2-11.fixed.json` | 勝ち | 7 局 |
| `kifu2-15.jsonl` | `kifu2-15` | `kifu/kifu2-15.fixed.json` | 勝ち | 追加 2 局 |
| `kifu2-16.jsonl` | `kifu2-16` | `kifu/kifu2-16.fixed.json` | 勝ち | 7 局 |
| `kifu2-17.jsonl` | `kifu2-17` | `kifu/kifu2-17.fixed.json` | 勝ち | 7 局 |
| `kifu2-18.jsonl` | `kifu2-18` | `kifu/kifu2-18.fixed.json` | 勝ち | 7 局 |
| `kifu2-20.jsonl` | `kifu2-20` | `kifu/kifu2-20.fixed.json` | 勝ち | 追加 2 局 |

**読み方**: 1 人・9 局の記録であり、件数を人の癖として一般化しない。本人が先手の局だけで、後手の局は含まない。`kifu2-04`(負け)は最後の ready 行の評価が本人側に大きく良い(+2692)。**負けの形は手順の記録からは見えない**(投了・時間切れなどの終局の種類は、記録の JSONL には無く、固定棋譜の `ending` にある。STEP D0-KIFU3 で足した)。死因①の規則と閾値は draft のまま。評価は 1 回の探索の値で、同じ局面でも別の探索では揺れる(P-33)。
