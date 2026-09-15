# records/real-03 ― 本人が後手の 15 局(2 人目 11 局・1 人目 4 局)を、先手の形に回して NNUE 版で評価した記録(STEP REAL-03)

**人間の実棋譜を評価した記録である**(リポジトリに置くことは、司令塔を通して伝えられた人間の承認による。2026-09-15)。本人は「1 人目」「2 人目」と書き、**相手の名前・元のファイル名・元の棋譜のパスはこの記録に書かない**。元の KIF は置かない。**この README が正本である。**

**盲検(司令塔の決定、2026-09-15)**: g3(kifu-01/04/07/09)の Event の中身は D3-COND の定義承認まで、C(件数)と f2(監査)以外は開かない。

| 項目 | 値 |
|---|---|
| ファイル | JSONL 15 本(NNUE 版の replay の記録)。`SHA256SUMS` に 15 本の sha256。**群は置き場を分けず、この一覧と下の表で示す** |
| 固定棋譜 | `kifu/<id>.fixed.json`(欄は `id`・`source`・`mirrored`・`originalUserSide`・`plyOffset`・`startSfen`・`ending`・`moves`・`originalMoves`。STEP D0-SIDE 段 2(`e3b0a17`)の道具で**本人が後手の棋譜を 180 度回し、元の相手の 1 手目を開始局面に畳んだ版**)。**STEP D0-KIFU3(`9d838ad`)の `kifu-import-check.ts --fixed --as gote` で元の棋譜から作り直し、棋譜に書かれた終局の種類と手数 `ending` を足した**(2026-09-15。`ending` を除くと作り直す前のファイルとバイト一致。`ply` は**回す前の手順**の手数 + 1。形は `scripts/playtest/README.md`)。**記録の JSONL は作り直す前の固定棋譜から回したもので、評価はし直していない**(再生は `ending` を読まない)。`kifu/SHA256SUMS` に 15 本の sha256(並びは下の表の群の順のまま、作り直した後の値)。**`SHA256SUMS`(記録)とは別の一覧** |
| 対象と群 | **G1 2 人目・負け 7 局**(`kifu2-02`・`03`・`05`・`06`・`07`・`08`・`10`、畳んだ後の手数 64・52・86・72・94・98・150、**すべて偶数**)/ **G2 2 人目・勝ち 4 局**(`kifu2-12`・`13`・`14`・`19`、67・57・43・93、**すべて奇数**)/ **G3 1 人目・勝ち 4 局**(`kifu-01`・`04`・`07`・`09`、51・49・89・25、**すべて奇数**)。**勝ち負けは固定棋譜に入っておらず、棋譜を用意した側の一覧による**。これで 2 人目は 20 局すべて(先手 9 局 = records/real-02)、1 人目は 10 局すべて(先手 6 局 = records/real-01) |
| コード | HEAD `e3b0a17`(STEP D0-SIDE 段 2)の worktree。汚れ 0(`node_modules` のリンクと `scripts/playtest/out/` だけ)。出力は `scripts/playtest/out/real-03/<群>/<id>.jsonl`(群 = `g1-p2-lose`・`g2-p2-win`・`g3-p1-win`) |
| 評価(replay) | `SHOGI_ENGINE_PATH=<共有ツリー>/apps/server/engine/nnue/YaneuraOu-by-gcc npx tsx scripts/playtest/replay.ts <固定棋譜 JSON> --nodes 4000000 --threads 1 --out <この記録>`。**NNUE 版**、実行ファイル sha256 `53999a5abdf6e4a29872fa5e0416aa9b592560ed2a464ef50f8f75fd74674351`、`eval/nn.bin`(水匠 5)sha256 `768068f0d534a0603a5d38bcd143de6bbca820d5f1c95a14d40863e5b7892d76`、`eval/eval_options.txt` = `FV_SCALE 24`(records/real-01・real-02 と同じ条件) |
| 回した記録の meta | 15 本とも `mirrored: true`・`originalUserSide: "gote"`・`plyOffset: 1`・`startSfen`(固定棋譜と一致、先手番・手数 2)・`sideAlignmentChecked: true`。**最初の ready 行(ply 0)の局面は `startSfen`**(= 元の相手の 1 手目の後)。元の手数との対応は `plyOffset` |
| R-8(畳んだ後の手数で決まる) | **G1(偶数)は落とさない**(`trailingMoveTruncated: false`・`truncatedTrailingMove` の欄なし)。**G2・G3(奇数)は最後の先手の手(本人の手)を落とした**(`true`・落とした手が固定棋譜の最後の手と一致)。**15 局とも error 行 0、ready 行は畳んだ後の手数から出した数と一致**(33・27・44・37・48・50・76 / 34・29・22・47 / 26・25・45・13) |
| 期間(2026-09-15 JST) | 17:21:44〜20:11:42(壁時計 10,198.2 秒、局ごとの所要の和 28,373.5 秒) |
| 並行 | 宣言は「本数 3」。**最初の 1 局(G1 `kifu2-02`)を単独で回して回した記録の欄と R-8 を確かめてから、残り 14 局を 3 本並行**。始める前・終わった後に機械全体の YaneuraOu 系のプロセスを数え、どちらも 0 本。同時に見えたエンジンは最大 3 本。途中で司令塔から本数 5 への引き上げを許されたが、道具の待ち行列が外から減らせず二重に回すおそれがあったので 3 本のまま回した |
| load average(1 分) | 3.0〜7.51(局の終わりの値)。18:05 に 6〜7 だったとき、エンジンはこの記録の 3 本だけで、ほかに音声のシステム処理と音声機器の常駐ソフトが CPU を使っていた。**所要は根拠にしない** |
| エンジンの最大 RSS | 1,454,688 KB(5 秒おきの標本、1 本あたり) |
| 失敗 | 15 局とも exit 0。出力に Error・UsiEngineTimeoutError の行を持つ局は 0 |
| `engineReference` が null の行 | G1: `kifu2-02` ply 28・52・54・60・62 / `kifu2-05` ply 74・76・78・86 / `kifu2-08` ply 50・52・58・68 / `kifu2-10` ply 96・98・108・118・120。G2: `kifu2-19` ply 26・92。G3: 4 行(1 局)。**どれも先手が王手をかけられている局面**で、replay は終局と先手の王手中では測らない。`diagnose.ts` が「測らない(王手中)」と数えた行と、**15 局とも局ごとの数が一致** |
| 記録に入っているパス | meta の `enginePath` だけ(既存の記録と同じ)。**固定棋譜のパスや `source` は meta に書かれない** |
| 診断 | 群ごとは同じ worktree(`e3b0a17`)の `diagnose.ts`(Failure Event JSON v0.2)を `--events` 付きで。2 人目 20 局合計(records/real-02 + G1 + G2)は HEAD `58b540a`(v0.4 + STEP D1b)で `--events`・`--events-rise`・`--events-maxdrop` 付き。**1 人目 10 局合計の出力はコミットしない**。結果は計画書 `docs/STEP_REAL-03_PLAN_2026-09-15.md` |

