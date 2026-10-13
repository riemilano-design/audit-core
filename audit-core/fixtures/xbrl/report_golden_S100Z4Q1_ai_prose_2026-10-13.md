# 検証の報告 ― jpcrp030000-asr-001_E36539-000_2026-06-30_01_2026-09-30.xbrl

- 道具: `adapters.xbrl.verify_document` / profile: `P16`
- 入力 ZIP の sha256: `0731a291f10af5dd207e05d54df8e2b5dc34e79a84de94af1c1a5d4e207228f6`(580,260 bytes)
- 文章の差し替え: あり(`{'element': 'jpcrp_cor:ManagementAnalysisOfFinancialPositionOperatingResultsAndCashFlowsTextBlock', 'member': 'XBRL/PublicDoc/jpcrp030000-asr-001_E36539-000_2026-06-30_01_2026-09-30.xbrl', 'text_sha256': '898ff5c54d94c746118cc997dd360c497702386b25d461924bbc4290edc26bbb', 'text_chars': 7084}`)
- engine の指紋: adapters `c413e10b4a5048e88b566ff7bb840cbd29debb394754e48cd753a6c70e4aba02` / core `34e836bb39762d5af831a9aa11d4ea095e73221beb5bd4510d3b234363a2a6e8` / git `a1c14017180bf6c33f0dd54f9fd6f2b8f379df02`

## 書類レベル

- 判定: **旗なし(書類レベルの UNVERIFIABLE には当たらない)**
- 主張の件数: **412**

| 状態 | 件数 | 割合 |
|---|---|---|
| 値が違う(VALUE_MISMATCH) | 25 | 6.1% |
| 根拠が見つからない(POINTER_NOT_FOUND) | 16 | 3.9% |
| 判定できない(UNVERIFIABLE) | 41 | 10.0% |
| 一致(GROUNDED) | 330 | 80.1% |

規則(字のまま): Claim 件数が 0 件の場合、書類レベルを UNVERIFIABLE とする。Claim 件数が 1 件以上の場合、GROUNDED 件数が 0 件、かつ POINTER_NOT_FOUND 件数 ÷ 全 Claim 件数が 0.5 を超える場合、書類レベルを UNVERIFIABLE とする。それ以外は、この規則によって UNVERIFIABLE とは判定しない。Claim 個別の state は変更しない。

凡例: 「文」は主張の周りの**抜粋(窓)**で全文ではない(語の途中で切れることがある)。「―」はその欄が**無い**状態(根拠が無い・理由が無い)、空欄は値が空。「理由」は判定を止めた状態(POINTER_NOT_FOUND・UNVERIFIABLE)にだけ付くので、VALUE_MISMATCH と GROUNDED の節では常に「―」になる。

## 値が違う(VALUE_MISMATCH) ― 25 件

根拠は見つかったが、文の値と根拠の値が違う。文の誤りか、結び先の誤りかは、この表では決めない。

