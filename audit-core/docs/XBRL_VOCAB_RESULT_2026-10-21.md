# 語彙の登録と枠の取り直し P24 ― 段 1 の結果(2026-10-21)

封: `docs/XBRL_VOCAB_SEAL_2026-10-21.md`(commit `08987d0`。**本文と予測は一字も直していない**。外れは外れとして残す)。
記録: `fixtures/xbrl/vocab_2026-10-21.json`(`measure/xbrl_vocab_2026-10-21.py --stage all --run-tests` の出力に、手で走らせた二つの欄 ― engine の変異の表と試作の読み ― を足した)。
門: `tests/measure/test_xbrl_vocab_result.py`(表と数のある文を記録から作った字で縛り、それ以外の散文に算用数字が在れば赤にする。散文は漢数字で書く)。
**0 USD・通信なし。engine の直しは人間の事前承認(2026-10-21)の範囲。既定は P22 のまま(段 1)。**

**予測 機械判定 当たり 7 / 外れ 0 / 測れない 1**(W-1〜W-8。W-9 は段 2 なので判定しない)。
engine の直し: `adapters/xbrl/vocabulary.py` 挿入 27・削除 1、`adapters/xbrl/recipes.py` 挿入 224・削除 0、`adapters/xbrl/registry_setup.py` 挿入 2・削除 0、`adapters/xbrl/comparators.py` 挿入 0・削除 0、`core/` 0 行。

## 1. 予測と実測

| # | 封の予測 | 実測 | 判定 |
|---|---|---|---|
| **W-1** | 67 書類の無改変で新しく GROUNDED になる行 **140〜156**、向きは全部 非 GROUNDED → GROUNDED。枠の取り直しが作る GROUNDED **0** | 67 書類(実数 67)の無改変で新 GROUNDED 148(型 {"語彙(CF 合計の符号)": 18, "語彙(主語の句)": 117, "語彙(手がかり語・ポイントの語)": 13})・枠の取り直しが作る GROUNDED 0 | **当たり** |
| **W-2** | 67 書類で GROUNDED → 非 GROUNDED **0〜1**。G → G(参照先が動いた)**0〜6** | GROUNDED → 非 GROUNDED 0・GROUNDED → GROUNDED(参照先が動いた)4 | **当たり** |
| **W-3** | 67 書類の VALUE_MISMATCH は **1,195〜1,211**(P23 1,418)。VM → UNVERIFIABLE(other_frame・ambiguous(member))**200〜215** | VALUE_MISMATCH P23 1,418 → P24 1,203(差 -215)・VM → UNVERIFIABLE(other_frame 198・ambiguous(member) 11)計 209 | **当たり** |
| **W-4** | 穴 B の 485 件を P24 で通す **0**、止めた行の state は P23 と全行同じ | 通した 0 / 485・止めた 483・その他 2。対照 P23 の通した 0。(結果, state)が P23 と違う行 0(reason・pointers まで含めて 0) | **当たり** |
| **W-5** | 儀式を P24 で: 通した **2〜3**、止めのうち VM → UNVERIFIABLE に移る **0〜1**(注入の対象の数は素の書類の GROUNDED で決まり 240 から動きうる。対象の数は予測しない) | 通した 2 / 247(N069・N096)・止めた 245 / 247・その他 {}。VM → UNVERIFIABLE に移った(共通の行 240 のうち)0。対照 P23 の通した 2 / 240 | **当たり** |
| **W-6** | 67 書類で P23 → P24 に GROUNDED か UNVERIFIABLE へ動いた行(G → G を含む。試作で 361 = 148 + 4 + 209。非 G → 非 G の 8 は含めない)への注入(1 回に 1 件、末尾の桁 ±3・10 倍・向きの語の反転、試作と同じ作り方)で P24 が GROUNDED にする **0** 回、止まらず UNVERIFIABLE **0〜3** 回 | 対象 361 行・注入 695 回で P24 が GROUNDED 0・UNVERIFIABLE 1・VALUE_MISMATCH 658・その他 36(対照 P23 は GROUNDED 2) | **当たり** |
| **W-7** | **新しい標本(手元の cache の 67 の外 214 書類のうち、67 と同じ抽出で claim が 1 以上の書類)**で P23 → P24 の新 GROUNDED を全部人が読み、**偽(間違った fact に結んだ)が新 GROUNDED の 3% 以下**、かつ VM → UNVERIFIABLE を全部読み「文が本当に違う」が **10% 以下**。claim が 1 以上の書類が 10 未満なら「測れない」と記録する(当たりにも外れにもしない) | 手元の cache の 67 の外 214 書類(区分 {"文なし": 214}・種別 {"jpsps…-asr-": 214})に 67 と同じ抽出をかけて claim が 1 以上の書類 0(claim 合計 0)。10 未満なので測れない | **測れない** |
| **W-8** | engine の差分 `recipes.py` **+200〜+250 / −0**、`vocabulary.py` **≤ 35 行**、`registry_setup.py` **≤ 5 行**、`comparators.py`・`core/` 0 行。既存試験の赤は登録の一覧・旗の形・sha の留め・diff の門だけ(数 / state の門 0、人間の決定の字の門 0) | vocabulary.py 挿入 27・削除 1、recipes.py 挿入 224・削除 0、registry_setup.py 挿入 2・削除 0、comparators.py 0/0、core/ 0 行。既存試験の赤(直す前)36 本、種類 {"diff の門": 5, "sha の留め": 15, "旗の形": 11, "登録の一覧": 5} | **当たり** |
| **W-9** | 段 2(既定 P22 → P24、P23 と P25 を含めてまとめて)は人間に 3 つの率(通す率・無改変で「違う」と言う率・結べない率)を見せてから | 段 2(既定 P22 → P24。P23 と P25 とまとめて)は人間に 3 つの率を見せてから。この実行では何も変えていない(DEFAULT_PROFILE = P22) | **判定しない(段 2)** |

**W-1 から W-6 は封 §0 の試作 `v3.1` の再現で、外れるなら実装が試作と違うことを示す予測である。** 実装は試作の差分(`git apply`)を入れ、封 §1 の字と一行ずつ照らした(第十二節に食い違い)。結果は、動いた行の全部が試作 `v3.1` の行と `(doc, id)` だけでなく state・reason・pointers まで一致した(第二節)。

