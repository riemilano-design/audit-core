# 検証の報告 ― jpcrp030000-asr-001_E27464-000_2026-06-30_01_2026-09-28.xbrl

- 道具: `adapters.xbrl.verify_document` / profile: `P16`
- 入力 ZIP の sha256: `9b695ec4541d08acbe57eb9b52e7378b61ab9d67f0d140e08bdaa62a0d0a1717`(742,337 bytes)
- 文章の差し替え: なし(書類の原文)
- engine の指紋: adapters `c413e10b4a5048e88b566ff7bb840cbd29debb394754e48cd753a6c70e4aba02` / core `34e836bb39762d5af831a9aa11d4ea095e73221beb5bd4510d3b234363a2a6e8` / git `a1c14017180bf6c33f0dd54f9fd6f2b8f379df02`

## 書類レベル

- 判定: **旗なし(書類レベルの UNVERIFIABLE には当たらない)**
- 主張の件数: **186**

| 状態 | 件数 | 割合 |
|---|---|---|
| 値が違う(VALUE_MISMATCH) | 53 | 28.5% |
| 根拠が見つからない(POINTER_NOT_FOUND) | 6 | 3.2% |
| 判定できない(UNVERIFIABLE) | 28 | 15.1% |
| 一致(GROUNDED) | 99 | 53.2% |

規則(字のまま): Claim 件数が 0 件の場合、書類レベルを UNVERIFIABLE とする。Claim 件数が 1 件以上の場合、GROUNDED 件数が 0 件、かつ POINTER_NOT_FOUND 件数 ÷ 全 Claim 件数が 0.5 を超える場合、書類レベルを UNVERIFIABLE とする。それ以外は、この規則によって UNVERIFIABLE とは判定しない。Claim 個別の state は変更しない。

## 値が違う(VALUE_MISMATCH) ― 53 件

根拠は見つかったが、文の値と根拠の値が違う。文の誤りか、結び先の誤りかは、この表では決めない。

