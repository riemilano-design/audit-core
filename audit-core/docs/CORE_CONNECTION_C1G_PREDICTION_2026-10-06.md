# Core 接続 C-1g(Adapter の意味の層の直し 4 つ、profile P6)の予測 ― 実装の前に封じる

**日付**: 2026-10-06 **人間の決定**: CF 流量項目は **b**(要素名の規約で符号を読む。2026-10-06)、C-1g は 4 項目を 1 つに束ねて予測を先に封じる **前提**: 3 社目の結果 `814ce44`・追記 `146d0ca`(2 社の false pass = 値 0・証拠 2・抽出 2) **封の手順**: この文書をコミットしてから書く。後から書き換えない。1 回目の計測は司令塔が凍結時点で回す。

## 1. 直す物(全部 Adapter。Core は 1 行も触らない = 門)

新しい profile **P6** を足す(P1・P5F は凍結のまま。224 件の既存の門は P1/P5F で緑のまま)。P6 = P5F + 次の 4 つ。

| # | 直し | 中身 |
|---|---|---|
| 1 | **語彙 7 行**(P6 の先頭に) | 流動負債 → CurrentLiabilities / 固定負債 → NoncurrentLiabilities / 投資有価証券の取得による支出 → PurchaseOfInvestmentSecurities / 1年内返済予定の長期借入金 → CurrentPortionOfLongTermLoansPayable・CurrentPortionOfLongTermBorrowings / 持分法による投資利益(と 投資損益) → ShareOfProfitOfEntitiesAccountedForUsingEquityMethod・ShareOfProfitLossOfEntitiesAccountedForUsingEquityMethod・EquityInEarningsOfAffiliates / ROE → RateOfReturnOnEquity / 退職給付に係る負債 → RetirementBenefitLiability |
| 2 | **CF 流量項目の符号の規約(b)** | 要素の局所名が `DecreaseIncreaseIn…` なら 正 = 減少(規約 −1)、`IncreaseDecreaseIn…`(`NetIncreaseDecreaseIn…` 含む)なら 正 = 増加(規約 +1)。**数の Claim**: 主語と数の間、または数の直後に 増加額/減少額/増加/減少 があれば claim の向き ±1 を取り、`equals_within` の params に `flow_convention`・`claim_direction` を入れる。比較子は梯子を **abs 無しの値**でなく「|fact| と |claim| の梯子」+「sign(fact) × 規約 == claim の向き」の両方で一致。normalization の札は abs を落とした梯子の札(round / truncate)。向きの語が無ければ従来どおり(abs)。**文章の Claim**: 主語が流量項目なら pointer は当期 1 本 + `builtin:flow_sign(cur)==direction`(新しい比較子、evidence は cur だけ、match = sign(cur) × 規約 == direction、差 0 は不一致、recomputed = cur) |
| 3 | **ポイント差の form** | 単位 ポイント で、数の手前 25 字に 前期比|前連結会計年度|前年 があれば derived_value: pointers [比率の当期, 比率の前期, `formula:a-b`]、比較子 `diff(a-b)(pure*100)`(新)= (a − b) × 100 と claim.value(符号つき)の差 ≤ 0.15、recomputed = round((a−b)×100, 2)。前期の語が無ければ `not_found_reason = "no_element(point without prior phrase)"`(新しい理由、POINTER_NOT_FOUND) |
| 4 | **member の分母を事業 member に** | 分母 = 連結 Duration context の explicitMember のうち **会社拡張の名前空間**(接頭辞が jppfs_cor・jpcrp_cor・jpigp_cor 等の標準でない)のもの。凍結の `member_denominator` は系譜の試験のために残し、P6 だけ新しい関数を使う |

登録簿: 比較子 +2・理由 +1 → **24**(scheme 3 不変)。Core の変更 **0**、インターフェース拡張 0。

## 2. 期待値の扱い(規則)

v1(`core_expectation_1B.json`・`_5F.json`)は **1 byte も変えない**。P1・P5F の門(前段照合・計器 3)は v1 のまま緑。P6 で 3 書類を回した結果は、§3 の **ID 単位の予測**と照合する。予測した差の集合と実測の差の集合が一致したときだけ、`core_expectation_1B_v2.json`(P6)と `core_expectation_3rd_v1.json`(S100YMFV、P6、140 件)を **人間の承認の後に**新設し、計器 3b とする。一致しなければ止まって差を表にする。

