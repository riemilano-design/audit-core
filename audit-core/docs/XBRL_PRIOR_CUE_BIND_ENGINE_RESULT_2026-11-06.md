# 結果: 前期の手がかりがある数を当期の fact に落とさない engine 規則 PB(P32E)

封: [XBRL_PRIOR_CUE_BIND_ENGINE_SEAL_2026-11-06.md](XBRL_PRIOR_CUE_BIND_ENGINE_SEAL_2026-11-06.md)(最初の commit `b7824e6`、追記 1 = `56317fb`、追記 2 = `0ed1cf9`)。engine の commit は `c2eb773`(`recipes.py` +24 / −0・`vocabulary.py` +5 / −0)、測定 script と門は `dae62f2`。人間の言葉「それで任せる進めて」2026-11-06 を、司令塔の意見 1〜7 の順で進める委任と読んだ(1 がこの規則)。この便は全部 0 USD(API の呼び出しなし。材料は既にある AI の文と手元の有報の原文)。【門なし】
数の正本は `fixtures/xbrl/pbind/` の記録 3 つ(`moves_200_2026-11-06.json`・`regress97_2026-11-06.json`・`inject_2026-11-06.json`)。下の 2 つの表は門 `tests/measure/test_xbrl_pbind_result.py` が記録から作り直して照らす。

**採用**(K-1〜K-5 を全部満たした。判定は門が機械で求め、司令塔は覆さない)。README の「外部の数の文に使う profile」の推奨を P30E から P32E に替える(文書だけ。別の commit)。既定の profile P27 は変えない。最後に決めるのは人間(§5)。

## §1 予測の判定(記録から機械で求めた。封 §3 の字のまま。外れは外れとして残す)

<!-- 門:start pred -->
| # | 欄 | 予測 | 測った値 | 判定 |
|---|---|---|---|---|
| E-1 | engine の差分(封の commit から engine の commit まで): `recipes.py` 挿入 / 削除、`vocabulary.py` 挿入 / 削除、`comparators.py`・`core/`・他の adapters の file | 18〜28 / 0、4〜6 / 0、0 | recipes 挿入 24・recipes 削除 0・vocabulary 挿入 5・vocabulary 削除 0・他の file 0 | **当たり** |
| E-2 | 旗が偽の不変: 97 書類の P22〜P30E の出力の sha256(engine の欄を除く)が RB の便の記録 `fixtures/xbrl/rmix/regress97_2026-11-04.json` と一致する書類、T9 の id の対応付けの 141 行の P30E の state が記録 9d0c8cb と同じ行 | 97 / 97、141 / 141 | 97 byte が同じ書類(profile 間の最小) 97・書類 97・profile 9・P30E の結果と state が同じ行 141・行 141 | **当たり** |
| E-3 | 97 書類の原文で P30E → P32E: GROUNDED を失う行 / 動いた行 / 動いた書類 | 0 / 15〜25 / 3〜8 | GROUNDED を失う行 0・動いた行 19・動いた書類 5 | **当たり** |
| E-4 | AI の文 200 本で P30E → P32E: 動いた行(state か pointer が違う)/ GROUNDED を失う行(うち札 真)/ POINTER_NOT_FOUND → VALUE_MISMATCH の行 | 45〜65 / 0〜2(0〜2)/ 12〜20 | 動いた行 54・GROUNDED を失う行 1・うち札 真 1・POINTER_NOT_FOUND → VALUE_MISMATCH 16 | **当たり** |
| E-5 | T9 の 141 行の P32E(手がかり真 129 行): 当期の fact に GROUNDED / 前期の fact を名指して VALUE_MISMATCH / 別の fact に GROUNDED。手がかり偽 12 行で P30E と同じ行 | 0 / 120〜129 / 0〜3、12 / 12 | 手がかり真の行 129・当期の fact に GROUNDED 0・前期の fact を名指して VALUE_MISMATCH 128・別の fact に GROUNDED 1・その他 0・手がかり偽の行 12・手がかり偽の行のうち P30E と同じ行 12 | **当たり** |
| E-6 | T9 の 141 行で P32E が通した率(分母 141)と、止めた行のうち 名指して原本(前期の fact を名指して VALUE_MISMATCH)の割合 | 5〜12%、90〜100% | 通した率(P32E) 8.5・名指して原本の割合 99.2 | **当たり** |
| E-7 | `tests/adapters/xbrl/test_recipes_p32e.py` の変異(§2-1 の 10 本)で赤になる本数 | 10 / 10 | 赤 10・変異の本数 10・写した全部赤の本数 16 | **当たり** |
| E-8 | 留めの連動で直した既存の試験 file の数(`git diff --name-status` の M。新しい file は別) | 40〜75 | 直した file(M) 64・新しい file(A) 1・engine の挿入の行数 29 | **当たり** |
| E-9 | engine の commit の後の全数: `tests/measure` の赤、`tests/adapters/xbrl` の赤 | axis3 の test_9 だけ、0 | 赤の試験 axis3 test_9・赤の本数 1・ほかの赤 0 | **当たり** |
| E-10 | 97 書類で P32E の VALUE_MISMATCH に動いた行の pointer の期 | 全部 Prior1Year(17〜19 行) | 行 18・CurrentYear 0・Prior1Year 18・Prior2Year 0・他 0・なし 0 | **当たり** |
<!-- 門:end -->