**本当に外れうる W-7(新しい標本)は測れなかった。** 手元の cache の六十七の外の書類は、封が数えた件数のとおり全部 `jpsps…-asr-`(特定有価証券の有価証券報告書)で、六十七書類と同じ抽出(`verify_document` の既定の経路 = 経営分析の節の文を取る)をかけると経営分析の節が無く、claim は零である。claim が一以上の書類が十未満なので、封の字のとおり「測れない」と記録した(当たりにも外れにもしない)。**新しい標本で偽(間違った fact に結んだ)を測る機会は、この便では得られなかった。** cache に無い書類は取りに行かない約束なので、取りに行っていない。第六節。

## 2. W-1〜W-3 無改変の六十七書類

67 書類(claim 7,799)の無改変で、P23 から P24 に動いた行は 369。新 GROUNDED 148(語彙(CF 合計の符号) 18・語彙(主語の句) 117・語彙(手がかり語・ポイントの語) 13)。枠の取り直しが作る GROUNDED 0。GROUNDED から離れた行 0、GROUNDED のまま参照先が動いた行 4。
VALUE_MISMATCH は P23 が 1,418、P24 が 1,203(差 -215)。VALUE_MISMATCH から UNVERIFIABLE に移った行は 209(other_frame 198・ambiguous(member) 11)。GROUNDED は 4,234 から 4,382。

| 項目 | 件数 |
|---|---:|
| 書類 | 67 |
| claim の総数 | 7,799 |
| 動いた行(全 state) | 369 |
| 新 GROUNDED(GROUNDED でない → GROUNDED) | 148 |
| うち 型別 | 語彙(CF 合計の符号) 18・語彙(主語の句) 117・語彙(手がかり語・ポイントの語) 13 |
| 枠の取り直しが作る GROUNDED | 0 |
| GROUNDED → GROUNDED でない | 0 |
| GROUNDED → GROUNDED(参照先だけ動いた) | 4 |
| VALUE_MISMATCH → UNVERIFIABLE | 209 |
| うち other_frame | 198 |
| うち ambiguous(member) | 11 |
| 新しい VALUE_MISMATCH(P23 が VALUE_MISMATCH でない) | 6 |
| W-6 の対象(GROUNDED か UNVERIFIABLE へ動いた行) | 361 |

| 無改変 67 書類 | GROUNDED | VALUE_MISMATCH | UNVERIFIABLE | POINTER_NOT_FOUND |
|---|---:|---:|---:|---:|
| P23(対照) | 4,234 | 1,418 | 1,323 | 824 |
| **P24** | **4,382** | **1,203** | **1,397** | **817** |

遷移の全部(P23 の state から P24 の state):

| 向き(P23 の state → P24 の state) | 行 |
|---|---:|
| G→G GROUNDED → GROUNDED | 4 |
| 非G→G POINTER_NOT_FOUND → GROUNDED | 5 |
| 非G→G UNVERIFIABLE → GROUNDED | 131 |
| 非G→G VALUE_MISMATCH → GROUNDED | 12 |
| 非G→非G POINTER_NOT_FOUND → POINTER_NOT_FOUND | 2 |
| 非G→非G POINTER_NOT_FOUND → VALUE_MISMATCH | 2 |
| 非G→非G UNVERIFIABLE → VALUE_MISMATCH | 4 |
| 非G→非G VALUE_MISMATCH → UNVERIFIABLE | 209 |

新 GROUNDED の前の state:

| 新 GROUNDED の前の state | 行 |
|---|---:|
| POINTER_NOT_FOUND(no_element(point without prior phrase)) | 3 |
| POINTER_NOT_FOUND(no_element) | 2 |
| UNVERIFIABLE(ambiguous(elements)) | 111 |
| UNVERIFIABLE(no_subject) | 20 |
| VALUE_MISMATCH(None) | 12 |

型別(動いた行の全部):

| 型 | 行 |
|---|---:|
| 枠の取り直し・非G→非G | 209 |
| 語彙(CF 合計の符号)・G→G | 4 |
| 語彙(CF 合計の符号)・非G→G | 18 |
| 語彙(主語の句)・非G→G | 117 |
| 語彙(主語の句)・非G→非G | 6 |
| 語彙(手がかり語・ポイントの語)・非G→G | 13 |
| 語彙(手がかり語・ポイントの語)・非G→非G | 2 |

### 2-1. 試作 `v3.1` の人の読み

試作 v3.1 の人の読み(司令塔の席の読み。実装席の読みではない)を同じ行に写した: 動いた行 369 の全部が試作の行と(doc, id)・state・reason・pointers まで一致。新 GROUNDED 148 行のうち読みが正 148。枠の VALUE_MISMATCH から UNVERIFIABLE に移った 209 行は、正しい文 207・文が違う 1・分からない 1。

| 向き・型 | 試作の読みの分類 | 行 |
|---|---|---:|
| G→G・語彙(CF 合計の符号) | 改善 | 4 |
| 非G→G・語彙(CF 合計の符号) | 正 | 18 |
| 非G→G・語彙(主語の句) | 正 | 117 |
| 非G→G・語彙(手がかり語・ポイントの語) | 正 | 13 |
| 非G→非G・枠の取り直し | 分からない | 1 |
| 非G→非G・枠の取り直し | 文が違う | 1 |
| 非G→非G・枠の取り直し | 正しい文 | 207 |
| 非G→非G・語彙(主語の句) | 正しい文 | 6 |
| 非G→非G・語彙(手がかり語・ポイントの語) | 理由だけ動いた | 2 |

司令塔の席の試作 v3.1(封 §0 の下調べ。scratchpad/vocab3/proto31.json。追跡外)で**人が読んだ読み**を、同じ (doc, id) の行に写した。実装席の読みではない。今回の実装の動いた行は試作の動いた行と (doc, id) が全部一致し、state・reason・pointers が 1 行も違わない(下の各行に試作の state・reason・pointers を持たせ、門が今回の行と突き合わせる)。読みの正しさ自体は門で縛れない。

