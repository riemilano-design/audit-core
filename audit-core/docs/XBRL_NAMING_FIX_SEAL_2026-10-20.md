# 封: 名指しの直し ― **値が合わなかったときの最後の枝に、期の手がかり・セグメント・増減の語を見せる(P21)。engine を変える。先に予測を固定する**

2026-10-20。人間の指示(原文)「さっきコアの精度と言ったけど、アダプターの問題か。とにかく君が精度を改善して。何してもいいから」。作法は変えない: この封 → 実装(別席)→ 独立監査 GO → commit → 測定 → 結果。**数を見てから封・予測を直さない。**

## §0 何を直すか(診断は読むだけの席が 2026-10-20 に行った。木は触っていない)

汎化 C の P20 の結果(`docs/XBRL_GENERALITY_P20_RESULT_2026-10-20.md`、記録 `fixtures/xbrl/gen_c/c0_p20_2026-10-20.json`)で Core-P が T5 50 件中 29 件を外した。診断の結論: **3 型とも `adapters/xbrl/recipes.py` の `_direct_value_claim` の「値が一致する fact が無いときの最後の枝」(309〜328 行)に落ち、その枝は `CurrentYear` の先頭の fact を 1 本名指すだけで、期の手がかり(`_prior_cue`)・増減の語(`is_diff`)・セグメント名を見ていない。**

| 直し | 中身(**この枝の中だけ**) | 当たる行(gen_c、診断席が関数の差し替えで実測) |
|---|---|---|
| **F1′ 前期の手がかり** | `profile.period_cue` が真・`not is_diff`・`_prior_cue(span, a, b)` が真なら `Prior1Year…` の fact を名指す | Z4GF-T5-02・07・12・16・23(特定 +5) |
| **F2′ セグメントの枠が無い** | 主語がセグメント利益・セグメント損失で member が None なら **名指さない**(POINTER_NOT_FOUND) | Z4GF-T5-01・10・13・17(誤認定 −4。特定は増えない) |
| **F3b 増減の文は残高の対** | `is_diff` が真で当期の残高(Instant)を選んだときは、残高の対 `[当期, 前期, formula:a-b]` にする(1 本の誤った名指しをやめる。pointer 3 本なので Core-P の「特定」には入らない) | YYT4-T5-01・05・15・16、YYUD-T5-02・03、Z4GF-T5-24(誤認定 −7) |

3 つとも **profile の旗 1 つ(`Profile` に既定 False の field を 1 つ足す)の後ろに置き、`P21 = dataclasses.replace(P20, name="P21", <旗>=True)`** とする。旗の後ろなので P1〜P20 の振る舞いは変えない(P16 の golden と P20 の決定の字に触れない)。
**やらないこと(別の封)**: F2 本体(連結の無い書類でセグメントの枠を使う。GROUNDED を奪う例が実測で在る)、F4(計算書の行のラベル。GROUNDED が新しく増えるので独立したラベルが要る)、F3c(増減 → 流量の要素。判断の入る対応)、YYT4 の表のセル(表の構造を読む新しい関数)。
**既定の profile**: 段 1 では `DEFAULT_PROFILE = "P20"` のまま(製品の経路は変わらない)。段 2 で `P21` に切り替える(§4 の N-4・N-5 が当たったときだけ。人間の 2026-10-14 の決定 P16 → P20 の次の決定として、`vocabulary.py` の決定の注記に日付と根拠を足す)。

## §1 過去の門の engine の留め(**先に列挙する**。記憶 engine-change-seal-must-list-past-engine-pins)

作業木の file の sha256 を留めている門(recipes.py・vocabulary.py は BASE `2745dd5` 以後 1 度も変わっていないので、全部が赤になる):

| 門 | 留めている file | 遷移の仕組み |
|---|---|---|
| `tests/measure/test_xbrl_axis3_decision.py` | verify_document・vocabulary(`ENGINE_SHA`)、`LATER_ENGINE_COMMITS` = {295e636, ac8c3ff}。test_9 は `2745dd5..HEAD -- adapters core` の commit を全部宣言済みにすることを要る | **在る**: 新しい engine の commit を `LATER_ENGINE_COMMITS` に宣言(結果の commit で。engine の commit と結果の commit の間は test_9 が赤 = 既知) |
| `tests/measure/test_xbrl_cd_seal.py` | extract・instance・verify_document・vocabulary。`FROZEN_LATER` は instance だけ | **半分在る**: `FROZEN_LATER` に vocabulary の新しい sha と封の名前を足す |
| `tests/measure/test_xbrl_branch_a.py` | recipes・resolve・verify_document・vocabulary | 無い → **足す**(「測った時点の sha」と「後の封で変わった sha」を分ける字) |
| `tests/measure/test_xbrl_p20_result.py` | recipes・resolve・verify_document・vocabulary | 無い → 足す |
| `tests/measure/test_xbrl_pnf_diag.py` | 同 4 本 | 無い → 足す |
| `tests/measure/test_xbrl_role_swap_result.py` | core verify・comparators・resolve・recipes・verify_document | 無い → 足す |
| `tests/measure/test_xbrl_a_core_vs_grep_seal.py` | verify_document・vocabulary・inject・prepare_material・SEED | 無い → 足す |
| `fixtures/frozen_bundle_sha.py` | `FROZEN_BUNDLE_GENERATIONS` | **在る**: 新しい世代の行を足す |

