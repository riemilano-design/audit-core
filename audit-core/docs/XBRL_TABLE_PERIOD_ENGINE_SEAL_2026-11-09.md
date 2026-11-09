# 封: 表の見出しの「前期」の列の数を前期の手がかりがある数として扱う engine 規則 T(P33E = P32E + 旗 `table_period_2026_11_09`。既定 P27 は不変)― 2026-11-09

前の便: PB(封 b7824e6 → engine c2eb773 → 結果 92a5bcb → README 8ea01bb → 台帳 8e16c1d)。PB の手がかりは数の直前 12 字の窓だけで、表の行の数には届かない。AI の文の表(`| 項目 | 当期 | 前期 | 増減 |`)の「前期」の列の数は、P32E でも当期の fact と比べられて VALUE_MISMATCH(前期の正しい数を「値が違う」と言う)になる。この封は表の見出しを期の手がかりに足す。

**下書き `docs/XBRL_TABLE_PERIOD_ENGINE_SEAL_2026-11-03.md`(P28E 土台・未 commit)はこの封が置き換える。** 下書きの P31・P31E は作らない。下書きは commit しない(人間の決定のまま残す)。

## §0 材料と決めごと

### §0-1 測った事実(この封を書く前に司令塔が 0 USD で数えた。試作は scratchpad/numfix/proto_t(engine の写しに §1 の規則を入れたもの。profile の名前は P32T)、script は scratchpad/numfix/ptable・ptable2。cache の一覧の sha256 は前後で同じ)

1. engine の読み(`adapters/xbrl/recipes.py`): `_prior_cue(s, a, b)` の呼び出しは `_direct_value_claim`(304・308・423・430)と `_dispatch_num_claim`(635・651)、`_prior_cue_window_2026_11_06(s, a)` の呼び出しは `_direct_value_claim`(320・402)。どれも `_build_raw_num_claims` の中からだけ呼ばれる(呼び出し元は `build_raw_claims` の 3 か所)。表の行は `extract.py` の `_split_lines` が `\n` で切った 1 文で、見出し行は別の文。**見出しの字を下の行の数に渡す仕掛けは無い**。
2. 列の数え(AI の文 200 本のうち表を持つ F3 の 40 本。見出しは全部 `項目 / 当期 / 前期 / 増減` の 4 列): 前期の列の数 415 は、P32E で VALUE_MISMATCH 367(全部 当期の fact を名指す)・当期の fact に GROUNDED 11・別の期の fact に GROUNDED 12・UNVERIFIABLE 22・POINTER_NOT_FOUND 3。当期の列は GROUNDED 388 ほか、増減の列は POINTER_NOT_FOUND 322・GROUNDED 101 ほか。P30E → P32E で表の行は 1 行も動いていない。
3. 試作(§1 の字。P32T)の 200 本の動き(PB の測定 script の `judge_book_pb` を P32E → P32T に替えて呼んだ。札は前の便の盲検の札): 動いた行(state か pointers が違う)394、**全部 F3 の前期の列**(表でない数・当期の列・増減の列・他の形は 0 行)。VALUE_MISMATCH(当期)→ GROUNDED(前期)365(札 真 283・新しい行 82)、VALUE_MISMATCH(当期)→ VALUE_MISMATCH(前期)2(札 偽 2)、POINTER_NOT_FOUND → VALUE_MISMATCH(前期)3(札 偽 1・新 2)、UNVERIFIABLE → GROUNDED(前期)1(札 真)、GROUNDED のまま期が前期に替わる 23(当期 11・前々期 2・他 10。全部 札 真)。GROUNDED 11,259 → 11,625、GROUNDED を失う行 0、札 偽の行が GROUNDED になった行 0。全 200 本で P32E と P32T の数の claim の鍵が同じ。
4. 試作の 97 書類の原文: 文のうち行頭が `|` の文は **0**(原文の表は HTML を剥がした字で `|` を持たない)→ P32T の動いた行 0・GROUNDED 6,568 不変。旗が偽の 10 profile(P22・P26・P27・P27E・P28・P28E・P29・P29E・P30E・P32E)の出力の sha256(engine の欄を除く)は PB の記録 `fixtures/xbrl/pbind/regress97_2026-11-06.json` と 97 / 97 で同じ。**原文では規則 T は届かない**(退行が無いことの確認であって、規則が客の書類で効くことの確認ではない)。
5. 試作の表の期の入れ替えの注入(新しい仕掛け。§5 の字): 見出しに前期の列 1 つ・当期の列 1 つの表の行で、セルに数がちょうど 1 つずつ、無改変で P32T が前期のセルを前期の fact に・当期のセルを当期の fact に GROUNDED にした行を site にした。site の候補 415 のうち 土台が合わない 30・2 つのセルの字が同じ 5・行の字が文に 1 回でない 3 を除いて 377。
   - **TP(前期のセルの数の字を同じ行の当期のセルの字に替える = 前期の列に当期の値)**: 対応が付かない 12。P32E は 365 / 377 を GROUNDED で通した(全部 当期の fact)。P32T は VALUE_MISMATCH(前期の fact を名指す)361・GROUNDED 4(前期 2・当期 1・他 1)= 通した 4 / 377。
   - **TC(当期のセルの字を前期のセルの字に替える。参考。規則 T は当期の列に効かない)**: 対応が付かない 6。P32E と P32T で state と期が違う行 1(UNVERIFIABLE → VALUE_MISMATCH 当期)。残りは同じ(VALUE_MISMATCH 当期 355・GROUNDED 15)。
