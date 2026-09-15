# STEP D0-KIFU3 計画: 棋譜の終局の種類(投了・切れ負け・詰みなど)を固定棋譜 JSON に `ending` として残す(2026-09-15、1e)

> 司令塔の依頼(2026-09-15): 人間向けレポートで「切れ負け」を記録から言えるようにする(f2 の指摘)。**計画だけ。実装は合図の後。** 基点 `8ee0839`(`15378c9` まで対象のファイルに差は無い ― f2)。エンジンは使わない。
>
> **状態(2026-09-15)**: 下書き `8a6579b2` に司令塔が E-1〜E-6 を決定(E-4 は直した)→ `1185bb37` に f2 の事前読み REVISE(必須 R-1〜R-4・推奨 S-1〜S-7)→ **司令塔が R-1・S-1 を決定し(R-1 は f2 の「`null` が 2 義になる」の指摘で `unreadable` の形に直した)、この版で全部を取り込んだ(9.)**。→ `992b5a69` に f2 の再読みは**条件つき GO**(C-1・C-2、推奨 S-A〜S-C)→ **この版で取り込んだ(9. の下の段)**。f2 が差分を見た後に実装 1e。急がない(D1b・20 局版が優先)。 → **実装 1e(worktree、基点 `0f47688`)、独立監査 C(往復 0、GO。報告は C の scratchpad `audit-kifu3/AUDIT_D0-KIFU3_IMPL.md` sha256 `420cecef`)、コミット `9d838ad`(司令塔が別の worktree で typecheck 0・623/623・check-docs 0 を測ってから ff)。試験 79/79(既存 66 + 新 13)、変異 15/15(C の追加 7 本は予測 7/7・鳴った 5)。P-1 的中(30 局: resign 21・timeUp 5・mate 4、ply 30/30、ending 以外バイト一致 30/30)、P-2 外れ(期待が変わる試験は 3 か所でなく 6 か所)。既知事項: C の K-1・K-2 は PHASES の P-54・P-55、K-3(「3 か所」は 6 か所)は P-2 の外れとしてここに記録。real-01/02/03 の `kifu/` の作り直しは次の作業(C)。**

## 0. 実物から分かった前提(1e が `8ee0839` の lib で数えた。名前・ファイル名は出していない)

- **F-1** `importKif`・`importCsa` は終局の行を `ending: SourceLine | null` として返す(`lib/kifuImport.ts:84`)。KIF は指し手の先頭が `KIF_ENDINGS` の 12 語のとき(**手数の照合 `:205` より前に判定するので、行頭の数が何でも終局の行になる** ― f2 R-1)、CSA は `%` で始まる最初の片。**shogiops に終局の語の表は無い**(f2)
- **F-2** 「まで N 手で…」の行は `ending` に入らず `summary`(`:180`)。**KIF の表に無い語の終局の行は、指し手として読めずに取り込み全体が止まる**(`unparsable_move`、`:205〜215` ― f2 S-1)
- **F-3** 固定棋譜 JSON を書く口は 3 つ: (i) 側を決めない `toFixedKifu` → `{ id, source, moves }`(`:401`)、(ii) 本人が先手 `alignedFixedKifu` の `mirrored: false` の枝(`lib/sideAlignment.ts:146`)、(iii) 本人が後手の枝(`:147`)。ほかに探索の `lib/players.ts:289` も固定棋譜を書く(この STEP の外)。**今は終局の情報がどこにも残らない**
- **F-4** 手元の分割済み実棋譜 30 局(KIF、道具 `scratchpad/kifu3/endings.mts`)は 30/30 取り込めて、終局の行も 30/30: **投了 21・切れ負け 5・詰み 4**、ほかの語は 0。行頭の数は 30/30 で「元の手順の指し手数 + 1」と一致。「まで N 手で(先手|後手)の勝ち」の行も 30/30(f2 は元の棋譜を開かない規則なので、この数は確かめていない)
- **F-5** `replay.ts` が固定棋譜から読むのは `id`・`moves`・そろえの欄・`originalMoves` だけ(`replay.ts:177〜184`)。知らない欄で止まるかは P-3 で測る
- **F-6** CSA の実棋譜は手元に無い。**2. の CSA の語の表は 1e の記憶による下書きで、確かめていない**(S-3: 実装の前に標準の文書と照らし、文書の名前と版を記録に残す。照らせない語は表に入れない = `unlisted`)

## 1. 目的と範囲

