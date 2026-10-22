# 「違う」に出る正しい文の主因を減らす P26 ― 段 1 の結果(2026-10-22)

封: `docs/XBRL_P26_SEAL_2026-10-21.md`(commit `a8d8099`。本文 §0〜§4 と予測 Q-1〜Q-8)。記録: `fixtures/xbrl/p26_2026-10-21.json`(`measure/xbrl_p26_2026-10-21.py --stage all` の出力)。
門: `tests/measure/test_xbrl_p26_result.py`(この文書の表と数のある文を記録から作った字と完全一致させ、散文の算用数字を禁じ、予測の判定を封の字と記録の行から門が自分で求める)。engine の試験: `tests/adapters/xbrl/test_recipes_p26.py`。
段 1 は旗だけを足した(`DEFAULT_PROFILE` は P22 のまま)。人間の事前承認は 2026-10-21(engine を変える)。0 USD、通信なし。**読みは実装席のエージェントの読みで、人間ではない。**

## 0. 結論

**予測 機械判定 当たり 7 / 外れ 0 / 読み待ち・測れない 0**(Q-1〜Q-7。Q-8 は段 2 なので判定しない)。

- 無改変の六十七書類で、「違う」は P25 の六百二十六行から P26 の四百三十三行になった。新しい GROUNDED は零。67 書類(claim 7,799)の無改変で、P25 から P26 に動いた行は 217。VALUE_MISMATCH は P25 が 626、P26 が 433(差 193)。GROUNDED は 4,382 → 4,371、UNVERIFIABLE は 1,397 → 1,579、POINTER_NOT_FOUND は 1,394 → 1,416。新しい GROUNDED は 0。
- 「違う」から外れた百九十三行を一行ずつ読み、全部「正しい文」と読んだ。「文が本当に違う」は零(封の外れ方は三以上)。**ただし読み手が試作の読みと違う。** 試作は百九十三行のうち七行を「分からない」と読んだ。今回は同じ集合を全部「正しい文」と読んだので、この七行(を含む境界の行)は読み手で動く。下の第三節に境界の行を名指した。独立監査で読み直すこと。
- 一致(GROUNDED)から外れた十一行は、全部「偶然の一致」と読んだ(語が別の項目にかかるのに、主語の fact の増減と偶然に向きが合っていた)。
- 誤りを通す側は零を保った: 穴 B の注入、儀式、段 2 の材料、動いた行への注入(末尾の桁をプラスマイナス三動かす注入と十倍の注入)、差の主張への末尾の桁のプラスマイナス一の注入のどれでも、P26 が新しく GROUNDED にした行は零。
- 代価: 差の主張の一単位の書き誤りは「違う」でなく「要確認」に出る。封の限界の文は試作の注入の止め百六十五としたが、この実行の実測は下の第五節。
- 旗一つずつの効き(下の第二節の表): 丸めた差の保留(G3)が百五十八行、要因の項目の向き(G4)が二十四行、概念の門(G1)が二十四行(組み合わせると G2 が先に一行を取るので二十三行と一行)、数の読み取り(G5)が十一行、最後の枝の大きさの条件(G2)が一行。

engine の直し: `adapters/xbrl/recipes.py` 挿入 251・削除 1、`adapters/xbrl/extract.py` 挿入 42・削除 0、`adapters/xbrl/vocabulary.py` 挿入 17・削除 0、`adapters/xbrl/registry_setup.py` 挿入 6・削除 0、`adapters/xbrl/report_customer.py` 挿入 7・削除 2、`adapters/xbrl/comparators.py` 挿入 0・削除 0、`core/` 0 行。

## 1. 予測と実測

| # | 封の予測 | 封の外れ方 | 実測 | 判定 |
|---|---|---|---|---|
| **Q-1** | 67 書類の無改変で VALUE_MISMATCH **425〜441**、新しい GROUNDED **0**、GROUNDED → 非 GROUNDED **8〜14** | 幅の外 / 新 GROUNDED 1 以上 | 67 書類(実数 67)・claim 7,799: VALUE_MISMATCH P25 626 → P26 433、新しい GROUNDED 0、GROUNDED から外れた行 11(GROUNDED 4,382 → 4,371)、動いた 217 行 | **当たり** |
| **Q-2** | 「違う」から外れた行を全部読み、「文が本当に違う」**0〜2** | 3 以上 | 「違う」から外れた 193 行の読み(実装席のエージェント): 正しい文 193・文が本当に違う 0・分からない 0・未読 0 | **当たり** |
| **Q-3** | 穴 B 通した **0 / 485**、儀式 通した **2〜3**、段 2 の注入 GROUNDED **0 / 64** | 幅の外 | 穴 B 通した 0 / 485・儀式 通した 2 / 243(N069・N096)・段 2 の注入 GROUNDED 0 / 64。穴 B の止め → 要確認 1、儀式の止め → 要確認 1(手で当てた円銭 4 行で通した 0)、段 2 の止め → 要確認 1 | **当たり** |
| **Q-4** | 動いた行への注入(1 回 1 件、末尾の桁 ±3・10 倍)で P26 の GROUNDED **0** | 1 以上 | 動いた 217 行・注入 342 回(作れなかった 46・有効 318)で P26 が GROUNDED 0(P25 の対照は 0) | **当たり** |
| **Q-5** | P25 で一致の差の主張への末尾の桁 ±1 の注入で、P25 が止めて P26 が GROUNDED にした行(新しい GROUNDED)**0**(G3 が誤りを通さない。P25 も P26 も GROUNDED にする行は数えない ― 試作では 9 行) | 1 以上 | P25 で GROUNDED の差の主張 608 行に末尾の桁 ±1 の注入 1095 回(有効 1068): P25 が止めて P26 が GROUNDED にした(新しい GROUNDED)0・P25 も P26 も GROUNDED にした 9(数えない)・P25 の止めが P26 で要確認に移った 171 | **当たり** |
| **Q-6** | engine の差分 recipes **+240〜+300 / −0〜−2**、extract **≤ 60**、vocabulary **≤ 45**、registry_setup **≤ 15**、comparators **0**、core/ 0。既存試験の赤は sha・指紋・profile の一覧・登録簿と理由の表・変異の予測の連鎖だけ(数 / state の門 0、人間の決定の字の門 0) | 超える / 種類の外の赤 | recipes.py 挿入 251・削除 1、extract.py 挿入 42・削除 0、vocabulary.py 挿入 17・削除 0、registry_setup.py 挿入 6・削除 0、comparators.py 0/0、core/ 0 行。既存試験の赤(直す前)65 本、種類 {"profile の一覧": 19, "sha・指紋": 36, "変異の予測": 2, "登録簿と理由の表": 8} | **当たり** |
| **Q-7** | 報告形で P26 明示の 67 書類の「違う」の節 = P26 の VALUE_MISMATCH、3 つの理由は全部「要確認」の節、登録簿の理由の網羅 16 → 19 | 違う | P26 明示の 67 書類: 「違う」の節の合計 433・VALUE_MISMATCH 433。3 つの理由の 205 行が入った節 {"要確認": 205}。登録簿の理由 19(POINTER_NOT_FOUND 10・UNVERIFIABLE 9)のうち表にある 19 | **当たり** |
| **Q-8** | 段 2(既定)は封 `docs/XBRL_FRESH_SAMPLE_SEAL_2026-10-21.md` §3 の基準で | ― | 段 2(既定)は封 docs/XBRL_FRESH_SAMPLE_SEAL_2026-10-21.md §3 の基準で、新しい標本を取ってから。この実行では何も変えていない(DEFAULT_PROFILE = P22) | **判定しない(段 2)** |

予測は全部当たった。**これは試作の再現(Q-1・Q-3〜Q-5)が試作と同じ engine で同じ書類を測ったからで、封も「本当に外れうるのは Q-2 と新しい標本での判定 Q-8」と書いた。** Q-2 の実測は読み手の違いを含む(第三節)。Q-8 はこの実行では判定しない。

## 2. Q-1 無改変の六十七書類

| 項目 | 件数 |
|---|---:|
| 書類 | 67 |
| claim の総数 | 7,799 |
| 動いた行(全 state) | 217 |
| 「違う」から外れた行(P25 が VALUE_MISMATCH、P26 が違う) | 193 |
| GROUNDED から外れた行(P25 が GROUNDED、P26 が違う) | 11 |
| 新しい GROUNDED(P25 が GROUNDED でなく P26 が GROUNDED) | 0 |
| 読みだけ変わった行(G5。state・reason は同じ) | 11 |

| 無改変 67 書類 | GROUNDED | VALUE_MISMATCH | UNVERIFIABLE | POINTER_NOT_FOUND |
|---|---:|---:|---:|---:|
| P25(対照) | 4,382 | 626 | 1,397 | 1,394 |
| **P26** | **4,371** | **433** | **1,579** | **1,416** |

向き(P25 → P26)の全部:

| 向き(P25 → P26) | 行 |
|---|---:|
| VALUE_MISMATCH(None) → UNVERIFIABLE(rounded_diff_within_double_band) | 158 |
| VALUE_MISMATCH(None) → POINTER_NOT_FOUND(other_concept) | 23 |
| GROUNDED(None) → UNVERIFIABLE(direction_on_cause_item) | 11 |
| VALUE_MISMATCH(None) → UNVERIFIABLE(direction_on_cause_item) | 11 |
| POINTER_NOT_FOUND(no_element) → POINTER_NOT_FOUND(no_element) | 9 |
| GROUNDED(None) → GROUNDED(None) | 1 |
| POINTER_NOT_FOUND(no_element(no prior for text)) → UNVERIFIABLE(direction_on_cause_item) | 1 |
| POINTER_NOT_FOUND(no_element(text needs money fact)) → UNVERIFIABLE(direction_on_cause_item) | 1 |
| POINTER_NOT_FOUND(no_same_value) → POINTER_NOT_FOUND(no_same_value) | 1 |
| VALUE_MISMATCH(None) → POINTER_NOT_FOUND(no_same_value) | 1 |

旗を一つずつ P25 に足した profile(measure の中だけで `dataclasses.replace` して作った。engine には登録していない)で測ると:

| 旗 1 つだけを P25 に足した profile | GROUNDED | VALUE_MISMATCH | UNVERIFIABLE | POINTER_NOT_FOUND | 動いた行 |
|---|---:|---:|---:|---:|---:|
| G1 | 4,382 | 602 | 1,397 | 1,418 | 24 |
| G2 | 4,382 | 625 | 1,397 | 1,395 | 1 |
| G3 | 4,382 | 468 | 1,555 | 1,394 | 158 |
| G4 | 4,371 | 615 | 1,421 | 1,392 | 24 |
| G5 | 4,382 | 626 | 1,397 | 1,394 | 11 |

読み取りの旗(G5)の十一行は state・reason が同じで、読んだ数だけが変わった(円と銭が続く表記を一つの数に読むようになった。読む数が整数の円から銭までを含む値に変わる)。一行は GROUNDED のまま、九行は結べないまま、一行は `no_same_value` のまま。

## 3. Q-2 「違う」から外れた行の読み

「違う」から外れた 193 行を全部読んで、正しい文 193・文が本当に違う 0・分からない 0(未読 0)。GROUNDED から外れた 11 行は、偶然の一致 11・正しい結びを失った 0・分からない 0(未読 0)。

| 動いた先の理由 | 行 | 正しい文 | 文が本当に違う | 分からない | 未読 |
|---|---:|---:|---:|---:|---:|
| rounded_diff_within_double_band | 158 | 158 | 0 | 0 | 0 |
| other_concept | 23 | 23 | 0 | 0 | 0 |
| direction_on_cause_item | 11 | 11 | 0 | 0 | 0 |
| no_same_value | 1 | 1 | 0 | 0 | 0 |
| **合計** | **193** | **193** | **0** | **0** | **0** |

読みは `measure/xbrl_p26_2026-10-21.py` の `--readings` に渡した JSON(各行に根拠の文)で、記録の各行に写してある。門が縛るのは行と読みの一対一 と語と根拠の有無だけで、**読みの中身は門で縛れない**。

読んだ型ごとの見立て:

- 丸めた差の保留(`rounded_diff_within_double_band`、百五十八行): 主語と名指した要素は同じ項目で、当期末 − 前期末が文の数と一単位(文の桁)だけずれる。二つの fact とも文の桁に丸めた値。向きは文と一致。丸めた数どうしの差で出るずれか、一単位の書き誤りかは文書から見分けられないので、「正しい文」と読んだ。
- 概念の門(`other_concept`、二十三行): 名指した fact が文の項目と別の概念だった(契約負債・前受収益・その他の営業収益の名前に部分一致した別の項目、または一株当たりの値)。文の数は、文が実際に言う項目(負債合計・引当金・未払法人所得税等・営業利益・使用権資産・リース負債・有形固定資産・売掛金など)の fact と一つずつ照合して合った。「違う」の理由は出典の当て先違いだった。
- 要因の項目の向き(`direction_on_cause_item`、十一行 + 一致から外れた十一行 + 結べない二行): 向きの語が主語でなく、要因に挙げた項目(資金の増加要因・減少要因)にかかる形。
- 一株当たり(`no_same_value`、一行): S100YZ7E N050 の文の「一百万円」は「その他の収入等」の金額で、主語に拾った「配当」は「利息及び配当金」の語の一部。名指していたのは一株当たり配当四百円(`JPYPerShares`)で、二百万円以内に入った偶然の近さ(P25 の証拠 (ii) の穴。G2 が大きさの条件で止める)。

**境界の行(読み手で動く行)**: 丸めた差の保留のうち、符号の規約の四行(S100YXLE N034・S100YYS4 N073・S100Z40G N043・S100Z4LC N028。自己株式・貸倒引当金は値が負の要素で、額の増減としては文の向きと一致と読んだ)と、文自身が示す二つの残高の差も文と一単位ずれる二行(S100Z5CH N051・N071)。試作はこの種の行を含む七行を「分からない」と読んだ。今回は読みの根拠を行ごとに書いて「正しい文」としたが、独立監査が別の読みをするなら「分からない」に動く。**封が縛るのは「文が本当に違う」零〜二だけで、この六行がどちらに読まれても Q-2 の判定は変わらない。**

一致から外れた行(Q-2b。封の予測の外):

| GROUNDED から外れた行 | 行 | 偶然の一致 | 正しい結びを失った | 分からない | 未読 |
|---|---:|---:|---:|---:|---:|
| 合計 | 11 | 11 | 0 | 0 | 0 |

十一行とも、語が主語でなく別の項目にかかるのに、主語の fact の増減と向きが偶然に合って一致していた行。数と語は主張として別だが、その行の語が「正しく結べていた」と言える行は無かった(「正しい結びを失った」は零)。同じ文の別の語が同じ中身を別に持つ行もあり、その行は文として失うものは無い。

## 4. Q-3 誤りを通す側(穴 B・儀式・段 2)

穴 B の注入 485 件を P26 で再検証すると、通した 0 / 485 = 0.0%(P25 は 0 / 485 = 0.0%)。儀式を P26 で回すと、通した 2 / 243 = 0.8%(N069・N096)。段 2 の材料の注入 64 件のうち Core 自身 P26 が GROUNDED にしたのは 0。

| 項目 | 実測 |
|---|---|
| 穴 B(前期の値への置き換え)の注入 P26 で通した | 0 / 485 = 0.0% |
| 穴 B P25(対照)で通した | 0 / 485 = 0.0% |
| 穴 B P25 の止めのうち要確認に移った | 1 / 481 = 0.2% |
| 儀式 P26 で通した | 2 / 243 = 0.8%(N069・N096) |
| 儀式 P25(対照)で通した | 2 / 247 = 0.8%(N069・N096) |
| 儀式の注入の止めが要確認に移った(共通の行) | 1 |
| 儀式 手で当てた(P26 の表から消えた)行 | 4(通した 0) |
| 段 2 の注入で Core 自身 P26 が GROUNDED | 0 / 64 = 0.0% |
| 段 2 の注入の止めのうち要確認に移った | 1 |

円銭の注入四か所は、G5 で「百四十八円二十二銭」の形を一つの数に読むため、儀式の道具が既存の読みで作る注入の site の表から消えた(儀式の行 P25 の二百四十七 → P26 の二百四十三)。消えた四行は、手で P26 の読みの注入を当てて走らせ直し、通した行は零だった(要確認が二行・違うが二行)。

## 5. Q-4・Q-5 動いた行への注入と、差の主張への末尾の桁のプラスマイナス一の注入

動いた 217 行に注入 342 回(作れなかった 46・有効 318・有効でない 24)。P26 が GROUNDED にした 0 回(P25 の対照も 0 回)。

P25 で GROUNDED の差の主張 608 行に末尾の桁 ±1 の注入 1095 回(有効 1068)。P25 が止めて P26 が GROUNDED にした行(新しい GROUNDED)は 0、P25 も P26 も GROUNDED にした注入は 9(数えない)、P25 の止めが P26 で要確認に移った注入は 171。

| 項目 | 実測 |
|---|---|
| Q-4 動いた行 | 217 |
| Q-4 注入(作れなかった 46) | 342 |
| Q-4 有効な注入 | 318 |
| Q-4 P26 が GROUNDED にした(P25 の対照 0) | 0 |
| Q-4 P25 の止めが P26 で要確認に移った有効な注入 | 18 |
| Q-5 P25 で GROUNDED の差の主張 | 608 |
| Q-5 注入(有効 1068) | 1095 |
| Q-5 新しい GROUNDED(P25 が止めて P26 が GROUNDED にした) | 0 |
| Q-5 P25 も P26 も GROUNDED にした(数えない) | 9 |
| Q-5 P25 の止めが P26 で要確認に移った | 171 / 628 |

Q-5 の「P25 も P26 も GROUNDED にした注入」は、P25 が既に通す形(文の数が丸めの許容帯の中に入る)で、P26 が新しく通したものではないので数えない(試作でも九行)。P26 の G3 は GROUNDED を作らない設計(UNVERIFIABLE に落とすだけ)で、新しい GROUNDED が零なのはその帰結。

## 6. Q-6 engine の差分と既存試験