6. engine の留めの現在の値: `recipes.py` の sha16 `0add35e7aa77d86b`(留める file 38)、`vocabulary.py` `e35b7fea2463818f`(39)、束ねた指紋 `adapter_xbrl_py_sha256` `dc13edfee7a9ac6b900ae610d056424b622b8447491113b78c4debf902bcfee8`(15 file)。前例 PB の engine の commit c2eb773 は 73 file。

### §0-2 司令塔の決定(人間の言葉「君に任せる進めて」2026-11-09 = 司令塔の報告(規則 T の下調べ: 前期の列の VALUE_MISMATCH 367 → GROUNDED 365・他の行 0・測っていないこと 3 つ)を受けて、規則 T を engine に入れる方向で封から進める委任。engine の変更を含む)

1. 規則は **profile の旗の後ろだけ**で、既定 P27・P27E〜P32E は 1 行も変わらない。新しい profile は E 系だけ **P33E = P32E + 旗**(P31・P31E・P33 は作らない)。
2. 表の前期の列の数は、`_prior_cue` と `_prior_cue_window_2026_11_06` が真を返す数と**同じ扱い**(上の 8 か所の呼び出し全部)。PB の縛り(当期の fact を外し、前期の fact を名指して VALUE_MISMATCH)も表の前期の列の数に効く。当期の列・増減の列・見出しが決まらない表の数は何も変えない。
3. 見出しの語は下書き(2026-11-03)の語のまま。列の見出しに「比・増減・率・差」の字があれば期の列にしない(「前年同期比」を前期の列にしない)。
4. 委任に含めないもの: 既定 profile P27・main へのマージ・T7 の帯幅・O を外す便(別の封)。

## §1 規則の字(engine。全部旗 `table_period_2026_11_09` が真のときだけ通る。偽なら 1 行も変わらない)

1. **表**: `_build_raw_num_claims` が持つ文の列で、`strip()` が `|` で始まる文の連なり(途中に `|` で始まらない文が来たら切れる)を 1 つの表とする。連なりの最初の文が見出し。セル = `strip()` の両端の `|` を除いて `|` で割った字。
2. **見出しのセルの種類**(新しい関数で持つ): セルに `比`・`増減`・`率`・`差` のどれかがあれば種類なし。前期の語(`前期`・`前連結会計年度`・`前事業年度`・`前年度`・`前年同期`・`前年`)があり当期の語が無ければ「前期」。当期の語(`当期`・`当連結会計年度`・`当事業年度`・`当年度`・`当中間`・`今期`)があり前期の語が無ければ「当期」。他は種類なし。見出しが使えるのは「前期」がちょうど 1 列・「当期」が 1 列以下のときだけ(使えない表は何も変えない)。
3. **前期の列の数**: 見出しの後の行で、セルの数が見出しと同じ行の、engine の数の読み(`_numbers_of(profile, s)`)が返す数のうち、`s[:a].count("|") - 1` が前期の列の番号の数。この数の (文の字, a) を集合に入れる。セルの数が見出しと違う行は入れない。
4. **効き方**: `_prior_cue(s, a, b)` と `_prior_cue_window_2026_11_06(s, a)` の先頭で、(s, a) が集合にあれば真を返す(既存の行は変えず、挿入だけ)。集合は `_build_raw_num_claims` の入口で毎回空にし、旗が真のときだけ埋める(試作と同じ。`_prior_cue` を呼ぶ経路は §0-1 の 1 のとおり全部 `_build_raw_num_claims` の中)。
5. 当たる例: 見出し `| 項目 | 当期 | 前期 | 増減 |` の下の `| 売上高 | 120億円 | 100億円 | +20.0% |` で、fact が当期 120億・前期 100億 → 「100億円」は P32E では当期の fact を名指して VALUE_MISMATCH、P33E では前期の fact に GROUNDED。同じ行の「100億円」を「120億円」に替える → P32E は当期の fact に GROUNDED(通す)、P33E は前期の fact を名指して VALUE_MISMATCH。当たらない例: 当期の列の「120億円」・増減の列の数・見出しが `| 項目 | 2026年3月期 | 2025年3月期 |` の表・見出しが `| 項目 | 当期 | 前年同期比 |` の表・セルの数が見出しと違う行・表でない文の数 → P32E と同じ。旗が偽(P32E)→ 全部今までどおり。

