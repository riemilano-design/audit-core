# XBRL 探り 3 本目(同じ書類で member 束縛だけを変数にした)の実測と、封じた予測との照合(2026-10-06、司令塔)

**追跡**

| 項目 | 値 |
|---|---|
| 予測の封 | [XBRL_PROBE3_PREDICTION_2026-10-06.md](XBRL_PROBE3_PREDICTION_2026-10-06.md)、コミット **`9651eca5129dba7efaaf3562463c7e78258c5698`**(2026-10-06 12:06:31 +0900)、sha256 `2357a45e726b1ff0dfdb022b2af8f123bcd3ce9f4ae436cf9b22d73eb85f9070`。**封じた後に変えていない** |
| script | `probe_xbrl_2026-10-06/xbrl_probe3.py`(コミット `a5bca12`、sha256 `3d2092a9b4f9793de02c6af7fd7241ee68b5398c2d4ab3ae294e34747eed136b`)。2 本目の `xbrl_probe.py` は sha `896492a7…` のまま不変。語彙 73・P-1〜P-7・正規表現・Claim の抽出・主語の取り方は不変(import して使っている) |
| byte freeze gate(§5) | `PROBE_MEMBER=0` の出力 sha256 **`73f413f228f62ec9528e42bd866cfd162e4336c94206a9e93f9d48f412752c20`** = 2 本目の `probe2B_S100Z4B6.json` と `cmp` で byte 一致。通過後に Run L を回した |
| Run L の証跡 | [probe_xbrl_2026-10-06/probe3L_S100Z4B6.json](probe_xbrl_2026-10-06/probe3L_S100Z4B6.json)(sha256 `168edc63ed53807183b57e184ff26de512037f20a4224769e1a1c94ae1e992d3`)。**1 回だけ回した。** 鍵も API も使っていない(保管 ZIP sha `d617b6e1…` を照合して読んだ) |
| Run R | **未実施**(人の手書きの登録簿は作っていない) |
| Core | 触っていない |

## 1. 何を変え、何を変えなかったか(Run L)

変えたのは予測 §3 の 2 つだけ。**A 構造の規則**: member 付き context を `population` の値として読む(文の中の事業名がちょうど 1 つ → その member。候補の fact は `members == [member]` の連結 context に**置き換え**、member 無しの context と合わせない。前期比は両期に同じ member を要求)。**B 対応の登録**: ZIP の中の会社拡張 label linkbase から標準ラベル(role `…/label`、`xml:lang="ja"`)を機械で引き、NFKC で正規化したラベルが MD&A の本文に現れる member だけを登録簿に入れた。**人は 1 行も書いていない。**

| 変わらなかったもの | 根拠 |
|---|---|
| 数の Claim 91 件・文章の Claim 42 件・再計算対象 18 件 | 抽出規則が凍結なので件数は同じ |
| form の分布(direct 72 / derived 19) | 同じ |
| 層・form・modifier・scheme | 増分 **0 / 0 / 0 / 0**(`schemes_used` = builtin / formula / xbrl のまま。member は `xbrl:` の locator の context 名に写っただけ) |
| `value_only` の 5 件 | 5 件とも同じ fact に GROUNDED(§4) |
| member が付かなかった文の Claim | 1 件も動いていない(動いたのは member が付いた文と `ambiguous(member)` の文だけ。§6 の表) |

## 2. 20 件の ID 表(予測 §1.3 で固定した分母)

ptr は Run L の束縛先。fact は人が XBRL で確かめられるように、要素・context・値・decimals・期間を §3 に書いた。