| file | 挿入 | 削除 |
|---|---:|---:|
| `adapters/xbrl/comparators.py` | 0 | 0 |
| `adapters/xbrl/extract.py` | 42 | 0 |
| `adapters/xbrl/recipes.py` | 251 | 1 |
| `adapters/xbrl/registry_setup.py` | 6 | 0 |
| `adapters/xbrl/report.py` | 0 | 0 |
| `adapters/xbrl/report_customer.py` | 7 | 2 |
| `adapters/xbrl/verify_document.py` | 0 | 0 |
| `adapters/xbrl/vocabulary.py` | 17 | 0 |
| `core/`(差の行数) | 0 | |

既存試験の赤(直す前): 65 本。直した後の既存試験の全実行は記録に写していない(commit 前の全実行の結果は司令塔への報告に書く)。

| 既存試験の赤(直す前)の種類 | 本数 |
|---|---:|
| sha・指紋 | 36 |
| profile の一覧 | 19 |
| 登録簿と理由の表 | 8 |
| 変異の予測 | 2 |
| **合計** | **65** |

既存試験の赤(直す前)の全一覧:

| 試験 | 種類 | 直し |
|---|---|---|
| `tests/measure/test_xbrl_a_core_vs_grep_seal.py::FrozenTest::test_9_tools_have_not_moved` | sha・指紋 | 宣言された遷移(P26 の封 docs/XBRL_P26_SEAL_2026-10-21.md と後の sha / 指紋 / frozen_bundle)を足した |
| `tests/measure/test_xbrl_axis3_decision.py::Axis3Test::test_9_the_engine_was_not_touched` | sha・指紋 | 宣言された遷移(P26 の封 docs/XBRL_P26_SEAL_2026-10-21.md と後の sha / 指紋 / frozen_bundle)を足した |
| `tests/measure/test_xbrl_branch_a.py::PredictionTest::test_14_engine_files_are_untouched` | sha・指紋 | 宣言された遷移(P26 の封 docs/XBRL_P26_SEAL_2026-10-21.md と後の sha / 指紋 / frozen_bundle)を足した |
| `tests/measure/test_xbrl_cd_seal.py::FrozenToolsTest::test_12_engine_and_tools_have_not_moved` | sha・指紋 | 宣言された遷移(P26 の封 docs/XBRL_P26_SEAL_2026-10-21.md と後の sha / 指紋 / frozen_bundle)を足した |
| `tests/measure/test_xbrl_customer_report_fix_result.py::RecordTest::test_5_module_and_untouched_files_are_the_ones_measured` | sha・指紋 | 宣言された遷移(P26 の封 docs/XBRL_P26_SEAL_2026-10-21.md と後の sha / 指紋 / frozen_bundle)を足した |
| `tests/measure/test_xbrl_customer_report_fix_result.py::MutationTest::test_baseline_is_green` | sha・指紋 | 宣言された遷移(P26 の封 docs/XBRL_P26_SEAL_2026-10-21.md と後の sha / 指紋 / frozen_bundle)を足した |
| `tests/measure/test_xbrl_customer_report_fix_seal.py::SealTest::test_11_untouched_files_keep_their_sha` | sha・指紋 | 宣言された遷移(P26 の封 docs/XBRL_P26_SEAL_2026-10-21.md と後の sha / 指紋 / frozen_bundle)を足した |
| `tests/measure/test_xbrl_customer_report_fix_seal.py::SealTest::test_12_engine_fingerprint_is_the_one_at_the_seal_or_a_declared_transition` | sha・指紋 | 宣言された遷移(P26 の封 docs/XBRL_P26_SEAL_2026-10-21.md と後の sha / 指紋 / frozen_bundle)を足した |
| `tests/measure/test_xbrl_customer_report_fix_seal.py::SealTest::test_13_frozen_bundle_is_the_one_at_the_seal_or_a_declared_transition` | sha・指紋 | 宣言された遷移(P26 の封 docs/XBRL_P26_SEAL_2026-10-21.md と後の sha / 指紋 / frozen_bundle)を足した |
| `tests/measure/test_xbrl_customer_report_fix_seal.py::SealTest::test_9_the_target_module_is_the_one_at_the_seal_and_has_no_zip_or_provenance_yet` | sha・指紋 | 宣言された遷移(P26 の封 docs/XBRL_P26_SEAL_2026-10-21.md と後の sha / 指紋 / frozen_bundle)を足した |
| `tests/measure/test_xbrl_customer_report_result.py::RecordTest::test_3_judgments_are_recomputed_from_rows_and_the_seal` | 登録簿と理由の表 | 理由の数・表の行数を 16 → 19(PNF 10・UNV 9)に直した(数の字を 1 か所ずつ) |
| `tests/measure/test_xbrl_customer_report_result.py::RecordTest::test_5_module_and_untouched_files_are_the_ones_measured` | sha・指紋 | 宣言された遷移(P26 の封 docs/XBRL_P26_SEAL_2026-10-21.md と後の sha / 指紋 / frozen_bundle)を足した |
| `tests/measure/test_xbrl_customer_report_result.py::RecordTest::test_6_c3_is_recomputed_from_the_module_and_the_registry_not_the_record` | 登録簿と理由の表 | 理由の数・表の行数を 16 → 19(PNF 10・UNV 9)に直した(数の字を 1 か所ずつ) |
| `tests/measure/test_xbrl_customer_report_result.py::MutationTest::test_baseline_is_green` | 登録簿と理由の表 | 理由の数・表の行数を 16 → 19(PNF 10・UNV 9)に直した(数の字を 1 か所ずつ) |
| `tests/measure/test_xbrl_customer_report_result.py::MutationTest::test_m15_c3_goes_red_when_the_table_loses_a_reason` | 登録簿と理由の表 | 理由の数・表の行数を 16 → 19(PNF 10・UNV 9)に直した(数の字を 1 か所ずつ) |
| `tests/measure/test_xbrl_customer_report_seal.py::SealTest::test_8_reason_table_key_counts_match_the_engine` | 登録簿と理由の表 | 理由の数・表の行数を 16 → 19(PNF 10・UNV 9)に直した(数の字を 1 か所ずつ) |
| `tests/measure/test_xbrl_customer_report_seal.py::SealedStateTest::test_11_untouched_files_keep_their_sha` | sha・指紋 | 宣言された遷移(P26 の封 docs/XBRL_P26_SEAL_2026-10-21.md と後の sha / 指紋 / frozen_bundle)を足した |
| `tests/measure/test_xbrl_customer_report_seal.py::SealedStateTest::test_12_engine_fingerprint_and_frozen_bundle_are_the_ones_at_the_seal_or_a_declared_transition` | sha・指紋 | 宣言された遷移(P26 の封 docs/XBRL_P26_SEAL_2026-10-21.md と後の sha / 指紋 / frozen_bundle)を足した |
| `tests/measure/test_xbrl_lastbranch_result.py::RecordTest::test_6_engine_is_the_one_measured_or_a_declared_transition` | sha・指紋 | 宣言された遷移(P26 の封 docs/XBRL_P26_SEAL_2026-10-21.md と後の sha / 指紋 / frozen_bundle)を足した |
| `tests/measure/test_xbrl_lastbranch_result.py::MutationTest::test_baseline_is_green` | sha・指紋 | 宣言された遷移(P26 の封 docs/XBRL_P26_SEAL_2026-10-21.md と後の sha / 指紋 / frozen_bundle)を足した |
| `tests/measure/test_xbrl_lastbranch_result.py::MutationTest::test_m20_a_wrong_engine_sha_is_red` | sha・指紋 | ENGINE_LATER に P26 の封の遷移(vocabulary・recipes・registry_setup)を足し、m20 は宣言された後の sha を取り違えた形でも赤になるよう直した |
| `tests/measure/test_xbrl_lastbranch_seal.py::SealTest::test_9_p24_flags_and_p25_base_are_unchanged` | profile の一覧 | 期待する profile の一覧に P26 を足した(P26 = P25 + 旗 5 つ) |
| `tests/measure/test_xbrl_lastbranch_seal.py::EngineAtSealTest::test_13_engine_sha_is_the_one_at_the_seal_or_a_declared_transition` | sha・指紋 | 宣言された遷移(P26 の封 docs/XBRL_P26_SEAL_2026-10-21.md と後の sha / 指紋 / frozen_bundle)を足した |
| `tests/measure/test_xbrl_lastbranch_seal.py::EngineAtSealTest::test_14_new_flag_p25_and_no_same_value_exist_now_default_is_p22` | profile の一覧 | 期待する profile の一覧に P26 を足した(P26 = P25 + 旗 5 つ) |
| `tests/measure/test_xbrl_p20_result.py::DisciplineTest::test_11_engine_is_untouched` | sha・指紋 | 宣言された遷移(P26 の封 docs/XBRL_P26_SEAL_2026-10-21.md と後の sha / 指紋 / frozen_bundle)を足した |
| `tests/measure/test_xbrl_period_bind_result.py::RecordTest::test_16_frozen_bundle_last_generation_is_the_working_tree_and_declares_step_2` | sha・指紋 | 宣言された遷移(P26 の封 docs/XBRL_P26_SEAL_2026-10-21.md と後の sha / 指紋 / frozen_bundle)を足した |
| `tests/measure/test_xbrl_period_bind_result.py::RecordTest::test_8_engine_is_the_one_measured_or_a_declared_transition` | sha・指紋 | 宣言された遷移(P26 の封 docs/XBRL_P26_SEAL_2026-10-21.md と後の sha / 指紋 / frozen_bundle)を足した |
| `tests/measure/test_xbrl_period_bind_seal.py::EngineAtSealTest::test_12_engine_sha_is_the_one_at_the_seal_or_a_declared_transition` | sha・指紋 | 宣言された遷移(P26 の封 docs/XBRL_P26_SEAL_2026-10-21.md と後の sha / 指紋 / frozen_bundle)を足した |
| `tests/measure/test_xbrl_period_bind_seal.py::EngineAtSealTest::test_13_default_is_p22_from_step_2_and_p22_is_registered_with_the_flag` | profile の一覧 | 期待する profile の一覧に P26 を足した(P26 = P25 + 旗 5 つ) |
| `tests/measure/test_xbrl_pnf_diag.py::DisciplineTest::test_7_engine_files_are_untouched` | sha・指紋 | 宣言された遷移(P26 の封 docs/XBRL_P26_SEAL_2026-10-21.md と後の sha / 指紋 / frozen_bundle)を足した |
| `tests/measure/test_xbrl_point_prior_result.py::RecordTest::test_3_judgments_recomputed_equal_the_script_and_the_record` | sha・指紋 | 宣言された遷移(P26 の封 docs/XBRL_P26_SEAL_2026-10-21.md と後の sha / 指紋 / frozen_bundle)を足した |
| `tests/measure/test_xbrl_point_prior_result.py::DocTest::test_6_the_document_equals_what_the_record_says` | sha・指紋 | 宣言された遷移(P26 の封 docs/XBRL_P26_SEAL_2026-10-21.md と後の sha / 指紋 / frozen_bundle)を足した |
| `tests/measure/test_xbrl_point_prior_result.py::DocTest::test_7_seal_and_engine_are_untouched_since_the_seal_commit` | sha・指紋 | 宣言された遷移(P26 の封 docs/XBRL_P26_SEAL_2026-10-21.md と後の sha / 指紋 / frozen_bundle)を足した |
| `tests/measure/test_xbrl_point_prior_result.py::MutationTest::test_m0_the_genuine_samples_pass` | sha・指紋 | 宣言された遷移(P26 の封 docs/XBRL_P26_SEAL_2026-10-21.md と後の sha / 指紋 / frozen_bundle)を足した |
| `tests/measure/test_xbrl_ritual_result.py::PredictionTest::test_8_judgments_recomputed_equal_the_document_table` | sha・指紋 | 宣言された遷移(P26 の封 docs/XBRL_P26_SEAL_2026-10-21.md と後の sha / 指紋 / frozen_bundle)を足した |
| `tests/measure/test_xbrl_role_swap_result.py::DisciplineTest::test_11_engine_untouched` | sha・指紋 | 宣言された遷移(P26 の封 docs/XBRL_P26_SEAL_2026-10-21.md と後の sha / 指紋 / frozen_bundle)を足した |
| `tests/measure/test_xbrl_rounding_result.py::RecordTest::test_6_engine_is_the_one_measured_or_a_declared_transition` | sha・指紋 | 宣言された遷移(P26 の封 docs/XBRL_P26_SEAL_2026-10-21.md と後の sha / 指紋 / frozen_bundle)を足した |
| `tests/measure/test_xbrl_rounding_result.py::MutationTest::test_baseline_is_green` | sha・指紋 | 宣言された遷移(P26 の封 docs/XBRL_P26_SEAL_2026-10-21.md と後の sha / 指紋 / frozen_bundle)を足した |
| `tests/measure/test_xbrl_rounding_result.py::MutationTest::test_m16_a_wrong_engine_sha_is_red` | sha・指紋 | 宣言された遷移(P26 の封 docs/XBRL_P26_SEAL_2026-10-21.md と後の sha / 指紋 / frozen_bundle)を足した |
| `tests/measure/test_xbrl_rounding_seal.py::EngineAtSealTest::test_11_engine_sha_is_the_one_at_the_seal_or_a_declared_transition` | sha・指紋 | 宣言された遷移(P26 の封 docs/XBRL_P26_SEAL_2026-10-21.md と後の sha / 指紋 / frozen_bundle)を足した |
| `tests/measure/test_xbrl_rounding_seal.py::EngineAtSealTest::test_12_flags_exist_default_is_p22_and_p23_is_p22_plus_the_two_flags` | profile の一覧 | 期待する profile の一覧に P26 を足した(P26 = P25 + 旗 5 つ) |
| `tests/measure/test_xbrl_vocab_result.py::RecordTest::test_6_engine_is_the_one_measured_or_a_declared_transition` | sha・指紋 | 宣言された遷移(P26 の封 docs/XBRL_P26_SEAL_2026-10-21.md と後の sha / 指紋 / frozen_bundle)を足した |
| `tests/measure/test_xbrl_vocab_result.py::MutationTest::test_baseline_is_green` | sha・指紋 | 宣言された遷移(P26 の封 docs/XBRL_P26_SEAL_2026-10-21.md と後の sha / 指紋 / frozen_bundle)を足した |
| `tests/measure/test_xbrl_vocab_result.py::MutationTest::test_m16_a_wrong_engine_sha_is_red` | sha・指紋 | 宣言された遷移(P26 の封 docs/XBRL_P26_SEAL_2026-10-21.md と後の sha / 指紋 / frozen_bundle)を足した |
| `tests/measure/test_xbrl_vocab_seal.py::EngineAtSealTest::test_13_engine_sha_is_the_one_at_the_seal_or_a_declared_transition` | sha・指紋 | 宣言された遷移(P26 の封 docs/XBRL_P26_SEAL_2026-10-21.md と後の sha / 指紋 / frozen_bundle)を足した |
| `tests/measure/test_xbrl_vocab_seal.py::EngineAtSealTest::test_14_new_flags_p24_and_other_frame_exist_now_default_is_p22` | profile の一覧 | 期待する profile の一覧に P26 を足した(P26 = P25 + 旗 5 つ) |
| `tests/measure/test_xbrl_vocab_seal.py::EngineAtSealTest::test_15_p23_flags_are_unchanged` | profile の一覧 | 期待する profile の一覧に P26 を足した(P26 = P25 + 旗 5 つ) |
| `tests/adapters/xbrl/test_mutations.py::MutationTwoWayTest::test_all_mutations_match_their_prediction` | 変異の予測 | mutation の木が写す試験(test_vocabulary・test_registry_setup など)の一覧を直した結果で緑に戻った。mutations.json は変えていない |
| `tests/adapters/xbrl/test_mutations.py::MutationsDoNotTouchRealSourceTest::test_real_source_sha256_unchanged_after_mutation_run` | 変異の予測 | mutation の木が写す試験(test_vocabulary・test_registry_setup など)の一覧を直した結果で緑に戻った。mutations.json は変えていない |
| `tests/adapters/xbrl/test_p17.py::PctToleranceTest::test_p18_is_p17_plus_the_tolerance_flag` | profile の一覧 | 期待する profile の一覧に P26 を足した(P26 = P25 + 旗 5 つ) |
| `tests/adapters/xbrl/test_p20.py::ProfileShapeTest::test_every_other_profile_keeps_the_flag_off` | profile の一覧 | 期待する profile の一覧に P26 を足した(P26 = P25 + 旗 5 つ) |
| `tests/adapters/xbrl/test_recipes_p21.py::FlagShapeTest::test_only_p21_has_the_flag_on` | profile の一覧 | 期待する profile の一覧に P26 を足した(P26 = P25 + 旗 5 つ) |
| `tests/adapters/xbrl/test_recipes_p22.py::FlagShapeTest::test_only_p22_has_the_flag_on` | profile の一覧 | 期待する profile の一覧に P26 を足した(P26 = P25 + 旗 5 つ) |
| `tests/adapters/xbrl/test_recipes_p22.py::WithoutCueTest::test_every_profile_before_p22_keeps_grounding_the_prior_fact` | profile の一覧 | 期待する profile の一覧に P26 を足した(P26 = P25 + 旗 5 つ) |
| `tests/adapters/xbrl/test_recipes_p23.py::FlagShapeTest::test_only_p23_has_the_new_flag_on` | profile の一覧 | 期待する profile の一覧に P26 を足した(P26 = P25 + 旗 5 つ) |
| `tests/adapters/xbrl/test_recipes_p23.py::P22UnchangedTest::test_every_profile_but_p23_keeps_the_signed_band_under_truncate` | profile の一覧 | 期待する profile の一覧に P26 を足した(P26 = P25 + 旗 5 つ) |
| `tests/adapters/xbrl/test_recipes_p24.py::FlagShapeTest::test_the_flags_are_false_by_default_and_for_every_other_profile` | profile の一覧 | 期待する profile の一覧に P26 を足した(P26 = P25 + 旗 5 つ) |
| `tests/adapters/xbrl/test_recipes_p25.py::FlagShapeTest::test_the_flag_is_false_by_default_and_true_only_for_p25` | profile の一覧 | 期待する profile の一覧に P26 を足した(P26 = P25 + 旗 5 つ) |
| `tests/adapters/xbrl/test_recipes_p25.py::FlagsOffIsP24Test::test_no_other_profile_is_touched_by_the_branch` | profile の一覧 | 期待する profile の一覧に P26 を足した(P26 = P25 + 旗 5 つ) |
| `tests/adapters/xbrl/test_registry_setup.py::RegisterAllTest::test_register_all_registration_counts_from_registry` | 登録簿と理由の表 | 理由の数・表の行数を 16 → 19(PNF 10・UNV 9)に直した(数の字を 1 か所ずつ) |
| `tests/adapters/xbrl/test_report_customer.py::ReasonTableTest::test_reason_table_is_exactly_the_registry` | 登録簿と理由の表 | 理由の数・表の行数を 16 → 19(PNF 10・UNV 9)に直した(数の字を 1 か所ずつ) |
| `tests/adapters/xbrl/test_report_customer.py::ReasonTableTest::test_registry_has_sixteen_reasons_and_is_unbound_reason_state_plus_two` | 登録簿と理由の表 | 理由の数・表の行数を 16 → 19(PNF 10・UNV 9)に直した(数の字を 1 か所ずつ) |
| `tests/adapters/xbrl/test_vocabulary.py::ProfileListPinsAreSelfCheckedTest::test_every_registry_pin_matches_the_registry` | profile の一覧 | 期待する profile の一覧に P26 を足した(P26 = P25 + 旗 5 つ) |
| `tests/adapters/xbrl/test_vocabulary.py::P7ProfileTest::test_p7_in_profiles_registry` | profile の一覧 | 期待する profile の一覧に P26 を足した(P26 = P25 + 旗 5 つ) |
| `tests/adapters/xbrl/test_vocabulary.py::P12P13P14ProfileTest::test_profiles_registry_lists_every_profile` | profile の一覧 | 期待する profile の一覧に P26 を足した(P26 = P25 + 旗 5 つ) |