## §2 engine の範囲

### §2-1 触る file(`core/`・`extract.py`・`verify_document.py`・`comparators.py`・`registry_setup.py`・`report_customer.py` は 0 行。既存の行の書き換えは 0 行。挿入だけ)

| file | 足すもの | 行数の見込み(挿入) |
|---|---|---|
| `adapters/xbrl/recipes.py` | 語の組と集合・見出しの種類の関数・前期の列の数の関数(注記つき)・`_prior_cue` と窓の関数の先頭の 2 行ずつ・`_build_raw_num_claims` の入口の 3 行 | 45〜75 |
| `adapters/xbrl/vocabulary.py` | 旗 1 つ(注記つき。`prior_cue_bind_2026_11_06` の直後)・P33E・`PROFILES` | 3〜6 |

- 関数を `_build_point_diff_claim` の直後に置かない(本体の sha16 を留める門がある)。
- 試験: `tests/adapters/xbrl/test_recipes_p33e.py`(新しい file)。§1 の 5 の当たる例・当たらない例を小さい文と fact で。P32E と P33E が「当たらない」の例で同じ出力。`V.P33E` の旗・`PROFILES`・`DEFAULT_PROFILE == "P27"`・旗の欄の位置。集合が呼び出しの間で残らないこと(P33E の後に P32E を同じ process で呼んで P32E の出力が変わらない)。変異で赤: 見出しの「比・増減・率・差」の除外を外す・前期の列の条件を「1 列以上」に緩める・列の番号を 1 ずらす・セルの数の条件を外す・`_prior_cue` の側の挿入を外す・窓の関数の側の挿入を外す・入口で集合を空にしない・旗が偽でも埋める・当期の列も入れる・P33E の旗を偽にする。

### §2-2 触る枝の中の人間の決定(字も振る舞いも壊さない)

1. C2 `_prior_cue`(2026-10-13)・PB の窓の関数(2026-11-06): 既存の字は変えない。先頭に旗の後ろの判定を挿入するだけ。
2. P22 `period_bind`・P24・案ア・§1b の止め・P21 F1′・F2′・P25・P26・P27E B・N・RB・O・P28〜P32E の規則と旗: 字は変えない。
3. **既定 `DEFAULT_PROFILE = "P27"`**(人間 2026-11-03): 変えない。P16〜P32E を明示した試験の数は 1 つも変えない。

### §2-3 既存の門の engine の留め(実装の便で同じ便に宣言された遷移を足す。測った当時の値は消さない。前例 PB c2eb773・RB d81d35f)

- `recipes.py`(`0add35e7aa77d86b`、38 file)・`vocabulary.py`(`e35b7fea2463818f`、39 file)の sha16 を留める門に、宣言の行 `(新しい sha16, "docs/XBRL_TABLE_PERIOD_ENGINE_SEAL_2026-11-09.md")` を前例と同じ形で足す。`test_xbrl_default_p27_result.py` の `ENGINE_DECL` の numstat の上限は挿入分だけ上げる(削除 0 は変えない)。
- 束ねた指紋 `adapter_xbrl_py_sha256`(`dc13edfe…`、15 file)の新しい値と、`fixtures/frozen_bundle_sha.py` の世代 +1。profile の名前の一覧に P33E。
- **PB の追記 1 の 2 の型**(sha16 でなく「封の commit から 0 行」で engine を留める門): nscan・jtypes・pswap・pswap_idmap・rmix・pbind・t5y の家族の門は `git grep` の sha16 の列挙に出ない。PB の便が `test_xbrl_rmix_seal.py` に足した「宣言された遷移だけを許す部品」に T の遷移(行数・sha16 2 値・指紋 1 値・封の path が履歴に在る・T の封の後に recipes と vocabulary を最初に触った commit ただ 1 つ)を同じ形で足す。PB の封の門・T5Y の門が engine の blob を照らしていれば同じ。
- `test_xbrl_axis3_decision.py` の `LATER_ENGINE_COMMITS` は次の便(test_9 は赤のままでよい)。
- 新しい門で engine の留めを定義するときは `ENGINE_LATER`・`UNTOUCHED`・`PIN_DEF`・`LATER_ENGINE_COMMITS`・`FROZEN_LATER`・`ENGINE_TRANSITIONS` を行頭の名前に使わない。