| ID | 文 | 主語(凍結) | form | 文の値 | 2 本目 | **3 本目 Run L** | member(事業) | 束縛元 | 根拠 |
|---|---|---|---|---|---|---|---|---|---|
| N017 | 31 | 売上高 | direct | 958,229 千円 | VALUE_MISMATCH | **GROUNDED** | 直営サロン運営事業 | sentence | `jppfs_cor:NetSales@CurrentYearDuration_…DirectSalonReportableSegmentMember` = 958,229,000(round) |
| N018 | 31 | 売上高 | derived(前期比) | +3.3% | VALUE_MISMATCH | **GROUNDED** | 直営サロン運営事業 | sentence | 958,229 / 927,625 − 1 = +3.30% |
| N019 | 31 | 売上高(実は セグメント利益) | direct | 32,925 千円 | VALUE_MISMATCH | VALUE_MISMATCH | 直営サロン運営事業 | sentence | member の NetSales 958,229 ≠ 32,925。主語が語彙に無い |
| N020 | 31 | 売上高(実は セグメント利益) | derived | −42.5% | VALUE_MISMATCH | VALUE_MISMATCH | 直営サロン運営事業 | sentence | NetSales の前期比 +3.3 ≠ −42.5 |
| N031 | 38 | 売上高 | direct | 221,898 千円 | VALUE_MISMATCH | **GROUNDED** | BS サロン運営事業 | sentence | `NetSales@…FranchiseReportableSegmentMember` = 221,898,000 |
| N032 | 38 | 売上高 | derived | −2.7% | VALUE_MISMATCH | **GROUNDED** | BS サロン運営事業 | sentence | 221,898 / 228,013 − 1 = −2.68% |
| N033 | 38 | 売上高(セグメント利益) | direct | 62,407 千円 | VALUE_MISMATCH | VALUE_MISMATCH | BS サロン運営事業 | sentence | 同上の理由 |
| N034 | 38 | 売上高(セグメント利益) | derived | −11.8% | VALUE_MISMATCH | VALUE_MISMATCH | BS サロン運営事業 | sentence | 同上 |
| N036 | 42 | 売上高 | direct | 382,711 千円 | VALUE_MISMATCH | **GROUNDED** | ヘアメイク事業 | sentence | `NetSales@…HairMakeReportableSegmentMember` = 382,711,000 |
| N037 | 42 | 売上高 | derived | +2.2% | VALUE_MISMATCH | **GROUNDED** | ヘアメイク事業 | sentence | 382,711 / 374,589 − 1 = +2.17% |
| N038 | 42 | 売上高(セグメント利益) | direct | 14,953 千円 | VALUE_MISMATCH | VALUE_MISMATCH | ヘアメイク事業 | sentence | 同上 |
| N039 | 42 | 売上高(セグメント利益) | derived | +19.2% | VALUE_MISMATCH | VALUE_MISMATCH | ヘアメイク事業 | sentence | 同上 |
| N040 | 47 | 売上高 | direct | 122,230 千円 | VALUE_MISMATCH | **GROUNDED** | 美容室支援事業 | sentence | `NetSales@…BeautyBusinessSupportBusinessReportableSegmentMember` = 122,230,000 |
| N041 | 47 | 売上高 | derived | +1.1% | VALUE_MISMATCH | **GROUNDED** | 美容室支援事業 | sentence | 122,230 / 120,875 − 1 = +1.12% |
| N042 | 47 | 売上高(セグメント利益) | direct | 76,608 千円 | VALUE_MISMATCH | VALUE_MISMATCH | 美容室支援事業 | sentence | 同上 |
| N043 | 47 | 売上高(セグメント利益) | derived | −2.2% | VALUE_MISMATCH | VALUE_MISMATCH | 美容室支援事業 | sentence | 同上 |
| N044 | 50 | 売上高 | direct | 253,763 千円 | VALUE_MISMATCH | **GROUNDED** | キャリアデザイン事業 | sentence | `NetSales@…CareerDesignReportableSegmentMember` = 253,763,000 |
| N045 | 50 | 売上高 | derived | −8.6% | VALUE_MISMATCH | **GROUNDED** | キャリアデザイン事業 | sentence | 253,763 / 277,758 − 1 = −8.64% |
| N046 | 50 | 売上高(セグメント利益) | direct | 14,224 千円 | VALUE_MISMATCH | VALUE_MISMATCH | キャリアデザイン事業 | sentence | 同上 |
| N047 | 50 | 売上高(セグメント利益) | derived | +7.6% | VALUE_MISMATCH | VALUE_MISMATCH | キャリアデザイン事業 | sentence | 同上 |

