# 丸めの帯を片側にする P23 ― 段 1 の結果(2026-10-21)

封: `docs/XBRL_ROUNDING_SEAL_2026-10-21.md`(commit `5008985`。**本文と予測は一字も直していない**。外れは外れとして残す)。
記録: `fixtures/xbrl/rounding_2026-10-21.json`(`measure/xbrl_rounding_2026-10-21.py --stage all --run-tests` の出力)。
門: `tests/measure/test_xbrl_rounding_result.py`(表と数のある文を記録から作った字で縛り、それ以外の散文に算用数字が在れば赤にする。散文は漢数字で書く)。
**0 USD・通信なし。engine の直しは人間の事前承認(2026-10-21)の範囲。既定は P22 のまま(段 1)。**

**予測 機械判定 当たり 5 / 外れ 1**(R-1〜R-6。R-7 は段 2 なので判定しない)。
engine の直し: `adapters/xbrl/vocabulary.py` 挿入 7・削除 1、`adapters/xbrl/comparators.py` 挿入 0・削除 0、`adapters/xbrl/recipes.py` 挿入 11・削除 3、`core/` 0 行。

## 1. 予測と実測

| # | 封の予測 | 実測 | 判定 |
|---|---|---|---|
| **R-1** | 儀式 240 件を P23 で: 通した **2〜3 / 240**(P22 の 15 から。残るのは退化値 N096 と N069 = 率の差 0.0502 が ±0.06 の中)、止めた **237〜238**。N237・N277(負の金額の符号つき切り捨て)は止まる | 通した 2 / 240(N069・N096)・止めた 238 / 240・その他 0。N237・N277 の結果 {"N237": ["detected:VALUE_MISMATCH"], "N277": ["detected:VALUE_MISMATCH"]}。対照 P22 の通した 15 / 240 | **当たり** |
| **R-2** | 67 書類の無改変で P22 → P23 で GROUNDED を離れる行 **6〜12**、うち金額 **0**、全部 率(％・ポイント)。新 GROUNDED **0**。書類ごとの丸め方の判定(R/T)は 67 書類で **1 つも変わらない** | 67 書類(実数 67)の無改変で動いた行 8・GROUNDED を離れた 8(率 8・金額 0、単位別 {"%": 7, "ポイント": 1})・新 GROUNDED 0・参照先だけ動いた 0・丸めの判定が変わった書類 0(丸め方が変わった 0) | **当たり** |
| **R-3** | 穴 B の 485 件(前期の値への置き換え)を P23 で通す **0〜2 / 485**(P22 の 1 から) | 通した 0 / 485・止めた 483・その他 2。対照 P22 の通した 1 | **当たり** |
| **R-4** | 無改変の VALUE_MISMATCH 1,410(P22)は **1,416〜1,422** に(R-2 の行が移る) | 無改変の VALUE_MISMATCH P22 1,410 → P23 1,418(差 8) | **当たり** |
| **R-5** | 段 2 の材料(192 行)の Core 自身は **1 行も動かない**(注入は最小の桁でなく型 T1〜T7) | 段 2 の材料 192 行の Core 自身 P22 → P23 で動いた行 0(対照: P22 の再計算が期を縛る P22 の記録と違った行 0) | **当たり** |
| **R-6** | engine の差分 `vocabulary.py` **≤ 20 行**、`comparators.py` **≤ 10 行**、`recipes.py` **≤ 10 行**(旗の受け渡しだけ)、`core/` 0 行。旗が偽なら 1 行も変わらない(P22 明示の数は不変)。登録の一覧の試験 4 か所に P23 を足す以外の既存試験は全部緑 | vocabulary.py 挿入 7・削除 1、comparators.py 挿入 0・削除 0、recipes.py 挿入 11・削除 3、core/ 0 行。既存試験 python3 -m pytest -q tests/adapters/xbrl → 860 passed, 1 skipped in 1152.35s (0:19:12)。4 か所のほかに直した既存試験 3 | **外れ** |
| **R-7** | 段 2(既定の切り替えは P24・P25 とまとめて人間に諮る): 儀式を既定で走らせ直して README の数を置き換え(通した 2〜3 / 240 が先頭に)、pin と既定の試験の遷移で全緑 | 段 2(既定 P22 → P23。P24・P25 とまとめて)は人間の承認の後。この実行では何も変えていない(DEFAULT_PROFILE = P22) | **判定しない(段 2)** |