読みの注意: 読みは**司令塔の席の試作の読み**で、実装席は読み直していない。実装席が確かめたのは、動いた行の全部が試作の行と同じ(doc, id)・同じ state・reason・pointers であること(門が行ごとに突き合わせる)。読みそのものの正しさは門で縛れない。**この読みは同じ六十七書類で、規則を作った書類を測っている**(封 §0 の注意のとおり、六十七書類での偽零は新しい標本での偽零を意味しない)。枠の取り直しの代価は、文が本当に違う一行と分からない一行(`UNVERIFIABLE` に弱めたので「違う」を言わなくなる)。

## 3. W-4 穴 B(前期の値への置き換え)

穴 B の注入 485 件を P24 で再検証すると、通した 0 / 485 = 0.0%・止めた 483 / 485 = 99.6%・その他 2 / 485 = 0.4%(P23 は通した 0 / 485 = 0.0%)。P23 と P24 で(結果, state)が違った行は 0。

| 穴 B の注入 485 件 | 通した | 止めた | その他 |
|---|---:|---:|---:|
| P23(対照) | 0 | 483 | 2 |
| **P24** | **0** | **483** | **2** |
| P23 と P24 で(結果, state)が違う行 | | | 0 |

## 4. W-5 儀式

儀式を P24 で回すと、通した 2 / 247 = 0.8%・止めた 245 / 247 = 99.2%(P23 は通した 2 / 240 = 0.8%)。通した id: N069・N096。止めのうち VALUE_MISMATCH から UNVERIFIABLE に移った行は 0。

| 儀式 | 注入の行 | 通した | 止めた | その他 |
|---|---:|---:|---:|---:|
| P23(対照) | 240 | 2 | 238 | 0 |
| **P24** | **247** | **2** | **245** | **0** |
| 素の書類 GROUNDED(P23 → P24) | 329 → 340 | | | |

P24 でも通した行の中身:

| id | 分類 | 値の差 | 1 最小単位 | 文脈 |
|---|---|---|---|---|
| N069 | 丸めの帯の中(±1 最小単位) | 0.10000000000000009 | 0.1 | 売上高営業利益率は前期の7.3%から3.8%へと3.5ポイント低 |
| N096 | 退化値(字は変わるが値が変わらない) | 0.0 | None | で、内訳は関係会社株式売却損6百万円および減損損失0百万円です。 |

## 5. W-6 動いた行への注入

動いた 361 行に注入 695 回(作れなかった 0)。P24 が GROUNDED にした 0 回・UNVERIFIABLE 1 回・VALUE_MISMATCH 658 回・その他 36 回。対照の P23 は同じ注入で GROUNDED 2 回。

| 変え方・結果 | P24 | P23(対照) |
|---|---:|---:|
| 10 倍:POINTER_NOT_FOUND | 18 | 116 |
| 10 倍:UNVERIFIABLE | 0 | 2 |
| 10 倍:VALUE_MISMATCH | 316 | 216 |
| 向きの語を反対に:GROUNDED | 0 | 2 |
| 向きの語を反対に:UNVERIFIABLE | 0 | 18 |
| 向きの語を反対に:VALUE_MISMATCH | 24 | 4 |
| 末尾の桁 ±3:POINTER_NOT_FOUND | 18 | 109 |
| 末尾の桁 ±3:UNVERIFIABLE | 1 | 9 |
| 末尾の桁 ±3:VALUE_MISMATCH | 318 | 219 |

P24 が UNVERIFIABLE にした注入:

| doc | id | 変え方 | 元の字 → 後の字 | reason |
|---|---|---|---|---|
| S100YWGX | N020 | 末尾の桁 ±3 | 18.8% → 18.5% | other_frame(CurrentYearDuration_OperatingSegmentsNotIncludedInReportableSegmentsAndOtherRevenueGeneratingBusinessActivitiesMember) |

注入は動いた行(GROUNDED か UNVERIFIABLE へ動いた行)の文の数を一回に一件だけ、末尾の桁を三つ動かす・十倍・向きの語を反対にして、P23 と P24 の両方で再検証した。**P24 が GROUNDED にした注入は零**(P23 は二回通した: 向きの語を反対にしたもの)。UNVERIFIABLE にしたのは一回で、`S100YWGX` の `N020`(率 `18.8%` を `18.5%` にした注入)。別の枠(その他事業)の当期・前期の率が `18.5%` に帯の中で合ったので、枠の取り直しが「違う」を「要確認」に弱めた。封 §3 に書いた代価がそのまま一回出た。

## 6. W-7 新しい標本

手元の cache の 67 の外 214 書類に 67 と同じ抽出をかけて、claim が 1 以上の書類は 0(claim の合計 0)。

| 67 の外の書類(手元の cache) | 件数 |
|---|---:|
| 書類 | 214 |
| 区分 | 文なし 214 |
| 種別 | jpsps…-asr- 214 |
| claim が 1 以上の書類(P23) | 0 |
| claim が 1 以上の書類(P24) | 0 |
| claim の合計(P23 / P24) | 0 / 0 |
| 動いた行 | 0 |

読みの表は作れなかった(新 GROUNDED も VALUE_MISMATCH から UNVERIFIABLE への移動も零行)。**封の W-7 は、claim が一以上の書類が十以上あって初めて測れる。** 手元の cache に在る六十七の外は、特定有価証券の有価証券報告書(経営分析の節が無い型)ばかりで、この予測を測る標本として使えなかった。次に測るには、一般の有価証券報告書の書類を別に取る必要があり、それは取りに行かない約束の外(人間の決定)。

## 7. 補助

補助: 段 2 の材料 192 行(注入 64)の Core 自身は、P23 から P24 で動いた行が 0。

| 段 2 の材料 192 行の Core 自身 | 件数 |
|---|---:|
| 行 | 192 |
| 注入 | 64 |
| P23 → P24 で動いた行 | 0 |
| 注入で Core 自身 P23 が GROUNDED | 0 |
| 注入で Core 自身 P24 が GROUNDED | 0 |

封 §3 のとおり、段 2 の材料にはこの規則の形の文が無い(動いた行 零)。この材料では P24 の安全を測れない。安全は W-6 と(測れなかった)W-7 で見るはずだった。