## §2 採用の判定(封 §4。判定は門が機械で求め、司令塔は覆さない)

<!-- 門:start judge -->
| # | 基準 | 測った値 | 判定 |
|---|---|---|---|
| K-1 | E-2 が 97 / 97 かつ 141 / 141(旗が偽で不変) | E-2 **当たり** | **当たり** |
| K-2 | E-3 の GROUNDED を失う行 0 | GROUNDED を失う行 0 | **当たり** |
| K-3 | E-4 の GROUNDED を失う行 ≤ 2 | GROUNDED を失う行 1 | **当たり** |
| K-4 | E-5 の当期の fact に GROUNDED 0〜3、かつ手がかり偽の 12 行が P30E と同じ | 当期の fact に GROUNDED 0・手がかり偽の行のうち P30E と同じ行 12・手がかり偽の行 12 | **当たり** |
| K-5 | E-7 が 10 / 10 かつ E-9(engine の留めが全部緑) | E-7 **当たり**・E-9 **当たり** | **当たり** |

採用の判定(K-1〜K-5 を全部満たす): **採用**。最後に決めるのは人間。
<!-- 門:end -->

## §3 読み

- **当たり 10 / 10**。E-3〜E-6 の幅は試作 第 2 版の数をそのまま幅にした(封 §3 の注記)。当たりは「試作と本物が同じ」の確認であり、規則の良さの証拠ではない。
- **期の取り違えの注入(T9 の 141 行)**: 「前期」と書かれた数に同じ要素の当期の値を入れた注入を、P30E は 138 行で通し、P32E は 12 行で通した(通した率 97.9% → 8.5%)。P32E が止めた 129 行は全部 VALUE_MISMATCH で、名指して原本 128 行(手がかり真で前期の fact を名指した 127 行と、手がかり偽で P30E も止めていた 1 行)・名指したが別の値 1 行(手がかり真で前期の fact を名指した)。【門なし】
- **P32E が通した 12 行の内訳**: 手がかり真の行(engine の手がかり。窓の手がかりと違う行は 0)で通したのは 1 行だけで、注入後の pointer は前期の fact(当期の値が前期の別の fact の値とも合った行)。手がかり真で当期の fact に GROUNDED は 0。残る 11 行は手がかり偽の行(数の直前 12 字に前期の語が無い)で、P30E と同じく当期の fact に GROUNDED。PB の窓に入らない書き方の数は、この規則では縛らない。
- **有報の原文(手元の 97 書類)**: 旗が偽の 9 profile の出力は 97 / 97 書類で RB の便の記録と byte 一致。P30E → P32E で GROUNDED は 6,568 のまま(失う行 0・得る行 0)。state が変わった行は 19(UNVERIFIABLE → VALUE_MISMATCH 12・POINTER_NOT_FOUND → VALUE_MISMATCH 6・UNVERIFIABLE → POINTER_NOT_FOUND 1)、5 書類。VALUE_MISMATCH に動いた 18 行の pointer の期は全部 Prior1Year。【門なし】
- **「動いた行」の 2 つの定義(封 追記 2)**: E-3 は state が変わった行で判定した(試作の数え方)。state か pointers が違う行で数えると 27 行・9 書類で、差の 8 行は VALUE_MISMATCH のまま pointer の期が CurrentYear から Prior1Year に替わった行。こちらの定義なら E-3 の幅(15〜25 行・3〜8 書類)の外になる。定義は記録を作る前に追記 2 で決めたが、実装席が使い捨ての下調べで 27 行・9 書類を先に見ていたので盲検ではない。採用の基準 K-1〜K-5 に動いた行の数は入っていない。
- **AI の文 200 本**: 数の claim は P30E と P32E で同じ数。P30E → P32E の動いた行(state か pointer が違う)54。GROUNDED → VALUE_MISMATCH 1(札 真)・POINTER_NOT_FOUND → VALUE_MISMATCH 16(札 真 5・偽 4・新しい行 7)・VALUE_MISMATCH のまま pointer の期が CurrentYear → Prior1Year 36(札 真 12・偽 8・新しい行 16)・UNVERIFIABLE → POINTER_NOT_FOUND 1(札 真)。GROUNDED になった行 0。【門なし】
- **GROUNDED を失った 1 行**: 「前期」と書かれた小さな額が当期の fact に GROUNDED だった行で、P32E は前期の fact を名指して VALUE_MISMATCH にした。札は前の便の盲検の席が P27 の claim を「真」と読んだもので、席が何を見て真としたかは記録に無い。この行を代価と読むか直りと読むかは engine の state と札からは決まらないので、封のとおり失う側に数えた(K-3 の上限 2 の中)。
- **前期の fact が無い要素(封 追記 1 の 1)**: その要素に前期の fact が無いのに当期の値で VALUE_MISMATCH になる型は、200 本でも 97 書類でも 0 行だった。材料にこの形が無かっただけで、型が無いことは言えない。【門なし】
- **Prior2Year(封 追記 1 の 4)**: P32E の動いた行で pointer の期が Prior2Year の行は 200 本・97 書類・T9 の 141 行とも 0。【門なし】
- E-7・E-9 は engine の commit の message の数を記録の header に写して判定した(この便で変異と全数を走らせ直していない)。所要: moves 約 6 分・regress97 約 4 分・inject 約 3 分(procs 6)。