R-6 は外れ。外れ方は二つ。(一)recipes.py の挿入が予測の幅を一行超えた。(二)封の「登録の一覧の試験 四か所」のほかに、既存試験を三本直す必要があった(率の旗を持つ profile の一覧、period_bind を持つ profile の一覧、除外の一覧)。どれも P23 を足しただけの一行の直しで、既存の挙動を縛る assert は一つも緩めていない。直した試験:

| 4 か所のほかに直した既存試験 |
|---|
| tests/adapters/xbrl/test_p17.py::PctToleranceTest::test_p18_is_p17_plus_the_tolerance_flag(率の旗 pct_tolerance_from_decimals を持つ profile の一覧に P23 を足した。P23 は P18 の旗を積む) |
| tests/adapters/xbrl/test_recipes_p22.py::FlagShapeTest::test_only_p22_has_the_flag_on(period_bind を持つ profile の一覧を [P22] から [P22, P23] に。P23 は P22 から作る) |
| tests/adapters/xbrl/test_recipes_p22.py::WithoutCueTest::test_every_profile_before_p22_keeps_grounding_the_prior_fact(除外を P22 のみから P22・P23 に。P23 は period_bind を引き継ぐ) |

## 2. R-1 儀式(同梱の一書類、注入二百四十件)

儀式 240 件を P23 で回すと、通した 2 / 240 = 0.8%・止めた 238 / 240 = 99.2%(P22 は通した 15 / 240 = 6.2%)。P22 で通した 15 件のうち P23 で止まったのは 13(率 11・金額ほか 2)。N237・N277 は止まった。
P23 でも通した id: N069・N096。

| 儀式 240 件 | 通した | 止めた | その他 |
|---|---:|---:|---:|
| P22(対照。いまの既定) | 15 | 225 | 0 |
| **P23** | **2** | **238** | **0** |

P22 で通っていた十五件と P23 の結果(通した行だけを載せる):

| id | 型 | 元の字 → 後の字 | 単位 | P22 | P23 |
|---|---|---|---|---|---|
| N011 | V2 | 61.7% → 61.8% | % | PASSED | **detected:VALUE_MISMATCH** |
| N017 | V2 | 2.9% → 2.8% | % | PASSED | **detected:VALUE_MISMATCH** |
| N031 | V2 | 7.1% → 7.2% | % | PASSED | **detected:VALUE_MISMATCH** |
| N033 | V2 | 67.5% → 67.6% | % | PASSED | **detected:VALUE_MISMATCH** |
| N037 | V2 | 29.8% → 29.9% | % | PASSED | **detected:VALUE_MISMATCH** |
| N045 | V2 | 6.1% → 6.2% | % | PASSED | **detected:VALUE_MISMATCH** |
| N069 | V2 | 3.8% → 3.9% | % | PASSED | **PASSED** |
| N096 | V1 | 0百万円 → 00百万円 | 円 | PASSED | **PASSED** |
| N113 | V2 | 13.3% → 13.4% | % | PASSED | **detected:VALUE_MISMATCH** |
| N131 | V2 | 8.9% → 8.8% | % | PASSED | **detected:VALUE_MISMATCH** |
| N177 | V2 | 6.1% → 6.2% | % | PASSED | **detected:VALUE_MISMATCH** |
| N225 | V2 | 10.8% → 10.9% | % | PASSED | **detected:VALUE_MISMATCH** |
| N237 | V2 | △22百万円 → △23百万円 | 円 | PASSED | **detected:VALUE_MISMATCH** |
| N251 | V2 | 61.7% → 61.8% | % | PASSED | **detected:VALUE_MISMATCH** |
| N277 | V2 | △780百万円 → △781百万円 | 円 | PASSED | **detected:VALUE_MISMATCH** |

P23 でも通した行の中身:

| id | 分類 | 値の差 | 1 最小単位 | 文脈 |
|---|---|---|---|---|
| N069 | 丸めの帯の中(±1 最小単位) | 0.10000000000000009 | 0.1 | 売上高営業利益率は前期の7.3%から3.8%へと3.5ポイント低 |
| N096 | 退化値(字は変わるが値が変わらない) | 0.0 | None | で、内訳は関係会社株式売却損6百万円および減損損失0百万円です。 |