- 固定棋譜 JSON に、棋譜に書かれていた終局の**種類**と**手数**を、**決まった語の表からだけ**残す。レポートは記録から「N 手目で切れ負け」を引ける。**新しい取り込みから効く**(E-4)
- 変える: `lib/kifuImport.ts`(語の表を 1 つにし、終局を `{ kind, ply }` に読む。R-1 の食い違い)・`toFixedKifu`・`lib/sideAlignment.ts` の `alignedFixedKifu`(2 つの枝)・`kifu-import-check.ts`(`ending_ply_mismatch` の詳しい行の出し方。表の列は変えない ― C-2 司令塔)・試験・`scripts/playtest/README.md` の形式の節(**D0-SIDE の欄も一緒に書く** ― S-5)
- 変えない: `replay.ts`(E-6)・`lib/players.ts`・Failure Event JSON・診断とレポートの文・作ってある固定棋譜(E-4)

## 2. 欄の形(決定)

- `"ending": { "kind": "timeUp", "ply": 78 }`。**文(終局の行の元の表記・「まで」の行)は写さない**(E-5)
- **語の表は 1 つ**(S-2): 英名の表から `KIF_ENDINGS` を作る。KIF の 12 語 = 投了 `resign`・切れ負け `timeUp`・詰み `mate`・中断 `abort`・千日手 `repetition`・持将棋 `impasse`・不詰 `noMate`・反則勝ち `illegalWin`・反則負け `illegalLoss`・入玉勝ち `enteringKingWin`・不戦勝 `defaultWin`・不戦敗 `defaultLoss`。CSA の `%` の語は F-6 のとおり実装で表を確かめる。**表に無い CSA の語は `kind: "unlisted"`**(語は写さない。E-3)
- **`ply` は「元の手順の指し手数 + 1」**(**R-1 司令塔の決定**。道具が数えた事実)。回した局でも `originalMoves.length + 1`。`ply` の手番の側は元の向きで読む(奇数 = 元の先手)。本人の側は `originalUserSide` で分かる(R-3)
- **KIF の行頭の数が `ply` と食い違うとき**(R-1 司令塔の決定): `ending` は **`{ kind: "unreadable", reason: "ply_mismatch", ply: null }`**(語・文は写さない。`reason` は列挙で、今は `ply_mismatch` だけ)。その行は **`lines.unread` だけ**に `why: "ending_ply_mismatch"` で入れ(`unused` の `ending` には入れない ― C-2)、取り込みは続ける。その後の指し手行は今と同じく「終局の行の後」として読まない。`kifu-import-check.ts` は読めなかった行に数え、**詳しい行にはこの理由と行番号だけを出す(元の文を出さない)**。表の「終局の行」の列は変えない(結果の `ending` が `null` なので今の書き方のまま「無し」になる ― 7. の限界)
- **取り込みの結果の形**(C-2): `KifuImportResult` の **`ending: SourceLine | null` は変えない**(食い違いのときは `null`)。**`endingFact: FixedKifuEnding | null` を足す**(`FixedKifuEnding` = `{ kind, ply }` か `{ kind: "unreadable", reason: "ply_mismatch", ply: null }`)。`toFixedKifu` は `endingFact` を `ending` として書く。KIF の食い違いは `ending: null`・`endingFact: unreadable` の組で表す
- **欄の位置**(R-2): (i) `{ id, source, ending, moves }` / (ii) `{ id, source, mirrored: false, ending, moves }` / (iii) `{ id, source, mirrored, originalUserSide, plyOffset, startSfen, ending, moves, originalMoves }`。`alignedFixedKifu` は入力に `ending` のキーがあれば同じ位置に写し、無ければ出さない
- **無いとき**(E-2・S-4): 取り込んで終局の行が無い → `null`(**食い違いは `null` にしない** ― 上の `unreadable`)。**キーが無い = 終局の行を見ていない**(この STEP より前の取り込み、探索 `players.ts` の棋譜のように外部の棋譜から作っていない)

## 3. 固定例(期待は試験を回す前に手で書く)

