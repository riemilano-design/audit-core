# 封: 注入の仕掛け(測定の harness)の総点検 ― 2026-10-29

**人間(2026-10-29)「テストハーネスの穴の総点検 ― 今回の手違いと同様のバグが、前期比テストや単位変換テストのスクリプト内に潜んでいないかを網羅的に点検すること。君に任せる」。** 前の 2 便(注入 T2 で通した 5 行の診断、注入 741 行の全行の診断)で見つかった「測定の対応付けが、差し替えた token とは別の文の claim を指した」型が、`measure/` の他の注入の仕掛けに無いかを点検する。**点検だけ。engine(`core/`・`adapters/`)は 0 行。既存の記録は 0 行。新しい記録 file も script も作らない(数は既存の記録から門が数え直す)。直すなら別の封。** 0 USD・通信なし・席(LLM)は呼ばない・engine を走らせない。
作法は変えない(封 → 文書 → 凍結 → 独立監査 GO → commit)。数を見てから封・予測を直さない。外れは外れとして残す(補足は日付つきの追記)。

- 封の時点: branch `feature/audit-core-final-eval-8`、HEAD `cb4283d`、`vocabulary.DEFAULT_PROFILE = "P27"`。
- この封は docID・claim の id を書かない(新しい標本・評価用・調整用・67 書類のどれも)。書類と行は位置か集計で呼ぶ。理由は前の 2 便と同じ(引きの門 `tests/measure/test_xbrl_fresh_seal.py` は `LATER_NAMING_FILES` の外の追跡 file に新しい標本の docID が出ると赤になる。評価用・調整用の docID も外に出さない)。
- 前例の型: 封 `docs/XBRL_INJECT_REACH_DIAG_SEAL_2026-10-28.md`(§0 の問い・§3 の欄ごとの予測・§6 の下調べ)と、その門 `tests/measure/test_xbrl_inject_reach.py`(順序の門 (i) の型)。

## §0 問いと根拠

### §0-1 問い

`measure/` の script のうち、**文の中の数(または文)・fact の属性・claim の値を差し替えて engine に再検証させ、その結果を元の claim に対応付けて数える仕掛け**(= 注入の harness)は何本あり、それぞれ:

1. **基準の claim の対応付け**はどう決めるか(site の id をそのまま使う / claim の id / 値(と字)で引く / fact の鍵で引く / 基準なし)。
2. **注入後の claim の対応付け**はどう決めるか(同じ id を引いて値を読み返す / 値(と字)で引く / fact の鍵)。
3. **「差し替えが、数えている claim に届いた」ことを仕掛け自身が確かめているか**(例: 同じ id の claim の値が差し替え後の値と一致しなければ `id_shift` にして数えない、という作り)。
4. 確かめていないなら、**記録のどの数が「対応付けの数」でありうるか**(= 前の 2 便と同じ穴)。その数を引いている台帳 `docs/FACTS_FOR_BUYERS_2026-10-20.md` の行(L-/D-/H-/P-)と `docs/` の結果文書はどれか。
5. 確かめているなら、**記録に残る「届かなかった行」の数**(`id_shift`・`sentence_not_found`・`missing` など、記録の欄の名のまま)はいくつか。

### §0-2 前の 2 便の判定(引用)

`docs/XBRL_T2_PASS_DIAG_2026-10-28.md` §5:

> 通した、と数えられた理由は、engine が単位の誤りを見逃したことではなく、測定の対応付け(`_find_base_claim` は値と字、`claim_for` は値だけに落ちる)が、差し替えた token とは別の場所の claim を指したことだと、記録の欄から言える。

`docs/XBRL_INJECT_REACH_DIAG_2026-10-28.md` §5:

> T1・T2・T5 では、「止めた」と数えた行の全部が「届いた(文)」の行だった(P22・P26・P27 とも。「届かない・止めた」は 0)。「届かない」のは 5 行で、5 行とも通した側にある。

同 §6 の仮説 3:

> 「止めた」の中に届かない行が無いのは、基準が「無改変の P22 で GROUNDED の claim」と定義されているため、状態が動いた行は定義から差し替えが claim に届いた行になるからでもある。

同 §8:

> 絞られた行(基準に対応が付かない・基準が GROUNDED でない)の側の差し替えが、engine にどう見えるか。この診断は絞られた後の 561 行しか見ていない。

### §0-3 この封が使う語(前の 2 便から)

- **届いた(文)**: 差し替えた token がある文(engine の文の一覧の番号)と、数えた claim の文が同じ。**届いた(数)**: さらに文の中の位置が claim の数の字に重なる(`docs/XBRL_INJECT_REACH_DIAG_SEAL_2026-10-28.md` §2-2)。この封は engine を走らせないので、届いた(文)・届いた(数)を**新しく数えない**。数えるのは、記録に既に在る欄だけ(§2-3)。
- **分類 6 語**((対応が付かない)・(文が 1 つに決まらない)・(届いた・止めた)・(届いた・通した)・(届かない・止めた)・(届かない・通した))は 741 行の記録 `fixtures/xbrl/inject_reach_2026-10-28.json` の語。この封は 6 語を他の記録に当てはめない(当てはめるには engine の文の番号が要る。§4)。
- **前の 2 便の穴の型**(この封で「同じ型」と呼ぶもの): 基準の claim、または注入後の claim を**値(と字の部分文字列)で引き**、引いた claim が差し替えた token の場所の claim であることを**確かめずに**数える作り。

### §0-4 封を書く前に見たもの(予測の偏りの出どころ)

- 前の 2 便の封・診断の文書の全文(4 本)と、新しい標本の封 `docs/XBRL_FRESH_SAMPLE_SEAL_2026-10-21.md` の全文。
- `measure/**/*.py` の 179 file に §1 の規準を当てた結果(file 名・行数・当たった字。39 file)と、file 名の字が他の file の本文に在るかの機械の一覧(使う側の下書き。`inject` のように短い名は他の file 名にも当たるので、そのままは使わない。§6 で import の形で数え直す)。
- 注入の字(`inject`・`注入`・`mutat`・`差し替え`・`tamper` ほか)を含む `sheet_*`・`final8_material`・`p17_measure` など 12 file の先頭の説明文(注入の仕掛けではなさそうだと見た。§6 で確かめる)。
- `measure/inject.py` の先頭 60 行と関数の一覧(`select`・`apply_edits`・`revert`・`build_t1`〜`build_t7`。claim への対応付けは持たない共通部品と見た)。
- `measure/xbrl_cd_material_2026-10-17.py` の 85〜307 行(注入 8 件を 1 本の文に当て、行 → claim を「値が許容差の内側 かつ 数の字面が span に在る」の**最初に当たった 1 件**で決める所)と、`measure/xbrl_rowclaim_map_2026-10-17.py`・`xbrl_branch_a`・`xbrl_contract_v1`・`xbrl_dim_diag`・`xbrl_role_swap`・`xbrl_verify_inventory`・`qwed_compare` の先頭の説明文と `apply_edits(` の行。
- `measure/kokkai_false_pass_2026-10-15.py` の全文(要約の claim の `number.value` を 1 件だけ書き換え、同じ id の claim の数の検査を読む作り)。
- 記録 13 本(§5 の下調べの記録)の**欄の名前だけ**(値は見ていない)。そこで見た欄の名: `period_bind_2026-10-20.json` の行に `id_shift`・`sentence_not_found`(先頭の行で None)、`ritual_2026-10-20*.json` の 4 本に「通した のうち参照先が動いた(注入の前後で GROUNDED の参照先が違う)」と行の欄 `参照先(注入前)`・`参照先(注入後)`・`参照先が動いた`、`p27/eval_inject_2026-10-27.json`・`tune_inject`・`tune_p27_inject` に `基準に対応が付かない`・`両方の profile で対応が付く`・行の欄 `docID`・`id`・`型`・`文体`・`基準の claim`・profile ごとの欄。
- 台帳 `docs/FACTS_FOR_BUYERS_2026-10-20.md` の節立てと L-30〜L-32 の 3 行の頭(行は `| ID | … | 〔印 記録の path#欄〕 |` の形で、印に記録の path が書かれている)。
- **見ていないもの**: 39 file のうち上に挙げた以外の対応付けの code、記録の値(行の数・欄の中身)、台帳の L-33 以降の行、`docs/` の結果文書のうち前の 2 便以外。