## §3 事前予測(**実装より先に固定。結果を見てから書き換えない**。外れは外れとして残す)

| # | 欄 | 予測(幅) | 外れ方 |
|---|---|---|---|
| T-1 | engine の差分(封の commit から engine の commit まで): `recipes.py` 挿入 / 削除、`vocabulary.py` 挿入 / 削除、`comparators.py`・`core/`・他の adapters の file | 45〜75 / 0、3〜6 / 0、0 | 削除 1 行以上か幅の外 = §2-1 の約束と違う |
| T-2 | 旗が偽の不変: 97 書類の P22〜P32E(10 profile)の出力の sha256(engine の欄を除く)が PB の記録と一致する書類、T9 の id の対応付けの 141 行で P33E の結果と state が PB の記録 `fixtures/xbrl/pbind/inject_2026-11-06.json` の P32E と同じ行 | 97 / 97、141 / 141 | 1 つでも違う = 旗が偽の経路か、表でない数が変わった |
| T-3 | 97 書類の原文で P32E → P33E: 行頭が `|` の文 / 動いた行 / GROUNDED を失う行 | 0 / 0 / 0 | 1 以上 |
| T-4 | AI の文 200 本で P32E → P33E: 動いた行(state か pointers が違う)/ そのうち表の前期の列の数でない行 / GROUNDED を失う行 / GROUNDED の数の増え | 380〜400 / 0 / 0 / +350〜+380 | 幅の外。表の前期の列でない行が 1 以上 = 規則が表の外に効いた |
| T-5 | 200 本の動いた行の札: VALUE_MISMATCH → GROUNDED の行のうち札 真 / 札 偽の行が GROUNDED になった行 | 270〜295 / 0 | 札 偽が GROUNDED に 1 行以上 = 誤りを通す側に動いた |
| T-6 | 表の期の入れ替え TP(§5): site / P32E が通した率 / P33E が通した率 / P33E が止めた行のうち前期の fact を名指して VALUE_MISMATCH の割合 | 360〜390 / 90〜100% / 0〜3% / 95〜100% | 幅の外。P33E の通した率が 3% を超える = 縛りが届かない枝が残る |
| T-7 | 表の期の入れ替え TC(参考): P32E と P33E で結果か state が違う行 | 0〜3 | 4 以上 = 規則が当期の列の数に間接に効いている |
| T-8 | `tests/adapters/xbrl/test_recipes_p33e.py` の変異(§2-1 の 10 本)で赤になる本数 | 10 / 10 | 黙った変異 1 本以上(試験を足して赤にできなければ外れのまま残す) |
| T-9 | 留めの連動で直した既存の試験 file の数(`git diff --name-status` の M。新しい file は別) | 40〜80 | 幅の外 |
| T-10 | engine の commit の後の全数: `tests/measure` の赤、`tests/adapters/xbrl` の赤 | axis3 の test_9 だけ、0 | 他に赤が残る |

封の席の偏り: T-3〜T-7 は試作の数をそのまま幅にした(PB・RB の便と同じ。当たりは「試作と本物が同じ」の確認で、規則の良さの証拠ではない)。T-6 の TP は司令塔が作った新しい注入で、site は P33E が無改変で両方のセルを GROUNDED にした行だけ(P33E に都合のよい母集団)。P32E が通す率の高さは「P32E が表の前期の列を見ていない」ことの確認で、他の型の誤りを止める力は測らない。

## §4 採用の基準

判定は記録から門が機械で求め、司令塔は覆さない。

- K-1: T-2 が 97 / 97 かつ 141 / 141。
- K-2: T-3 の GROUNDED を失う行 0、かつ T-4 の GROUNDED を失う行 0。
- K-3: T-4 の表の前期の列でない動いた行 0、かつ T-5 の札 偽が GROUNDED になった行 0。
- K-4: T-6 の P33E の通した率 ≤ 3%(分母 = 注入の行。分母 0 は外れ)、かつ P32E の通した率 ≥ 90%(注入が P32E の弱点に届いていること)。
- K-5: T-8 が 10 / 10 かつ T-10(engine の留めが全部緑)。