| # | 入力 | 期待 |
|---|---|---|
| T-1 | KIF 20 手 + `  21 投了   ( 0:01/00:00:30)`(`kifText` の既定) | `ending` が `{ kind: "resign", ply: 21 }` と **toStrictEqual** |
| T-2 | 終局の行を `切れ負け`・`詰み` に替えた 2 本 | `timeUp`・`mate`、ply 21 |
| T-3 | KIF の 12 語を 1 本ずつ(表の抜け) | 12 の英名がすべて出て重ならない。英名の表と `KIF_ENDINGS` が同じ集合 |
| T-4 | 終局の行の無い KIF | `ending: null`(キーはある) |
| T-5 | **R-1**: 20 手 + `  25 投了` | 固定棋譜 JSON を丸ごと `{ id, source, ending: { kind: "unreadable", reason: "ply_mismatch", ply: null }, moves: <20 手> }` と toStrictEqual・`unread` に `ending_ply_mismatch` が 1 行・**結果の `ending === null`・`lines.unused` に `kind: "ending"` が 0**(S-D)・取り込みの `kind` は `imported` |
| T-6 | **R-4**: 語の後に文が続く終局の行(`  21 投了 〇〇〇〇` の架空の文) | `ending` が `{ kind: "resign", ply: 21 }` と toStrictEqual(文が写らない) |
| T-7 | CSA `%TORYO`・表に無い語・**符号つきの語 1 つ**(S-3) | `resign`・`unlisted`・`unlisted`、どれも `{ kind, ply }` と toStrictEqual |
| T-8 | **(ii)** 本人が先手で `alignedFixedKifu`。**入力に `ending` の無い例も 1 つ**(S-C) | 欄の並びが 2. の (ii) と toStrictEqual、`ending` は入力と同じ。入力に無い例では出力にもキーが無い |
| T-9 | **(iii)** 本人が後手 | 並びが (iii)。`ending.ply === originalMoves.length + 1`、`ending.ply − plyOffset === moves.length + 1` |
| T-10 | `kifu-import-check.ts --fixed` の子プロセス(架空の KIF、(i)・(ii)・(iii)。**終局の行に文を置かない**)と、**食い違いの行に架空の文(`  25 投了 〇〇〇〇`)を置いた棋譜**の表 | 書いたファイルを**丸ごと** toStrictEqual。食い違いの棋譜は読めなかった行 1・**`ending_ply_mismatch` の詳しい行に 〇〇〇〇 が出ない**(C-1 (a)。ほかの行の元の文は S-7 のとおりこの STEP の外) |
| T-11 | `ending` を持つ固定棋譜を `readSideAlignment`・`planReplayMoves` に通す | 止まらず、`ending` の無いときと同じ結果 |
| T-12 | **S-1(限界の押さえ)**: KIF の表に無い語の終局の行 | 今と同じく `not_imported`・`unparsable_move` |

**既存の試験で期待が変わる 3 か所**(R-2。P-2): `kifuImport.test.ts:224`(`Object.keys` → `["id", "source", "ending", "moves"]`)・`sideAlignment.test.ts:186〜187`(先手の枝 → `ending` を入れた 5 欄)・`:192`(後手の枝 → `ending` を入れた 9 欄)。3 つとも入力の固定棋譜に `ending` を持たせる。**結果の `ending`(`SourceLine`)は変えないので、それを見る既存の試験(`kifuImport.test.ts:108`・`:147`・`:190`・`:308`)と `kifu-import-check.ts:65` の終局の行の文は変わらない**(C-2)

## 4. 変異(中心を壊す変異を必ず入れる ― 規則 11.8。最終の予測は実装の後、当てる前に道具に書く)

- **中心**: 語の表から 1 語を落とす(T-3)/ 食い違いの判定を外し、行頭の数を `ply` に書く(T-5。S-A: 判定を残したまま行頭の数を書くのは、成功した終局では等価)/ 食い違いでも語の `kind` を書く(T-5)/ 食い違いを `null` にする(T-4 と T-5 の区別)/ 食い違いでも結果の `ending` に `SourceLine` を残す(T-5。S-D: 残すと表の `:65` に元の文が出るが T-10 では見えない)/ (ii) の枝で `ending` を落とす(T-8)/ (iii) の枝で `ending` を落とす(T-9)/ 終局の行の文を写す(T-6・T-10)/ 表に無い CSA の語を写す(T-7)/ 終局の行が無いときキーを出さない(T-4)
- **周辺**: CSA の `ply` を 1 ずらす(T-7)/ `ending_ply_mismatch` の詳しい行に元の文を出す(T-10)/ `KIF_ENDINGS`(判定の側)だけから 1 語を落とす(T-3。S-B: 中身の同じ表を別々に持つのは等価)/ 入力に `ending` が無いとき `null` を書く(T-8。S-C)

## 5. 予測(測る前に書く)