赤は全部、sha・指紋の留め、profile の一覧、登録簿と理由の表、変異の予測の連鎖で、数の門・state の門・人間の決定の字の門の赤は零だった。直しは、遷移の宣言(後の sha と P26 の封)・期待する一覧に P26 を足す・理由の数を十六から十九に直す、だけ。**人間の決定の行の字は変えていない**(`comparators.py` は零行、`core/` は零行、`report.py`・`verify_document.py` も零行)。

既存の行の書き換えは `recipes.py` の数の読み取りの for 文一行だけ(`E.iter_numbers(s)` を `_numbers_of(profile, s)` にした)。`iter_numbers` 自身の字は変えていない(写し元との照合 `test_lineage` は緑)。

pin の遷移で試験の側を足した所: 封が名指した十本の連鎖に加え、`point_prior_result` と `ritual_result` は `adapters` を丸ごと見る門なので、`extract.py` の遷移を足した。`lastbranch_result` の `test_m20` は、遷移が宣言された file では測った時点の sha を取り違えても赤にならない形だったので、宣言された後の sha を取り違えた形でも赤になるように直した。封の列挙に在った `test_xbrl_verify_inventory.py` の `test_9_engine_untouched` は、`comparators.py` だけを留める門で P26 が触らないので、赤にならず、直していない。