**20 件中 GROUNDED 10(売上高の直接 5 + 前期比 5)、VALUE_MISMATCH 10(セグメント利益の 10 件。主語が「売上高」のまま member の NetSales と比べられて不一致 = 止まる側)。** `ambiguous(member)` 0、`no_prior_member_context` 0、引き継ぎ(carried)で決まったもの 0(5 文とも事業名が文の中に在った)。

## 3. 新たに GROUNDED になった全件(10 件)の正準の fact(人が読んで確かめた)

すべて `jppfs_cor:NetSales`、unit JPY、`decimals="-3"`(千円精度)、member はちょうど 1 つ。当期 2025-07-01〜2026-06-30、前期 2024-07-01〜2025-06-30。

| 事業(member) | 当期 NetSales | 前期 NetSales | 文の値(当期) | 一致 | 文の前期比 | 再計算 | 一致(±0.15) |
|---|---:|---:|---:|---|---:|---:|---|
| 直営サロン運営事業(`DirectSalonReportableSegmentMember`) | 958,229,000 | 927,625,000 | 958,229 千円 | round | +3.3% | +3.30% | ○ |
| BS サロン運営事業(`FranchiseReportableSegmentMember`) | 221,898,000 | 228,013,000 | 221,898 千円 | round | −2.7% | −2.68% | ○ |
| ヘアメイク事業(`HairMakeReportableSegmentMember`) | 382,711,000 | 374,589,000 | 382,711 千円 | round | +2.2% | +2.17% | ○ |
| 美容室支援事業(`BeautyBusinessSupportBusinessReportableSegmentMember`) | 122,230,000 | 120,875,000 | 122,230 千円 | round | +1.1% | +1.12% | ○ |
| キャリアデザイン事業(`CareerDesignReportableSegmentMember`) | 253,763,000 | 277,758,000 | 253,763 千円 | round | −8.6% | −8.64% | ○ |

判定の根拠(Claim 単位): 直接値は `match_value` の `round`(|fact − 文の値 × 1000| ≤ 500 円。切捨てではなく丸めで一致)、前期比は凍結の式 `(cur − prior) / |prior| × 100` と文の値の差が 0.15 ポイント以内。文の事業名と fact の member のラベルは同じ語。**連結の総額(`NetSalesSummaryOfBusinessResults@CurrentYearDuration` = 1,850,502,000)は 10 件のどれにも使っていない**(§6 の pointer が全部 member 付き context)。

## 4. `value_only` 5 件の全件確認

| ID | 文の値 | 2 本目の fact | 3 本目の fact | 変化 |
|---|---:|---|---|---|
| N052 | 102,694 千円(税金等調整前当期純損失) | `jppfs_cor:IncomeBeforeIncomeTaxes@CurrentYearDuration` = −102,694,000 | 同じ | なし |
| N065 | 150,000 千円(短期借入金の増加額) | `IncreaseDecreaseInShortTermLoansPayableFinCF@CurrentYearDuration` = 150,000,000 | 同じ | なし |
| N073 | 1,377,499 千円(売上原価) | `CostOfSales@CurrentYearDuration` = 1,377,499,000 | 同じ | なし |
| N080 | 4,171 千円(営業外収益) | `NonOperatingIncome@CurrentYearDuration` = 4,171,000 | 同じ | なし |
| N081 | 50,551 千円(営業外費用) | `NonOperatingExpenses@CurrentYearDuration` = 50,551,000 | 同じ | なし |

5 件とも member の付かない文にあり(member None)、候補の母集団は 2 本目と同じ連結の context。ambiguous 化 **0**。5 件とも主語なしだが、値と文の語(税金等調整前当期純損失・短期借入金の増加額・売上原価・営業外収益・営業外費用)は fact の要素名と人が読んで一致する。

## 5. member の表(対応表の出どころ。分母は予測 §3.2 の定義どおり、結果を見て変えていない)

**分母 = 19**(当期または前期の連結の Duration context に現れる `explicitMember` の異なり数)。label linkbase は ZIP の `XBRL/PublicDoc/jpcrp030000-asr-001_E05055-000_2026-06-30_01_2026-09-29_lab.xml` の 1 本。