| id | 主語 | 文の値 | 根拠から出た値 | 根拠(pointer) | 理由 | 文 |
|---|---|---|---|---|---|---|
| N007 | 経常利益 | 711,406 千円 | -639,811,000 | xbrl:jppfs_cor:OrdinaryIncome@CurrentYearDuration | ― | 74,675千円の経常利益)、親会社株主に帰属する当期純損失711,406千円(前年同期は345, |
| N008 | 経常利益 | 345,951 千円 | -639,811,000 | xbrl:jppfs_cor:OrdinaryIncome@CurrentYearDuration | ― | 親会社株主に帰属する当期純損失711,406千円(前年同期は345,951千円の親会社株主に帰属す |
| N009 | 売上高 | 7,056,648 千円 | 11,804,911,000 | xbrl:jppfs_cor:NetSales@CurrentYearDuration | ― | 以上の結果、売上高7,056,648千円(前年同期比0.8% |
| N010 | 売上高 | 0.8 % | -8.4 | xbrl:jppfs_cor:NetSales@CurrentYearDuration ; xbrl:jppfs_cor:NetSales@Prior1YearDuration | ― | 以上の結果、売上高7,056,648千円(前年同期比0.8%増)、営業利益294 |
| N011 | 営業利益 | 294,099 千円 | -521,333,000 | xbrl:jppfs_cor:OperatingIncome@CurrentYearDuration | ― | 上高7,056,648千円(前年同期比0.8%増)、営業利益294,099千円(同11.8%増)と |
| N012 | 営業利益 | 11.8 % | -198.37 | xbrl:jppfs_cor:OperatingIncome@CurrentYearDuration ; xbrl:jppfs_cor:OperatingIncome@Prior1YearDuration | ― | 千円(前年同期比0.8%増)、営業利益294,099千円(同11.8%増)となりました。 |
| N013 | 売上高 | 2,523,449 千円 | 11,804,911,000 | xbrl:jppfs_cor:NetSales@CurrentYearDuration | ― | 以上の結果、売上高2,523,449千円(前年同期比27.6 |
| N014 | 売上高 | -27.6 % | -8.4 | xbrl:jppfs_cor:NetSales@CurrentYearDuration ; xbrl:jppfs_cor:NetSales@Prior1YearDuration | ― | 以上の結果、売上高2,523,449千円(前年同期比27.6%減)、営業損失135 |
| N015 | 営業損失 | 135,305 千円 | -521,333,000 | xbrl:jppfs_cor:OperatingIncome@CurrentYearDuration | ― | 高2,523,449千円(前年同期比27.6%減)、営業損失135,305千円(前年同期は124, |
| N016 | 営業損失 | 124,763 千円 | -521,333,000 | xbrl:jppfs_cor:OperatingIncome@CurrentYearDuration | ― | 同期比27.6%減)、営業損失135,305千円(前年同期は124,763千円の営業利益)となりま |
| N020 | 売上高 | 525,423 千円 | 11,804,911,000 | xbrl:jppfs_cor:NetSales@CurrentYearDuration | ― | 以上の結果、売上高525,423千円(前年同期比15.1 |
| N021 | 売上高 | -15.1 % | -8.4 | xbrl:jppfs_cor:NetSales@CurrentYearDuration ; xbrl:jppfs_cor:NetSales@Prior1YearDuration | ― | 以上の結果、売上高525,423千円(前年同期比15.1%減)、営業利益25, |
| N022 | 営業利益 | 25,666 千円 | -521,333,000 | xbrl:jppfs_cor:OperatingIncome@CurrentYearDuration | ― | 売上高525,423千円(前年同期比15.1%減)、営業利益25,666千円(同32.2%減)と |
| N023 | 営業利益 | -32.2 % | -198.37 | xbrl:jppfs_cor:OperatingIncome@CurrentYearDuration ; xbrl:jppfs_cor:OperatingIncome@Prior1YearDuration | ― | 千円(前年同期比15.1%減)、営業利益25,666千円(同32.2%減)となりました。 |
| N024 | 売上高 | 259,831 千円 | 11,804,911,000 | xbrl:jppfs_cor:NetSales@CurrentYearDuration | ― | 以上の結果、売上高259,831千円(前年同期比6.3% |
| N025 | 売上高 | -6.3 % | -8.4 | xbrl:jppfs_cor:NetSales@CurrentYearDuration ; xbrl:jppfs_cor:NetSales@Prior1YearDuration | ― | 以上の結果、売上高259,831千円(前年同期比6.3%減)、営業損失715 |
| N026 | 営業損失 | 715,890 千円 | -521,333,000 | xbrl:jppfs_cor:OperatingIncome@CurrentYearDuration | ― | 、売上高259,831千円(前年同期比6.3%減)、営業損失715,890千円(前年同期は83,3 |
| N027 | 営業損失 | 83,351 千円 | -521,333,000 | xbrl:jppfs_cor:OperatingIncome@CurrentYearDuration | ― | 年同期比6.3%減)、営業損失715,890千円(前年同期は83,351千円の営業利益)となりま |
| N028 | 売上高 | 392,735 千円 | 11,804,911,000 | xbrl:jppfs_cor:NetSales@CurrentYearDuration | ― | 以上の結果、売上高392,735千円(前年同期比21.8 |
| N029 | 売上高 | -21.8 % | -8.4 | xbrl:jppfs_cor:NetSales@CurrentYearDuration ; xbrl:jppfs_cor:NetSales@Prior1YearDuration | ― | 以上の結果、売上高392,735千円(前年同期比21.8%減)、営業損失38, |
| N030 | 営業損失 | 38,212 千円 | -521,333,000 | xbrl:jppfs_cor:OperatingIncome@CurrentYearDuration | ― | 売上高392,735千円(前年同期比21.8%減)、営業損失38,212千円(前年同期は27,3 |
| N031 | 営業損失 | 27,398 千円 | -521,333,000 | xbrl:jppfs_cor:OperatingIncome@CurrentYearDuration | ― | 年同期比21.8%減)、営業損失38,212千円(前年同期は27,398千円の営業利益)となりま |
| N032 | 売上高 | 1,046,823 千円 | 11,804,911,000 | xbrl:jppfs_cor:NetSales@CurrentYearDuration | ― | 以上の結果、売上高1,046,823千円(前年同期比4.6% |
| N033 | 売上高 | 4.6 % | -8.4 | xbrl:jppfs_cor:NetSales@CurrentYearDuration ; xbrl:jppfs_cor:NetSales@Prior1YearDuration | ― | 以上の結果、売上高1,046,823千円(前年同期比4.6%増)、営業利益29, |
| N034 | 営業利益 | 29,431 千円 | -521,333,000 | xbrl:jppfs_cor:OperatingIncome@CurrentYearDuration | ― | 上高1,046,823千円(前年同期比4.6%増)、営業利益29,431千円(同388.6%増) |
| N035 | 営業利益 | 388.6 % | -198.37 | xbrl:jppfs_cor:OperatingIncome@CurrentYearDuration ; xbrl:jppfs_cor:OperatingIncome@Prior1YearDuration | ― | 3千円(前年同期比4.6%増)、営業利益29,431千円(同388.6%増)となりました。 |
| N036 | 流動資産 | 1,376,654 千円 | 7,048,162,000 | xbrl:jppfs_cor:CurrentAssets@CurrentYearInstant | ― | 連結会計年度末における流動資産は、前連結会計年度末と比較して1,376,654千円増加し、7,048, |
| N038 | 販売用不動産 | 1,463,505 千円 | 2,287,197,000 | xbrl:jppfs_cor:RealEstateForSale@CurrentYearInstant | ― | 主な増加要因は、販売用不動産の増加1,463,505千円、現金及び預金の増加 |
| N040 | 営業貸付金 | 275,052 千円 | 1,100,000,000 | xbrl:jppfs_cor:OperatingLoansCA@CurrentYearInstant | ― | 千円、現金及び預金の増加302,764千円、営業貸付金の増加275,052千円であります。 |
| N041 | 貸倒引当金 | 699,508 千円 | -993,151,000 | xbrl:jppfs_cor:AllowanceForDoubtfulAccountsCA@CurrentYearInstant | ― | 一方、主な減少要因は、貸倒引当金の増加699,508千円、仕掛販売用不動産の |
| N045 | リース資産 | 79,550 千円 | 752,020,000 | xbrl:jppfs_cor:LeaseAssetsPPE@CurrentYearInstant | ― | 主な増加要因は、リース資産の増加79,550千円、土地の増加60,1 |
| N046 | リース資産 | 60,121 千円 | 752,020,000 | xbrl:jppfs_cor:LeaseAssetsPPE@CurrentYearInstant | ― | 主な増加要因は、リース資産の増加79,550千円、土地の増加60,121千円、機械装置及び運搬具 |
| N047 | 機械装置及び運搬具 | 28,909 千円 | 270,523,000 | xbrl:jppfs_cor:MachineryEquipmentAndVehicles@CurrentYearInstant | ― | 0千円、土地の増加60,121千円、機械装置及び運搬具の増加28,909千円であります。 |
| N048 | 建物及び構築物 | 43,136 千円 | 2,400,994,000 | xbrl:jppfs_cor:BuildingsAndStructures@CurrentYearInstant | ― | 一方、主な減少要因は、建物及び構築物の減少43,136千円であります。 |
| N065 | 利益剰余金 | 711,406 千円 | 302,581,000 | xbrl:jppfs_cor:RetainedEarnings@CurrentYearInstant | ― | 、親会社株主に帰属する当期純損失の計上による利益剰余金の減少711,406千円、剰余金の配当82, |
| N092 | 売上高 | 7,056,648 千円 | 7,106,655,000 | xbrl:jppfs_cor:NetSales@CurrentYearDuration_jpcrp030000-asr_E27464-000ParkingReportableSegmentsMember | ― | な料金改定等による既存駐車場の活性化に注力した結果、売上高は7,056,648千円(同0.8%増)とな |
| N093 | 売上高 | 0.8 % | 1.46 | xbrl:jppfs_cor:NetSales@CurrentYearDuration_jpcrp030000-asr_E27464-000ParkingReportableSegmentsMember ; xbrl:jppfs_cor:NetSales@Prior1YearDuration_jpcrp030000-asr_E27464-000ParkingReportableSegmentsMember | ― | 場の活性化に注力した結果、売上高は7,056,648千円(同0.8%増)となりました。 |
| N094 | 売上高 | 2,523,449 千円 | 2,547,957,000 | xbrl:jppfs_cor:NetSales@CurrentYearDuration_jpcrp030000-asr_E27464-000PropertiesDevelopmentAndSalesReportableSegmentsMember | ― | 、既竣工物件と合わせて68戸の引渡しを実施した結果、売上高は2,523,449千円(同27.6%減)と |
| N095 | 売上高 | -27.6 % | -27.38 | xbrl:jppfs_cor:NetSales@CurrentYearDuration_jpcrp030000-asr_E27464-000PropertiesDevelopmentAndSalesReportableSegmentsMember ; xbrl:jppfs_cor:NetSales@Prior1YearDuration_jpcrp030000-asr_E27464-000PropertiesDevelopmentAndSalesReportableSegmentsMember | ― | 戸の引渡しを実施した結果、売上高は2,523,449千円(同27.6%減)となりました。 |
| N096 | 売上高 | 525,423 千円 | 549,817,000 | xbrl:jppfs_cor:NetSales@CurrentYearDuration_jpcrp030000-asr_E27464-000SecuritiesRetailingBusinessReportableSegmentsMember | ― | う駐車場等小口化事業は、3物件を組成し、完売した結果、売上高525,423千円(同15.1%減)と |
| N097 | 売上高 | -15.1 % | -14.51 | xbrl:jppfs_cor:NetSales@CurrentYearDuration_jpcrp030000-asr_E27464-000SecuritiesRetailingBusinessReportableSegmentsMember ; xbrl:jppfs_cor:NetSales@Prior1YearDuration_jpcrp030000-asr_E27464-000SecuritiesRetailingBusinessReportableSegmentsMember | ― | 、3物件を組成し、完売した結果、売上高525,423千円(同15.1%減)となりました。 |
| N102 | 売上高 | 1,046,823 千円 | 11,804,911,000 | xbrl:jppfs_cor:NetSales@CurrentYearDuration | ― | また、その他につきましては売上高1,046,823千円(同4.6%増)とな |
| N103 | 売上高 | 4.6 % | -8.4 | xbrl:jppfs_cor:NetSales@CurrentYearDuration ; xbrl:jppfs_cor:NetSales@Prior1YearDuration | ― | また、その他につきましては売上高1,046,823千円(同4.6%増)となりました。 |
| N106 | 売上総利益 | 277,948 千円 | 2,235,088,000 | xbrl:jppfs_cor:GrossProfit@CurrentYearDuration | ― | ,088千円となり前連結会計年度の2,513,037千円から277,948千円減少(前年同期比11 |
| N112 | 販売費及び一般管理費 | 773,361 千円 | 2,756,422,000 | xbrl:jppfs_cor:SellingGeneralAndAdministrativeExpenses@CurrentYearDuration | ― | ,422千円となり前連結会計年度の1,983,060千円から773,361千円増加(同39.0%増 |
| N119 | 受取配当金 | 40,305 千円 | 3,332,000 | xbrl:jppfs_cor:DividendsIncomeNOI@CurrentYearDuration | ― | 取利息4,309千円、受取配当金3,332千円等の計上により40,305千円(前年同期比42.6 |
| N120 | 受取配当金 | -42.6 % | 141.1 | xbrl:jppfs_cor:DividendsIncomeNOI@CurrentYearDuration ; xbrl:jppfs_cor:DividendsIncomeNOI@Prior1YearDuration | ― | 当金3,332千円等の計上により40,305千円(前年同期比42.6%減)となりました。 |
| N122 | 支払利息 | 158,783 千円 | 138,206,000 | xbrl:jppfs_cor:InterestExpensesNOE@CurrentYearDuration | ― | また、営業外費用は、支払利息138,206千円等の計上により158,783千円(同26.5%増)と |
| N123 | 支払利息 | 26.5 % | 46.51 | xbrl:jppfs_cor:InterestExpensesNOE@CurrentYearDuration ; xbrl:jppfs_cor:InterestExpensesNOE@Prior1YearDuration | ― | 払利息138,206千円等の計上により158,783千円(同26.5%増)となりました。 |
| N128 | 固定資産除却損 | 32,898 千円 | 8,000,000 | xbrl:jppfs_cor:LossOnRetirementOfNoncurrentAssetsEL@CurrentYearDuration | ― | 失24,898千円、固定資産除却損8,000千円の計上により32,898千円(前年同期比90.7 |
| T012 | 営業貸付金 | 下回 | 275,053,000 | xbrl:jppfs_cor:OperatingLoansCA@CurrentYearInstant ; xbrl:jppfs_cor:OperatingLoansCA@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 、当該医療法人の経営改善の遅れにより、回収可能額が見積り額を下回る可能性が |
| T021 | 貸倒引当金 | 増加 | -699,509,000 | xbrl:jppfs_cor:AllowanceForDoubtfulAccountsCA@CurrentYearInstant ; xbrl:jppfs_cor:AllowanceForDoubtfulAccountsCA@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 一方、主な減少要因は、貸倒引当金の増加699,5 |
| T030 | 建物及び構築物 | 減少 | 70,285,000 | xbrl:jppfs_cor:BuildingsAndStructures@CurrentYearInstant ; xbrl:jppfs_cor:BuildingsAndStructures@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 一方、主な減少要因は、建物及び構築物の減少43,13 |

## 根拠が見つからない(POINTER_NOT_FOUND) ― 6 件

文の主張に当たる根拠が書類に見つからなかった。

| id | 主語 | 文の値 | 根拠から出た値 | 根拠(pointer) | 理由 | 文 |
|---|---|---|---|---|---|---|
| N017 | ― | 155,000 千円 | ― | ― | no_element | パートナーズ第38号(神奈川県藤沢市、大分県別府市、販売総額155,000千円)」、「トラストパー |
| N018 | ― | 147,000 千円 | ― | ― | no_element | (長崎県長崎市、山口県下関市、広島県呉市及び尾道市、販売総額147,000千円)」及び「トラストパ |
| N019 | ― | 137,000 千円 | ― | ― | no_element | ートナーズ第40号(鹿児島県鹿児島市、高知県高知市、販売総額137,000千円)」を組成、完売いた |
| N109 | 売上総利益 | 0.5 ポイント | ― | ― | no_element(point without prior phrase) | 年同期比11.1%減)した結果、売上総利益率は18.9%(同0.5ポイント減)となりました。 |
| N129 | 固定資産除却損 | 90.7 % | ― | ― | no_element | 除却損8,000千円の計上により32,898千円(前年同期比90.7%増)となりました。 |
| T038 | 1年内償還予定の社債 | 減少 | ― | ― | no_element | 一方、主な減少要因は、1年内償還予定の社債の減少300,0 |

## 判定できない(UNVERIFIABLE) ― 28 件

主語や形が取れず、判定を止めた。

| id | 主語 | 文の値 | 根拠から出た値 | 根拠(pointer) | 理由 | 文 |
|---|---|---|---|---|---|---|
| N073 | ― | 672,709 千円 | ― | ― | no_subject | これは主に、税金等調整前当期純損失672,709千円、棚卸資産の増加額1 |
| N074 | ― | 1,323,185 千円 | ― | ― | no_subject | 、税金等調整前当期純損失672,709千円、棚卸資産の増加額1,323,185千円、仕入債務の増加額8 |
| N114 | ― | 521,333 千円 | ― | ― | no_subject | 以上の結果、当連結会計年度は521,333千円の営業損失(前年同期 |
| N124 | ― | 639,811 千円 | ― | ― | ambiguous(elements) | 以上の結果、当連結会計年度は639,811千円の経常損失(前年同期 |
| N130 | ― | 711,406 千円 | ― | ― | ambiguous(elements) | 以上の結果、当連結会計年度は711,406千円の親会社株主に帰属す |
| N131 | ― | 345,951 千円 | ― | ― | ambiguous(elements) | 11,406千円の親会社株主に帰属する当期純損失(前年同期は345,951千円の親会社株主に帰属す |
| N132 | ― | 3,200,000,000 円 | ― | ― | ambiguous(elements) | 締結することで手元流動性を確保しており、金融機関との間で総額32億円の契約を締結しており |
| N133 | ― | 2,000,000,000 円 | ― | ― | ambiguous(elements) | 本契約に基づく当連結会計年度末の借入実行残高は20億円であります。 |
| N134 | 経常利益 | 10 % | ― | ― | target_or_plan | 数値目標としましては、売上高経常利益率10%の達成を目標としてお |
| T001 | ― | 改善 | ― | ― | no_subject | 当連結会計年度における我が国経済は、雇用・所得環境の改善などにより |
| T004 | ― | 拡大 | ― | ― | no_subject | 及び駐車場等小口化事業における「トラストパートナーズ」の販売拡大の他、各種 |
| T005 | ― | 改善 | ― | ― | no_subject | おける「トラストパートナーズ」の販売拡大の他、各種事業の収益改善等に注力し |
| T006 | ― | 増加 | ― | ― | no_subject | の情報収集や営業体制の強化により開発が順調に推移し、車室数が増加いたしまし |
| T008 | ― | 下回 | ― | ― | target_or_plan | による消費者マインドの低下等により、引渡し実績は計画を大幅に下回る68戸( |
| T009 | ― | 低下 | ― | ― | no_subject | の高止まり、住宅ローンの金利上昇の影響による消費者マインドの低下等により、 |
| T013 | ― | 減収 | ― | ― | no_subject | たが、新車・中古車ともに販売台数が計画を下回り、前年同期比で減収・減益とな |
| T014 | ― | 減益 | ― | ― | no_subject | 新車・中古車ともに販売台数が計画を下回り、前年同期比で減収・減益となりまし |
| T015 | ― | 下回 | ― | ― | target_or_plan | ション等に注力しましたが、新車・中古車ともに販売台数が計画を下回り、前年同 |
| T017 | ― | 増加 | ― | ― | no_subject | 主な増加要因は、販 |
| T022 | ― | 減少 | ― | ― | no_subject | 一方、主な減少要因は、貸 |
| T025 | ― | 増加 | ― | ― | no_subject | 主な増加要因は、リ |
| T029 | ― | 減少 | ― | ― | no_subject | 一方、主な減少要因は、建 |
| T033 | ― | 増加 | ― | ― | no_subject | 主な増加要因は、短 |
| T037 | ― | 減少 | ― | ― | no_subject | 一方、主な減少要因は、1 |
| T040 | ― | 増加 | ― | ― | no_subject | 主な増加要因は、リ |
| T042 | ― | 減少 | ― | ― | no_subject | 一方、主な減少要因は、長 |
| T046 | ― | 減少 | ― | ― | no_subject | 主な減少要因は、親 |
| T049 | ― | 増加 | ― | ― | no_subject | は主に、税金等調整前当期純損失672,709千円、棚卸資産の増加額1,32 |

## 一致(GROUNDED) ― 99 件

文の値と根拠の値が一致した。

| id | 主語 | 文の値 | 根拠から出た値 | 根拠(pointer) | 理由 | 文 |
|---|---|---|---|---|---|---|
| N001 | 売上高 | 11,804,911 千円 | 11,804,911,000 | xbrl:jppfs_cor:NetSales@CurrentYearDuration | ― | 以上の結果、売上高11,804,911千円(前年同期比8.4% |
| N002 | 売上高 | -8.4 % | -8.4 | xbrl:jppfs_cor:NetSales@CurrentYearDuration ; xbrl:jppfs_cor:NetSales@Prior1YearDuration | ― | 以上の結果、売上高11,804,911千円(前年同期比8.4%減)、営業損失521 |
| N003 | 営業損失 | 521,333 千円 | -521,333,000 | xbrl:jppfs_cor:OperatingIncome@CurrentYearDuration | ― | 高11,804,911千円(前年同期比8.4%減)、営業損失521,333千円(前年同期は529, |
| N004 | 営業損失 | 529,976 千円 | 529,976,000 | xbrl:jppfs_cor:OperatingIncome@Prior1YearDuration | ― | 年同期比8.4%減)、営業損失521,333千円(前年同期は529,976千円の営業利益)、経常損 |
| N005 | 経常損失 | 639,811 千円 | -639,811,000 | xbrl:jppfs_cor:OrdinaryIncome@CurrentYearDuration | ― | 33千円(前年同期は529,976千円の営業利益)、経常損失639,811千円(前年同期は474, |
| N006 | 経常損失 | 474,675 千円 | 474,675,000 | xbrl:jppfs_cor:OrdinaryIncome@Prior1YearDuration | ― | 76千円の営業利益)、経常損失639,811千円(前年同期は474,675千円の経常利益)、親会社 |
| N037 | 流動資産 | 7,048,162 千円 | 7,048,162,000 | xbrl:jppfs_cor:CurrentAssets@CurrentYearInstant | ― | は、前連結会計年度末と比較して1,376,654千円増加し、7,048,162千円となりました。 |
| N039 | 現金及び預金 | 302,764 千円 | 302,764,000 | xbrl:jppfs_cor:CashAndDeposits@CurrentYearInstant ; xbrl:jppfs_cor:CashAndDeposits@Prior1YearInstant ; formula:a-b | ― | 販売用不動産の増加1,463,505千円、現金及び預金の増加302,764千円、営業貸付金の増加2 |
| N042 | 仕掛販売用不動産 | 179,082 千円 | -179,082,000 | xbrl:jppfs_cor:RealEstateForSaleInProcess@CurrentYearInstant ; xbrl:jppfs_cor:RealEstateForSaleInProcess@Prior1YearInstant ; formula:a-b | ― | 、貸倒引当金の増加699,508千円、仕掛販売用不動産の減少179,082千円であります。 |
| N043 | 固定資産 | 124,435 千円 | 124,435,000 | xbrl:jppfs_cor:NoncurrentAssets@CurrentYearInstant ; xbrl:jppfs_cor:NoncurrentAssets@Prior1YearInstant ; formula:a-b | ― | 固定資産は前連結会計年度末と比較して124,435千円増加し、3,183, |
| N044 | 固定資産 | 3,183,881 千円 | 3,183,881,000 | xbrl:jppfs_cor:NoncurrentAssets@CurrentYearInstant | ― | 定資産は前連結会計年度末と比較して124,435千円増加し、3,183,881千円となりました。 |
| N049 | 総資産 | 10,232,043 千円 | 10,232,043,000 | xbrl:jppfs_cor:Assets@CurrentYearInstant | ― | 以上の結果、総資産は10,232,043千円となり、前連結会計年 |
| N050 | 総資産 | 1,501,089 千円 | 1,501,089,000 | xbrl:jppfs_cor:Assets@CurrentYearInstant ; xbrl:jppfs_cor:Assets@Prior1YearInstant ; formula:a-b | ― | 資産は10,232,043千円となり、前連結会計年度末に比べ1,501,089千円増加しました。 |
| N051 | 流動負債 | 2,883,722 千円 | 2,883,722,000 | xbrl:jppfs_cor:CurrentLiabilities@CurrentYearInstant ; xbrl:jppfs_cor:CurrentLiabilities@Prior1YearInstant ; formula:a-b | ― | 連結会計年度末における流動負債は、前連結会計年度末と比較して2,883,722千円増加し、7,178, |
| N052 | 流動負債 | 7,178,548 千円 | 7,178,548,000 | xbrl:jppfs_cor:CurrentLiabilities@CurrentYearInstant | ― | は、前連結会計年度末と比較して2,883,722千円増加し、7,178,548千円となりました。 |
| N053 | 短期借入金 | 1,696,000 千円 | 1,696,000,000 | xbrl:jppfs_cor:ShortTermLoansPayable@CurrentYearInstant ; xbrl:jppfs_cor:ShortTermLoansPayable@Prior1YearInstant ; formula:a-b | ― | 主な増加要因は、短期借入金の増加1,696,000千円、買掛金の増加853 |
| N054 | 買掛金 | 853,794 千円 | 853,794,000 | xbrl:jppfs_cor:AccountsPayableTrade@CurrentYearInstant ; xbrl:jppfs_cor:AccountsPayableTrade@Prior1YearInstant ; formula:a-b | ― | 要因は、短期借入金の増加1,696,000千円、買掛金の増加853,794千円、1年内返済予定の長 |
| N055 | 1年内返済予定の長期借入金 | 431,011 千円 | 431,011,000 | xbrl:jppfs_cor:CurrentPortionOfLongTermLoansPayable@CurrentYearInstant ; xbrl:jppfs_cor:CurrentPortionOfLongTermLoansPayable@Prior1YearInstant ; formula:a-b | ― | 金の増加853,794千円、1年内返済予定の長期借入金の増加431,011千円であります。 |
| N056 | 1年内償還予定の社債 | 300,000 千円 | 300,000,000 | xbrl:jppfs_cor:CurrentPortionOfBonds@Prior1YearInstant | ― | 一方、主な減少要因は、1年内償還予定の社債の減少300,000千円であります。 |
| N057 | 固定負債 | 618,771 千円 | -618,771,000 | xbrl:jppfs_cor:NoncurrentLiabilities@CurrentYearInstant ; xbrl:jppfs_cor:NoncurrentLiabilities@Prior1YearInstant ; formula:a-b | ― | 固定負債は前連結会計年度末と比較して618,771千円減少し、2,599, |
| N058 | 固定負債 | 2,599,500 千円 | 2,599,500,000 | xbrl:jppfs_cor:NoncurrentLiabilities@CurrentYearInstant | ― | 定負債は前連結会計年度末と比較して618,771千円減少し、2,599,500千円となりました。 |
| N059 | リース債務 | 60,982 千円 | 60,982,000 | xbrl:jppfs_cor:LeaseObligationsNCL@CurrentYearInstant ; xbrl:jppfs_cor:LeaseObligationsNCL@Prior1YearInstant ; formula:a-b | ― | 主な増加要因は、リース債務の増加60,982千円であります。 |
| N060 | 長期借入金 | 672,874 千円 | -672,874,000 | xbrl:jppfs_cor:LongTermLoansPayable@CurrentYearInstant ; xbrl:jppfs_cor:LongTermLoansPayable@Prior1YearInstant ; formula:a-b | ― | 一方、主な減少要因は、長期借入金の減少672,874千円であります。 |
| N061 | 負債合計 | 9,778,049 千円 | 9,778,049,000 | xbrl:jppfs_cor:Liabilities@CurrentYearInstant | ― | 以上の結果、負債合計は9,778,049千円となり、前連結会計年 |
| N062 | 負債合計 | 2,264,951 千円 | 2,264,951,000 | xbrl:jppfs_cor:Liabilities@CurrentYearInstant ; xbrl:jppfs_cor:Liabilities@Prior1YearInstant ; formula:a-b | ― | 債合計は9,778,049千円となり、前連結会計年度末に比べ2,264,951千円増加しました。 |
| N063 | 純資産 | 763,861 千円 | -763,861,000 | xbrl:jppfs_cor:NetAssets@CurrentYearInstant ; xbrl:jppfs_cor:NetAssets@Prior1YearInstant ; formula:a-b | ― | 当連結会計年度末における純資産は、前連結会計年度末と比較して763,861千円減少し、453,99 |
| N064 | 純資産 | 453,994 千円 | 453,994,000 | xbrl:jppfs_cor:NetAssets@CurrentYearInstant | ― | 資産は、前連結会計年度末と比較して763,861千円減少し、453,994千円となりました。 |
| N066 | 剰余金の配当 | 82,796 千円 | -82,796,000 | xbrl:jppfs_cor:DividendsFromSurplus@CurrentYearDuration | ― | の計上による利益剰余金の減少711,406千円、剰余金の配当82,796千円であります。 |
| N067 | 自己資本比率 | 4.4 % | 4.4 | xbrl:jpcrp_cor:EquityToAssetRatioSummaryOfBusinessResults@CurrentYearInstant | ― | 以上の結果、自己資本比率は4.4%(前連結会計年度末は |
| N068 | 自己資本比率 | 13.9 % | 13.9 | xbrl:jpcrp_cor:EquityToAssetRatioSummaryOfBusinessResults@Prior1YearInstant | ― | 以上の結果、自己資本比率は4.4%(前連結会計年度末は13.9%)となりました。 |
| N069 | 現金及び現金同等物 | 302,764 千円 | 302,764,000 | xbrl:jppfs_cor:CashAndCashEquivalents@CurrentYearInstant ; xbrl:jppfs_cor:CashAndCashEquivalents@Prior1YearInstant ; formula:a-b | ― | 計年度末における現金及び現金同等物は、前連結会計年度末と比べ302,764千円増加し、2,014, |
| N070 | 現金及び現金同等物 | 2,014,581 千円 | 2,014,581,000 | xbrl:jppfs_cor:CashAndCashEquivalents@CurrentYearInstant | ― | 金同等物は、前連結会計年度末と比べ302,764千円増加し、2,014,581千円となりました。 |
| N071 | 営業活動によるキャッシュ・フロー | 259,597 千円 | -259,597,000 | xbrl:jppfs_cor:NetCashProvidedByUsedInOperatingActivities@CurrentYearDuration | ― | 営業活動によるキャッシュ・フローは、259,597千円のマイナス(前年同期 |
| N072 | 営業活動によるキャッシュ・フロー | 737,785 千円 | -737,785,000 | xbrl:jppfs_cor:NetCashProvidedByUsedInOperatingActivities@Prior1YearDuration | ― | ャッシュ・フローは、259,597千円のマイナス(前年同期は737,785千円のマイナス)となりま |
| N075 | 仕入債務 | 853,794 千円 | 853,794,000 | xbrl:jppfs_cor:IncreaseDecreaseInNotesAndAccountsPayableTradeOpeCF@CurrentYearDuration | ― | 円、棚卸資産の増加額1,323,185千円、仕入債務の増加額853,794千円、貸倒引当金の増加6 |
| N076 | 貸倒引当金 | 699,508 千円 | 699,508,000 | xbrl:jppfs_cor:IncreaseDecreaseInAllowanceForDoubtfulAccountsOpeCF@CurrentYearDuration | ― | 5千円、仕入債務の増加額853,794千円、貸倒引当金の増加699,508千円、減価償却費425, |
| N077 | 減価償却費 | 425,020 千円 | 425,020,000 | xbrl:jppfs_cor:DepreciationAndAmortizationOpeCF@CurrentYearDuration | ― | ,794千円、貸倒引当金の増加699,508千円、減価償却費425,020千円、営業貸付金の増加額 |
| N078 | 営業貸付金 | 275,052 千円 | -275,052,000 | xbrl:jppfs_cor:DecreaseIncreaseInOperatingLoansReceivableOpeCF@CurrentYearDuration | ― | 508千円、減価償却費425,020千円、営業貸付金の増加額275,052千円によるものであります |
| N079 | 投資活動によるキャッシュ・フロー | 345,731 千円 | -345,731,000 | xbrl:jpcrp_cor:NetCashProvidedByUsedInInvestingActivitiesSummaryOfBusinessResults@CurrentYearDuration | ― | 投資活動によるキャッシュ・フローは、345,731千円のマイナス(前年同期 |
| N080 | 投資活動によるキャッシュ・フロー | 225,524 千円 | -225,524,000 | xbrl:jpcrp_cor:NetCashProvidedByUsedInInvestingActivitiesSummaryOfBusinessResults@Prior1YearDuration | ― | ャッシュ・フローは、345,731千円のマイナス(前年同期は225,524千円のマイナス)となりま |
| N081 | 有形固定資産の取得による支出 | 348,590 千円 | -348,590,000 | xbrl:jppfs_cor:PurchaseOfPropertyPlantAndEquipmentInvCF@CurrentYearDuration | ― | これは主に、有形固定資産の取得による支出348,590千円によるものであります |
| N082 | 財務活動によるキャッシュ・フロー | 908,092 千円 | 908,092,000 | xbrl:jppfs_cor:NetCashProvidedByUsedInFinancingActivities@CurrentYearDuration | ― | 財務活動によるキャッシュ・フローは、908,092千円のプラス(前年同期は |
| N083 | 財務活動によるキャッシュ・フロー | 64,115 千円 | -64,115,000 | xbrl:jppfs_cor:NetCashProvidedByUsedInFinancingActivities@Prior1YearDuration | ― | キャッシュ・フローは、908,092千円のプラス(前年同期は64,115千円のマイナス)となりま |
| N084 | 短期借入金 | 1,696,000 千円 | 1,696,000,000 | xbrl:jppfs_cor:ShortTermLoansPayable@CurrentYearInstant ; xbrl:jppfs_cor:ShortTermLoansPayable@Prior1YearInstant ; formula:a-b | ― | これは主に、短期借入金の増加額1,696,000千円、長期借入金の返済に |
| N085 | 長期借入金の返済による支出 | 1,416,863 千円 | -1,416,863,000 | xbrl:jppfs_cor:RepaymentOfLongTermLoansPayableFinCF@CurrentYearDuration | ― | 金の増加額1,696,000千円、長期借入金の返済による支出1,416,863千円、長期借入れによる収 |
| N086 | 長期借入れによる収入 | 1,175,000 千円 | 1,175,000,000 | xbrl:jppfs_cor:ProceedsFromLongTermLoansPayableFinCF@CurrentYearDuration | ― | の返済による支出1,416,863千円、長期借入れによる収入1,175,000千円、社債の償還による支 |
| N087 | 社債の償還による支出 | 300,000 千円 | -300,000,000 | xbrl:jppfs_cor:RedemptionOfBondsFinCF@CurrentYearDuration | ― | 借入れによる収入1,175,000千円、社債の償還による支出300,000千円によるものであります |
| N088 | 売上高 | 11,804,911 千円 | 11,804,911,000 | xbrl:jppfs_cor:NetSales@CurrentYearDuration | ― | 当連結会計年度の売上高は、11,804,911千円となり前連結会計年度 |
| N089 | 売上高 | 12,887,524 千円 | 12,887,524,000 | xbrl:jppfs_cor:NetSales@Prior1YearDuration | ― | 度の売上高は、11,804,911千円となり前連結会計年度の12,887,524千円から1,082,61 |
| N090 | 売上高 | 1,082,613 千円 | -1,082,613,000 | xbrl:jppfs_cor:NetSales@CurrentYearDuration ; xbrl:jppfs_cor:NetSales@Prior1YearDuration ; formula:a-b | ― | 911千円となり前連結会計年度の12,887,524千円から1,082,613千円の減少(前年同期比8 |
| N091 | 売上高 | -8.4 % | -8.4 | xbrl:jppfs_cor:NetSales@CurrentYearDuration ; xbrl:jppfs_cor:NetSales@Prior1YearDuration | ― | 87,524千円から1,082,613千円の減少(前年同期比8.4%減)となりました。 |
| N098 | 売上高 | 259,831 千円 | 259,831,000 | xbrl:jppfs_cor:NetSales@CurrentYearDuration_jpcrp030000-asr_E27464-000MedicalReportableSegmentsMember | ― | 、医療機関等からの賃貸収入を中心に売上を計上した結果、売上高259,831千円(同6.3%減)とな |
| N099 | 売上高 | -6.3 % | -6.31 | xbrl:jppfs_cor:NetSales@CurrentYearDuration_jpcrp030000-asr_E27464-000MedicalReportableSegmentsMember ; xbrl:jppfs_cor:NetSales@Prior1YearDuration_jpcrp030000-asr_E27464-000MedicalReportableSegmentsMember | ― | 収入を中心に売上を計上した結果、売上高259,831千円(同6.3%減)となりました。 |
| N100 | 売上高 | 392,735 千円 | 392,735,000 | xbrl:jppfs_cor:NetSales@CurrentYearDuration_jpcrp030000-asr_E27464-000RVReportableSegmentsMember | ― | の製造、販売及び修理・リノベーション等に注力した結果、売上高392,735千円(同21.8%減)と |
| N101 | 売上高 | -21.8 % | -21.78 | xbrl:jppfs_cor:NetSales@CurrentYearDuration_jpcrp030000-asr_E27464-000RVReportableSegmentsMember ; xbrl:jppfs_cor:NetSales@Prior1YearDuration_jpcrp030000-asr_E27464-000RVReportableSegmentsMember | ― | リノベーション等に注力した結果、売上高392,735千円(同21.8%減)となりました。 |
| N104 | 売上総利益 | 2,235,088 千円 | 2,235,088,000 | xbrl:jppfs_cor:GrossProfit@CurrentYearDuration | ― | 当連結会計年度の売上総利益は、2,235,088千円となり前連結会計年度 |
| N105 | 売上総利益 | 2,513,037 千円 | 2,513,037,000 | xbrl:jppfs_cor:GrossProfit@Prior1YearDuration | ― | の売上総利益は、2,235,088千円となり前連結会計年度の2,513,037千円から277,948千 |
| N107 | 売上総利益 | -11.1 % | -11.06 | xbrl:jppfs_cor:GrossProfit@CurrentYearDuration ; xbrl:jppfs_cor:GrossProfit@Prior1YearDuration | ― | 2,513,037千円から277,948千円減少(前年同期比11.1%減)した結果、売上総 |
| N108 | 売上総利益率 | 18.9 % | 18.93 | xbrl:jppfs_cor:GrossProfit@CurrentYearDuration ; xbrl:jppfs_cor:NetSales@CurrentYearDuration ; formula:a/b*100 | ― | 8千円減少(前年同期比11.1%減)した結果、売上総利益率は18.9%(同0.5ポイント減 |
| N110 | 販売費及び一般管理費 | 2,756,422 千円 | 2,756,422,000 | xbrl:jppfs_cor:SellingGeneralAndAdministrativeExpenses@CurrentYearDuration | ― | 一方、販売費及び一般管理費は、2,756,422千円となり前連結会計年度 |
| N111 | 販売費及び一般管理費 | 1,983,060 千円 | 1,983,060,000 | xbrl:jppfs_cor:SellingGeneralAndAdministrativeExpenses@Prior1YearDuration | ― | び一般管理費は、2,756,422千円となり前連結会計年度の1,983,060千円から773,361千 |
| N113 | 販売費及び一般管理費 | 39 % | 39 | xbrl:jppfs_cor:SellingGeneralAndAdministrativeExpenses@CurrentYearDuration ; xbrl:jppfs_cor:SellingGeneralAndAdministrativeExpenses@Prior1YearDuration | ― | 計年度の1,983,060千円から773,361千円増加(同39.0%増)しました。 |
| N115 | 営業損失 | 529,976 千円 | 529,976,000 | xbrl:jppfs_cor:OperatingIncome@Prior1YearDuration | ― | 果、当連結会計年度は521,333千円の営業損失(前年同期は529,976千円の営業利益)となりま |
| N116 | 受取保険金 | 11,337 千円 | 11,337,000 | xbrl:jppfs_cor:InsuranceIncomeNOI@CurrentYearDuration | ― | 当連結会計年度の営業外収益は、受取保険金11,337千円、受取利息4,309 |
| N117 | 受取利息 | 4,309 千円 | 4,309,000 | xbrl:jppfs_cor:InterestIncomeNOI@CurrentYearDuration | ― | 会計年度の営業外収益は、受取保険金11,337千円、受取利息4,309千円、受取配当金3,33 |
| N118 | 受取配当金 | 3,332 千円 | 3,332,000 | xbrl:jppfs_cor:DividendsIncomeNOI@CurrentYearDuration | ― | 取保険金11,337千円、受取利息4,309千円、受取配当金3,332千円等の計上により40, |
| N121 | 支払利息 | 138,206 千円 | 138,206,000 | xbrl:jppfs_cor:InterestExpensesNOE@CurrentYearDuration | ― | また、営業外費用は、支払利息138,206千円等の計上により158 |
| N125 | 経常損失 | 474,675 千円 | 474,675,000 | xbrl:jppfs_cor:OrdinaryIncome@Prior1YearDuration | ― | 果、当連結会計年度は639,811千円の経常損失(前年同期は474,675千円の経常利益)となりま |
| N126 | 減損損失 | 24,898 千円 | 24,898,000 | xbrl:jppfs_cor:ImpairmentLossEL@CurrentYearDuration | ― | 当連結会計年度の特別損失は、減損損失24,898千円、固定資産除却損8, |
| N127 | 固定資産除却損 | 8,000 千円 | 8,000,000 | xbrl:jppfs_cor:LossOnRetirementOfNoncurrentAssetsEL@CurrentYearDuration | ― | 計年度の特別損失は、減損損失24,898千円、固定資産除却損8,000千円の計上により32,8 |
| T011 | 営業貸付金 | 改善 | 275,053,000 | xbrl:jppfs_cor:OperatingLoansCA@CurrentYearInstant ; xbrl:jppfs_cor:OperatingLoansCA@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 一方で、医療法人への営業貸付金について、当該医療法人の経営改善の遅れによ |
| T016 | 流動資産 | 増加 | 1,376,655,000 | xbrl:jppfs_cor:CurrentAssets@CurrentYearInstant ; xbrl:jppfs_cor:CurrentAssets@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 流動資産は、前連結会計年度末と比較して1,376,654千円増加し、7,0 |
| T018 | 販売用不動産 | 増加 | 1,463,506,000 | xbrl:jppfs_cor:RealEstateForSale@CurrentYearInstant ; xbrl:jppfs_cor:RealEstateForSale@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 主な増加要因は、販売用不動産の増加1,463 |
| T019 | 現金及び預金 | 増加 | 302,764,000 | xbrl:jppfs_cor:CashAndDeposits@CurrentYearInstant ; xbrl:jppfs_cor:CashAndDeposits@Prior1YearInstant ; builtin:sign(cur-prior) | ― | は、販売用不動産の増加1,463,505千円、現金及び預金の増加302,7 |
| T020 | 営業貸付金 | 増加 | 275,053,000 | xbrl:jppfs_cor:OperatingLoansCA@CurrentYearInstant ; xbrl:jppfs_cor:OperatingLoansCA@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 05千円、現金及び預金の増加302,764千円、営業貸付金の増加275,0 |
| T023 | 仕掛販売用不動産 | 減少 | -179,082,000 | xbrl:jppfs_cor:RealEstateForSaleInProcess@CurrentYearInstant ; xbrl:jppfs_cor:RealEstateForSaleInProcess@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 因は、貸倒引当金の増加699,508千円、仕掛販売用不動産の減少179,0 |
| T024 | 固定資産 | 増加 | 124,435,000 | xbrl:jppfs_cor:NoncurrentAssets@CurrentYearInstant ; xbrl:jppfs_cor:NoncurrentAssets@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 固定資産は前連結会計年度末と比較して124,435千円増加し、3,1 |
| T026 | リース資産 | 増加 | 77,613,000 | xbrl:jppfs_cor:LeaseAssetsPPE@CurrentYearInstant ; xbrl:jppfs_cor:LeaseAssetsPPE@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 主な増加要因は、リース資産の増加79,55 |
| T027 | リース資産 | 増加 | 77,613,000 | xbrl:jppfs_cor:LeaseAssetsPPE@CurrentYearInstant ; xbrl:jppfs_cor:LeaseAssetsPPE@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 主な増加要因は、リース資産の増加79,550千円、土地の増加60,12 |
| T028 | 機械装置及び運搬具 | 増加 | 38,080,000 | xbrl:jppfs_cor:MachineryEquipmentAndVehicles@CurrentYearInstant ; xbrl:jppfs_cor:MachineryEquipmentAndVehicles@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 550千円、土地の増加60,121千円、機械装置及び運搬具の増加28,90 |
| T031 | 総資産 | 増加 | 1,501,089,000 | xbrl:jppfs_cor:Assets@CurrentYearInstant ; xbrl:jppfs_cor:Assets@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 43千円となり、前連結会計年度末に比べ1,501,089千円増加しました。 |
| T032 | 流動負債 | 増加 | 2,883,722,000 | xbrl:jppfs_cor:CurrentLiabilities@CurrentYearInstant ; xbrl:jppfs_cor:CurrentLiabilities@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 流動負債は、前連結会計年度末と比較して2,883,722千円増加し、7,1 |
| T034 | 短期借入金 | 増加 | 1,696,000,000 | xbrl:jppfs_cor:ShortTermLoansPayable@CurrentYearInstant ; xbrl:jppfs_cor:ShortTermLoansPayable@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 主な増加要因は、短期借入金の増加1,696 |
| T035 | 買掛金 | 増加 | 853,794,000 | xbrl:jppfs_cor:AccountsPayableTrade@CurrentYearInstant ; xbrl:jppfs_cor:AccountsPayableTrade@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 増加要因は、短期借入金の増加1,696,000千円、買掛金の増加853,7 |
| T036 | 1年内返済予定の長期借入金 | 増加 | 431,011,000 | xbrl:jppfs_cor:CurrentPortionOfLongTermLoansPayable@CurrentYearInstant ; xbrl:jppfs_cor:CurrentPortionOfLongTermLoansPayable@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 買掛金の増加853,794千円、1年内返済予定の長期借入金の増加431,0 |
| T039 | 固定負債 | 減少 | -618,771,000 | xbrl:jppfs_cor:NoncurrentLiabilities@CurrentYearInstant ; xbrl:jppfs_cor:NoncurrentLiabilities@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 固定負債は前連結会計年度末と比較して618,771千円減少し、2,5 |
| T041 | リース債務 | 増加 | 27,726,000 | xbrl:jppfs_cor:LeaseObligationsCL@CurrentYearInstant ; xbrl:jppfs_cor:LeaseObligationsCL@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 主な増加要因は、リース債務の増加60,98 |
| T043 | 長期借入金 | 減少 | -672,874,000 | xbrl:jppfs_cor:LongTermLoansPayable@CurrentYearInstant ; xbrl:jppfs_cor:LongTermLoansPayable@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 一方、主な減少要因は、長期借入金の減少672,8 |
| T044 | 負債合計 | 増加 | 2,264,951,000 | xbrl:jppfs_cor:Liabilities@CurrentYearInstant ; xbrl:jppfs_cor:Liabilities@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 49千円となり、前連結会計年度末に比べ2,264,951千円増加しました。 |
| T045 | 純資産 | 減少 | -763,861,000 | xbrl:jppfs_cor:NetAssets@CurrentYearInstant ; xbrl:jppfs_cor:NetAssets@Prior1YearInstant ; builtin:sign(cur-prior) | ― | おける純資産は、前連結会計年度末と比較して763,861千円減少し、453 |
| T047 | 利益剰余金 | 減少 | -794,203,000 | xbrl:jppfs_cor:RetainedEarnings@CurrentYearInstant ; xbrl:jppfs_cor:RetainedEarnings@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 因は、親会社株主に帰属する当期純損失の計上による利益剰余金の減少711,4 |
| T048 | 現金及び現金同等物 | 増加 | 302,764,000 | xbrl:jppfs_cor:CashAndCashEquivalents@CurrentYearInstant ; xbrl:jppfs_cor:CashAndCashEquivalents@Prior1YearInstant ; builtin:sign(cur-prior) | ― | 金及び現金同等物は、前連結会計年度末と比べ302,764千円増加し、2,0 |
| T050 | 仕入債務 | 増加 | 853,794,000 | xbrl:jppfs_cor:IncreaseDecreaseInNotesAndAccountsPayableTradeOpeCF@CurrentYearDuration ; builtin:flow_sign(cur)==direction | ― | 09千円、棚卸資産の増加額1,323,185千円、仕入債務の増加額853, |
| T051 | 貸倒引当金 | 増加 | 699,508,000 | xbrl:jppfs_cor:IncreaseDecreaseInAllowanceForDoubtfulAccountsOpeCF@CurrentYearDuration ; builtin:flow_sign(cur)==direction | ― | 185千円、仕入債務の増加額853,794千円、貸倒引当金の増加699,5 |
| T052 | 営業貸付金 | 増加 | -275,052,000 | xbrl:jppfs_cor:DecreaseIncreaseInOperatingLoansReceivableOpeCF@CurrentYearDuration ; builtin:flow_sign(cur)==direction | ― | 99,508千円、減価償却費425,020千円、営業貸付金の増加額275, |
| T053 | 短期借入金 | 増加 | 1,696,000,000 | xbrl:jppfs_cor:ShortTermLoansPayable@CurrentYearInstant ; xbrl:jppfs_cor:ShortTermLoansPayable@Prior1YearInstant ; builtin:sign(cur-prior) | ― | これは主に、短期借入金の増加額1,69 |
| T054 | 売上高 | 減少 | -1,082,613,000 | xbrl:jppfs_cor:NetSales@CurrentYearDuration ; xbrl:jppfs_cor:NetSales@Prior1YearDuration ; builtin:sign(cur-prior) | ― | 計年度の12,887,524千円から1,082,613千円の減少(前年同期 |
| T055 | 売上総利益 | 減少 | -277,949,000 | xbrl:jppfs_cor:GrossProfit@CurrentYearDuration ; xbrl:jppfs_cor:GrossProfit@Prior1YearDuration ; builtin:sign(cur-prior) | ― | 前連結会計年度の2,513,037千円から277,948千円減少(前年同期 |
| T056 | 販売費及び一般管理費 | 増加 | 773,362,000 | xbrl:jppfs_cor:SellingGeneralAndAdministrativeExpenses@CurrentYearDuration ; xbrl:jppfs_cor:SellingGeneralAndAdministrativeExpenses@Prior1YearDuration ; builtin:sign(cur-prior) | ― | 前連結会計年度の1,983,060千円から773,361千円増加(同39. |

---
この報告は入口の JSON を並べ替えただけで、判定を足していない。「根拠から出た値」は engine が根拠から計算した値(直接の値は書類の単位 = 円など、率・差は文と同じ単位)。「文の値」は文の単位のまま。
