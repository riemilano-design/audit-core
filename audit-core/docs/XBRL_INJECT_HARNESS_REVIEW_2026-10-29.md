# 注入の仕掛け(測定の harness)の総点検 ― 結果 2026-10-29

**人間(2026-10-29)「テストハーネスの穴の総点検 ― 今回の手違いと同様のバグが、前期比テストや単位変換テストのスクリプト内に潜んでいないかを網羅的に点検すること。君に任せる」。** 封 `docs/XBRL_INJECT_HARNESS_REVIEW_SEAL_2026-10-29.md`(commit `365b468`)の §5-2 の文書と門。

- 点検だけ。engine(`core/`・`adapters/`)は走らせていない。記録は不変(既存の記録を一字も書き換えていない)。新しい記録 file も script も作っていない。費用なし・通信なし・席(LLM)は呼んでいない。`~/.cache/audit-core/edinetdb-p27/` は開いていない。
- 「前の二便」は、注入 T2 で通した行の診断(`docs/XBRL_T2_PASS_DIAG_2026-10-28.md`)と、注入の全行で差し替えが届いたかを数えた診断(`docs/XBRL_INJECT_REACH_DIAG_2026-10-28.md`)。そこで見つかった穴の型(値と字の部分文字列で claim を引き、引いた claim が差し替えた場所のものかを確かめずに数える)を、`measure/` の他の注入の仕掛けに探した。
- 数は `<!-- 門:start 名前 -->` の中だけにある。門 `tests/measure/test_xbrl_inject_harness_review.py` が、封の規準・既存の記録・この文書の判断の表から表を作り直して一字ずつ照合する。判断(file の役・確かめの有無・台帳の行の読み)は文書の表にあり、門は決まった語・実在・表どうしの整合・関数の中に根拠の字が在ることを見る。判断そのものは code を読む監査が読み直す。
- 門の外の散文は数を持たない。数を持つ行には 【門なし】 を付ける。

## 1. 予測 H-1 から H-16 の当否

封 §3 の予測を、文書の表と記録から門が求め直した当否。予測・外れ方は封の字のまま。**外れは外れのまま残し、封も予測も直さない。**

<!-- 門:start pred -->
| # | 欄 | 予測(封の字のまま) | 外れ方(封の字のまま) | 実測(文書の表と記録から) | 当否 |
|---|---|---|---|---|---|
| **H-1** | 仕掛け(§2-1 の単位)の本数(39 file の中) | **8 以上 13 以下** | 7 以下、または 14 以上 | 仕掛け(表の行)は 24 | **外れ** |
| **H-2** | 届いたことを確かめている仕掛け(有) | **2 以上 5 以下** | 1 以下、または 6 以上 | 確かめ 有は 7 | **外れ** |
| **H-3** | 確かめていない仕掛け(無) | **3 以上 6 以下** | 2 以下、または 7 以上 | 確かめ 無は 10 | **外れ** |
| **H-4** | 確かめが要らない仕掛け(不要) | **1 以上 3 以下** | 0、または 4 以上 | 確かめ 不要は 7 | **外れ** |
| **H-5** | 穴の型が「同じ型」(値で引き、確かめ無し)の仕掛け | **3 以上 5 以下**。その中に `xbrl_fresh_2026-10-21.py` の注入(`inject_doc`)と `xbrl_p27_tune_2026-10-27.py` の注入(`inject_doc`)の両方が入る | 2 以下、6 以上、またはどちらかが入らない | 同じ型は 10(新しい標本の注入 入る・調整用の注入 入る) | **外れ** |
| **H-6** | 基準も注入後も id で引く仕掛け(`false_pass_2026-10-14.py` の `run_doc`、`xbrl_period_bind_2026-10-20.py` の `inject_with_profile` を含む) | **全部が注入後の値の読み返しを持つ(届いたことの確かめ 有)** | 1 本でも 無 | site の id と同じ id で引く仕掛け 3(M-01・M-15・M-19)、そのうち確かめ 無 0 | **当たり** |
| **H-7** | `period_bind_2026-10-20.json` の注入の行で `id_shift` が None でない行・`sentence_not_found` が None でない行 | **どちらも 0 以上 5 以下** | どちらかが 6 以上、または欄が行に無い | period_bind E1 の P22 の state: id_shift 1・sentence_not_found 1、行に id_shift・sentence_not_found の欄: 無い | **外れ** |
| **H-8** | 儀式の記録 4 本の「通した のうち参照先が動いた」 | **4 本とも 0** | どれか 1 本で 1 以上 | 儀式 4 本の『通した のうち参照先が動いた』: 0・2・0・0 | **外れ** |
| **H-9** | 評価用・調整用の記録(`eval_inject`・`tune_inject`・`tune_p27_inject`)の行の欄 | **文の番号・token の位置・届いた/届かないの欄を持たない**(届いたかを記録から数えられない) | どれか 1 本でも持つ | 3 本の行・profile の欄に文の番号・位置・届いた/届かないの欄: 無い | **当たり** |
| **H-10** | 評価用の記録の「名指したが別の値」に当たる分類(在れば。P22・P26・P27 の各 profile) | **各 profile で 1 以上**。P26 と P27 の両方でその分類の行が、どちらか一方だけの行より多い | どれかの profile で 0、または一方だけの行が両方の行以上、またはその分類の語が記録に無い | 評価用『名指したが別の値』: P22 7・P26 5・P27 5、P26 と P27 の両方 5・どちらか一方だけ 0 | **当たり** |
| **H-11** | 評価用の記録の T1_VALUE の「基準に対応が付かない」(書類別の数えの合計) | `採った` の合計の **20% 以上** | 20% 未満 | 評価用 T1_VALUE の基準に対応が付かない 7 / 採った 24 = 29.2% | **当たり** |
| **H-12** | 「同じ型」の仕掛け(と使う側)の記録を引く台帳の行(§2-4 の規準) | **6 以上 15 以下** | 5 以下、または 16 以上 | 同じ型の仕掛け(と使う側)を引く台帳の行は 42 | **外れ** |
| **H-13** | 39 file のうち対象外 | **12 以上 22 以下** | 11 以下、または 23 以上 | 対象外の file は 5 | **外れ** |
| **H-14** | 議事録の 2 本(`kokkai_inject_2026-10-14.py`・`kokkai_false_pass_2026-10-15.py`) | **どちらも「同じ型」でない**(`kokkai_false_pass` は 不要。`kokkai_inject` も値で引かない) | どちらかが「同じ型」 | kokkai_false_pass 無し・kokkai_inject は役 共通部品 | **当たり** |
| **H-15** | `xbrl_attr_inject_2026-10-17.py`(fact の属性を変える) | **穴の型は「別の型」で、届いたことの確かめは 有**(注入後の claim を id で引き、変えた fact を pointers が指すかを見る) | 「同じ型」、確かめ 無、または 不要 | attr_inject: 穴の型 無し・確かめ 不要 | **外れ** |
| **H-16** | cd8 の材料の行 → claim の対応(`xbrl_cd_material_2026-10-17.py` の行の対応付け) | **「同じ型」**(値と字の最初の 1 件で、届いたことの確かめ無し)。同じ対応付けを写した、または import した file が他に **1 以上**在る | 「同じ型」でない、または他に 0 | cd_material: 穴の型 同じ型・確かめ 無、同じ対応付けを持つ他の file 6 | **当たり** |
<!-- 門:end -->

外れた予測: H-1・H-2・H-3・H-4・H-5・H-7・H-8・H-12・H-13・H-15。外れは外れのまま残す(封も予測も直さない)。【門なし】

当たった予測: H-6・H-9・H-10・H-11・H-14・H-16。【門なし】

外れの向き: 仕掛けの本数・確かめの内訳・同じ型の本数・対象外の file の本数・台帳の依存の行の数(H-1 から H-5・H-12・H-13)は、封の幅より多く(対象外は少なく)出た。封を書いた席は、仕掛けの本数・cd8 の対応付けの写し・使う側・台帳の依存を少なく見た(同じ向き)。別の向きの外れは H-7・H-8・H-15 で、欄の名(`id_shift`)や『確かめの有無』から作りを推したことによる。

- H-7: 数は幅の中だが、`period_bind` の行に `id_shift`・`sentence_not_found` の欄は無い(語は profile の欄の `state` の値)。外れ方の字『欄が行に無い』に当たる。封 §6-5 の 1 のとおり、当否は封の字のまま。
- H-8: 儀式の記録の一本(P21)で『通した のうち参照先が動いた』が 0 でない。これは engine の pointers が注入の前後で違う行の数で、対応付けの数ではない(同じ id を値で読み返した行)。
- H-15: `attr_inject` は fact の鍵を検査に直に渡す作りで、claim を引かない。穴の型は無し・確かめは不要。

## 2. 列挙(規準と file の役)

規準(封 §1-1。字の部分一致。門が封の字から読む): `measure/**/*.py` の本文に封の七つの呼び出しの字のどれかが在る、または file 名に `inject`・`false_pass` が在る。`measure/tests/`・`measure/lib/` を含む。`fixtures/**/*.py`・`tests/**`・`scratchpad/` は母集団の外(`fixtures/**/*.py` に同じ規準を当てた数は表 summary)。

役の語: **仕掛け持ち**(注入した入力で engine を走らせた出力から、数える claim または行を決める実装を持つ)・**使う側**(仕掛けを import して呼ぶ、または仕掛けの記録を読む)・**共通部品**(注入の入力を作るだけで claim への対応付けを持たない)・**対象外**(注入でない、注入した本文を外の道具や席に渡すだけ、試験 file)。仕掛けは file でなく関数で数える(一つの file が持つ仕掛けの数は零以上)。

