# 採用条件の試験 ― T-R1・T-R2・T-R4・T-R5・T-E1・T-E2 の実装と検知の実証(2026-10-13)

人間の許可(2026-10-13): **この 6 条件だけ**を検証用 worktree で実装・検証する。**T-R3・T-E3・T-E4 は実装しない。T-R6 は整理と設計案だけで実装しない。**

## 0 3 つの状態を分ける(人間の指定)

| 状態 | 中身 |
|---|---|
| **main に保存された設計・patch** | `docs/patches/adoption_tests_2026-10-13.patch`(sha256 は下の §1)。**`recipes.py` は main では未変更**。**この patch は main の実装を守っていない**(main に `_representative`・`_assign_period_form` は存在しない) |
| **patch を適用した検証用の木** | `ce22fd0` の使い捨て worktree に 代表選択 → 抽出 v2 → この patch の順で `git apply`。**ここでのみ試験が実装を守る** |
| **実装済みの main** | **該当なし。** この作業の後も該当なし。採用は人間が決める |

**保護面(`core/py` + `adapters`)の束ね sha は main で `490888d46d034ca9eaae8e4b4d01f494919abf21a8b057e87c835d25256d7116` のまま**(作業の前後で測った)。
検証用の木で変更したのは**試験ファイル 3 本だけ**で、`recipes.py` の sha は `68ac3cc36f4e4ec540c30a42554a92c4dc928325ee1c4f2650d9676f4873a518`(2 本の patch を当てた値)から**動いていない**。

## 1 変更(ファイル・関数・理由)

| ファイル(新規) | 行 | 守る対象 | 理由 |
|---|---|---|---|
| `tests/adapters/xbrl/test_representative_selection.py` | 169 | `recipes._representative`・`_collapse_candidates`・`_direct_value_claim` の 3 呼び出し | T-R1・T-R2・T-R4 |
| `tests/adapters/xbrl/test_extraction_v2_boundary.py` | 141 | `recipes._assign_period_form` と期間の選び方 | T-E1・T-E2 |
| `tests/adapters/xbrl/test_adoption_mutation_gate.py` | 273 | 上の 2 本が**実際に欠陥を検知する**ことを留める | T-R5 |

patch: `docs/patches/adoption_tests_2026-10-13.patch`・3 ファイル・**+583 行**。**`recipes.py` への行は 0**(`grep -c` で確認)。
検証用の木での各ファイルの sha256: `4a3fbb96…1527` / `1c0727df…6b17` / `bfd8819e…77ae`。

**封じたものは 1 行も触っていない。** 封 `EXTRACTION_SEAL_V2` §2.1 の表は既存の `test_extraction_v2.py` が持ち続け、境界の追加は**別ファイル**に置いた。Golden 期待値・`core_expectation_*.json`・`mutations.json`・既存の試験ファイルは **0 行**変更。

## 2 条件と実装・試験の対応

| 条件 | 試験(名前) | 本数 |
|---|---|---|
| **T-R1** | `TR1Representative`: `test_no_jppfs_kind_returns_the_head_in_document_order`・`test_exactly_one_jppfs_kind_wins_even_when_it_is_not_the_head`・`test_two_jppfs_kinds_decide_nothing`・`test_three_jppfs_kinds_decide_nothing`・`test_same_jppfs_name_in_several_facts_takes_the_first_in_document_order` | 5 |
| **T-R2** | `TR2AllThreeCallSitesStop`: `test_single_path_stops`・`test_pair_path_stops_when_only_the_a_side_is_ambiguous`・`test_pair_path_stops_when_only_the_b_side_is_ambiguous` + 経路を通っていることを留める 2 本 | 5 |
| **T-R4** | `TR4SelectionDoesNotUseValues`: `test_representative_ignores_the_value_of_the_group`・`test_several_groups_stop_even_when_one_of_them_matches_the_claim`・`test_the_same_two_groups_bind_nothing_whatever_the_fact_values_are` | 3 |
| **T-E1** | `TE1Boundary`: `test_each_boundary_row`(7 行)・`test_the_cue_window_rows_differ_by_exactly_one_character` | 2 |
| **T-E2** | `TE2AssignmentIgnoresValues`: `test_bending_the_digits_does_not_move_the_assignment`・`test_the_pointer_does_not_move_when_the_claim_value_changes`・`test_the_pointer_does_not_move_when_the_fact_value_changes`・`test_a_value_that_does_not_match_is_not_looked_for_in_another_period` | 4 |
| **T-R5** | `AdoptionMutationGate`: `test_1_baseline_is_green`・`test_2_negative_control_does_not_turn_anything_red`・`test_3_every_mutation_is_detected_by_name_then_restored`・`test_4_every_mutation_names_a_condition_and_a_test_that_exists` | 4 |

