# 封: 前期の手がかりがある数を当期の fact に落とさない engine 規則 PB(P32E = P30E + 旗 `prior_cue_bind_2026_11_06`。既定 P27 は不変)― 2026-11-06

前の便: 期の取り違えの注入 T9(封 3a6aefa → 結果 d74f491)と第 2 便(封 ec00fa1 → 結果 9d0c8cb・README b507f9b・台帳 fe8946e)。「前期」と書かれた数に同じ要素の当期の値を入れた注入を P30E が通した率 138 / 141 = 97.9%(engine の直接値の枝は「前期」の手がかりで前期の fact を先に見るだけで縛らない)。この封は engine にその縛りを足す。

## §0 材料と決めごと

### §0-1 測った事実(この封を書く前に司令塔が 0 USD で数えた。試作は scratchpad/numfix/proto_pb(engine の写しに §1 の block を入れたもの)、script は scratchpad/numfix/pbind/)

1. engine の読み(`adapters/xbrl/recipes.py` `_direct_value_claim`): 数が当期の fact に GROUNDED になる枝は 3 つ。(ア) 最初の枝 `if hits and not (is_diff and subj)`(C2 の `_prior_cue` は hits を Prior1Year が先になるよう並べ替えるだけ。P22 `period_bind` は手がかりが**無い**数から Prior1Year を外す逆向き)。(イ) 導出 a−b の後の `elif hits:`(増減の語がある数 = is_diff が、値の合った fact に結ぶ枝「diff phrase but value matched a fact」)。(ウ) 最後の枝の P27E B `_last_branch_decide_2026_10_27`(相対の近さで名指す。値が一致すれば GROUNDED)。前期の fact を名指して VALUE_MISMATCH にする F1′ は `not is_diff` のときだけ。`_prior_cue(s, a, b)` の `a, b` は数の字の始まりと終わり(単位を含まない)で、窓の枝(直前 12 字が 前期・前期末・前連結会計年度・前事業年度・前年同期・(同 で終わる)と「から」の枝(直後 2 字が「から」= 「32.5%から29.8%へ」の前の数)を持つ。
2. 試作 第 1 版(最初の枝の前で「`_prior_cue` 真かつ hits に Prior1Year が無ければ CurrentYear の hit を外す」だけ)の下調べ: AI の文 200 本で P30E → P32E の動いた行 6(全部 既存の行で札 真: GROUNDED → VALUE_MISMATCH 4・UNVERIFIABLE → POINTER_NOT_FOUND 2)。6 行のうち 3 行は「営業外収益3億円から営業外費用1億円を」「当期純利益10.6億円から配当4.1億円を」「発行による収入317万円から」= 「A から B を」の A が「から」の枝で手がかり真になる偽陽性。T9 の 141 行では GROUNDED 138 → 14 で、残った 12 行(手がかり真)は「(前期56億1480万円)と減少」のように増減の語がある数(is_diff)が (イ)(ウ) から GROUNDED。手元の 97 書類の原文で動いた行 1(UNVERIFIABLE → POINTER_NOT_FOUND)・GROUNDED 6,568 不変。
3. 試作 第 2 版(§1 の字 = 窓だけの手がかり + 最後の枝の名指し)の下調べ: AI の文 200 本で P30E → P32E の動いた行(state か pointer が違う)54: GROUNDED → VALUE_MISMATCH 1(既存・札 真。「切下額は0.6億円(前期0.3億円)」の 0.3 が当期の fact に GROUNDED だった行 → 前期の fact を名指す)・POINTER_NOT_FOUND → VALUE_MISMATCH 16(既存 9 = 札 真 5・偽 4、新 7)・VALUE_MISMATCH のまま pointer が CurrentYear → Prior1Year 36(既存 20 = 札 真 12・偽 8、新 16)・UNVERIFIABLE → POINTER_NOT_FOUND 1(札 真)。GROUNDED 11,260 → 11,259。手元の 97 書類の原文で動いた行 19(UNVERIFIABLE → VALUE_MISMATCH 12・POINTER_NOT_FOUND → VALUE_MISMATCH 6・UNVERIFIABLE → POINTER_NOT_FOUND 1)、動いた書類 5 / 97、GROUNDED 6,568 不変(失う行 0)。T9 の id の対応付けの 141 行(記録 9d0c8cb)を P32E で判定: 手がかり真 129 行は 前期の fact を名指して VALUE_MISMATCH 128・別の要素の前期の fact に GROUNDED 1(値の偶然一致。T9 の第 2 便と同じ行)・当期の fact に GROUNDED 0。手がかり偽 12 行は P30E と同じ(GROUNDED 11・VALUE_MISMATCH 1)。P30E の判定は 141 / 141 が記録と同じ。
4. 前の便の下調べ(T9 の結果 §3 の 8): 無改変の 200 本で、仕掛けの identified の参照先が CurrentYear の数 627 のうち `_prior_cue` 真 13、P30E が当期に GROUNDED かつ手がかり真 0。

### §0-2 司令塔の決定(人間の言葉「それで任せる進めて」2026-11-06 = 司令塔の意見 1〜7(1 期の手がかりを縛る engine 規則を最優先で設計・2 規則 T は独立して再評価・3 T7 の帯幅は触らない・4 T5 の仕掛け・5 O は外す方向・6 既定 P27 と main は保留・7 worktree)の順で進める委任。engine の変更を含む)

1. 規則は **profile の旗の後ろだけ**で、既定 P27・P27E〜P30E は 1 行も変わらない。新しい profile は E 系だけ **P32E = P30E + 旗**(P31 は規則 T の下書き `docs/XBRL_TABLE_PERIOD_ENGINE_SEAL_2026-11-03.md` に取り置く。P32 は作らない)。
2. 手がかりは**数の直前 12 字の窓だけ**(`_prior_cue` の窓の枝と同じ語・同じ窓)。「から」の枝は使わない(§0-1 の 2 の偽陽性 3 行)。`_prior_cue` の字は変えず、新しい関数 `_prior_cue_window_2026_11_06(s, a)` で持つ。
3. 縛った後の state は **前期の fact を名指して VALUE_MISMATCH**(F1′ と同じ名指し)。POINTER_NOT_FOUND に落とさない(値検索と区別がつかなくなる)。前期の fact が無い要素なら従来の枝に落ちる。
4. 委任に含めないもの: 既定 profile P27・main へのマージ・規則 T の下書きの commit・T7 の帯幅。O を外す便・T5 の仕掛けの便は別の封。

## §1 規則の字(engine。全部旗 `prior_cue_bind_2026_11_06` が真のときだけ通る。偽なら 1 行も変わらない)

1. **新しい関数** `_prior_cue_window_2026_11_06(s, a)`: `s[max(0, a - 12):a]` が `_PRIOR_CUE_RE` か `_PRIOR_PAREN_RE` に当たれば真(「から」の枝は無い)。
2. **A(最初の枝の前)**: C2 の並べ替え・P22 `period_bind`・P24 の行の**後**、`if hits and not (is_diff and subj):` の**前**に: 旗が真・窓の手がかりが真・hits が空でない・hits に context が `Prior1Year` で始まる fact が無い、のとき `hits` から context が `CurrentYear` で始まる fact を外す(Prior2Year 以前は残す)。外した後は従来の枝(導出 a−b → 最後の枝)に落ちる。
3. **B(最後の枝)**: `cur` が空でなく §1b の止め(前々期が無い「前連結会計年度は…」)の**後**、`last_branch_cues` の block の**前**に: 旗が真・窓の手がかりが真のとき、`fs` の `Prior1Year` の fact があれば先頭を名指して `VALUE_MISMATCH`(pointer・bound・recomputed・reason "value differs(segment/other period?)" は F1′ と同じ字)で return。増減の語(is_diff)があっても同じ。`Prior1Year` の fact が無ければ何もしない(下へ)。
4. 当たる例: 「前期の2百万円」(fact: 前期 2,459,000・当期 221,071,000)を「前期の2億円」に替える → P30E は当期の fact に GROUNDED、P32E は前期の fact を名指して VALUE_MISMATCH。「売上原価は56億円(前期50億円)と減少」の「50億」を当期の値に替える(is_diff)→ P32E は前期の fact を名指して VALUE_MISMATCH。当たらない例: 「営業外収益3億円から営業外費用1億円を引く」の 3億(「から」の枝だけ)→ P30E と同じ。「前期比 2.9% 増の 100億円」(末尾が 比)→ 同じ。前期の fact に値が合う「前期 50億円」→ 今までどおり前期の fact に GROUNDED。旗が偽(P30E)→ 全部今までどおり。

## §2 engine の範囲

### §2-1 触る file(`core/`・`extract.py`・`verify_document.py`・`comparators.py`・`registry_setup.py`・`report_customer.py` は 0 行。既存の行の書き換えは 0 行。挿入だけ)

| file | 足すもの | 行数の見込み(挿入) |
|---|---|---|
| `adapters/xbrl/recipes.py` | 関数 1 つ(注記つき)+ block A(4〜6 行)+ block B(9〜12 行) | 18〜28 |
| `adapters/xbrl/vocabulary.py` | 旗 1 つ(注記つき。`rounding_mixed_2026_11_04` の直後)・P32E・`PROFILES` | 4〜6 |

- 試験: `tests/adapters/xbrl/test_recipes_p32e.py`(新しい file)。§1 の 4 の当たる例・当たらない例を小さい文と fact で(`test_recipes_p24` の `num_claims` の土台)。P30E と P32E が「当たらない」の例で同じ出力。is_diff の例で B が名指す。前期の fact が無い要素の例で従来どおり。`V.P32E` の旗・`PROFILES`・`DEFAULT_PROFILE == "P27"`・旗の欄の位置。変異で赤: 窓の関数に「から」の枝を足す・A の Prior1Year の条件を外す(常に外す)・A を CurrentYear でなく全部外す・B を is_diff のときだけに狭める・B の名指しを GROUNDED にする・B の名指しを POINTER_NOT_FOUND(pointer なし)にする・旗の block を外す・P32E の旗を偽にする。

### §2-2 触る枝の中の人間の決定(字も振る舞いも壊さない。新しい行は旗が真のときだけ通る block)

1. C2(2026-10-13)`_prior_cue` の並べ替え・`_prior_cue` の字(「から」の枝を含む): 変えない。PB は別の関数と後ろの block。
2. P22 `period_bind`(2026-10-20)・P24 `vocab_2026_10_21`/`frame_rebind`(2026-10-21): 字は変えない。A は P24 の `hits = hits_before_bind` の**後**に置く。
3. 案ア(2026-10-08。主語なしは結ばない)・§1b の止め(前々期が無い「前連結会計年度は…」): 変えない。B は §1b の止めの後。
4. P21 F1′・F2′(2026-10-20)・P25・P26 G2/G3・P27E B: 字は変えない。B は `last_branch_cues` の block の前で return する(F2′ のセグメント利益の止めより前に効く。§3 の E-6 で数える)。
5. N(c43517d)・RB(d81d35f)・O・P27E・P28〜P30E の規則と旗: 字は変えない。
6. **既定 `DEFAULT_PROFILE = "P27"`**(人間 2026-11-03): 変えない。P16〜P30E を明示した試験の数は 1 つも変えない。

### §2-3 既存の門の engine の留め(実装の便で同じ便に宣言された遷移を足す。測った当時の値は消さない。前例 RB d81d35f・impl_brief_rb.md)

- `recipes.py`(sha16 `86fd620840807ed7`、留める門 37 file)・`vocabulary.py`(`5b9fe3711a00fce3`、38 file)の sha16 を留める門に、宣言の行 `(新しい sha16, "docs/XBRL_PRIOR_CUE_BIND_ENGINE_SEAL_2026-11-06.md")` を前例と同じ形で足す。`comparators.py` は触らない(宣言は不要)。`test_xbrl_default_p27_result.py` の `ENGINE_DECL` の numstat の上限は挿入分だけ上げる(recipes 85 → 85 + 挿入、vocabulary 35 → 35 + 挿入。削除 0 は変えない)。
- 束ねた指紋 `adapter_xbrl_py_sha256`(前の値 `4ea77c93…`。`ENGINE_FP_LATER`)の新しい値と、`fixtures/frozen_bundle_sha.py` の世代 +1。profile の名前の一覧に P32E。`test_xbrl_axis3_decision.py` の `LATER_ENGINE_COMMITS` は次の便(test_9 は赤のままでよい)。
- 新しい門で engine の留めを定義するときは `ENGINE_LATER`・`UNTOUCHED`・`PIN_DEF`・`LATER_ENGINE_COMMITS`・`FROZEN_LATER`・`ENGINE_TRANSITIONS` を行頭の名前に使わない。
- 見込み: 直す試験 file 40〜75。

## §3 事前予測(**実装より先に固定。結果を見てから書き換えない**。外れは外れとして残す)

| # | 欄 | 予測(幅) | 外れ方 |
|---|---|---|---|
| E-1 | engine の差分(封の commit から engine の commit まで): `recipes.py` 挿入 / 削除、`vocabulary.py` 挿入 / 削除、`comparators.py`・`core/`・他の adapters の file | 18〜28 / 0、4〜6 / 0、0 | 削除 1 行以上か幅の外 = §2-1 の約束と違う |
| E-2 | 旗が偽の不変: 97 書類の P22〜P30E の出力の sha256(engine の欄を除く)が RB の便の記録 `fixtures/xbrl/rmix/regress97_2026-11-04.json` と一致する書類、T9 の id の対応付けの 141 行の P30E の state が記録 9d0c8cb と同じ行 | 97 / 97、141 / 141 | 1 つでも違えば旗が偽の経路が変わった |
| E-3 | 97 書類の原文で P30E → P32E: GROUNDED を失う行 / 動いた行 / 動いた書類 | 0 / 15〜25 / 3〜8 | 失う行 1 以上 = 有報の原文を壊す。幅の外 = 試作と本物が違う |
| E-4 | AI の文 200 本で P30E → P32E: 動いた行(state か pointer が違う)/ GROUNDED を失う行(うち札 真)/ POINTER_NOT_FOUND → VALUE_MISMATCH の行 | 45〜65 / 0〜2(0〜2)/ 12〜20 | 幅の外。失う行 3 以上 = 代価が試作より大きい |
| E-5 | T9 の 141 行の P32E(手がかり真 129 行): 当期の fact に GROUNDED / 前期の fact を名指して VALUE_MISMATCH / 別の fact に GROUNDED。手がかり偽 12 行で P30E と同じ行 | 0 / 120〜129 / 0〜3、12 / 12 | 当期に GROUNDED 1 以上 = 縛りが届かない枝が残る。偽の行が動けば旗の外に効いている |
| E-6 | T9 の 141 行で P32E が通した率(分母 141)と、止めた行のうち 名指して原本(前期の fact を名指して VALUE_MISMATCH)の割合 | 5〜12%、90〜100% | 幅の外 |
| E-7 | `tests/adapters/xbrl/test_recipes_p32e.py` の変異(§2-1 の 10 本)で赤になる本数 | 10 / 10 | 黙った変異 1 本以上(試験を足して赤にできなければ外れのまま残す) |
| E-8 | 留めの連動で直した既存の試験 file の数(`git diff --name-status` の M。新しい file は別) | 40〜75 | 幅の外 |
| E-9 | engine の commit の後の全数: `tests/measure` の赤、`tests/adapters/xbrl` の赤 | axis3 の test_9 だけ、0 | 他に赤が残る |
| E-10 | 97 書類で P32E の VALUE_MISMATCH に動いた行の pointer の期 | 全部 Prior1Year(17〜19 行) | CurrentYear を名指す行が 1 以上 = B の名指しが前期でない |

封の席の偏り: E-3〜E-6 は試作 第 2 版の数をそのまま幅にした(RB の便と同じ。当たりは「試作と本物が同じ」の確認で規則の良さの証拠ではない)。E-4 の失う行は試作で 1 行(札 真)だが、札は P30E の GROUNDED を「正しい」と読んだ札で、その行の pointer は CurrentYear(前期と書かれた数が当期の fact)なので、失う側に数えてよいかは結果で読む。

## §4 採用の基準

判定は記録から門が機械で求め、司令塔は覆さない。

- K-1: E-2 が 97 / 97 かつ 141 / 141(旗が偽で不変)。
- K-2: E-3 の GROUNDED を失う行 0。
- K-3: E-4 の GROUNDED を失う行 ≤ 2。
- K-4: E-5 の当期の fact に GROUNDED 0〜3、かつ手がかり偽の 12 行が P30E と同じ。
- K-5: E-7 が 10 / 10 かつ E-9(engine の留めが全部緑)。

K-1〜K-5 を全部満たせば「採用」= 記録を正本にし、README の「外部の数の文に使う profile」の推奨を **P30E → P32E** に替え(負けの側の率は P32E の値に。P30E の字は消さない)、台帳に L・D・P の行を足す。1 つでも外れたら「採用しない(人間に返す)」= engine の P32E は残し README は P30E のまま。既定 P27 はどちらでも不変。

## §5 測り方(全部 0 USD。測定 script は engine の commit の後)

- `measure/xbrl_pbind_2026-11-06.py`: (1) AI の文 200 本で P30E → P32E の動いた行(種類・文の番号・位置で対応。既存の行には盲検の札。RB の `xbrl_rmix_2026-11-04.py` の作り)、(2) 手元の 97 書類の原文で P30E → P32E の動いた行(`xbrl_rmix_regress97_2026-11-04.py` の作り。前の便の記録と P22〜P30E の出力の sha256 が一致 = 旗が偽なら不変)、(3) T9 の id の対応付けの注入を P30E・P32E で(`xbrl_pswap_idmap_2026-11-06.py` を importlib で読み込み profile を替える。site・種・cap・行の id は T9 と同じ)。記録 `fixtures/xbrl/pbind/{moves_200,regress97,inject}_2026-11-06.json`。`tally` は封の字から幅を読んで E-1〜E-10・K-1〜K-5 を判定し 2 表。
- 門 `tests/measure/test_xbrl_pbind_seal.py`・`tests/measure/test_xbrl_pbind_result.py`(前例の作り。欄は行から数え直す。変異で赤)。結果 `docs/XBRL_PRIOR_CUE_BIND_ENGINE_RESULT_2026-11-06.md`。
- 採用なら README の P30E の推奨の行を **P32E** に替え(負けの側の率も P32E の値に)、台帳に L・D・P の行。

## §6 言えないこと

1. 「通した」「止めた」は engine の state で、札(人の目)は無い。200 本の動いた行の札は前の便の盲検の札(既存の行だけ)。
2. 手がかりは直前 12 字の窓の 6 語 + 「(同」だけ。表の見出し(規則 T の対象)・「〜から」の枝・同じ節の「前期は」(`_prior_cue_clause`)は PB の手がかりではない。
3. 200 本は Claude の model 2 つが書いた文。97 書類は有報の原文。注入は T9 の母集団(identified の前期の数 218 site)だけ。
4. B は `fs`(主語の要素の fact)の Prior1Year の先頭を名指す。要素が複数あるときどの fact かは従来の F1′ と同じ順。

## §7 作法と順序

1. この封を commit(文書だけ。fresh_seal・facts・boundary の門を走らせてから)→ engine の実装と試験(step-implementer、worktree。留めの連動も同じ便)→ 変異 → 独立監査 GO → engine の commit(パス指定)→ 測定 script と門(step-implementer)→ 監査 GO → commit → 記録 3 つ(本番)→ 結果の文書 → 門 → 監査 GO → commit → README(採用なら)→ 台帳 → 監査 → commit → axis3 の宣言は次の便。
2. 使わない: `git add -A`・`stash`・`reset`・`checkout`。cache に file を足さない。`edinetdb-p27`・`sgogi-coach-handoff` は開かない。鍵は全部 unset。

## 追記 1(2026-11-06、engine の実装席の報告を読んだ後・測定の前。§1〜§4 の字は変えない)

1. **前期の fact が無い要素**: 実装の依頼文の (カ) で司令塔は「前期の fact が無い要素は P30E と同じ出力」と見込んだが、§1 の 2 の字(hits に Prior1Year が無ければ CurrentYear を外す)では、その要素に前期の fact がそもそも無くても CurrentYear の hit は外れ、最後の枝が当期の fact を名指して VALUE_MISMATCH(recomputed は当期の値と同じ)になる。主語の無い数は no_subject から no_element になる。実装は封の字のまま(司令塔の見込みの方が封に無い)。97 書類の原文で GROUNDED を失う行は 0(§0-1 の 3)なので E-3 は据え置き。前期の fact が無い会社(新規上場など)の「前期は …」の数に当たる型で、この便では件数を測らず、測定 script の動いた行の内訳で「前期の fact が無い要素」を別に数えられるなら数える(数えられなくても予測は変えない)。
2. **§2-3 の列挙に無かった門 12 本**: nscan・jtypes・pswap・pswap_idmap の 4 家族(seal 門の untouched・前の便の門の blob の byte 一致・result 門の記録の頭の指紋)は sha16 でなく「封の commit から 0 行」で engine を留めていたため、`git grep` の列挙に出なかった。実装席は `test_xbrl_rmix_seal.py` に PB の宣言された遷移(行数 +24 / 0・+5 / 0、sha16 2 値、指紋 1 値、封の path が履歴に在る、PB の封の後に recipes と vocabulary を最初に触った commit ただ 1 つ)だけを許す部品を足した。封に無い決めなので、監査で「許す枝が宣言の字に限られている」ことを見る(監査の依頼 9)。§2-3 の見込み「直す試験 file 40〜75」の中(変更 72・新規 1)。
3. **§0-1 の 1 の「a, b は単位を含まない」は誤り**: 本番の `iter_numbers` の b は単位の終わり(「5,000千円」なら 4〜11)。PB の窓は a だけを使うので §1 の規則は変わらない。
4. **Prior2Year**: 当期・前期・前々期に同じ値が在る要素の「前期の X」は P32E では Prior2Year の fact に GROUNDED になる(§1 の 2 の字どおり。P30E は当期)。E-10 の予測「全部 Prior1Year」はそのまま置き、測定で Prior2Year が出れば外れとして残す。

## 追記 2(2026-11-06 夜、測定 script の実装席の報告を読んだ後・本番の記録の前。§1〜§4 の字は変えない)

1. **E-3・E-10 の「動いた行」は state が変わった行で数える。** §0-1 の 3 の 97 書類の数(19 行・5 書類)は、試作の script(scratchpad の `pbind/pass1_pb_97.py`)が P30E と P32E の claim を index で対応させ、state が違う行だけを数えた値で、E-3 の幅はこの数から作った。だから E-3 の定義も同じにする。E-4(200 本)は §3 の字どおり「state か pointer が違う行」のまま。
2. **この決めは盲検ではない。** 測定 script の実装席は、定義を script の docstring に書いた後、使い捨ての下調べで「state か pointers が違う行」の定義だと 97 書類で 27 行・9 書類になることを見て報告した(E-3 の幅の外)。結果の文書には 2 つの定義の数を並べ、どちらで判定したかを書く。採用の基準 K-1〜K-5 に E-3 の動いた行の数は入っていない(K-2 は GROUNDED を失う行だけ)。
3. **後の便への連絡**: この便の封の門は `measure/lib/` と `measure/inject.py` が engine の commit の blob と byte 同じことを見る。T5Y の便(`docs/XBRL_T5_YEN_SEAL_2026-11-06.md`)は `sites.py` と `inject.py` を変えるので、T5Y の commit でこの門に宣言された遷移を足す。