<!-- 門:start files -->
| # | path | 行数 | (a) で当たった字 | (b) | 役 | 仕掛け(関数)・使う先 |
|---|---|---|---|---|---|---|
| 1 | `measure/false_pass_2026-10-14.py` | 231 | `run_doc(`・`mutate(` | 名 | 仕掛け持ち | `run_doc`(id + 値の読み返し) |
| 2 | `measure/false_pass_compare_2026-10-15.py` | 277 | ― | 名 | 使う側 | 上の記録を読む |
| 3 | `measure/holdout_p17_pair_2026-10-14.py` | 176 | `run_doc(` | ― | 対象外 | 注入でない(P16 と P17 を同じ書類に当てて鍵で並べる。`run_doc` は同名の別の関数) |
| 4 | `measure/inject.py` | 710 | `apply_edits(` | 名 | 共通部品 | `select`・`apply_edits`・`revert`・`build_t1` から `build_t7`。claim への対応付けは持たない |
| 5 | `measure/kokkai_false_pass_2026-10-15.py` | 172 | ― | 名 | 仕掛け持ち | `run`(要約の claim の値を同じ id のまま書き換える) |
| 6 | `measure/kokkai_inject_2026-10-14.py` | 144 | `inject(` | 名 | 共通部品 | 議事録の claim を id を保ったまま書き換える。engine を呼ばない(数えは `measure/` の外) |
| 7 | `measure/qwed_compare_2026-10-19.py` | 1053 | `apply_edits(` | ― | 対象外 | 注入した本文を外の道具(QWED)に渡す。Audit Core 側は記録から写す |
| 8 | `measure/ritual_2026-10-20.py` | 323 | `run_doc(` | ― | 使う側 | `false_pass` の `run_doc` を呼ぶ |
| 9 | `measure/tests/test_inject.py` | 1427 | `apply_edits(` | 名 | 対象外 | 試験 file |
| 10 | `measure/xbrl_a_core_vs_grep_2026-10-17.py` | 359 | `apply_edits(`・`run_doc(`・`IJ.select(` | ― | 仕掛け持ち | `claim_for`(値と後の字 → 値だけ)・`run_doc` |
| 11 | `measure/xbrl_attr_inject_2026-10-17.py` | 319 | `apply_edits(`・`inject(` | 名 | 仕掛け持ち | `main`(足した fact の鍵を `verify_external` の pointers に直に渡す) |
| 12 | `measure/xbrl_branch_a_2026-10-17.py` | 228 | `apply_edits(` | ― | 対象外 | 注入した本文で engine の実行行を trace する診断。結果を claim に対応付けて数えない |
| 13 | `measure/xbrl_cd_material_2026-10-17.py` | 307 | `apply_edits(`・`IJ.select(` | ― | 仕掛け持ち | `main` の行 → claim(値が許容差の内側 かつ 数の字面が span に在る、の最初の 1 件) |
| 14 | `measure/xbrl_contract_v1_2026-10-17.py` | 262 | `apply_edits(` | ― | 仕掛け持ち + 使う側 | `main` の B′(行の値と席の参照先を `verify_external` に直に渡す)。B は role_swap の記録を読む |
| 15 | `measure/xbrl_default_p26_2026-10-23.py` | 614 | `inject_with_profile(` | ― | 使う側 | period_bind の `inject_with_profile`・`core_say_for` |
| 16 | `measure/xbrl_default_p27_2026-10-28.py` | 683 | `inject_with_profile(` | ― | 使う側 | period_bind の `inject_with_profile`・`core_say_for` |
| 17 | `measure/xbrl_dim_diag_2026-10-17.py` | 294 | `apply_edits(` | ― | 対象外 | 注入した本文から行と fact を作り直して読むだけ。注入の結果を数えない |
| 18 | `measure/xbrl_dim_hold_2026-10-17.py` | 342 | `apply_edits(`・`inject(` | ― | 仕掛け持ち | `main`(行の値と席の参照先を `verify_external` に直に渡す) |
| 19 | `measure/xbrl_fresh_2026-10-21.py` | 551 | `apply_edits(`・`IJ.select(`・`inject(`・`inject_doc(` | ― | 仕掛け持ち | `_find_base_claim`・`inject_doc`(注入後は a_core_vs_grep の `claim_for`) |
| 20 | `measure/xbrl_gen_c1_2026-10-20.py` | 820 | `apply_edits(` | ― | 仕掛け持ち + 使う側 | `engine_stage`(行の値を `verify_external` に直に渡す)。材料は cd_material の `main` を入出力だけ替えて回す |
| 21 | `measure/xbrl_gen_c_2026-10-20.py` | 757 | `apply_edits(`・`run_doc(` | ― | 使う側 | a_core_vs_grep の `run_doc`・`claim_for`(Recorder でかぶせる) |
| 22 | `measure/xbrl_holds_product_path_2026-10-19.py` | 464 | `apply_edits(`・`inject(` | ― | 仕掛け持ち | `f4_f5_f6`(行の値と参照先を `verify_external` に直に渡す) |
| 23 | `measure/xbrl_hybrid_s2_2026-10-20.py` | 882 | `apply_edits(`・`IJ.select(` | ― | 使う側 | cd_material の `main`(注入の型の選び方だけ替える)と材料の Core 欄 |
| 24 | `measure/xbrl_inject_reach_2026-10-28.py` | 431 | `apply_edits(`・`IJ.select(` | 名 | 仕掛け持ち | 診断(値で引き、文の番号と位置で届いたかを数える) |
| 25 | `measure/xbrl_lastbranch_2026-10-21.py` | 1051 | `inject_with_profile(` | ― | 仕掛け持ち + 使う側 | `injections_doc`(文の番号と文の中の位置で claim を引き、値を読み返す)。period_bind の `inject_with_profile`・`e4` を使う |
| 26 | `measure/xbrl_p20_rerun_2026-10-17.py` | 313 | `apply_edits(` | ― | 仕掛け持ち | `claim_of`(cd_material と同じ対応付けの写し) |
| 27 | `measure/xbrl_p27_eval_2026-10-27.py` | 665 | `inject(` | ― | 使う側 | p27_tune の `inject_doc`・`claim_for_p27`・`classify` |
| 28 | `measure/xbrl_p27_tune_2026-10-27.py` | 1076 | `apply_edits(`・`IJ.select(`・`inject(`・`inject_doc(` | ― | 仕掛け持ち | `find_base_claim`・`base_status`・`claim_for_p27`・`classify`・`inject_doc`(値を円に直して引く) |
| 29 | `measure/xbrl_p27_tune_rerun_2026-10-27.py` | 225 | `inject(` | ― | 使う側 | p27_tune の `inject_doc`(profile を 4 つに) |
| 30 | `measure/xbrl_period_bind_2026-10-20.py` | 925 | `inject_with_profile(` | ― | 仕掛け持ち | 2 つ持つ: `inject_with_profile`(id + 値の読み返し)と `core_say_for`(E-4。cd_material と同じ対応付けの写し) |
| 31 | `measure/xbrl_period_unit_hold_2026-10-19.py` | 262 | `apply_edits(`・`inject(` | ― | 仕掛け持ち | `main`(行の値と席の参照先を `verify_external` に直に渡す) |
| 32 | `measure/xbrl_pnf_diag_2026-10-17.py` | 349 | `apply_edits(` | ― | 仕掛け持ち | `main` の行 → claim(cd_material と同じ対応付けの写し) |
| 33 | `measure/xbrl_point_prior_2026-10-20.py` | 624 | `inject_doc(` | ― | 仕掛け持ち | `inject_doc`(id + 値の読み返し) |
| 34 | `measure/xbrl_role_swap_2026-10-17.py` | 298 | `apply_edits(` | ― | 仕掛け持ち | `main` の行 → recipe の claim(cd_material と同じ対応付けの写し) |
| 35 | `measure/xbrl_rounding_2026-10-21.py` | 584 | `inject_with_profile(` | ― | 使う側 | period_bind の `inject_with_profile`・`e4` |
| 36 | `measure/xbrl_rowclaim_map_2026-10-17.py` | 165 | `apply_edits(` | ― | 仕掛け持ち | `claim_of`(cd_material と同じ対応付けの写しで、1 対 1 かを数える) |
| 37 | `measure/xbrl_t2_pass_diag_2026-10-28.py` | 404 | `apply_edits(`・`IJ.select(` | ― | 仕掛け持ち | 診断(値で引き、文の番号で届いたかを数える) |
| 38 | `measure/xbrl_verify_inventory_2026-10-17.py` | 278 | `apply_edits(` | ― | 仕掛け持ち | `part2` の行 → recipe の claim(cd_material と同じ対応付けの写し) |
| 39 | `measure/xbrl_vocab_2026-10-21.py` | 843 | `inject_with_profile(` | ― | 仕掛け持ち + 使う側 | `injections`(文の番号と位置で claim を引き、値を読み返す)。period_bind の `inject_with_profile`・`e4` を使う |
<!-- 門:end -->

### 規準の外で見つかった仕掛けと使う側(別の表)

封 §6-5 の 4 のとおり、規準に当たらない file は上の表と門 (a) に入れない(規準は変えない)。封 §4 の 3 の副産物の検査(規準に当たらず、`verify_document(`・`verify_external(` を呼び、本文の差し替えの字を持つ file)で見つかった file と、code を読んで見つけた使う側を別の表に書く。『本文の差し替えの字』は封の `replace(`・`tampered` に、字 `注入` を足して数えた(封にない判断)。使う側の列と台帳の依存の規準には、これらの file 名を入れた。規準を広げるかは次の封で決める。

<!-- 門:start outside -->
| path | 呼んでいる検査 | 本文の差し替えの字 | 役 | 注 |
|---|---|---|---|---|
| `measure/xbrl_customer_report_2026-10-21.py` | `verify_document(` | `replace(` | 注入でない | `replace(` は字の整え |
| `measure/xbrl_customer_report_fix_2026-10-21.py` | `verify_document(` | `replace(` | 注入でない | `replace(` は字の整え |
| `measure/xbrl_gen_c_alpha_2026-10-20.py` | `verify_external(` | `注入` | 使う側(不要) | `engine_item` は席の参照先を `verify_external` に直に渡す。材料の Core 欄(M-05)の使う側 |
| `measure/xbrl_naming_fix_2026-10-20.py` | `verify_document(` | `replace(`・`注入` | 使う側 | gen_c_p20 を経て a_core_vs_grep の `claim_for`(M-03)を使う側 |
| `measure/xbrl_p26_2026-10-21.py` | `verify_document(` | `replace(`・`注入` | 仕掛けを持つ(有。規準の外なので仕掛けの本数に数えない)+ 使う側 | `diff_pm1_doc` は同じ id の claim の span が無改変と違うかで確かめる。Q-4 は M-12 の使う側 |
| `measure/xbrl_period_pair_stage2_2026-10-19.py` | `verify_external(` | `注入` | 不要 | `verify_external` に直に渡す。材料の使う側 |
| `measure/xbrl_cd_score_2026-10-17.py` | ― | ― | 使う側 | 規準にも副産物の検査にも当たらない。材料の記録を読む(M-05) |
| `measure/xbrl_cd_ceiling_2026-10-17.py` | ― | ― | 使う側 | 同上(M-05) |
| `measure/xbrl_hybrid_trust_2026-10-20.py` | ― | ― | 使う側 | 同上(M-05) |
| `measure/xbrl_gen_c_p20_2026-10-20.py` | ― | ― | 使う側 | 同上(M-03) |
| `measure/xbrl_p20_pred_recheck_2026-10-17.py` | ― | ― | 使う側 | 同上(M-13) |
<!-- 門:end -->

## 3. 仕掛けの表

一行が一つの仕掛け(関数で数える)。列は封 §2-2。語は次の決まった語で始め、` ― ` の後ろに注を書く。

- 届いたことの確かめ: **有**(数える claim が差し替えを持つことを code が確かめ、持たない行を数えない欄に落とす)・**無**・**不要**(差し替えが数える claim そのものに入る作り、または値・鍵を検査にそのまま渡す作りで、別の claim を指しようがない)。
- 穴の型: **同じ型**(値と字の部分文字列で claim を引き、確かめ無し)・**別の型**・**無し**。確かめが有なら同じ型にならず、確かめが無なら同じ型である(門が見る)。
- 不要の単位: 『行の値・fact の鍵をそのまま `verify_external` に渡す』作りは、封 §2-1 の『出力から数える claim を一つ決める』に字どおりは当たらない(選ぶ所が無い)が、注入した入力で engine を走らせて行ごとに数えるので仕掛けに数えた(封 §6-5 の 2。表に『選ぶ所が無い』ことを注記)。これらの行は cd_material の `build_rows`(本文の数の token の並び。注入の行は token の位置が差し替えの位置に重なるかで決める)から来るので、行と注入の対応は位置で決まっている。
- 基準の対応付け・注入後の対応付け・注入の対象の語は、封 §2-2 の列挙に、文の番号と位置で引く作り(`位置(文の番号と文の中の位置)`)と、本文の字と fact の属性の両方を触る作り(`本文の字・fact の属性`)を足した(封にない判断)。
- 『記録に残る届かなかった行』は、記録の欄の語のまま、記録から門が数えた(K の番号の行は §4 の表 reach)。欄が無い記録では『記録に該当の欄なし』と書き、0 とは書かない。