## §1 列挙の規準(機械)と、当たった file

### §1-1 規準

1. 母集団: audit-core の木の `measure/**/*.py`(`glob` の recursive。`measure/tests/` と `measure/lib/` を含む)。HEAD `cb4283d` で **179 file**。
2. 当たり: 次の (a) か (b) のどちらか。
   - (a) 本文(UTF-8 で読んだ字)に、次の 7 つの字のどれかが部分文字列として在る(大文字小文字を区別する): `apply_edits(`・`inject_with_profile(`・`run_doc(`・`mutate(`・`IJ.select(`・`inject(`・`inject_doc(`。
   - (b) file 名(basename)に `inject` か `false_pass` が在る。
3. 依頼文が例に挙げた 6 つの字(`inject_doc(` を除く)だけでは **36 file** で、依頼文が候補に挙げた `measure/xbrl_point_prior_2026-10-20.py`(当たる字は `inject_doc(` だけ)と `measure/kokkai_false_pass_2026-10-15.py`(7 つの字のどれも無い)が落ちる。だから `inject_doc(` と (b) を足した。(b) で新しく入るのは `kokkai_false_pass_2026-10-15.py`・`false_pass_compare_2026-10-15.py` の 2 つ。
4. 母集団の外(この封の対象にしない): `fixtures/**/*.py`(53 file)・`tests/**`・`scratchpad/`。§6 で同じ規準を `fixtures/**/*.py` に当てた数を副産物として書く(対象には入れない)。
5. 門 (a) はこの規準で列挙し直し、文書の表の file の集合と一致することを見る。

### §1-2 当たった file(39。HEAD `cb4283d`)

| # | path | 行数 | (a) で当たった字 | (b) |
|---|---|---|---|---|
| 1 | `measure/false_pass_2026-10-14.py` | 231 | `run_doc(`・`mutate(` | 名 |
| 2 | `measure/false_pass_compare_2026-10-15.py` | 277 | ― | 名 |
| 3 | `measure/holdout_p17_pair_2026-10-14.py` | 176 | `run_doc(` | ― |
| 4 | `measure/inject.py` | 710 | `apply_edits(` | 名 |
| 5 | `measure/kokkai_false_pass_2026-10-15.py` | 172 | ― | 名 |
| 6 | `measure/kokkai_inject_2026-10-14.py` | 144 | `inject(` | 名 |
| 7 | `measure/qwed_compare_2026-10-19.py` | 1053 | `apply_edits(` | ― |
| 8 | `measure/ritual_2026-10-20.py` | 323 | `run_doc(` | ― |
| 9 | `measure/tests/test_inject.py` | 1427 | `apply_edits(` | 名 |
| 10 | `measure/xbrl_a_core_vs_grep_2026-10-17.py` | 359 | `apply_edits(`・`run_doc(`・`IJ.select(` | ― |
| 11 | `measure/xbrl_attr_inject_2026-10-17.py` | 319 | `apply_edits(`・`inject(` | 名 |
| 12 | `measure/xbrl_branch_a_2026-10-17.py` | 228 | `apply_edits(` | ― |
| 13 | `measure/xbrl_cd_material_2026-10-17.py` | 307 | `apply_edits(`・`IJ.select(` | ― |
| 14 | `measure/xbrl_contract_v1_2026-10-17.py` | 262 | `apply_edits(` | ― |
| 15 | `measure/xbrl_default_p26_2026-10-23.py` | 614 | `inject_with_profile(` | ― |
| 16 | `measure/xbrl_default_p27_2026-10-28.py` | 683 | `inject_with_profile(` | ― |
| 17 | `measure/xbrl_dim_diag_2026-10-17.py` | 294 | `apply_edits(` | ― |
| 18 | `measure/xbrl_dim_hold_2026-10-17.py` | 342 | `apply_edits(`・`inject(` | ― |
| 19 | `measure/xbrl_fresh_2026-10-21.py` | 551 | `apply_edits(`・`IJ.select(`・`inject(`・`inject_doc(` | ― |
| 20 | `measure/xbrl_gen_c1_2026-10-20.py` | 820 | `apply_edits(` | ― |
| 21 | `measure/xbrl_gen_c_2026-10-20.py` | 757 | `apply_edits(`・`run_doc(` | ― |
| 22 | `measure/xbrl_holds_product_path_2026-10-19.py` | 464 | `apply_edits(`・`inject(` | ― |
| 23 | `measure/xbrl_hybrid_s2_2026-10-20.py` | 882 | `apply_edits(`・`IJ.select(` | ― |
| 24 | `measure/xbrl_inject_reach_2026-10-28.py` | 431 | `apply_edits(`・`IJ.select(` | 名 |
| 25 | `measure/xbrl_lastbranch_2026-10-21.py` | 1051 | `inject_with_profile(` | ― |
| 26 | `measure/xbrl_p20_rerun_2026-10-17.py` | 313 | `apply_edits(` | ― |
| 27 | `measure/xbrl_p27_eval_2026-10-27.py` | 665 | `inject(` | ― |
| 28 | `measure/xbrl_p27_tune_2026-10-27.py` | 1076 | `apply_edits(`・`IJ.select(`・`inject(`・`inject_doc(` | ― |
| 29 | `measure/xbrl_p27_tune_rerun_2026-10-27.py` | 225 | `inject(` | ― |
| 30 | `measure/xbrl_period_bind_2026-10-20.py` | 925 | `inject_with_profile(` | ― |
| 31 | `measure/xbrl_period_unit_hold_2026-10-19.py` | 262 | `apply_edits(`・`inject(` | ― |
| 32 | `measure/xbrl_pnf_diag_2026-10-17.py` | 349 | `apply_edits(` | ― |
| 33 | `measure/xbrl_point_prior_2026-10-20.py` | 624 | `inject_doc(` | ― |
| 34 | `measure/xbrl_role_swap_2026-10-17.py` | 298 | `apply_edits(` | ― |
| 35 | `measure/xbrl_rounding_2026-10-21.py` | 584 | `inject_with_profile(` | ― |
| 36 | `measure/xbrl_rowclaim_map_2026-10-17.py` | 165 | `apply_edits(` | ― |
| 37 | `measure/xbrl_t2_pass_diag_2026-10-28.py` | 404 | `apply_edits(`・`IJ.select(` | ― |
| 38 | `measure/xbrl_verify_inventory_2026-10-17.py` | 278 | `apply_edits(` | ― |
| 39 | `measure/xbrl_vocab_2026-10-21.py` | 843 | `inject_with_profile(` | ― |