## 7. Q-7 報告形

| 項目 | 実測 |
|---|---|
| 報告形の「違う」の節の合計(P26 を明示した 67 書類) | 433 |
| P26 の VALUE_MISMATCH(state)の合計 | 433 |
| 三つの理由の行(入った節) | 205(要確認 205) |
| 登録簿の理由 | 19(POINTER_NOT_FOUND 10・UNVERIFIABLE 9) |
| うち報告形の表 REASON_JA にある | 19 |

三つの理由(`other_concept`・`direction_on_cause_item`・`rounded_diff_within_double_band`)の行は、P26 を明示した六十七書類で全部「要確認」の節に入り、「違う」の節は P26 の VALUE_MISMATCH と書類ごとにも一致した。報告形の理由の表には封の文言どおりの三行を足した。

## 8. 段 2 に人間へ見せる数(Q-8。判定しない)

この実行では何も変えていない。見せる数は第二節の state の表(「違う」六百二十六 → 四百三十三、「違う」の割合は表のとおり)と、第四〜五節の誤りを通す数(全部零)。**新しい標本での判定は `docs/XBRL_FRESH_SAMPLE_SEAL_2026-10-21.md` §3 の基準で、標本を取ってから。** 「判定しない(段 2)」。

## 9. engine の変異(手で走らせた)

engine の変異 32 通りは、作業木とは別のコピー(scratchpad の使い捨ての木。adapters/・core/・tests/adapters/xbrl の必要な file を写した)の recipes.py・extract.py・vocabulary.py・registry_setup.py に 1 つずつ入れ、tests/adapters/xbrl/test_recipes_p26.py だけを走らせ、毎回コピーを作り直して戻した(木は走らせの後に消した。実木の engine 6 file は走らせの前後で sha256 が同じ)。予測は実走の前に固定した(mut_defs.py の sha256 50aab42c374755984d818b9c235f8e583e683c7af5db728543a6551cd4f65bf0 を走らせの前に書いた)。手で走らせた。この表は記録の写しを門が縛るだけで、変異そのものを毎回走らせてはいない。基準線は P26 の試験 74 本(全緑)。初回の走らせの途中で M5 の黙りを見て試験を 1 本足したので、初回の M29〜M32 は 75 本、M1〜M28 は 74 本で測った。初回: 緑(黙った変異)2 件(M5・M23)、赤 30 件。予測の当たり 14・外れ 18(外れのうち『赤が多かった』11・『赤が少なかった』1・『緑だった』または別の試験が赤 6)。黙った変異 2 件の原因は試験の弱さだった: M5 は帯の下限を試す値が桁の整数倍だけで下限の変異に届かなかったこと、M23 は主語が 2 回出る文で最初の出現と最後の出現の gap が同じ形になる値だったこと。あわせて、旗のガードを外す変異 M1 を『旗が偽の側が止めている』ことを確かめない対の比べが見逃す形だったので、その試験に旗の無い側の結果を確かめる 1 行と、旗の行が動く実物の書類 2 本(S100Z5CH・S100YYQX)を足した。試験を直して(74 本 → 75 本)全部再実測したら、32 通り全部赤(黙った変異は 0)。