| member | 標準ラベル(ja、role `…/label`) | 本文に現れる | 出どころ | 当期 / 前期の context | 用途 |
|---|---|---|---|---|---|
| `…:DirectSalonReportableSegmentMember` | 直営サロン運営事業 | ○ | **label(自動)** | ○ / ○ | 事業セグメント |
| `…:FranchiseReportableSegmentMember` | ＢＳサロン運営事業 → NFKC「BSサロン運営事業」 | ○ | **label(自動)** | ○ / ○ | 事業セグメント |
| `…:HairMakeReportableSegmentMember` | ヘアメイク事業 | ○ | **label(自動)** | ○ / ○ | 事業セグメント |
| `…:BeautyBusinessSupportBusinessReportableSegmentMember` | 美容室支援事業 | ○ | **label(自動)** | ○ / ○ | 事業セグメント |
| `…:CareerDesignReportableSegmentMember` | キャリアデザイン事業 | ○ | **label(自動)** | ○ / ○ | 事業セグメント |
| `jpcrp_cor:ReportableSegmentsMember` / `ReconcilingItemsMember` / `UnallocatedAmountsAndEliminationMember` | (標準タクソノミ。ZIP にラベル無し) | ― | なし | 計・調整額・消去 | セグメント注記の合計行 |
| `jpcrp_cor:DirectorsExcludingOutsideDirectorsMember` / `CorporateAuditorsExcludingOutsideCorporateAuditorsMember` / `OutsideDirectorsAndOtherOfficersMember` | (標準。ラベル無し) | ― | なし | 役員報酬の区分 | セグメントではない |
| `jppfs_cor:ShareholdersEquityMember` / `CapitalStockMember` / `CapitalSurplusMember` / `RetainedEarningsMember` / `TreasuryStockMember` / `ValuationAndTranslationAdjustmentsMember` / `ValuationDifferenceOnAvailableForSaleSecuritiesMember` / `SubscriptionRightsToSharesMember` | (標準。ラベル無し) | ― | なし | 株主資本等変動計算書の列 | セグメントではない |

ラベルだけで事業名に対応付けできた member: **5 / 19(26%)**。ただし事業セグメントの member は 5 つで、**5 / 5 が自動**。手書きが要った member: **0**(Run R を回す理由が無かった)。標準タクソノミの 14 member はラベルが ZIP に無く、MD&A にも語として出ない。

label linkbase の根拠: 各 member に ja ラベルが 2 本(`role/label` = 「直営サロン運営事業」、`role/verboseLabel` = 「直営サロン運営事業、報告セグメント [メンバー]」)。script は `role` が `/label` で終わるものだけを取る。`loc` の `href` 断片 `jpcrp030000-asr_E05055-000_DirectSalonReportableSegmentMember` と context の `explicitMember` 値 `jpcrp030000-asr_E05055-000:DirectSalonReportableSegmentMember` を `:` → `_` で突き合わせた。

## 6. member 束縛の選別の結果と、前期の member 一致

文ごとの解決: 事業名が文に 1 つ = **29 文**(31・38・42・47・50 の業績文と、見出し「(直営サロン運営事業)」等、設備投資・研究開発の節の文)、引き継ぎ(carried)= **1 文**(36。中に数の Claim は無く、文章の Claim は状態の語 1 件で元から UNVERIFIABLE)、`ambiguous(member)`(2 事業名以上)= **3 文**(17・20・115。全社の総括の文)。

member 付きの context で選ばれた fact は全部 `members == [member]` の 1 member だけの context。事業セグメント 5 つは当期・前期とも context が在り、`jppfs_cor:NetSales` と `jppfs_cor:OperatingIncome` が両期に在る(前期の BS サロンは fact 4 本と少ないが NetSales は在る)。**前期比 5 件は 5 件とも、当期と前期で同じ member の context の対(`CurrentYearDuration_…Member` ↔ `Prior1YearDuration_…Member`)で再計算した。** `no_prior_member_context` は 0。

**動いた Claim の全部**(member が付いた文 + ambiguous の文。これ以外は 1 件も動いていない):