使う側の script・記録の path・台帳の行の列は、code と記録を読んだ後の事実なので §6 の表に書く(§2 の欄)。

## §2 仕掛けごとの点検の欄

### §2-1 数える単位

- **仕掛け** = 「注入した入力で engine を走らせた出力から、数える claim(または行)を 1 つ決める実装」1 か所。**file でなく関数で数える。** 1 つの file に 0・1・2 以上の仕掛けがありうる。
- 仕掛けを import して呼ぶだけの file は**使う側**(使う側の記録の数は、呼んだ仕掛けの型を引き継ぐ)。
- 注入の入力を作るだけで claim への対応付けを持たない部品(`measure/inject.py` など)は**共通部品**。
- 次の file は**対象外**と書き、理由を 1 行で残す: 注入でない(規則を壊す変異・読む file を差し替えるだけ など)/ 注入した本文を席や外部の道具に渡すだけで、engine の出力を claim に対応付けて数えない / 試験 file。

### §2-2 表の列(文書 `docs/XBRL_INJECT_HARNESS_REVIEW_2026-10-29.md` の仕掛けの表)

| 列 | 中身 |
|---|---|
| 仕掛け | file と関数名(門は関数名が file の本文に在ることを見る) |
| 役 | 仕掛け持ち / 使う側 / 共通部品 / 対象外 |
| 注入の対象 | 本文の字 / fact の属性 / 構造化された claim の値 |
| 基準の対応付け | site の id / claim の id / 値(と字)/ fact の鍵 / 基準なし |
| 注入後の対応付け | 同じ id(値の読み返しあり・なし)/ 値(と字)/ fact の鍵 |
| 届いたことの確かめ | **有**(数える claim が差し替えを持つこと ― 値・字・位置のどれか ― を code が確かめ、持たない行を数えない欄に落とす)/ **無** / **不要**(差し替えが数える claim そのものに入る作りで、別の claim を指しようがない) |
| 記録に残る届かなかった行 | 記録の欄の名のまま(`id_shift`・`sentence_not_found`・`missing`・「参照先が動いた」・「基準に対応が付かない」など)と、その数(記録から数える) |
| 穴の型 | **同じ型**(値で引き、確かめ無し)/ **別の型**(何かを書く)/ **無し** |
| 使う側と記録 | 使う側の script(import の形で数える)と記録の path |
| 依存する台帳の行・結果文書 | §2-4 の規準で |

「届いたことの確かめ」の有・無・不要は **code を読んだ判断**で、機械の値ではない。文書は判断の根拠を関数名と、その関数の中の確かめの字(blockquote で 1 行)で書く。門はその字が file に在ることを見る(判断そのものは監査が読み直す)。

### §2-3 記録から数える数(門が数え直す。新しく測らない)

既存の記録にある欄だけを数える。engine は走らせない。

1. `fixtures/xbrl/period_bind_2026-10-20.json`(67 書類・注入 485 件): 行の `id_shift`・`sentence_not_found` が None でない行の数、型別。
2. 同じ注入の仕掛けを使う記録(`rounding_2026-10-21.json`・`default_p26_2026-10-23.json`・`default_p27_2026-10-28.json` の該当の節。§6 で code から特定する)の同じ欄。
3. 儀式の記録 4 本(`ritual_2026-10-20.json`・`_p21`・`_p22`・`_p26`): 行の数、通した数、「通した のうち参照先が動いた」の数と、行の欄 `参照先が動いた` を数え直した数。
4. `fixtures/xbrl/p27/eval_inject_2026-10-27.json`(評価用)・`tune_inject_2026-10-27.json`(調整用)・`tune_p27_inject_2026-10-27.json`(調整用 P27): 行の数、`基準に対応が付かない`(書類別の数えの合計、型別)、profile ごとの分類の語の数(「名指したが別の値」に当たる語があればそれ)と、profile の間の行の重なり。
5. `fixtures/xbrl/cd8/attr_inject_2026-10-17.json`・`fixtures/kokkai/inject_record_*.json`・`false_pass_round12_2026-10-15.json`: 仕掛けの型に応じた届かなかった行の欄(在れば)。
6. `fixtures/xbrl/fresh/fresh_2026-10-21.json`・`inject_reach_2026-10-28.json`: 前の 2 便の数(通した 5・届かない 5 など)を表に写すだけ。数え直しは前の便の門と同じ。

数えた数は文書の `<!-- 門:start 名前 -->`〜`<!-- 門:end -->` の中に置き、門の外の散文は数を持たない。

### §2-4 依存する台帳の行

台帳 `docs/FACTS_FOR_BUYERS_2026-10-20.md` の `| <ID> |` で始まる行(ID は `L-`・`D-`・`H-`・`P-` に数)のうち、行の字に、その仕掛け(または使う側)の**記録の path**、**script の file 名**、**結果文書の file 名**のどれかが在る行。機械で決める。門 (c) は文書が引く行 ID が台帳に在ることを見る。外に出した紙(`~/Desktop/sgogi-coach-handoff/`)は読まない。台帳と `docs/` の結果文書だけ。

## §3 事前予測(欄ごと・外れうる形・外れ方つき。§6 の下調べより前に固定)

予測の土台(§0-4 の範囲で見たもの): 依頼文の候補の一覧、cd8 の材料の行 → claim の対応(値と字の最初の 1 件)、議事録の小さな誤り(claim の値を直接書き換える)、記録の欄の名(`id_shift`・`sentence_not_found`・「参照先が動いた」・「基準に対応が付かない」)。欄の名に `id_shift` があるので、67 書類側の注入(site の id + 値の読み返し)は届いたことを確かめる作りだと見る。新しい標本と調整用・評価用は値で引く作りで、確かめの欄は無いと見る。