| # | 変異 | 予測 | 実測 |
|---|---|---|---|
| M1 | recipes.py: G3 の旗のガード `getattr(profile, "rounded_diff_hold", False) and` を外す(旗が偽でも丸めた差を止める) | FlagsOffIsP25Test::test_real_documents_are_identical_to_p25_with_the_flags_off・FlagsOffIsP25Test::test_the_flags_alone_change_only_their_own_rows・RoundedDiffHoldTest::test_the_flag_alone_is_enough_and_false_means_p25 | 初回 赤 4 本(HumanDecisionsTest::test_g3_comes_before_f3b_and_only_in_the_second_pass・RoundedDiffHoldTest::test_one_unit_short_is_held_not_named・RoundedDiffHoldTest::test_real_document_rows・RoundedDiffHoldTest::test_the_round_mode_holds_too)。最終の試験(75 本)で 赤 6 本(FlagsOffIsP25Test::test_real_documents_are_identical_to_p25_with_the_flags_off・HumanDecisionsTest::test_g3_comes_before_f3b_and_only_in_the_second_pass・RoundedDiffHoldTest::test_one_unit_short_is_held_not_named・RoundedDiffHoldTest::test_real_document_rows・RoundedDiffHoldTest::test_the_flag_alone_is_enough_and_false_means_p25・RoundedDiffHoldTest::test_the_round_mode_holds_too)。外れ(予測と別の試験が赤) |
| M2 | recipes.py: G3 の『当期の残高だけ』の条件 `startswith("CurrentYearInstant")` を外す | RoundedDiffHoldTest::test_only_a_current_balance_with_a_prior_pair_and_a_difference_sentence | 初回 赤 1 本(RoundedDiffHoldTest::test_only_a_current_balance_with_a_prior_pair_and_a_difference_sentence)。最終の試験(75 本)で 赤 1 本(RoundedDiffHoldTest::test_only_a_current_balance_with_a_prior_pair_and_a_difference_sentence)。予測どおり |
| M3 | recipes.py: G3 の『2 つの fact の精度が主張の桁と同じ』の条件を外す | RoundedDiffHoldTest::test_the_precision_of_both_facts_must_equal_the_claim_scale | 初回 赤 1 本(RoundedDiffHoldTest::test_the_precision_of_both_facts_must_equal_the_claim_scale)。最終の試験(75 本)で 赤 1 本(RoundedDiffHoldTest::test_the_precision_of_both_facts_must_equal_the_claim_scale)。予測どおり |
| M4 | recipes.py: G3 の帯 ROUNDED_DIFF_BAND_X を 2 → 3 にする | FlagShapeTest::test_the_constants_are_pinned_in_letters・RoundedDiffHoldTest::test_two_units_short_or_larger_than_the_difference_is_not_held | 初回 赤 3 本(FlagShapeTest::test_the_constants_are_pinned_in_letters・RoundedDiffHoldTest::test_g3_never_makes_a_grounded_row_over_a_grid・RoundedDiffHoldTest::test_two_units_short_or_larger_than_the_difference_is_not_held)。最終の試験(75 本)で 赤 3 本(FlagShapeTest::test_the_constants_are_pinned_in_letters・RoundedDiffHoldTest::test_g3_never_makes_a_grounded_row_over_a_grid・RoundedDiffHoldTest::test_two_units_short_or_larger_than_the_difference_is_not_held)。外れ(赤が多かった) |
| M5 | recipes.py: G3 の下限 `0 <=` を `-scale <` にする(文の数のほうが fact の差より 1 単位まで大きい場合も止める) | RoundedDiffHoldTest::test_two_units_short_or_larger_than_the_difference_is_not_held | 初回 緑(赤 0 本)。試験の弱さ。直して再実測。最終の試験(75 本)で 赤 1 本(RoundedDiffHoldTest::test_the_lower_bound_is_zero_a_difference_smaller_than_the_sentence_is_not_matched)。外れ(予測は赤、初回は緑 = 黙った変異) |
| M6 | recipes.py: G3 の reason を登録簿の名前でなく P25 までの `value differs(segment/other period?)` にする | RoundedDiffHoldTest::test_one_unit_short_is_held_not_named・RoundedDiffHoldTest::test_the_recipe_keeps_the_named_pair_in_provenance_and_no_pointer・RoundedDiffHoldTest::test_core_turns_it_into_unverifiable_with_the_registered_reason_and_no_pointer・RoundedDiffHoldTest::test_real_document_rows | 初回 赤 11 本(CauseItemGateTest::test_real_document_rows・FlagsOffIsP25Test::test_real_documents_are_identical_to_p25_with_the_flags_off・RoundedDiffHoldTest::test_a_decrease_is_held_the_same_way・RoundedDiffHoldTest::test_core_turns_it_into_unverifiable_with_the_registered_reason_and_no_pointer・RoundedDiffHoldTest::test_g3_never_makes_a_grounded_row_over_a_grid・RoundedDiffHoldTest::test_one_unit_short_is_held_not_named・RoundedDiffHoldTest::test_real_document_rows・RoundedDiffHoldTest::test_the_flag_alone_is_enough_and_false_means_p25・RoundedDiffHoldTest::test_the_precision_of_both_facts_must_equal_the_claim_scale・RoundedDiffHoldTest::test_the_recipe_keeps_the_named_pair_in_provenance_and_no_pointer・RoundedDiffHoldTest::test_the_round_mode_holds_too)。最終の試験(75 本)で 赤 11 本(CauseItemGateTest::test_real_document_rows・FlagsOffIsP25Test::test_real_documents_are_identical_to_p25_with_the_flags_off・RoundedDiffHoldTest::test_a_decrease_is_held_the_same_way・RoundedDiffHoldTest::test_core_turns_it_into_unverifiable_with_the_registered_reason_and_no_pointer・RoundedDiffHoldTest::test_g3_never_makes_a_grounded_row_over_a_grid・RoundedDiffHoldTest::test_one_unit_short_is_held_not_named・RoundedDiffHoldTest::test_real_document_rows・RoundedDiffHoldTest::test_the_flag_alone_is_enough_and_false_means_p25・RoundedDiffHoldTest::test_the_precision_of_both_facts_must_equal_the_claim_scale・RoundedDiffHoldTest::test_the_recipe_keeps_the_named_pair_in_provenance_and_no_pointer・RoundedDiffHoldTest::test_the_round_mode_holds_too)。外れ(赤が多かった) |
| M7 | recipes.py: G1 unit_family の食い違いの向きを反転(`!=` を `==` に) | ConceptGateTest::test_unit_family_a_per_share_fact_for_a_total_subject・ConceptGateTest::test_unit_family_a_total_fact_for_a_per_share_subject・ConceptGateTest::test_unit_family_does_not_hit_matching_families_or_other_units・ConceptGateTest::test_real_document_rows | 初回 赤 6 本(ConceptGateTest::test_the_order_is_unit_family_then_loose_prefix・ConceptGateTest::test_the_recipe_keeps_the_named_facts_in_provenance_and_core_gives_pointer_not_found・ConceptGateTest::test_unit_family_a_per_share_fact_for_a_total_subject・ConceptGateTest::test_unit_family_a_total_fact_for_a_per_share_subject・ConceptGateTest::test_unit_family_does_not_hit_matching_families_or_other_units・FlagsOffIsP25Test::test_the_flags_alone_change_only_their_own_rows)。最終の試験(75 本)で 赤 6 本(ConceptGateTest::test_the_order_is_unit_family_then_loose_prefix・ConceptGateTest::test_the_recipe_keeps_the_named_facts_in_provenance_and_core_gives_pointer_not_found・ConceptGateTest::test_unit_family_a_per_share_fact_for_a_total_subject・ConceptGateTest::test_unit_family_a_total_fact_for_a_per_share_subject・ConceptGateTest::test_unit_family_does_not_hit_matching_families_or_other_units・FlagsOffIsP25Test::test_the_flags_alone_change_only_their_own_rows)。外れ(予測と別の試験が赤) |
| M8 | recipes.py: G1 unit_family の `JPY の族でない単位は見ない` の足切り `continue` を外す | ConceptGateTest::test_unit_family_does_not_hit_matching_families_or_other_units | 初回 赤 1 本(ConceptGateTest::test_unit_family_does_not_hit_matching_families_or_other_units)。最終の試験(75 本)で 赤 1 本(ConceptGateTest::test_unit_family_does_not_hit_matching_families_or_other_units)。予測どおり |
| M9 | recipes.py: G1 の `_core_grounded` の『符号の行で差がちょうど 0 は一致でない』の例外を外す | ConceptGateTest::test_a_sign_row_with_zero_difference_is_not_counted_as_grounded | 初回 赤 2 本(ConceptGateTest::test_a_sign_row_with_zero_difference_is_not_counted_as_grounded・ConceptGateTest::test_real_document_rows)。最終の試験(75 本)で 赤 2 本(ConceptGateTest::test_a_sign_row_with_zero_difference_is_not_counted_as_grounded・ConceptGateTest::test_real_document_rows)。外れ(赤が多かった) |
| M10 | recipes.py: G1 の入口 `not claim.get("bound")`(束縛のない行は触らない)を外す | ConceptGateTest::test_grounded_unbound_and_pointerless_rows_are_untouched | 初回 赤 1 本(ConceptGateTest::test_grounded_unbound_and_pointerless_rows_are_untouched)。最終の試験(75 本)で 赤 1 本(ConceptGateTest::test_grounded_unbound_and_pointerless_rows_are_untouched)。予測どおり |
| M11 | recipes.py: G1 loose_prefix の `all(...)`(部分一致した要素の全部が前置きの悪い形)を `any(...)` にする | ConceptGateTest::test_loose_prefix_needs_all_of_the_matching_elements_to_have_a_bad_prefix | 初回 赤 1 本(ConceptGateTest::test_loose_prefix_needs_all_of_the_matching_elements_to_have_a_bad_prefix)。最終の試験(75 本)で 赤 1 本(ConceptGateTest::test_loose_prefix_needs_all_of_the_matching_elements_to_have_a_bad_prefix)。予測どおり |
| M12 | recipes.py: G1 の CONCEPT_GATE_PREFIX_OK から "Cash" を落とす | FlagShapeTest::test_the_constants_are_pinned_in_letters・ConceptGateTest::test_loose_prefix_does_not_hit_an_exact_name_or_the_summary_names_or_ok_prefixes | 初回 赤 4 本(ConceptGateTest::test_loose_prefix_does_not_hit_an_exact_name_or_the_summary_names_or_ok_prefixes・ConceptGateTest::test_loose_prefix_needs_all_of_the_matching_elements_to_have_a_bad_prefix・FlagShapeTest::test_the_constants_are_pinned_in_letters・FlagsOffIsP25Test::test_the_flags_alone_change_only_their_own_rows)。最終の試験(75 本)で 赤 4 本(ConceptGateTest::test_loose_prefix_does_not_hit_an_exact_name_or_the_summary_names_or_ok_prefixes・ConceptGateTest::test_loose_prefix_needs_all_of_the_matching_elements_to_have_a_bad_prefix・FlagShapeTest::test_the_constants_are_pinned_in_letters・FlagsOffIsP25Test::test_the_flags_alone_change_only_their_own_rows)。外れ(赤が多かった) |
| M13 | recipes.py: G1 loose_prefix が見る pointer を『先頭』から『最後』にする | ConceptGateTest::test_loose_prefix_uses_the_first_xbrl_pointer_only | 初回 赤 1 本(ConceptGateTest::test_loose_prefix_uses_the_first_xbrl_pointer_only)。最終の試験(75 本)で 赤 1 本(ConceptGateTest::test_loose_prefix_uses_the_first_xbrl_pointer_only)。予測どおり |
| M14 | recipes.py: G1 loose_prefix の『flow_item・ratio_table の主語は見ない』を外す | ConceptGateTest::test_loose_prefix_is_skipped_for_flow_item_and_ratio_table_subjects | 初回 赤 1 本(ConceptGateTest::test_loose_prefix_is_skipped_for_flow_item_and_ratio_table_subjects)。最終の試験(75 本)で 赤 1 本(ConceptGateTest::test_loose_prefix_is_skipped_for_flow_item_and_ratio_table_subjects)。予測どおり |
| M15 | recipes.py: G1 を文字の主張(text_claims)に当てない(`num_claims + text_claims` を `num_claims` に) | ConceptGateTest::test_real_document_rows | 初回 赤 2 本(ConceptGateTest::test_real_document_rows・ConceptGateTest::test_the_recipe_keeps_the_named_facts_in_provenance_and_core_gives_pointer_not_found)。最終の試験(75 本)で 赤 2 本(ConceptGateTest::test_real_document_rows・ConceptGateTest::test_the_recipe_keeps_the_named_facts_in_provenance_and_core_gives_pointer_not_found)。外れ(赤が多かった) |
| M16 | recipes.py: G2 の LAST_BRANCH_NAMED_MIN_K を 2 → 1 にする | FlagShapeTest::test_the_constants_are_pinned_in_letters・DigitNeedsSizeTest::test_p25_names_a_small_value_by_digit_within_k_and_p26_does_not・DigitNeedsSizeTest::test_a_real_document_row | 初回 赤 2 本(DigitNeedsSizeTest::test_the_boundary_is_two_times_the_unit・FlagShapeTest::test_the_constants_are_pinned_in_letters)。最終の試験(75 本)で 赤 2 本(DigitNeedsSizeTest::test_the_boundary_is_two_times_the_unit・FlagShapeTest::test_the_constants_are_pinned_in_letters)。外れ(予測と別の試験が赤) |
| M17 | recipes.py: G2 の境界 `<` を `<=` にする(ちょうど 2 単位の値を証拠にしない) | DigitNeedsSizeTest::test_the_boundary_is_two_times_the_unit | 初回 赤 1 本(DigitNeedsSizeTest::test_the_boundary_is_two_times_the_unit)。最終の試験(75 本)で 赤 1 本(DigitNeedsSizeTest::test_the_boundary_is_two_times_the_unit)。予測どおり |
| M18 | recipes.py: G2 を P25 の旗なしでも効かせる(`last_branch_names_only_if_evidence` の条件を外す) | DigitNeedsSizeTest::test_it_needs_the_p25_flag_too | 初回 赤 1 本(DigitNeedsSizeTest::test_it_needs_the_p25_flag_too)。最終の試験(75 本)で 赤 1 本(DigitNeedsSizeTest::test_it_needs_the_p25_flag_too)。予測どおり |
| M19 | recipes.py: G4 形 A の『gap に金額の数が在る』条件を外す | CauseItemFormTest::test_form_a_needs_a_money_number_between_the_subject_and_the_word | 初回 赤 1 本(CauseItemFormTest::test_form_a_needs_a_money_number_between_the_subject_and_the_word)。最終の試験(75 本)で 赤 2 本(CauseItemFormTest::test_form_a_needs_a_money_number_between_the_subject_and_the_word・CauseItemFormTest::test_the_gap_runs_from_the_last_occurrence_of_the_subject)。予測どおり |
| M20 | recipes.py: G4 形 C の『gap が の だけ(主語そのものの向き)は当てない』を外す | CauseItemFormTest::test_form_c_does_not_hit_the_subjects_own_direction | 初回 赤 2 本(CauseItemFormTest::test_form_c_does_not_hit_the_subjects_own_direction・CauseItemGateTest::test_a_row_the_forms_do_not_hit_is_untouched)。最終の試験(75 本)で 赤 2 本(CauseItemFormTest::test_form_c_does_not_hit_the_subjects_own_direction・CauseItemGateTest::test_a_row_the_forms_do_not_hit_is_untouched)。外れ(赤が多かった) |
| M21 | recipes.py: G4 の除外『主語が語のかかる列挙の 1 つ』を外す | CauseItemFormTest::test_the_exclusion_the_subject_is_one_of_an_enumeration | 初回 赤 2 本(CauseItemFormTest::test_the_exclusion_the_subject_is_one_of_an_enumeration・CauseItemGateTest::test_real_document_rows)。最終の試験(75 本)で 赤 2 本(CauseItemFormTest::test_the_exclusion_the_subject_is_one_of_an_enumeration・CauseItemGateTest::test_real_document_rows)。外れ(赤が多かった) |
| M22 | recipes.py: G4 の列挙の除外を閉じる字から数字を落とす(`[0-9０-９はがをにで。()（）]` → `[はがをにで。()（）]`) | CauseItemFormTest::test_the_exclusion_is_closed_by_digits_particles_and_brackets | 初回 赤 1 本(CauseItemFormTest::test_the_exclusion_is_closed_by_digits_particles_and_brackets)。最終の試験(75 本)で 赤 1 本(CauseItemFormTest::test_the_exclusion_is_closed_by_digits_particles_and_brackets)。予測どおり |
| M23 | recipes.py: G4 の gap の起点を『主語の最後の出現』から『最初の出現』にする(`rfind` → `find`) | CauseItemFormTest::test_the_gap_runs_from_the_last_occurrence_of_the_subject | 初回 緑(赤 0 本)。試験の弱さ。直して再実測。最終の試験(75 本)で 赤 1 本(CauseItemFormTest::test_the_gap_runs_from_the_last_occurrence_of_the_subject)。外れ(予測は赤、初回は緑 = 黙った変異) |
| M24 | recipes.py: G4 の『既に UNVERIFIABLE の主張には触らない』を外す | CauseItemGateTest::test_an_already_unverifiable_row_is_untouched | 初回 赤 1 本(CauseItemGateTest::test_an_already_unverifiable_row_is_untouched)。最終の試験(75 本)で 赤 1 本(CauseItemGateTest::test_an_already_unverifiable_row_is_untouched)。予測どおり |
| M25 | recipes.py: G4 の旗のガード(build_raw_claims の `if getattr(profile, "cause_item_direction", False):`)を外す | CauseItemGateTest::test_it_is_applied_in_build_raw_claims_before_the_concept_gate_and_only_with_the_flag・FlagsOffIsP25Test::test_real_documents_are_identical_to_p25_with_the_flags_off・FlagsOffIsP25Test::test_the_flags_alone_change_only_their_own_rows | 初回 赤 3 本(CauseItemGateTest::test_it_is_applied_in_build_raw_claims_before_the_concept_gate_and_only_with_the_flag・CauseItemGateTest::test_real_document_rows・FlagsOffIsP25Test::test_the_flags_alone_change_only_their_own_rows)。最終の試験(75 本)で 赤 3 本(CauseItemGateTest::test_it_is_applied_in_build_raw_claims_before_the_concept_gate_and_only_with_the_flag・CauseItemGateTest::test_real_document_rows・FlagsOffIsP25Test::test_the_flags_alone_change_only_their_own_rows)。外れ(予測と別の試験が赤) |
| M26 | extract.py: G5 の円銭の精度 0.01 → 1.0 | NumbersTest::test_yen_sen_joins_with_two_decimals | 初回 赤 1 本(NumbersTest::test_yen_sen_joins_with_two_decimals)。最終の試験(75 本)で 赤 1 本(NumbersTest::test_yen_sen_joins_with_two_decimals)。予測どおり |
| M27 | extract.py: G5 の連結に当たった範囲と重なる既存の読みを捨てない(`rest` を全部残す) | NumbersTest::test_cho_oku_joins_into_one_number・NumbersTest::test_man_sen_hyaku_joins・NumbersTest::test_yen_sen_joins_with_two_decimals・NumbersTest::test_the_claim_carries_the_joined_value_only_when_the_flag_is_true | 初回 赤 7 本(DigitNeedsSizeTest::test_a_real_document_row・FlagsOffIsP25Test::test_the_flags_alone_change_only_their_own_rows・NumbersTest::test_cho_oku_joins_into_one_number・NumbersTest::test_forms_that_do_not_join_are_read_as_before・NumbersTest::test_man_sen_hyaku_joins・NumbersTest::test_the_claim_carries_the_joined_value_only_when_the_flag_is_true・NumbersTest::test_yen_sen_joins_with_two_decimals)。最終の試験(75 本)で 赤 7 本(DigitNeedsSizeTest::test_a_real_document_row・FlagsOffIsP25Test::test_the_flags_alone_change_only_their_own_rows・NumbersTest::test_cho_oku_joins_into_one_number・NumbersTest::test_forms_that_do_not_join_are_read_as_before・NumbersTest::test_man_sen_hyaku_joins・NumbersTest::test_the_claim_carries_the_joined_value_only_when_the_flag_is_true・NumbersTest::test_yen_sen_joins_with_two_decimals)。外れ(赤が多かった) |
| M28 | extract.py: G5 の円銭の符号を落とす(`(-1 if m.group(1) else 1) * yen, "円", 0.01` → `yen, "円", 0.01`) | NumbersTest::test_a_minus_sign_is_carried | 初回 赤 1 本(NumbersTest::test_a_minus_sign_is_carried)。最終の試験(75 本)で 赤 1 本(NumbersTest::test_a_minus_sign_is_carried)。予測どおり |
| M29 | recipes.py: G5 の読み手の選択 `_numbers_of` の旗を反転(偽のとき連結の読み) | NumbersTest::test_the_flag_chooses_the_reader・NumbersTest::test_the_claim_carries_the_joined_value_only_when_the_flag_is_true・FlagsOffIsP25Test::test_real_documents_are_identical_to_p25_with_the_flags_off | 初回 赤 2 本(NumbersTest::test_the_claim_carries_the_joined_value_only_when_the_flag_is_true・NumbersTest::test_the_flag_chooses_the_reader)。最終の試験(75 本)で 赤 2 本(NumbersTest::test_the_claim_carries_the_joined_value_only_when_the_flag_is_true・NumbersTest::test_the_flag_chooses_the_reader)。外れ(赤が少なかった) |
| M30 | recipes.py: `_state_of` で rounded_diff_within_double_band を UNVERIFIABLE でなく POINTER_NOT_FOUND にする | FlagShapeTest::test_the_three_reasons_are_registered_in_the_right_state_and_nothing_else_is・RoundedDiffHoldTest::test_core_turns_it_into_unverifiable_with_the_registered_reason_and_no_pointer | 初回 赤 7 本(CauseItemGateTest::test_real_document_rows・FlagShapeTest::test_the_three_reasons_are_registered_in_the_right_state_and_nothing_else_is・FlagsOffIsP25Test::test_real_documents_are_identical_to_p25_with_the_flags_off・RoundedDiffHoldTest::test_core_turns_it_into_unverifiable_with_the_registered_reason_and_no_pointer・RoundedDiffHoldTest::test_one_unit_short_is_held_not_named・RoundedDiffHoldTest::test_real_document_rows・RoundedDiffHoldTest::test_the_recipe_keeps_the_named_pair_in_provenance_and_no_pointer)。最終の試験(75 本)で 赤 7 本(CauseItemGateTest::test_real_document_rows・FlagShapeTest::test_the_three_reasons_are_registered_in_the_right_state_and_nothing_else_is・FlagsOffIsP25Test::test_real_documents_are_identical_to_p25_with_the_flags_off・RoundedDiffHoldTest::test_core_turns_it_into_unverifiable_with_the_registered_reason_and_no_pointer・RoundedDiffHoldTest::test_one_unit_short_is_held_not_named・RoundedDiffHoldTest::test_real_document_rows・RoundedDiffHoldTest::test_the_recipe_keeps_the_named_pair_in_provenance_and_no_pointer)。外れ(赤が多かった) |
| M31 | registry_setup.py: 登録簿から理由 other_concept を落とす | FlagShapeTest::test_the_three_reasons_are_registered_in_the_right_state_and_nothing_else_is・FlagShapeTest::test_the_report_has_the_three_reason_lines_in_the_to_check_section・ConceptGateTest::test_the_recipe_keeps_the_named_facts_in_provenance_and_core_gives_pointer_not_found | 初回 赤 6 本(ConceptGateTest::test_real_document_rows・ConceptGateTest::test_the_recipe_keeps_the_named_facts_in_provenance_and_core_gives_pointer_not_found・DigitNeedsSizeTest::test_a_real_document_row・FlagShapeTest::test_the_report_has_the_three_reason_lines_in_the_to_check_section・FlagShapeTest::test_the_three_reasons_are_registered_in_the_right_state_and_nothing_else_is・FlagsOffIsP25Test::test_real_documents_are_identical_to_p25_with_the_flags_off)。最終の試験(75 本)で 赤 6 本(ConceptGateTest::test_real_document_rows・ConceptGateTest::test_the_recipe_keeps_the_named_facts_in_provenance_and_core_gives_pointer_not_found・DigitNeedsSizeTest::test_a_real_document_row・FlagShapeTest::test_the_report_has_the_three_reason_lines_in_the_to_check_section・FlagShapeTest::test_the_three_reasons_are_registered_in_the_right_state_and_nothing_else_is・FlagsOffIsP25Test::test_real_documents_are_identical_to_p25_with_the_flags_off)。外れ(赤が多かった) |
| M32 | vocabulary.py: P26 の旗 cause_item_direction を偽にする(`cause_item_direction=True, ` を落とす) | FlagShapeTest::test_p26_is_p25_plus_exactly_the_five_flags | 初回 赤 4 本(CauseItemGateTest::test_real_document_rows・FlagShapeTest::test_only_p26_has_any_flag_and_p26_is_the_only_new_profile・FlagShapeTest::test_p26_is_p25_plus_exactly_the_five_flags・FlagsOffIsP25Test::test_the_flags_alone_change_only_their_own_rows)。最終の試験(75 本)で 赤 4 本(CauseItemGateTest::test_real_document_rows・FlagShapeTest::test_only_p26_has_any_flag_and_p26_is_the_only_new_profile・FlagShapeTest::test_p26_is_p25_plus_exactly_the_five_flags・FlagsOffIsP25Test::test_the_flags_alone_change_only_their_own_rows)。外れ(赤が多かった) |

