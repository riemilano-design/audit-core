# STEP D0-NNUE(番号は仮): NNUE 評価関数のエンジンを組み、評価値が信用できる形で出るかを確かめる(2026-09-14)

**状態**: 実測を終えた(2026-09-15 時点。**圧縮をまたいでも読めるよう、進み具合をここに書く**)。
- **エンジンは解放済み**(2026-09-15 02:28 頃に司令塔へ宣言。終わった後の私のエンジン・ドライバは 0 本を確かめてから)
- **7 局の再生は終わった**: 全部 exit=0、ready 107 行、`engineReference` null 1 行(王手の局面で測らない作り)。出力 `/private/tmp/claude-501/-Users-midoriko-Desktop-sgogi-coach/e66396dd-d562-40ec-92b2-4076c559afb2/scratchpad/wt-d0-nnue/scripts/playtest/out/d0-nnue/`(7 ファイル。**D1 の `diagnose.ts` をかけるまで worktree を残す**)。数字は 6.11
- **残り**: 司令塔への報告(ready 行数と null 行数・記録項目・この計画書の sha1)。既知事項の候補は 7.1〜7.3(番号は付けない)
- 記録すべき値は 6.6・6.7 にある(評価ファイル sha256 `768068f0…`・64,217,066 バイト、実行ファイル sha256 `53999a5a…`、clone の HEAD `c1b80eaa`、FV_SCALE 24 を `eval_options.txt` で)
**位置づけ**: Diagnostic Spike 0 の半分。**方針(2026-09-14 の人間の決定。並行セッション経由で伝わり、人間本人にチャットで確かめた)**: 主役を「対局中の⑤候補手」から「対局後の負け方診断(棋譜を横断して、破滅の分岐 → 物理イベント → 死因候補 → 個人パターン)」へ移す。同じ解析基盤の 2 つ目の出口。対局中の帯・①②③は残す。
**エンジンを使うのはこのセッションだけ**(並行セッションの割り振り)。**エンジンを使う前後に宣言する。時間を測るのは他のセッションがエンジンを使っていないことを確かめてから**(AGENT_PROTOCOL 3. の 12 番)。

---

## 1. なぜ要るか

いまの `apps/server/engine/YaneuraOu-by-gcc` は**駒得だけの評価関数**(`YANEURAOU_ENGINE_MATERIAL`。`spike/README.md` の手順で組んだ。同 README の 60 行目「指し手の強さ・評価値の意味は将棋として最善手を示すものではない(疎通確認が目的)」)。**診断は「+300 の優勢」「−400 の急落」「詰み」を根拠にするので、この数字では作れない。**

## 2. やらないこと

- **既存のバイナリを上書きしない。** NNUE 版は `apps/server/engine/nnue/` に置く(`apps/server/.gitignore` の `/engine/` で無視されることを確かめた)
- **本番の `apps/server/src` には 1 行も触らない。** 触る必要が見えたら報告だけ(`setoption name EvalDir` を送る必要があっても、コードは変えない)
- **評価関数ファイルは、候補(名前・配布元 URL・サイズ・利用条件)を示して人間の許可を得るまで落とさない**
- **どちらの評価値が「正しい」とは言わない。** 違いを数える

## 3. 手順

| # | やること | 確かめること |
|---|---|---|
| 1 | やねうら王のソースを scratchpad に `git clone --depth 1`(人間が許可済み。GPL-3.0、リポジトリ全体は約 81MB) | 取得した commit |
| 2 | NNUE 版を組む(`YANEURAOU_EDITION=YANEURAOU_ENGINE_NNUE`、`TARGET_CPU=APPLEM1`、`COMPILER=clang++`) | 組めたか、警告、所要 |
| 3 | `EvalDir` の既定と、何から見た相対かを**ソースで**確かめる | `UsiEngine` は cwd を渡さずに spawn する(`usiEngine.ts:102`)。したがって**エンジンの cwd は呼んだ Node の cwd**。「実行ファイルからの相対」か「cwd からの相対」かで置き場所が変わる |
| 4 | 評価関数ファイルの候補を調べて報告し、人間の許可を得てから落とす | 名前・配布元 URL・サイズ・利用条件 |
| 5 | worktree で `SHOGI_ENGINE_PATH` を NNUE 版に向け、固定棋譜を `replay.ts --nodes 4000000 --threads 1` で再生 | 下の 4. |

## 4. 何を測るか

1. **`usi` / `isready` が通り、`readyok` までにエラーが出ないこと。** 評価ファイルが読めないと `isready` で落ちるはず、という見立てがある(並行セッション)。**落ちなかったら、読めたことを何で確かめるかを書く**(読めていないのに黙って動く形を疑う ― 規則 11.6 の「測れなかった」と「無かった」を混ぜない)
2. **各 ready 行の `engineReference` の評価値**と、**`score mate` が出るべき局面で出ること**
   - **固定棋譜 7 局は 20 手か 30 手で途中までの記録で、終局が無い**(2026-09-14 に確かめた。JSON の欄は `id`・`source`・`moves` だけ)。**詰みはこの 7 局では確かめられない見込み**
   - そこで**校正用の詰みの局面を手で作る**(1 手詰)。**使う前に、本番のルール関数(`rules/` の王手判定と合法手)で、指したあと本当に詰みになることを確かめる**。エンジンの答えを正解にしない