<!-- 門:start mech -->
| ID | 仕掛け(file) | 関数 | 役 | 注入の対象 | 基準の対応付け | 注入後の対応付け | 届いたことの確かめ | 穴の型 | 記録に残る届かなかった行 |
|---|---|---|---|---|---|---|---|---|---|
| M-01 | `measure/false_pass_2026-10-14.py` | `run_doc` | 仕掛け持ち | 本文の字 | site の id ― 文の数を engine と同じ順で数えて id を付け、id の値が engine と合わない site は除く | 同じ id(値の読み返しあり) ― 同じ id の claim の値が期待と違えば id_shift、claim が無ければ missing、文が見つからなければ sentence_not_found | 有 | 無し | 373 行で id_shift 0・sentence_not_found 0・missing 0・unmutable 0(K-12・K-13・K-14・K-15・K-16・K-17・K-18・K-19・K-20・K-21 → 表 reach) |
| M-02 | `measure/kokkai_false_pass_2026-10-15.py` | `run` | 仕掛け持ち | 構造化された claim の値 | claim の id ― 無改変の要約の同じ id の claim が GROUNDED の行だけを測る | 同じ id(値の読み返しなし) ― 書き換えた claim の検査の欄を同じ id で読む | 不要 | 無し | 49 行で skipped 0(K-33 → 表 reach) |
| M-03 | `measure/xbrl_a_core_vs_grep_2026-10-17.py` | `claim_for` | 仕掛け持ち | 本文の字 | 基準なし | 値(と字) ― 値と後の字(T3 は span の先頭の字が挿入文の中)。字で 1 件に決まらなければ値だけ | 無 | 同じ型 | 142 行で 対応が付いた 123・対応が付かない 19(K-34・K-35 → 表 reach) |
| M-04 | `measure/xbrl_attr_inject_2026-10-17.py` | `main` | 仕掛け持ち | 本文の字・fact の属性 | fact の鍵 ― 席の参照先の fact | fact の鍵 ― 足した fact の鍵を pointers に直に渡す | 不要 | 無し | 24 行で 無効 0(K-32 → 表 reach) |
| M-05 | `measure/xbrl_cd_material_2026-10-17.py` | `main` | 仕掛け持ち | 本文の字 | 基準なし | 値(と字) ― 値が許容差の内側 かつ 数の字面が span に在る、の最初の 1 件(1 件に決まるかは見ない) | 無 | 同じ型 | 行 192・対応が付かない行 51・共有された行 36・共有された主張 12・T5 50・T5 のうち 1 対 1 26・T5 のうち共有 24(K-36・K-37 → 表 reach) |
| M-06 | `measure/xbrl_contract_v1_2026-10-17.py` | `main` | 仕掛け持ち | 本文の字 | 基準なし | なし(値・鍵を検査に直に渡す) ― B′ は行の値と席の参照先を渡す | 不要 | 無し | 記録に該当の欄なし |
| M-07 | `measure/xbrl_dim_hold_2026-10-17.py` | `main` | 仕掛け持ち | 本文の字・fact の属性 | 基準なし | なし(値・鍵を検査に直に渡す) ― 行の値と席の参照先を渡す | 不要 | 無し | 記録に該当の欄なし |
| M-08 | `measure/xbrl_fresh_2026-10-21.py` | `_find_base_claim`・`inject_doc` | 仕掛け持ち | 本文の字 | 値(と字) ― 無改変の P22 で値と元の字、1 件でなければ値だけ | 値(と字) ― a_core_vs_grep の claim_for | 無 | 同じ型 | 741 行で GROUNDED 5(K-38 → 表 reach) |
| M-09 | `measure/xbrl_gen_c1_2026-10-20.py` | `engine_stage` | 仕掛け持ち | 本文の字 | 基準なし | なし(値・鍵を検査に直に渡す) ― 行の値を渡す | 不要 | 無し | 記録に該当の欄なし |
| M-10 | `measure/xbrl_holds_product_path_2026-10-19.py` | `f4_f5_f6` | 仕掛け持ち | 本文の字・fact の属性 | 基準なし | なし(値・鍵を検査に直に渡す) ― 行の値と参照先を渡す | 不要 | 無し | 記録に該当の欄なし |
| M-11 | `measure/xbrl_inject_reach_2026-10-28.py` | `classify_row` | 仕掛け持ち | 本文の字 | 値(と字) ― 値と字(基準を引く字) | 値(と字) ― 値と字。届いたかを文の番号と位置で数える | 有 | 無し | 741 行で (対応が付かない) 4・(文が 1 つに決まらない) 0・(届いた・止めた) 732・(届いた・通した) 0・(届かない・止めた) 0・(届かない・通した) 5(K-40 → 表 reach) |
| M-12 | `measure/xbrl_lastbranch_2026-10-21.py` | `injections_doc` | 仕掛け持ち | 本文の字 | 位置(文の番号と文の中の位置) ― P24 から P25 に動いた行の文の番号と位置 | 位置(文の番号と文の中の位置)+ 値の読み返し ― 位置の claim が無ければ主張が見つからない、値が違えば値がずれた | 有 | 無し | 1154 行で 主張が見つからない 20・値がずれた 16・文が見つからない 0・数が見つからない 0(K-22・K-23・K-26・K-27・K-28・K-29 → 表 reach) |
| M-13 | `measure/xbrl_p20_rerun_2026-10-17.py` | `claim_of` | 仕掛け持ち | 本文の字 | 基準なし | 値(と字) ― cd_material と同じ対応付けの写し | 無 | 同じ型 | 記録に該当の欄なし |
| M-14 | `measure/xbrl_p27_tune_2026-10-27.py` | `find_base_claim`・`base_status`・`claim_for_p27`・`classify`・`inject_doc` | 仕掛け持ち | 本文の字 | 値(と字) ― 値(円に直す)と書かれた字、無改変の P22。P26 で同じ claim が同じ値・span・unit | 値(と字) ― 値(円に直す)と後の字、1 件でなければ値だけ。注入後の claim の id が基準の id と同じかを見ない | 無 | 同じ型 | 評価用・調整用の記録の『基準に対応が付かない』『対応が付かない』(→ 表 p27rec) |
| M-15 | `measure/xbrl_period_bind_2026-10-20.py` | `inject_with_profile` | 仕掛け持ち | 本文の字 | site の id ― 文の数を engine と同じ順で数えて id を付け、id の値が engine と合わない site は除く | 同じ id(値の読み返しあり) ― 同じ id の claim の値が期待と違えば id_shift、claim が無ければ missing、文が見つからなければ sentence_not_found | 有 | 無し | 485 行で id_shift 1・sentence_not_found 1・missing 0(K-02・K-03・K-04・K-05・K-06・K-07・K-08・K-09・K-10・K-11・K-30・K-31 → 表 reach) |
| M-16 | `measure/xbrl_period_bind_2026-10-20.py` | `core_say_for` | 仕掛け持ち | 本文の字 | 基準なし | 値(と字) ― cd_material と同じ対応付けの写し | 無 | 同じ型 | 穴 B 注入 485・穴 B 既定のその他 5・段 2 注入 64・段 2 の Core 自身(既定)が GROUNDED の件 0(K-31・K-30 → 表 reach) |
| M-17 | `measure/xbrl_period_unit_hold_2026-10-19.py` | `main` | 仕掛け持ち | 本文の字・fact の属性 | 基準なし | なし(値・鍵を検査に直に渡す) ― 行の値と席の参照先を渡す | 不要 | 無し | 記録に該当の欄なし |
| M-18 | `measure/xbrl_pnf_diag_2026-10-17.py` | `main` | 仕掛け持ち | 本文の字 | 基準なし | 値(と字) ― cd_material と同じ対応付けの写し | 無 | 同じ型 | 記録に該当の欄なし |
| M-19 | `measure/xbrl_point_prior_2026-10-20.py` | `inject_doc` | 仕掛け持ち | 本文の字 | site の id ― 文の数を engine と同じ順で数えて id を付け、id の値が engine と合わない site は除く | 同じ id(値の読み返しあり) ― 同じ id の claim の値が期待と違えば id_shift、claim が無ければ missing、文が見つからなければ sentence_not_found | 有 | 無し | 485 行で id_shift 1・sentence_not_found 1・missing 0(K-01 → 表 reach) |
| M-20 | `measure/xbrl_role_swap_2026-10-17.py` | `main` | 仕掛け持ち | 本文の字 | 基準なし | 値(と字) ― cd_material と同じ対応付けの写し(recipe の claim の span) | 無 | 同じ型 | 記録に該当の欄なし |
| M-21 | `measure/xbrl_rowclaim_map_2026-10-17.py` | `claim_of` | 仕掛け持ち | 本文の字 | 基準なし | 値(と字) ― cd_material と同じ対応付けの写し(1 対 1 かは数えるが、位置は見ない) | 無 | 同じ型 | 行 192・対応が付かない行 51・共有された行 36・共有された主張 12・T5 50・T5 のうち 1 対 1 26・T5 のうち共有 24(K-36 → 表 reach) |
| M-22 | `measure/xbrl_t2_pass_diag_2026-10-28.py` | `classify` | 仕掛け持ち | 本文の字 | 値(と字) ― 値と字(基準を引く字) | 値(と字) ― 値と字。届いたかを文の番号で数える | 有 | 無し | 5 行で GROUNDED 5(K-39 → 表 reach) |
| M-23 | `measure/xbrl_verify_inventory_2026-10-17.py` | `part2` | 仕掛け持ち | 本文の字 | 基準なし | 値(と字) ― cd_material と同じ対応付けの写し(recipe の claim の span) | 無 | 同じ型 | 記録に該当の欄なし |
| M-24 | `measure/xbrl_vocab_2026-10-21.py` | `injections` | 仕掛け持ち | 本文の字 | 位置(文の番号と文の中の位置) ― P23 から P24 に動いた行の文の番号と位置 | 位置(文の番号と文の中の位置)+ 値の読み返し ― 位置の claim が無ければ主張が見つからない、値が違えば値がずれた | 有 | 無し | 695 行で 主張が見つからない 0・値がずれた 0・文が見つからない 0・数が見つからない 0(K-24・K-25 → 表 reach) |
<!-- 門:end -->

### 判断の根拠(関数の中の確かめ、または引く所の字)

仕掛けごとに、判断の根拠になる字を、その関数の中から一行だけ引く。門は『その字が、その file のその関数の中に在ること』を見る。**有**の仕掛けでは確かめの字、**無**の仕掛けでは値(と字)で引く所の字、**不要**の仕掛けでは値・鍵・claim を検査に渡す所の字を引いた。