理由 `other_frame` の Recipe が、合った枠の context を provenance に持つか(登録簿の理由の名は context を含まない固定の `other_frame`):

| 理由 other_frame の Recipe | 件数 |
|---|---:|
| other_frame の Recipe | 198 |
| provenance に context あり | 198 |

## 8. W-8 engine の差分と既存試験

既存試験の赤(直す前): 36 本。直した後の既存試験: python3 -m pytest -q tests/adapters/xbrl → 928 passed, 1 skipped in 1691.05s (0:28:11)。

| file | 挿入 | 削除 |
|---|---:|---:|
| `adapters/xbrl/vocabulary.py` | 27 | 1 |
| `adapters/xbrl/comparators.py` | 0 | 0 |
| `adapters/xbrl/recipes.py` | 224 | 0 |
| `adapters/xbrl/registry_setup.py` | 2 | 0 |
| `core/` | 0 | |

既存試験の赤(直す前)。実装席が P24 を engine に入れた直後に `tests/adapters/xbrl` と `tests/measure` を走らせて赤だった試験の全部と、その直し。**数や state を見る門・人間の決定の字の門は零。** 赤になったのは登録の一覧・旗の形・sha の留め・diff の門だけ。直しは全部「一覧に P24 を足す」「遷移を宣言する」の一行で、既存の assert を緩めてはいない。

| 試験 | 種類 | 直し |
|---|---|---|
| tests/adapters/xbrl/test_mutations.py::MutationTwoWayTest::test_all_mutations_match_their_prediction | 登録の一覧 | 変異の部分木に写された test_vocabulary の登録の一覧に P24 が無く、変異 9 本が予測と逆に赤になった。test_vocabulary の一覧 2 本を直して解消(この試験自体は直していない) |
| tests/adapters/xbrl/test_p17.py::PctToleranceTest::test_p18_is_p17_plus_the_tolerance_flag | 旗の形 | 率の旗 pct_tolerance_from_decimals を持つ profile の一覧に P24 を足した(P24 は P23 から作る) |
| tests/adapters/xbrl/test_p20.py::ProfileShapeTest::test_every_other_profile_keeps_the_flag_off | 旗の形 | 除外の一覧に P24 を足した(nonconsolidated_fallback を引き継ぐ) |
| tests/adapters/xbrl/test_recipes_p21.py::FlagShapeTest::test_only_p21_has_the_flag_on | 旗の形 | last_branch_cues を持つ profile の一覧を P21・P22・P23 から P21・P22・P23・P24 に |
| tests/adapters/xbrl/test_recipes_p22.py::FlagShapeTest::test_only_p22_has_the_flag_on | 旗の形 | period_bind を持つ profile の一覧を P22・P23 から P22・P23・P24 に |
| tests/adapters/xbrl/test_recipes_p22.py::WithoutCueTest::test_every_profile_before_p22_keeps_grounding_the_prior_fact | 旗の形 | 除外を P22・P23 から P22・P23・P24 に |
| tests/adapters/xbrl/test_recipes_p23.py::FlagShapeTest::test_only_p23_has_the_new_flag_on | 旗の形 | truncate_abs_band を持つ profile の一覧を P23 から P23・P24 に |
| tests/adapters/xbrl/test_recipes_p23.py::P22UnchangedTest::test_every_profile_but_p23_keeps_the_signed_band_under_truncate | 旗の形 | 除外を P19・P23 から P19・P23・P24 に |
| tests/adapters/xbrl/test_registry_setup.py::RegisterAllTest::test_register_all_registration_counts_from_registry | 登録の一覧 | UNVERIFIABLE の理由の数を 6 から 7、登録の総数を 30 から 31 に(other_frame を足したため) |
| tests/adapters/xbrl/test_vocabulary.py::ProfileListPinsAreSelfCheckedTest::test_every_registry_pin_matches_the_registry | 登録の一覧 | この試験自体は直していない: 下の 2 本の一覧に P24 を足すと緑になる(登録表と字の一覧の食い違いを見つける守りが効いた) |
| tests/adapters/xbrl/test_vocabulary.py::P7ProfileTest::test_p7_in_profiles_registry | 登録の一覧 | PROFILES の一覧に P24 を足した |
| tests/adapters/xbrl/test_vocabulary.py::P12P13P14ProfileTest::test_profiles_registry_lists_every_profile | 登録の一覧 | PROFILES の一覧に P24 を足した |
| tests/measure/test_xbrl_a_core_vs_grep_seal.py::FrozenTest::test_9_tools_have_not_moved | sha の留め | ENGINE_LATER の vocabulary.py の遷移を P24 の段 1 の値に(測った時点の値は注記に残す) |
| tests/measure/test_xbrl_axis3_decision.py::Axis3Test::test_9_the_engine_was_not_touched | sha の留め | ENGINE_LATER の vocabulary.py の遷移を P24 の段 1 の値に |
| tests/measure/test_xbrl_branch_a.py::PredictionTest::test_14_engine_files_are_untouched | sha の留め | ENGINE_LATER の recipes.py・vocabulary.py の遷移を P24 の段 1 の値に |
| tests/measure/test_xbrl_cd_seal.py::FrozenToolsTest::test_12_engine_and_tools_have_not_moved | sha の留め | FROZEN_LATER の vocabulary.py の遷移を P24 の段 1 の値に |
| tests/measure/test_xbrl_p20_result.py::DisciplineTest::test_11_engine_is_untouched | sha の留め | ENGINE_LATER の recipes.py・vocabulary.py の遷移を P24 の段 1 の値に |
| tests/measure/test_xbrl_period_bind_result.py::RecordTest::test_16_frozen_bundle_last_generation_is_the_working_tree_and_declares_step_2 | sha の留め | fixtures/frozen_bundle_sha.py の FROZEN_BUNDLE_GENERATIONS に世代を 1 つ足し、門が段 2 の宣言を最新から後の封の宣言を飛ばして読むようにした |
| tests/measure/test_xbrl_period_bind_result.py::RecordTest::test_8_engine_is_the_one_measured_or_a_declared_transition | sha の留め | ENGINE_LATER の recipes.py・vocabulary.py の遷移を P24 の段 1 の値に |
| tests/measure/test_xbrl_period_bind_seal.py::EngineAtSealTest::test_12_engine_sha_is_the_one_at_the_seal_or_a_declared_transition | sha の留め | ENGINE_LATER の recipes.py・vocabulary.py の遷移を P24 の段 1 の値に |
| tests/measure/test_xbrl_pnf_diag.py::DisciplineTest::test_7_engine_files_are_untouched | sha の留め | ENGINE_LATER の recipes.py・vocabulary.py の遷移を P24 の段 1 の値に |
| tests/measure/test_xbrl_role_swap_result.py::DisciplineTest::test_11_engine_untouched | sha の留め | ENGINE_LATER の recipes.py の遷移を P24 の段 1 の値に |
| tests/measure/test_xbrl_rounding_result.py::RecordTest::test_6_engine_is_the_one_measured_or_a_declared_transition | sha の留め | ENGINE_LATER(空だった)に recipes.py・vocabulary.py の遷移を P24 の段 1 の値で宣言 |
| tests/measure/test_xbrl_rounding_result.py::MutationTest::test_baseline_is_green | sha の留め | 上と同じ(基準線が engine_ok を呼ぶ) |
| tests/measure/test_xbrl_rounding_result.py::MutationTest::test_m16_a_wrong_engine_sha_is_red | sha の留め | 変異『測った時点の sha を壊すと赤』が、宣言された遷移の受け入れで赤にならなくなったので、この変異の中だけ ENGINE_LATER を空にして確かめる(変異の意図は不変) |
| tests/measure/test_xbrl_rounding_seal.py::EngineAtSealTest::test_11_engine_sha_is_the_one_at_the_seal_or_a_declared_transition | sha の留め | ENGINE_LATER を P24 の段 1 の値に(P23 の段 1 の値は注記に残す) |
| tests/measure/test_xbrl_vocab_seal.py::EngineAtSealTest::test_13_engine_sha_is_the_one_at_the_seal_or_a_declared_transition | sha の留め | ENGINE_LATER(空)に 3 file の遷移を宣言(docstring のとおり) |
| tests/measure/test_xbrl_point_prior_result.py::RecordTest::test_3_judgments_recomputed_equal_the_script_and_the_record | diff の門 | ENGINE_LATER に registry_setup.py を足し、recipes.py・vocabulary.py の遷移を P24 の段 1 の値に |
| tests/measure/test_xbrl_point_prior_result.py::DocTest::test_6_the_document_equals_what_the_record_says | diff の門 | 上と同じ |
| tests/measure/test_xbrl_point_prior_result.py::DocTest::test_7_seal_and_engine_are_untouched_since_the_seal_commit | diff の門 | 上と同じ |
| tests/measure/test_xbrl_point_prior_result.py::MutationTest::test_m0_the_genuine_samples_pass | diff の門 | 上と同じ |
| tests/measure/test_xbrl_ritual_result.py::PredictionTest::test_8_judgments_recomputed_equal_the_document_table | diff の門 | ENGINE_LATER に registry_setup.py を足し、recipes.py・vocabulary.py の遷移を P24 の段 1 の値に |
| tests/measure/test_xbrl_period_bind_seal.py::EngineAtSealTest::test_13_default_is_p22_from_step_2_and_p22_is_registered_with_the_flag | 旗の形 | period_bind を持つ profile の一覧を P22・P23 から P22・P23・P24 に |
| tests/measure/test_xbrl_rounding_seal.py::EngineAtSealTest::test_12_flags_exist_default_is_p22_and_p23_is_p22_plus_the_two_flags | 旗の形 | truncate_abs_band・pct_tolerance_from_decimals を持つ profile の一覧に P24 を足した |
| tests/measure/test_xbrl_vocab_seal.py::EngineAtSealTest::test_14_new_flags_p24_and_other_frame_do_not_exist_yet_default_is_p22 | 旗の形 | docstring のとおり『まだ無い』を『在る(旗は Profile に在って既定は偽・真なのは P24 だけ・other_frame は registry_setup.py に在る・core/ に無い)』に直した |
| tests/measure/test_xbrl_vocab_seal.py::EngineAtSealTest::test_15_p23_flags_are_unchanged | 旗の形 | 最後の assert『truncate_abs_band が真なのは P23 だけ』は P24 = P23 + 旗 2 つが引き継ぐので成り立たない。P23・P24 に直した(封の門の食い違い。封の字は不変) |