| ID | 文 | 2 本目 → 3 本目 | 中身 |
|---|---|---|---|
| N017〜N047 の 20 件 | 31/38/42/47/50 | §2 | pointer が連結の総額 → member の NetSales に置き換わった(20 件とも) |
| N004 | 20 | VALUE_MISMATCH → **未束縛 `ambiguous(member)`** | 「BS サロン運営事業及びヘアメイク事業に係る固定資産について減損損失 3,758 千円」。2 本目は「減損損失」が語彙に無く「経常損失」に付いて連結の経常損失と比べていた(誤った束縛の VALUE_MISMATCH)。3 本目は 2 事業名の文なので束縛しない |
| T008・T009 | 17 | **GROUNDED → 未束縛 `ambiguous(member)`** | 「…直営サロン運営事業、ヘアメイク事業、美容室支援事業が堅調に推移し前期に比べ増収となり、全社としても増収となりました」。2 本目は連結の売上高(+6,442 千円)で GROUNDED。3 本目は 2 事業名以上の文なので束縛しない。**正しかった 2 件が規則で落ちた** |
| T010 | 17 | VALUE_MISMATCH → 未束縛 `ambiguous(member)` | 「BS サロン運営事業及びキャリアデザイン事業が前期に比べ減少」。予測どおり |
| T025 | 47 | GROUNDED → GROUNDED(**pointer が変わった**) | 「(美容室支援事業の)売上高は前期に比べ微増」。2 本目は連結の売上高(+6,442)で GROUNDED、3 本目は member の NetSales(+1,355)で GROUNDED。**結論は同じだが 2 本目の証拠は母集団が違っていた**(§8) |
| T026 | 47 | VALUE_MISMATCH → VALUE_MISMATCH(pointer が変わった) | 「減益」が凍結の主語規則で「売上高」に付く。member でも売上高は増なので不一致のまま |
| T034〜T036 | 115 | 未束縛 `no_subject` → 未束縛 `ambiguous(member)` | 理由の札が変わっただけ |

## 7. 2 席の照合

| 指標 | 2 本目 | 人間の予測 | 司令塔の予測 | **実測(Run L)** | 人間 | 司令塔 |
|---|---:|---:|---:|---:|---|---|
| セグメントの Claim → GROUNDED | 0 | 9〜15 / 18 | 5〜10 / 20 | **10 / 20** | 一致(数は範囲内。分母は 20) | 一致(上限) |
| 売上高の直接値 5 件 | 0 | | 3〜5 | **5** | | 一致 |
| 売上高の前期比 5 件 | 0 | | 2〜5 | **5** | | 一致 |
| セグメント利益 10 件 | 0 | | 0 | **0** | | 一致 |
| 残る VALUE_MISMATCH の最多理由 | | セグメント利益の要素名 等 | セグメント利益を売上高の要素と比べた | **その 10 件のみ** | 一致 | 一致 |
| 引き継ぎで決まった事業 | | | 5 中 3 | **0**(5 文とも文の中に事業名) | | **外れ**(2 本目の span の切れ端を文だと思った) |
| `ambiguous(member)` のセグメント Claim | | | 0〜2 | 0 | | 一致 |
| 数の束縛率 | 63.7 | ― | 60〜66 | **62.6**(57 / 91) | ― | 一致 |
| 数の束縛内 GROUNDED | 44.8 | 60〜75 | 52〜65 | **63.2**(36 / 57) | 一致 | 一致 |
| 再計算一致 | 38.9 | 65〜85 | 50〜67 | **66.7**(12 / 18) | 一致(下限) | 一致(上限) |
| 直接一致 | 47.5 | 60〜75 | 55〜65 | **61.5**(24 / 39) | 一致 | 一致 |
| セグメント以外の VALUE_MISMATCH 12 件 | 12 | | 12 のまま | **11**(N004 が未束縛へ) | | **外れ**(止まる側へ 1 件) |
| 引き継ぎが広すぎて新しく落ちる連結の Claim | 0 | | 0〜4 | 引き継ぎ由来 **0**。`ambiguous(member)` 由来で数 1(N004)・文章 3(T008/T009/T010) | | 半分一致(経路が違った) |
| 文章の束縛 | 14 | +0〜3 件、率は原則不変 | +0〜2 件 | **11(−3)** | **外れ**(減った) | **外れ**(減った) |
| 文章の束縛内 GROUNDED | 71.4 | 原則不変 | 65〜80 | **72.7**(8 / 11) | 一致 | 一致 |
| T010 の行方 | VM | | 未束縛へ | 未束縛へ | | 一致 |
| 層 / form / modifier / scheme | 0 | 0 | 0 | **0 / 0 / 0 / 0** | 一致 | 一致 |
| Adapter の登録簿 | | +1 種類 | 構造の規則 + 対応の登録を別に | +1 種類(事業名 ↔ member)。構造の規則は会社名を含まない | 一致 | 一致 |
| member の分母 | | (結果で確定) | 6〜9 | **19** | ― | **外れ**(株主資本等変動計算書の列・役員区分の member を数え落とした) |
| ラベルだけで対応付けできた member | | **半分以上** | 5(事業 5 つ) | **5 / 19 = 26%**。事業 member に限れば **5 / 5** | **外れ**(分母の定義どおりに数えると半分未満。事業 member だけなら全部) | 一致 |
| 手書きが要る member | | 残り | 0〜2 | **0** | ― | 一致 |
| 標準タクソノミの member のラベルは ZIP に無い | | | 無い | **無い**(14 member) | | 一致 |
| false pass(予測 §4 の定義) | 0 | 0〜1 | 0〜1 | **値の層 0、証拠の層 1(T025。§8)** | 一致 | 一致 |
| `value_only` の ambiguous 化 | 0 | +0〜3 | +0〜1 | **0** | 一致 | 一致 |
| member の対応が付かない Claim の落ち先 | | VM か UNVERIFIABLE | 未束縛か VM、GROUNDED にはならない | 未束縛(`ambiguous(member)`)か VM。GROUNDED 0 | 一致 | 一致 |