## 10. 封と実物の食い違い

- 封は「既存試験の赤は試作で六十五」とした。実物の既存試験の赤(直す前)の本数と一覧は第六節のとおりで、種類は封の四つの中だけ。封の門自身(`test_xbrl_p26_seal.py`)は、封が約束した宣言(`ENGINE_TRANSITIONS`・`LATER_FINGERPRINT`・`LATER_FROZEN`)を足し、登録簿の理由の数を留める二つの字(`test_16` が持つ数)を段 1 の後の数に書き換えた。封の引用や予測の字には触れていない。
- 封の限界の文は G3 の代価を『試作で注入の止め百六十五』と書いた。この実行の実測は第五節の文のとおり(封の数と違う)。封の文は直していない(日付つきの追記はこの文書がする)。
- 封の §4 の列挙に `extract.py` の遷移が無かった(`point_prior_result` と `ritual_result` は `adapters` 全体を見る)。足した。
- 封の §4 の列挙の `test_mutations` は、mutation の木が試験 file を写して走らせるため、`test_vocabulary` などの一覧を直した結果で緑に戻った。`mutations.json` 自体は変えていない。

## 11. 限界

- 手元の cache の六十七書類(経営分析の文を持つ)。規則はこの六十七書類を読んで作った(試作二回)。無作為ではない。六十七書類での「違う」の減りは、新しい標本での減りを意味しない。
- Q-2 の読みは実装席のエージェントで、人間ではない。読みの中身は門で縛れない。境界の六行は読み手で動く。
- G3 は GROUNDED を作らない代わりに、一単位の書き誤りを「要確認」に出す。G4 は同じ形の正しい結びも外しうる。G1 の前置きの許す字四つと G4 の形は六十七書類の字で決めた。
- 数の読み取り(G5)は円以外の単位を読まない。
- 「違う」に残る正しい文の主因(区分の取り違えの疑い・向きの語の残り)はこの封では直らない。
- 変異の表は手で走らせた記録の写しで、門が縛るのは写しだけ。

