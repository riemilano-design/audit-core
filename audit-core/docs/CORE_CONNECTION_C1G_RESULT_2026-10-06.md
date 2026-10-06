# Core 接続 C-1g(Adapter の意味の層の直し 4 つ、profile P6)の結果

**日付**: 2026-10-06 **予測の封**: [CORE_CONNECTION_C1G_PREDICTION_2026-10-06.md](CORE_CONNECTION_C1G_PREDICTION_2026-10-06.md)(`d0fe6e8`、sha `15dea394…`、不変) **監査**: GO(独立の監査。凍結 sha を 2 回照合、260/33 を再現、直し 4 つを逐語で確認、自作変異 5 本、1 回目 JSON 3 本を独立に再計算して司令塔の照合と一致) **コミット**: `3afd0ba`(Adapter + 試験 + 1 回目の計測 3 本)

## 1. 何を直したか(全部 `adapters/xbrl/`。Core 0 行)

| # | 直し | 実装(実装担当の報告と司令塔の読み) |
|---|---|---|
| 1 | 語彙 7 行 | `vocabulary.SUBJECTS_P6_EXTRA_7` を P6 の `subjects` の先頭に。P1・P5F の `Profile(...)` の呼び出し行は不変(新フラグ 3 つは既定 False) |
| 2 | CF 流量項目の符号の規約 b | `vocabulary.flow_convention(element_name)`: 局所名が `^(?:Net)?DecreaseIncreaseIn` → −1(正 = 減少)、`^(?:Net)?IncreaseDecreaseIn` → +1。数の Claim: `equals_within` が params `flow_convention`・`claim_direction` を受けたとき \|値\| の梯子 + 符号の一致で、札から abs が落ちる。文章の Claim: 新比較子 `builtin:flow_sign(cur)==direction`、pointer は cur 1 本 + builtin |
| 3 | ポイント差 | 数の手前 25 字に 前期比\|前連結会計年度\|前年 があれば derived: pointers [cur, prior, `formula:a-b(pure)`]、新比較子 `diff(a-b)(pure*100)`、tolerance 0.15。無ければ新理由 `no_element(point without prior phrase)`(POINTER_NOT_FOUND) |
| 4 | member の分母 | `instance.segment_member_denominator(contexts)`: 連結 Duration の explicitMember のうち会社拡張の名前空間だけ |

差分: `adapters/xbrl` 5 本 +321/−20(**正味 +301**)、試験 7 本 + 新規 `tests/golden/test_p6_smoke.py`(48 行)、`mutations.json` +7 本。`core/`・`fixtures/` の期待値 v1・原本・`docs/` は実装担当が触っていない(sha で確認)。

## 2. 門(司令塔が凍結時点で測った)

| 門 | 結果 |
|---|---|
| Core 4 本の sha | `9aea7f9e / a65e285c / 38ac65a5 / d29b21dc`(`f917f02` から不変) |
| v1 期待値 2 本・原本 4 本の sha | 不変(`f8a45ecc / a19f3419`、`896492a7 / 3d2092a9 / f25652f0 / 275ae50e`) |
| `unittest discover` | **Ran 260 OK**(219 + 新規 41) |
| 変異 | **33/33 が予測どおり**(既存 26 不変 + G-R1〜R5 red・G-G1/G-G2 green) |
| 前段照合 224・計器 3 の 224・計器 5・系譜 | 260 の中で緑(P1・P5F の挙動は不変) |
| 登録 | scheme 2 + 比較子 8 + normalization 4 + 理由 10 = **24**(C-1d と同じ数え方 = Adapter の登録だけ。`register_all` 後の登録簿は builtin と equals を含めて 3/9/4/10) |

## 3. 1 回目の計測(司令塔が凍結の後 17:53 に P6 で 1 回ずつ)

出力: `fixtures/xbrl/c1g_first_run_{1B,5F,3rd}_P6.json`(sha `e4b37952… / b942be06… / 7ea91a52…`)。基準: 1B・5F は v1 期待値(`--gate`)、3rd は `third_S100YMFV_P5F.json`。照合は state・pointers・recomputed・normalization の 4 欄、ID 単位。

### 3.1 1 社目 S100Z4Q1(91 件)― 予測 5 件、動いた 5 件、**ID 単位で完全一致**

| ID | 予測 | 実測 |
|---|---|---|
| N030 / N048 / N050 | 札から abs が消える | abs+round → round、abs+truncate → truncate、abs+round → round |
| T026 | VM → G、pointers が cur 1 本 | VM → G、pointers 3 → 2、recomputed −802,686,000 |
| T028 | G のまま、pointers が cur 1 本(証拠の層の false pass が消える) | G、pointers 3 → 2、recomputed −300,297,000 |

state 集計 G 72・VM 5・PNF 7・UNV 7。他 86 件は 4 欄とも不変。