**T-E1 の 7 行の期待値は、封 §2 の規則の字から導いた**(実装の出力を写していない)。実装前に探りで突き合わせ、**7 行とも一致**した。食い違えば試験が赤くなる形で書いてある。

## 3 なぜ専用ハーネスか・検知と「実行が失敗しただけ」をどう分けたか

**既存の `test_mutations.py` は、2 本の patch を重ねた木では使えない。** 部分木の `unittest discover` を終了コードで判定する作りだが、**変異を当てる前から 13 本落ちている**ので、どの変異も rc=1 =「赤」に見える(飽和)。実際に緑と予測された 11 本が全部「赤」になって落ちている。

専用ハーネスは部分木に**この条件のための試験 2 ファイルだけ**を置く(ZIP も Golden も読まないので基準が緑)。変異を当てた回は次の **4 つを別々に**見て、**全部満たしたときだけ検知**とする。

1. `Ran N tests` の組が**ちょうど 1 組**で、N が基準と同じ(収集が落ちていない)。
2. `errors` が 0(import やハーネスの壊れではなく assert の失敗)。
3. 落ちた試験の**名前**が、その変異に対応する名前を含む(**件数では数えない**)。
4. 終了コードが 0 でない。

**`grep -c "^FAIL:"` のような行数の合算は使わない。**

## 4 変異ごとの結果(基準・変異・陰性対照・復元)

**基準**: rc=0・`Ran [19]`(組は 1 つ)・OK・落ちた名前なし。**陰性対照**(コメントだけ変える): rc=0・`Ran [19]`・OK・復元 sha 一致。

| 変異 | 条件 | 置換 | rc | Ran | errors | 期待した名前が落ちたか | 判定 | 復元後 |
|---|---|---|---|---|---|---|---|---|
| M-R1-prefix-swapped | T-R1・T-R2 | `startswith("jppfs_cor:")` → `"jpcrp_cor:"` | 1 | [19] | 0 | はい(9 本落ちた) | **検知** | OK・sha 一致 |
| M-R2-representative-is-the-tail | T-R1 | `return group[0]` → `group[-1]` | 1 | [19] | 0 | はい(1 本) | **検知** | OK・sha 一致 |
| M-R3-one-kind-becomes-at-least-one | T-R1・T-R2 | `len(names) == 1` → `>= 1` | 1 | [19] | 0 | はい(5 本) | **検知** | OK・sha 一致 |
| M-R4-never-returns-none | T-R1・T-R2 | `return None` → `return group[0]` | 1 | [19] | 0 | はい(5 本) | **検知** | OK・sha 一致 |
| M-R5-groups-chosen-by-value | T-R4 | 候補の群を値で選ぶ | 1 | [19] | 0 | はい(2 本) | **検知** | OK・sha 一致 |
| M-E1a-diff-word-includes-zougakugaku | T-E1 | `(?!額)` を外す | 1 | [19] | 0 | はい | **検知** | OK・sha 一致 |
| M-E1b-bare-word-ignores-following-kanji | T-E1 | `[増減](?![一-龥])` → `[増減]` | 1 | [19] | 0 | はい | **検知** | OK・sha 一致 |
| M-E1c-f3-allows-percent | T-E1 | F3 の `%` 除外を外す | 1 | [19] | 0 | はい | **検知** | OK・sha 一致 |
| M-E1d-flow-item-rule-removed | T-E1 | R-2f を外す | 1 | [19] | 0 | はい | **検知** | OK・sha 一致 |
| M-E1e-baseline-cue-not-excluded | T-E1 | 比較の基準の除外を外す | 1 | [19] | 0 | はい | **検知** | OK・sha 一致 |
| M-E1f-cue-window-widened | T-E1 | `a - 15` → `a - 25` | 1 | [19] | 0 | はい | **検知** | OK・sha 一致 |
| M-E2-period-searched-again-by-value | T-E2 | 値が合わないとき別の期間を探す | 1 | [19] | 0 | はい(5 本) | **検知** | OK・sha 一致 |

**12 本すべて検知。** **M-R1 は台帳 L-021 で「統合の木でも黙った」と記録した変異①と同じ置換**で、既存の試験ではエンジンの出力が 28 行変わっても試験の数が動かなかった。**新しい試験は 9 本が落ちる。**

### 4-1 実装の途中で、ハーネスが**私自身の誤り 3 件**を捕まえた(記録として残す)