K-1〜K-5 を全部満たせば「採用」= 記録を正本にし、README の「外部の数の文に使う profile」の推奨を **P32E → P33E** に替え(P32E の字は消さない)、台帳に L・D・P の行を足す。1 つでも外れたら「採用しない(人間に返す)」= engine の P33E は残し README は P32E のまま。既定 P27 はどちらでも不変。

## §5 測り方(全部 0 USD。測定 script は engine の commit の後)

- `measure/xbrl_tperiod_2026-11-09.py`(PB の script `measure/xbrl_pbind_2026-11-06.py` を importlib で読み込み、関数を写さない):
  1. **moves**: AI の文 200 本で P32E → P33E の動いた行(PB の `judge_book_pb` と同じ鍵・札・欄)。各行に「表の前期の列の数か」の真偽を足す(engine の §1 の関数の集合に (文の字, 位置) があるか)。記録 `fixtures/xbrl/tperiod/moves_200_2026-11-09.json`。
  2. **regress97**: 手元の 97 書類で 10 profile の出力の sha256 を PB の記録と照らし、P32E → P33E の動いた行と行頭が `|` の文の数。記録 `fixtures/xbrl/tperiod/regress97_2026-11-09.json`。
  3. **inject**: (a) T9 の id の対応付けの 141 行を P30E 土台・P33E で判定し(PB の `inject_text_pb` の対を (P30E, P33E) に替える)、id ごとに PB の記録の P32E の欄と照らす。(b) 表の期の入れ替え TP・TC(§0-1 の 5 の字: 見出しの前期 1 列・当期 1 列、セルに数 1 つずつ、無改変の P33E で前期のセル = 前期の fact・当期のセル = 当期の fact に GROUNDED、2 つのセルの字が違う、行の字が文に 1 回だけ。1 回に 1 か所だけ替え、P32E・P33E で判定。対応は文の番号と替えたセルの数の位置)。site は全部採る(cap なし)。記録 `fixtures/xbrl/tperiod/inject_2026-11-09.json`。行は id・形・model・型・各 profile の state と期・対応の有無だけ(文・値・要素名を持たない)。
  4. `tally` は封の字から幅を読んで T-1〜T-10・K-1〜K-5 を判定し 2 表。T-8・T-10 は engine の commit の message の字を header に写す(PB の便の決めと同じ)。
- 門 `tests/measure/test_xbrl_tperiod_seal.py`・`tests/measure/test_xbrl_tperiod_result.py`(PB の門の作り。欄は行から数え直す。変異で赤。importlib で前の便の script を読むときは、前から在る `sys.modules` の名前を戻す)。結果 `docs/XBRL_TABLE_PERIOD_ENGINE_RESULT_2026-11-09.md`。

## §6 言えないこと

1. 「通した」「止めた」は engine の state で、注入の行に札は無い。200 本の動いた行の札は前の便の盲検の札(既存の行だけ)。
2. 表は AI の文の F3 の 40 本だけで、見出しは全部 `項目 / 当期 / 前期 / 増減`(書き手への指示が決めた形)。客の表の見出しの語・列の順・列の数はこれと違いうる。年だけの見出し(「2025年3月期」)・`|` 以外の区切り(タブ・全角空白・PDF の抜き出し)は規則 T の外。見出しの読み違いを行ごとに目で確かめてはいない。
3. 有報の原文(97 書類)には `|` の表が無く、規則 T は原文では届かない。T-3 は退行が無いことだけを見る。
4. TP・TC は司令塔が作った注入で、site は P33E が無改変で正しく結んだ行だけ。表の前期の列の他の型の誤り(値の書き違い・単位の取り違え)は測らない。
5. 集合は (文の字, 位置) で持つので、同じ字の文が 2 つあれば両方に効く。

## §7 作法と順序

1. この封を commit(文書だけ。fresh_seal・facts・boundary の門を走らせてから)→ engine の実装と試験(step-implementer、worktree。留めの連動も同じ便)→ 変異 → 独立監査 GO → engine の commit(パス指定)→ 測定 script と門(step-implementer)→ 監査 GO → commit → 記録 3 つ(本番)→ 結果の文書 → 門 → 監査 GO → commit → README(採用なら)→ 台帳 → 監査 → commit → axis3 の宣言は台帳の便。
2. 使わない: `git add -A`・`stash`・`reset`・`checkout`。cache に file を足さない。`edinetdb-p27`・`sgogi-coach-handoff` は開かない。鍵は全部 unset。