触らない留め: `tests/adapters/xbrl/test_boundary.py`(import を増やさない)、`test_verify_external_v1.py`、記録の事実として `ac8c3ff` を留める門(generality・c1・p20・period_pair_stage2。作業木を比べない)、`tests/adapters/xbrl/mutations.json` の old の字(X-R1b `if prev_year_phrase and profile is not None and profile.prior2_required:`、A-R3・D-R7、G-R4、X-R7a2・X-R7a3、P20-M8 ― **これらの字は変えず、分岐を前に足す**)。
profile の字の一覧(P21 を足すと要更新): `tests/adapters/xbrl/test_vocabulary.py`、`test_p20.py`、`test_run.py`、`test_p17.py`、`tests/measure/test_xbrl_generality_seal.py`(既定 = P20 の字は段 1 では不変)。
`tests/adapters/xbrl/test_verify_entry.py` の `test_p16_matches_the_holdout_dumps` は**既定の profile**で走らせた結果を P16 の記録と比べる → 段 2(既定 = P21)で赤くなる行は **S100Z4N9 の H-124・H-067・H-120・H-122(F1′)と S100Z39P の H-075(F3b)の 5 行だけ**(診断席の実測。全部 VALUE_MISMATCH の参照先の移動で GROUNDED ではない)。段 2 ではこの 5 行を「P21 で動いた行」として字で留める。

## §2 材料と測り方(全部 0 USD。席は呼ばない)

| 材料 | 何を測るか |
|---|---|
| gen_c 8 書類の (ア)(注入 128 件、種 `measure/SEED.json`、`--profile P21`) | T5 の特定・誤認定、T1 の通し、T3 の名指し。**P20 の記録と行ごとに並べる** |
| cd8 の (ア) 8 書類(`fixtures/xbrl/cd8/a_core_vs_grep_P20_2026-10-17.json` の相手)`--profile P21` | 同上 |
| 無改変の 40 書類(gen_c 8・(ア)/final8 8・cd8 の引いた 8・開発 14・未使用 2 = 診断席の集合。**id の一覧を記録に書く**)を `verify_document` で P20 と P21 | state と参照先の行ごとの差。**GROUNDED の行で state か参照先が動いた数** |
| K-4 の 20 行(C1 の席 A 16 / 20 対 Core-P) | Core-P(P21)の特定 |
| C0-3(engine を Core-P(P21)の参照先に) | GROUNDED(= 誤りを通す) |
| 対照 | **M-C1** `--profile P20` で gen_c の (ア) を回し `c0_p20` の記録と全欄一致(旗の後ろに置いた証拠)。**M-C2** 既存の試験 `python3 -m pytest -q tests/adapters tests/core tests/golden tests/fixtures measure/tests` が緑(P16 の golden・P20 の決定・mutations)。**M-C3** 変異: 旗を P20 でも真にすると M-C1 が赤 |

## §3 予測(**測る前に固定。欄ごと・外れうる形**。数の出どころは診断席の差し替え実測。**実装が診断の数を再現するか、GROUNDED を奪わないか**がこの封の問い)