## 12. 迷った点

- Q-2b(一致から外れた行)の読みの語は封に無い。『偶然の一致』『正しい結びを失った』『分からない』の三語を実装席が決め、行ごとに根拠を付けた。
- 旗一つずつの測定は、engine に旗ごとの profile を登録せず、measure の中で一時的に `V.PROFILES` へ足した(封の『登録は P26 だけ』に従う)。
- 変異で黙った二件(M5・M23)は、試験を直して再実測した(結果は第九節)。直したのは試験で、engine ではない。

- この門自身の変異: 試験の中に、壊した記録で赤になることを確かめる試験が三十本ある(`MutationTest`)。別に、門の判定の分岐を手で外した二十二通り(幅の片側・条件の一つ・検査の一行)を使い捨ての木で走らせ、黙ったのは五通りだった(GROUNDED から外れた数の幅・儀式で結果が違う行の検査・P25 の書類別の突き合わせ・文書の変異の表の写し・provenance の Recipe の数)。うち四通りは、その検査だけが見つける試験を足して赤にした。残る一通り(文書の変異の表の写しの検査)は、表が文書に無いと散文の数字の検査が先に赤くなるので、外しても赤になる(重なる検査)。この二十二通りの結果は記録に写していない(手で走らせた)。

## 13. 再現

```
cd audit-core
python3 measure/xbrl_p26_2026-10-21.py --stage all --readings <読みの JSON> --mutations <変異の表の JSON> --existing-red <赤の一覧の JSON> --out fixtures/xbrl/p26_2026-10-21.json --jobs 6
python3 -m pytest -q tests/measure/test_xbrl_p26_result.py
AUDIT_CORE_P26=1 python3 -m pytest -q tests/measure/test_xbrl_p26_result.py     # 全部の走らせ直し(約 二十分)
```

記録の所要秒: {"Q1 Q2": 17.4, "Q3": 161.7, "Q4": 161.3, "Q5": 579.2, "Q7": 33.6, "全体": 1019.2, "旗ごと": 58.1}。