## 3. 予測(司令塔の席、ID 単位。既知の fact から導いた。直す前に書いた)

### 3.1 1 社目 S100Z4Q1(P6 vs v1、91 件)― 動くのは **5 件**、他 86 件は state・pointers・recomputed・normalization 不変

| ID | 文 | 今(v1) | P6 の予測 | 根拠 |
|---|---|---|---|---|
| N030 | 業務未払金の減少 3 億円 | G、abs+round | **G、round**(規約: IncreaseDecrease、cur −300,297,000 = 減少、向き 減少 → 一致) | fact |
| N048 | 売上債権の増加額 8 億 2 百万円 | G、abs+truncate | **G、truncate**(DecreaseIncrease、cur −802,686,000 = 増加) | fact |
| N050 | 仕入債務の減少額 3 億円 | G、abs+round | **G、round** | fact |
| T026 | 売上債権 増加 | **VM** | **G**(pointers = cur 1 本 + flow_sign。−802M × (−1) = +1 == 増加) | 取りこぼしが直る |
| T028 | 仕入債務 減少 | G(偶然) | **G**(pointers が cur 1 本 + flow_sign に変わる。−300M × (+1) = −1 == 減少) | 証拠の層 false pass が消える |
| N028 | 完成業務補償引当金の増加 7 億 8 千 6 百万円 | G、round | **不変**(会社拡張の IncreaseDecrease…、cur +786M = 増加 → 一致、札は round のまま) | ― |
| N042 | (資金)2 億 9 千 3 百万円減少 | G、abs+round、主語 None | **不変**(主語が無いので規約を当てない) | ― |

state の集計: G 71 → **72**、VM 6 → **5**、PNF 7・UNV 7 不変。

### 3.2 2 社目 S100Z4B6(P6 vs v1、133 件)― 動くのは **0 件**

N065(短期借入金の増減、主語 None)は規約を当てない。語彙 7 行の語は 2 社目の MD&A に無い(前段照合で主語に現れていない)。member の分母は **19 → 5**(事業 member 5 は会社拡張 `jpcrp030000-asr_E05055-000:…`)、束縛は不変。

### 3.3 3 社目 S100YMFV(P6 vs P5F の結果 `814ce44`、140 件)― 動くのは **17 件**