1. **同じ字数の置換は pyc が古いまま使われて変異が隠れた。** `== 1`→`>= 1`、`a - 15`→`a - 25`、`jppfs_cor:`→`jpcrp_cor:` はどれも字数が同じで、mtime の分解能(1 秒)では無効化されない。**実行ごとに pycache を捨てる**ことで直した。
2. **復元を逆向きの置換でやると別の場所に当たりうる。** **保存した原文を書き戻す**方式に直した。
3. **M-E1f の期待に、構造的に検知できない試験名を入れていた。** `test_the_cue_window_rows_differ_by_exactly_one_character` は表の宣言と印の位置だけを見るので、窓の変異を検知できない。**期待から外し、その理由を試験の中に書いた**(検知できないものを検知したと数えない)。

## 5 Golden・境界・全体試験

| 項目 | コマンド | 結果 |
|---|---|---|
| Golden 差 | `AC_OUT=… python3 fixtures/xbrl/golden_delta_2026-10-12.py .` | **1B 18・5F 11 = 29 件。統合測定の出力(`integ_golden_delta_RX2_2026-10-13.json`)と JSON が完全同一**(`==` で比較)。**Golden の期待値は 1 行も変えていない**。Golden の一致を正しい束縛の証明として使っていない |
| unittest 全体 | `python3 -m unittest discover -s tests -t .` | **最終プロセスの終了コード 1**。**最終の組は `Ran 522 tests` / `FAILED (failures=13)`**。499 → 522(+23 = 新規の試験の本数)。落ちは 13 本のまま |
| 入れ子の出力 | 同上の log | `Ran`/`FAILED` の組は **12 組**(入れ子 11 + 最終 1)。**`grep -c "^FAIL:"` は 15** ― **落ちた本数ではない。** 最終の `FAILED (failures=13)` を読む |
| pytest 全体 | `python3 -m pytest -q` | **13 failed / 605 passed**(595 → 618)。**落ちた 13 本の名前は統合測定のときと `diff` で完全一致・新規の落ち 0** |
| 新規の 3 ファイル単体 | `-p "<ファイル名>"` | 13 OK / 6 OK / 4 OK(rc=0) |
| patch の再現 | 新しい worktree で 3 本を `git apply` | `--check` rc=0、適用後に 3 ファイルとも OK |

**落ちた試験の名前は pytest 側を正とした。** unittest の log からの名前の抽出は、**入れ子の出力が失敗メッセージの中に埋め込まれる**ため信頼できない(私の行番号による抽出は 13 本のうち 8 本しか拾えなかった)。

## 6 T-R6 の整理と設計案(**実装しない**。人間の判断待ち)

### 6-1 参照先と外部出力

| | |
|---|---|
| 立てる箇所 | `recipes.py` の **5 か所**。319(`not subj` の診断枝・**main に元からある**)・343・348・370・375 |
| 入れている値 | 319 = 値が一致した fact の**要素名の種類数** / 343 = `max(len(groups_a), len(groups_b))`・370 = `len(groups)`(**畳んだ後の候補数**)/ 348・375 = **字のままの `2`** |
| Core 側で読む箇所 | **0 件**(`grep -rn "ambiguous_count" core/py`) |
| 外部出力 | `recipes.py:785` で `Claim.provenance["ambiguous_count"]` に入る。過去の計測の run の JSON **9 本**に欄として出ている |
| Golden 期待値 | **0 件**(`core_expectation_1B/1B_v2/5F` のいずれにも無い) |
| 見ている試験 | **0 本**(今回足した T-R2 は「**立っていること**」だけを見て、**値は固定していない**) |

### 6-2 候補数と曖昧の理由の意味

**封 `CANDIDATE_DEFINITION_SEAL_2026-10-12` §5 は「`ambiguous_count` は畳んだ後の候補数を入れる」と既に決めている。** 343・370 はこれに従う。
**しかし封は `_representative` が `None` を返す場合を扱っていない。** この枝では畳んだ群は **1 つ**なので、封の字どおりなら **1** になり、「候補が 1 つなのに曖昧」という読めない値になる。字のままの `2` は「`jppfs` が 2 種以上」という**別のものを数えた下限**である。

**実測(統合の木・1B + 5F + P7、`ambiguous(elements)` で停止した数の主張)**

| 値 | 立てた枝 | 件数 |
|---|---|---|
| 2 | **群が複数**(畳んだ後の候補数) | **38** |
| 2 | **代表が決まらない**(字の 2) | **4** |
| 3 | 群が複数 | 16 |
| 4 | 群が複数 | 4 |
| 14 | 群が複数 | 5 |

**`ambiguous_count = 2` は、実際の書類で 2 つの違う意味から出ている(38 件と 4 件)。読み手はどちらか区別できない。**