| # | 欄 | 予測 | 外れ方 |
|---|---|---|---|
| **H-1** | 仕掛け(§2-1 の単位)の本数(39 file の中) | **8 以上 13 以下** | 7 以下、または 14 以上 |
| **H-2** | 届いたことを確かめている仕掛け(有) | **2 以上 5 以下** | 1 以下、または 6 以上 |
| **H-3** | 確かめていない仕掛け(無) | **3 以上 6 以下** | 2 以下、または 7 以上 |
| **H-4** | 確かめが要らない仕掛け(不要) | **1 以上 3 以下** | 0、または 4 以上 |
| **H-5** | 穴の型が「同じ型」(値で引き、確かめ無し)の仕掛け | **3 以上 5 以下**。その中に `xbrl_fresh_2026-10-21.py` の注入(`inject_doc`)と `xbrl_p27_tune_2026-10-27.py` の注入(`inject_doc`)の両方が入る | 2 以下、6 以上、またはどちらかが入らない |
| **H-6** | 基準も注入後も id で引く仕掛け(`false_pass_2026-10-14.py` の `run_doc`、`xbrl_period_bind_2026-10-20.py` の `inject_with_profile` を含む) | **全部が注入後の値の読み返しを持つ(届いたことの確かめ 有)** | 1 本でも 無 |
| **H-7** | `period_bind_2026-10-20.json` の注入の行で `id_shift` が None でない行・`sentence_not_found` が None でない行 | **どちらも 0 以上 5 以下** | どちらかが 6 以上、または欄が行に無い |
| **H-8** | 儀式の記録 4 本の「通した のうち参照先が動いた」 | **4 本とも 0** | どれか 1 本で 1 以上 |
| **H-9** | 評価用・調整用の記録(`eval_inject`・`tune_inject`・`tune_p27_inject`)の行の欄 | **文の番号・token の位置・届いた/届かないの欄を持たない**(届いたかを記録から数えられない) | どれか 1 本でも持つ |
| **H-10** | 評価用の記録の「名指したが別の値」に当たる分類(在れば。P22・P26・P27 の各 profile) | **各 profile で 1 以上**。P26 と P27 の両方でその分類の行が、どちらか一方だけの行より多い | どれかの profile で 0、または一方だけの行が両方の行以上、またはその分類の語が記録に無い |
| **H-11** | 評価用の記録の T1_VALUE の「基準に対応が付かない」(書類別の数えの合計) | `採った` の合計の **20% 以上** | 20% 未満 |
| **H-12** | 「同じ型」の仕掛け(と使う側)の記録を引く台帳の行(§2-4 の規準) | **6 以上 15 以下** | 5 以下、または 16 以上 |
| **H-13** | 39 file のうち対象外 | **12 以上 22 以下** | 11 以下、または 23 以上 |
| **H-14** | 議事録の 2 本(`kokkai_inject_2026-10-14.py`・`kokkai_false_pass_2026-10-15.py`) | **どちらも「同じ型」でない**(`kokkai_false_pass` は 不要。`kokkai_inject` も値で引かない) | どちらかが「同じ型」 |
| **H-15** | `xbrl_attr_inject_2026-10-17.py`(fact の属性を変える) | **穴の型は「別の型」で、届いたことの確かめは 有**(注入後の claim を id で引き、変えた fact を pointers が指すかを見る) | 「同じ型」、確かめ 無、または 不要 |
| **H-16** | cd8 の材料の行 → claim の対応(`xbrl_cd_material_2026-10-17.py` の行の対応付け) | **「同じ型」**(値と字の最初の 1 件で、届いたことの確かめ無し)。同じ対応付けを写した、または import した file が他に **1 以上**在る | 「同じ型」でない、または他に 0 |

- H-2〜H-4 の幅は H-1 の幅と独立に置いた(合計が H-1 と合わない組み合わせも外れ方に含まれる。それぞれの欄で判定する)。
- H-6・H-7・H-15 は「欄の名に `id_shift` がある」ことから作った見立てで、code はまだ読んでいない。外れたら §0-4 の偏り(欄の名から作りを推した)の外れとして残す。
- H-8 の 0 は「儀式が誤りを通さない」の主張ではない。儀式の「通した」が、測定の対応付けの数ではなく engine の数でありうるか、という欄だけの予測である。
- H-10・H-11 は「値で引く仕掛けは記録の中に対応付けの数でありうる行を持つ」という見立ての予測で、その行が実際に届いていないかは、この便では数えない(§4 の 2)。

## §4 限界(封の時点で分かっているもの)

1. **この封と文書は code と既存の記録を読むだけで、engine を走らせない。** 「届いた(文)」「届いた(数)」は新しく数えない。仕掛けごとの「届いたことの確かめ」の有・無・不要は code を読んだ判断で、門はその根拠の字が file に在ることだけを見る(判断の読み直しは監査がする)。
2. **評価用・調整用の文は repo の外にあり、席も司令塔も開かない(`~/.cache/audit-core/edinetdb-p27/` は開かない)。** 評価用・調整用の仕掛けに同じ穴の型があっても、この便では「位置で数える」ことはしない。文書の「次に測ること」に、要るものだけを書く: 記録に持てる欄(engine の文の一覧の番号・token の文の番号・基準の claim の文の番号と文の中の位置・届いた/届かない・分類 6 語・対応の付け方)と、持てない欄(文の抜粋・docID と文の対応を外から引ける字)を分けて。
3. **列挙の規準は字の部分一致である。** 7 つの字も file 名の字も持たずに本文を差し替えて engine を呼ぶ script は落ちる。§6 で、規準の外の `measure/**/*.py` のうち `verify_document(` を呼び、かつ本文を差し替える字(`replace(`・`tampered` など)を持つ file を数えて副産物として書く(対象には足さない。足すなら日付つきの追記で)。
4. **母集団は `measure/` だけ。** `fixtures/**/*.py`(53 file)・`tests/**` に仕掛けが在っても対象外(§6 に数だけ書く)。
5. **記録の数は記録の欄の範囲。** `id_shift` などの欄が None の行が「届いた」行だという主張は、仕掛けの code がその欄をどう決めるか(§6 で読む)に依る。欄の無い記録で「届かなかった行は 0」とは書かない。
6. **台帳の依存は §2-4 の字の規準で決める。** 台帳の行が数を引いていても、記録の path・script 名・結果文書名のどれも書いていなければ落ちる。外に出した紙(`~/Desktop/sgogi-coach-handoff/` の PDF・HTML)は読まない。紙に載った数は、台帳と結果文書を経由して言えるものだけ。
7. **議事録(国会会議録)は XBRL と別の領域で、別の作り。** 並べて率を比べない。
8. 読みは無い(席は呼ばない。人の目も入らない)。仕掛けの判断は封を書く席と監査の席の code の読みで、人の読みではない。

## §5 file と順序