| id | 主語 | 文の値 | 根拠から出た値 | 根拠(pointer) | 理由 | 文 |
|---|---|---|---|---|---|---|
| N039 | 従業員数 | 1,447 名 | 1,462 | xbrl:jpcrp_cor:NumberOfEmployees@CurrentYearInstant | ― | 当社グループの従業員数は1,462名(前期末1,447名)、臨時従業員は年間 |
| N040 | 従業員 | 409 名 | 1,462 | xbrl:jpcrp_cor:NumberOfEmployees@CurrentYearInstant | ― | 数は1,462名(前期末1,447名)、臨時従業員は年間平均409名(同393名)と人員 |
| N041 | 従業員 | 393 名 | 1,462 | xbrl:jpcrp_cor:NumberOfEmployees@CurrentYearInstant | ― | 2名(前期末1,447名)、臨時従業員は年間平均409名(同393名)と人員は着実に増加 |
| N080 | 不動産賃貸料 | 37,000,000 円 | 15,315,000 | xbrl:jppfs_cor:RealEstateRentNOI@CurrentYearDuration | ― | 20百万円)、不動産賃貸料15百万円(同15百万円)、その他37百万円(同35百万円)です |
| N081 | 不動産賃貸料 | 35,000,000 円 | 15,315,000 | xbrl:jppfs_cor:RealEstateRentNOI@CurrentYearDuration | ― | 不動産賃貸料15百万円(同15百万円)、その他37百万円(同35百万円)です。 |
| N120 | その他の包括利益 | 782,000,000 円 | 1,310,889,000 | xbrl:jppfs_cor:OtherComprehensiveIncome@CurrentYearDuration | ― | その他の包括利益は1,310百万円(前期528百万円)と782百万円増加しております。 |
| N124 | その他有価証券評価差額金 | 62,000,000 円 | 631,931,000 | xbrl:jppfs_cor:ValuationDifferenceOnAvailableForSaleSecurities@CurrentYearInstant | ― | 前期470百万円)、その他有価証券評価差額金217百万円(同62百万円)、為替換算調整勘定 |
| N144 | 流動資産 | 513,000,000 円 | 16,943,470,000 | xbrl:jppfs_cor:CurrentAssets@CurrentYearInstant | ― | - その他の流動資産:513百万円(同454百万円)、 |
| N145 | 流動資産 | 454,000,000 円 | 16,943,470,000 | xbrl:jppfs_cor:CurrentAssets@CurrentYearInstant | ― | - その他の流動資産:513百万円(同454百万円)、59百万円の増加 |
| N146 | 流動資産 | 59,000,000 円 | 16,943,470,000 | xbrl:jppfs_cor:CurrentAssets@CurrentYearInstant | ― | - その他の流動資産:513百万円(同454百万円)、59百万円の増加 |
| N173 | その他有価証券評価差額金 | 3,000,000 円 | 631,931,000 | xbrl:jppfs_cor:ValuationDifferenceOnAvailableForSaleSecurities@CurrentYearInstant | ― | 万円から631百万円へ増加)および一部銘柄の追加取得(取得額3百万円)によるものです。 |
| N213 | 資産除去債務 | 242,000,000 円 | 215,469,000 | xbrl:jppfs_cor:AssetRetirementObligationsNCL@CurrentYearInstant | ― | 万円減)、資産除去債務215百万円(同198百万円)、その他242百万円です。 |
| N220 | 長期借入金 | 843,000,000 円 | 275,773,000 | xbrl:jppfs_cor:LongTermLoansPayable@CurrentYearInstant | ― | 34百万円と長期借入金275百万円の合計510百万円(前期末843百万円)まで減少しており、 |
| N221 | 長期借入金 | 2,605 百万円 | 275,773,000 | xbrl:jppfs_cor:LongTermLoansPayable@CurrentYearInstant | ― | 計510百万円(前期末843百万円)まで減少しており、現預金2,605百万円に対して実質無借金に |
| N238 | その他の包括利益 | 2,907 百万円 | 1,310,889,000 | xbrl:jppfs_cor:OtherComprehensiveIncome@CurrentYearDuration | ― | - その他の包括利益累計額:2,907百万円(同1,596百万円 |
| N239 | その他の包括利益 | 1,596 百万円 | 1,310,889,000 | xbrl:jppfs_cor:OtherComprehensiveIncome@CurrentYearDuration | ― | - その他の包括利益累計額:2,907百万円(同1,596百万円)、1,310百万円 |
| N250 | 剰余金の配当 | 292,000,000 円 | -652,881,000 | xbrl:jppfs_cor:DividendsFromSurplus@CurrentYearDuration | ― | 当期純利益945百万円の計上と剰余金の配当652百万円により292百万円の増加にとどまりまし |
| N283 | 売上債権 | 802,000,000 円 | -802,686,000 | xbrl:jppfs_cor:DecreaseIncreaseInNotesAndAccountsReceivableTradeOpeCF@CurrentYearDuration | ― | たこと、3前期は売上債権が209百万円減少したのに対し当期は802百万円増加し、差引1,01 |
| N290 | 関係会社株式の売却による収入 | 47,000,000 円 | 9,834,000 | xbrl:jppfs_cor:ProceedsFromSalesOfStocksOfSubsidiariesAndAffiliatesInvCF@CurrentYearDuration | ― | 支出44百万円、関係会社株式の売却による収入9百万円、その他47百万円の収入です。 |
| N292 | 設備投資 | 453,000,000 円 | 341,000,000 | xbrl:jpcrp_cor:CapitalExpendituresOverviewOfCapitalExpendituresEtc@CurrentYearDuration | ― | 前期(設備投資関連453百万円)と比べ投資額は抑制 |
| N293 | 投資活動によるキャッシュ・フロー | 773,000,000 円 | -259,037,000 | xbrl:jpcrp_cor:NetCashProvidedByUsedInInvestingActivitiesSummaryOfBusinessResults@CurrentYearDuration | ― | るキャッシュ・フローを差し引いたフリー・キャッシュ・フローは773百万円のプラス(前期2,5 |
| N294 | 投資活動によるキャッシュ・フロー | 2,522 百万円 | -259,037,000 | xbrl:jpcrp_cor:NetCashProvidedByUsedInInvestingActivitiesSummaryOfBusinessResults@CurrentYearDuration | ― | 引いたフリー・キャッシュ・フローは773百万円のプラス(前期2,522百万円のプラス)を確保して |
| N299 | 配当金の支払額 | 7,000,000 円 | -651,749,000 | xbrl:jppfs_cor:CashDividendsPaidFinCF@CurrentYearDuration | ― | 済による支出332百万円、配当金の支払額651百万円、その他7百万円の支出です。 |
| T085 | 剰余金の配当 | 増加 | -126,564,000 | xbrl:jppfs_cor:DividendsFromSurplus@CurrentYearDuration ; xbrl:jppfs_cor:DividendsFromSurplus@Prior1YearDuration ; builtin:sign(cur-prior) | ― | 5百万円の計上と剰余金の配当652百万円により292百万円の増加にとどまり |
| T099 | 売上債権 | 増加 | 209,659,000 | xbrl:jppfs_cor:DecreaseIncreaseInNotesAndAccountsReceivableTradeOpeCF@Prior1YearDuration ; builtin:flow_sign(cur)==direction | ― | 期は売上債権が209百万円減少したのに対し当期は802百万円増加し、差引1 |

## 根拠が見つからない(POINTER_NOT_FOUND) ― 16 件

文の主張に当たる根拠が書類に見つからなかった。

| id | 主語 | 文の値 | 根拠から出た値 | 根拠(pointer) | 理由 | 文 |
|---|---|---|---|---|---|---|
| N019 | ― | 5,951 百万円 | ― | ― | no_element | 5年間で約5,951百万円、18.5%の成長で |
| N032 | 売上高 | 2.9 % | ― | ― | no_element(ratio without fact) | 売上高の伸び率2.9%を大きく上回る原価の |
| N035 | 売上原価 | 2.7 ポイント | ― | ― | no_element(point without prior phrase) | となった結果、売上原価率は前期の67.5%から70.2%へと2.7ポイント上昇し、売上総利益率 |
| N058 | ― | 554,000,000 円 | ― | ― | no_element | その他」の販管費は5,962百万円(前期5,407百万円)と554百万円増加しており、増加額 |
| N070 | 営業利益 | 3.5 ポイント | ― | ― | no_element(point without prior phrase) | 売上高営業利益率は前期の7.3%から3.8%へと3.5ポイント低下しております。 |
| N103 | 税金等調整前当期純利益 | 34.9 % | ― | ― | no_element(ratio without fact) | 税金等調整前当期純利益に対する負担率は34.9%(前期29.0%)と |
| N104 | 税金等調整前当期純利益 | 29 % | ― | ― | no_element(ratio without fact) | 税金等調整前当期純利益に対する負担率は34.9%(前期29.0%)と上昇しております |
| N109 | ― | 1 株 | ― | ― | no_element(unit not in XBRL) | 1株当たり当期純利益は1 |
| N148 | 総資産 | 40.5 % | ― | ― | no_element(ratio without fact) | なお、契約資産11,267百万円は総資産の40.5%を占めており、当社グ |
| N217 | 有利子負債 | 234,000,000 円 | ― | ― | no_element | 有利子負債は1年内返済予定分234百万円と長期借入金275百 |
| N253 | 自己資本比率 | 1.1 ポイント | ― | ― | no_element(point without prior phrase) | この結果、自己資本比率は61.7%(前期末60.6%)と1.1ポイント上昇し、1株当たり純 |
| N254 | 自己資本比率 | 1 株 | ― | ― | no_element(unit not in XBRL) | 比率は61.7%(前期末60.6%)と1.1ポイント上昇し、1株当たり純資産額は2, |
| N263 | ― | 1,996 百万円 | ― | ― | no_element | 032百万円(前期は3,029百万円の増加)となり、前期比で1,996百万円の収入減少となりまし |
| N304 | 有利子負債 | 510,000,000 円 | ― | ― | no_element | 当期末の現金及び預金は2,605百万円、有利子負債は510百万円であり、ネットキャ |
| T025 | 従業員 | 増加 | ― | ― | no_element(text needs money fact) | )、臨時従業員は年間平均409名(同393名)と人員は着実に増加しており、 |
| T087 | 自己資本比率 | 改善 | ― | ― | no_element(text needs money fact) | 自己資本比率は2022年6月期の50.6%から5期連続で改善しており、 |

## 判定できない(UNVERIFIABLE) ― 41 件

主語や形が取れず、判定を止めた。

| id | 主語 | 文の値 | 根拠から出た値 | 根拠(pointer) | 理由 | 文 |
|---|---|---|---|---|---|---|
| N020 | ― | 18.5 % | ― | ― | no_subject | 5年間で約5,951百万円、18.5%の成長であり、受注環 |
| N054 | ― | -28,000,000 円 | ― | ― | ambiguous(elements) | また、役員株式報酬引当金繰入額は△28百万円(前期58百万円)と |
| N055 | ― | 58,000,000 円 | ― | ― | ambiguous(elements) | また、役員株式報酬引当金繰入額は△28百万円(前期58百万円)と戻入となっており |
| N056 | ― | 5,962 百万円 | ― | ― | no_subject | これらを除く「その他」の販管費は5,962百万円(前期5,407百万 |
| N057 | ― | 5,407 百万円 | ― | ― | no_subject | これらを除く「その他」の販管費は5,962百万円(前期5,407百万円)と554百万円増加 |
| N062 | ― | 786,000,000 円 | ― | ― | no_subject | この786百万円の増加は、当期の営業 |
| N196 | ― | 7,000,000 円 | ― | ― | ambiguous(elements) | - 役員株式報酬引当金:7百万円(同69百万円)、6 |
| N197 | ― | 69,000,000 円 | ― | ― | no_subject | - 役員株式報酬引当金:7百万円(同69百万円)、62百万円の減少 |
| N198 | ― | 62,000,000 円 | ― | ― | ambiguous(elements) | - 役員株式報酬引当金:7百万円(同69百万円)、62百万円の減少 |
| N261 | ― | 1,032 百万円 | ― | ― | ambiguous(elements) | 営業活動による資金の増加は1,032百万円(前期は3,029百 |
| N262 | ― | 3,029 百万円 | ― | ― | ambiguous(elements) | 営業活動による資金の増加は1,032百万円(前期は3,029百万円の増加)となり、前期 |
| N273 | ― | 1,813 百万円 | ― | ― | no_subject | 小計は1,813百万円(前期4,032百万 |
| N274 | ― | 4,032 百万円 | ― | ― | no_subject | 小計は1,813百万円(前期4,032百万円)となり、これに利息 |
| N285 | ― | 259,000,000 円 | ― | ― | ambiguous(elements) | 投資活動による資金の減少は259百万円(前期は506百万円 |
| N286 | ― | 506,000,000 円 | ― | ― | ambiguous(elements) | 投資活動による資金の減少は259百万円(前期は506百万円の減少)となりました |
| N295 | ― | 1,073 百万円 | ― | ― | ambiguous(elements) | 財務活動による資金の減少は1,073百万円(前期は1,740百 |
| N296 | ― | 1,740 百万円 | ― | ― | ambiguous(elements) | 財務活動による資金の減少は1,073百万円(前期は1,740百万円の減少)となりました |
| N300 | ― | 905,000,000 円 | ― | ― | no_subject | 前期は短期借入金の純減905百万円がありましたが、当期 |
| T001 | ― | 増収 | ― | ― | no_subject | 増収減益という |
| T002 | ― | 減益 | ― | ― | no_subject | 増収減益という結果 |
| T003 | ― | 下回 | ― | ― | no_subject | 増収減益という結果であり、特に利益面では前期の水準を大きく下回る厳しい決 |
| T006 | ― | 減益 | ― | ― | no_subject | 減益の主たる要 |
| T016 | ― | 増収 | ― | ― | no_subject | 増収にもかかわ |
| T024 | ― | 改善 | ― | ― | no_subject | 価率上昇の主たる背景としては、技術者の確保・定着に向けた処遇改善に伴う人件 |
| T028 | ― | 増加 | ― | ― | no_subject | これは人員の増加および賃金 |
| T030 | ― | 減少 | ― | ― | no_subject | 28百万円(前期58百万円)と戻入となっており、この点は費用減少要因として |
| T031 | ― | 増加 | ― | ― | no_subject | 管費は5,962百万円(前期5,407百万円)と554百万円増加しており、 |
| T032 | ― | 増加 | ― | ― | no_subject | 2百万円(前期5,407百万円)と554百万円増加しており、増加額の大半が |
| T034 | ― | 増加 | ― | ― | no_subject | この786百万円の増加は、当期の |
| T064 | ― | 上回 | ― | ― | no_subject | 境が良好に推移したことにより、年金資産が退職給付債務を大きく上回る積立超過 |
| T065 | ― | 拡大 | ― | ― | no_subject | 、年金資産が退職給付債務を大きく上回る積立超過の状態がさらに拡大しておりま |
| T075 | ― | 減少 | ― | ― | no_subject |  役員株式報酬引当金:7百万円(同69百万円)、62百万円の減少 |
| T089 | ― | 増加 | ― | ― | no_subject | 営業活動による資金の増加は1,03 |
| T090 | ― | 増加 | ― | ― | no_subject | による資金の増加は1,032百万円(前期は3,029百万円の増加)となり、 |
| T091 | ― | 減少 | ― | ― | no_subject | ,029百万円の増加)となり、前期比で1,996百万円の収入減少となりまし |
| T101 | ― | 減少 | ― | ― | no_subject | 前期からの減少の主因は、 |
| T106 | ― | 低下 | ― | ― | no_subject | これらは当社の収益力そのものの低下を意味する |
| T107 | ― | 減少 | ― | ― | no_subject | 投資活動による資金の減少は259百 |
| T108 | ― | 減少 | ― | ― | no_subject | 投資活動による資金の減少は259百万円(前期は506百万円の減少)となりま |
| T109 | ― | 減少 | ― | ― | no_subject | 財務活動による資金の減少は1,07 |
| T110 | ― | 減少 | ― | ― | no_subject | による資金の減少は1,073百万円(前期は1,740百万円の減少)となりま |

## 一致(GROUNDED) ― 330 件

文の値と根拠の値が一致した。

| id | 主語 | 文の値 | 根拠から出た値 | 根拠(pointer) | 理由 | 文 |
|---|---|---|---|---|---|---|
| N001 | 売上高 | 38,064 百万円 | 38,064,274,000 | xbrl:jppfs_cor:NetSales@CurrentYearDuration | ― | 6月30日まで)における当社グループの連結経営成績は、売上高38,064百万円(前期比2.9%増) |
| N002 | 売上高 | 2.9 % | 2.94 | xbrl:jppfs_cor:NetSales@CurrentYearDuration ; xbrl:jppfs_cor:NetSales@Prior1YearDuration | ― | 社グループの連結経営成績は、売上高38,064百万円(前期比2.9%増)と過去最高を更新 |
| N003 | 営業利益 | 1,465 百万円 | 1,465,387,000 | xbrl:jppfs_cor:OperatingIncome@CurrentYearDuration | ― | 万円(前期比2.9%増)と過去最高を更新した一方、営業利益は1,465百万円(同46.0%減)、 |
| N004 | 営業利益 | -46 % | -46.04 | xbrl:jppfs_cor:OperatingIncome@CurrentYearDuration ; xbrl:jppfs_cor:OperatingIncome@Prior1YearDuration | ― | 増)と過去最高を更新した一方、営業利益は1,465百万円(同46.0%減)、経常利益は1, |
| N005 | 経常利益 | 1,457 百万円 | 1,457,848,000 | xbrl:jppfs_cor:OrdinaryIncome@CurrentYearDuration | ― | 方、営業利益は1,465百万円(同46.0%減)、経常利益は1,457百万円(同46.2%減)、 |
| N006 | 経常利益 | -46.2 % | -46.19 | xbrl:jppfs_cor:OrdinaryIncome@CurrentYearDuration ; xbrl:jppfs_cor:OrdinaryIncome@Prior1YearDuration | ― | 65百万円(同46.0%減)、経常利益は1,457百万円(同46.2%減)、親会社株主に帰 |
| N007 | 親会社株主に帰属する当期純利益 | 945,000,000 円 | 945,793,000 | xbrl:jppfs_cor:ProfitLossAttributableToOwnersOfParent@CurrentYearDuration | ― | 7百万円(同46.2%減)、親会社株主に帰属する当期純利益は945百万円(同50.8%減)と |
| N008 | 親会社株主に帰属する当期純利益 | -50.8 % | -50.81 | xbrl:jppfs_cor:ProfitLossAttributableToOwnersOfParent@CurrentYearDuration ; xbrl:jppfs_cor:ProfitLossAttributableToOwnersOfParent@Prior1YearDuration | ― | .2%減)、親会社株主に帰属する当期純利益は945百万円(同50.8%減)となりました。 |
| N009 | 総資産 | 27,836 百万円 | 27,836,421,000 | xbrl:jppfs_cor:Assets@CurrentYearInstant | ― | 一方で、財政状態につきましては、総資産27,836百万円、純資産17,165 |
| N010 | 純資産 | 17,165 百万円 | 17,165,944,000 | xbrl:jppfs_cor:NetAssets@CurrentYearInstant | ― | で、財政状態につきましては、総資産27,836百万円、純資産17,165百万円、自己資本比率61. |
| N011 | 自己資本比率 | 61.7 % | 61.7 | xbrl:jpcrp_cor:EquityToAssetRatioSummaryOfBusinessResults@CurrentYearInstant | ― | 産27,836百万円、純資産17,165百万円、自己資本比率61.7%(前期末60.6%) |
| N012 | 自己資本比率 | 60.6 % | 60.6 | xbrl:jpcrp_cor:EquityToAssetRatioSummaryOfBusinessResults@Prior1YearInstant | ― | 円、純資産17,165百万円、自己資本比率61.7%(前期末60.6%)と財務の健全性はさ |
| N013 | 包括利益 | 2,256 百万円 | 2,256,683,000 | xbrl:jppfs_cor:ComprehensiveIncome@CurrentYearDuration | ― | また、包括利益は2,256百万円を計上しており、退職 |
| N014 | 売上高 | 38,064 百万円 | 38,064,274,000 | xbrl:jppfs_cor:NetSales@CurrentYearDuration | ― | 当連結会計年度の売上高は38,064百万円となり、前連結会計年 |
| N015 | 売上高 | 36,975 百万円 | 36,975,577,000 | xbrl:jppfs_cor:NetSales@Prior1YearDuration | ― | 会計年度の売上高は38,064百万円となり、前連結会計年度の36,975百万円から1,088百万円 |
| N016 | 売上高 | 1,088 百万円 | 1,088,697,000 | xbrl:jppfs_cor:NetSales@CurrentYearDuration ; xbrl:jppfs_cor:NetSales@Prior1YearDuration ; formula:a-b | ― | ,064百万円となり、前連結会計年度の36,975百万円から1,088百万円、率にして2.9%の |
| N017 | 売上高 | 2.9 % | 2.94 | xbrl:jppfs_cor:NetSales@CurrentYearDuration ; xbrl:jppfs_cor:NetSales@Prior1YearDuration | ― | 結会計年度の36,975百万円から1,088百万円、率にして2.9%の増収となりました。 |
| N018 | 売上高 | 38,064 百万円 | 38,064,274,000 | xbrl:jppfs_cor:NetSales@CurrentYearDuration | ― | 131百万円、2025年6月期36,975百万円、そして当期38,064百万円と、5期連続で増収を |
| N021 | 受取手形及び売掛金 | 2,556 百万円 | 2,556,498,000 | xbrl:jppfs_cor:NotesAndAccountsReceivableTrade@CurrentYearInstant | ― | なお、売上債権(受取手形及び売掛金)は期末時点で2,556百万円と前期末の1,751 |
| N022 | 受取手形及び売掛金 | 1,751 百万円 | 1,751,723,000 | xbrl:jppfs_cor:NotesAndAccountsReceivableTrade@Prior1YearInstant | ― | (受取手形及び売掛金)は期末時点で2,556百万円と前期末の1,751百万円から804百万円増加 |
| N023 | 受取手形及び売掛金 | 804,000,000 円 | 804,775,000 | xbrl:jppfs_cor:NotesAndAccountsReceivableTrade@CurrentYearInstant ; xbrl:jppfs_cor:NotesAndAccountsReceivableTrade@Prior1YearInstant ; formula:a-b | ― | )は期末時点で2,556百万円と前期末の1,751百万円から804百万円増加しており、期末近 |
| N024 | 売上総利益 | 11,334 百万円 | 11,334,658,000 | xbrl:jppfs_cor:GrossProfit@CurrentYearDuration | ― | 売上総利益は11,334百万円となり、前期の12, |
| N025 | 売上総利益 | 12,018 百万円 | 12,018,937,000 | xbrl:jppfs_cor:GrossProfit@Prior1YearDuration | ― | 売上総利益は11,334百万円となり、前期の12,018百万円から684百万円、5 |
| N026 | 売上総利益 | 684,000,000 円 | -684,279,000 | xbrl:jppfs_cor:GrossProfit@CurrentYearDuration ; xbrl:jppfs_cor:GrossProfit@Prior1YearDuration ; formula:a-b | ― | 利益は11,334百万円となり、前期の12,018百万円から684百万円、5.7%の減少とな |
| N027 | 売上総利益 | -5.7 % | -5.69 | xbrl:jppfs_cor:GrossProfit@CurrentYearDuration ; xbrl:jppfs_cor:GrossProfit@Prior1YearDuration | ― | 34百万円となり、前期の12,018百万円から684百万円、5.7%の減少となりました。 |
| N028 | 売上原価 | 26,729 百万円 | 26,729,616,000 | xbrl:jppfs_cor:CostOfSales@CurrentYearDuration | ― | 売上原価は26,729百万円(前期24,956百 |
| N029 | 売上原価 | 24,956 百万円 | 24,956,639,000 | xbrl:jppfs_cor:CostOfSales@Prior1YearDuration | ― | 売上原価は26,729百万円(前期24,956百万円)と1,772百万円 |
| N030 | 売上原価 | 1,772 百万円 | 1,772,977,000 | xbrl:jppfs_cor:CostOfSales@CurrentYearDuration ; xbrl:jppfs_cor:CostOfSales@Prior1YearDuration ; formula:a-b | ― | 売上原価は26,729百万円(前期24,956百万円)と1,772百万円、7.1%増加しまし |
| N031 | 売上原価 | 7.1 % | 7.1 | xbrl:jppfs_cor:CostOfSales@CurrentYearDuration ; xbrl:jppfs_cor:CostOfSales@Prior1YearDuration | ― | ,729百万円(前期24,956百万円)と1,772百万円、7.1%増加しました。 |
| N033 | 売上原価率 | 67.5 % | 67.49 | xbrl:jppfs_cor:CostOfSales@Prior1YearDuration ; xbrl:jppfs_cor:NetSales@Prior1YearDuration ; formula:a/b*100 | ― | 9%を大きく上回る原価の伸びとなった結果、売上原価率は前期の67.5%から70.2%へと2 |
| N034 | 売上原価率 | 70.2 % | 70.22 | xbrl:jppfs_cor:CostOfSales@CurrentYearDuration ; xbrl:jppfs_cor:NetSales@CurrentYearDuration ; formula:a/b*100 | ― | 回る原価の伸びとなった結果、売上原価率は前期の67.5%から70.2%へと2.7ポイント上 |
| N036 | 売上総利益率 | 32.5 % | 32.51 | xbrl:jppfs_cor:GrossProfit@Prior1YearDuration ; xbrl:jppfs_cor:NetSales@Prior1YearDuration ; formula:a/b*100 | ― | .5%から70.2%へと2.7ポイント上昇し、売上総利益率は32.5%から29.8%へと低 |
| N037 | 売上総利益率 | 29.8 % | 29.78 | xbrl:jppfs_cor:GrossProfit@CurrentYearDuration ; xbrl:jppfs_cor:NetSales@CurrentYearDuration ; formula:a/b*100 | ― | .2%へと2.7ポイント上昇し、売上総利益率は32.5%から29.8%へと低下しております |
| N038 | 従業員数 | 1,462 名 | 1,462 | xbrl:jpcrp_cor:NumberOfEmployees@CurrentYearInstant | ― | 当社グループの従業員数は1,462名(前期末1,447名 |
| N042 | 販売費及び一般管理費 | 9,869 百万円 | 9,869,271,000 | xbrl:jppfs_cor:SellingGeneralAndAdministrativeExpenses@CurrentYearDuration | ― | 販売費及び一般管理費は9,869百万円となり、前期の9,3 |
| N043 | 販売費及び一般管理費 | 9,303 百万円 | 9,303,013,000 | xbrl:jppfs_cor:SellingGeneralAndAdministrativeExpenses@Prior1YearDuration | ― | 販売費及び一般管理費は9,869百万円となり、前期の9,303百万円から566百万円、6 |
| N044 | 販売費及び一般管理費 | 566,000,000 円 | 566,258,000 | xbrl:jppfs_cor:SellingGeneralAndAdministrativeExpenses@CurrentYearDuration ; xbrl:jppfs_cor:SellingGeneralAndAdministrativeExpenses@Prior1YearDuration ; formula:a-b | ― | 般管理費は9,869百万円となり、前期の9,303百万円から566百万円、6.1%増加しまし |
| N045 | 販売費及び一般管理費 | 6.1 % | 6.09 | xbrl:jppfs_cor:SellingGeneralAndAdministrativeExpenses@CurrentYearDuration ; xbrl:jppfs_cor:SellingGeneralAndAdministrativeExpenses@Prior1YearDuration | ― | 869百万円となり、前期の9,303百万円から566百万円、6.1%増加しました。 |
| N046 | 従業員給料及び手当 | 3,559 百万円 | 3,559,936,000 | xbrl:jppfs_cor:EmployeesSalariesAndAllowancesSGA@CurrentYearDuration | ― | 内訳を見ますと、従業員給料及び手当は3,559百万円(前期3,441百万 |
| N047 | 従業員給料及び手当 | 3,441 百万円 | 3,441,694,000 | xbrl:jppfs_cor:EmployeesSalariesAndAllowancesSGA@Prior1YearDuration | ― | 内訳を見ますと、従業員給料及び手当は3,559百万円(前期3,441百万円)と118百万円増加 |
| N048 | 従業員給料及び手当 | 118,000,000 円 | 118,242,000 | xbrl:jppfs_cor:EmployeesSalariesAndAllowancesSGA@CurrentYearDuration ; xbrl:jppfs_cor:EmployeesSalariesAndAllowancesSGA@Prior1YearDuration ; formula:a-b | ― | 業員給料及び手当は3,559百万円(前期3,441百万円)と118百万円増加しております。 |
| N049 | 研究開発費 | 255,000,000 円 | 255,928,000 | xbrl:jppfs_cor:ResearchAndDevelopmentExpensesSGA@CurrentYearDuration | ― | 研究開発費は255百万円(前期257百万円) |
| N050 | 研究開発費 | 257,000,000 円 | 257,810,000 | xbrl:jppfs_cor:ResearchAndDevelopmentExpensesSGA@Prior1YearDuration | ― | 研究開発費は255百万円(前期257百万円)とほぼ前年並みの水 |
| N051 | 退職給付費用 | 118,000,000 円 | 118,308,000 | xbrl:jppfs_cor:RetirementBenefitExpensesSGA@CurrentYearDuration | ― | 退職給付費用は118百万円(前期137百万円) |
| N052 | 退職給付費用 | 137,000,000 円 | 137,251,000 | xbrl:jppfs_cor:RetirementBenefitExpensesSGA@Prior1YearDuration | ― | 退職給付費用は118百万円(前期137百万円)と18百万円減少し |
| N053 | 退職給付費用 | 18,000,000 円 | -18,943,000 | xbrl:jppfs_cor:RetirementBenefitExpensesSGA@CurrentYearDuration ; xbrl:jppfs_cor:RetirementBenefitExpensesSGA@Prior1YearDuration ; formula:a-b | ― | 退職給付費用は118百万円(前期137百万円)と18百万円減少しました。 |
| N059 | 完成業務補償引当金 | 991,000,000 円 | 991,000,000 | xbrl:jpcrp030000-asr_E36539-000:ProvisionForWarrantiesForCompletedOperationCL@CurrentYearInstant | ― | 完成業務補償引当金は期末残高が991百万円となり、前期末の20 |
| N060 | 完成業務補償引当金 | 205,000,000 円 | 205,000,000 | xbrl:jpcrp030000-asr_E36539-000:ProvisionForWarrantiesForCompletedOperationCL@Prior1YearInstant | ― | 完成業務補償引当金は期末残高が991百万円となり、前期末の205百万円から786百万円増加 |
| N061 | 完成業務補償引当金 | 786,000,000 円 | 786,000,000 | xbrl:jpcrp030000-asr_E36539-000:ProvisionForWarrantiesForCompletedOperationCL@CurrentYearInstant ; xbrl:jpcrp030000-asr_E36539-000:ProvisionForWarrantiesForCompletedOperationCL@Prior1YearInstant ; formula:a-b | ― | 当金は期末残高が991百万円となり、前期末の205百万円から786百万円増加いたしました。 |
| N063 | 営業利益 | 1,250 百万円 | -1,250,537,000 | xbrl:jppfs_cor:OperatingIncome@CurrentYearDuration ; xbrl:jppfs_cor:OperatingIncome@Prior1YearDuration ; formula:a-b | ― | この786百万円の増加は、当期の営業利益の減益額1,250百万円の約6割に相当する規 |
| N064 | 営業利益 | 1,465 百万円 | 1,465,387,000 | xbrl:jppfs_cor:OperatingIncome@CurrentYearDuration | ― | この結果、営業利益は1,465百万円となり、前期の2,7 |
| N065 | 営業利益 | 2,715 百万円 | 2,715,924,000 | xbrl:jppfs_cor:OperatingIncome@Prior1YearDuration | ― | この結果、営業利益は1,465百万円となり、前期の2,715百万円から1,250百万円 |
| N066 | 営業利益 | 1,250 百万円 | -1,250,537,000 | xbrl:jppfs_cor:OperatingIncome@CurrentYearDuration ; xbrl:jppfs_cor:OperatingIncome@Prior1YearDuration ; formula:a-b | ― | 営業利益は1,465百万円となり、前期の2,715百万円から1,250百万円、46.0%の大幅減 |
| N067 | 営業利益 | -46 % | -46.04 | xbrl:jppfs_cor:OperatingIncome@CurrentYearDuration ; xbrl:jppfs_cor:OperatingIncome@Prior1YearDuration | ― | 5百万円となり、前期の2,715百万円から1,250百万円、46.0%の大幅減益となりまし |
| N068 | 売上高営業利益率 | 7.3 % | 7.35 | xbrl:jppfs_cor:OperatingIncome@Prior1YearDuration ; xbrl:jppfs_cor:NetSales@Prior1YearDuration ; formula:a/b*100 | ― | 売上高営業利益率は前期の7.3%から3.8%へと3. |
| N069 | 売上高営業利益率 | 3.8 % | 3.85 | xbrl:jppfs_cor:OperatingIncome@CurrentYearDuration ; xbrl:jppfs_cor:NetSales@CurrentYearDuration ; formula:a/b*100 | ― | 売上高営業利益率は前期の7.3%から3.8%へと3.5ポイント低 |
| N071 | 営業外収益 | 87,000,000 円 | 87,537,000 | xbrl:jppfs_cor:NonOperatingIncome@CurrentYearDuration | ― | 営業外収益は87百万円(前期72百万円)と |
| N072 | 営業外収益 | 72,000,000 円 | 72,687,000 | xbrl:jppfs_cor:NonOperatingIncome@Prior1YearDuration | ― | 営業外収益は87百万円(前期72百万円)と14百万円増加し |
| N073 | 営業外収益 | 14,000,000 円 | 14,850,000 | xbrl:jppfs_cor:NonOperatingIncome@CurrentYearDuration ; xbrl:jppfs_cor:NonOperatingIncome@Prior1YearDuration ; formula:a-b | ― | 営業外収益は87百万円(前期72百万円)と14百万円増加しました。 |
| N074 | 受取利息 | 9,000,000 円 | 9,510,000 | xbrl:jppfs_cor:InterestIncomeNOI@CurrentYearDuration | ― | 主な内訳は、受取利息9百万円(前期1百万円)、受 |
| N075 | 受取利息 | 1,000,000 円 | 1,901,000 | xbrl:jppfs_cor:InterestIncomeNOI@Prior1YearDuration | ― | 主な内訳は、受取利息9百万円(前期1百万円)、受取配当金25百 |
| N076 | 受取配当金 | 25,000,000 円 | 25,567,000 | xbrl:jppfs_cor:DividendsIncomeNOI@CurrentYearDuration | ― | 主な内訳は、受取利息9百万円(前期1百万円)、受取配当金25百万円(同20百万円)、不 |
| N077 | 受取配当金 | 20,000,000 円 | 20,161,000 | xbrl:jppfs_cor:DividendsIncomeNOI@Prior1YearDuration | ― | 、受取利息9百万円(前期1百万円)、受取配当金25百万円(同20百万円)、不動産賃貸料15 |
| N078 | 不動産賃貸料 | 15,000,000 円 | 15,296,000 | xbrl:jppfs_cor:RealEstateRentNOI@Prior1YearDuration | ― | 百万円)、受取配当金25百万円(同20百万円)、不動産賃貸料15百万円(同15百万円)、そ |
| N079 | 不動産賃貸料 | 15,000,000 円 | 15,296,000 | xbrl:jppfs_cor:RealEstateRentNOI@Prior1YearDuration | ― | 配当金25百万円(同20百万円)、不動産賃貸料15百万円(同15百万円)、その他37百万円 |
| N082 | 営業外費用 | 95,000,000 円 | 95,075,000 | xbrl:jppfs_cor:NonOperatingExpenses@CurrentYearDuration | ― | 営業外費用は95百万円(前期79百万円)と |
| N083 | 営業外費用 | 79,000,000 円 | 79,560,000 | xbrl:jppfs_cor:NonOperatingExpenses@Prior1YearDuration | ― | 営業外費用は95百万円(前期79百万円)と15百万円増加し |
| N084 | 営業外費用 | 15,000,000 円 | 15,515,000 | xbrl:jppfs_cor:NonOperatingExpenses@CurrentYearDuration ; xbrl:jppfs_cor:NonOperatingExpenses@Prior1YearDuration ; formula:a-b | ― | 営業外費用は95百万円(前期79百万円)と15百万円増加しました。 |
| N085 | 支払利息 | 80,000,000 円 | 80,579,000 | xbrl:jppfs_cor:InterestExpensesNOE@CurrentYearDuration | ― | 主な内訳は支払利息80百万円(前期58百万円)で |
| N086 | 支払利息 | 58,000,000 円 | 58,689,000 | xbrl:jppfs_cor:InterestExpensesNOE@Prior1YearDuration | ― | 主な内訳は支払利息80百万円(前期58百万円)で、金利上昇の影響 |
| N087 | 支払利息 | 21,000,000 円 | 21,890,000 | xbrl:jppfs_cor:InterestExpensesNOE@CurrentYearDuration ; xbrl:jppfs_cor:InterestExpensesNOE@Prior1YearDuration ; formula:a-b | ― | 支払利息80百万円(前期58百万円)で、金利上昇の影響により21百万円増加しております。 |
| N088 | 経常利益 | 1,457 百万円 | 1,457,848,000 | xbrl:jppfs_cor:OrdinaryIncome@CurrentYearDuration | ― | 以上の結果、経常利益は1,457百万円(前期2,709百万 |
| N089 | 経常利益 | 2,709 百万円 | 2,709,051,000 | xbrl:jppfs_cor:OrdinaryIncome@Prior1YearDuration | ― | 以上の結果、経常利益は1,457百万円(前期2,709百万円)となり、1,251 |
| N090 | 経常利益 | 1,251 百万円 | -1,251,203,000 | xbrl:jppfs_cor:OrdinaryIncome@CurrentYearDuration ; xbrl:jppfs_cor:OrdinaryIncome@Prior1YearDuration ; formula:a-b | ― | 、経常利益は1,457百万円(前期2,709百万円)となり、1,251百万円、46.2%の減益と |
| N091 | 経常利益 | -46.2 % | -46.19 | xbrl:jppfs_cor:OrdinaryIncome@CurrentYearDuration ; xbrl:jppfs_cor:OrdinaryIncome@Prior1YearDuration | ― | 57百万円(前期2,709百万円)となり、1,251百万円、46.2%の減益となりました。 |
| N092 | 特別利益 | 1,000,000 円 | 1,232,000 | xbrl:jppfs_cor:ExtraordinaryIncome@CurrentYearDuration | ― | 特別利益は1百万円で、固定資産売却益1 |
| N093 | 固定資産売却益 | 1,000,000 円 | 1,232,000 | xbrl:jppfs_cor:GainOnSalesOfNoncurrentAssetsEI@CurrentYearDuration | ― | 特別利益は1百万円で、固定資産売却益1百万円を計上しました。 |
| N094 | 特別損失 | 7,000,000 円 | 7,068,000 | xbrl:jppfs_cor:ExtraordinaryLoss@CurrentYearDuration | ― | 特別損失は7百万円で、内訳は関係会社株 |
| N095 | 関係会社株式売却損 | 6,000,000 円 | 6,165,000 | xbrl:jppfs_cor:LossOnSalesOfStocksOfSubsidiariesAndAffiliatesEL@CurrentYearDuration | ― | 特別損失は7百万円で、内訳は関係会社株式売却損6百万円および減損損失0百万 |
| N096 | 減損損失 | 0 円 | 903,000 | xbrl:jppfs_cor:ImpairmentLossEL@CurrentYearDuration | ― | は7百万円で、内訳は関係会社株式売却損6百万円および減損損失0百万円です。 |
| N097 | 税金等調整前当期純利益 | 1,452 百万円 | 1,452,012,000 | xbrl:jppfs_cor:IncomeBeforeIncomeTaxes@CurrentYearDuration | ― | この結果、税金等調整前当期純利益は1,452百万円(前期2,707百万 |
| N098 | 税金等調整前当期純利益 | 2,707 百万円 | 2,707,871,000 | xbrl:jppfs_cor:IncomeBeforeIncomeTaxes@Prior1YearDuration | ― | この結果、税金等調整前当期純利益は1,452百万円(前期2,707百万円)となりました。 |
| N099 | 法人税等合計 | 506,000,000 円 | 506,218,000 | xbrl:jppfs_cor:IncomeTaxes@CurrentYearDuration | ― | 法人税等合計は506百万円(前期785百万円) |
| N100 | 法人税等合計 | 785,000,000 円 | 785,289,000 | xbrl:jppfs_cor:IncomeTaxes@Prior1YearDuration | ― | 法人税等合計は506百万円(前期785百万円)で、内訳は法人税等 |
| N101 | 法人税、住民税及び事業税 | 626,000,000 円 | 626,340,000 | xbrl:jppfs_cor:IncomeTaxesCurrent@CurrentYearDuration | ― | 円)で、内訳は法人税等調整額を除く法人税、住民税及び事業税が626百万円、法人税等調整額が△ |
| N102 | 法人税等調整額 | -120,000,000 円 | -120,121,000 | xbrl:jppfs_cor:IncomeTaxesDeferred@CurrentYearDuration | ― | 除く法人税、住民税及び事業税が626百万円、法人税等調整額が△120百万円です。 |
| N105 | 親会社株主に帰属する当期純利益 | 945,000,000 円 | 945,793,000 | xbrl:jppfs_cor:ProfitLossAttributableToOwnersOfParent@CurrentYearDuration | ― | 以上により、親会社株主に帰属する当期純利益は945百万円(前期1,922百万 |
| N106 | 親会社株主に帰属する当期純利益 | 1,922 百万円 | 1,922,581,000 | xbrl:jppfs_cor:ProfitLossAttributableToOwnersOfParent@Prior1YearDuration | ― | 上により、親会社株主に帰属する当期純利益は945百万円(前期1,922百万円)となり、976百万 |
| N107 | 親会社株主に帰属する当期純利益 | 976,000,000 円 | -976,788,000 | xbrl:jppfs_cor:ProfitLossAttributableToOwnersOfParent@CurrentYearDuration ; xbrl:jppfs_cor:ProfitLossAttributableToOwnersOfParent@Prior1YearDuration ; formula:a-b | ― | する当期純利益は945百万円(前期1,922百万円)となり、976百万円、50.8%の減益と |
| N108 | 親会社株主に帰属する当期純利益 | -50.8 % | -50.81 | xbrl:jppfs_cor:ProfitLossAttributableToOwnersOfParent@CurrentYearDuration ; xbrl:jppfs_cor:ProfitLossAttributableToOwnersOfParent@Prior1YearDuration | ― | は945百万円(前期1,922百万円)となり、976百万円、50.8%の減益となりました。 |
| N110 | 1株当たり当期純利益 | 115 円 | 115.43 | xbrl:jpcrp_cor:BasicEarningsLossPerShareSummaryOfBusinessResults@CurrentYearDuration | ― | 1株当たり当期純利益は115円43銭(前期236円 |
| N111 | 1株当たり当期純利益 | 236 円 | 236.28 | xbrl:jpcrp_cor:BasicEarningsLossPerShareSummaryOfBusinessResults@Prior1YearDuration | ― | 1株当たり当期純利益は115円43銭(前期236円28銭)、自己資本当 |
| N112 | ROE | 5.8 % | 5.8 | xbrl:jpcrp_cor:RateOfReturnOnEquitySummaryOfBusinessResults@CurrentYearDuration | ― | 3銭(前期236円28銭)、自己資本当期純利益率(ROE)は5.8%(前期13.3%)と |
| N113 | ROE | 13.3 % | 13.3 | xbrl:jpcrp_cor:RateOfReturnOnEquitySummaryOfBusinessResults@Prior1YearDuration | ― | 6円28銭)、自己資本当期純利益率(ROE)は5.8%(前期13.3%)となっております。 |
| N114 | 包括利益 | 2,256 百万円 | 2,256,683,000 | xbrl:jppfs_cor:ComprehensiveIncome@CurrentYearDuration | ― | 当期純利益が大幅減益となった一方、**包括利益は2,256百万円**(前期2,451 |
| N115 | 包括利益 | 2,451 百万円 | 2,451,498,000 | xbrl:jppfs_cor:ComprehensiveIncome@Prior1YearDuration | ― | 幅減益となった一方、**包括利益は2,256百万円**(前期2,451百万円)と、前期比では19 |
| N116 | 包括利益 | 194,000,000 円 | -194,815,000 | xbrl:jppfs_cor:ComprehensiveIncome@CurrentYearDuration ; xbrl:jppfs_cor:ComprehensiveIncome@Prior1YearDuration ; formula:a-b | ― | は2,256百万円**(前期2,451百万円)と、前期比では194百万円、7.9%の減少にと |
| N117 | 包括利益 | -7.9 % | -7.95 | xbrl:jppfs_cor:ComprehensiveIncome@CurrentYearDuration ; xbrl:jppfs_cor:ComprehensiveIncome@Prior1YearDuration | ― | 万円**(前期2,451百万円)と、前期比では194百万円、7.9%の減少にとどまりまし |
| N118 | その他の包括利益 | 1,310 百万円 | 1,310,889,000 | xbrl:jppfs_cor:OtherComprehensiveIncome@CurrentYearDuration | ― | その他の包括利益は1,310百万円(前期528百万円) |
| N119 | その他の包括利益 | 528,000,000 円 | 528,917,000 | xbrl:jppfs_cor:OtherComprehensiveIncome@Prior1YearDuration | ― | その他の包括利益は1,310百万円(前期528百万円)と782百万円増加 |
| N121 | 退職給付に係る調整額 | 1,085 百万円 | 1,085,488,000 | xbrl:jppfs_cor:RemeasurementsOfDefinedBenefitPlansNetOfTaxOCI@CurrentYearDuration | ― | 内訳は、退職給付に係る調整額1,085百万円(前期470百万円) |
| N122 | 退職給付に係る調整額 | 470,000,000 円 | 470,303,000 | xbrl:jppfs_cor:RemeasurementsOfDefinedBenefitPlansNetOfTaxOCI@Prior1YearDuration | ― | 内訳は、退職給付に係る調整額1,085百万円(前期470百万円)、その他有価証券評 |
| N123 | その他有価証券評価差額金 | 217,000,000 円 | 217,490,000 | xbrl:jppfs_cor:ValuationDifferenceOnAvailableForSaleSecurities@CurrentYearInstant ; xbrl:jppfs_cor:ValuationDifferenceOnAvailableForSaleSecurities@Prior1YearInstant ; formula:a-b | ― | ,085百万円(前期470百万円)、その他有価証券評価差額金217百万円(同62百万円)、為 |
| N125 | 為替換算調整勘定 | 2,000,000 円 | 2,918,000 | xbrl:jppfs_cor:ForeignCurrencyTranslationAdjustmentNetOfTaxOCI@CurrentYearDuration | ― | 証券評価差額金217百万円(同62百万円)、為替換算調整勘定2百万円(同△3百万円)、繰 |
| N126 | 為替換算調整勘定 | -3,000,000 円 | -3,621,000 | xbrl:jppfs_cor:ForeignCurrencyTranslationAdjustmentNetOfTaxOCI@Prior1YearDuration | ― | 金217百万円(同62百万円)、為替換算調整勘定2百万円(同△3百万円)、繰延ヘッジ損益4 |
| N127 | 繰延ヘッジ損益 | 4,000,000 円 | 4,992,000 | xbrl:jppfs_cor:DeferredGainsOrLossesOnHedges@CurrentYearInstant | ― | )、為替換算調整勘定2百万円(同△3百万円)、繰延ヘッジ損益4百万円です。 |
| N128 | 総資産 | 27,836 百万円 | 27,836,421,000 | xbrl:jppfs_cor:Assets@CurrentYearInstant | ― | 当連結会計年度末の総資産は27,836百万円となり、前連結会計年 |
| N129 | 総資産 | 25,554 百万円 | 25,554,675,000 | xbrl:jppfs_cor:Assets@Prior1YearInstant | ― | 年度末の総資産は27,836百万円となり、前連結会計年度末の25,554百万円から2,281百万円 |
| N130 | 総資産 | 2,281 百万円 | 2,281,746,000 | xbrl:jppfs_cor:Assets@CurrentYearInstant ; xbrl:jppfs_cor:Assets@Prior1YearInstant ; formula:a-b | ― | 836百万円となり、前連結会計年度末の25,554百万円から2,281百万円、8.9%増加しまし |
| N131 | 総資産 | 8.9 % | 8.93 | xbrl:jppfs_cor:Assets@CurrentYearInstant ; xbrl:jppfs_cor:Assets@Prior1YearInstant | ― | 、前連結会計年度末の25,554百万円から2,281百万円、8.9%増加しました。 |
| N132 | 流動資産 | 16,943 百万円 | 16,943,470,000 | xbrl:jppfs_cor:CurrentAssets@CurrentYearInstant | ― | **流動資産**は16,943百万円(前期末16,533 |
| N133 | 流動資産 | 16,533 百万円 | 16,533,523,000 | xbrl:jppfs_cor:CurrentAssets@Prior1YearInstant | ― | **流動資産**は16,943百万円(前期末16,533百万円)と409百万円増加 |
| N134 | 流動資産 | 409,000,000 円 | 409,947,000 | xbrl:jppfs_cor:CurrentAssets@CurrentYearInstant ; xbrl:jppfs_cor:CurrentAssets@Prior1YearInstant ; formula:a-b | ― | 動資産**は16,943百万円(前期末16,533百万円)と409百万円増加しました。 |
| N135 | 現金及び預金 | 2,605 百万円 | 2,605,950,000 | xbrl:jppfs_cor:CashAndDeposits@CurrentYearInstant | ― | - 現金及び預金:2,605百万円(前期末2,899百 |
| N136 | 現金及び預金 | 2,899 百万円 | 2,899,140,000 | xbrl:jppfs_cor:CashAndDeposits@Prior1YearInstant | ― | - 現金及び預金:2,605百万円(前期末2,899百万円)、293百万円の減 |
| N137 | 現金及び預金 | 293,000,000 円 | -293,190,000 | xbrl:jppfs_cor:CashAndDeposits@CurrentYearInstant ; xbrl:jppfs_cor:CashAndDeposits@Prior1YearInstant ; formula:a-b | ― |  現金及び預金:2,605百万円(前期末2,899百万円)、293百万円の減少 |
| N138 | 受取手形及び売掛金 | 2,556 百万円 | 2,556,498,000 | xbrl:jppfs_cor:NotesAndAccountsReceivableTrade@CurrentYearInstant | ― | - 受取手形及び売掛金:2,556百万円(同1,751百万円 |
| N139 | 受取手形及び売掛金 | 1,751 百万円 | 1,751,723,000 | xbrl:jppfs_cor:NotesAndAccountsReceivableTrade@Prior1YearInstant | ― | - 受取手形及び売掛金:2,556百万円(同1,751百万円)、804百万円の増 |
| N140 | 受取手形及び売掛金 | 804,000,000 円 | 804,775,000 | xbrl:jppfs_cor:NotesAndAccountsReceivableTrade@CurrentYearInstant ; xbrl:jppfs_cor:NotesAndAccountsReceivableTrade@Prior1YearInstant ; formula:a-b | ― | 受取手形及び売掛金:2,556百万円(同1,751百万円)、804百万円の増加 |
| N141 | 契約資産 | 11,267 百万円 | 11,267,515,000 | xbrl:jppfs_cor:ContractAssets@CurrentYearInstant | ― | - 契約資産:11,267百万円(同11,428百万 |
| N142 | 契約資産 | 11,428 百万円 | 11,428,545,000 | xbrl:jppfs_cor:ContractAssets@Prior1YearInstant | ― | - 契約資産:11,267百万円(同11,428百万円)、161百万円の減 |
| N143 | 契約資産 | 161,000,000 円 | -161,030,000 | xbrl:jppfs_cor:ContractAssets@CurrentYearInstant ; xbrl:jppfs_cor:ContractAssets@Prior1YearInstant ; formula:a-b | ― | - 契約資産:11,267百万円(同11,428百万円)、161百万円の減少 |
| N147 | 契約資産 | 11,267 百万円 | 11,267,515,000 | xbrl:jppfs_cor:ContractAssets@CurrentYearInstant | ― | なお、契約資産11,267百万円は総資産の40.5% |
| N149 | 固定資産 | 10,892 百万円 | 10,892,950,000 | xbrl:jppfs_cor:NoncurrentAssets@CurrentYearInstant | ― | **固定資産**は10,892百万円(前期末9,021百 |
| N150 | 固定資産 | 9,021 百万円 | 9,021,152,000 | xbrl:jppfs_cor:NoncurrentAssets@Prior1YearInstant | ― | **固定資産**は10,892百万円(前期末9,021百万円)と1,871百万円 |
| N151 | 固定資産 | 1,871 百万円 | 1,871,798,000 | xbrl:jppfs_cor:NoncurrentAssets@CurrentYearInstant ; xbrl:jppfs_cor:NoncurrentAssets@Prior1YearInstant ; formula:a-b | ― | 固定資産**は10,892百万円(前期末9,021百万円)と1,871百万円、20.7%の大幅増 |
| N152 | 固定資産 | 20.7 % | 20.75 | xbrl:jppfs_cor:NoncurrentAssets@CurrentYearInstant ; xbrl:jppfs_cor:NoncurrentAssets@Prior1YearInstant | ― | ,892百万円(前期末9,021百万円)と1,871百万円、20.7%の大幅増加となりまし |
| N153 | 有形固定資産 | 2,092 百万円 | 2,092,189,000 | xbrl:jppfs_cor:PropertyPlantAndEquipment@CurrentYearInstant | ― | - 有形固定資産:2,092百万円(前期末2,083百 |
| N154 | 有形固定資産 | 2,083 百万円 | 2,083,066,000 | xbrl:jppfs_cor:PropertyPlantAndEquipment@Prior1YearInstant | ― | - 有形固定資産:2,092百万円(前期末2,083百万円)、9百万円の増加 |
| N155 | 有形固定資産 | 9,000,000 円 | 9,123,000 | xbrl:jppfs_cor:PropertyPlantAndEquipment@CurrentYearInstant ; xbrl:jppfs_cor:PropertyPlantAndEquipment@Prior1YearInstant ; formula:a-b | ― |  有形固定資産:2,092百万円(前期末2,083百万円)、9百万円の増加 |
| N156 | 無形固定資産 | 371,000,000 円 | 371,901,000 | xbrl:jppfs_cor:IntangibleAssets@CurrentYearInstant | ― | - 無形固定資産:371百万円(同528百万円)、 |
| N157 | 無形固定資産 | 528,000,000 円 | 528,971,000 | xbrl:jppfs_cor:IntangibleAssets@Prior1YearInstant | ― | - 無形固定資産:371百万円(同528百万円)、157百万円の減 |
| N158 | 無形固定資産 | 157,000,000 円 | -157,070,000 | xbrl:jppfs_cor:IntangibleAssets@CurrentYearInstant ; xbrl:jppfs_cor:IntangibleAssets@Prior1YearInstant ; formula:a-b | ― | - 無形固定資産:371百万円(同528百万円)、157百万円の減少(うち、のれん |
| N159 | のれん | 213,000,000 円 | 213,025,000 | xbrl:jppfs_cor:Goodwill@Prior1YearInstant | ― | 百万円(同528百万円)、157百万円の減少(うち、のれんが213百万円から159百万円へ5 |
| N160 | のれん | 159,000,000 円 | 159,768,000 | xbrl:jppfs_cor:Goodwill@CurrentYearInstant | ― | 百万円)、157百万円の減少(うち、のれんが213百万円から159百万円へ53百万円減少) |
| N161 | のれん | 53,000,000 円 | -53,257,000 | xbrl:jppfs_cor:Goodwill@CurrentYearInstant ; xbrl:jppfs_cor:Goodwill@Prior1YearInstant ; formula:a-b | ― | 7百万円の減少(うち、のれんが213百万円から159百万円へ53百万円減少) |
| N162 | 投資その他の資産 | 8,428 百万円 | 8,428,859,000 | xbrl:jppfs_cor:InvestmentsAndOtherAssets@CurrentYearInstant | ― | - 投資その他の資産:8,428百万円(同6,409百万円 |
| N163 | 投資その他の資産 | 6,409 百万円 | 6,409,114,000 | xbrl:jppfs_cor:InvestmentsAndOtherAssets@Prior1YearInstant | ― | - 投資その他の資産:8,428百万円(同6,409百万円)、2,019百万円 |
| N164 | 投資その他の資産 | 2,019 百万円 | 2,019,745,000 | xbrl:jppfs_cor:InvestmentsAndOtherAssets@CurrentYearInstant ; xbrl:jppfs_cor:InvestmentsAndOtherAssets@Prior1YearInstant ; formula:a-b | ― |  投資その他の資産:8,428百万円(同6,409百万円)、2,019百万円の増加 |
| N165 | 退職給付に係る資産 | 6,174 百万円 | 6,174,228,000 | xbrl:jppfs_cor:NetDefinedBenefitAsset@CurrentYearInstant | ― | 固定資産増加の最大の要因は、**退職給付に係る資産**が6,174百万円(前期末4,345百 |
| N166 | 退職給付に係る資産 | 4,345 百万円 | 4,345,389,000 | xbrl:jppfs_cor:NetDefinedBenefitAsset@Prior1YearInstant | ― | 要因は、**退職給付に係る資産**が6,174百万円(前期末4,345百万円)と1,828百万円 |
| N167 | 退職給付に係る資産 | 1,828 百万円 | 1,828,839,000 | xbrl:jppfs_cor:NetDefinedBenefitAsset@CurrentYearInstant ; xbrl:jppfs_cor:NetDefinedBenefitAsset@Prior1YearInstant ; formula:a-b | ― | に係る資産**が6,174百万円(前期末4,345百万円)と1,828百万円増加したことです。 |
| N168 | 投資有価証券 | 1,203 百万円 | 1,203,225,000 | xbrl:jppfs_cor:InvestmentSecurities@CurrentYearInstant | ― | また、投資有価証券も1,203百万円(同901百万円)と |
| N169 | 投資有価証券 | 901,000,000 円 | 901,714,000 | xbrl:jppfs_cor:InvestmentSecurities@Prior1YearInstant | ― | また、投資有価証券も1,203百万円(同901百万円)と301百万円増加 |
| N170 | 投資有価証券 | 301,000,000 円 | 301,511,000 | xbrl:jppfs_cor:InvestmentSecurities@CurrentYearInstant ; xbrl:jppfs_cor:InvestmentSecurities@Prior1YearInstant ; formula:a-b | ― | また、投資有価証券も1,203百万円(同901百万円)と301百万円増加しました。 |
| N171 | その他有価証券評価差額金 | 414,000,000 円 | 414,441,000 | xbrl:jppfs_cor:ValuationDifferenceOnAvailableForSaleSecurities@Prior1YearInstant | ― | これは保有株式の時価上昇(その他有価証券評価差額金が414百万円から631百万円へ増 |
| N172 | その他有価証券評価差額金 | 631,000,000 円 | 631,931,000 | xbrl:jppfs_cor:ValuationDifferenceOnAvailableForSaleSecurities@CurrentYearInstant | ― | 有株式の時価上昇(その他有価証券評価差額金が414百万円から631百万円へ増加)および一部銘 |
| N174 | 負債合計 | 10,670 百万円 | 10,670,476,000 | xbrl:jppfs_cor:Liabilities@CurrentYearInstant | ― | 負債合計は10,670百万円となり、前期末の10 |
| N175 | 負債合計 | 10,055 百万円 | 10,055,929,000 | xbrl:jppfs_cor:Liabilities@Prior1YearInstant | ― | 負債合計は10,670百万円となり、前期末の10,055百万円から614百万円、6 |
| N176 | 負債合計 | 614,000,000 円 | 614,547,000 | xbrl:jppfs_cor:Liabilities@CurrentYearInstant ; xbrl:jppfs_cor:Liabilities@Prior1YearInstant ; formula:a-b | ― | 計は10,670百万円となり、前期末の10,055百万円から614百万円、6.1%増加しまし |
| N177 | 負債合計 | 6.1 % | 6.11 | xbrl:jppfs_cor:Liabilities@CurrentYearInstant ; xbrl:jppfs_cor:Liabilities@Prior1YearInstant | ― | 0百万円となり、前期末の10,055百万円から614百万円、6.1%増加しました。 |
| N178 | 流動負債 | 8,041 百万円 | 8,041,190,000 | xbrl:jppfs_cor:CurrentLiabilities@CurrentYearInstant | ― | **流動負債**は8,041百万円(前期末7,642百 |
| N179 | 流動負債 | 7,642 百万円 | 7,642,406,000 | xbrl:jppfs_cor:CurrentLiabilities@Prior1YearInstant | ― | **流動負債**は8,041百万円(前期末7,642百万円)と398百万円増加 |
| N180 | 流動負債 | 398,000,000 円 | 398,784,000 | xbrl:jppfs_cor:CurrentLiabilities@CurrentYearInstant ; xbrl:jppfs_cor:CurrentLiabilities@Prior1YearInstant ; formula:a-b | ― | *流動負債**は8,041百万円(前期末7,642百万円)と398百万円増加しました。 |
| N181 | 業務未払金 | 1,757 百万円 | 1,757,446,000 | xbrl:jppfs_cor:AccountsPayableOperatingSpecific@CurrentYearInstant | ― | - 業務未払金:1,757百万円(前期末2,057百 |
| N182 | 業務未払金 | 2,057 百万円 | 2,057,744,000 | xbrl:jppfs_cor:AccountsPayableOperatingSpecific@Prior1YearInstant | ― | - 業務未払金:1,757百万円(前期末2,057百万円)、300百万円の減 |
| N183 | 業務未払金 | 300,000,000 円 | -300,298,000 | xbrl:jppfs_cor:AccountsPayableOperatingSpecific@CurrentYearInstant ; xbrl:jppfs_cor:AccountsPayableOperatingSpecific@Prior1YearInstant ; formula:a-b | ― | - 業務未払金:1,757百万円(前期末2,057百万円)、300百万円の減少 |
| N184 | 未払消費税等 | 1,490 百万円 | 1,490,580,000 | xbrl:jppfs_cor:AccruedConsumptionTaxes@CurrentYearInstant | ― | - 未払消費税等:1,490百万円(同1,191百万円 |
| N185 | 未払消費税等 | 1,191 百万円 | 1,191,514,000 | xbrl:jppfs_cor:AccruedConsumptionTaxes@Prior1YearInstant | ― | - 未払消費税等:1,490百万円(同1,191百万円)、299百万円の増 |
| N186 | 未払消費税等 | 299,000,000 円 | 299,066,000 | xbrl:jppfs_cor:AccruedConsumptionTaxes@CurrentYearInstant ; xbrl:jppfs_cor:AccruedConsumptionTaxes@Prior1YearInstant ; formula:a-b | ― | - 未払消費税等:1,490百万円(同1,191百万円)、299百万円の増加 |
| N187 | 未払法人税等 | 579,000,000 円 | 579,515,000 | xbrl:jppfs_cor:IncomeTaxesPayable@CurrentYearInstant | ― | - 未払法人税等:579百万円(同687百万円)、 |
| N188 | 未払法人税等 | 687,000,000 円 | 687,368,000 | xbrl:jppfs_cor:IncomeTaxesPayable@Prior1YearInstant | ― | - 未払法人税等:579百万円(同687百万円)、107百万円の減 |
| N189 | 未払法人税等 | 107,000,000 円 | -107,853,000 | xbrl:jppfs_cor:IncomeTaxesPayable@CurrentYearInstant ; xbrl:jppfs_cor:IncomeTaxesPayable@Prior1YearInstant ; formula:a-b | ― | - 未払法人税等:579百万円(同687百万円)、107百万円の減少 |
| N190 | 契約負債 | 1,500 百万円 | 1,500,638,000 | xbrl:jppfs_cor:ContractLiabilities@CurrentYearInstant | ― | - 契約負債:1,500百万円(同1,594百万円 |
| N191 | 契約負債 | 1,594 百万円 | 1,594,084,000 | xbrl:jppfs_cor:ContractLiabilities@Prior1YearInstant | ― | - 契約負債:1,500百万円(同1,594百万円)、93百万円の減少 |
| N192 | 契約負債 | 93,000,000 円 | -93,446,000 | xbrl:jppfs_cor:ContractLiabilities@CurrentYearInstant ; xbrl:jppfs_cor:ContractLiabilities@Prior1YearInstant ; formula:a-b | ― | - 契約負債:1,500百万円(同1,594百万円)、93百万円の減少 |
| N193 | 1年内返済予定の長期借入金 | 234,000,000 円 | 234,864,000 | xbrl:jppfs_cor:CurrentPortionOfLongTermLoansPayable@CurrentYearInstant | ― | - 1年内返済予定の長期借入金:234百万円(同332百万円)、 |
| N194 | 1年内返済予定の長期借入金 | 332,000,000 円 | 332,864,000 | xbrl:jppfs_cor:CurrentPortionOfLongTermLoansPayable@Prior1YearInstant | ― | - 1年内返済予定の長期借入金:234百万円(同332百万円)、98百万円の減少 |
| N195 | 1年内返済予定の長期借入金 | 98,000,000 円 | -98,000,000 | xbrl:jppfs_cor:CurrentPortionOfLongTermLoansPayable@CurrentYearInstant ; xbrl:jppfs_cor:CurrentPortionOfLongTermLoansPayable@Prior1YearInstant ; formula:a-b | ― | 1年内返済予定の長期借入金:234百万円(同332百万円)、98百万円の減少 |
| N199 | 受注損失引当金 | 19,000,000 円 | 19,680,000 | xbrl:jppfs_cor:ProvisionForLossOnOrderReceivedCL@CurrentYearInstant | ― | - 受注損失引当金:19百万円(同18百万円)、1 |
| N200 | 受注損失引当金 | 18,000,000 円 | 18,500,000 | xbrl:jppfs_cor:ProvisionForLossOnOrderReceivedCL@Prior1YearInstant | ― | - 受注損失引当金:19百万円(同18百万円)、1百万円の増加 |
| N201 | 受注損失引当金 | 1,000,000 円 | 1,180,000 | xbrl:jppfs_cor:ProvisionForLossOnOrderReceivedCL@CurrentYearInstant ; xbrl:jppfs_cor:ProvisionForLossOnOrderReceivedCL@Prior1YearInstant ; formula:a-b | ― | - 受注損失引当金:19百万円(同18百万円)、1百万円の増加 |
| N202 | 固定負債 | 2,629 百万円 | 2,629,286,000 | xbrl:jppfs_cor:NoncurrentLiabilities@CurrentYearInstant | ― | **固定負債**は2,629百万円(前期末2,413百 |
| N203 | 固定負債 | 2,413 百万円 | 2,413,522,000 | xbrl:jppfs_cor:NoncurrentLiabilities@Prior1YearInstant | ― | **固定負債**は2,629百万円(前期末2,413百万円)と215百万円増加 |
| N204 | 固定負債 | 215,000,000 円 | 215,764,000 | xbrl:jppfs_cor:NoncurrentLiabilities@CurrentYearInstant ; xbrl:jppfs_cor:NoncurrentLiabilities@Prior1YearInstant ; formula:a-b | ― | *固定負債**は2,629百万円(前期末2,413百万円)と215百万円増加しました。 |
| N205 | 繰延税金負債 | 1,738 百万円 | 1,738,948,000 | xbrl:jppfs_cor:DeferredTaxLiabilities@CurrentYearInstant | ― | 主な内訳は、繰延税金負債1,738百万円(前期末1,290百 |
| N206 | 繰延税金負債 | 1,290 百万円 | 1,290,441,000 | xbrl:jppfs_cor:DeferredTaxLiabilities@Prior1YearInstant | ― | 主な内訳は、繰延税金負債1,738百万円(前期末1,290百万円、448百万円増)、 |
| N207 | 繰延税金負債 | 448,000,000 円 | 448,507,000 | xbrl:jppfs_cor:DeferredTaxLiabilities@CurrentYearInstant ; xbrl:jppfs_cor:DeferredTaxLiabilities@Prior1YearInstant ; formula:a-b | ― | 訳は、繰延税金負債1,738百万円(前期末1,290百万円、448百万円増)、長期借入金27 |
| N208 | 長期借入金 | 275,000,000 円 | 275,773,000 | xbrl:jppfs_cor:LongTermLoansPayable@CurrentYearInstant | ― | 百万円(前期末1,290百万円、448百万円増)、長期借入金275百万円(同510百万円、2 |
| N209 | 長期借入金 | 510,000,000 円 | 510,637,000 | xbrl:jppfs_cor:LongTermLoansPayable@Prior1YearInstant | ― | ,290百万円、448百万円増)、長期借入金275百万円(同510百万円、234百万円減)、 |
| N210 | 長期借入金 | 234,000,000 円 | -234,864,000 | xbrl:jppfs_cor:LongTermLoansPayable@CurrentYearInstant ; xbrl:jppfs_cor:LongTermLoansPayable@Prior1YearInstant ; formula:a-b | ― | 、448百万円増)、長期借入金275百万円(同510百万円、234百万円減)、資産除去債務2 |
| N211 | 資産除去債務 | 215,000,000 円 | 215,469,000 | xbrl:jppfs_cor:AssetRetirementObligationsNCL@CurrentYearInstant | ― | 275百万円(同510百万円、234百万円減)、資産除去債務215百万円(同198百万円)、 |
| N212 | 資産除去債務 | 198,000,000 円 | 198,269,000 | xbrl:jppfs_cor:AssetRetirementObligationsNCL@Prior1YearInstant | ― | 510百万円、234百万円減)、資産除去債務215百万円(同198百万円)、その他242百万 |
| N214 | 完成業務補償引当金 | 991,000,000 円 | 991,000,000 | xbrl:jpcrp030000-asr_E36539-000:ProvisionForWarrantiesForCompletedOperationCL@CurrentYearInstant | ― | また、完成業務補償引当金991百万円(前期末205百万円 |
| N215 | 完成業務補償引当金 | 205,000,000 円 | 205,000,000 | xbrl:jpcrp030000-asr_E36539-000:ProvisionForWarrantiesForCompletedOperationCL@Prior1YearInstant | ― | また、完成業務補償引当金991百万円(前期末205百万円)が前述のとおり78 |
| N216 | 完成業務補償引当金 | 786,000,000 円 | 786,000,000 | xbrl:jpcrp030000-asr_E36539-000:ProvisionForWarrantiesForCompletedOperationCL@CurrentYearInstant ; xbrl:jpcrp030000-asr_E36539-000:ProvisionForWarrantiesForCompletedOperationCL@Prior1YearInstant ; formula:a-b | ― | 務補償引当金991百万円(前期末205百万円)が前述のとおり786百万円増加しております。 |
| N218 | 長期借入金 | 275,000,000 円 | 275,773,000 | xbrl:jppfs_cor:LongTermLoansPayable@CurrentYearInstant | ― | 有利子負債は1年内返済予定分234百万円と長期借入金275百万円の合計510百万円( |
| N219 | 長期借入金 | 510,000,000 円 | 510,637,000 | xbrl:jppfs_cor:LongTermLoansPayable@Prior1YearInstant | ― | は1年内返済予定分234百万円と長期借入金275百万円の合計510百万円(前期末843百万円 |
| N222 | 純資産合計 | 17,165 百万円 | 17,165,944,000 | xbrl:jppfs_cor:NetAssets@CurrentYearInstant | ― | 純資産合計は17,165百万円となり、前期末の15 |
| N223 | 純資産合計 | 15,498 百万円 | 15,498,746,000 | xbrl:jppfs_cor:NetAssets@Prior1YearInstant | ― | 純資産合計は17,165百万円となり、前期末の15,498百万円から1,667百万円 |
| N224 | 純資産合計 | 1,667 百万円 | 1,667,198,000 | xbrl:jppfs_cor:NetAssets@CurrentYearInstant ; xbrl:jppfs_cor:NetAssets@Prior1YearInstant ; formula:a-b | ― | 計は17,165百万円となり、前期末の15,498百万円から1,667百万円、10.8%増加しま |
| N225 | 純資産合計 | 10.8 % | 10.76 | xbrl:jppfs_cor:NetAssets@CurrentYearInstant ; xbrl:jppfs_cor:NetAssets@Prior1YearInstant | ― | 万円となり、前期末の15,498百万円から1,667百万円、10.8%増加しました。 |
| N226 | 株主資本 | 14,258 百万円 | 14,258,142,000 | xbrl:jppfs_cor:ShareholdersEquity@CurrentYearInstant | ― | - 株主資本:14,258百万円(前期末13,890 |
| N227 | 株主資本 | 13,890 百万円 | 13,890,595,000 | xbrl:jppfs_cor:ShareholdersEquity@Prior1YearInstant | ― | - 株主資本:14,258百万円(前期末13,890百万円)、367百万円の増 |
| N228 | 株主資本 | 367,000,000 円 | 367,547,000 | xbrl:jppfs_cor:ShareholdersEquity@CurrentYearInstant ; xbrl:jppfs_cor:ShareholdersEquity@Prior1YearInstant ; formula:a-b | ― |  株主資本:14,258百万円(前期末13,890百万円)、367百万円の増加 |
| N229 | 資本金 | 2,000 百万円 | 2,000,000,000 | xbrl:jppfs_cor:CapitalStock@Prior1YearInstant | ― | - 資本金2,000百万円(増減なし) |
| N230 | 資本剰余金 | 1,766 百万円 | 1,766,366,000 | xbrl:jppfs_cor:CapitalSurplus@CurrentYearInstant | ― | - 資本剰余金1,766百万円(同1,696百万円 |
| N231 | 資本剰余金 | 1,696 百万円 | 1,696,099,000 | xbrl:jppfs_cor:CapitalSurplus@Prior1YearInstant | ― | - 資本剰余金1,766百万円(同1,696百万円)、70百万円増 |
| N232 | 資本剰余金 | 70,000,000 円 | 70,267,000 | xbrl:jppfs_cor:CapitalSurplus@CurrentYearInstant ; xbrl:jppfs_cor:CapitalSurplus@Prior1YearInstant ; formula:a-b | ― | - 資本剰余金1,766百万円(同1,696百万円)、70百万円増 |
| N233 | 利益剰余金 | 10,510 百万円 | 10,510,398,000 | xbrl:jppfs_cor:RetainedEarnings@CurrentYearInstant | ― | - 利益剰余金10,510百万円(同10,217百万 |
| N234 | 利益剰余金 | 10,217 百万円 | 10,217,485,000 | xbrl:jppfs_cor:RetainedEarnings@Prior1YearInstant | ― | - 利益剰余金10,510百万円(同10,217百万円)、292百万円増 |
| N235 | 利益剰余金 | 292,000,000 円 | 292,913,000 | xbrl:jppfs_cor:RetainedEarnings@CurrentYearInstant ; xbrl:jppfs_cor:RetainedEarnings@Prior1YearInstant ; formula:a-b | ― | - 利益剰余金10,510百万円(同10,217百万円)、292百万円増 |
| N236 | 自己株式 | -18,000,000 円 | -18,621,000 | xbrl:jppfs_cor:TreasuryStock@CurrentYearInstant | ― | - 自己株式△18百万円(同△22百万円) |
| N237 | 自己株式 | -22,000,000 円 | -22,989,000 | xbrl:jppfs_cor:TreasuryStock@Prior1YearInstant | ― | - 自己株式△18百万円(同△22百万円) |
| N240 | その他の包括利益 | 1,310 百万円 | 1,310,889,000 | xbrl:jppfs_cor:OtherComprehensiveIncome@CurrentYearDuration | ― | 他の包括利益累計額:2,907百万円(同1,596百万円)、1,310百万円の増加 |
| N241 | その他有価証券評価差額金 | 631,000,000 円 | 631,931,000 | xbrl:jppfs_cor:ValuationDifferenceOnAvailableForSaleSecurities@CurrentYearInstant | ― | - その他有価証券評価差額金631百万円(同414百万円) |
| N242 | その他有価証券評価差額金 | 414,000,000 円 | 414,441,000 | xbrl:jppfs_cor:ValuationDifferenceOnAvailableForSaleSecurities@Prior1YearInstant | ― | - その他有価証券評価差額金631百万円(同414百万円) |
| N243 | 繰延ヘッジ損益 | 4,000,000 円 | 4,992,000 | xbrl:jppfs_cor:DeferredGainsOrLossesOnHedges@CurrentYearInstant | ― | - 繰延ヘッジ損益4百万円 |
| N244 | 為替換算調整勘定 | -16,000,000 円 | -16,146,000 | xbrl:jppfs_cor:ForeignCurrencyTranslationAdjustment@CurrentYearInstant | ― | - 為替換算調整勘定△16百万円(同△19百万円) |
| N245 | 為替換算調整勘定 | -19,000,000 円 | -19,064,000 | xbrl:jppfs_cor:ForeignCurrencyTranslationAdjustment@Prior1YearInstant | ― | - 為替換算調整勘定△16百万円(同△19百万円) |
| N246 | 退職給付に係る調整累計額 | 2,287 百万円 | 2,287,023,000 | xbrl:jppfs_cor:RemeasurementsOfDefinedBenefitPlans@CurrentYearInstant | ― | - 退職給付に係る調整累計額2,287百万円(同1,201百万円 |
| N247 | 退職給付に係る調整累計額 | 1,201 百万円 | 1,201,534,000 | xbrl:jppfs_cor:RemeasurementsOfDefinedBenefitPlans@Prior1YearInstant | ― | - 退職給付に係る調整累計額2,287百万円(同1,201百万円) |
| N248 | 当期純利益 | 945,000,000 円 | 945,793,000 | xbrl:jppfs_cor:ProfitLoss@CurrentYearDuration | ― | 利益剰余金は当期純利益945百万円の計上と剰余金の配当 |
| N249 | 剰余金の配当 | 652,000,000 円 | -652,881,000 | xbrl:jppfs_cor:DividendsFromSurplus@CurrentYearDuration | ― | 利益剰余金は当期純利益945百万円の計上と剰余金の配当652百万円により292百万円の |
| N251 | 自己資本比率 | 61.7 % | 61.7 | xbrl:jpcrp_cor:EquityToAssetRatioSummaryOfBusinessResults@CurrentYearInstant | ― | この結果、自己資本比率は61.7%(前期末60.6%) |
| N252 | 自己資本比率 | 60.6 % | 60.6 | xbrl:jpcrp_cor:EquityToAssetRatioSummaryOfBusinessResults@Prior1YearInstant | ― | この結果、自己資本比率は61.7%(前期末60.6%)と1.1ポイント上 |
| N255 | 1株当たり純資産額 | 2,096 円 | 2,096.83 | xbrl:jpcrp_cor:NetAssetsPerShareSummaryOfBusinessResults@CurrentYearInstant | ― | 期末60.6%)と1.1ポイント上昇し、1株当たり純資産額は2,096円83銭(同1,897 |
| N256 | 1株当たり純資産額 | 1,897 円 | 1,897.74 | xbrl:jpcrp_cor:NetAssetsPerShareSummaryOfBusinessResults@Prior1YearInstant | ― | 1ポイント上昇し、1株当たり純資産額は2,096円83銭(同1,897円74銭)と199円増 |
| N257 | 1株当たり純資産額 | 199 円 | 199.09 | xbrl:jpcrp_cor:NetAssetsPerShareSummaryOfBusinessResults@CurrentYearInstant ; xbrl:jpcrp_cor:NetAssetsPerShareSummaryOfBusinessResults@Prior1YearInstant ; formula:a-b | ― | 当たり純資産額は2,096円83銭(同1,897円74銭)と199円増加しております。 |
| N258 | 現金及び現金同等物 | 2,605 百万円 | 2,605,950,000 | xbrl:jppfs_cor:CashAndCashEquivalents@CurrentYearInstant | ― | 当連結会計年度末の現金及び現金同等物(以下「資金」)は2,605百万円となり、前連結会計年 |
| N259 | 現金及び現金同等物 | 2,899 百万円 | 2,899,140,000 | xbrl:jppfs_cor:CashAndCashEquivalents@Prior1YearInstant | ― | (以下「資金」)は2,605百万円となり、前連結会計年度末の2,899百万円から293百万円減少 |
| N260 | 現金及び現金同等物 | 293,000,000 円 | -293,190,000 | xbrl:jppfs_cor:CashAndCashEquivalents@CurrentYearInstant ; xbrl:jppfs_cor:CashAndCashEquivalents@Prior1YearInstant ; formula:a-b | ― | ,605百万円となり、前連結会計年度末の2,899百万円から293百万円減少しました。 |
| N264 | 税金等調整前当期純利益 | 1,452 百万円 | 1,452,012,000 | xbrl:jppfs_cor:IncomeBeforeIncomeTaxes@CurrentYearDuration | ― | 主な内容は、税金等調整前当期純利益1,452百万円、減価償却費452百 |
| N265 | 減価償却費 | 452,000,000 円 | 452,168,000 | xbrl:jppfs_cor:DepreciationAndAmortizationOpeCF@CurrentYearDuration | ― | な内容は、税金等調整前当期純利益1,452百万円、減価償却費452百万円、のれん償却額53百 |
| N266 | のれん償却額 | 53,000,000 円 | 53,256,000 | xbrl:jppfs_cor:AmortizationOfGoodwillOpeCF@Prior1YearDuration | ― | 純利益1,452百万円、減価償却費452百万円、のれん償却額53百万円、完成業務補償引当金 |
| N267 | 完成業務補償引当金 | 786,000,000 円 | 786,000,000 | xbrl:jpcrp030000-asr_E36539-000:IncreaseDecreaseInProvisionForWarrantiesForCompletedOperationOpeCF@CurrentYearDuration | ― | 52百万円、のれん償却額53百万円、完成業務補償引当金の増加786百万円、契約資産の減少16 |
| N268 | 契約資産 | 161,000,000 円 | 161,030,000 | xbrl:jpcrp030000-asr_E36539-000:DecreaseIncreaseInContractAssetsOpeCF@CurrentYearDuration | ― | 百万円、完成業務補償引当金の増加786百万円、契約資産の減少161百万円などの収入要因に対し |
| N269 | 退職給付に係る資産 | 1,828 百万円 | -1,828,838,000 | xbrl:jppfs_cor:IncreaseDecreaseInNetDefinedBenefitAssetOpeCF@CurrentYearDuration | ― | 少161百万円などの収入要因に対し、退職給付に係る資産の増加1,828百万円、売上債権の増加80 |
| N270 | 売上債権 | 802,000,000 円 | -802,686,000 | xbrl:jppfs_cor:DecreaseIncreaseInNotesAndAccountsReceivableTradeOpeCF@CurrentYearDuration | ― | し、退職給付に係る資産の増加1,828百万円、売上債権の増加802百万円、仕入債務の減少30 |
| N271 | 仕入債務 | 300,000,000 円 | -300,297,000 | xbrl:jppfs_cor:IncreaseDecreaseInNotesAndAccountsPayableTradeOpeCF@CurrentYearDuration | ― | 1,828百万円、売上債権の増加802百万円、仕入債務の減少300百万円、契約負債の減少93 |
| N272 | 契約負債 | 93,000,000 円 | -93,465,000 | xbrl:jppfs_cor:IncreaseDecreaseInContractLiabilitiesOpeCF@CurrentYearDuration | ― | 増加802百万円、仕入債務の減少300百万円、契約負債の減少93百万円などの支出要因があり |
| N275 | 利息及び配当金の受取額 | 35,000,000 円 | 35,005,000 | xbrl:jppfs_cor:InterestAndDividendsIncomeReceivedOpeCFInvCF@CurrentYearDuration | ― | (前期4,032百万円)となり、これに利息及び配当金の受取額35百万円、利息の支払額△80 |
| N276 | 利息の支払額 | -80,000,000 円 | -80,414,000 | xbrl:jppfs_cor:InterestExpensesPaidOpeCFFinCF@CurrentYearDuration | ― | となり、これに利息及び配当金の受取額35百万円、利息の支払額△80百万円、法人税等の支払額△ |
| N277 | 法人税等の支払額 | -780,000,000 円 | -780,243,000 | xbrl:jppfs_cor:IncomeTaxesPaidOpeCF@CurrentYearDuration | ― | 受取額35百万円、利息の支払額△80百万円、法人税等の支払額△780百万円を加減しております。 |
| N278 | 税金等調整前当期純利益 | 1,255 百万円 | -1,255,859,000 | xbrl:jppfs_cor:IncomeBeforeIncomeTaxes@CurrentYearDuration ; xbrl:jppfs_cor:IncomeBeforeIncomeTaxes@Prior1YearDuration ; formula:a-b | ― | 前期からの減少の主因は、1税金等調整前当期純利益が1,255百万円減少したこと、2退職 |
| N279 | 退職給付に係る資産 | 890,000,000 円 | -890,115,000 | xbrl:jppfs_cor:IncreaseDecreaseInNetDefinedBenefitAssetOpeCF@Prior1YearDuration | ― | 255百万円減少したこと、2退職給付に係る資産の増加額が前期890百万円から当期1,828百 |
| N280 | 退職給付に係る資産 | 1,828 百万円 | -1,828,838,000 | xbrl:jppfs_cor:IncreaseDecreaseInNetDefinedBenefitAssetOpeCF@CurrentYearDuration | ― | こと、2退職給付に係る資産の増加額が前期890百万円から当期1,828百万円へと938百万円拡大 |
| N281 | 退職給付に係る資産 | 938,000,000 円 | -938,723,000 | xbrl:jppfs_cor:IncreaseDecreaseInNetDefinedBenefitAssetOpeCF@CurrentYearDuration ; xbrl:jppfs_cor:IncreaseDecreaseInNetDefinedBenefitAssetOpeCF@Prior1YearDuration ; formula:a-b | ― | る資産の増加額が前期890百万円から当期1,828百万円へと938百万円拡大したこと、3前期 |
| N282 | 売上債権 | 209,000,000 円 | 209,659,000 | xbrl:jppfs_cor:DecreaseIncreaseInNotesAndAccountsReceivableTradeOpeCF@Prior1YearDuration | ― | 828百万円へと938百万円拡大したこと、3前期は売上債権が209百万円減少したのに対し当期 |
| N284 | 売上債権 | 1,012 百万円 | -1,012,345,000 | xbrl:jppfs_cor:DecreaseIncreaseInNotesAndAccountsReceivableTradeOpeCF@CurrentYearDuration ; xbrl:jppfs_cor:DecreaseIncreaseInNotesAndAccountsReceivableTradeOpeCF@Prior1YearDuration ; formula:a-b | ― | が209百万円減少したのに対し当期は802百万円増加し、差引1,012百万円のマイナス要因となっ |
| N287 | 有形固定資産の取得による支出 | 307,000,000 円 | -307,279,000 | xbrl:jppfs_cor:PurchaseOfPropertyPlantAndEquipmentInvCF@CurrentYearDuration | ― | 主な内訳は、有形固定資産の取得による支出307百万円、無形固定資産の取得 |
| N288 | 無形固定資産の取得による支出 | 44,000,000 円 | -44,037,000 | xbrl:jppfs_cor:PurchaseOfIntangibleAssetsInvCF@CurrentYearDuration | ― | 産の取得による支出307百万円、無形固定資産の取得による支出44百万円、関係会社株式の売却 |
| N289 | 関係会社株式の売却による収入 | 9,000,000 円 | 9,834,000 | xbrl:jppfs_cor:ProceedsFromSalesOfStocksOfSubsidiariesAndAffiliatesInvCF@CurrentYearDuration | ― | 資産の取得による支出44百万円、関係会社株式の売却による収入9百万円、その他47百万円の |
| N291 | 設備投資 | 341,000,000 円 | 341,000,000 | xbrl:jpcrp_cor:CapitalExpendituresOverviewOfCapitalExpendituresEtc@CurrentYearDuration | ― | 当期の設備投資総額は341百万円であり、業務効率化の |
| N297 | 長期借入金の返済による支出 | 332,000,000 円 | -332,864,000 | xbrl:jppfs_cor:RepaymentOfLongTermLoansPayableFinCF@CurrentYearDuration | ― | 主な内訳は、長期借入金の返済による支出332百万円、配当金の支払額65 |
| N298 | 配当金の支払額 | 651,000,000 円 | -651,749,000 | xbrl:jppfs_cor:CashDividendsPaidFinCF@CurrentYearDuration | ― | 訳は、長期借入金の返済による支出332百万円、配当金の支払額651百万円、その他7百万円の支 |
| N301 | 配当金の支払額 | 529,000,000 円 | -529,177,000 | xbrl:jppfs_cor:CashDividendsPaidFinCF@Prior1YearDuration | ― | 配当金の支払額は前期の529百万円から122百万円増加 |
| N302 | 配当金の支払額 | 122,000,000 円 | -122,572,000 | xbrl:jppfs_cor:CashDividendsPaidFinCF@CurrentYearDuration ; xbrl:jppfs_cor:CashDividendsPaidFinCF@Prior1YearDuration ; formula:a-b | ― | 配当金の支払額は前期の529百万円から122百万円増加しており、株主還 |
| N303 | 現金及び預金 | 2,605 百万円 | 2,605,950,000 | xbrl:jppfs_cor:CashAndDeposits@CurrentYearInstant | ― | 当期末の現金及び預金は2,605百万円、有利子負債は510 |
| T005 | 販売費及び一般管理費 | 増加 | 566,258,000 | xbrl:jppfs_cor:SellingGeneralAndAdministrativeExpenses@CurrentYearDuration ; xbrl:jppfs_cor:SellingGeneralAndAdministrativeExpenses@Prior1YearDuration ; builtin:sign(cur-prior) | ― | 成業務補償引当金の大幅な積み増しを含む販売費及び一般管理費の増加、の二点に |
| T007 | 売上総利益 | 減少 | -684,279,000 | xbrl:jppfs_cor:GrossProfit@CurrentYearDuration ; xbrl:jppfs_cor:GrossProfit@Prior1YearDuration ; builtin:sign(cur-prior) | ― | 減益の主たる要因は、(1)売上原価率の上昇による売上総利益の減少、(2)完 |
| T008 | 退職給付に係る調整額 | 増加 | 615,185,000 | xbrl:jppfs_cor:RemeasurementsOfDefinedBenefitPlansNetOfTaxOCI@CurrentYearDuration ; xbrl:jppfs_cor:RemeasurementsOfDefinedBenefitPlansNetOfTaxOCI@Prior1YearDuration ; builtin:sign(cur-prior) | ― | 給付に係る調整額や保有株式の評価差額を含めた広義の企業価値の増加という観点 |
| T009 | 当期純利益 | 減少 | -976,788,000 | xbrl:jppfs_cor:ProfitLoss@CurrentYearDuration ; xbrl:jppfs_cor:ProfitLoss@Prior1YearDuration ; builtin:sign(cur-prior) | ― | 差額を含めた広義の企業価値の増加という観点では、当期純利益の減少ほどには毀 |
| T010 | 売上高 | 増収 | 1,088,697,000 | xbrl:jppfs_cor:NetSales@CurrentYearDuration ; xbrl:jppfs_cor:NetSales@Prior1YearDuration ; builtin:sign(cur-prior) | ― | の36,975百万円から1,088百万円、率にして2.9%の増収となりまし |
| T011 | 売上高 | 増収 | 1,088,697,000 | xbrl:jppfs_cor:NetSales@CurrentYearDuration ; xbrl:jppfs_cor:NetSales@Prior1YearDuration ; builtin:sign(cur-prior) | ― | 6,975百万円、そして当期38,064百万円と、5期連続で増収を続けてお |
| T014 | 受取手形及び売掛金 | 増加 | 804,775,000 | xbrl:jppfs_cor:NotesAndAccountsReceivableTrade@CurrentYearInstant ; xbrl:jppfs_cor:NotesAndAccountsReceivableTrade@Prior1YearInstant ; builtin:sign(cur-prior) | ― | で2,556百万円と前期末の1,751百万円から804百万円増加しており、 |
| T015 | 売上総利益 | 減少 | -684,279,000 | xbrl:jppfs_cor:GrossProfit@CurrentYearDuration ; xbrl:jppfs_cor:GrossProfit@Prior1YearDuration ; builtin:sign(cur-prior) | ― | となり、前期の12,018百万円から684百万円、5.7%の減少となりまし |
| T017 | 売上原価 | 増加 | 1,772,977,000 | xbrl:jppfs_cor:CostOfSales@CurrentYearDuration ; xbrl:jppfs_cor:CostOfSales@Prior1YearDuration ; builtin:sign(cur-prior) | ― | 増収にもかかわらず売上総利益が減少した背景には、売上原価の増加があります |
| T018 | 売上総利益 | 減少 | -684,279,000 | xbrl:jppfs_cor:GrossProfit@CurrentYearDuration ; xbrl:jppfs_cor:GrossProfit@Prior1YearDuration ; builtin:sign(cur-prior) | ― | 増収にもかかわらず売上総利益が減少した背景に |
| T019 | 売上原価 | 増加 | 1,772,977,000 | xbrl:jppfs_cor:CostOfSales@CurrentYearDuration ; xbrl:jppfs_cor:CostOfSales@Prior1YearDuration ; builtin:sign(cur-prior) | ― | 百万円(前期24,956百万円)と1,772百万円、7.1%増加しました。 |
| T020 | 売上高 | 上回 | 1,088,697,000 | xbrl:jppfs_cor:NetSales@CurrentYearDuration ; xbrl:jppfs_cor:NetSales@Prior1YearDuration ; builtin:sign(cur-prior) | ― | 売上高の伸び率2.9%を大きく上回る原価の伸 |
| T021 | 売上高 | 伸び | 1,088,697,000 | xbrl:jppfs_cor:NetSales@CurrentYearDuration ; xbrl:jppfs_cor:NetSales@Prior1YearDuration ; builtin:sign(cur-prior) | ― | 売上高の伸び率2.9% |
| T022 | 売上高 | 伸び | 1,088,697,000 | xbrl:jppfs_cor:NetSales@CurrentYearDuration ; xbrl:jppfs_cor:NetSales@Prior1YearDuration ; builtin:sign(cur-prior) | ― | 売上高の伸び率2.9%を大きく上回る原価の伸びとなった結 |
| T023 | 売上総利益 | 低下 | -684,279,000 | xbrl:jppfs_cor:GrossProfit@CurrentYearDuration ; xbrl:jppfs_cor:GrossProfit@Prior1YearDuration ; builtin:sign(cur-prior) | ― | 7ポイント上昇し、売上総利益率は32.5%から29.8%へと低下しておりま |
| T026 | 販売費及び一般管理費 | 増加 | 566,258,000 | xbrl:jppfs_cor:SellingGeneralAndAdministrativeExpenses@CurrentYearDuration ; xbrl:jppfs_cor:SellingGeneralAndAdministrativeExpenses@Prior1YearDuration ; builtin:sign(cur-prior) | ― | 万円となり、前期の9,303百万円から566百万円、6.1%増加しました。 |
| T027 | 従業員給料及び手当 | 増加 | 118,242,000 | xbrl:jppfs_cor:EmployeesSalariesAndAllowancesSGA@CurrentYearDuration ; xbrl:jppfs_cor:EmployeesSalariesAndAllowancesSGA@Prior1YearDuration ; builtin:sign(cur-prior) | ― | 手当は3,559百万円(前期3,441百万円)と118百万円増加しておりま |
| T029 | 退職給付費用 | 減少 | -18,943,000 | xbrl:jppfs_cor:RetirementBenefitExpensesSGA@CurrentYearDuration ; xbrl:jppfs_cor:RetirementBenefitExpensesSGA@Prior1YearDuration ; builtin:sign(cur-prior) | ― | 退職給付費用は118百万円(前期137百万円)と18百万円減少しました。 |
| T033 | 完成業務補償引当金 | 増加 | 786,000,000 | xbrl:jpcrp030000-asr_E36539-000:ProvisionForWarrantiesForCompletedOperationCL@CurrentYearInstant ; xbrl:jpcrp030000-asr_E36539-000:ProvisionForWarrantiesForCompletedOperationCL@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 高が991百万円となり、前期末の205百万円から786百万円増加いたしまし |
| T035 | 営業利益 | 減益 | -1,250,537,000 | xbrl:jppfs_cor:OperatingIncome@CurrentYearDuration ; xbrl:jppfs_cor:OperatingIncome@Prior1YearDuration ; builtin:sign(cur-prior) | ― | この786百万円の増加は、当期の営業利益の減益額1,25 |
| T036 | 営業利益 | 減益 | -1,250,537,000 | xbrl:jppfs_cor:OperatingIncome@CurrentYearDuration ; xbrl:jppfs_cor:OperatingIncome@Prior1YearDuration ; builtin:sign(cur-prior) | ― | 業利益の減益額1,250百万円の約6割に相当する規模であり、減益の最大の単 |
| T037 | 営業利益 | 減益 | -1,250,537,000 | xbrl:jppfs_cor:OperatingIncome@CurrentYearDuration ; xbrl:jppfs_cor:OperatingIncome@Prior1YearDuration ; builtin:sign(cur-prior) | ― | 前期の2,715百万円から1,250百万円、46.0%の大幅減益となりまし |
| T038 | 営業利益 | 低下 | -1,250,537,000 | xbrl:jppfs_cor:OperatingIncome@CurrentYearDuration ; xbrl:jppfs_cor:OperatingIncome@Prior1YearDuration ; builtin:sign(cur-prior) | ― | 上高営業利益率は前期の7.3%から3.8%へと3.5ポイント低下しておりま |
| T039 | 営業外収益 | 増加 | 14,850,000 | xbrl:jppfs_cor:NonOperatingIncome@CurrentYearDuration ; xbrl:jppfs_cor:NonOperatingIncome@Prior1YearDuration ; builtin:sign(cur-prior) | ― | 営業外収益は87百万円(前期72百万円)と14百万円増加しました。 |
| T040 | 受取利息 | 増加 | 7,609,000 | xbrl:jppfs_cor:InterestIncomeNOI@CurrentYearDuration ; xbrl:jppfs_cor:InterestIncomeNOI@Prior1YearDuration ; builtin:sign(cur-prior) | ― | 受取利息の増加は国内金利 |
| T041 | 営業外費用 | 増加 | 15,515,000 | xbrl:jppfs_cor:NonOperatingExpenses@CurrentYearDuration ; xbrl:jppfs_cor:NonOperatingExpenses@Prior1YearDuration ; builtin:sign(cur-prior) | ― | 営業外費用は95百万円(前期79百万円)と15百万円増加しました。 |
| T042 | 支払利息 | 増加 | 21,890,000 | xbrl:jppfs_cor:InterestExpensesNOE@CurrentYearDuration ; xbrl:jppfs_cor:InterestExpensesNOE@Prior1YearDuration ; builtin:sign(cur-prior) | ― | 0百万円(前期58百万円)で、金利上昇の影響により21百万円増加しておりま |
| T043 | 経常利益 | 減益 | -1,251,203,000 | xbrl:jppfs_cor:OrdinaryIncome@CurrentYearDuration ; xbrl:jppfs_cor:OrdinaryIncome@Prior1YearDuration ; builtin:sign(cur-prior) | ― | 前期2,709百万円)となり、1,251百万円、46.2%の減益となりまし |
| T044 | 親会社株主に帰属する当期純利益 | 減益 | -976,788,000 | xbrl:jppfs_cor:ProfitLossAttributableToOwnersOfParent@CurrentYearDuration ; xbrl:jppfs_cor:ProfitLossAttributableToOwnersOfParent@Prior1YearDuration ; builtin:sign(cur-prior) | ― | 円(前期1,922百万円)となり、976百万円、50.8%の減益となりまし |
| T045 | 当期純利益 | 減益 | -976,788,000 | xbrl:jppfs_cor:ProfitLoss@CurrentYearDuration ; xbrl:jppfs_cor:ProfitLoss@Prior1YearDuration ; builtin:sign(cur-prior) | ― | 当期純利益が大幅減益となった一 |
| T046 | 包括利益 | 減少 | -194,815,000 | xbrl:jppfs_cor:ComprehensiveIncome@CurrentYearDuration ; xbrl:jppfs_cor:ComprehensiveIncome@Prior1YearDuration ; builtin:sign(cur-prior) | ― | 前期2,451百万円)と、前期比では194百万円、7.9%の減少にとどまり |
| T047 | その他の包括利益 | 増加 | 781,972,000 | xbrl:jppfs_cor:OtherComprehensiveIncome@CurrentYearDuration ; xbrl:jppfs_cor:OtherComprehensiveIncome@Prior1YearDuration ; builtin:sign(cur-prior) | ― | 包括利益は1,310百万円(前期528百万円)と782百万円増加しておりま |
| T048 | 退職給付に係る資産 | 増加 | 1,828,839,000 | xbrl:jppfs_cor:NetDefinedBenefitAsset@CurrentYearInstant ; xbrl:jppfs_cor:NetDefinedBenefitAsset@Prior1YearInstant ; builtin:sign(cur-prior) | ― | これは後述する退職給付に係る資産の大幅増加と表裏一体 |
| T049 | 総資産 | 増加 | 2,281,746,000 | xbrl:jppfs_cor:Assets@CurrentYearInstant ; xbrl:jppfs_cor:Assets@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 会計年度末の25,554百万円から2,281百万円、8.9%増加しました。 |
| T050 | 流動資産 | 増加 | 409,947,000 | xbrl:jppfs_cor:CurrentAssets@CurrentYearInstant ; xbrl:jppfs_cor:CurrentAssets@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 16,943百万円(前期末16,533百万円)と409百万円増加しました。 |
| T051 | 現金及び預金 | 減少 | -293,190,000 | xbrl:jppfs_cor:CashAndDeposits@CurrentYearInstant ; xbrl:jppfs_cor:CashAndDeposits@Prior1YearInstant ; builtin:sign(cur-prior) | ― | :2,605百万円(前期末2,899百万円)、293百万円の減少 |
| T052 | 受取手形及び売掛金 | 増加 | 804,775,000 | xbrl:jppfs_cor:NotesAndAccountsReceivableTrade@CurrentYearInstant ; xbrl:jppfs_cor:NotesAndAccountsReceivableTrade@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 掛金:2,556百万円(同1,751百万円)、804百万円の増加 |
| T053 | 契約資産 | 減少 | -161,030,000 | xbrl:jppfs_cor:ContractAssets@CurrentYearInstant ; xbrl:jppfs_cor:ContractAssets@Prior1YearInstant ; builtin:sign(cur-prior) | ― | :11,267百万円(同11,428百万円)、161百万円の減少 |
| T054 | 流動資産 | 増加 | 409,947,000 | xbrl:jppfs_cor:CurrentAssets@CurrentYearInstant ; xbrl:jppfs_cor:CurrentAssets@Prior1YearInstant ; builtin:sign(cur-prior) | ― | の他の流動資産:513百万円(同454百万円)、59百万円の増加 |
| T055 | 売上債権 | 増加 | -802,686,000 | xbrl:jppfs_cor:DecreaseIncreaseInNotesAndAccountsReceivableTradeOpeCF@CurrentYearDuration ; builtin:flow_sign(cur)==direction | ― | 売上債権の増加は期末近傍 |
| T056 | 契約資産 | 減少 | -161,030,000 | xbrl:jppfs_cor:ContractAssets@CurrentYearInstant ; xbrl:jppfs_cor:ContractAssets@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 売上債権の増加は期末近傍の検収集中によるもので、契約資産の減少とあわせて |
| T057 | 固定資産 | 増加 | 1,871,798,000 | xbrl:jppfs_cor:NoncurrentAssets@CurrentYearInstant ; xbrl:jppfs_cor:NoncurrentAssets@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 前期末9,021百万円)と1,871百万円、20.7%の大幅増加となりまし |
| T058 | 有形固定資産 | 増加 | 9,123,000 | xbrl:jppfs_cor:PropertyPlantAndEquipment@CurrentYearInstant ; xbrl:jppfs_cor:PropertyPlantAndEquipment@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 資産:2,092百万円(前期末2,083百万円)、9百万円の増加 |
| T059 | 無形固定資産 | 減少 | -157,070,000 | xbrl:jppfs_cor:IntangibleAssets@CurrentYearInstant ; xbrl:jppfs_cor:IntangibleAssets@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 無形固定資産:371百万円(同528百万円)、157百万円の減少(うち、の |
| T060 | のれん | 減少 | -53,257,000 | xbrl:jppfs_cor:Goodwill@CurrentYearInstant ; xbrl:jppfs_cor:Goodwill@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 減少(うち、のれんが213百万円から159百万円へ53百万円減少) |
| T061 | 投資その他の資産 | 増加 | 2,019,745,000 | xbrl:jppfs_cor:InvestmentsAndOtherAssets@CurrentYearInstant ; xbrl:jppfs_cor:InvestmentsAndOtherAssets@Prior1YearInstant ; builtin:sign(cur-prior) | ― | :8,428百万円(同6,409百万円)、2,019百万円の増加 |
| T062 | 固定資産 | 増加 | 1,871,798,000 | xbrl:jppfs_cor:NoncurrentAssets@CurrentYearInstant ; xbrl:jppfs_cor:NoncurrentAssets@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 固定資産増加の最大の要 |
| T063 | 退職給付に係る資産 | 増加 | 1,828,839,000 | xbrl:jppfs_cor:NetDefinedBenefitAsset@CurrentYearInstant ; xbrl:jppfs_cor:NetDefinedBenefitAsset@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 6,174百万円(前期末4,345百万円)と1,828百万円増加したことで |
| T066 | 投資有価証券 | 増加 | 301,511,000 | xbrl:jppfs_cor:InvestmentSecurities@CurrentYearInstant ; xbrl:jppfs_cor:InvestmentSecurities@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 資有価証券も1,203百万円(同901百万円)と301百万円増加しました。 |
| T067 | その他有価証券評価差額金 | 増加 | 217,490,000 | xbrl:jppfs_cor:ValuationDifferenceOnAvailableForSaleSecurities@CurrentYearInstant ; xbrl:jppfs_cor:ValuationDifferenceOnAvailableForSaleSecurities@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 昇(その他有価証券評価差額金が414百万円から631百万円へ増加)および一 |
| T068 | 負債合計 | 増加 | 614,547,000 | xbrl:jppfs_cor:Liabilities@CurrentYearInstant ; xbrl:jppfs_cor:Liabilities@Prior1YearInstant ; builtin:sign(cur-prior) | ― | となり、前期末の10,055百万円から614百万円、6.1%増加しました。 |
| T069 | 流動負債 | 増加 | 398,784,000 | xbrl:jppfs_cor:CurrentLiabilities@CurrentYearInstant ; xbrl:jppfs_cor:CurrentLiabilities@Prior1YearInstant ; builtin:sign(cur-prior) | ― | *は8,041百万円(前期末7,642百万円)と398百万円増加しました。 |
| T070 | 業務未払金 | 減少 | -300,298,000 | xbrl:jppfs_cor:AccountsPayableOperatingSpecific@CurrentYearInstant ; xbrl:jppfs_cor:AccountsPayableOperatingSpecific@Prior1YearInstant ; builtin:sign(cur-prior) | ― | :1,757百万円(前期末2,057百万円)、300百万円の減少 |
| T071 | 未払消費税等 | 増加 | 299,066,000 | xbrl:jppfs_cor:AccruedConsumptionTaxes@CurrentYearInstant ; xbrl:jppfs_cor:AccruedConsumptionTaxes@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 税等:1,490百万円(同1,191百万円)、299百万円の増加 |
| T072 | 未払法人税等 | 減少 | -107,853,000 | xbrl:jppfs_cor:IncomeTaxesPayable@CurrentYearInstant ; xbrl:jppfs_cor:IncomeTaxesPayable@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 未払法人税等:579百万円(同687百万円)、107百万円の減少 |
| T073 | 契約負債 | 減少 | -93,446,000 | xbrl:jppfs_cor:ContractLiabilities@CurrentYearInstant ; xbrl:jppfs_cor:ContractLiabilities@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 約負債:1,500百万円(同1,594百万円)、93百万円の減少 |
| T074 | 1年内返済予定の長期借入金 | 減少 | -98,000,000 | xbrl:jppfs_cor:CurrentPortionOfLongTermLoansPayable@CurrentYearInstant ; xbrl:jppfs_cor:CurrentPortionOfLongTermLoansPayable@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 定の長期借入金:234百万円(同332百万円)、98百万円の減少 |
| T076 | 受注損失引当金 | 増加 | 1,180,000 | xbrl:jppfs_cor:ProvisionForLossOnOrderReceivedCL@CurrentYearInstant ; xbrl:jppfs_cor:ProvisionForLossOnOrderReceivedCL@Prior1YearInstant ; builtin:sign(cur-prior) | ― | - 受注損失引当金:19百万円(同18百万円)、1百万円の増加 |
| T077 | 固定負債 | 増加 | 215,764,000 | xbrl:jppfs_cor:NoncurrentLiabilities@CurrentYearInstant ; xbrl:jppfs_cor:NoncurrentLiabilities@Prior1YearInstant ; builtin:sign(cur-prior) | ― | *は2,629百万円(前期末2,413百万円)と215百万円増加しました。 |
| T078 | 繰延税金負債 | 増加 | 448,507,000 | xbrl:jppfs_cor:DeferredTaxLiabilities@CurrentYearInstant ; xbrl:jppfs_cor:DeferredTaxLiabilities@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 繰延税金負債の増加は、退職給 |
| T079 | 投資有価証券 | 増加 | 301,511,000 | xbrl:jppfs_cor:InvestmentSecurities@CurrentYearInstant ; xbrl:jppfs_cor:InvestmentSecurities@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 金負債の増加は、退職給付に係る資産および投資有価証券の評価益増加に対応する |
| T080 | 完成業務補償引当金 | 増加 | 786,000,000 | xbrl:jpcrp030000-asr_E36539-000:ProvisionForWarrantiesForCompletedOperationCL@CurrentYearInstant ; xbrl:jpcrp030000-asr_E36539-000:ProvisionForWarrantiesForCompletedOperationCL@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 991百万円(前期末205百万円)が前述のとおり786百万円増加しておりま |
| T081 | 長期借入金 | 減少 | -234,864,000 | xbrl:jppfs_cor:LongTermLoansPayable@CurrentYearInstant ; xbrl:jppfs_cor:LongTermLoansPayable@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 入金275百万円の合計510百万円(前期末843百万円)まで減少しており、 |
| T082 | 純資産合計 | 増加 | 1,667,198,000 | xbrl:jppfs_cor:NetAssets@CurrentYearInstant ; xbrl:jppfs_cor:NetAssets@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 、前期末の15,498百万円から1,667百万円、10.8%増加しました。 |
| T083 | 株主資本 | 増加 | 367,547,000 | xbrl:jppfs_cor:ShareholdersEquity@CurrentYearInstant ; xbrl:jppfs_cor:ShareholdersEquity@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 4,258百万円(前期末13,890百万円)、367百万円の増加 |
| T084 | その他の包括利益 | 増加 | 781,972,000 | xbrl:jppfs_cor:OtherComprehensiveIncome@CurrentYearDuration ; xbrl:jppfs_cor:OtherComprehensiveIncome@Prior1YearDuration ; builtin:sign(cur-prior) | ― | :2,907百万円(同1,596百万円)、1,310百万円の増加 |
| T086 | 1株当たり純資産額 | 増加 | 199.09 | xbrl:jpcrp_cor:NetAssetsPerShareSummaryOfBusinessResults@CurrentYearInstant ; xbrl:jpcrp_cor:NetAssetsPerShareSummaryOfBusinessResults@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 資産額は2,096円83銭(同1,897円74銭)と199円増加しておりま |
| T088 | 現金及び現金同等物 | 減少 | -293,190,000 | xbrl:jppfs_cor:CashAndCashEquivalents@CurrentYearInstant ; xbrl:jppfs_cor:CashAndCashEquivalents@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 円となり、前連結会計年度末の2,899百万円から293百万円減少しました。 |
| T092 | 完成業務補償引当金 | 増加 | 786,000,000 | xbrl:jpcrp030000-asr_E36539-000:IncreaseDecreaseInProvisionForWarrantiesForCompletedOperationOpeCF@CurrentYearDuration ; builtin:flow_sign(cur)==direction | ― | 費452百万円、のれん償却額53百万円、完成業務補償引当金の増加786百万 |
| T093 | 退職給付に係る資産 | 増加 | -1,828,838,000 | xbrl:jppfs_cor:IncreaseDecreaseInNetDefinedBenefitAssetOpeCF@CurrentYearDuration ; builtin:flow_sign(cur)==direction | ― | の減少161百万円などの収入要因に対し、退職給付に係る資産の増加1,828 |
| T094 | 売上債権 | 増加 | -802,686,000 | xbrl:jppfs_cor:DecreaseIncreaseInNotesAndAccountsReceivableTradeOpeCF@CurrentYearDuration ; builtin:flow_sign(cur)==direction | ― | に対し、退職給付に係る資産の増加1,828百万円、売上債権の増加802百万 |
| T095 | 契約資産 | 減少 | 161,030,000 | xbrl:jpcrp030000-asr_E36539-000:DecreaseIncreaseInContractAssetsOpeCF@CurrentYearDuration ; builtin:flow_sign(cur)==direction | ― | 53百万円、完成業務補償引当金の増加786百万円、契約資産の減少161百万 |
| T096 | 仕入債務 | 減少 | -300,297,000 | xbrl:jppfs_cor:IncreaseDecreaseInNotesAndAccountsPayableTradeOpeCF@CurrentYearDuration ; builtin:flow_sign(cur)==direction | ― | 増加1,828百万円、売上債権の増加802百万円、仕入債務の減少300百万 |
| T097 | 契約負債 | 減少 | -93,465,000 | xbrl:jppfs_cor:IncreaseDecreaseInContractLiabilitiesOpeCF@CurrentYearDuration ; builtin:flow_sign(cur)==direction | ― | 権の増加802百万円、仕入債務の減少300百万円、契約負債の減少93百万円 |
| T098 | 退職給付に係る資産 | 増加 | -1,828,838,000 | xbrl:jppfs_cor:IncreaseDecreaseInNetDefinedBenefitAssetOpeCF@CurrentYearDuration ; builtin:flow_sign(cur)==direction | ― | 純利益が1,255百万円減少したこと、2退職給付に係る資産の増加額が前期8 |
| T100 | 退職給付に係る資産 | 拡大 | 1,828,839,000 | xbrl:jppfs_cor:NetDefinedBenefitAsset@CurrentYearInstant ; xbrl:jppfs_cor:NetDefinedBenefitAsset@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 額が前期890百万円から当期1,828百万円へと938百万円拡大したこと、 |
| T102 | 税金等調整前当期純利益 | 減少 | -1,255,859,000 | xbrl:jppfs_cor:IncomeBeforeIncomeTaxes@CurrentYearDuration ; xbrl:jppfs_cor:IncomeBeforeIncomeTaxes@Prior1YearDuration ; builtin:sign(cur-prior) | ― | らの減少の主因は、1税金等調整前当期純利益が1,255百万円減少したこと、 |
| T103 | 売上債権 | 減少 | 209,659,000 | xbrl:jppfs_cor:DecreaseIncreaseInNotesAndAccountsReceivableTradeOpeCF@Prior1YearDuration ; builtin:flow_sign(cur)==direction | ― | へと938百万円拡大したこと、3前期は売上債権が209百万円減少したのに対 |
| T104 | 退職給付に係る資産 | 増加 | -1,828,838,000 | xbrl:jppfs_cor:IncreaseDecreaseInNetDefinedBenefitAssetOpeCF@CurrentYearDuration ; builtin:flow_sign(cur)==direction | ― | なお、2の退職給付に係る資産の増加は年金資産 |
| T105 | 退職給付に係る資産 | 増加 | -1,828,838,000 | xbrl:jppfs_cor:IncreaseDecreaseInNetDefinedBenefitAssetOpeCF@CurrentYearDuration ; builtin:flow_sign(cur)==direction | ― | ー調整項目であり、3は期末の検収集中による一時的な運転資本の増加です。 |
| T111 | 配当金の支払額 | 増加 | 122,572,000 | xbrl:jppfs_cor:CashDividendsPaidFinCF@CurrentYearDuration ; xbrl:jppfs_cor:CashDividendsPaidFinCF@Prior1YearDuration ; builtin:sign(\|cur\|-\|prior\|) | ― | 配当金の支払額は前期の529百万円から122百万円増加しており、 |

---
この報告は入口の JSON を並べ替えただけで、判定を足していない。「根拠から出た値」は engine が根拠から計算した値(直接の値は書類の単位 = 円など、率・差は文と同じ単位)。「文の値」は文の単位のまま。