### 6-3 設計案(**選ばない**。人間が決める)

| 案 | 中身 | 得るもの | 失うもの |
|---|---|---|---|
| (a) | `None` の枝も封の字に合わせ、畳んだ後の候補数(= 1)を入れる | 欄の意味が 1 つになる | **1 は曖昧さを表さない**。「候補 1 件で停止」と読めてしまう |
| (b) | `None` の枝は `jppfs` の要素名の種類数(実測の 2 以上)を入れる | 下限でなく実際の数になる | 欄の意味が「候補数」と「要素名の種類数」の 2 つに割れたまま |
| (c) | 欄を分ける(候補数と、曖昧の原因の種類) | 2 つの量を混ぜない | **外部出力の形が変わる**(provenance の欄が増える)。封の追記が必要 |
| (d) | 何もしない | 変更 0 | **`2` の二重の意味が残る**。試験で値を固定できない |

**どの案も封の字を超える**ので司令塔は選ばない。**(c) は外部出力の形を変えるので、採用条件の意味の変更に当たる。**

## 7 未解決事項(隠さず全部)

1. **T-R3 は未実装。** H-R3(対の両側で代表の種類が食い違うことを許すか)が未判断。
2. **T-E3 は未実装。** H-E2・H-E3 が未判断。
3. **T-E4 は未実装。** 手がかり語が窓の端をまたぐ場合の契約が封じられていない。
4. **T-R6 は実装しない。** §6 の 4 案は人間の判断待ち。
5. **検知できない欠陥**: `test_the_cue_window_rows_differ_by_exactly_one_character` は窓の広さの変異を**構造的に検知できない**(表の宣言と印の位置だけを見る)。窓の変異を赤にするのは `test_each_boundary_row` の 2 行。
6. **概念の正しさは守っていない。** 今回の試験が守るのは「規約どおりに代表を選ぶ」「封どおりに割当を決める」「値を使わない」まで。**`N268`・`N272`(判定不能)・概念が違う 10 行・貸借と CF の区別は 1 つも守っていない**(H-1・H-E2 の未判断)。
7. **既存の `test_mutations.py` の飽和は直していない。** 2 本の patch を重ねた木では、既存の変異ハーネスは依然としてどの変異も「赤」に見える。**`mutations.json` は 1 行も触っていない。**
8. **13 本の既存の落ちはそのまま**(Golden 10 + 比較器の門 2 + 窓 1)。H-R1・H-R2・H-E1・H-E4 の未判断。
9. **独立監査は未実施。** 上の数は全部司令塔が測った。**第三者が検算していない。**
10. **main は未採用。** patch が保存されただけで、**main の実装は何も守られていない**(§0)。

## 8 完了の判定

**許可された 6 条件(T-R1・T-R2・T-R4・T-R5・T-E1・T-E2)について、正常系・対象変異・陰性対照・復元の 4 段階が確認できた**(§4)。この 6 条件の範囲では**実装・検証完了**。
**採用条件の全体は未達**(T-R3・T-R6・T-E3・T-E4 が残る)。**main 採用の承認ではない。**

---

## 訂正(2026-10-13・同日の追記。**本文は直さない**)

**§6-2 の実測の表は、立てた枝の帰属を誤っていた。** 「値 3 は群が複数 16 件 / 値 4 は群が複数 4 件 / 値 14 は群が複数 5 件」と書いたが、
枝を 1 件ずつ追って測り直すと、**値 3・4・14 は全部 `319`(= main の `237`・`len(fams)` = 要素名の種類数)から出ている**。
封が足した枝(`343`・`370`・`348`・`375`)が出す値は **2 だけ**。

正しい内訳(1B + 5F + P7。欄が埋まった主張 **67 件**):

| 立てた枝 | 入れる量 | 値 2 | 値 3 | 値 4 | 値 14 | 計 |
|---|---|---:|---:|---:|---:|---:|
| `319`(main の意味) | 要素名の種類数 | 25 | 16 | 4 | 5 | **50** |
| `343`・`370` | 畳んだ後の候補数(封 §5) | 13 | 0 | 0 | 0 | **13** |
| `348`・`375` | 字の 2 | 4 | 0 | 0 | 0 | **4** |

**§6-2 の結論「`ambiguous_count = 2` は 2 つの違う意味から出ている」は、正しくは 3 つ**(基準の意味 25 件 / 畳んだ後の候補数 13 件 / 字の 2 が 4 件)。
**「読み手はどちらか区別できない」という結論自体は変わらない**(むしろ強まる)。
全体は `CONTRACT_READING_2026-10-13.md` §1-2・人間の判定 **D-019** を参照。