3. **駒得版の既存の記録(`scripts/playtest/out/u6l`)と並べ、同じ局面で評価値の分布がどう違うか**
   - |Δ| ≥ 300 の行数、`lowerbound` / `upperbound` の標識付きの割合、評価値の中央値・最大・最小(規則 11.5: 目当ての数字の隣に性質の違う量を並べる)
   - **行の対応は (kifuId, ply) で取る。** 数が合わないときは、合わない行を数えて出す(黙って飛ばさない)
4. **探索 1 本の所要時間とメモリ**(枠の見積もりに使う。**根拠にはしない**)。**他のセッションがエンジンを使っていないことを宣言で確かめてから**測る

## 5. 予測(**測る前に書く**)

| # | 予測 | 外れたと言える条件 |
|---|---|---|
| 予-N1 | NNUE 版は Apple clang 14.0.3・GNU make 3.81 で**組める** | 組めない。**そのときは警告・エラーをそのまま報告し、コンパイラを入れ替える判断は人間に委ねる** |
| 予-N2 | 評価ファイルが無い状態で `isready` を送ると、`readyok` の前に**評価ファイルが読めない旨のエラーが出る** | 何も言わずに `readyok` が返る。**そのときは「読めていないのに動く」前提で、読めたことを別の手段で確かめる** |
| 予-N3 | 手で作った 1 手詰の局面で、NNUE 版は `score mate` を返す | `score cp` しか返らない、または `mate` の手数が合わない |
| 予-N4 | 駒得版と NNUE 版で、同じ局面の評価値は**多くの行でずれる** | ほとんどずれない(そのときは、評価ファイルが本当に読めているかを先に疑う) |

**|Δ| ≥ 300 の行数・標識付きの割合・所要時間は、予測しない**(根拠になる数字を持っていない)。**数えて出す。**

---

## 6. 実測

(ここから下に、測った順に足す)

### 6.1 ソースの取得(2026-09-14。**人間がチャットで許可した**)

- `git clone --depth 1 https://github.com/yaneurao/YaneuraOu.git`(scratchpad。リポジトリの外)。**所要 1 秒、4.9MB**
- 取得した commit: **`c1b80eaa09fe13d5f12b1599d1ae4d53c224de30`**(2026-09-14 18:12 +0900「progress.binの読み込みに失敗したときにnn.binのFileNotFoundが出ていたの修正。」)。**評価ファイルの読み込みの周りが、取得した当日に直されている。** 6.3 で EvalDir と読み込み失敗の振る舞いを確かめるときは、この commit のソースで見る

### 6.2 比べる相手(駒得版の記録 `scripts/playtest/out/u6l`)を先に数えた

| 記録 | ready 行 | `engineReference.baseline.scoreCp` あり | `mate` あり | meta |
|---|---|---|---|---|
| 2026-09-10-claude-10moves | 11 | 11 | 0 | nodes 4000000・threads 1・gitHead 55f13b29 |
| 2026-09-12-live-30moves-claude-1 | 16 | 16 | 0 | 同上 |
| 2026-09-12-live-30moves-claude-2 | 16 | 16 | 0 | 同上 |
| 2026-09-12-live-30moves-claude-3 | 16 | 16 | 0 | 同上 |
| **合計** | **59** | **59** | **0** | |

- **`engineReference` には `lowerbound` / `upperbound` の標識が載っていない**(P-34 のとおり、`scoreCp` が標識を落として記録している)。**標識付きの割合を比べるには、U6-L で足した `searchPvs` の側を使う**
- **駒得版の 59 行に `mate` は 0 行。** 固定棋譜に終局が無いので、ここからは詰みの振る舞いは比べられない(4. の 2)

### 6.3 `EvalDir` の読み方と、評価ファイルが読めないときの振る舞い(**ソースで確かめた**。commit `c1b80eaa`)

| 確かめたこと | ソース | 結果 |
|---|---|---|
| `EvalDir` の既定 | `eval/nnue/evaluate_nnue.cpp:70-76` | **`NNUE_EMBEDDING_OFF` が定義されているときだけ `"eval"`。それ以外は `"<internal>"`**(実行ファイルに埋め込んだ評価関数を読む) |
| 何から見た相対か | 同 `:908`(`load_eval()`) | **`Path::Combine(Directory::GetBinaryFolder(), dir_name)` ― 実行ファイルのあるフォルダから見た相対。** `UsiEngine` が cwd を渡さずに spawn すること(`apps/server/src/engine/usiEngine.ts:102`)は、評価ファイルの置き場所に**影響しない** |
| 読めないとき | 同 `:916-918`・`:949-952` | ファイルが開けなければ `FileNotFound`。**`Error! : failed to read <パス> : <理由>` を出して `Tools::exit()` で終了する。** 黙って動き続けない |
| 読み始めたことの記録 | 同 `:917`・`:942` | `info string loading eval file : <パス>`(埋め込みなら `<internal>`)を出す。**これを、どのファイルを読んだかを確かめる手段に使う** |
| 埋め込みの前提 | `config.h:332` | 「ビルドするときに source フォルダ直下に `nn.bin` を配置すること」 |

**したがって**:

- **`EvalDir` が `"eval"` になる組み方なら、評価ファイルは `apps/server/engine/nnue/eval/nn.bin` に置けば読まれ、`setoption name EvalDir` を送る必要は無い**(本番コードの変更は要らない見込み)
- **`"<internal>"` になる組み方なら、ビルド時に何を埋め込んだかを確かめないと、評価値の出どころが分からない**(6.4 で確かめる)
- **予-N2 の範囲を狭める**: 「評価ファイルが無いと `isready` でエラー」は **`EvalDir` が `"<internal>"` でないとき**に限る。**どのファイルを読んだかは `info string loading eval file :` の行で確かめる**