### 3.2 2 社目 S100Z4B6(133 件)― 予測 0 件、動いた **0 件**。member の分母 **19 → 5**(予測どおり。5 つは `jpcrp030000-asr_E05055-000:*ReportableSegmentMember`)

### 3.3 3 社目 S100YMFV(140 件)― 予測 18 件、動いた **20 件**

| ID | 予測 | 実測 | 判定 |
|---|---|---|---|
| N046 N058 N059 N060 N061 N066 | VM → G | VM → G | 当たり(6) |
| N085 N086 | UNV → G | UNV → G(7.3、1.2) | 当たり(2) |
| N087 | UNV → VM(目標値 8.6% を ROE 7.3 と比べる安全側の誤り) | UNV → VM、recomputed 7.3 | 当たり |
| N088 | UNV → PNF `no_element(point without prior phrase)` | そのとおり | 当たり |
| T021 | G(偶然)→ VM | G → VM、pointers 3 → 2 | 当たり |
| T023 T036 T037 | VM → G | VM → G | 当たり(3) |
| T040 | VM → PNF no_element | そのとおり | 当たり |
| T039 | pointers だけ(負債 → 固定負債)、state G 不変 | pointers が NoncurrentLiabilities に、recomputed も変わる、G 不変 | 当たり(recomputed の変化は pointers の変化に伴う) |
| **N019 N020** | **UNV → PNF**(根拠: plain context に P/L の持分法損益の fact が無い) | **UNV → G**(`EquityInEarningsOfAffiliatesNOI` が plain context に在った。N019 46,069 千円 ≈ 46 百万円 round、N020 pct_change −43.96 ≈ −44.0%) | **外れ 2**(私の根拠が誤り。fact は在った。GROUNDED は本物で false pass ではない) |
| **T025** | VM のまま(「流量規約の対象外」と書いただけ) | VM のまま。**主語が 投資有価証券(残高)→ 投資有価証券の取得による支出 に乗り換え、pointers が PurchaseOfInvestmentSecuritiesInvCF に変わった** | **予測に無い変化 1**(語彙 7 行の効果を T025 まで追っていなかった) |
| **T052** | 書いていない(不変と見なしていた) | **UNV no_subject → PNF no_element**(ROE の文章 Claim「目標値を 1.3 ポイント下回り」。ROE が主語になり、文章用の cur/prior の対が無く PNF) | **予測に無い変化 1**(安全側) |

normalization の札: N058 は **round**(予測 truncate)、N060 は **abs+round**(予測 abs+truncate)。どちらも値は一致し state は予測どおりだが、梯子は round を先に試すので 56,204 千円 → 56 は round で止まる。**欄単位で外れ 2**。

state 集計: **G 73・VM 3・PNF 19・UNV 45**(予測 71 / 3 / 20 / 46)。VM 3 = T021・N087・T025 は予測どおり。G +2・PNF −1・UNV −1 のずれは N019/N020(PNF → G)と T052(UNV → PNF)で説明がつく。member の分母 **12 → 0**(予測どおり)。1B は 14 → 0(予測に書いていない)。

### 3.4 その他の予測との照合

| # | 予測 | 実測 | 判定 |
|---|---|---|---|
| a | Core・v1・原本 不変 | 不変 | 当たり |
| b | P1・P5F の門 緑 | 緑(260 の中) | 当たり |
| c | 登録 24・Core 0・拡張 0 | 24・0・0 | 当たり。ただし封じた行の内訳「比較子 8・scheme 3・normalization 4・理由 10」は和が 25 で字が合っていない(scheme に builtin を数えた)。数え方は C-1d の 21 と同じ(Adapter の登録だけ) |
| d | 試験 +25〜45 | **+41** | 当たり |
| e | 変異 +6〜9、green 2 | **+7**(red 5・green 2) | 当たり |
| f | 行数 +150〜300 | **+301**(正味) | **外れ**(1 行) |
| g | 分母 19 → 5 を 3 本目の結果に追記 | 追記した(§6) | ― |
| h | 1 回目で予測と違う ID 0〜2 | **4**(N019・N020・T025・T052)+ 欄単位で 2(N058・N060 の札) | **外れ**。疑っていた所(向きの語の窓・`Net…`)ではなく、**fact の有無の読み違い**と**語彙を足した波及先の追い漏れ**が原因 |

**集計**: 1B 5/5、5F 0/0、3rd 18 件中 16 当たり・2 外れ + 予測外 2、欄単位の外れ 2、3.4 の 8 項目中 6 当たり・2 外れ。**封じた予測は変えていない。実装を予測に寄せていない**(実装担当の報告 §3 も同じ。§5 の逸脱を参照)。

## 4. 手検査と false pass