追加で、**新しい試験 file を足したために赤くなった覆いの門が三本**ある(engine と無関係。封 §4 の最後の『覆い』で直す): `test_facts_for_buyers.py`・`test_suite_coverage.py` の三本。

もう一つ、封の門 `test_xbrl_vocab_seal.py::test_15` の最後の assert(`truncate_abs_band` が真なのは P23 だけ)は、P24 が P23 に旗を積む作りなので成り立たない。P23・P24 に直した。封の字は直していない。

comparators.py は零行。封 §1 の通り旗の受け渡しは recipes.py の中で閉じた(P23 のときと違い「写しの帯」の食い違いは無い)。

## 9. engine の変異(手で走らせた)

| # | 変異 | 予測 | 実測 |
|---|---|---|---|
| M1 | recipes.py: (1) の P22 period_bind を戻す行 `hits = hits_before_bind` を `hits = hits` に | PriorCueWordsTest の zandaka・zennen_wa・zenki_space・real_documents、FlagsOffIsP23Test::test_the_battery_does_change_with_the_flags_on(5 本) | 赤 6 本(FlagsOffIsP23::each_flag_acts_alone・FlagsOffIsP23::the_battery_does_change_with_the_flags_on・PriorCueWords::real_documents・PriorCueWords::zandaka_ties_the_value_to_the_prior_year_instant_in_p24_only・PriorCueWords::zenki_space_ties_the_value_to_the_prior_year_in_p24_only・PriorCueWords::zennen_wa_ties_the_value_to_the_prior_year_in_p24_only)。**予測は外れ**: +1: FlagsOffIsP23Test::each_flag_acts_alone(電池の『前年は』の文が、語彙の旗だけの効きを見る試験にも使われていた) |
| M2 | recipes.py: _PRIOR_CLAUSE_RE_2026_10_21 の (は｜には) を (は｜には｜に) に(「前連結会計年度に」を手がかりにする) | PriorCueWordsTest::test_zenrenketsu_ni_is_not_a_cue(1 本) | 赤 2 本(PriorCueWords::zenrenketsu_ni_is_not_a_cue・DocumentLevel::nothing_that_was_grounded_in_p23_leaves_grounded)。**予測は外れ**: +1: DocumentLevelTest::nothing_that_was_grounded_in_p23_leaves_grounded(『前連結会計年度に』を手がかりにすると、実物の書類で GROUNDED から離れる行が出る = 封が代価と書いた型が実物で確かめられた) |
| M3 | recipes.py: _PRIOR_CLAUSE_RE_2026_10_21 から `｜前年は` を消す | PriorCueWordsTest の zennen_wa・real_documents、CfTotalSignTest::test_the_other_prior_cues_also_switch_the_branch、FlagsOffIsP23Test::test_the_battery_does_change_with_the_flags_on(4 本) | 赤 5 本(FlagsOffIsP23::each_flag_acts_alone・FlagsOffIsP23::the_battery_does_change_with_the_flags_on・PriorCueWords::real_documents・PriorCueWords::zennen_wa_ties_the_value_to_the_prior_year_in_p24_only・CfTotalSign::the_other_prior_cues_also_switch_the_branch)。**予測は外れ**: +1: FlagsOffIsP23Test::each_flag_acts_alone(M1 と同じ文) |
| M4 | recipes.py: _PRIOR_CLAUSE_RE_2026_10_21 から `｜[(（]前期[ 　]` を消す | PriorCueWordsTest の zenki_space・real_documents(2 本) | 赤 2 本(PriorCueWords::real_documents・PriorCueWords::zenki_space_ties_the_value_to_the_prior_year_in_p24_only)。予測どおり |
| M5 | recipes.py: _POINT_PRIOR_PHRASE_RE_2026_10_21 から `｜前事業年度末｜前事業年度` を消す | PointPhraseTest の zenjigyonendo_matsu・zenjigyonendo・real_document、FlagsOffIsP23Test::test_the_battery_does_change_with_the_flags_on(4 本) | 赤 6 本(FlagsOffIsP23::the_battery_does_change_with_the_flags_on・PointPhrase::a_wrong_value_is_stopped_not_rubber_stamped・PointPhrase::real_document・PointPhrase::the_direction_word_still_sets_the_sign・PointPhrase::zenjigyonendo・PointPhrase::zenjigyonendo_matsu)。**予測は外れ**: +2: PointPhraseTest::a_wrong_value_is_stopped_not_rubber_stamped・the_direction_word_still_sets_the_sign(同じ『前事業年度末』の文を使う試験が予測から漏れていた) |
| M6 | recipes.py: _POINT_PRIOR_PHRASE_RE_2026_10_21 に `｜前期` を足す | PointPhraseTest::test_zenki_space_is_not_a_point_phrase(1 本) | 赤 1 本(PointPhrase::zenki_space_is_not_a_point_phrase)。予測どおり |
| M7 | recipes.py: 新しい資金の句の Prior2Year 以前を外す行 `hits = [(f, how) for f, how in hits if f["context"].startswith(("CurrentYear", "Prior1Year"))]` を `hits = hits` に | FundSubjectTest::test_the_new_phrases_do_not_bind_to_prior2year(1 本) | 赤 1 本(FundSubject::the_new_phrases_do_not_bind_to_prior2year)。予測どおり |
| M8 | vocabulary.py: ("投資活動による資金の減少", _CF_INV) を _CF_FIN に | FundSubjectTest::test_each_phrase_maps_to_the_cash_flow_element_of_its_activity(1 本) | 赤 1 本(FundSubject::each_phrase_maps_to_the_cash_flow_element_of_its_activity)。予測どおり |
| M9 | recipes.py: (4) の `_cf_total_prior_cue(s, m.start(), profile)` を `True` に(手がかりが無くても入る) | CfTotalSignTest::test_without_a_cue_it_is_p23_unchanged(1 本) | 赤 1 本(CfTotalSign::without_a_cue_it_is_p23_unchanged)。予測どおり |
| M10 | recipes.py: _cf_total_text_claim の `"GROUNDED" if actual == sg` を `actual != sg` に | CfTotalSignTest の sign_decides・wrong_direction・negative_prior・other_prior_cues・real_documents、DocumentLevelTest::test_nothing_that_was_grounded_in_p23_leaves_grounded(6 本) | 赤 4 本(CfTotalSign::the_other_prior_cues_also_switch_the_branch・CfTotalSign::with_a_cue_the_prior_year_value_sign_decides・CfTotalSign::with_a_cue_the_wrong_direction_is_stopped・CfTotalSign::with_a_negative_prior_year_value_the_decrease_is_right)。**予測は外れ**: -2: real_documents と DocumentLevelTest が黙った。文字の主張の最終の state は Core が pointer の comparator(builtin:flow_sign(cur)==direction)で再計算して決めるので、builder の raw result を反転しても実物の書類の state は変わらない。予測が raw result と最終の state を同じものと見ていた誤り(raw result を見る合成の試験 4 本だけが赤) |
| M11 | recipes.py: _unbind_other_frame で `claim["result"] = None` を `claim["result"] = "GROUNDED"` に | FrameRebindTest の direct_value_one_other_frame・matches_only_a_member_frame・two_other_frames・difference・ratio・percent・never_a_grounded・real_documents_through_core、DocumentLevelTest::test_a_frame_rebind_never_ends_in_grounded(9 本以上) | 赤 10 本(FrameRebind::ambiguous_recipe_has_no_other_frame_provenance・FrameRebind::difference_of_current_and_prior・FrameRebind::direct_value_matches_only_a_member_frame・FrameRebind::direct_value_one_other_frame・FrameRebind::it_never_makes_a_grounded_claim・FrameRebind::percent_change・FrameRebind::ratio_of_current_to_prior・FrameRebind::real_documents_through_core・FrameRebind::the_recipe_uses_the_registered_reason_and_keeps_the_context_in_provenance・FrameRebind::two_other_frames_are_ambiguous)。予測の本数の中。本数は『9 以上』の中。名前は一部違う: DocumentLevelTest::a_frame_rebind_never_ends_in_grounded は黙り(最終の state は reason で決まり、raw の GROUNDED は Core に届かない)、recipe の試験 2 本が赤 |
| M12 | recipes.py: _unbind_other_frame の `if len(found) == 1:` を `if len(found) >= 1:` に | FrameRebindTest::test_two_other_frames_are_ambiguous、test_ambiguous_recipe_has_no_other_frame_provenance(2 本) | 赤 2 本(FrameRebind::ambiguous_recipe_has_no_other_frame_provenance・FrameRebind::two_other_frames_are_ambiguous)。予測どおり |
| M13 | recipes.py: 最後の枝の frame_rebind の入口から前期の手がかりの 2 つの `not` を外す | FrameRebindTest::test_a_prior_cue_keeps_the_old_behaviour(1 本) | 赤 1 本(FrameRebind::a_prior_cue_keeps_the_old_behaviour)。予測どおり |
| M14 | recipes.py: _other_frame_current_facts の `startswith("CurrentYear")` を `startswith(("CurrentYear", "Prior1Year"))` に | FrameRebindTest::test_it_does_not_widen_to_a_prior_year_frame(1 本) | 赤 1 本(FrameRebind::it_does_not_widen_to_a_prior_year_frame)。予測どおり |
| M15 | recipes.py: _other_frame_current_facts の「member が 2 つ以上なら除く」の 2 行を消す | FrameRebindTest::test_a_member_in_a_multi_member_context_is_not_a_candidate(1 本) | 赤 1 本(FrameRebind::a_member_in_a_multi_member_context_is_not_a_candidate)。予測どおり |
| M16 | recipes.py: provenance に other_frame を入れる `if raw.get("other_frame") is not None:` を `if False:` に | FrameRebindTest の the_recipe_uses_the_registered_reason_and_keeps_the_context_in_provenance・real_documents_through_core(2 本) | 赤 2 本(FrameRebind::real_documents_through_core・FrameRebind::the_recipe_uses_the_registered_reason_and_keeps_the_context_in_provenance)。予測どおり |
| M17 | registry_setup.py: "other_frame" を登録の一覧から消す | FlagShapeTest::test_other_frame_is_a_registered_unverifiable_reason と、Core を通す FrameRebindTest::test_real_documents_through_core、DocumentLevelTest の 1 本以上(3 本以上) | 赤 7 本(FlagShape::other_frame_is_a_registered_unverifiable_reason・PriorCueWords::real_documents・FundSubject::real_document_phrases_are_registered_only_in_p24・CfTotalSign::real_documents・FrameRebind::real_documents_through_core・DocumentLevel::a_frame_rebind_never_ends_in_grounded・DocumentLevel::nothing_that_was_grounded_in_p23_leaves_grounded)。予測どおり |
| M18 | recipes.py: _vocab_flag を常に True に | FlagsOffIsP23Test の battery_is_identical・each_flag_acts_alone と、P23 との対照を持つ語彙の試験の多く(15 本以上) | 赤 14 本(FlagsOffIsP23::each_flag_acts_alone・FlagsOffIsP23::the_battery_does_change_with_the_flags_on・PriorCueWords::real_documents・PriorCueWords::zandaka_ties_the_value_to_the_prior_year_instant_in_p24_only・PriorCueWords::zenki_space_ties_the_value_to_the_prior_year_in_p24_only・PriorCueWords::zennen_wa_ties_the_value_to_the_prior_year_in_p24_only・PointPhrase::dou・PointPhrase::real_document・PointPhrase::zenjigyonendo・PointPhrase::zenjigyonendo_matsu・FundSubject::real_document_phrases_are_registered_only_in_p24・FundSubject::the_new_phrases_do_not_bind_to_prior2year・CfTotalSign::real_documents・CfTotalSign::with_a_cue_the_prior_year_value_sign_decides)。**予測は外れ**: 14 本で下限の 15 を 1 本割った(幅の外) |
| M19 | recipes.py: _build_point_diff_claim_2026_10_21 の窓 `a - 25` を `a - 5` に | PointPhraseTest の zenjigyonendo_matsu・zenjigyonendo・real_document、FlagsOffIsP23Test::test_the_battery_does_change_with_the_flags_on(4 本) | 赤 6 本(FlagsOffIsP23::the_battery_does_change_with_the_flags_on・PointPhrase::a_wrong_value_is_stopped_not_rubber_stamped・PointPhrase::real_document・PointPhrase::the_direction_word_still_sets_the_sign・PointPhrase::zenjigyonendo・PointPhrase::zenjigyonendo_matsu)。**予測は外れ**: +2(M5 と同じ文を使う 2 本) |
| M20 | recipes.py: build_raw_claims の資金の句の足し込み(`profile = dataclasses.replace(profile, subjects=tuple(V.CF_FUND_SUBJECTS_2026_10_21) + tuple(profile.subjects))`)を `pass` に | FundSubjectTest::test_real_document_phrases_are_registered_only_in_p24、CfTotalSignTest::test_real_documents(2 本) | 赤 2 本(FundSubject::real_document_phrases_are_registered_only_in_p24・CfTotalSign::real_documents)。予測どおり |
| M21 | recipes.py: _prior_cue_clause_2026_10_21 の節の切り(`cut = max(seg.rfind("、"), seg.rfind("。"))`)を `cut = -1` に | PriorCueWordsTest::test_the_cue_must_be_in_the_same_clause(1 本) | 赤 1 本(PriorCueWords::the_cue_must_be_in_the_same_clause)。予測どおり |
| M22 | recipes.py: _cf_total_facts の `_CF_TOTAL_RE.match(...)` を常に真に | CfTotalSignTest::test_a_non_cash_flow_total_is_unchanged_even_with_a_cue(1 本) | 赤 2 本(CfTotalSign::a_non_cash_flow_total_is_unchanged_even_with_a_cue・HumanDecisions::1b_no_prior2_stops_without_substituting)。**予測は外れ**: +1: HumanDecisionsTest::1b_no_prior2_stops_without_substituting(CF 合計の要素に限る守りが無いと §1b の止め(人間の決定)が破れる = この守りは人間の決定を守っている) |
| M23 | recipes.py: _prior_cue_clause_2026_10_21 の閉じた括弧を除く行 `seg = re.sub(r"[(（][^()（）]*[)）]", "", s[:pos])` を `seg = s[:pos]` に(追加の変異。試験 1 本 test_a_cue_inside_an_earlier_closed_parenthesis_does_not_count を足した後に予測) | PriorCueWordsTest::test_a_cue_inside_an_earlier_closed_parenthesis_does_not_count(1 本) | 赤 2 本(PriorCueWords::a_cue_inside_an_earlier_closed_parenthesis_does_not_count・DocumentLevel::nothing_that_was_grounded_in_p23_leaves_grounded)。**予測は外れ**: +1: DocumentLevelTest::nothing_that_was_grounded_in_p23_leaves_grounded(実物の書類に、閉じた括弧の中の手がかりに頼る行が在る) |