### 6.4 ビルドの結果・埋め込みの有無・校正の詰みの局面・評価ファイルの候補(2026-09-14)

**ビルド(予-N1: 的中)**

| 項目 | 結果 |
|---|---|
| コマンド | `make -j8 normal COMPILER=clang++ TARGET_CPU=APPLEM1 YANEURAOU_EDITION=YANEURAOU_ENGINE_NNUE`(scratchpad のソース内。`apps/server/engine/` にはまだ置いていない) |
| 終了コード・所要 | **0・27 秒** |
| 警告・エラー | **警告 1(`ld: warning: option -s is obsolete and being ignored`)・エラー 0** |
| 実行ファイル | `YaneuraOu-by-gcc`、Mach-O 64-bit arm64、699,645 バイト |
| 付いた定義 | `-DYANEURAOU_ENGINE_NNUE` のみ(型の定義 `-DEVAL_NNUE_*` は無し)。**Makefile:10 により標準 NNUE 型(halfKP256)** |

**埋め込みの有無(6.3 の「6.4 で確かめる」を解消)**: Makefile:160 の既定 `EVAL_EMBEDDING = OFF` では `-DNNUE_EMBEDDING` が付かない(Makefile:499-500)。`config.h:382-388` は「NNUE かつ `NNUE_EMBEDDING` が無いなら `NNUE_EMBEDDING_OFF` を定義する」。**したがってこのビルドは埋め込みなしで、`EvalDir` の既定は `"eval"`(実行ファイルから見た相対)。** 評価ファイルは `apps/server/engine/nnue/eval/nn.bin` に置く。ビルド時に source 直下に `nn.bin` は無かった(`ls` で確かめた)。

**校正の詰みの局面(4. の 2。エンジンとは別の根拠で確かめた)**

- 局面: `4k4/9/4P4/9/9/9/9/9/4K4 b G 1`(先手: 5九玉・5三歩・持ち駒 金 / 後手: 5一玉)
- 手: `G*5b`(▲5二金打)
- **本番のルール関数だけで確かめた結果**(`apps/server/src/rules/`。エンジンは使っていない): `isLegalMove` → true / 指したあとの局面 `4k4/4G4/4P4/9/9/9/9/9/4K4 w - 2` で `isInCheck(gote)` → true / **後手の `getLegalMoves` → 0 件** / `isGameOver` → true / **`getGameOutcome` → `{ result: "checkmate", winner: "sente" }`**。元の局面は `isGameOver` → false(先手の合法手 85 件)
- **つまり root 局面で先手に 1 手詰がある。** 予-N3 は、この root 局面を探索させて `score mate 1`(または同等)が出るかで判定する

**FV_SCALE**: 既定値は **16**(`eval/nnue/evaluate_nnue.cpp:101`)。候補の配布元に書かれた最適値は、水匠 5 が 24、Háo が 20。**`UsiEngine` は FV_SCALE を送らない**ので、既定の 16 のまま測ると配布元の推奨と違う値で評価することになる。**本番コードを変えずに渡す手として `eval_options.txt`(`usi.cpp:1383-1386`)がある**が、その探し方(実行ファイル基準か cwd 基準か)は 6.5 で確かめる。

**展開の道具**: 候補はどちらも `.7z`。`7z` 系のコマンドは無いが、**macOS 標準の `bsdtar 3.5.3`(libarchive)が 7-zip の展開に対応**(`man tar`)。

**評価ファイルの候補**(**GitHub の公開 API と Release の本文で確かめた。書かれていないことは書かれていないと書く**)