1. **この封**(文書だけ)。本線へは `docs/XBRL_INJECT_HARNESS_REVIEW_SEAL_2026-10-29.md` として司令塔が写して commit する(scratchpad の file と byte 一致)。封の commit が文書・門のどの commit よりも前であること(順序の門は commit の順で見る)。docID・claim の id を含まない。
2. 点検の便(1 commit。独立監査 GO の後):
   - 文書 `docs/XBRL_INJECT_HARNESS_REVIEW_2026-10-29.md`(節立て: 予測 H-1〜H-16 の当否(先頭)→ 列挙(§1 の規準と 39 file の役)→ 仕掛けの表(§2-2 の列)→ 記録から数えた数(§2-3)→ 依存する台帳の行と結果文書(§2-4)→ 判定(同じ型の仕掛けごとに、どの数が対応付けの数でありうるか)→ 言えないこと → 次に測ること。表と数は `<!-- 門:start 名前 -->`〜`<!-- 門:end -->` の中。門の外の散文は数を持たない(持つ行は【門なし】)。docID・claim の id・禁止語(依頼文の 5 語)・code fence を書かない)。
   - 門 `tests/measure/test_xbrl_inject_harness_review.py`: (a) §1-1 の規準で `measure/**/*.py` を列挙し直し、文書の表の file の集合・行数・当たった字と一致 (b) §2-3 の数を記録から数え直して文書の表と一致(仕掛けの表の関数名と根拠の字が file に在ることも) (c) 文書が引く台帳の行 ID が台帳に在り、§2-4 の規準で選び直した行の集合と一致 (d) H-1〜H-16 の当否を、封の字(予測・外れ方)と文書の表から読み直して一致 (e) 封と文書に docID 0(新しい標本 30・評価用・調整用の docID の字)・claim の id 0・禁止語 0・code fence 0 (f) 順序(封の commit が文書・門の commit より前。前例 `tests/measure/test_xbrl_inject_reach.py` の `test_i_*` の型) (g) 偽物で赤(文書の表の 1 字・記録の写しの 1 欄・封の予測の 1 字・規準に当たる偽の file 1 つを足すと、(a)〜(d) のどれかが赤)。
   - **新しい記録 file は作らない**(数は既存の記録から門が数え直す)。**script も作らない。**
   - 覆い: `python3 measure/suite_coverage_2026-10-16.py --write` と `docs/SUITE_COVERAGE_2026-10-16.md` §2-1 の数(A-06〜A-09)。
3. 凍結(木の sha256 の一覧)→ 独立監査(`step-auditor`。§1 の列挙を自分で走らせ直す、仕掛けの判断を code から読み直す、記録から数え直す、変異 (g))→ GO → commit(パス指定)。監査中は木を触らない。
4. 直しはこの便に入れない。「同じ型」の仕掛けが見つかっても、測り直し(位置で数える)・台帳の字の直しは別の封(司令塔が決める。評価用・調整用の文を開くかは人間が決める)。

## §6 下調べの観測(予測の後。記録と code を読むだけ。0 USD)

§3 を書いて file を保存した後に、本線の木(HEAD `cb4283d`)の code と記録を**読むだけ**で下調べをした(`probe/scripts/records_probe.py` → `probe/records_probe_out.json`、`probe/scripts/ledger_probe.py` → `probe/ledger_probe_out.txt`、ほかに `probe/survey.txt`・`probe/outside_criterion.txt`・`probe/p27_counts.txt`)。**§0〜§5 の字は変えていない**(§3 を固定した時点の §0〜§5 の sha256 `09212a70…0fd246` = 観測の後の sha256。`probe/mtime_seal_predictions.txt`・`probe/mtime_probe_observed.txt`・`probe/seal_s0_s5_at_predictions.md`)。時刻: 予測を固定 2026-10-29 11:16:21 JST、記録の数えの出力 11:27:10 JST、この節はその後に足した。`probe/survey.txt`(11:11:48)・`probe/record_keys.txt`(11:12)・`probe/s1_list.txt`(11:13)は予測の前に作ったが、予測の前に見たのは §0-4 に書いた範囲(file 名・行数・欄の名前)だけで、`survey.txt` の中身(対応付けの行)は予測の後に読んだ。
engine は走らせていない。`~/.cache/audit-core/` の中の file は読んでいない。ただし下調べの終わりの確かめで、誤って `~/.cache/audit-core/` の項目の数を数える command を 1 回走らせた(印字されたのは数 7 だけ。名前・中身は見ていない。依頼文の「読まない」に反する 1 回として残す)。`edinetdb-p27/` は開いていない。`~/Desktop/sgogi-coach-handoff/` は読んでいない。本線の木には書いていない。`/tmp` に file を足していない(TMPDIR と PYTHONPYCACHEPREFIX は probe の下)。席は呼んでいない。
ここの数と判断は下調べのもので、正本は §5 の文書と門が出す。**H-1〜H-16 の当否は文書の段で門が封の字から求め直す。**

### §6-1 39 file の役(code を読んだ判断。§2-1 の単位)