人の読み: N237・N277(負の金額に対する符号つきの切り捨て)は、旗 `truncate_abs_band` だけで止まった(封 §0 では率の旗だけを積むと通っていた二件)。率の旗だけで止まるのは率十二件。N125・N199 は P22 の `period_bind` で止まっている。残った N069 は差が一つの最小単位の中で、率の帯 `±0.06` の内側に収まる(封 §3 に書いた限界のとおり、差が `0.05` から `0.06` の注入は通る)。N096 は `0` を `00` と書く退化値で、値が変わらないので帯では止まらない(注入道具の欠陥、封 §3)。

## 3. R-2 無改変の六十七書類

67 書類(claim 7,799)の無改変で、P22 から P23 に動いた行は 8。全部 GROUNDED → VALUE_MISMATCH で、率 8(% 7・ポイント 1)・金額ほか 0。新 GROUNDED 0。書類 6 に散る。
書類ごとの丸め方の判定(R・T・丸め方)が P22 と P23 で変わった書類は 0(書類 67 のうち切り捨て 20)。

| 項目 | 件数 |
|---|---:|
| 動いた行(全 state) | 8 |
| GROUNDED を離れた | 8 |
| うち 率(％・ポイント) | 8 |
| うち 金額ほか | 0 |
| 単位別 | % 7・ポイント 1 |
| 新 GROUNDED | 0 |
| GROUNDED のまま参照先だけ動いた | 0 |
| 離れた行のある書類 | 6 |
| 丸めの判定(R・T・丸め方)が変わった書類 | 0 |
| 書類 | 67 |
| claim の総数 | 7,799 |

動いた行の全部(抜粋・生の値・文の値):