engine の変異 23 通りは、作業木とは別のコピー(scratchpad の使い捨ての木)の recipes.py・vocabulary.py・registry_setup.py に 1 つずつ入れ、tests/adapters/xbrl/test_recipes_p24.py だけを走らせ、毎回コピーを作り直して戻した(木は最後に消した。実木は 1 字も触っていない)。予測は実走の前に固定した(impl1/mut_predictions.txt。M23 は試験を 1 本足した後に追加)。手で走らせた。この表は記録の写しを門が縛るだけで、変異そのものを毎回走らせてはいない。M1〜M22 は試験 67 本、M23 は 68 本の基準線(どちらも全緑)。全部赤: 黙った変異は 0。予測の当たり 14・外れ 9(外れの向きは『赤が多かった』が 7・『少なかった』が 2)。

## 10. 限界

- 試作の読みは同じ六十七書類(規則を作った書類)の読みで、新しい標本では測れなかった。偽零は新しい標本の偽零を意味しない。
- 枠の取り直しは、別の枠の率が帯の中で合うとき、注入した誤りを UNVERIFIABLE にする。「違う」を「要確認」に弱める代価がある(第二節・第五節)。
- 「前期同期」(誤字)の文、増減の数・支出の減少率を当期の値や符号つきの率と照合する型の正しい文は VALUE_MISMATCH のまま(封 §3)。
- 手がかりの無い CF 合計の文字の主張は P23 のまま(前期・前々期の対の符号で、偶然に合う行がある)。
- 登録する語は六十七書類の字。別の提出者の言い回しは測れなかった(第六節)。
- 段 2 の材料(百九十二行)にはこの規則の形の文が無く、この材料では安全を測れない。
- 「違う」のうち最後の枝の名指し・率の再計算で対が無い・増減で対が無い・向きの語は、この封では直らない(P25 の封)。単位(店舗・社・台・株・倍・件)は fact が無いので登録していない。
- 変異の表は手で走らせた記録の写しで、毎回は走らせない。