| # | file(`measure/` の下) | 役 | 仕掛け(関数)・使う先 |
|---|---|---|---|
| 1 | `false_pass_2026-10-14.py` | 仕掛け持ち | `run_doc`(id + 値の読み返し) |
| 2 | `false_pass_compare_2026-10-15.py` | 使う側 | 1 の記録を読む |
| 3 | `holdout_p17_pair_2026-10-14.py` | 対象外 | 注入でない(P16 と P17 を同じ書類に当てて鍵で並べる。`run_doc` は同名の別の関数) |
| 4 | `inject.py` | 共通部品 | `select`・`apply_edits`・`revert`・`build_t1`〜`build_t7`。claim への対応付けは持たない |
| 5 | `kokkai_false_pass_2026-10-15.py` | 仕掛け持ち | `run`(要約の claim の値を同じ id のまま書き換える) |
| 6 | `kokkai_inject_2026-10-14.py` | 共通部品 | 議事録の claim を id を保ったまま書き換える。engine を呼ばない(数えは `measure/` の外) |
| 7 | `qwed_compare_2026-10-19.py` | 対象外 | 注入した本文を外の道具(QWED)に渡す。Audit Core 側は記録から写す |
| 8 | `ritual_2026-10-20.py` | 使う側 | 1 の `run_doc` |
| 9 | `tests/test_inject.py` | 対象外 | 試験 file |
| 10 | `xbrl_a_core_vs_grep_2026-10-17.py` | 仕掛け持ち | `claim_for`・`run_doc`(値と後の字 → 値だけ) |
| 11 | `xbrl_attr_inject_2026-10-17.py` | 仕掛け持ち | `main`(足した fact の鍵を `verify_external` の pointers に直に渡す) |
| 12 | `xbrl_branch_a_2026-10-17.py` | 対象外 | 注入した本文で engine の実行行を trace する診断。結果を claim に対応付けて数えない |
| 13 | `xbrl_cd_material_2026-10-17.py` | 仕掛け持ち | `main` の行 → claim(値が許容差の内側 かつ 数の字面が span に在る、の最初の 1 件) |
| 14 | `xbrl_contract_v1_2026-10-17.py` | 仕掛け持ち + 使う側 | `main` の B′(行の値と席の参照先を `verify_external` に直に渡す)。B は 34 の記録を読む |
| 15 | `xbrl_default_p26_2026-10-23.py` | 使う側 | 30 の `inject_with_profile`・`core_say_for` |
| 16 | `xbrl_default_p27_2026-10-28.py` | 使う側 | 30 の `inject_with_profile`・`core_say_for` |
| 17 | `xbrl_dim_diag_2026-10-17.py` | 対象外 | 注入した本文から行と fact を作り直して読むだけ。注入の結果を数えない |
| 18 | `xbrl_dim_hold_2026-10-17.py` | 仕掛け持ち | `main`(行の値と席の参照先を `verify_external` に直に渡す) |
| 19 | `xbrl_fresh_2026-10-21.py` | 仕掛け持ち | `_find_base_claim`・`inject_doc`(注入後は 10 の `claim_for`) |
| 20 | `xbrl_gen_c1_2026-10-20.py` | 仕掛け持ち + 使う側 | `engine_stage`(行の値を `verify_external` に直に渡す)。材料は 13 の `MB.main` を入出力だけ替えて回す |
| 21 | `xbrl_gen_c_2026-10-20.py` | 使う側 | 10 の `run_doc`・`claim_for`(Recorder でかぶせる) |
| 22 | `xbrl_holds_product_path_2026-10-19.py` | 仕掛け持ち | `f4_f5_f6`(行の値と参照先を `verify_external` に直に渡す) |
| 23 | `xbrl_hybrid_s2_2026-10-20.py` | 使う側 | 13 の `MB.main`(注入の型の選び方だけ替える)と材料の Core 欄 |
| 24 | `xbrl_inject_reach_2026-10-28.py` | 仕掛け持ち | 診断(値で引き、文の番号と位置で届いたかを数える) |
| 25 | `xbrl_lastbranch_2026-10-21.py` | 仕掛け持ち + 使う側 | `injections_doc`(文の番号と文の中の位置で claim を引き、値を読み返す)。30 の `inject_with_profile`・`e4` |
| 26 | `xbrl_p20_rerun_2026-10-17.py` | 仕掛け持ち | `claim_of`(13 と同じ対応付けの写し) |
| 27 | `xbrl_p27_eval_2026-10-27.py` | 使う側 | 28 の `inject_doc`・`claim_for_p27`・`classify` |
| 28 | `xbrl_p27_tune_2026-10-27.py` | 仕掛け持ち | `find_base_claim`・`base_status`・`claim_for_p27`・`classify`・`inject_doc`(値を円に直して引く) |
| 29 | `xbrl_p27_tune_rerun_2026-10-27.py` | 使う側 | 28 の `inject_doc`(profile を 4 つに) |
| 30 | `xbrl_period_bind_2026-10-20.py` | 仕掛け持ち(2) | `inject_with_profile`(id + 値の読み返し)と `core_say_for`(E-4。13 と同じ対応付けの写し) |
| 31 | `xbrl_period_unit_hold_2026-10-19.py` | 仕掛け持ち | `main`(行の値と席の参照先を `verify_external` に直に渡す) |
| 32 | `xbrl_pnf_diag_2026-10-17.py` | 仕掛け持ち | `main` の行 → claim(13 と同じ対応付けの写し) |
| 33 | `xbrl_point_prior_2026-10-20.py` | 仕掛け持ち | `inject_doc`(id + 値の読み返し) |
| 34 | `xbrl_role_swap_2026-10-17.py` | 仕掛け持ち | `main` の行 → recipe の claim(13 と同じ対応付けの写し) |
| 35 | `xbrl_rounding_2026-10-21.py` | 使う側 | 30 の `inject_with_profile`・`e4` |
| 36 | `xbrl_rowclaim_map_2026-10-17.py` | 仕掛け持ち | `claim_of`(13 と同じ対応付けの写しで、1 対 1 かを数える) |
| 37 | `xbrl_t2_pass_diag_2026-10-28.py` | 仕掛け持ち | 診断(値で引き、文の番号で届いたかを数える) |
| 38 | `xbrl_verify_inventory_2026-10-17.py` | 仕掛け持ち | `main` の行 → recipe の claim(13 と同じ対応付けの写し) |
| 39 | `xbrl_vocab_2026-10-21.py` | 仕掛け持ち + 使う側 | `injections`(文の番号と位置で claim を引き、値を読み返す)。30 の `inject_with_profile`・`e4` |

数: 仕掛け持ち 23 file(30 は 2 つ持つので**仕掛け 24**)、使う側だけ 9、共通部品 2、対象外 5。

### §6-2 仕掛けの表(§2-2 の列。根拠は関数の中の字)

**届いたことの確かめ 有(7)** ― 数えた claim が差し替えを持たない行を、数えない語に落とす:

| 仕掛け | 基準 | 注入後 | 確かめの字(要旨) | 記録に残る届かなかった行 |
|---|---|---|---|---|
| `false_pass` `run_doc` | site の id(engine と同じ順で文の数を数え、id の値が engine と合わない site は除く) | 同じ id | 値が期待と違えば `id_shift`、id が無ければ `missing`、文が見つからなければ `sentence_not_found` | p17 の 6 記録(行 203〜746)で 3 語とも 0。儀式の 4 記録(行 240〜243)で 3 語とも 0 |
| `point_prior` `inject_doc` | site の id(同上) | 同じ id | 同上(`結果の細目` に書く) | 485 行で `id_shift` 1・`sentence_not_found` 1・`missing` 0 |
| `period_bind` `inject_with_profile` | 同上 | 同じ id | 同上(profile の欄の `state` に書く) | E1 485 行で 2 profile とも `id_shift` 1・`sentence_not_found` 1。使う側の `rounding` R3・`vocab` W4・`lastbranch` L4・`p26` Q3 も同じ 2 行(各 2 profile)。`default_p27` の S6 は行を持たず「その他 5」(内訳は記録から言えない) |
| `lastbranch` `injections_doc` | 動いた行の文の番号と文の中の位置 | 同じ文の番号・位置の claim を引き、値を読み返す | 位置の claim が無ければ「主張が見つからない」、値が違えば「値がずれた」 | L7 1,154 行で 2 profile とも 主張が見つからない 20・値がずれた 16 |
| `vocab` `injections` | 同上 | 同上 | 同上 | W6 695 行で 0 |
| `t2_pass_diag` | 値(`_find_base_claim` と同じ) | 値(`claim_for` と同じ) | engine の文の一覧の差で token の文を決め、基準の claim の文と比べる | 前の便の記録(5 行) |
| `inject_reach` | 同上 | 同上 | 同上(届いた(文)・届いた(数)) | 前の便の記録(741 行。届かない 5) |

**確かめ 無 = 「同じ型」(10)** ― 値(と字の部分文字列)で claim を引き、差し替えた token の場所の claim かを確かめない:

| 仕掛け | 基準 | 注入後 | 記録の数(対応付けの数でありうるもの) |
|---|---|---|---|
| `a_core_vs_grep` `claim_for` | なし | 値と後の字 → 値だけ(T3 は span の先頭 20 字が挿入文の中) | cd8 142 行(対応が付いた 123・付かない 19)。使う側 `gen_c` C0-2 128 行(付いた 104・付かない 24) |
| `fresh` `_find_base_claim`・`inject_doc` | 値と元の字 → 値だけ(無改変の P22) | `claim_for` | 通した 5 / 741(前の 2 便で、5 行とも届いていない = 対応付けの数と診断済み) |
| `p27_tune` `find_base_claim`・`claim_for_p27`・`classify` | 値(円に直す)と書かれた字 → 値だけ(P22。P26 で同じ claim が同じ値・span・unit) | 値(円に直す)と後の字 → 値だけ。**注入後の claim の id が基準の id と同じかを見ない**(`classify` は基準の claim と pointers・recomputed を比べるだけ) | 評価用 96 行: 通した P22 27・P26 27・P27 0・P27E 0、名指したが別の値 7・5・5・7、対応が付かない 2(各 profile)。調整用 101 行: 通した 28・28、名指したが別の値 4・4、対応が付かない 3。調整用 P27: 通した P27 0・P27E 0、名指したが別の値 7・9 |
| `cd_material` `main` の行 → claim | ― | 値が許容差の内側 かつ 数の字面が span に在る、の**最初の 1 件**(1 件に決まるかも見ない) | 材料の Core 欄 192 行(注入 64)。同じ対応付けの写しで数えた記録(`rowclaim_map`): 対応が付かない 51・複数の行が張り付いた行 36(主張 12)、T5 50 行のうち 1 対 1 26・共有 24 |
| `p20_rerun` `claim_of` | ― | 同上の写し | (記録の行は Core 欄の P16・P20) |
| `rowclaim_map` `claim_of` | ― | 同上の写し(1 対 1 かは数えるが、位置は見ない) | 上の数(2026-10-17 の記録に「器の欠陥」「対応付けを直していない。直すのは別便(span の位置で決める等)」と書かれている) |
| `role_swap` `main` | ― | 同上の写し(recipe の claim の span) | B の最終判定(使う側 `contract_v1` が読む) |
| `verify_inventory` `main` | ― | 同上の写し | 「Core に主張が無い」ほか |
| `pnf_diag` `main` | ― | 同上の写し | 診断の行 |
| `period_bind` `core_say_for`(E-4) | ― | 同上の写し | 段 2 の材料 192 行・注入 64。`default_p27` S6 の「全注入で Core 自身(既定)が GROUNDED 0 / 64」はこの対応付けの数 |

**確かめ 不要(7)** ― 差し替えた値・鍵をそのまま検査に渡す(数える行は位置で決まる、または claim そのものを書き換える): `kokkai_false_pass` `run`(49 行・通した 1)、`attr_inject` `main`(24 行・無効 0)、`contract_v1` の B′、`dim_hold` `main`、`period_unit_hold` `main`、`holds_product_path` `f4_f5_f6`、`gen_c1` `engine_stage`。これらの行は `cd_material` の `build_rows`(本文の数の token の並び。注入の行は token の位置が差し替えの位置に重なるかで決める)から来るので、行と注入の対応は位置で決まっている。

### §6-3 下調べの時点の当否の見立て(門が文書の段で求め直す)

| # | 見立て | 理由(§6-1・§6-2 の数) |
|---|---|---|
| H-1 | **外れ** | 仕掛け 24(幅 8〜13 の上) |
| H-2 | **外れ** | 有 7(幅 2〜5 の上) |
| H-3 | **外れ** | 無 10(幅 3〜6 の上) |
| H-4 | **外れ** | 不要 7(幅 1〜3 の上) |
| H-5 | **外れ** | 同じ型 10(幅 3〜5 の上)。`fresh` と `p27_tune` の両方は入る |
| H-6 | 当たり | id で引く 3 つ(`false_pass`・`point_prior`・`period_bind` の `inject_with_profile`)は全部、値の読み返しを持つ |
| H-7 | **外れ** | 数は `id_shift` 1・`sentence_not_found` 1 で幅の中だが、`period_bind` の行にその名の**欄は無い**(語は profile の欄の `state` の値。`point_prior` は `結果の細目` の値)。外れ方の字「欄が行に無い」に当たる |
| H-8 | **外れ** | P21 の記録(`ritual_2026-10-20_p21.json`)で 2(他の 3 本は 0)。「参照先が動いた」は engine の pointers が注入の前後で違う数で、対応付けの数ではない(同じ id を値で読み返した行) |
| H-9 | 当たり | 3 本とも行の欄は `docID`・`id`・`型`・`文体`・`基準の claim`・profile ごとの `対応`・`結果`・`state`・`reason` だけ |
| H-10 | 当たり | 評価用の名指したが別の値: P22 7・P26 5・P27 5。P26 と P27 の両方 5・一方だけ 0 |
| H-11 | 当たり | T1_VALUE の基準に対応が付かない 7 / 採った 24 = 29.2% |
| H-12 | **外れ** | §2-4 の規準で 42 行(記録の path だけで数えると 37 行)。幅 6〜15 の上 |
| H-13 | **外れ** | 対象外 5(幅 12〜22 の下) |
| H-14 | 当たり | `kokkai_false_pass` は不要、`kokkai_inject` は共通部品(値で引かない) |
| H-15 | **外れ** | 不要(足した fact の鍵を pointers に直に渡す。claim を引かない) |
| H-16 | 当たり | 同じ型。同じ対応付けの写しが他に 6(`p20_rerun`・`rowclaim_map`・`role_swap`・`verify_inventory`・`pnf_diag`・`period_bind` の `core_say_for`) |

見立ての向き: 外れ 10・当たり 6。H-1〜H-5・H-12・H-13 の外れは同じ向き(**仕掛けの数・写しの数・使う側・台帳の依存を少なく見た**)。cd8(2026-10-17)の対応付けが 6 か所に写されていることを、予測の前には 1 か所(`cd_material`)しか見ていなかった偏り。H-7・H-8・H-15 は別の向き(欄の名から作りを推した外れ。§3 の注のとおり)。

### §6-4 下調べで分かったこと(文書の判定の材料。記録は書き換えない)