| doc | id | 単位 | 文の値 | P22 の生の値(recomputed) | 差(絶対値) | 向き | 文の抜粋 |
|---|---|---|---|---|---|---|---|
| S100YMFV | N066 | ポイント | 2.9 | 3.0 | 0.10 | GROUNDED → VALUE_MISMATCH | あり、当連結会計年度末の自己資本比率は、前連結会計年度末から2.9ポイント増加し52.5%とな |
| S100YUHC | N015 | % | -18.1 | -18.02 | 0.08 | GROUNDED → VALUE_MISMATCH | .9%減、2億16百万円減)、経常利益は13億51百万円(同 18.1%減、2億97百万円減 |
| S100YUHC | N050 | % | 229.1 | 229.03 | 0.07 | GROUNDED → VALUE_MISMATCH | 以上の結果、アセット事業の売上高は2億4百万円(前年同期比 229.1%増、1億42百万円増 |
| S100YYVN | N011 | % | 2.6 | 2.71 | 0.11 | GROUNDED → VALUE_MISMATCH | ザイン ビジネスの売上も寄与したことなどから、売上高は前期比2.6%増の392億60百万 |
| S100Z1WR | N013 | % | 43.9 | 43.97 | 0.07 | GROUNDED → VALUE_MISMATCH | 年同期比4.6%増)、営業利益は4,610百万円(前年同期比43.9%増)、経常利益は4, |
| S100Z3HP | N010 | % | 100.1 | 100.2 | 0.10 | GROUNDED → VALUE_MISMATCH | 果、営業利益は同103.1%の12億74百万円、経常利益は同100.1%の15億29百万円、 |
| S100Z3HP | N012 | % | 102.8 | 102.73 | 0.07 | GROUNDED → VALUE_MISMATCH | 、経常利益は同100.1%の15億29百万円、当期純利益は同102.8%の10億55百万円と |
| S100Z3IZ | N080 | % | 539.7 | 539.79 | 0.09 | GROUNDED → VALUE_MISMATCH | 費用は、譲渡制限付株式関連費用の増加等により、43百万円(同539.7%増)となりました。 |

人の読み: 動いた行は全部、文の値と生の値の差が `0.06` より大きく `0.15` 以下の率で、P22 の帯 `±0.15` では通り、P23 の帯 `±0.06`(一桁)では通らなくなった行である。文の字は、生の値を一桁に四捨五入した字とは最後の桁で一つ違う。これは封 §3 が代価として残した型(提出者が表示の桁の金額から率を出した型の疑い)に当たるが、元の金額から出し直して確かめてはいない(未測定)。金額の行は一つも動いていない。

### 3-1. 旗 `truncate_abs_band` だけを積んだ場合(R-2 の補助)

旗 `truncate_abs_band` だけを P22 に積むと、67 書類で動く行は 0。旗が効きうる行(切り捨てと判定された 20 書類で負の fact に GROUNDED した金額の claim)は 209(20 書類)。

| 旗 truncate_abs_band だけを P22 に積む(R-2b) | 件数 |
|---|---:|
| 動いた行 | 0 |
| 切り捨てと判定された書類 | 20 |
| 旗が効きうる行のある書類 | 20 |
| うち札 abs+truncate | 197 |
| うち札 truncate(CF 流量項目。札は abs を落とした梯子で付く) | 12 |
| 負の fact に GROUNDED(切り捨ての書類の金額) | 209 |

読み: 金額で動く行が零なのは、旗が効きうる行が無いからではない。切り捨てと判定された書類に、負の fact に GROUNDED した金額の claim が在る。その中で札が `abs+truncate` の行は絶対値で説明できた正しい文で、旗の有無で結果が変わらない。CF 流量項目の札は abs を落とした梯子で付くので `truncate` と出るが、両辺が非負なので同じである(M-8・M-9 参照)。旗が止めるのは「文の絶対値が fact の絶対値より大きい」誤りで、六十七書類の実物の文にはそれが無い。旗が効くことは儀式の N237・N277 と `tests/adapters/xbrl/test_recipes_p23.py` が示す。

## 4. R-3 穴 B(前期の値への置き換え)

穴 B の注入 485 件を P23 で再検証すると、通した 0 / 485 = 0.0%・止めた 483 / 485 = 99.6%・その他 2 / 485 = 0.4%(P22 は通した 1 / 485 = 0.2%)。

| 書類 | id | 元の字 → 後の字 | 当期の fact | 前期の fact | P22 | P23 |
|---|---|---|---|---|---|---|
| S100YXLE | N081 | 89.4% → 89.5% | 0.894 | 0.895 | 通した(参照先が当期の同じ参照先のまま) | 止めた |

| 穴 B の注入 485 件 | 通した | 止めた | その他 |
|---|---:|---:|---:|
| P22(対照) | 1 | 482 | 2 |
| **P23** | **0** | **483** | **2** |

P22 で通っていた一件(率 `89.4` を `89.5` に)は P23 で止まった。

## 5. R-4 無改変の VALUE_MISMATCH

無改変の VALUE_MISMATCH は P22 が 1,410、P23 が 1,418(差 8)。GROUNDED は 4,242 から 4,234。

| 無改変 67 書類 | GROUNDED | VALUE_MISMATCH |
|---|---:|---:|
| P22 | 4,242 | 1,410 |
| **P23** | **4,234** | **1,418** |

増えた分は R-2 の動いた行と同じである。

## 6. R-5 段 2 の材料の Core 自身

段 2 の材料 192 行(注入 64)の Core 自身は、P22 から P23 で動いた行が 0。対照の P22 の再計算は期を縛る P22 の記録と全行一致(違った行 0)。

| 段 2 の材料 192 行の Core 自身 | 件数 |
|---|---:|
| 行 | 192 |
| 注入 | 64 |
| P22 → P23 で動いた行 | 0 |
| 注入で Core 自身 P22 が GROUNDED | 0 |
| 注入で Core 自身 P23 が GROUNDED | 0 |
| 対照: P22 の再計算が期を縛る P22 の記録と違った行 | 0 |

## 7. R-6 engine の差分と既存試験

| file | 挿入 | 削除 |
|---|---:|---:|
| `adapters/xbrl/vocabulary.py` | 7 | 1 |
| `adapters/xbrl/comparators.py` | 0 | 0 |
| `adapters/xbrl/recipes.py` | 11 | 3 |
| `core/` | 0 | |

既存試験: python3 -m pytest -q tests/adapters/xbrl → 860 passed, 1 skipped in 1152.35s (0:19:12)。封の 4 か所のほかに直した既存試験は 3 本。

comparators.py は零行。封 §1 の「写しの帯」を comparators.py の変更として数えたのは実物と食い違っていた: 切り捨ての帯を絶対値で当てる枝は P19 のときに `vocabulary.match_value` と `comparators._match_value` の両方へ既に入っていて、検証時の照合へは `params["magnitude_truncate"]` で届く。足りなかったのは「旗を渡す側」だけである。そこで recipes.py に `_mag_trunc(profile, rounding)` を足し、三か所の呼び出し(`_direct_value_claim`・`_dispatch_num_claim`・向きの語の金額の照合)を置き換えた。`_mag_trunc` は P19 の旗を従来どおり返し、P23 の旗は書類の丸め方が切り捨てと決まった二周目(`rounding == "truncate"`)だけ真にする。一周目は `decide_rounding` が根拠を数える軸なので P22 のまま(これが P19 の旗を積まない理由の裏返し)。

旗が偽なら一行も変わらないことは、P22 の再計算が儀式の記録(二百四十行)・期を縛る P22 の記録の穴 B(四百八十五行)・段 2 の材料(百九十二行)・無改変六十七書類の書類ごとの GROUNDED と全部一致したことで示した(門が記録同士を突き合わせる)。

## 8. engine の変異(手で走らせた)

| # | 変異 | 予測 | 実測 |
|---|---|---|---|
| M-1 | recipes.py の _mag_trunc が P23 の旗を無視する(truncate_on_magnitude だけ見る) | test_recipes_p23 が 3 本以上赤(P23 が止める・検証時に帯が載る・comparator が builder と一致)。test_p17・lineage は黙る | 赤 3 本(test_recipes_p23 の p23_stops_it_under_a_truncating_document・p23_carries_the_band_to_the_verifier・the_comparator_agrees_with_the_builder)。test_p17・lineage は緑 ― 予測どおり |
| M-2 | recipes.py の _mag_trunc から rounding == "truncate" を外す(1 周目にも帯) | test_recipes_p23 が 2 本赤(first_pass_is_the_same_as_p22・rounding_evidence_axis) | 赤 3 本(first_pass_is_the_same_as_p22・a_rounding_document_is_untouched・no_subject_is_the_same_as_p22_down_to_reason_and_state)。**予測は外れ(予測した 2 本のうち rounding_evidence_axis は黙り、予測に無い 2 本が赤)。向きは予測どおり(1 周目の P22 との同一性を見る試験が赤)。rounding_evidence_axis が黙ったのは、その標本では根拠の行(差・桁)が旗の有無で変わらないため(根拠を数える側の守りは first_pass_is_the_same_as_p22 が持つ)** |
| M-3 | recipes.py の _mag_trunc が truncate_on_magnitude を無視する(P19 の旗を壊す) | test_recipes_p23 の 1 本(p19_still_stops_it_on_its_own_flag)だけ赤。test_p17 は黙る(match_value 直叩き) | 赤 1 本(p19_still_stops_it_on_its_own_flag)。test_p17 は緑 ― 予測どおり |
| M-4 | vocabulary.py の P23 から pct_tolerance_from_decimals=True を外す | test_recipes_p23 の FlagShape 1 本 + PercentTest 2 本が赤 | 赤 3 本(FlagShape の p23_is_p22_plus_exactly_the_two_flags・PercentTest の a_tenth_off_is_grounded_in_p22_and_stopped_in_p23・the_tolerance_is_the_p18_one)― 予測どおり |
| M-5 | vocabulary.py の P23 に truncate_on_magnitude=True を積む | FlagShape 2 本以上 + test_p17 の MagnitudeTruncateTest.test_p19_is_p18_plus_the_flag が赤 | 赤 6 本(FlagShape 2・NegativeAmountTruncation 2・PeriodBind 1・test_p17 1)― 予測どおり(幅の中) |
| M-6 | recipes.py の _direct_value_claim が match_value に mag_trunc を渡さない(False 固定) | test_recipes_p23 の 1〜2 本が赤。comparator 側の試験は緑のまま | 赤 2 本(p23_stops_it_under_a_truncating_document・p19_still_stops_it_on_its_own_flag)。comparator_agrees は緑 ― 予測どおり |
| M-7 | comparators.py の _match_value が magnitude_truncate を無視する(符号つきに戻す) | test_p17 の comparators 2 本 + test_recipes_p23 の comparator_agrees が赤。recipes 側の試験は緑 | 赤 3 本(test_p17 の the_two_copies_agree_on_a_grid・comparators_copy_takes_the_same_argument、test_recipes_p23 の the_comparator_agrees_with_the_builder)。test_lineage は緑 ― 予測どおり |
| M-8 | recipes.py の _dispatch_num_claim が _mag_trunc(profile, None) を使う(流量項目 _apply_flow_sign へ旗が届かない) | 赤 0 本(黙る。流量項目の試験が無い)→ 黙ったら理由を調べる | 赤 0 本 ― 予測どおり黙った。**等価な変異**: _apply_flow_sign は両辺を abs にしてから match_value を呼ぶので、非負どうしでは帯が符号つきでも絶対値でも同じ。等価を格子で留める試験(NonNegativeOperandsAreIndifferentTest)を足した |
| M-9 | recipes.py の _direction_amount_check への受け渡しを truncate_on_magnitude だけに戻す | 赤 0 本(黙る)→ 黙ったら理由を調べる | 赤 0 本 ― 予測どおり黙った。**等価な変異**: _direction_amount_check も両辺を abs にして match_value を呼ぶ(M-8 と同じ理由) |

engine の変異 9 通りは、コピー(作業木と別。scratchpad)の recipes.py・vocabulary.py・comparators.py に 1 つずつ入れ、同じ 6 file の試験(test_recipes_p23・test_p17・test_lineage・test_comparators・test_recipes_p22・test_recipes_p21)を走らせて、戻して byte 一致を確かめた。予測は実走の前に固定した(手で走らせた。この表は記録の写しを門が縛るだけで、変異そのものを毎回走らせてはいない)。

## 9. 限界

- 率の帯(一桁で `±0.06`)は、提出者が表示の桁の金額から率を出した型を落とす。代価として残す(封 §3)。差が `0.05` から `0.06` の注入は通る。
- 退化値(`0` を `00`)は注入道具の欠陥で、帯では止まらない。
- 前々期の値への置き換えは P23 でも通る(P22 の限界のまま)。
- 字の端数処理の方針は使わない(取れる書類が六十七のうち五)。P19 の `truncate_on_magnitude` は積まない(判定の軸も変わる)。
- 手元の cache の六十七書類は無作為ではない。別の書類では動く行が増えうる。
- 動いた行の正しさの読み(第三節)は人の読みで、門は縛っていない。

## 10. 再現

```
cd audit-core
python3 measure/xbrl_rounding_2026-10-21.py --stage all --run-tests        # 記録を書く(約 三十分。tests/adapters/xbrl の pytest を含む)
python3 measure/xbrl_rounding_2026-10-21.py --stage r3 --docs S100YXLE --out /path/to/r3.json   # 軽い走らせ直し
python3 -m pytest -q tests/measure/test_xbrl_rounding_result.py             # 門
AUDIT_CORE_ROUNDING=1 python3 -m pytest -q tests/measure/test_xbrl_rounding_result.py   # 全部の走らせ直し
```

## 11. 次

- 段 2(既定 P22 から P23 への切り替え)は **P24・P25 とまとめて**、この結果を人間に見せてから(R-7 は判定しない)。
- `test_xbrl_axis3_decision.py` の `LATER_ENGINE_COMMITS` への段 1 の engine commit の宣言は、commit の後の次の便。
- 独立監査(`step-auditor`)の GO を経てから commit する。
- 残る HUMAN: `verify_document.py` の docstring「既定 P20」(engine のため触っていない)。

記録の所要秒: {"R1": 37.7, "R2": 56.7, "R2b": 80.1, "R3": 174.4, "R5": 10.6, "R6": 1152.6, "全体": 1519.8}。

## 12. 追記(2026-10-21、独立監査 GO の軽い指摘)

- 儀式の素の書類で P22 から P23 へ動いた claim は、第二節の儀式の表とも六十七書類の八行とも別に一件ある: `N054`(「役員株式報酬引当金繰入額は`△28百万円`」)。state は UNVERIFIABLE のままで、reason が `ambiguous(elements)` から `no_subject` に変わる。主語なしの負の金額で、符号つきの切り捨ての帯では候補の要素の二つの家族に一致していたのが、絶対値の帯で一つの家族に絞れ、案ア(主語なし)に落ちる。旗 `truncate_abs_band` だけを積んでも同じ動き(率の旗だけでは動かない、監査の席の手元)。新 GROUNDED は零。この型(主語なし・負の値・理由名の変化)を直接見る試験は無い。