## §4 言えないこと

1. 「通した」「止めた」は engine の state で、注入の行に札(人の目)は無い。動いた行の札は前の便の盲検の 1 席目の札で、既存の行(P27 にも在る行)にしか無い。
2. 200 本は Claude の model 2 つが書いた文。97 書類は 2026 年提出の有報に偏る。【門なし】
3. 注入は T9 の 1 型だけ(前期の fact に結ばれた数に当期の値を入れる)。期・単位・主語の他の取り違えは測っていない。
4. PB の手がかりは数の直前 12 字の窓の語と「(同」だけ。表の列の見出し(規則 T の対象)・「〜から」・同じ節の「前期は」は手がかりにしない。手がかり偽の 11 行はこの範囲の外。
5. 前期の fact が無い要素で当期の値を VALUE_MISMATCH にする型は、この材料に 0 行だった。新規上場の会社などの文では出うる。
6. E-7・E-9 は engine の commit の message の写しで、この便で走らせ直した数ではない。

## §5 次(人間が決める)

1. **README の推奨を P30E → P32E に替える**(封 §4 の採用の帰結。負けの側の率も P32E の値に。P30E の字は消さない)。司令塔はこの便の次の commit で替える。
2. 台帳に L・D・P の行を足す。axis3 の宣言(`LATER_ENGINE_COMMITS`)に engine の commit を足すのは次の便。
3. **既定の profile(P27)**・**main へのマージ**は人間の決定のまま。規則 T(表の列の見出し)の再評価は、この便の後に測り直してから伺う。