1. **前期比の注入(穴 B の 485 行。`point_prior` → `period_bind` → `rounding`・`vocab`・`lastbranch`・`p26`・`default_p26`・`default_p27`)と儀式(`false_pass` の `run_doc`)は、前の 2 便と同じ穴ではない。** site は engine と同じ順で文の数を数えて id を付け、注入後は同じ id の claim の値を差し替え後の値と読み返し、合わなければ `id_shift` にして通した・止めたのどちらにも数えない。記録に残る届かなかった行は、485 行の側で `id_shift` 1・`sentence_not_found` 1(同じ 2 行が各 profile で)、儀式の側で 0。
2. **単位の注入(新しい標本の T2_UNIT)は診断済み。** 属性の注入(`attr_inject`・`period_unit_hold`・`holds_product_path`・`dim_hold`)は、差し替えた fact の鍵か行の値をそのまま検査に渡す作りで、対応付けを持たない(不要)。
3. **同じ型(値で引き、届いたかを確かめない)は 3 つの系統に 10 か所。** (ア) 新しい標本(`fresh`。診断済み)、(イ) 評価用・調整用(`p27_tune` と使う側 2)、(ウ) cd8 の行 → claim(`cd_material` とその写し 6、`a_core_vs_grep` の `claim_for`)。(ウ) の対応付けが多対一になることは 2026-10-17 の `rowclaim_map` の記録が既に数えていて(張り付いた行 36 / 192)、その記録は「直すのは別便(span の位置で決める等)」と書いたまま、同じ対応付けが `period_bind` の `core_say_for`(2026-10-20)まで写された。前の 2 便の穴(2026-10-21 の `fresh`)は、この写しの系譜とは別に、`a_core_vs_grep` の `claim_for`(値だけへの落とし込み)を使った。
4. **(イ) 評価用・調整用は、記録から届いたかを言えない。** 行は基準の claim の id を持つが、注入後に数えた claim の id を持たない。`classify` は注入後の claim と基準の claim の id が同じかを見ない。新しい値は refs のどの値とも違うように選び、値は円に直して比べる(だから、注入後の claim が差し替えた token を読んでいない行は「対応が付かない」に落ちやすい)という違いはあるが、それは「届いた」の確かめではない。評価用の 通した P22 27・P26 27 と、名指したが別の値(P22 7・P26 5・P27 5・P27E 7)、調整用の 通した 28・28 と 名指したが別の値 4・4・7・9 は、**記録の欄では engine の数か対応付けの数かを分けられない**。
5. **台帳の依存。** §2-4 の規準で 42 行(L-14〜L-18・L-28〜L-34・L-36〜L-38・D-05・D-09〜D-13・D-21〜D-23・D-25・D-26・H-01・H-09・H-12〜H-14・P-02・P-03・P-09・P-14〜P-21)。記録の path だけで数えると 37 行。規準は file 名の字で粗く当てるので、同じ記録の無改変の数・読みの数を引く行も入る(例: 無改変の 40 書類の行、読み手の偏りの行)。どの行の数が対応付けを通った数かは、文書の段で行ごとに読み分ける(§6-5 の 3)。
6. **規準の外の file。** §4 の 3 の副産物の検査(規準に当たらず、`verify_document(`・`verify_external(` を呼び、本文の差し替えの字を持つ file)で 6 file: `xbrl_p26_2026-10-21.py`(**仕掛けを持つ**: `diff_pm1_doc` は同じ id の claim の span が無改変と違うかで確かめる = 有。Q-4 は `lastbranch` の `injections_doc` の使う側。記録 Q4 388 行で 数が見つからない 46・主張が見つからない 6・値がずれた P25 12 / P26 18、Q5 1,095 行で 主張が見つからない 27)、`xbrl_gen_c_alpha_2026-10-20.py`(`engine_item` = 不要。材料の Core 欄の使う側)、`xbrl_period_pair_stage2_2026-10-19.py`(不要)、`xbrl_naming_fix_2026-10-20.py`(`a_core_vs_grep` の `main` の使う側)、`xbrl_customer_report_2026-10-21.py`・`xbrl_customer_report_fix_2026-10-21.py`(注入でない。`replace(` は字の整え)。ほかに code を読んで見つけた使う側(規準にも副産物の検査にも当たらない): `xbrl_cd_score_2026-10-17.py`・`xbrl_cd_ceiling_2026-10-17.py`・`xbrl_hybrid_trust_2026-10-20.py`・`xbrl_gen_c_p20_2026-10-20.py`・`xbrl_p20_pred_recheck_2026-10-17.py`。`fixtures/**/*.py` 53 file は規準に 0。
7. 議事録の注入(`kokkai_inject`)の結果を数える所は `measure/` に無い(記録 `out_injected_*` は engine の出力、数えは結果文書の側)。この便では確かめていない。

### §6-5 追記(2026-10-29、下調べの後。§2・§5 の仕様の補い。§3 の字は変えない)

1. **§2-3 の 1 の欄の名の補い。** `period_bind` の行に `id_shift`・`sentence_not_found` の欄は無い。語は profile の欄の `state` の値(`point_prior` は `結果の細目` の値)。門は「profile の欄の `state`(または `結果の細目`)が `id_shift`・`sentence_not_found`・`missing` の行」で数える。H-7 の当否は封の字のまま(外れ方「欄が行に無い」に当たる)。
2. **不要の単位の補い。** 「行の値・fact の鍵をそのまま `verify_external` に渡す」作りは、§2-1 の「出力から数える claim を 1 つ決める」に字どおりは当たらない(選ぶ所が無い)が、注入した入力で engine を走らせて行ごとに数えるので、仕掛け(届いたことの確かめ 不要)に数えた。文書もこの読みで書き、表に「選ぶ所が無い」と注記する。
3. **台帳の依存の読み分け。** §2-4 の規準の 42 行は粗い。文書は、行ごとに「数が同じ型の対応付けを通ったか」(通った / 通っていない / 記録から分からない)を読んで分け、読みの根拠(行の欄の字と 印 の欄)を書く。門 (c) は規準の 42 行の集合を見て、読み分けは監査が読み直す。
4. **規準の外の file**(§6-4 の 6)は、§1-2 の 39 の表と門 (a) には入れない(規準は変えない)。文書は別の表で「規準の外で見つかった仕掛けと使う側」を書き、使う側の列と台帳の依存の規準にはそれらの file 名を入れる。規準そのものを広げるかは次の封で決める。
5. **次に測ること(文書の「次に測ること」に書く。この便では測らない):**
   - (ウ) cd8 の系統: 材料は手元の cache の 8 書類(`~/.cache/audit-core/edinet/`)で 0 USD で作り直せる。行 → claim を位置(engine の文の番号と文の中の位置)で引き直し、値と字の最初の 1 件で引いた claim と同じかを行ごとに数える。記録に持てる欄: 行の id・token の位置・位置で引いた claim の id・値で引いた claim の id・同じか・文の番号。
   - (イ) 評価用・調整用: 文は repo の外(`~/.cache/audit-core/edinetdb-p27/`)にあり、開くかは人間が決める。記録に持てる欄: 注入後に数えた claim の id と基準の claim の id が同じか・engine の文の一覧の番号(token の文・基準の claim の文)・文の中の位置・届いた(文)/届いた(数)・分類 6 語・対応の付け方(値と字 / 値だけ)。持てない欄: 文の抜粋・span・subject・value・recomputed(`p27_tune` が repo の記録に入れない欄と同じ)と、docID と文の対応を外から引ける字。いちばん安い 1 欄は「注入後の claim の id が基準の id と同じか」(文を repo に出さずに持てる)。
   - `a_core_vs_grep` の `claim_for`(cd8 142 行・gen_c 128 行): 同じく位置で引き直す。