| ID | 文 | P5F | P6 の予測 | 根拠 |
|---|---|---|---|---|
| N019 | 持分法による投資利益 46 百万円 | UNV ambiguous | **PNF no_element** | 連結 plain context に P/L の持分法損益の fact が無い(OCI と社数だけ) |
| N020 | 同 前期比 44.0% 減 | UNV no_subject | **PNF no_element** | 同上 |
| N046 | 投資有価証券の取得による支出 143 百万円 | VM(残高に束縛) | **G、abs+truncate**(PurchaseOfInvestmentSecuritiesInvCF cur −143,940,000) | fact |
| N058 | 流動負債 56 百万円増加 | VM | **G、derived diff(a−b)、truncate**(1,832,856 − 1,776,652 = 56,204 千円) | fact |
| N059 | 流動負債 1,832 百万円 | VM | **G、truncate** | fact |
| N060 | 固定負債 144 百万円減少 | VM | **G、derived、abs+truncate**(1,232,728 − 1,377,036 = −144,308) | fact |
| N061 | 固定負債 1,232 百万円 | VM | **G、truncate** | fact |
| N066 | 自己資本比率 2.9 ポイント増加 | VM(比率と直接比較) | **G、derived diff(pure*100)**((0.525 − 0.495) × 100 = 3.0、差 0.1 ≤ 0.15) | fact |
| N085 | ROE 7.3% | UNV no_subject | **G**(0.073 × 100) | fact |
| N086 | ROE 前期比 1.2 ポイント増 | UNV | **G**((0.073 − 0.061) × 100 = 1.2) | fact |
| N087 | 目標値であった 8.6% | UNV | **VM**(主語 ROE が付いて 7.3 と比べる。**文は目標値で事実の主張ではない** = 語彙を足したことで生じる安全側の誤り。「目標値」の規則はこの段では入れない) | 設計の帰結 |
| N088 | 目標値と比べて 1.3 ポイント下回り | UNV | **PNF no_element(point without prior phrase)** | 前期の語なし |
| T021 | 売上債権の減少額 61 百万円**等の増加**(資金の増加) | G(偶然) | **VM**(flow_sign: +61M × (−1) = 減少 ≠ 増加。語 増加 は資金のもの) | 偶然の G が消える(安全側) |
| T023 | 売上債権の減少額 | VM | **G**(−1 == 減少) | 取りこぼしが直る |
| T036 | 流動負債 増加 | VM | **G**(CurrentLiabilities +56M) | fact |
| T037 | 1 年内返済予定の長期借入金 増加 | VM | **G**(435.9 → 473.0) | fact |
| T040 | 退職給付に係る負債 増加 | VM | **PNF no_element**(連結 plain context に RetirementBenefitLiability 無し) | fact |
| T039 | 固定負債 144 百万円減少 | G(負債合計の偶然) | **G**(pointers が NoncurrentLiabilities に変わる) | 証拠が正しくなる(state 不変・pointers 変) |
| N043 | 売上債権の減少額 61 百万円 | G、round | **不変**(+61.27M = 減少、向き 減少 → 一致。札 round) | ― |
| T025 | 投資有価証券の取得による支出 143 百万円等の**減少**(資金) | VM | **VM のまま**(流量規約の対象外。cur − prior = +76M ≠ 減少) | ― |

state の集計: **G 61 → 71、VM 11 → 3(T021・N087・T025)、PNF 16 → 20、UNV 52 → 46**。state が動く 17 件 + pointers だけ動く 1 件(T039)= 18 件。他 122 件は不変。member の分母 **12 → 0**。

### 3.4 その他

| # | 項目 | 予測 |
|---|---|---|
| a | Core 4 本の sha / v1 期待値 2 本 / 原本 4 本 | 不変(門) |
| b | P1・P5F の門(前段照合 224・計器 3 の 224・計器 5) | 緑のまま(門) |
| c | 登録 | 24(比較子 8・scheme 3・normalization 4・理由 10)。Core の変更 0・拡張 0 |
| d | 試験 | 新規 **25〜45 本**(flow 規約の単体 8〜12、ポイント差 4〜6、分母 3〜4、語彙 2〜3、P6 の 3 書類の ID 照合 3、系譜の不変 1〜2)。計画した試験ファイル数 4 × 10 で見積もった |
| e | 変異 | +6〜9 本(規約の符号を反転 → 1B T026/T028 と 3 社目 T021/T023 が返る = red、ポイント差の tolerance、分母の名前空間判定を外す → 2 社目 5 → 19 で red、語彙の行を 1 つ消す、green 2)。予測を先に |
| f | 行数 | +150〜300(vocabulary・extract・recipes・comparators・registry_setup・instance) |
| g | 2 社の記録の訂正 | member の分母 19 → 5(3 本目の結果に追記)。false pass の記録は 値 0・証拠 2 のまま(直したのは今後の判定で、過去の記録は変えない) |
| h | 1 回目の計測で予測と違う ID | **0〜2 件**(疑うのは、向きの語の検出範囲(25 字)と、流量項目の判定の正規表現が `Net…` と会社拡張を拾うか) |

## 4. 3 役と止まる所

実装担当(adapters/ と tests/ だけ、コミットしない。P1・P5F の挙動は 1 byte も変えない)→ 司令塔が凍結し **P6 で 3 書類を 1 回ずつ回して §3 と ID 単位で照合、結果を `fixtures/xbrl/c1g_first_run_{1B,5F,3rd}_P6.json` に保存** → 監査(変異を自作、v1 不変、Core 不変、P1/P5F 不変、§3 の差の集合と実測の集合の一致を独立に再現)→ GO でコミット → 結果文書 → 人間が §3 の差を読んで承認すれば v2/3rd の期待値を新設(別コミット)。