- 1 社目 T028: pointers が cur 1 本になり、根拠の計算が文の意味と一致した。**証拠の層の false pass は P6 で消えた。** 記録(2 社で 値 0・証拠 2 = T025(5F)・T028(1B))は過去の判定の記録として変えない。
- 3 社目 T025: 主語が新語彙に乗り換えて正しい要素(PurchaseOfInvestmentSecuritiesInvCF)を指すようになったが、`PurchaseOf…` は規約 b の対象外(Decrease/Increase の名前を持たない)なので sign(cur−prior) で判定され VM のまま。文は「支出が減少」で正しい(cur −143.9M、prior −219.9M、支出の大きさは減った)。**取りこぼし(安全側)**。「支出」系の規約は C-1g の予測 §1 で「データが要求するまで広げない」とした範囲。次に直す物。
- N019・N020: GROUNDED は値(46 百万円・−44.0%)と証拠(持分法による投資利益の当期・前期)が一致している。false pass ではない。

## 5. 手順との差(記録)

1. **実装担当が凍結前に P6 を 3 書類で自分でも回した**(出力は scratchpad のみ、`fixtures/` には書いていない)。規則「1 回目は司令塔が凍結時点で回す」からの逸脱。実装担当は「予測に合わせて実装は調整していない」と報告。司令塔の公式の 1 回目(§3)は凍結の後に別に回し、両者の Claim 総数と state 集計は一致した。実装担当が見た結果と予測の差(G 73 vs 71 など)は、報告の中で「調整していない」と明記された。**次からは実装担当の指示に「P6 を実書類で回さない(試験の合成材料だけ)」を書く。**
2. `tests/golden/test_p6_smoke.py` の Claim 総数 91/133/140 は実装担当の非公式 run の数で書かれた(公式と一致)。§3 の ID 予測は書き写していない。
3. `fixtures/xbrl/run_core_path.py` の出力 JSON 先頭の `"registry"` 欄は `6/3/4/9` の直書きで、P6 の 24 を反映していない(計測の道具の欠陥。凍結中は直さず、別コミットで `register_all` 後の登録簿から数える形に直す)。1 回目の JSON 3 本はその古い欄のまま保存した(値は Claim の行に影響しない)。

### 5.4 監査の非ブロッキングの記録事項(3 点)

1. `flow_convention` の `(?:Net)?` を DecreaseIncreaseIn と IncreaseDecreaseIn の両方に対称に掛けている。封じた仕様は Net を IncreaseDecreaseIn 側にだけ明記。3 書類に `NetDecreaseIncrease…` の実例は 0 件(grep)で実害なし。
2. 語彙 7 行の「持分法による投資利益(と投資損益)」の括弧の読みが曖昧。実装は単一語だけ登録し N019 は正しく束縛された。仕様の意図は人間に確認してよい。
3. 向きの語の窓(数の直後 4 字)の定数を留める単体試験が無い。監査の自作変異 4→10・4→1 は単体試験・門・3 書類の Core 経由の再計算のどれでも差 0(等価)。**人が決めた数を字で留める試験が無い**ので将来の変化を検出できない(記憶 `pin-human-decided-numbers-literally` と同型)。次に足す。

## 6. 2 社の記録の訂正

- 3 本目の結果([XBRL_PROBE3_RESULT_2026-10-06.md](XBRL_PROBE3_RESULT_2026-10-06.md))に追記: member の分母 19 は株主資本等変動計算書の member と役員区分を含んでいた。事業 member は **5**(会社拡張の名前空間)。
- 3 社目の結果([CORE_CONNECTION_THIRD_RESULT_2026-10-06.md](CORE_CONNECTION_THIRD_RESULT_2026-10-06.md))に追記: 分母 12 → 0、XP-3rd-1〜4 が P6 でどう動いたか(§3.3)。

## 7. 次に直す物(この段では直していない。直すなら封じてから)

1. **「支出」系 CF 項目の規約**(`PurchaseOf…`・`RepaymentsOf…`・`PaymentsFor…`: 負で記録され、文の「減少」は大きさの減少)。3 社目 T025 が取りこぼし。
2. **目標値・計画値の Claim**(1 社目 N013「ROE 10% 以上を目標」、3 社目 N087「目標値 8.6%」): 手前に 目標|計画 の語があれば UNVERIFIABLE(理由 1 つ追加)。安全側の誤り 2 件が消える。
3. 文章 Claim の cur/prior の対が無いときの理由(T052 は `no_element` で、「文章用の対が無い」ことが読めない)。
4. `run_core_path.py` の `registry` 欄(§5.3)。
5. 向きの語の窓 4 字と前期の語の窓 25 字を字で留める試験(§5.4 の 3)。

## 8. 期待値 v2 / 3rd v1 の新設(人間の承認待ち)

規則(予測 §2)どおり、v1 は 1 byte も変えていない。§3 の差(1B 5 件・3rd 20 件)を人間が読んで承認すれば、`core_expectation_1B_v2.json`(P6)と `core_expectation_3rd_v1.json`(P6)を**別コミット**で新設し、計器 3b として P6 の門にする。承認までは `c1g_first_run_*_P6.json` が 1 回目の記録。