## `kifuId` の組

`kifuId` は固定棋譜の `id` をそのまま使う。

| この記録 | `kifuId` | 固定棋譜 | 群 | 勝ち負け |
|---|---|---|---|---|
| `kifu2-02.jsonl` | `kifu2-02` | `kifu/kifu2-02.fixed.json` | G1 | 負け |
| `kifu2-03.jsonl` | `kifu2-03` | `kifu/kifu2-03.fixed.json` | G1 | 負け |
| `kifu2-05.jsonl` | `kifu2-05` | `kifu/kifu2-05.fixed.json` | G1 | 負け |
| `kifu2-06.jsonl` | `kifu2-06` | `kifu/kifu2-06.fixed.json` | G1 | 負け |
| `kifu2-07.jsonl` | `kifu2-07` | `kifu/kifu2-07.fixed.json` | G1 | 負け |
| `kifu2-08.jsonl` | `kifu2-08` | `kifu/kifu2-08.fixed.json` | G1 | 負け |
| `kifu2-10.jsonl` | `kifu2-10` | `kifu/kifu2-10.fixed.json` | G1 | 負け |
| `kifu2-12.jsonl` | `kifu2-12` | `kifu/kifu2-12.fixed.json` | G2 | 勝ち |
| `kifu2-13.jsonl` | `kifu2-13` | `kifu/kifu2-13.fixed.json` | G2 | 勝ち |
| `kifu2-14.jsonl` | `kifu2-14` | `kifu/kifu2-14.fixed.json` | G2 | 勝ち |
| `kifu2-19.jsonl` | `kifu2-19` | `kifu/kifu2-19.fixed.json` | G2 | 勝ち |
| `kifu-01.jsonl` | `kifu-01` | `kifu/kifu-01.fixed.json` | G3 | 勝ち |
| `kifu-04.jsonl` | `kifu-04` | `kifu/kifu-04.fixed.json` | G3 | 勝ち |
| `kifu-07.jsonl` | `kifu-07` | `kifu/kifu-07.fixed.json` | G3 | 勝ち |
| `kifu-09.jsonl` | `kifu-09` | `kifu/kifu-09.fixed.json` | G3 | 勝ち |

**読み方**: 2 人・15 局の記録であり、件数を人の癖として一般化しない。回した記録の評価は先手 = 本人から見た値。**元の相手の 1 手目の直前の局面は評価していない**。`kifu2-10`(負け)は最後の ready 行の評価が本人側に大きく良い(records/real-02 の `kifu2-04` と同じく、**負けの形は手順の記録からは見えない**。終局の種類は固定棋譜の `ending` にある)。死因①の規則と閾値は draft のまま。評価は 1 回の探索の値で、同じ局面でも別の探索では揺れる(P-33)。