## 11. 次

- 段 2(既定 P22 から P24 への切り替え)は **P23 と P25 を含めてまとめて**、通す率・無改変で「違う」と言う率・結べない率の三つを人間に見せてから(W-9 は判定しない)。
- `test_xbrl_axis3_decision.py` の `LATER_ENGINE_COMMITS` への段 1 の engine commit の宣言は、commit の後の次の便。
- 独立監査(`step-auditor`)の GO を経てから commit する。
- 新しい標本が要る(第六節)。取りに行くかは人間の決定。

## 12. 迷った点・封と実物の食い違い

- **封 §1 の四番目(CF 合計の符号)の括弧「(増加・減少・獲得・使用・支出)」**: 獲得・使用・支出は、この engine の向きの語の一覧(`extract.DIRECTION_WORDS` の十七語)に無い(資金の主語の句の中にだけ在る)。実装は一覧の十七語の全部に同じ枝を使い、語で絞っていない。試作 `v3.1` と同じ。
- **封の門 `test_15`**: 第八節のとおり、P24 が積む旗で成り立たない assert を P23・P24 に直した(封の字は不変)。
- **空白**: 封 §1 の一番目(前期の手がかり語)の「(前期␣」の空白は、実装では半角と全角の両方(`[ 　]`)。抽出が NFKC で全角を半角にするので、実物では半角。
- **覆いの三本と test_mutations**: 覆いの三本は封の W-8 の字の種類に無いが、engine と無関係(新しい試験 file の数)なので別に載せ、W-8 の判定には含めなかった。`test_mutations.py` の赤は変異の部分木に写された `test_vocabulary` の一覧が原因なので「登録の一覧」に分けた(封 §0 は別の項目に数えていた)。
- **W-7 の標本**: 第六節。手元の cache の六十七の外に一般の有価証券報告書が無いので測れなかった。claim が一以上の書類の数を数える抽出は、六十七と同じ経路(`verify_document` の既定)をそのまま使った。他の抽出(経営分析以外の節)を足すと「同じ抽出」でなくなるので足していない。
- **試作の読みの使い方**: 動いた行の全部が試作の行と同一だったので、試作の読みを今回の行に写した。実装席が読んだものではない(第二節)。

## 13. 再現

```
cd audit-core
python3 measure/xbrl_vocab_2026-10-21.py --stage all --run-tests        # 記録を書く(約 一時間。tests/adapters/xbrl の pytest を含む)
python3 measure/xbrl_vocab_2026-10-21.py --stage w4 --docs S100YXLE --out /path/to/w4.json   # 軽い走らせ直し
python3 -m pytest -q tests/adapters/xbrl/test_recipes_p24.py              # P24 の engine の試験
python3 -m pytest -q tests/measure/test_xbrl_vocab_result.py              # 門
AUDIT_CORE_VOCAB=1 python3 -m pytest -q tests/measure/test_xbrl_vocab_result.py   # 全部の走らせ直し
```

記録の所要秒: {"S2": 11.6, "W1W2W3": 66.5, "W4": 191.6, "W5": 44.6, "W6": 975.8, "W7": 85.2, "W8": 1691.4, "provenance": 30.7, "全体": 3106.3}。