| | 予測 | **外れ方** |
|---|---|---|
| **N-1** | gen_c T5 50 件: Core-P(P21)の特定 **26 / 50**(P20 21)、誤認定 **3**(P20 19)。増えた特定はちょうど Z4GF-T5-02・07・12・16・23 | 件数か id が 1 つでも違う |
| **N-2** | cd8 (ア) T5 64 件: 特定 **46 / 64 のまま**、誤認定 **12 → 6** | どちらか違う |
| **N-3** | T1 の通し gen_c **0 / 38**・cd8 **0 / 38**。T3 の名指し gen_c **7 / 40**・cd8 **6 / 40**(どちらも不変) | 1 件でも違う |
| **N-4** | 無改変 40 書類: **GROUNDED の行で state か参照先が動いた数 0**。動いた行は VALUE_MISMATCH / POINTER_NOT_FOUND の参照先の移動だけで、合計 **120〜220 行** | GROUNDED 1 行でも / 合計が幅の外 |
| **N-5** | gen_c 8 書類の C0-1(製品の経路)の state の合計は P20 と P21 で **同じ**(GROUNDED 443・VM 194・UNVERIFIABLE 165・PNF 111)。F2′ で VM → PNF に動く行があれば、その数だけ VM が減り PNF が増える(**0〜10 行**) | 合計が 10 行超動く / GROUNDED が動く |
| **N-6** | K-4 の 20 行: Core-P(P21)**9〜12 / 20**(P20 7)、席 A 16 / 20 との差 **+20〜+35 pt** | 幅の外 |
| **N-7** | C0-3: Core-P(P21)の参照先で engine が GROUNDED にする件数 **0**(独立した証拠ではない。C0 と同じ) | 1 件でも |
| **N-8** | 対照 M-C1 全欄一致・M-C2 緑・M-C3 赤 | 1 つでも外れ |
| **N-9** | engine の差分: `adapters/xbrl/recipes.py` は `_direct_value_claim` の最後の枝の中だけ(**+40 行以下**)、`adapters/xbrl/vocabulary.py` は field 1 つ + P21 の 1 行 + `PROFILES` の登録(段 2 で DEFAULT_PROFILE)。`core/py/` **0 行**。`instance.py`・`extract.py` **0 行** | 他の file が動く / recipes +41 行以上 |
| **N-10** | `tests/adapters/xbrl/mutations.json` の old の字は全部そのまま file に 1 回在る(test_mutations 緑) | 1 つでも赤 |
| **N-11** | §1 の 7 本の門に遷移の字を足し、`pytest -q tests/measure` の赤は **axis3 の test_9 だけ**(結果の commit で宣言して消える) | 他に赤 |
| **N-12** | 段 2(既定 = P21): `test_p16_matches_the_holdout_dumps` で動く行は §1 の **5 行だけ**、全部 VALUE_MISMATCH の参照先の移動 | 6 行以上 / GROUNDED の行 |

**本当に測っているのは N-1・N-4・N-6 である。**N-4 が外れたら段 2 はやらない(既定は P20 のまま)。

## §4 限界(先に書く)

- 直すのは「値が合わなかったときの最後の枝」だけ。特定が増えるのは F1′ の 5 件だけで、F2′・F3b は**誤った 1 本の名指しをやめる**直し。Core-P の特定率は 26 / 50 = 52.0% 止まり(席 80.0%)。残り: 参照先を出さない 10 件(F4・表のセル)、セグメント枠(F2 本体)、科目違い。
- 予測の数は診断席の差し替え実測から写した。実装が同じ数を出すことと、無改変で GROUNDED を奪わないことを測る封であって、新しい標本での汎化は測らない(次の未使用書類で測る)。
- 無改変 40 書類に正解の参照先は無い(GROUNDED の不動 = 退行なし、であって正しさの証明ではない)。

## §5 触る file と順序

**段 1(engine。別席。独立監査 GO の後に commit)**: `adapters/xbrl/recipes.py`(最後の枝)・`adapters/xbrl/vocabulary.py`(field・P21)・`tests/adapters/xbrl/test_vocabulary.py` ほか profile の字の一覧(P21 を足す)・`tests/adapters/xbrl/test_recipes_p21.py`(新規: 3 つの直しの振る舞いの試験。それぞれ変異で赤)・§1 の 7 本の門の遷移の字・`fixtures/frozen_bundle_sha.py`。
**段 1 の測定(同じ席。0 USD)**: `measure/xbrl_naming_fix_2026-10-20.py` → `fixtures/xbrl/naming_fix/p21_2026-10-20.json`(§2 の全部)・`docs/XBRL_NAMING_FIX_RESULT_2026-10-20.md`・`tests/measure/test_xbrl_naming_fix_result.py`(変異 3 通り)・`tests/measure/test_xbrl_axis3_decision.py` の `LATER_ENGINE_COMMITS` に段 1 の commit を宣言・覆いの記録。
**段 2(既定を P21 に。N-4・N-5 が当たったときだけ)**: `adapters/xbrl/vocabulary.py` の `DEFAULT_PROFILE` と決定の注記・`tests/adapters/xbrl/test_verify_entry.py` の 5 行の留め・profile の既定の字の一覧・記録の追記。
**これ以外に触らない。**

**順序**: この封 + 門を commit → 段 1 実装(worktree か共有木。木を書く席は 1 つ)→ 凍結 → 独立監査 GO → engine の commit → 測定 → 監査 → 結果の commit(axis3 の宣言)→ 段 2 → 監査 → commit。**数を見てから封・予測を直さない。外れは外れとして残す。**