<!-- 門:start evidence -->
**M-01** `measure/false_pass_2026-10-14.py` の `run_doc`
> elif exp is None or c.get("value") is None or abs(c["value"] - exp) > 1e-6 * max(1.0, abs(exp)):
**M-02** `measure/kokkai_false_pass_2026-10-15.py` の `run`
> cc["number"]["value"] = n["value"] + step
**M-03** `measure/xbrl_a_core_vs_grep_2026-10-17.py` の `claim_for`
> if c.get("value") is not None and abs(c["value"] - v) <= TOL
**M-04** `measure/xbrl_attr_inject_2026-10-17.py` の `main`
> out = VE.verify_external(dict(spec, pointers=[key]), fs)
**M-05** `measure/xbrl_cd_material_2026-10-17.py` の `main`
> if abs(c["value"] - r["値"]) <= A1.TOL and r["数の字面"] in (c.get("span") or ""):
**M-06** `measure/xbrl_contract_v1_2026-10-17.py` の `main`
> out = VE.verify_external(
**M-07** `measure/xbrl_dim_hold_2026-10-17.py` の `main`
> out = VE.verify_external({"kind": "single_value", "value": val,
**M-08** `measure/xbrl_fresh_2026-10-21.py` の `_find_base_claim`
> cands = [c for c in base_claims if c.get("value") is not None and abs(c["value"] - v0) <= TOL and c.get("span") and s0 in c["span"]]
**M-09** `measure/xbrl_gen_c1_2026-10-20.py` の `engine_stage`
> on = VE.verify_external(spec, facts, contexts, registry, claim_id=cid, period_pair=True)
**M-10** `measure/xbrl_holds_product_path_2026-10-19.py` の `f4_f5_f6`
> out = VE.verify_external(spec, facts, contexts, registry)
**M-11** `measure/xbrl_inject_reach_2026-10-28.py` の `classify_row`
> if reached:
**M-12** `measure/xbrl_lastbranch_2026-10-21.py` の `injections_doc`
> hit = [c for c in raw.values() if c.get("sentence") == si and c.get("pos") == a]
**M-13** `measure/xbrl_p20_rerun_2026-10-17.py` の `claim_of`
> if (abs(c["value"] - row[u"値"]) <= A1.TOL
**M-14** `measure/xbrl_p27_tune_2026-10-27.py` の `claim_for_p27`
> hit = [c for c in claims if c.get("value") is not None and same_number(claim_scaled(c), target)]
**M-15** `measure/xbrl_period_bind_2026-10-20.py` の `inject_with_profile`
> elif exp is None or c.get("value") is None or abs(c["value"] - exp) > 1e-6 * max(1.0, abs(exp)):
**M-16** `measure/xbrl_period_bind_2026-10-20.py` の `core_say_for`
> if abs(c["value"] - r["値"]) <= A1.TOL and r["数の字面"] in (c.get("span") or ""):
**M-17** `measure/xbrl_period_unit_hold_2026-10-19.py` の `main`
> out = VE.verify_external(spec_of(val, unit, loc), facts)
**M-18** `measure/xbrl_pnf_diag_2026-10-17.py` の `main`
> if (abs(c["value"] - r[u"値"]) <= A1.TOL
**M-19** `measure/xbrl_point_prior_2026-10-20.py` の `inject_doc`
> elif exp is None or c.get("value") is None or abs(c["value"] - exp) > 1e-6 * max(1.0, abs(exp)):
**M-20** `measure/xbrl_role_swap_2026-10-17.py` の `main`
> if (abs(c.value - r[u"値"]) <= A1.TOL
**M-21** `measure/xbrl_rowclaim_map_2026-10-17.py` の `claim_of`
> if (abs(c["value"] - row[u"値"]) <= A1.TOL
**M-22** `measure/xbrl_t2_pass_diag_2026-10-28.py` の `classify`
> return C_U_B if token_in_claim_sentence else C_U_A
**M-23** `measure/xbrl_verify_inventory_2026-10-17.py` の `part2`
> if abs(c.value - r[u"値"]) <= A1.TOL and r[u"数の字面"] in span:
**M-24** `measure/xbrl_vocab_2026-10-21.py` の `injections`
> hit = [c for c in raw.values() if c.get("sentence") == si and c.get("pos") == a
<!-- 門:end -->

### 使う側・記録・結果文書・台帳の行

使う側の script・仕掛けの数が現れる記録・結果文書を、仕掛けごとに書く。使う側は、仕掛けの file 名か、挙げた記録の名を本文に持つこと(使っている印)を門が見る。台帳の行の列は、穴の型が同じ型の仕掛けだけ封 §2-4 の規準で機械が選ぶ(他は『同じ型でない』と書く。台帳の列を同じ型の仕掛けに限ったのは封にない判断)。

<!-- 門:start ref -->
| ID | 使う側の script | 記録 | 結果文書 | 依存する台帳の行 |
|---|---|---|---|---|
| M-01 | `measure/ritual_2026-10-20.py`・`measure/false_pass_compare_2026-10-15.py` | `fixtures/xbrl/p17/false_pass_2026-10-14.json`・`fixtures/xbrl/p17/false_pass_2026-10-14_P18.json`・`fixtures/xbrl/p17/false_pass_2026-10-14_P19both.json`・`fixtures/xbrl/p17/false_pass_2026-10-14_batch1.json`・`fixtures/xbrl/p17/false_pass_2026-10-14_both.json`・`fixtures/xbrl/p17/false_pass_2026-10-14_fixed.json`・`fixtures/xbrl/ritual_2026-10-20.json`・`fixtures/xbrl/ritual_2026-10-20_p21.json`・`fixtures/xbrl/ritual_2026-10-20_p22.json`・`fixtures/xbrl/ritual_2026-10-20_p26.json` | ― | ―(同じ型でない) |
| M-02 | ― | `fixtures/kokkai/false_pass_round12_2026-10-15.json` | ― | ―(同じ型でない) |
| M-03 | `measure/xbrl_gen_c_2026-10-20.py`・`measure/xbrl_gen_c_p20_2026-10-20.py`・`measure/xbrl_naming_fix_2026-10-20.py` | `fixtures/xbrl/cd8/a_core_vs_grep_2026-10-17.json`・`fixtures/xbrl/gen_c/c0_2026-10-20.json`・`fixtures/xbrl/gen_c/c0_p20_2026-10-20.json`・`fixtures/xbrl/naming_fix/p21_2026-10-20.json` | `XBRL_A_CORE_VS_GREP_RESULT_2026-10-17.md`・`XBRL_GENERALITY_RESULT_2026-10-20.md`・`XBRL_NAMING_FIX_RESULT_2026-10-20.md` | L-17・L-28・L-29・D-09・D-10・D-11・D-12・H-01・H-09・P-14・P-15・P-18 |
| M-04 | `measure/xbrl_dim_hold_2026-10-17.py`・`measure/xbrl_holds_product_path_2026-10-19.py` | `fixtures/xbrl/cd8/attr_inject_2026-10-17.json` | ― | ―(同じ型でない) |
| M-05 | `measure/xbrl_cd_score_2026-10-17.py`・`measure/xbrl_cd_ceiling_2026-10-17.py`・`measure/xbrl_gen_c1_2026-10-20.py`・`measure/xbrl_gen_c_alpha_2026-10-20.py`・`measure/xbrl_hybrid_trust_2026-10-20.py`・`measure/xbrl_hybrid_s2_2026-10-20.py` | `fixtures/xbrl/cd8/material_2026-10-17.json`・`fixtures/xbrl/cd8/score_2026-10-17.json`・`fixtures/xbrl/cd8/ceiling_2026-10-17.json`・`fixtures/xbrl/cd8/rowclaim_map_2026-10-17.json`・`fixtures/xbrl/gen_c/material_2026-10-20.json`・`fixtures/xbrl/gen_c/c1_2026-10-20.json`・`fixtures/xbrl/gen_c/alpha_2026-10-20.json`・`fixtures/xbrl/gen_c/hybrid_trust_2026-10-20.json`・`fixtures/xbrl/gen_c/hybrid_s2_material_2026-10-20.json`・`fixtures/xbrl/gen_c/hybrid_s2_2026-10-20.json` | `XBRL_CD_RESULT_2026-10-17.md` | L-14・L-15・L-18・L-30・L-31・D-11・D-13・H-09・P-16・P-17 |
| M-06 | ― | `fixtures/xbrl/cd8/contract_v1_2026-10-17.json` | ― | ―(同じ型でない) |
| M-07 | `measure/xbrl_period_unit_hold_2026-10-19.py` | `fixtures/xbrl/cd8/dim_hold_2026-10-17.json` | ― | ―(同じ型でない) |
| M-08 | ― | `fixtures/xbrl/fresh/fresh_2026-10-21.json` | `XBRL_FRESH_SAMPLE_RESULT_2026-10-21.md` | L-36・H-12 |
| M-09 | `measure/xbrl_gen_c_alpha_2026-10-20.py`・`measure/xbrl_hybrid_s2_2026-10-20.py` | `fixtures/xbrl/gen_c/c1_2026-10-20.json` | ― | ―(同じ型でない) |
| M-10 | ― | `fixtures/xbrl/cd8/holds_product_path_2026-10-19.json` | ― | ―(同じ型でない) |
| M-11 | ― | `fixtures/xbrl/inject_reach_2026-10-28.json` | ― | ―(同じ型でない) |
| M-12 | `measure/xbrl_p26_2026-10-21.py` | `fixtures/xbrl/lastbranch_2026-10-21.json`・`fixtures/xbrl/p26_2026-10-21.json` | ― | ―(同じ型でない) |
| M-13 | `measure/xbrl_p20_pred_recheck_2026-10-17.py` | `fixtures/xbrl/cd8/p20_rerun_2026-10-17.json`・`fixtures/xbrl/cd8/p20_pred_recheck_2026-10-17.json` | ― | P-09 |
| M-14 | `measure/xbrl_p27_eval_2026-10-27.py`・`measure/xbrl_p27_tune_rerun_2026-10-27.py` | `fixtures/xbrl/p27/eval_inject_2026-10-27.json`・`fixtures/xbrl/p27/tune_inject_2026-10-27.json`・`fixtures/xbrl/p27/tune_p27_inject_2026-10-27.json` | `XBRL_P27_RESULT_2026-10-27.md`・`XBRL_P27_TUNE_DIAG_2026-10-27.md` | L-32・L-33・L-34・L-37・L-38・D-21・D-22・D-23・D-26・H-13・H-14・P-19・P-20 |
| M-15 | `measure/xbrl_rounding_2026-10-21.py`・`measure/xbrl_vocab_2026-10-21.py`・`measure/xbrl_lastbranch_2026-10-21.py`・`measure/xbrl_p26_2026-10-21.py`・`measure/xbrl_default_p26_2026-10-23.py`・`measure/xbrl_default_p27_2026-10-28.py` | `fixtures/xbrl/period_bind_2026-10-20.json`・`fixtures/xbrl/rounding_2026-10-21.json`・`fixtures/xbrl/vocab_2026-10-21.json`・`fixtures/xbrl/lastbranch_2026-10-21.json`・`fixtures/xbrl/p26_2026-10-21.json`・`fixtures/xbrl/default_p26_2026-10-23.json`・`fixtures/xbrl/default_p27_2026-10-28.json` | ― | ―(同じ型でない) |
| M-16 | `measure/xbrl_rounding_2026-10-21.py`・`measure/xbrl_vocab_2026-10-21.py`・`measure/xbrl_lastbranch_2026-10-21.py`・`measure/xbrl_p26_2026-10-21.py`・`measure/xbrl_default_p26_2026-10-23.py`・`measure/xbrl_default_p27_2026-10-28.py` | `fixtures/xbrl/period_bind_2026-10-20.json`・`fixtures/xbrl/rounding_2026-10-21.json`・`fixtures/xbrl/vocab_2026-10-21.json`・`fixtures/xbrl/lastbranch_2026-10-21.json`・`fixtures/xbrl/p26_2026-10-21.json`・`fixtures/xbrl/default_p26_2026-10-23.json`・`fixtures/xbrl/default_p27_2026-10-28.json` | ― | D-23・D-25・P-21 |
| M-17 | ― | `fixtures/xbrl/cd8/period_unit_hold_2026-10-19.json` | ― | ―(同じ型でない) |
| M-18 | ― | `fixtures/xbrl/cd8/pnf_diag_2026-10-17.json` | ― | なし(台帳の行に記録の path・script 名・結果文書名が無い) |
| M-19 | `measure/xbrl_period_bind_2026-10-20.py`・`measure/xbrl_rounding_2026-10-21.py` | `fixtures/xbrl/point_prior_2026-10-20.json` | ― | ―(同じ型でない) |
| M-20 | `measure/xbrl_contract_v1_2026-10-17.py` | `fixtures/xbrl/cd8/role_swap_2026-10-17.json`・`fixtures/xbrl/cd8/contract_v1_2026-10-17.json` | ― | L-16・D-05・P-02・P-03 |
| M-21 | ― | `fixtures/xbrl/cd8/rowclaim_map_2026-10-17.json` | ― | なし(台帳の行に記録の path・script 名・結果文書名が無い) |
| M-22 | `measure/xbrl_inject_reach_2026-10-28.py` | `fixtures/xbrl/t2_pass_diag_2026-10-28.json` | ― | ―(同じ型でない) |
| M-23 | ― | `fixtures/xbrl/cd8/verify_inventory_2026-10-17.json` | ― | なし(台帳の行に記録の path・script 名・結果文書名が無い) |
| M-24 | `measure/xbrl_lastbranch_2026-10-21.py` | `fixtures/xbrl/vocab_2026-10-21.json` | ― | ―(同じ型でない) |
<!-- 門:end -->

## 4. 記録から数えた数

既存の記録の欄だけを数えた(engine は走らせていない)。数えた欄・語は記録の欄の名のまま。

- 表 reach: 『届かなかった行』を表す欄や語(`id_shift`・`sentence_not_found`・`missing`・`unmutable`・`主張が見つからない`・`値がずれた`・`数が見つからない`・`対応が付かない` など)を持つ記録の側。前期比の注入の記録の行には `id_shift`・`sentence_not_found` という名の欄は無く、語は profile の欄の `state` の値(`point_prior` は `結果の細目` の値)である。行に型の欄が無いので、型別には数えない(封 §2-3 の 1 の『型別』は出せない。封にない判断)。前期比の注入を測る行は、使う側の記録(rounding・vocab・lastbranch・p26・default_p26・default_p27)でも同じ行が数えない欄に落ちている。default_p26・default_p27 の S6 は行を持たず、『既定のその他』の内訳は記録から言えない。
- 表 ritual: 儀式の記録の四本。記録の『通した のうち参照先が動いた』を、行の欄 `参照先が動いた` と、行の `参照先(注入前)`・`参照先(注入後)` の違いの二通りで数え直した。
- 表 p27rec: 評価用・調整用の記録三本。行の欄に文の番号・token の位置・届いた/届かないの欄は無い(行は基準の claim の id を持つが、注入後に数えた claim の id を持たない)。
- 前の二便の数(表 reach の fresh・t2_pass_diag・inject_reach)は、前の便の門が数えている。ここでは写しとして数え直しただけで、届いた(文)・届いた(数)は新しく数えない。

<!-- 門:start reach -->
| K | 記録の path | 節 | 数えた欄 | 行 | 語と数 |
|---|---|---|---|---|---|
| K-01 | `fixtures/xbrl/point_prior_2026-10-20.json` | B | 行の 結果の細目 | 485 | id_shift 1・sentence_not_found 1・missing 0 |
| K-02 | `fixtures/xbrl/period_bind_2026-10-20.json` | E1 | 行の P21(対照) の state | 485 | id_shift 1・sentence_not_found 1・missing 0 |
| K-03 | `fixtures/xbrl/period_bind_2026-10-20.json` | E1 | 行の P22 の state | 485 | id_shift 1・sentence_not_found 1・missing 0 |
| K-04 | `fixtures/xbrl/rounding_2026-10-21.json` | R3 | 行の P22 の state | 485 | id_shift 1・sentence_not_found 1・missing 0 |
| K-05 | `fixtures/xbrl/rounding_2026-10-21.json` | R3 | 行の P23 の state | 485 | id_shift 1・sentence_not_found 1・missing 0 |
| K-06 | `fixtures/xbrl/vocab_2026-10-21.json` | W4 | 行の P23 の state | 485 | id_shift 1・sentence_not_found 1・missing 0 |
| K-07 | `fixtures/xbrl/vocab_2026-10-21.json` | W4 | 行の P24 の state | 485 | id_shift 1・sentence_not_found 1・missing 0 |
| K-08 | `fixtures/xbrl/lastbranch_2026-10-21.json` | L4 | 行の P24 の state | 485 | id_shift 1・sentence_not_found 1・missing 0 |
| K-09 | `fixtures/xbrl/lastbranch_2026-10-21.json` | L4 | 行の P25 の state | 485 | id_shift 1・sentence_not_found 1・missing 0 |
| K-10 | `fixtures/xbrl/p26_2026-10-21.json` | Q3 穴 B | 行の P25 の state | 485 | id_shift 1・sentence_not_found 1・missing 0 |
| K-11 | `fixtures/xbrl/p26_2026-10-21.json` | Q3 穴 B | 行の P26 の state | 485 | id_shift 1・sentence_not_found 1・missing 0 |
| K-12 | `fixtures/xbrl/p17/false_pass_2026-10-14.json` | 全部の run | 行の outcome | 373 | id_shift 0・sentence_not_found 0・missing 0・unmutable 0 |
| K-13 | `fixtures/xbrl/p17/false_pass_2026-10-14_P18.json` | 全部の run | 行の outcome | 203 | id_shift 0・sentence_not_found 0・missing 0・unmutable 0 |
| K-14 | `fixtures/xbrl/p17/false_pass_2026-10-14_P19both.json` | 全部の run | 行の outcome | 406 | id_shift 0・sentence_not_found 0・missing 0・unmutable 0 |
| K-15 | `fixtures/xbrl/p17/false_pass_2026-10-14_batch1.json` | 全部の run | 行の outcome | 746 | id_shift 0・sentence_not_found 0・missing 0・unmutable 0 |
| K-16 | `fixtures/xbrl/p17/false_pass_2026-10-14_both.json` | 全部の run | 行の outcome | 746 | id_shift 0・sentence_not_found 0・missing 0・unmutable 0 |
| K-17 | `fixtures/xbrl/p17/false_pass_2026-10-14_fixed.json` | 全部の run | 行の outcome | 576 | id_shift 0・sentence_not_found 0・missing 0・unmutable 0 |
| K-18 | `fixtures/xbrl/ritual_2026-10-20.json` | 注入の一覧 | 行の 結果 | 243 | id_shift 0・sentence_not_found 0・missing 0 |
| K-19 | `fixtures/xbrl/ritual_2026-10-20_p21.json` | 注入の一覧 | 行の 結果 | 241 | id_shift 0・sentence_not_found 0・missing 0 |
| K-20 | `fixtures/xbrl/ritual_2026-10-20_p22.json` | 注入の一覧 | 行の 結果 | 240 | id_shift 0・sentence_not_found 0・missing 0 |
| K-21 | `fixtures/xbrl/ritual_2026-10-20_p26.json` | 注入の一覧 | 行の 結果 | 243 | id_shift 0・sentence_not_found 0・missing 0 |
| K-22 | `fixtures/xbrl/lastbranch_2026-10-21.json` | L7 | 行の P24 の state か 結果 | 1154 | 主張が見つからない 20・値がずれた 16・文が見つからない 0・数が見つからない 0 |
| K-23 | `fixtures/xbrl/lastbranch_2026-10-21.json` | L7 | 行の P25 の state か 結果 | 1154 | 主張が見つからない 20・値がずれた 16・文が見つからない 0・数が見つからない 0 |
| K-24 | `fixtures/xbrl/vocab_2026-10-21.json` | W6 | 行の P23 の state か 結果 | 695 | 主張が見つからない 0・値がずれた 0・文が見つからない 0・数が見つからない 0 |
| K-25 | `fixtures/xbrl/vocab_2026-10-21.json` | W6 | 行の P24 の state か 結果 | 695 | 主張が見つからない 0・値がずれた 0・文が見つからない 0・数が見つからない 0 |
| K-26 | `fixtures/xbrl/p26_2026-10-21.json` | Q4 | 行の P25 の state か 結果 | 388 | 主張が見つからない 6・値がずれた 12・文が見つからない 0・数が見つからない 46 |
| K-27 | `fixtures/xbrl/p26_2026-10-21.json` | Q4 | 行の P26 の state か 結果 | 388 | 主張が見つからない 6・値がずれた 18・文が見つからない 0・数が見つからない 46 |
| K-28 | `fixtures/xbrl/p26_2026-10-21.json` | Q5 | 行の P25 の state か 結果 | 1095 | 主張が見つからない 27・値がずれた 0・文が見つからない 0・数が見つからない 0 |
| K-29 | `fixtures/xbrl/p26_2026-10-21.json` | Q5 | 行の P26 の state か 結果 | 1095 | 主張が見つからない 27・値がずれた 0・文が見つからない 0・数が見つからない 0 |
| K-30 | `fixtures/xbrl/default_p26_2026-10-23.json` | S6 | 穴 B と段 2 の数(行を持たない) | ― | 穴 B 注入 485・穴 B 既定のその他 5・段 2 注入 64・段 2 の Core 自身(既定)が GROUNDED の件 0 |
| K-31 | `fixtures/xbrl/default_p27_2026-10-28.json` | S6 | 穴 B と段 2 の数(行を持たない) | ― | 穴 B 注入 485・穴 B 既定のその他 5・段 2 注入 64・段 2 の Core 自身(既定)が GROUNDED の件 0 |
| K-32 | `fixtures/xbrl/cd8/attr_inject_2026-10-17.json` | rows | 行の **無効** | 24 | 無効 0 |
| K-33 | `fixtures/kokkai/false_pass_round12_2026-10-15.json` | rows | 行の skipped | 49 | skipped 0 |
| K-34 | `fixtures/xbrl/cd8/a_core_vs_grep_2026-10-17.json` | rows | 行の 対応が付いた | 142 | 対応が付いた 123・対応が付かない 19 |
| K-35 | `fixtures/xbrl/gen_c/c0_2026-10-20.json` | C0-2 rows | 行の 対応が付いた | 128 | 対応が付いた 104・対応が付かない 24 |
| K-36 | `fixtures/xbrl/cd8/rowclaim_map_2026-10-17.json` | 合計 | 合計の欄(多対一を数えた記録) | ― | 行 192・対応が付かない行 51・共有された行 36・共有された主張 12・T5 50・T5 のうち 1 対 1 26・T5 のうち共有 24 |
| K-37 | `fixtures/xbrl/cd8/material_2026-10-17.json` | 合計 | 合計の欄 | ― | 書類 8・行 192・注入 64 |
| K-38 | `fixtures/xbrl/fresh/fresh_2026-10-21.json` | 注入の行 | 行の 結果 P26 の state | 741 | GROUNDED 5 |
| K-39 | `fixtures/xbrl/t2_pass_diag_2026-10-28.json` | rows | 行の 結果 P22 の state(通した行だけの記録) | 5 | GROUNDED 5 |
| K-40 | `fixtures/xbrl/inject_reach_2026-10-28.json` | rows | 行の profile P22 の 分類 | 741 | (対応が付かない) 4・(文が 1 つに決まらない) 0・(届いた・止めた) 732・(届いた・通した) 0・(届かない・止めた) 0・(届かない・通した) 5 |
<!-- 門:end -->

<!-- 門:start ritual -->
| 記録の path | 行 | 通した(PASSED) | 記録の『通した のうち参照先が動いた』 | 行の欄 参照先が動いた で数え直した数 | 参照先(注入前)と(注入後)の違いで数え直した数 |
|---|---|---|---|---|---|
| `fixtures/xbrl/ritual_2026-10-20.json` | 243 | 2 | 0 | 0 | 0 |
| `fixtures/xbrl/ritual_2026-10-20_p21.json` | 241 | 17 | 2 | 2 | 2 |
| `fixtures/xbrl/ritual_2026-10-20_p22.json` | 240 | 15 | 0 | 0 | 0 |
| `fixtures/xbrl/ritual_2026-10-20_p26.json` | 243 | 2 | 0 | 0 | 0 |
<!-- 門:end -->

<!-- 門:start p27rec -->
| 記録の path | 注入の行 | T1_VALUE の基準に対応が付かない / 採った(書類別の数えの合計) | T8_REL の基準に対応が付かない / 採った | 行の欄 | profile の欄 |
|---|---|---|---|---|---|
| `fixtures/xbrl/p27/eval_inject_2026-10-27.json` | 96 | 7 / 24 | 5 / 89 | docID・id・型・文体・基準の claim・P22・P26・P27・P27E | 対応・結果・state・reason |
| `fixtures/xbrl/p27/tune_inject_2026-10-27.json` | 101 | 5 / 32 | 1 / 90 | docID・id・型・文体・基準の claim・P22・P26 | 対応・結果・state・reason |
| `fixtures/xbrl/p27/tune_p27_inject_2026-10-27.json` | 101 | 5 / 32 | 1 / 90 | docID・id・型・文体・基準の claim・P22・P26・P27・P27E | 対応・結果・state・reason |

| 記録の path | profile | 行 | 通した | 名指したが別の値 | 対応が付かない |
|---|---|---|---|---|---|
| `fixtures/xbrl/p27/eval_inject_2026-10-27.json` | P22 | 96 | 27 | 7 | 2 |
| `fixtures/xbrl/p27/eval_inject_2026-10-27.json` | P26 | 96 | 27 | 5 | 2 |
| `fixtures/xbrl/p27/eval_inject_2026-10-27.json` | P27 | 96 | 0 | 5 | 2 |
| `fixtures/xbrl/p27/eval_inject_2026-10-27.json` | P27E | 96 | 0 | 7 | 2 |
| `fixtures/xbrl/p27/tune_inject_2026-10-27.json` | P22 | 101 | 28 | 4 | 3 |
| `fixtures/xbrl/p27/tune_inject_2026-10-27.json` | P26 | 101 | 28 | 4 | 3 |
| `fixtures/xbrl/p27/tune_p27_inject_2026-10-27.json` | P22 | 101 | 28 | 4 | 3 |
| `fixtures/xbrl/p27/tune_p27_inject_2026-10-27.json` | P26 | 101 | 28 | 4 | 3 |
| `fixtures/xbrl/p27/tune_p27_inject_2026-10-27.json` | P27 | 101 | 0 | 7 | 3 |
| `fixtures/xbrl/p27/tune_p27_inject_2026-10-27.json` | P27E | 101 | 0 | 9 | 3 |

| 評価用の『名指したが別の値』の行の重なり | 両方 | 前の profile だけ | 後の profile だけ |
|---|---|---|---|
| P22・P26 | 5 | 2 | 0 |
| P22・P27 | 5 | 2 | 0 |
| P22・P27E | 6 | 1 | 1 |
| P26・P27 | 5 | 0 | 0 |
| P26・P27E | 5 | 0 | 2 |
| P27・P27E | 5 | 0 | 2 |
<!-- 門:end -->

## 5. 依存する台帳の行と結果文書

規準(封 §2-4。機械): 台帳 `docs/FACTS_FOR_BUYERS_2026-10-20.md` の `| <ID> |` で始まる行(ID は `L-`・`D-`・`H-`・`P-`)のうち、行の字に、同じ型の仕掛け(または使う側)の記録の path・script の file 名・結果文書の file 名のどれかが在る行。外に出した紙は読まない。**台帳の ID の `H-12` から `H-14` は、封の予測 H-12 から H-14 とは別の名前空間である。**

読みの規則(封 §6-5 の 3。台帳の行ごとに、行の字と印を読む):

- **通った**: 行の数のうち一つ以上が、同じ型の対応付けを通った数(注入した場所の claim を値(と字)で引いて state・参照先を読んだ数、または基準に対応が付いた行だけが行になる数)。
- **通っていない**: 行の数が、無改変の主張・席の答え・値検索・値や鍵を検査に直に渡す数・読み手の席の数で、同じ型の対応付けを使わない。
- **記録から分からない**: 行の字と印からは、通ったかを言えない(予測の当たり・外れの本数など)。

一つの行に通った数と通っていない数が混ざる行は『通った』とし、根拠にどの数が通ったかを書く。『通った』は、その数が対応付けの数でありうるという意味で、対応付けの数だったという意味ではない(§6)。引用は台帳の行の字の一部で、門が行の中に在ることを見る。

<!-- 門:start ledger -->
| 台帳の行 | 引いた仕掛け | 一致した字 | 読み | 根拠 | 行の字(引用) |
|---|---|---|---|---|---|
| L-14 | M-05 | 記録・script | 通った | C′ の誤認定・特定は、材料の Core 欄(行 → claim を M-05 の対応付けで引いた参照先)を読んだ数。A は席だけ、D′ は値検索で、この 2 つは通っていない | `A の誤認定 8 / 85 = 9.4%` |
| L-15 | M-05 | 記録・script | 通っていない | D′ の偽警報(無改変の主張)の数。D′ は値検索で、行 → claim の対応付けを使わない | `C1 の D′ の偽警報(記録の注: 判定には使わない) 43 / 128 = ` |
| L-16 | M-20 | 記録・script | 通った | B の検出・実証不能は、行 → recipe の claim を M-20 の対応付けで引いて検査した数。A は席の判定 | `A の検出(注入 64 行) 51 / 64 = 79.7%` |
| L-17 | M-03 | 記録・script | 通った | Core の特定と Core-P の特定・誤認定は、注入した場所の claim を M-03 の claim_for で引いて読んだ数。D′ は値検索で通っていない | `封の読みの Core の特定 0 / 64 = 0.0%` |
| L-18 | M-05 | 記録・script | 通った | 『Core が正解を持っていた』と Core-P の特定は、材料の Core 欄(M-05 の対応付け)を読んだ数。席が外した行は席の答えに依る | `席が外した行 7` |
| L-28 | M-03 | 記録・script | 通った | Core の特定・Core-P の特定と誤認定は、gen_c の C0-2(M-03 の claim_for)で注入した場所の claim を引いた数 | `Core の特定 0 / 50 = 0.0%` |
| L-29 | M-03 | 記録・script | 記録から分からない | 予測の当たり・外れの本数。行の字と印には、どの予測がどの数に依るかが書かれていない | `封の予測の外れ(記録の false) 6` |
| L-30 | M-05 | 記録・script | 通った | Core-P の特定は材料の Core 欄(M-05)の数。席 A の特定は席の答え | `席 A の特定 16 / 20 = 80.0%` |
| L-31 | M-05 | 記録・script | 通っていない | 席が名指した参照先を engine に直に渡して検算した数(gen_c_alpha の engine_item。値・鍵を直に渡す作り)。claim を値で引かない | `裏づけた(一致) 46 / 77 = 59.7%` |
| L-32 | M-14 | 記録・script・結果文書 | 通った | P26 の T8_REL の『名指して原本の値を返した』と対応が付く行は、注入後の claim を claim_for_p27(M-14)で引いた行の数 | `P26 の T8_REL: 名指して原本の値を返した行 36 / 87 = 41` |
| L-33 | M-14 | script・結果文書 | 通っていない | 読む行は無改変の文の判定が違うと言った行(D-26 の字: 読む行 47 は P22 の VALUE_MISMATCH 47 / 534 と同数)で、注入の行でない | `評価用: 読む行 2` |
| L-34 | M-14 | 記録・script | 通った | T8_REL・T1_VALUE の『名指して原本の値を返した』は M-14 の claim_for_p27 で引いた行の数。GROUNDED を離れた行は無改変の数 | `P26 の T8_REL: 名指して原本の値を返した行 36 / 87 = 41` |
| L-36 | M-08 | 記録・script・結果文書 | 通った | 『通した 5』は M-08 の対応付け(値と字 → 値だけ)の数。前の 2 便の診断で、5 行とも差し替えが基準の claim の文の外にあった(診断済み) | `注入の回数 741` |
| L-37 | M-14 | script・結果文書 | 通っていない | K-3・K-4 の行は無改変の P26・P27・P27E の判定の差で、注入の行でない | `読む行 2` |
| L-38 | M-14 | 記録・script・結果文書 | 通った | R-11a・R-11f・R-11g は T8_REL の注入の数(M-14 の対応付け)。R-6b・R-7a は無改変の数 | `R-6b: 調整用の P22 の VALUE_MISMATCH の率 47 / ` |
| D-05 | M-20 | 記録・script | 通った | 『Core 自身の recipe で検証を試みられた行』は行 → recipe の claim(M-20)を引いた数。B′ 側の『注入のうち検査を通った』は値・鍵を直に渡す作り(M-06) | `Core 自身の recipe で検証を試みられた行 42 / 85 = 49.` |
| D-09 | M-03 | 記録・script | 通っていない | C0-1 は無改変の本文の主張を製品の経路に通した数で、注入を使わない | `主張 913` |
| D-10 | M-03 | 記録・script | 通った | 特定と誤認定は、注入した T5 の参照先を gen_c の C0-2(M-03)と名前直しの再走で引いた数 | `P16 の特定(未使用 8 書類) 13 / 50 = 26.0%` |
| D-11 | M-03・M-05 | 記録・script | 通った | Core-P の特定は材料の Core 欄(M-05)の数。席 A は席の答え | `席 A 16 / 20 = 80.0%` |
| D-12 | M-03 | 記録・script | 記録から分からない | 無改変の 40 書類の数は通っていない。段 2 の照合の行(未使用 2 書類の P16 の記録の行)が、注入の行を対応付けで引いた数かは、行の字と印から言えない | `主張 4665` |
| D-13 | M-05 | 記録・script | 通っていない | 席が名指した参照先を engine に直に渡して検算した数(gen_c_alpha の engine_item)で、claim を値で引かない | `検算の対象(確認済みで参照先が在った行) 77` |
| D-21 | M-14 | script・結果文書 | 通っていない | 無改変の文の判定(claim の数と VALUE_MISMATCH の率)で、注入を使わない | `claim の数(4 profile とも) 523` |
| D-22 | M-14 | 記録・script | 通った | 通した率・名指した率は、注入後の claim を claim_for_p27(M-14)で引いた行の数 | `T8_REL の P22: 通した 27 / 87 = 31.0%` |
| D-23 | M-14・M-16 | 記録・script・結果文書 | 通った | K-1・K-2 は T8_REL・T1_VALUE の注入の数(M-14)。K-3 から K-5 と D は無改変の数 | `K-1: T8_REL の P27E の通した 0 / 87 = 0.0%` |
| D-25 | M-16 | 記録・script | 通った | 『段 2 の材料の注入 64 件で Core 自身(既定)が GROUNDED』は M-16 の対応付けの数。有報の原文の注入の側は M-15(確かめ 有) | `書類(手元の 67 ＋ 新しい標本 30) 97` |
| D-26 | M-14 | 記録・script・結果文書 | 通った | T8_REL・T1_VALUE の通した・名指した率は M-14 の数。無改変の判定・読む行は通っていない | `claim の数(P26) 534` |
| H-01 | M-03 | 記録・結果文書 | 通っていない | 欠陥 A の数(値違いの数の主張・候補の修正が動かした件)は無改変の書類の主張で、注入を使わない | `今日: 直しは未採用のまま。P21 の F3b(増減の文は残高の対にする)が一部` |
| H-09 | M-03・M-05 | 記録・script・結果文書 | 通った | gen_c の特定(P21)と Core-P が名指した注入の行は M-03 の claim_for で引いた数。『engine が誤りを一致にした』は参照先を直に渡す数(M-09 と同じ型) | `今日: 名指しの直し P21 で特定は増えた。engine に Core-P の` |
| H-12 | M-08 | 記録・script・結果文書 | 通った | 『通した 5』は M-08 の対応付けの数(診断済み) | `今日: 診断済み(2026-10-28)。P22 から P26 の 5 つの p` |
| H-13 | M-14 | script・結果文書 | 通っていない | 読み手の席の側の数で、注入を使わない | `今日: 人の目なしのまま。評価用・調整用の読む行は全部「道具」に揃った。数: 評` |
| H-14 | M-14 | script・結果文書 | 通っていない | 文2 の札の数(読む行の側)で、注入を使わない | `今日: 未測定のまま。段 1・段 2 の会社は最新の有報で、翌期の有報が存在しな` |
| P-02 | M-20 | 記録・script | 記録から分からない | 予測の当たり・外れの本数。どの予測がどの数に依るかは行の字と印に無い | `当たり 6` |
| P-03 | M-20 | 記録・script | 記録から分からない | 予測の当たり・外れの本数。どの予測がどの数に依るかは行の字と印に無い | `当たり 6` |
| P-09 | M-13 | 記録・script | 記録から分からない | 予測の当たり・外れの本数。どの予測がどの数に依るかは行の字と印に無い | `当たり 9` |
| P-14 | M-03 | 記録・script | 記録から分からない | 予測の当たり・外れの本数。どの予測がどの数に依るかは行の字と印に無い | `記録の判定が true 7` |
| P-15 | M-03 | 記録・script | 記録から分からない | 予測の当たり・外れの本数。どの予測がどの数に依るかは行の字と印に無い | `記録の判定が true 4` |
| P-16 | M-05 | 記録・script | 記録から分からない | 予測の当たり・外れの本数。どの予測がどの数に依るかは行の字と印に無い | `記録の判定が true 9` |
| P-17 | M-05 | 記録・script | 記録から分からない | 予測の当たり・外れの本数。どの予測がどの数に依るかは行の字と印に無い | `記録の判定が true 3` |
| P-18 | M-03 | 記録・script | 記録から分からない | 予測の当たり・外れの本数。どの予測がどの数に依るかは行の字と印に無い | `記録の判定が true 8` |
| P-19 | M-14 | 記録・script | 通った | 注入の行の数は、基準に対応が付いた行だけが行になる数(M-14 の find_base_claim を通った行)。claim の数と読む行は無改変の数 | `調整用の claim の数(P26) 534` |
| P-20 | M-14 | 記録・script | 通った | 注入の行の数は、基準に対応が付いた行だけが行になる数(M-14)。claim の数・読む行・書類の数は通っていない | `評価用の claim の数(P26) 523` |
| P-21 | M-16 | 記録・script | 記録から分からない | 予測 S の判定の真偽。どの予測がどの数に依るかは行の字と印に無い | `S-1 の判定(記録の当たり) true` |
<!-- 門:end -->

## 6. 判定

同じ型の仕掛けごとに、どの記録のどの数が『対応付けの数でありうる』かを、**記録の欄の範囲で**書く。engine を走らせていないので、**「engine が通した」とも「対応付けの欠陥だった」とも言い切らない**(測っていない)。前の二便が位置で数えて決めた(M-08 の通した行)ものだけが、診断済みである。

同じ型の仕掛けごとの『言えること』(語は **診断済み**・**対応付けの数でありうる**・**分けられない**。数の出どころと数は記録から機械が出す)。

<!-- 門:start verdict -->
| ID | 数の出どころ(記録の欄) | 数(記録から) | 言えること | 台帳の読みが『通った』の行 |
|---|---|---|---|---|
| M-03 | a_core_vs_grep_2026-10-17.json rows 行の 対応が付いた・c0_2026-10-20.json C0-2 rows 行の 対応が付いた | 142 行で 対応が付いた 123・対応が付かない 19(K-34 ほか) | 対応付けの数でありうる ― 『対応が付かない』は 1 件に決まらなかった行。cd8 と gen_c の C0 の Core の特定・Core-P の特定と誤認定は、この claim_for で引いた claim の読み | L-17・L-28・D-10・D-11・H-09 |
| M-05 | rowclaim_map_2026-10-17.json 合計 合計の欄(多対一を数えた記録)・material_2026-10-17.json 合計 合計の欄 | 行 192・対応が付かない行 51・共有された行 36・共有された主張 12・T5 50・T5 のうち 1 対 1 26・T5 のうち共有 24(K-36 ほか) | 対応付けの数でありうる ― 材料の Core 欄と、それを読む数(席に Core を足した C′・Core の特定・Core-P・『Core が正解を持っていた』)。2026-10-17 の記録が多対一を数え済み(影響するのは Core 欄だけ) | L-14・L-18・L-30・D-11・H-09 |
| M-08 | fresh_2026-10-21.json 注入の行 行の 結果 P26 の state | 741 行で GROUNDED 5 | 診断済み ― 『通した』は対応付けの数(前の 2 便の診断で、その行は差し替えが基準の claim の文の外にあった) | L-36・H-12 |
| M-13 | 記録に該当の欄なし(記録は材料の Core 欄・行ごとの結果) | ― | 対応付けの数でありうる ― M-05 と同じ写し。数える欄は記録に無く、Core 欄の読み | ― |
| M-14 | 評価用・調整用の記録の行・書類別の数え(→ 表 p27rec) | 評価用の注入の行 96: 対応が付かない 2(各 profile)・基準に対応が付かない T1 7 / 24・名指したが別の値 P22 7・P26 5・P27 5・通した P22 27・P26 27 | 分けられない ― 記録に注入後の claim の id・文の番号・位置・届いたかの欄が無く、engine の数か対応付けの数かを記録の欄から分けられない。『対応が付かない』は対応付けが 1 件に決まらなかった行 | L-32・L-34・L-38・D-22・D-23・D-26・P-19・P-20 |
| M-16 | default_p27_2026-10-28.json S6 穴 B と段 2 の数(行を持たない)・default_p26_2026-10-23.json S6 穴 B と段 2 の数(行を持たない) | 穴 B 注入 485・穴 B 既定のその他 5・段 2 注入 64・段 2 の Core 自身(既定)が GROUNDED の件 0(K-31 ほか) | 対応付けの数でありうる ― 段 2 の材料の注入で Core 自身(既定)が GROUNDED の件など。M-05 と同じ写し | D-23・D-25 |
| M-18 | 記録に該当の欄なし(記録は材料の Core 欄・行ごとの結果) | ― | 対応付けの数でありうる ― M-05 と同じ写し。診断の行 | ― |
| M-20 | 記録に該当の欄なし(記録は材料の Core 欄・行ごとの結果) | ― | 対応付けの数でありうる ― M-05 と同じ写し(recipe の claim の span)。B の検出・実証不能 | L-16・D-05 |
| M-21 | rowclaim_map_2026-10-17.json 合計 合計の欄(多対一を数えた記録) | 行 192・対応が付かない行 51・共有された行 36・共有された主張 12・T5 50・T5 のうち 1 対 1 26・T5 のうち共有 24 | 対応付けの数でありうる ― 多対一を数えた記録そのもの。位置は見ない | ― |
| M-23 | 記録に該当の欄なし(記録は材料の Core 欄・行ごとの結果) | ― | 対応付けの数でありうる ― M-05 と同じ写し(recipe の claim の span)。『Core に主張が無い』など | ― |
<!-- 門:end -->

<!-- 門:start summary -->
| 数えたもの | 数 |
|---|---|
| measure/**/*.py の file | 179 |
| 規準に当たった file | 39 |
| 仕掛け(表の行) | 24 |
| 届いたことの確かめ 有 | 7 |
| 同 無 | 10 |
| 同 不要 | 7 |
| 穴の型 同じ型 | 10 |
| 穴の型 別の型 | 0 |
| 穴の型 無し | 14 |
| file の役 仕掛け持ち(+ 使う側を含む) | 23 |
| file の役 使う側だけ | 9 |
| file の役 共通部品 | 2 |
| file の役 対象外 | 5 |
| 台帳の行(§2-4 の規準) | 42 |
| 読み 通った | 21 |
| 読み 通っていない | 10 |
| 読み 記録から分からない | 11 |
| 言えること 診断済み | 1 |
| 言えること 対応付けの数でありうる | 8 |
| 言えること 分けられない | 1 |
| cd8 の行 → claim の対応付けを持つ file(cd_material を含む) | 7 |
| 副産物の検査で見つかった規準の外の file | 6 |
| fixtures/**/*.py の file / 規準に当たった file | 53 / 0 |
<!-- 門:end -->

**前期比の注入・儀式・位置で引く仕掛け(確かめ 有)は、前の二便と同じ穴ではない。** 前期比の注入(M-15・M-19)と儀式(M-01)は、site に id を付け、注入後は同じ id の claim の値を差し替え後の値と読み返し、合わなければ `id_shift` にして通した・止めたのどちらにも数えない。lastbranch・vocab(M-12・M-24)は文の番号と位置で引いて値を読み返す。届かなかった行の語と数は表 reach。前期比の注入の側では、各 profile で同じ行が数えない欄に落ちている(語と数は表 reach)。

**差し替えが claim そのものに入る、または値・鍵を検査に直に渡す仕掛け(確かめ 不要)は、別の claim を指す対応付けを持たない。** M-02・M-04・M-06・M-07・M-09・M-10・M-17。M-02 の数は書き換えた claim の検査の欄、他の数は行の値と席の参照先(または足した fact の鍵)を engine の検査に渡した結果である。席の参照先に依る数は、席の答えに依る(対応付けの数ではない)。

**同じ型の仕掛けと、対応付けの数でありうる記録の数(記録の欄の範囲):**

- **M-08(新しい標本の注入。診断済み)**: `fixtures/xbrl/fresh/fresh_2026-10-21.json` の注入の行の『通した』(表 reach の K-38。P22 から P26 の同じ行)は対応付けの数。前の二便の診断で、その行は差し替えが基準にした claim の文の外にあった。記録は不変(読み直しは前の便の文書に日付つきで在る)。
- **M-14(評価用・調整用の注入)**: 記録の欄の範囲では、行は基準の claim の id を持ち、注入後に数えた claim の id・文の番号・位置・届いたかの欄を持たない(表 p27rec)。したがって『通した』『名指したが別の値』『名指して原本の値を返した』『止めたが名指さない』は、注入後の claim を値(円に直す)と後の字で引いた後の数で、**engine の数か対応付けの数かを記録の欄から分けられない**。『基準に対応が付かない』『対応が付かない』は、一件に決まらず None になった行の数で、engine の判定ではなく対応付けの側の数である。台帳の読みが『通った』の行(L-32・L-34・L-38・D-22・D-23・D-26・P-19・P-20)はこの数を引く。
- **M-05(cd8 の行 → claim。値が許容差の内側 かつ 数の字面が span に在る、の最初の一件)**: 材料の Core 欄(`席の前に出せる分` の Core)と、それを読む数(席に Core を足した C′、Core の特定・Core-P の特定と誤認定、『Core が正解を持っていた』)が、対応付けの数でありうる。2026-10-17 の記録 `fixtures/xbrl/cd8/rowclaim_map_2026-10-17.json` は、この対応付けが多対一になること(『対応が付かない行』『共有された行』『共有された主張』は表 reach の K-36)を既に数え、『影響するのは Core 欄だけ』と書き、『対応付けを直していない。直すのは別便』と書いて残っている。席の答え・D′・D″ はこの対応付けを通らない。
- **M-13・M-16・M-18・M-20・M-21・M-23(M-05 と同じ対応付けの写し)**: 数える記録は、p20_rerun・period_bind の段 2(E-4。default_p26・default_p27 の S6 の『全注入で Core 自身(既定)が GROUNDED』は表 reach の K-30・K-31)・pnf_diag・role_swap(contract_v1 の B が読む)・rowclaim_map・verify_inventory の Core 欄。同じ写しなので、M-05 と同じく『Core 欄の数が対応付けの数でありうる』と言える。写しの file は門が字で数える(表 summary)。
- **M-03(a_core_vs_grep の `claim_for`)**: 値(と字)で引き、一件に決まらなければ None。『対応が付いた』『対応が付かない』(表 reach の K-34・K-35)は対応付けの側の数。cd8 と gen_c の C0 の Core の特定・Core-P の特定・誤認定の数が、対応付けの数でありうる。新しい標本の M-08 の注入後の対応付けはこの `claim_for` を使う。

**台帳の読み**: 『通った』の行は、上の記録の数を引くので、その数は対応付けの数でありうる。『通っていない』の行は、この点検の範囲でその穴の型を通らない。『記録から分からない』の行(予測の当たり・外れの本数など)は、読みを決められなかった。台帳の行の字は直していない(直しは別の封)。

**言い切らないこと**: 同じ型の仕掛けの数が、engine の数だったか、対応付けの数だったかは、**位置で数えるまで言い切らない**。M-08 は位置で数えて対応付けの数と決まった。M-05 の系統は、記録(rowclaim_map)が対応付けの多対一を数えているが、行ごとに『位置で引いた claim と同じか』は数えていない。M-14 の系統は、記録に注入後の claim の id が無く、数えられない。

## 7. 言えないこと

- この点検は code と既存の記録を読むだけで、**engine を走らせていない**。届いた(文)・届いた(数)は新しく数えていない。前の二便の分類 6 語を他の記録に当てはめていない(当てはめるには engine の文の番号が要る)。
- 仕掛けごとの『届いたことの確かめ』の有・無・不要は code を読んだ判断で、機械の値ではない。門が見るのは、根拠の字が関数の中に在ること、語が決まった語であること、表どうしが合うことまで。判断の読み直しは監査がする。
- 列挙の規準は字の部分一致である。七つの字も file 名の字も持たずに本文を差し替えて engine を呼ぶ script は落ちる。副産物の検査(表 outside)は、字 `注入` を足して数えた。
- 母集団は `measure/` だけ。`fixtures/**/*.py` に規準に当たる file は無い(表 summary)が、`tests/**` の仕掛けは見ていない。
- 記録の数は記録の欄の範囲。欄が無い記録(不要の仕掛け、写しの file の多く)で『届かなかった行は 0』とは書かなかった。『確かめ 有』の仕掛けが、別の欠陥(同じ id に別の claim が来て、値がたまたま同じ)を持たないとは言っていない。
- 台帳の依存は字の規準で決めた。台帳の行が数を引いていても、記録の path・script 名・結果文書名のどれも書いていなければ落ちる。外に出した紙(PDF・HTML)は読んでいない。
- 評価用・調整用の文は repo の外にあり、開いていない(`~/.cache/audit-core/edinetdb-p27/`)。評価用・調整用の系統に同じ穴の型があっても、位置で数えていない。
- 議事録(国会会議録)は XBRL と別の領域で別の作り。XBRL の仕掛けと率を並べない。
- 読みは無い(席は呼ばない。人の目も入らない)。仕掛けの判断はこの点検の席の code の読みで、人の読みではない。

## 8. 次に測ること

この便では測らない。直すなら別の封(司令塔が決める。評価用・調整用の文を開くかは人間が決める)。

- **cd8 の系統(M-05 と写し六file・M-03)**: 材料は手元の cache の八書類(`~/.cache/audit-core/edinet/`)で費用なしで作り直せる。行 → claim を位置(engine の文の番号と文の中の位置)で引き直し、値と字の最初の一件で引いた claim と同じかを行ごとに数える。記録に持てる欄: 行の id・token の位置・位置で引いた claim の id・値で引いた claim の id・同じか・文の番号。
- **評価用・調整用の系統(M-14)**: 文は repo の外(`~/.cache/audit-core/edinetdb-p27/`)にあり、開くかは人間が決める。記録に持てる欄: 注入後に数えた claim の id と基準の claim の id が同じか・engine の文の一覧の番号(token の文・基準の claim の文)・文の中の位置・届いた(文)/届いた(数)・分類 6 語・対応の付け方(値と字 / 値だけ)。持てない欄: 文の抜粋・span・subject・value・recomputed(`p27_tune` が repo の記録に入れない欄と同じ)と、docID と文の対応を外から引ける字。いちばん安い 1 欄は『注入後の claim の id が基準の id と同じか』(文を repo に出さずに持てる)。
- **`a_core_vs_grep` の `claim_for`(M-03。cd8 と gen_c の C0 の行)**: 同じく位置で引き直す。
- **台帳の字の直し**: 『通った』の行の注記は、位置で数えた結果が出てから別の封で決める。この点検は台帳の字を直していない。
- **規準の広げ方**: 表 outside の file を規準に入れるか。

## 9. 封にない判断

封の字に無く、実装の席が決めたこと。

- 仕掛け `verify_inventory` の関数名を `part2` とした(封 §6-1 は `main`。行 → recipe の claim を引く所は `part2` の中にあり、`main` にない)。
- 副産物の検査(封 §4 の 3)の『本文を差し替える字』の集合を、封の `replace(`・`tampered` に字 `注入` を足して決めた(封は『など』。足すと封 §6-4 の 6 の六file になる。足さないと四file)。
- 仕掛けの表の語彙を決めた: 基準・注入後の対応付けに `位置(文の番号と文の中の位置)` を足し、注入の対象に `本文の字・fact の属性` を足した。`attr_inject`・`dim_hold`・`period_unit_hold`・`holds_product_path` は、本文の注入の行を作り、足した fact の鍵や行の値を検査に渡すので両方とした。
- 台帳の依存(列と読み分け)を、穴の型が同じ型の仕掛けに限った。他の仕掛けの台帳の列は『同じ型でない』。H-12 の数も同じ型の仕掛けの行(封 §6-5 の 3 の行の集合)。
- 『通った』の規則を『行の数の一つ以上が通った数』とした。混ざる行は根拠に通った数を書いた。
- H-6 の対象を『基準の対応付けが site の id、注入後が同じ id の仕掛け』とした(封の字は『基準も注入後も id で引く仕掛け』)。`kokkai_false_pass` は基準が claim の id で、注入後の値を読み返さない(確かめ 不要)ので対象に入れていない。当否は『確かめ 無が一本でもあれば外れ』(封の外れ方の字)。
- H-10 の『どちらか一方だけの行』を、P26 だけの行と P27 だけの行の和とした。
- H-14 の『`kokkai_inject` が同じ型でない』を、`kokkai_inject` が仕掛けの表に行を持たない(役が共通部品)ことと読んだ。
- 表 reach の語に、前の二便と封 §2-3 の `id_shift`・`sentence_not_found`・`missing` のほか `unmutable`(p17 の記録)と、位置で引く仕掛けの `主張が見つからない`・`値がずれた`・`文が見つからない`・`数が見つからない` を足した。`rowclaim_map`・`material` は欄の値を写した。
- 仕掛け M-05 の記録の列に `rowclaim_map` の記録を足した(『対応が付かない行』『共有された行』を同じ仕掛けの表に出すため)。台帳の行の集合は変わらない。
- 規準の外の使う側五file(cd_score・cd_ceiling・hybrid_trust・gen_c_p20・p20_pred_recheck)を別の表に足した(封 §6-4 の 6 が名を挙げている)。表の『呼んでいる検査』『差し替えの字』は『―』。
- 封 §2-3 の 1 の『型別』は、前期比の注入の行に型の欄が無いので出していない。
- 門の本数・名前: 封 §5-2 の (a)〜(g) を、門 (a)=列挙、(b)=記録・判断の表、(c)=台帳、(d)=当否、(e)=docID 等、(f)=順序、(g)=偽物で赤、の分け方で試験にした。