人間の列: 一致 11・外れ 2。司令塔の列: 一致 17・外れ 4(半分一致 1)。**外れは 2 席とも「文章の束縛が減った」で同じ向き**(2 席とも `ambiguous(member)` が総括の文の正しい GROUNDED を落とすことを読んでいなかった)。

## 8. false pass の確認

- **値の層**: 新たに GROUNDED になった 10 件を §3 のとおり全部読んだ。文の値・符号・母集団・期間が fact と一致する。**0。**
- **証拠の層(予測 §4 の定義に当たるか、人間の判断を仰ぐ)**: **T025** は 2 本目で GROUNDED だったが、その証拠は連結の売上高(+6,442 千円)で、文の主語は美容室支援事業の売上高(+1,355 千円)。方向が偶然同じだったので結論は変わらないが、**2 本目の GROUNDED は母集団の違う証拠で通っていた。** 定義の「実際には誤って GROUNDED だった」を結論で読むなら 0、証拠(pointer)で読むなら 1。v0.2 の Result は provenance を持つので、司令塔は**証拠の層の false pass 1 と数える**方を推す(結論が合っていても証拠が違えば監査は通していない)。
- 2 本目の T008・T009(全社の増収)は正しい証拠で正しい結論だったが、3 本目の規則で未束縛に落ちた。これは false pass ではなく、規則の鈍さ(§9 XP3-4)。

## 9. 予測に無かった事実(XP3-1〜XP3-7)