- **P-1** 手元の 30 局で `--fixed` を作り直すと、`ending` は投了 21・切れ負け 5・詰み 4、`ply` は 30/30 で**元の手順**(先手の局は `moves`、回した局は `originalMoves`)の指し手数 + 1、`unreadable` は 0。`moves`(回した局は `originalMoves` も)は今の固定棋譜とバイト一致
- **P-2** 既存の試験で期待が変わるのは 3. の 3 か所だけ。ほかの既存の試験は期待を変えずに通る
- **P-3** T-11 のとおり、`ending` のある固定棋譜を再生の前段は拒まない(エンジンを使わず lib の関数で測る)

## 6. 決定(推奨どおり決まったもの。R-1・S-1 は 9.)

- **E-1** 欄は `kind` と `ply` だけ(`unreadable` のときだけ `reason` を足す。勝った側・手番の側は入れない)/ **E-2** 終局の行が無い → `null`、食い違い → `unreadable`、見ていない → キー無し / **E-3** 表に無い CSA の語は `unlisted`(語を写さない・止めない)/ **E-5** 語は表からだけ、元の行の文と「まで」の行は写さない / **E-6** `replay.ts` の meta に写さない
- **E-4** `records/real-01`・`real-02`・`real-03` の `kifu/` は**この STEP では作り直さない**。real-03 のコミットの後に、C が別の小さな STEP で 3 つまとめて作り直す(`moves` のバイト一致・SHA256SUMS の更新)。**そのとき real-01・02 の README の「欄は `id`・`moves`・`source`」と、実棋譜の監査で許す欄も一緒に直す**(S-6)

## 7. やらないこと・限界

- 勝敗・負けた理由の判定、消費時間の読み、変化(分岐)の終局、「まで」の行の読み取り、KI2 形式
- **限界(S-1 司令塔の決定)**: KIF の表に無い語の終局の行は、今と同じく取り込み全体が止まる(語を足さない)。CSA の `unlisted` と非対称なのは、KIF で表に無い行は指し手の可能性があり、黙って続けない方が安全だから
- **限界(C-2 司令塔の決定で表を変えない)**: 手数の食い違う棋譜は、`kifu-import-check.ts` の表の「終局の行」の列が「無し」になる(行はあるが読めなかった。読めなかった行の数と `ending_ply_mismatch` の詳しい行で分かる)
- **この STEP の外(S-7、既知事項の候補)**: `kifu-import-check.ts` のフォルダの表(`:65`)と詳しい行は、終局の行や読めなかった行の元の文を標準出力に出す。E-5 の理由は標準出力にも当てはまる(T-10 は架空の文で `ending_ply_mismatch` の詳しい行だけを見る ― C-1 は (a) を取った。`:65` の列を英名にする (b) は司令塔の判断で、この STEP の外のまま)

## 8. CLAUDE.md のルールとの対応

- 事実だけを残す(「切れ負け」は棋譜に書かれた語で、AI の判断ではない)。相手の名前・元のファイル名は書かない
- 動きを変える変更なので、実装は監査の GO を経てコミットする(承認の委任の条件 1)

## 9. 事前読み f2(`1185bb37` に REVISE)と司令塔の決定の取り込み

| # | 取り込んだ場所 |
|---|---|
| R-1 | 司令塔の決定(ply = 元の手順の指し手数 + 1、食い違いは `{ kind: "unreadable", reason: "ply_mismatch", ply: null }` + `ending_ply_mismatch`。f2 の 2 義の指摘で `null` から直した)→ F-1・2.・T-5・4.・E-2 |
| R-2 | 2. の欄の位置・3. の変わる 3 か所・P-2 |
| R-3 | F-3 の 3 つの口・2. の読み方・T-8・T-9・4.・P-1 |
| R-4 | T-6・T-7・T-10 の toStrictEqual と 4. の中心 |
| S-1 | 司令塔の決定(語を足さない)→ F-2・T-12・7. の限界 / S-2 → 2.・T-3 / S-3 → F-6・T-7 / S-4 → 2. の「無いとき」/ S-5 → 1.(README に D0-SIDE の欄も)/ S-6 → E-4 / S-7 → 7. |
| **再読み `992b5a69`(条件つき GO)** | **C-1** → T-10 を (a) に絞り、§7 に (b) を残した / **C-2**(司令塔: 元の行の `ending` は替えず別の欄を足す・既存の試験 4 か所と表は変えない)→ 2. の「取り込みの結果の形」(`endingFact` を足す・食い違いは `unread` だけ)・3. の P-2 の文・7. の限界 / **S-A**・**S-B** → 4. の変異の定義 / **S-C** → T-8・4. |