| | 水匠 5 | tanuki- の Háo |
|---|---|---|
| 配布元 | [yaneurao/YaneuraOu の Release `suisho5`](https://github.com/yaneurao/YaneuraOu/releases/tag/suisho5)(やねうら王の公式リポジトリ。本文に「たややんさんに提供していただきました」) | [nodchip/tanuki- の Release `tanuki-.halfkp_256x2-32-32.2023-05-08`](https://github.com/nodchip/tanuki-/releases/tag/tanuki-.halfkp_256x2-32-32.2023-05-08) |
| ファイル | `Suisho5.7z`(展開すると `nn.bin`) | `tanuki-.halfkp_256x2-32-32.2023-05-08.7z` |
| サイズ | **24,062,512 バイト** | **23,966,109 バイト** |
| 公開日 | 2024-06-09 | 2023-05-08 |
| 型 | 「標準NNUE型(NNUE_halfKP256)」(本文) | 「標準 NNUE (halfkp_256x2-32-32)」(本文) |
| FV_SCALE の最適値 | 24(本文) | 20(本文) |
| **利用条件** | **Release の本文にも公式記事(2024-06-23)にも書かれていない。** リポジトリ全体のライセンスは GPL-3.0 だが、**提供者が別であり、この評価ファイルに GPL-3.0 が及ぶとは書かれていない** | **Release の本文には書かれていない。** リポジトリ全体のライセンスは GPL-3.0(API で確かめた)。検索結果の要約にあった「GPLv3 明示」は、**配布元の本文では確かめられなかった** |
| このビルドとの型の一致 | 一致(halfKP256) | 一致(halfkp_256x2-32-32 = 標準 NNUE) |

### 6.5 `eval_options.txt` の探し方と FV_SCALE の渡し方(**ソースで確かめた**)

**6.4 で疑った「`eval_options.txt` だけ cwd 基準になる」は、誤りだった。** `usi.cpp:1385` は `Path::Combine(options["EvalDir"], "eval_options.txt")` を作るだけだが、それを開く `SystemIO::TextReader::Open`(`misc.cpp`)が**「起動フォルダ相対での path」として `Path::Combine(Directory::GetBinaryFolder(), filename)` を前に付けて開く。** したがって `eval_options.txt` も `nn.bin` と同じく、**実行ファイルのフォルダから見た `eval/`** で探される。

| 確かめたこと | ソース | 結果 |
|---|---|---|
| FV_SCALE の既定 | `eval/nnue/evaluate_nnue.cpp:101` | USI オプション `FV_SCALE`、既定 16・範囲 1〜128 |
| `eval_options.txt` を読む時点 | `usi.cpp:1376-1390` | **`isready` の中、`engine.isready()` の前**(評価ファイルを読むより前に値が上書きされる) |
| 読んだことの記録 | `usioption.cpp:431-441`(`read_engine_options`) | 開けたら `info string read engine options, path = <パス>` を出す。**開けなければ何も出さずに戻る**(黙る側) |
| 書式 | `usioption.cpp`(`build_option`) | `option name …` の形、`名前 値` の形、`名前=値` の形のいずれも可 |

**FV_SCALE の渡し方(採った順と理由)**: 並行セッションが示した順は「(1) `usi` の応答に `option name FV_SCALE` があるか → (2) ハーネス(`scripts/`)から `setoption` → (3) `eval_options.txt`」。**`eval_options.txt` は `scripts/` も `apps/` も 1 行も変えずに済む**(gitignore 済みの `apps/server/engine/nnue/eval/` にテキストを 1 つ置くだけ)ので、**(3) を (2) より先に試す。** 効いたことは次の 2 つで確かめる ―(a) `isready` の後に `info string read engine options, path = …/eval/eval_options.txt` が出る、(b) **`read_engine_options` は開けないと黙る**ので、(a) の行が出なければ「効いていない」と読む(何も出ないことを、効いたことと読まない)。**それでも効かなければ (2) に進み、`scripts/` の変更として書く。**

### 6.6 記録に残すもの(**`meta` に評価関数の種類が残らないため**。並行セッションの指示)

**`meta.enginePath` は、駒得版でも NNUE 版でも同じ名前(`…/YaneuraOu-by-gcc`)になりうる。** 記録から評価関数の種類を区別できない。したがって NNUE 版で `replay.ts` を回すときは、**次を実測の節に必ず書く**:

- エンジンの `usi` の応答の `id name` の行(そのまま)
- 評価ファイルの名前・パス・sha256・サイズ(と、展開元の `.7z` の sha256・サイズ)
- 実行ファイルの sha256 と、ビルドした commit(clone した HEAD `c1b80eaa`)
- `SHOGI_ENGINE_PATH` に渡した値
- FV_SCALE の値と、それを渡した経路(6.5)
- 出力先の JSONL のパス(**駒得版の `out/u6l` と混ざらない場所**。`scripts/playtest/out/d0-nnue/`)

**既知事項の候補(番号未定。採番は並行セッション)**: **`meta` 行に評価関数の種類が残らない。** `enginePath` はファイル名で、駒得版と NNUE 版を区別しない。評価ファイルのパス・sha256、FV_SCALE、`id name` も載らない。**記録だけを見て、どの評価関数で測った数字かが分からない**(U6-R が `gitHead` について直した「どのコミットのものでもない数字」と同じ型で、こちらは「どの評価関数のものでもない数字」)。載せるには `scripts/playtest/lib/recorder.ts`(`buildMetaLine`)か `apps/server/src/engine/usiEngine.ts` の変更が要るので、**D0 では行わない。**

### 6.7 評価ファイルの取得と配置(2026-09-14。**人間がチャットで「水匠 5 を落とす」を選んだ**)

| 項目 | 値 |
|---|---|
| 取得元 | `https://github.com/yaneurao/YaneuraOu/releases/download/suisho5/Suisho5.7z`(Release `suisho5`) |
| `.7z` のサイズ | **24,062,512 バイト**(Release の API の値と一致) |
| `.7z` の sha256 | `6734e3a3d28e67b9206c3442f6d10f16148138327dff811cadedfcf581f79809` |
| 中身 | `nn.bin` 1 つ(`bsdtar -tvf` で確かめた。日付 2021-10-28) |
| 展開 | `bsdtar -xf`(macOS 標準、libarchive 3.5.3) |
| `nn.bin` のサイズ | **64,217,066 バイト** |
| `nn.bin` の sha256 | `768068f0d534a0603a5d38bcd143de6bbca820d5f1c95a14d40863e5b7892d76` |
| 置いた先 | `apps/server/engine/nnue/eval/nn.bin`(置いた先と展開元の sha256 が一致することを確かめた) |
| FV_SCALE | `apps/server/engine/nnue/eval/eval_options.txt` に `FV_SCALE 24`(6.5 の経路 (3)) |
| 実行ファイル | `apps/server/engine/nnue/YaneuraOu-by-gcc`、sha256 `53999a5abdf6e4a29872fa5e0416aa9b592560ed2a464ef50f8f75fd74674351`(組んだ場所のものと一致)。ビルドの commit `c1b80eaa09fe13d5f12b1599d1ae4d53c224de30` |
| 駒得版 | `apps/server/engine/YaneuraOu-by-gcc`、sha256 `1a6bbf963980dce9fe9f994e837c00ccdbe15ca82c1d9331791bb983ea206e87`。**置く前後で変わっていない** |
| git | `apps/server/engine/` 以下は `git status` に出ない(`apps/server/.gitignore` の `/engine/`) |
| **利用条件** | **Release の本文にも公式記事(2024-06-23)にも書かれていない**(6.4)。**法律の判断はしていない** |

### 6.8 FV_SCALE が「効いた」ことを評価値で確かめる ― 予測(**測る前に書く**)

**「読んだ」と「効いた」は別である**(並行セッションの指示)。`info string read engine options` の行は「読んだ」の証拠にしかならない。**同じ局面を FV_SCALE 16 と 24 で 1 回ずつ探索し、評価値そのものが変わることを見る。**

**向き(ソースで確かめた)**: `eval/nnue/evaluate_nnue.cpp:820-822` で評価値は **`output[0] / FV_SCALE`**。**FV_SCALE を大きくすると、評価値の絶対値は小さくなる。** 並行セッションの指示文にあった「24/16 に近い比で変わる」は、**比の向きが逆**である(24 の方が大きくなるのではなく、16 の方が大きい)。

| # | 予測 | 外れたと言える条件 |
|---|---|---|
| 予-N5 | 同じ局面・同じノード数で、**FV_SCALE 24 の `score cp` は、16 のときの約 16/24 ≈ 0.67 倍になる**(符号は同じ) | 比が 0.67 から大きく離れる、または符号が変わる。**比がほぼ 1 なら、24 が効いていない**(`eval_options.txt` を読んでも値に反映されていない) |

- **比は厳密には 0.67 にならない。** 探索は評価値の大きさで枝の選び方が変わるので、同じノード数でも読み筋が変わりうる(**P-33**: 別々の探索は一致しない)。**「近い」の幅は決めずに、比の値をそのまま出す。**
- **局面は、評価値が 0 付近にならないものを使う**(0 付近だと比が暴れる)。初期局面から後手の飛車を 1 枚除いた局面(`lnsgkgsnl/7b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1`)を使う。**この局面の評価値の良し悪しは判断しない**(比だけを見る)
- **16 のときも `eval_options.txt` に `FV_SCALE 16` と明示して読ませる**(ファイルを外して既定に戻すと、「読んだかどうか」まで一緒に変わってしまい、比べる条件が 2 つ変わる)。**終わったら `FV_SCALE 24` に戻し、sha256 で照合する**
- **エンジンは 1 回ごとに新しいプロセスで起動する**(置換表の持ち越しを避ける)

### 6.9 エンジンの確かめ(2026-09-14。**宣言してから使った**)

**条件**: エンジン `apps/server/engine/nnue/YaneuraOu-by-gcc`(sha256 `53999a5a…`)、評価ファイル `apps/server/engine/nnue/eval/nn.bin`(水匠 5、sha256 `768068f0…`)。**エンジンの cwd はわざと scratchpad(エンジンのフォルダと無関係)にした。** エンジンは 1 回ごとに新しいプロセスで起動し、1 本ずつ動かした。

**`usi` の応答(記録に残すもの。6.6)**

```
id name YaneuraOu NNUE 9.80git 64APPLEM1
id author yaneurao
option name EvalDir type string default eval
option name FV_SCALE type spin default 16 min 1 max 128
```

**`isready`(`eval_options.txt` あり)** ― 所要 1.38 秒(`usi` から `readyok` まで。**時間の根拠にはしない**)

```
info string read engine options, path = eval/eval_options.txt
info string loading eval file : /Users/midoriko/Desktop/sgogi-coach/apps/server/engine/nnue/eval/nn.bin
info string Error! : can't read file : /Users/midoriko/Desktop/sgogi-coach/apps/server/engine/nnue/book/standard_book.db
readyok
```

| 確かめたこと | 結果 |
|---|---|
| 評価ファイルが実行ファイル基準で読まれる(6.3) | **読まれた。** cwd を scratchpad にしても `…/apps/server/engine/nnue/eval/nn.bin` を読んだ(絶対パスで出る) |
| `eval_options.txt` を読んだか(6.5) | **読んだ**(`read engine options` の行が出た)。**これは「読んだ」の証拠であって「効いた」の証拠ではない**(6.8 で確かめる) |
| `eval_options.txt` が無いと黙るか(6.5 の (b)) | **黙った。** ファイルを一時的に外すと `read engine options` の行は **0 行**、評価ファイルは読まれて `readyok` も返った(所要 0.84 秒)。**ファイルは戻し、sha256 の一致を確かめた** |
| 予-N3(1 手詰で `score mate`) | **的中。** `4k4/9/4P4/9/9/9/9/9/4K4 b G 1` を `go nodes 200000` で `info depth 8 seldepth 2 multipv 1 score mate 1 nodes 677 … pv G*5b` / `bestmove G*5b`。rules/ で確かめた手(6.4)と一致 |

**気づいたこと ― 定跡ファイルのエラー**: `isready` で毎回 `info string Error! : can't read file : …/nnue/book/standard_book.db` が出る。**定跡ファイルが無いというエラーで、`readyok` まで進むので致命的ではない。** **既知事項の候補(番号未定)として 7. に書いた。**

**「120 秒で終わらず裏に回った」原因(並行セッションの依頼。P-38 の材料)**: **エンジンの待ちではなく、担当が書いたドライバの読み方の誤りだった。** 1 版目のドライバは `select` でパイプを見てから text モードの `readline` で 1 行ずつ読んでいた。エンジンは `usi` に対してオプション一覧と `usiok` をまとめて出すので、Python 側が最初の読み込みで全部を内部バッファに取り込み、最初の 1 行(`id name …`)だけを返した。残りはバッファにあるのにパイプには新しいデータが来ないので `select` が「何も来ていない」と答え続け、`usiok` を待ったまま 120 秒で打ち切った。**`isready` での評価ファイルの読み込みでも、`bestmove` を待つ時間でもない。** ファイル記述子から直接読む 2 版目では同じ手順が 1.38 秒で終わった。**P-38 に対しての含意**: **応答が来ないように見える待ちには、読む側のバッファで見えていないだけのものがありうる。本番の `UsiEngine`(Node の stream)が同じ形かは確かめていない。**(P-38 へ添えるかは司令塔がコミット時に決める。P-38 の行は触らない)

**止めたときの誤り(担当自身。記録として残す)**: 1 版目のドライバを止めるとき、**自分の処理を 3 回、自分で数えた** ―(1) コマンドライン全文に `usi_driver.py` を含むかで判定し、**判定の文字列を含む自分のシェル**を数えた、(2) 数える Python のコードに同じ語が入っていて**数える Python 自身**を数えた、(3) 同上をもう一度。**P-31(ps で自分を数えて本数を多く見る)と同じ型を、規則 10 番の注記を書いた本人が 3 回踏んだ。** 自分の pid を除き、エンジンは `comm`、ドライバは引数の「語」がドライバのパスで終わるものだけを数える形に直してから、始める前も終わった後も 0 本だった。**0 本側の誤り(見落とし)ではなく、多い側の誤り(自分を数える)だったので、止めすぎ・回し損ねで済み、他のセッションの処理には触れていない**(止めたのは NNUE 版のエンジン 37912 と、私の scratchpad のドライバとシェルだけ)。

### 6.10 評価ファイルが無いときの振る舞い(予-N2)と、FV_SCALE が効いたか(予-N5)(2026-09-14)

**予-N2: 的中。** `nn.bin` を一時的に外して `usi` → `isready` を送ると、

```
info string read engine options, path = eval/eval_options.txt
info string loading eval file : /Users/midoriko/Desktop/sgogi-coach/apps/server/engine/nnue/eval/nn.bin
Error! : failed to read /Users/midoriko/Desktop/sgogi-coach/apps/server/engine/nnue/eval/nn.bin : FileNotFound
```

のあと、**`readyok` を返さずに終了した(終了コード 1、`readyok` の行 0)。** 黙って動き続けない(6.3 のソースの読みどおり)。**`nn.bin` は戻し、sha256 の一致を確かめた。**

**予-N5: 的中(比 0.697。目安 16/24 = 0.667)。** 同じ局面(初期局面から後手の飛車を 1 枚除いた `lnsgkgsnl/7b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1`)を `go nodes 1000000`・Threads 1・毎回新しいプロセスで探索した。**どちらの回も `read engine options` の行が出た**(16 のときも `eval_options.txt` に明示して読ませた)。

| FV_SCALE | 最後の `score cp` | depth | nodes | bestmove |
|---|---|---|---|---|
| 16 | **1101** | 19 | 1,000,302 | 7g7f |
| 24 | **767** | 21 | 1,000,486 | 7g7f |

- **比 cp24 / cp16 = 767 / 1101 = 0.697。** 符号は同じ。**比が 1 から大きく離れているので、`eval_options.txt` の `FV_SCALE 24` は評価値に効いている。**
- **0.667 と一致しないのは予想の範囲**(6.8: 同じノード数でも読み筋が変わる。実際に depth と読み筋の後半が違う)。**局面の評価の良し悪しは判断していない。**
- 終わってから `eval_options.txt` を `FV_SCALE 24` に戻し、**置いたときの sha256 と一致することを確かめた。**
- **速さ(枠の見積もりに使うだけで根拠にしない)**: 1 スレッドで nps 約 58〜59 万、100 万ノードで約 1.7 秒。**このとき他のセッションの作業で load average は 4 台だった**(6.9 の確かめの直前に 4.78)

## 7. 既知事項の候補(**番号は付けない**。採番は司令塔がコミット時に行う。規則 9 番)

### 7.1 `meta` 行に評価関数の種類が残らない

6.6 に書いたとおり。**D0 では直さない**(`recorder.ts` か `usiEngine.ts` の変更が要る)。

### 7.2 定跡ファイルが無いというエラー行が `isready` で毎回出る(BookFile を `no_book` にしていない)

- **(a) エラー行の実物**(NNUE 版。6.9 の `isready`。確かめの 5 回すべてで同じ行が出た):

  ```
  info string read book file : /Users/midoriko/Desktop/sgogi-coach/apps/server/engine/nnue/book/standard_book.db
  info string Error! : can't read file : /Users/midoriko/Desktop/sgogi-coach/apps/server/engine/nnue/book/standard_book.db
  ```

  `usi` の応答では `option name BookFile type combo default standard_book.db …`、`option name BookDir type string default book`。エラーのあとも `readyok` まで進む。
- **今日の手は探索の手である。** `apps/server/engine/book` も `apps/server/engine/nnue/book` も**存在しない**(司令塔が確かめ、担当も `ls` で確かめた)。本番の `apps/server/src/engine/usiEngine.ts` が送る `setoption` は `MultiPV`(:195)と `Threads`(:204)だけで、**`BookFile` を `no_book` にしていない**(担当も `grep` で確かめた)。
- **危険は将来の話**: **誰かが `book/` を置いた日に、探索ではなく定跡の手が返る。** 候補手の安全確認(CLAUDE.md の 3 番)や診断の評価値が、探索の結果でないものを混ぜうる。
- **(b) 駒得版(`apps/server/engine/YaneuraOu-by-gcc`)でも同じ行が出るかは確かめていない。** 同じソースの系統なので出るはずだと見ているが、**確かめていない**(駒得版はこの STEP では起動していない)。
- **(c) 行が `Error!` を含む**ので、エンジンの出力から「エラーの行」を拾う道具(ログの見張り・テストの判定)が、**致命的でないこの行を誤って拾いうる。**
- **D0 では直さない**(`apps/server/src` には触らない)。

### 6.11 固定棋譜 7 局の再生と、駒得版の記録との比べ(2026-09-14〜15。**宣言してから使い、終わって解放を宣言した**)

**条件**: worktree `scratchpad/wt-d0-nnue`(HEAD `a9da058`、汚れ 0)、`SHOGI_ENGINE_PATH=/Users/midoriko/Desktop/sgogi-coach/apps/server/engine/nnue/YaneuraOu-by-gcc`(sha256 `53999a5a…`)、`nn.bin` sha256 `768068f0…`、`eval_options.txt` = `FV_SCALE 24`、`replay.ts --nodes 4000000 --threads 1`。出力 `scratchpad/wt-d0-nnue/scripts/playtest/out/d0-nnue/`(7 ファイル)。**meta 行は 7 ファイルとも nodes 4000000・threads 1・gitHead `a9da0589`・dirty false・enginePath は上の NNUE 版のパス。**

**1 局ごと**(所要は枠の見積もりにだけ使う。**load average が 3.7〜8.1 で、他のセッションの作業と重なっていた。根拠にしない**)

| 局 | exit | 所要 | ready 行 | `engineReference` が null | load(1 分) |
|---|---|---|---|---|---|
| 2026-09-10-claude-10moves | 0 | 401.7 秒 | 11 | 0 | 5.85 |
| 2026-09-12-live-30moves-claude-1-round2 | 0 | 654.3 秒 | 16 | 0 | 8.10 |
| 2026-09-12-live-30moves-claude-1 | 0 | 945.5 秒 | 16 | 0 | 5.73 |
| 2026-09-12-live-30moves-claude-2-round2 | 0 | 364.7 秒 | 16 | **1** | 3.93 |
| 2026-09-12-live-30moves-claude-2 | 0 | 386.7 秒 | 16 | 0 | 3.69 |
| 2026-09-12-live-30moves-claude-3-round2 | 0 | 365.2 秒 | 16 | 0 | 4.28 |
| 2026-09-12-live-30moves-claude-3 | 0 | 774.0 秒 | 16 | 0 | 4.31 |
| **合計** | **全部 0** | **3,892 秒** | **107** | **1** | |

- **`UsiEngineTimeoutError`・エラーの行: 0**(再生の出力を見張りで見た)。**始める前も終わった後も、私のエンジン・ドライバは 0 本**
- **エンジンの最大 RSS: 1,453,168 KB**(5 秒おきの標本。**置換表の既定の大きさによると見ているが、確かめていない**)

**null の 1 行は「測っていない」(規則 11.6)。** `claude-2-round2` の ply 22(`B*1e` の直後、`lnsgkgsnl/1r5p1/p1pppp2p/6PR1/4b3b/9/P1PPPP2P/1+p1S4L/LN1GKGSN1 b 2Pp 23`)は**先手が王手をかけられている局面**で、`apps/server/src/analysis/engineReference.ts:150` の `if (isInCheck(sfen, "sente")) return { reference: null, searchPvs };` で測らない作り(パスが成立しないため)。記録の `response.urgentMessages` にも `check_received` がある。`elapsedMs` 34。**エンジンの失敗ではない。** 駒得版の `out/u6l` にはこの局が無いので、駒得版でも null になるかは比べられない。

**行の数(司令塔の (1))**

| 記録 | ファイル | ready 行 | `engineReference` が null | `baseline.mate` あり |
|---|---|---|---|---|
| 駒得版 `out/u6l` | 4 | **59** | **0** | 0 |
| NNUE 版 `out/d0-nnue` | 7 | **107** | **1**(上の王手の行) | 0 |

- **(kifuId, ply) の対応: 両方にある 59 / 駒得版だけ 0 / NNUE 版だけ 48(`-round2` の 3 局 × 16)/ 両方にあるが sfen が違う 0**

**同じ 59 行の比べ**(`scratchpad/d0_compare.py`。**どちらが正しいとは言わない**)

| 量 | 駒得版 | NNUE 版 |
|---|---|---|
| `baseline.scoreCp` 中央値 / 最小 / 最大 | −156 / −6772 / 68 | −180 / −4310 / 338 |
| `dropCp` 中央値 / 最小 / 最大 | 203 / −45 / 3578 | 211 / 58 / 2887 |
| `dropCp` ≥ 300 の行 | **27** | **23** |
| `searchPvs`(248 本)の標識付き | 112(45.2%。lower 63 / upper 49) | **81(32.7%。lower 44 / upper 37)** |
| `searchPvs` の読み筋の長さ 中央値 / 最大 | 12 / 32 | 18 / 43 |

| 差(NNUE − 駒得、`baseline.scoreCp`、59 行) | 値 |
|---|---|
| \|Δ\| ≥ 300 の行 | **15** |
| \|Δ\| ≥ 100 の行 | **42** |
| Δ = 0 の行 | 1 |
| \|Δ\| 中央値 / 最大 | 183 / 2522 |
| Δ 中央値 / 最小 / 最大 | 125 / −330 / 2522 |
| 符号が入れ替わった行(両方 0 でない) | 16 |
| `baseline.bestmove` が一致した行 | 25 / 59 |

- **予-N4(多くの行でずれる): 的中**(|Δ| ≥ 100 が 59 行中 42)。**ただし差のうちどれだけが評価関数の違いで、どれだけが探索の揺れかは分けていない。** 規則 12 番の注記(駒得版の同じエンジン・固定ノードでも、別々の探索の値は 0/59 行で再現せず、最大 423cp ずれた)があるので、**1 行ごとの Δ を評価関数の違いの証拠にはしない。**
- **`searchPvs` は `engineReference` とは別の探索である**(`scripts/playtest/lib/recorder.ts:247-254`: `measureEngineReference` の読み筋は捨て、記録の `searchPvs` は本番が③⑤を作った探索)。実際に、同じ行の `engineReference` の cp と、`searchPvs` の同じ source・multipv 1 の cp は、**駒得版 0/59 行・NNUE 版 baseline 1/106 行・afterPass 2/106 行でしか一致しなかった。** これは規則 12 番の注記と同じ現象で、新しい誤りとは見ていない。**上の標識付きの割合は③⑤の探索の割合で、`engineReference` の標識の割合ではない**(P-34: `engineReference` には標識が残らない)
- **NNUE 版だけの 48 行**: `baseline.scoreCp` 中央値 −2356 / 最小 −4824 / 最大 224、`dropCp` ≥ 300 の行 21、`afterPass.mate` 入り 1(`claude-3-round2` ply 24、`mate 11`、`dropCp` は null)
- **詰みは、固定棋譜の `baseline` では 0 行**(4. の 2 の見込みどおり)。**詰みの振る舞いの確かめは 6.9 の 1 手詰の 1 局面だけ**

**気づいたこと ― 詰みでない特別な値が `cp` で記録され、`dropCp` に入っている(1 行)**

- `claude-3-round2` ply 30: `engineReference.afterPass = { scoreCp: 35281, mate: null }`、`baseline.scoreCp` −4824、**`dropCp` 30457**。**2 つの記録を合わせた cp 値(駒得版 118 + 247、NNUE 版 211 + 340)のうち、|cp| ≥ 30000 はこの 1 つだけ**
- **ソースで確かめた(commit `c1b80eaa`)**: `score cp` は `100 * v / PawnValue`(`usi.cpp` の `USIEngine::to_cp`、`evaluate.h:78` の `PawnValue = 90`)。**35281 になる内部値は 31753 だけ**(31752 → 35280、31754 → 35282)。**31753 = `VALUE_SUPERIOR` = `VALUE_MAX_EVAL`**(`types.h`: `VALUE_MATE` 32000 − `MAX_PLY` 246 − 1)。`score.cpp` の `Score::Score` は `is_decisive(v)`(`types.h:515-527`: `v >= VALUE_TB_WIN_IN_MAX_PLY` = 31754)でないときに `cp` で出すので、**31753 は詰みではなく `cp` として出る。**
- **31753 が出る経路は 2 つある**: (i) NNUE の評価値を `VALUE_MAX_EVAL` で切り詰めた値(`eval/nnue/evaluate_nnue.cpp:820-827`。同じ箇所のコメントは、この値が返るのは「ほぼ詰みの局面」だとしている)、(ii) 優等局面の千日手の値(`types.cpp:129` の `REPETITION_SUPERIOR`)。**どちらだったかは測れなかった**(ハーネスの参考探索の info 行は記録に残らない。`recorder.ts:247-254`)。**再現させる探索もしていない**(エンジンは解放済み)
- **意味**: `dropCp` は「両方 cp なら差を取る」(`engineReference.ts:169-172`)ので、**この値は普通の評価値として 30457 の急落に数えられる。** 駒得版の記録には無かった(|cp| 最大は `dropCp` 3578)。**NNUE 版では大差の局面が増えるので、診断の閾値(「−400 の急落」など)に、評価値ではない値が混ざりうる。** 既知事項の候補として 7.3 に書く

### 7.3 詰みでない特別な値(`VALUE_MAX_EVAL` = 35281cp)が `cp` として記録され、`dropCp` に入る

- **実物**: `claude-3-round2` ply 30 の `engineReference.afterPass.scoreCp` 35281(`mate` null)、`dropCp` 30457(6.11)。**NNUE 版の 107 行で 1 行、駒得版の 59 行で 0 行**
- **ソース**: 35281 = `100 × 31753 / 90`、31753 = `VALUE_MAX_EVAL`(= `VALUE_SUPERIOR`)。**詰みの閾値(31754)の 1 つ手前なので `score cp` で出る**(6.11)。**(i) NNUE の評価値の切り詰めか、(ii) 優等局面の千日手か、どちらだったかは測れなかった**
- **危険**: 本番の `engineReference.ts` も `dropCp` も、この値を普通の cp として扱う。**診断(D1 の `diagnose.ts`)が cp の差や閾値で「急落」を数えると、評価値ではない値が急落 1 件として混ざる。** 対局中の③(`pieceThreatFocusExplanation.ts`)が同じ値をどう使うかは確かめていない
- **D0 では直さない**(`apps/server/src` には触らない)。**処遇の案(担当の案。決めるのは司令塔)**: 診断の側で |cp| ≥ 35281 を「評価値として数えない」と明記する / USI の読み取りで区別する