| # | 事実 | 仕様への影響 |
|---|---|---|
| XP3-1 | セグメントの fact は連結と**同じ局所名**(`jppfs_cor:NetSales`・`jppfs_cor:OperatingIncome`)を member 付き context で持つ。別に `jpcrp_cor:RevenuesFromExternalCustomers`・`TransactionsWithOtherSegments` も在るが、MD&A の数は NetSales(セグメント計)と一致した | 要素の選び方(完全一致優先)は member でそのまま効いた。語彙は member の有無で分ける必要が無い。`population` が独立の修飾であることの実測 |
| XP3-2 | 会社拡張の label linkbase は ZIP に在り、事業 member 5 つの標準ラベルが MD&A の事業名と**文字どおり一致**(全角「ＢＳ」は NFKC で吸収)。verboseLabel は「…、報告セグメント [メンバー]」で別物 | 事業 member の対応は**データ自身の鍵で引ける**(会社をまたいで移る部分)。ただし role を `/label` に固定して読むこと |
| XP3-3 | 分母の定義に従うと member は 19 で、うち 14 は株主資本等変動計算書の列・役員報酬の区分・セグメント注記の合計行。事業セグメントは 5 | 「評価対象の member」の分母は軸(axis)で切るべきだった(セグメント軸の member だけなら 8: 事業 5 + 計・調整・消去 3)。分母は変えずに記録し、次の予測で軸つきの定義にする |
| XP3-4 | `ambiguous(member)`(1 文に 2 事業名以上)が当たったのは**全社の総括の文**(17・20・115)で、そこには「全社としても増収」のような連結の主張が混じる。正しかった GROUNDED 2 件(T008/T009)が落ち、誤っていた束縛 1 件(N004)も落ちた | 規則は止まる側に鈍い。「全社」「連結」の語で母集団を連結に戻す規則は候補だが、**3 本目では足さない**(4 本目の予測へ) |
| XP3-5 | 引き継ぎ(carried)は 1 文(36)にだけ当たり、その文に数の Claim は無かった。5 つの業績文は全部、文の中に事業名を持っていた | 引き継ぎの規則は**効き目を測れていない**。残すなら次の会社で測る |
| XP3-6 | T025 は 2 本目で**母集団の違う証拠**で GROUNDED になっていた(方向が偶然一致)。3 本目で member の証拠に置き換わって初めて分かった | 「通った誤り 0」は値の層の話で、証拠の層では 2 本目に 1 件あった。結果に provenance を持たせる v0.2 の設計が要る理由の実物 |
| XP3-7 | (Run L は使っていない情報)member 付きの `jppfs_cor:OperatingIncome` の当期値は、文の「セグメント利益」5 件(32,925 / 62,407 / 14,953 / 76,608 / 14,224 千円)と**5 / 5 一致**する。前期も在る | 語彙に「セグメント利益 → OperatingIncome」を 1 行足せば 10 件が束縛の対象になる見込み。**3 本目では足していない**(語彙 73 は凍結)。足すなら 4 本目の予測を先に封じる |

## 10. 判定

| 問い | 答え |
|---|---|
| 同じ Core の構造のまま、既存の `population` と Adapter の登録簿だけで、2 本目の安全な遮断を GROUNDED に回収できたか | **できた(10 / 20)。** 回収できなかった 10 件は語彙(セグメント利益)の問題で、母集団の問題ではない。層・form・modifier・scheme は増えていない |
| 対応表の出どころ | 事業 member は **label linkbase から全部自動**(5 / 5)。手書き 0。Run R は不要だった |
| 通った誤り | 値の層 0。証拠の層で 2 本目の 1 件(T025)が見つかった |
| 率 | 束縛内 GROUNDED 44.8 → 63.2、再計算 38.9 → 66.7、直接 47.5 → 61.5。文章の束縛は 14 → 11 に**減った**(規則の鈍さ) |
| 予測との照合 | 2 席とも主要な数は範囲内。2 席とも「文章の束縛が減る」を外した。司令塔は分母 19 と引き継ぎ 0 も外した |
| Core 接続の GO / NO-GO | **まだ判定しない**(計器 4 つは接続のとき) |

## 11. 次に人間が決めること(提案。どれも 3 本目では実施していない)

1. T025 を false pass に数えるか(証拠の層 / 値の層)。
2. 4 本目を同じ書類でやるか: 語彙に「セグメント利益」1 行 + `ambiguous(member)` の文で「全社」「連結」の語があれば連結に戻す規則。やるなら予測を先に封じる(セグメント利益 10 件の行方・T008/T009 の復帰・false pass)。
3. 文章の Claim の指標(束縛内 GROUNDED 率)の固定は 3 社目以降(予測どおり持ち越し)。
4. Core 接続の GO / NO-GO は 1〜3 の後。
